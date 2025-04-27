import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import hashlib
import asyncio

from app.common.utils.distributed import (
    ConsistentHashing,
    get_node_for_transaction,
    distributed_lock,
    is_responsible_for_key,
    NODE_ID,
    CLUSTER_NODES
)

class TestConsistentHashing:
    """Test cases for consistent hashing implementation."""

    def test_hash_ring_initialization(self):
        """Test that hash ring is correctly initialized with nodes."""
        nodes = ["node1", "node2", "node3"]
        replicas = 10
        ch = ConsistentHashing(nodes, replicas)
        
        # Verify all nodes are in the ring
        for node in nodes:
            assert node in ch.ring.values()
            
        # Verify we have the expected number of keys
        assert len(ch.ring) == len(nodes) * replicas
        
        # Verify keys are sorted
        assert ch.sorted_keys == sorted(ch.ring.keys())

    def test_add_node(self):
        """Test adding a node to the hash ring."""
        nodes = ["node1", "node2"]
        replicas = 10
        ch = ConsistentHashing(nodes, replicas)
        
        # Initial state
        initial_key_count = len(ch.ring)
        
        # Add a node
        ch.add_node("node3")
        
        # Verify the node was added
        assert "node3" in ch.ring.values()
        
        # Verify key count increased by expected amount
        assert len(ch.ring) == initial_key_count + replicas

    def test_remove_node(self):
        """Test removing a node from the hash ring."""
        nodes = ["node1", "node2", "node3"]
        replicas = 10
        ch = ConsistentHashing(nodes, replicas)
        
        # Initial state
        initial_key_count = len(ch.ring)
        
        # Remove a node
        ch.remove_node("node2")
        
        # Verify the node was removed
        assert "node2" not in ch.ring.values()
        
        # Verify key count decreased by expected amount
        assert len(ch.ring) == initial_key_count - replicas

    def test_get_node_consistent(self):
        """Test that the same key always maps to the same node."""
        nodes = ["node1", "node2", "node3"]
        ch = ConsistentHashing(nodes)
        
        # Get node for a key
        key = "test_transaction_id"
        node = ch.get_node(key)
        
        # Get the node again for the same key
        node2 = ch.get_node(key)
        
        # Verify we get the same node
        assert node == node2

    def test_get_node_distribution(self):
        """Test that keys are distributed across nodes."""
        nodes = ["node1", "node2", "node3"]
        ch = ConsistentHashing(nodes)
        
        # Generate a large number of keys
        keys = [f"key{i}" for i in range(1000)]
        
        # Map keys to nodes
        node_counts = {node: 0 for node in nodes}
        for key in keys:
            node = ch.get_node(key)
            node_counts[node] += 1
            
        # Verify all nodes got some keys
        for node in nodes:
            assert node_counts[node] > 0
        
        # Verify distribution is reasonably balanced
        # (no node should have more than 50% of the keys in a 3-node system)
        for node in nodes:
            assert node_counts[node] < 500

    def test_get_node_empty_ring(self):
        """Test that getting a node from an empty ring raises an exception."""
        ch = ConsistentHashing([])
        
        with pytest.raises(Exception, match="Hash ring is empty"):
            ch.get_node("test_key")

    def test_hash_function(self):
        """Test that the hash function returns consistent results."""
        ch = ConsistentHashing(["node1"])
        
        # Test hash values
        test_key = "test_key"
        expected_hash = int(hashlib.md5(test_key.encode()).hexdigest(), 16)
        actual_hash = ch._hash(test_key)
        
        assert actual_hash == expected_hash

class TestDistributedFunctions:
    """Test cases for distributed utility functions."""

    def test_get_node_for_transaction(self):
        """Test the get_node_for_transaction function."""
        transaction_id = "test_transaction_id"
        
        # Get node for transaction
        node = get_node_for_transaction(transaction_id)
        
        # Verify it returns a node from our cluster
        assert node in CLUSTER_NODES
        
        # Verify it's consistent
        node2 = get_node_for_transaction(transaction_id)
        assert node == node2

    def test_is_responsible_for_key(self):
        """Test the is_responsible_for_key function."""
        # Mock consistent hashing to return NODE_ID
        with patch('app.common.utils.distributed.get_node_for_transaction', return_value=NODE_ID):
            # This key should be our responsibility
            assert is_responsible_for_key("test_key") is True
            
        # Mock consistent hashing to return a different node
        with patch('app.common.utils.distributed.get_node_for_transaction', return_value="different_node"):
            # This key should not be our responsibility
            assert is_responsible_for_key("test_key") is False

    @pytest.mark.asyncio
    async def test_distributed_lock_success(self):
        """Test the distributed_lock decorator acquires and releases a lock."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # Lock acquisition succeeds
        mock_redis.get.return_value = f"{NODE_ID}:123456"  # We still own the lock
        
        with patch('app.common.utils.distributed.redis_client', mock_redis):
            # Create a test function to decorate
            @distributed_lock(key_prefix="test_lock")
            async def test_function(resource_id):
                return f"processed {resource_id}"
                
            # Call the decorated function
            result = await test_function("test_resource")
            
            # Verify function was called and returned expected result
            assert result == "processed test_resource"
            
            # Verify lock was acquired
            mock_redis.set.assert_called_once()
            
            # Verify lock was released
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_distributed_lock_failure(self):
        """Test the distributed_lock decorator handles lock acquisition failure."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.set.return_value = False  # Lock acquisition fails
        
        with patch('app.common.utils.distributed.redis_client', mock_redis):
            # Create a test function to decorate
            @distributed_lock(key_prefix="test_lock")
            async def test_function(resource_id):
                return f"processed {resource_id}"
                
            # Call the decorated function - should raise exception
            with pytest.raises(Exception, match="Failed to acquire lock"):
                await test_function("test_resource")
            
            # Verify lock was not released (since it was never acquired)
            mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_distributed_lock_lost_ownership(self):
        """Test the distributed_lock decorator handles losing lock ownership."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # Lock acquisition succeeds
        mock_redis.get.return_value = "different_owner:123456"  # Lock ownership changed
        
        with patch('app.common.utils.distributed.redis_client', mock_redis):
            # Create a test function to decorate
            @distributed_lock(key_prefix="test_lock")
            async def test_function(resource_id):
                return f"processed {resource_id}"
                
            # Call the decorated function
            result = await test_function("test_resource")
            
            # Verify function was called and returned expected result
            assert result == "processed test_resource"
            
            # Verify lock was not released (since we don't own it anymore)
            mock_redis.delete.assert_not_called() 