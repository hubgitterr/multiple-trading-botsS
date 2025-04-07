# backend/db/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
load_dotenv(dotenv_path=dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment variables. Database connection cannot be established.")
    # Optionally raise an error or handle appropriately
    engine = None
    SessionLocal = None
else:
    try:
        # Consider connection pooling options for production
        engine = create_engine(DATABASE_URL) 
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine and session created successfully.")
        # Test connection (optional)
        # with engine.connect() as connection:
        #    logger.info("Database connection test successful.")
    except Exception as e:
        logger.exception(f"Failed to create database engine or session: {e}")
        engine = None
        SessionLocal = None

Base = declarative_base()

# Dependency to get DB session in FastAPI routes
def get_db():
    if SessionLocal is None:
         logger.error("Database session is not configured.")
         # This should ideally raise an HTTPException in the route if needed
         yield None 
         return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()