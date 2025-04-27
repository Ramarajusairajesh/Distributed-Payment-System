import json
import os
import logging
from typing import Dict, Any, Callable, List, Optional
from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from kafka.errors import KafkaError
import threading
import uuid
import time

# Environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRANSACTION_TOPIC = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "transactions")
NOTIFICATION_TOPIC = os.getenv("KAFKA_TOPIC_NOTIFICATIONS", "notifications")
NODE_ID = os.getenv("NODE_ID", "node1")

# Configure logging
logger = logging.getLogger(__name__)

class KafkaClient:
    """
    Kafka client for producing and consuming messages.
    """
    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers = {}
        self.consumer_threads = {}
        self.running = True
        
    def _create_producer(self):
        """
        Create a Kafka producer.
        """
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas to acknowledge
                    retries=3,    # Retry up to 3 times
                    linger_ms=10  # Batch messages
                )
                logger.info(f"Kafka producer created, connected to {self.bootstrap_servers}")
            except KafkaError as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise
    
    def produce_message(self, topic: str, value: Dict[str, Any], key: Optional[str] = None) -> None:
        """
        Produce a message to a Kafka topic.
        """
        if self.producer is None:
            self._create_producer()
            
        try:
            # If no key is provided, generate one for consistent routing
            if key is None:
                key = str(uuid.uuid4())
                
            # Add node_id to message metadata
            if isinstance(value, dict) and 'metadata' not in value:
                value['metadata'] = {}
            if isinstance(value, dict) and isinstance(value.get('metadata'), dict):
                value['metadata']['source_node'] = NODE_ID
                
            future = self.producer.send(topic, value=value, key=key)
            logger.debug(f"Message sent to topic {topic} with key {key}")
            return future
        except KafkaError as e:
            logger.error(f"Failed to produce message to {topic}: {e}")
            raise
    
    def create_consumer(self, topic: str, group_id: str, auto_offset_reset: str = 'earliest'):
        """
        Create a Kafka consumer for a topic.
        """
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True
            )
            return consumer
        except KafkaError as e:
            logger.error(f"Failed to create Kafka consumer for {topic}: {e}")
            raise
    
    def start_consumer(self, topic: str, group_id: str, callback: Callable, auto_offset_reset: str = 'earliest'):
        """
        Start a consumer in a background thread.
        """
        def consumer_thread():
            consumer = self.create_consumer(topic, group_id, auto_offset_reset)
            self.consumers[topic] = consumer
            
            while self.running:
                try:
                    for message in consumer:
                        if not self.running:
                            break
                        try:
                            logger.debug(f"Received message from {topic}: {message.value}")
                            callback(message.value, message.key)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                except Exception as e:
                    logger.error(f"Consumer error: {e}")
                    if self.running:
                        # Try to recreate consumer after a brief delay
                        time.sleep(5)
                        consumer = self.create_consumer(topic, group_id, auto_offset_reset)
                        self.consumers[topic] = consumer
        
        thread = threading.Thread(target=consumer_thread)
        thread.daemon = True
        thread.start()
        self.consumer_threads[topic] = thread
        logger.info(f"Started consumer for topic {topic} with group {group_id}")
    
    def stop(self):
        """
        Stop all consumers and close the producer.
        """
        self.running = False
        
        # Close consumers
        for topic, consumer in self.consumers.items():
            try:
                consumer.close()
                logger.info(f"Consumer for topic {topic} closed")
            except Exception as e:
                logger.error(f"Error closing consumer for {topic}: {e}")
        
        # Close producer
        if self.producer:
            try:
                self.producer.close()
                logger.info("Producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")

# Create a global Kafka client instance
kafka_client = KafkaClient() 