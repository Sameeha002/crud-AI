import sqlite3
import requests
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session
import threading

_engine = None
_session_factory = None
_db_instance = None
Base = None
_initialized = False
_lock = threading.Lock()

# music agent
def get_engine_for_chinook_db():
    """
    Pull SQL file, populate in-memory database, and create engine.
    
    Downloads the Chinook database SQL script from GitHub and creates an in-memory 
    SQLite database populated with the sample data.
    
    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine connected to the in-memory database
    """
    # Download the Chinook database SQL script from the official repository
    url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
    response = requests.get(url)
    sql_script = response.text

    # Create an in-memory SQLite database connection
    # check_same_thread=False allows the connection to be used across threads
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    
    # Execute the SQL script to populate the database with sample data
    connection.executescript(sql_script)
    
    # Create and return a SQLAlchemy engine that uses the populated connection
    return create_engine(
        "sqlite://",  # SQLite URL scheme
        creator=lambda: connection,  # Function that returns the database connection
        poolclass=StaticPool,  # Use StaticPool to maintain single connection
        connect_args={"check_same_thread": False},  # Allow cross-thread usage
    )

def initialize_db():
    """Run once — sets up engine, reflects tables, creates session factory"""
    global _engine, _session_factory, Base, _initialized
    if _initialized:
        return

    with _lock:
        if _initialized:
            return
        _engine = get_engine_for_chinook_db()
        Base = automap_base()
        Base.prepare(_engine, reflect=True)  # reads all existing Chinook tables
        _session_factory = sessionmaker(bind=_engine)
        _initialized = True
        print('chinook db initialized')

def get_chinook_db() -> SQLDatabase:
    """For LangChain agents that need SQLDatabase wrapper"""
    global _db_instance
    if _db_instance is None:
        initialize_db()
        _db_instance = SQLDatabase(_engine)
    return _db_instance

def get_session() -> Session:
    """For ORM queries in tools"""
    initialize_db()
    return _session_factory()

def get_classes():
    """Returns all reflected Chinook table classes"""
    initialize_db()
    return Base.classes


