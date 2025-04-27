import logging
import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional

from app.common.utils.kafka_client import kafka_client, NOTIFICATION_TOPIC

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Environment variables
NODE_ID = os.getenv("NODE_ID", "node1")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMS_ENABLED = os.getenv("SMS_ENABLED", "false").lower() == "true"

class NotificationService:
    """
    Service for processing and sending notifications.
    """
    def __init__(self):
        self.is_running = False
        self.topics = {
            "transaction_events": self.handle_transaction_event,
            "account_events": self.handle_account_event,
            "balance_events": self.handle_balance_event,
            NOTIFICATION_TOPIC: self.handle_direct_notification
        }
        
    async def start(self):
        """
        Start the notification service.
        """
        logger.info("Starting Notification Service...")
        self.is_running = True
        
        # Start Kafka consumers for all topics
        for topic, handler in self.topics.items():
            logger.info(f"Setting up consumer for topic: {topic}")
            kafka_client.start_consumer(
                topic,
                f"notification-service-{NODE_ID}-{topic}",
                handler
            )
        
        logger.info("Notification Service started")
        
        # Keep the service running
        while self.is_running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """
        Stop the notification service.
        """
        logger.info("Stopping Notification Service...")
        self.is_running = False
        kafka_client.stop()
        logger.info("Notification Service stopped")
    
    async def handle_transaction_event(self, event: Dict[str, Any], key: str):
        """
        Handle transaction events.
        """
        event_type = event.get("event_type")
        
        if event_type == "transaction_completed":
            # Transaction completed, notify both sender and receiver
            transaction_id = event.get("transaction_id")
            reference_id = event.get("reference_id")
            from_account_id = event.get("from_account_id")
            to_account_id = event.get("to_account_id")
            amount = event.get("amount")
            currency = event.get("currency")
            
            # In a real system, we would look up user contact info and send actual notifications
            logger.info(f"Transaction {reference_id} completed: {amount} {currency} from {from_account_id} to {to_account_id}")
            
            # Simulate sending notifications
            await self.send_email_notification(
                to_user_id=self.get_user_id_for_account(from_account_id),
                subject=f"Payment Sent: {reference_id}",
                body=f"Your payment of {amount} {currency} has been sent. Reference: {reference_id}"
            )
            
            await self.send_email_notification(
                to_user_id=self.get_user_id_for_account(to_account_id),
                subject=f"Payment Received: {reference_id}",
                body=f"You have received a payment of {amount} {currency}. Reference: {reference_id}"
            )
            
        elif event_type == "transaction_failed":
            # Transaction failed, notify the sender
            transaction_id = event.get("transaction_id")
            reference_id = event.get("reference_id")
            reason = event.get("reason", "Unknown error")
            
            # In a real system, we would look up the sender's contact info
            logger.info(f"Transaction {reference_id} failed: {reason}")
            
            # Simulate sending notification to sender
            # We'd need to query the transaction details to get the sender account
            # For simplicity, we're logging only
            logger.info(f"Would send failure notification for transaction {reference_id}")
    
    async def handle_account_event(self, event: Dict[str, Any], key: str):
        """
        Handle account events.
        """
        event_type = event.get("event_type")
        data = event.get("data", {})
        
        if event_type == "account_created":
            # Account created, notify the user
            account_id = data.get("id")
            user_id = data.get("user_id")
            account_number = data.get("account_number")
            
            logger.info(f"Account {account_number} created for user {user_id}")
            
            # Simulate sending notification
            await self.send_email_notification(
                to_user_id=user_id,
                subject="Account Created",
                body=f"Your new account {account_number} has been created successfully."
            )
            
        elif event_type == "account_updated":
            # Account updated, notify the user if status changed
            account_id = data.get("id")
            user_id = data.get("user_id")
            status = data.get("status")
            
            if status:
                logger.info(f"Account {account_id} status updated to {status} for user {user_id}")
                
                # Simulate sending notification
                await self.send_email_notification(
                    to_user_id=user_id,
                    subject="Account Status Updated",
                    body=f"Your account status has been updated to {status}."
                )
    
    async def handle_balance_event(self, event: Dict[str, Any], key: str):
        """
        Handle balance events.
        """
        event_type = event.get("event_type")
        data = event.get("data", {})
        
        if event_type == "balance_updated":
            # Balance updated, notify the user
            account_id = data.get("account_id")
            user_id = data.get("user_id")
            amount = data.get("amount")
            balance = data.get("balance")
            currency = data.get("currency")
            operation = data.get("operation")
            
            logger.info(f"Balance {operation} of {amount} {currency} on account {account_id} for user {user_id}")
            
            # Simulate sending notification
            await self.send_email_notification(
                to_user_id=user_id,
                subject=f"Account {operation.title()} Notification",
                body=f"A {operation} of {amount} {currency} has been processed on your account. New balance: {balance} {currency}"
            )
    
    async def handle_direct_notification(self, notification: Dict[str, Any], key: str):
        """
        Handle direct notification requests.
        """
        notification_type = notification.get("type", "email")
        recipient = notification.get("recipient")
        subject = notification.get("subject")
        message = notification.get("message")
        
        if notification_type == "email":
            await self.send_email_notification(
                to_user_id=recipient,
                subject=subject,
                body=message
            )
        elif notification_type == "sms":
            await self.send_sms_notification(
                to_user_id=recipient,
                message=message
            )
    
    async def send_email_notification(self, to_user_id: str, subject: str, body: str):
        """
        Send an email notification.
        """
        if not EMAIL_ENABLED:
            logger.info(f"Email notification would be sent to user {to_user_id}: {subject}")
            return
        
        # In a real system, this would use an email service like SendGrid, Mailgun, etc.
        logger.info(f"Sending email to user {to_user_id}: {subject}")
        # Simulate email sending delay
        await asyncio.sleep(0.1)
        logger.info(f"Email sent to user {to_user_id}")
    
    async def send_sms_notification(self, to_user_id: str, message: str):
        """
        Send an SMS notification.
        """
        if not SMS_ENABLED:
            logger.info(f"SMS notification would be sent to user {to_user_id}: {message[:20]}...")
            return
        
        # In a real system, this would use an SMS service like Twilio, Nexmo, etc.
        logger.info(f"Sending SMS to user {to_user_id}")
        # Simulate SMS sending delay
        await asyncio.sleep(0.1)
        logger.info(f"SMS sent to user {to_user_id}")
    
    def get_user_id_for_account(self, account_id: str) -> str:
        """
        Get the user ID for an account.
        
        In a real system, this would query the account service or database.
        For simplicity, we're returning a placeholder.
        """
        return f"user-for-{account_id}"

# Main entry point
async def main():
    """
    Main entry point for the notification service.
    """
    service = NotificationService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main()) 