import logging
from sqlalchemy.exc import SQLAlchemyError
from app.common.database.db import engine, Base, get_db_context
from app.common.models.users import User
from app.common.models.accounts import Account, AccountType, AccountStatus
from app.common.models.transactions import Transaction, TransactionStatus, TransactionType
from app.common.utils.security import get_password_hash
import uuid
import os

logger = logging.getLogger(__name__)

def create_tables():
    """
    Create all database tables if they don't exist.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def create_superuser():
    """
    Create a superuser if no users exist in the database.
    """
    try:
        with get_db_context() as db:
            # Check if any users exist
            user_count = db.query(User).count()
            
            if user_count == 0:
                # Create a superuser
                admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
                superuser = User(
                    id=str(uuid.uuid4()),
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash(admin_password),
                    full_name="System Administrator",
                    is_active=True,
                    is_superuser=True
                )
                db.add(superuser)
                
                # Create a system account for handling platform operations
                system_account = Account(
                    id=str(uuid.uuid4()),
                    user_id=superuser.id,
                    account_number=f"SYS-{uuid.uuid4().hex[:8].upper()}",
                    account_type=AccountType.BUSINESS,
                    status=AccountStatus.ACTIVE,
                    balance=1000000.0,  # Initial system balance
                    currency="USD"
                )
                db.add(system_account)
                
                db.commit()
                logger.info("Superuser and system account created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating superuser: {e}")
        raise

def init_db():
    """
    Initialize the database.
    """
    logger.info("Initializing database...")
    create_tables()
    create_superuser()
    logger.info("Database initialization completed") 