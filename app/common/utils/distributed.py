import hashlib
import os
from typing import List, Optional, Dict, Any, Callable
import json
import time
import random
import redis
from functools import wraps

# Environment variables
NODE_ID = os.getenv("NODE_ID", "node1")
CLUSTER_NODES = os.getenv("CLUSTER_NODES", "node1,node2,node3").split(",")

# Redis connection for distributed locks
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class ConsistentHashing:
    """
    Consistent hashing implementation for distributing transactions across nodes.
    """
    def __init__(self, nodes: List[str], replicas: int = 100):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        
        for node in nodes:
            self.add_node(node)
    
    def add_node(self, node: str) -> None:
        """
        Add a node to the hash ring.
        """
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
        self.sorted_keys = sorted(self.ring.keys())
    
    def remove_node(self, node: str) -> None:
        """
        Remove a node from the hash ring.
        """
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            if key in self.ring:
                del self.ring[key]
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key: str) -> str:
        """
        Get the node that should handle the given key.
        """
        if not self.ring:
            raise Exception("Hash ring is empty")
        
        hash_key = self._hash(key)
        
        # Find the first point in the ring with a value >= hash_key
        for ring_key in self.sorted_keys:
            if ring_key >= hash_key:
                return self.ring[ring_key]
        
        # If we reached here, it means the hash_key is greater than all
        # keys in the ring, so we return the first node in the ring
        return self.ring[self.sorted_keys[0]]
    
    def _hash(self, key: str) -> int:
        """
        Generate a hash value for a key.
        """
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

# Create a global consistent hash ring
consistent_hash = ConsistentHashing(CLUSTER_NODES)

def get_node_for_transaction(transaction_id: str) -> str:
    """
    Determine which node should process a given transaction.
    """
    return consistent_hash.get_node(transaction_id)

def distributed_lock(key_prefix: str, lock_timeout: int = 10):
    """
    Decorator for distributed locking using Redis.
    
    Args:
        key_prefix: Prefix for the lock key
        lock_timeout: Lock timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the resource identifier from the first argument (typically resource_id)
            resource_id = args[0] if args else kwargs.get('resource_id')
            if not resource_id:
                raise ValueError("Resource ID must be provided as first argument or as 'resource_id' kwarg")
            
            lock_key = f"{key_prefix}:{resource_id}"
            lock_value = f"{NODE_ID}:{time.time()}"
            lock_acquired = redis_client.set(lock_key, lock_value, nx=True, ex=lock_timeout)
            
            if not lock_acquired:
                # Could implement retry logic here
                raise Exception(f"Failed to acquire lock for {lock_key}")
            
            try:
                return await func(*args, **kwargs)
            finally:
                # Only release lock if we still own it
                current_value = redis_client.get(lock_key)
                if current_value == lock_value:
                    redis_client.delete(lock_key)
                
        return wrapper
    return decorator

def is_responsible_for_key(key: str) -> bool:
    """
    Check if the current node is responsible for handling the given key.
    """
    return get_node_for_transaction(key) == NODE_ID 