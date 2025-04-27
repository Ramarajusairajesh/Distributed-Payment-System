import pytest
from unittest.mock import patch, MagicMock, call
import json
import uuid

from app.common.utils.kafka_client import (
    KafkaClient,
    kafka_client,
    TRANSACTION_TOPIC,
    NOTIFICATION_TOPIC,
    NODE_ID
)

class TestKafkaClient:
    """Test cases for Kafka client implementation."""

    def test_initialization(self):
        """Test client initialization."""
        bootstrap_servers = "test_server:9092"
        client = KafkaClient(bootstrap_servers)
        
        assert client.bootstrap_servers == bootstrap_servers
        assert client.producer is None
        assert client.consumers == {}
        assert client.consumer_threads == {}
        assert client.running is True

    @patch('app.common.utils.kafka_client.KafkaProducer')
    def test_create_producer(self, mock_kafka_producer):
        """Test producer creation."""
        # Setup mock
        mock_instance = MagicMock()
        mock_kafka_producer.return_value = mock_instance
        
        # Create client and producer
        client = KafkaClient("test_server:9092")
        client._create_producer()
        
        # Verify producer was created with correct config
        mock_kafka_producer.assert_called_once()
        assert client.producer == mock_instance

    @patch('app.common.utils.kafka_client.KafkaProducer')
    def test_produce_message(self, mock_kafka_producer):
        """Test producing a message."""
        # Setup mocks
        mock_instance = MagicMock()
        mock_future = MagicMock()
        mock_instance.send.return_value = mock_future
        mock_kafka_producer.return_value = mock_instance
        
        # Create client
        client = KafkaClient("test_server:9092")
        
        # Test producing a message
        topic = "test_topic"
        value = {"test_key": "test_value"}
        key = "test_key"
        
        result = client.produce_message(topic, value, key)
        
        # Verify producer was created
        mock_kafka_producer.assert_called_once()
        
        # Verify send was called with correct arguments
        mock_instance.send.assert_called_once()
        call_args = mock_instance.send.call_args[1]
        assert call_args["topic"] == topic
        assert call_args["key"] == key
        
        # Check that metadata was added
        sent_value = call_args["value"]
        assert sent_value["metadata"]["source_node"] == NODE_ID
        
        # Verify result is the future
        assert result == mock_future

    @patch('app.common.utils.kafka_client.KafkaProducer')
    def test_produce_message_no_key(self, mock_kafka_producer):
        """Test producing a message without a key generates a UUID."""
        # Setup mocks
        mock_instance = MagicMock()
        mock_instance.send.return_value = MagicMock()
        mock_kafka_producer.return_value = mock_instance
        
        # Create client
        client = KafkaClient("test_server:9092")
        
        # Test producing a message without a key
        topic = "test_topic"
        value = {"test_key": "test_value"}
        
        with patch('uuid.uuid4', return_value="mocked-uuid"):
            client.produce_message(topic, value)
        
        # Verify send was called with UUID key
        call_args = mock_instance.send.call_args[1]
        assert call_args["key"] == "mocked-uuid"

    @patch('app.common.utils.kafka_client.KafkaConsumer')
    def test_create_consumer(self, mock_kafka_consumer):
        """Test consumer creation."""
        # Setup mock
        mock_instance = MagicMock()
        mock_kafka_consumer.return_value = mock_instance
        
        # Create client
        client = KafkaClient("test_server:9092")
        
        # Create consumer
        topic = "test_topic"
        group_id = "test_group"
        auto_offset_reset = "latest"
        
        consumer = client.create_consumer(topic, group_id, auto_offset_reset)
        
        # Verify consumer was created with correct config
        mock_kafka_consumer.assert_called_once_with(
            topic,
            bootstrap_servers=client.bootstrap_servers,
            value_deserializer=mock_kafka_consumer.call_args[1]["value_deserializer"],
            key_deserializer=mock_kafka_consumer.call_args[1]["key_deserializer"],
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True
        )
        
        # Verify consumer instance was returned
        assert consumer == mock_instance

    @patch('app.common.utils.kafka_client.threading.Thread')
    @patch('app.common.utils.kafka_client.KafkaConsumer')
    def test_start_consumer(self, mock_kafka_consumer, mock_thread):
        """Test starting a consumer thread."""
        # Setup mocks
        mock_consumer = MagicMock()
        mock_kafka_consumer.return_value = mock_consumer
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Create client
        client = KafkaClient("test_server:9092")
        
        # Create callback function
        callback = MagicMock()
        
        # Start consumer
        topic = "test_topic"
        group_id = "test_group"
        
        client.start_consumer(topic, group_id, callback)
        
        # Verify consumer was created
        mock_kafka_consumer.assert_called_once()
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify consumer and thread were stored
        assert client.consumers.get(topic) == mock_consumer
        assert client.consumer_threads.get(topic) == mock_thread_instance

    def test_stop(self):
        """Test stopping the client."""
        # Create client with mocked consumers and producer
        client = KafkaClient("test_server:9092")
        
        # Create mock consumers
        mock_consumer1 = MagicMock()
        mock_consumer2 = MagicMock()
        client.consumers = {
            "topic1": mock_consumer1,
            "topic2": mock_consumer2
        }
        
        # Create mock producer
        mock_producer = MagicMock()
        client.producer = mock_producer
        
        # Stop the client
        client.stop()
        
        # Verify running flag is set to False
        assert client.running is False
        
        # Verify consumers were closed
        mock_consumer1.close.assert_called_once()
        mock_consumer2.close.assert_called_once()
        
        # Verify producer was closed
        mock_producer.close.assert_called_once()

    @patch('app.common.utils.kafka_client.KafkaProducer')
    def test_produce_message_with_existing_metadata(self, mock_kafka_producer):
        """Test producing a message with existing metadata."""
        # Setup mocks
        mock_instance = MagicMock()
        mock_instance.send.return_value = MagicMock()
        mock_kafka_producer.return_value = mock_instance
        
        # Create client
        client = KafkaClient("test_server:9092")
        
        # Test producing a message with existing metadata
        topic = "test_topic"
        value = {
            "test_key": "test_value",
            "metadata": {
                "existing_key": "existing_value"
            }
        }
        
        client.produce_message(topic, value)
        
        # Verify metadata was merged
        call_args = mock_instance.send.call_args[1]
        sent_value = call_args["value"]
        assert sent_value["metadata"]["existing_key"] == "existing_value"
        assert sent_value["metadata"]["source_node"] == NODE_ID

    @patch('app.common.utils.kafka_client.KafkaProducer')
    def test_produce_message_error_handling(self, mock_kafka_producer):
        """Test error handling in produce_message."""
        # Setup mock to raise exception
        mock_instance = MagicMock()
        mock_instance.send.side_effect = Exception("Test error")
        mock_kafka_producer.return_value = mock_instance
        
        # Create client
        client = KafkaClient("test_server:9092")
        
        # Test producing a message
        topic = "test_topic"
        value = {"test_key": "test_value"}
        
        # Should raise exception
        with pytest.raises(Exception, match="Test error"):
            client.produce_message(topic, value)

    def test_global_instance(self):
        """Test that the global kafka_client instance exists."""
        assert kafka_client is not None
        assert isinstance(kafka_client, KafkaClient) 