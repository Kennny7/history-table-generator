"""
Database abstraction layer
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import threading
from contextlib import contextmanager
from enum import Enum

class DatabaseError(Exception):
    """Custom database exception"""
    pass

class BaseDatabase(ABC):
    """Abstract base class for database operations"""
    
    def __init__(self, config: Dict[str, Any], ui):
        self.config = config
        self.ui = ui
        self.connection = None
        self.lock = threading.RLock()
        self._transaction_stack = []
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection"""
        pass
    
    @abstractmethod
    def get_databases(self) -> List[str]:
        """Get list of databases"""
        pass
    
    @abstractmethod
    def get_schemas(self, database: str) -> List[str]:
        """Get list of schemas in database"""
        pass
    
    @abstractmethod
    def get_tables(self, schema: str) -> List[Dict[str, Any]]:
        """Get list of tables in schema"""
        pass
    
    @abstractmethod
    def get_table_columns(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a specific table"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a SQL query"""
        pass
    
    @abstractmethod
    def execute_many(self, queries: List[str]):
        """Execute multiple SQL queries"""
        pass
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        self.begin_transaction()
        try:
            yield
            self.commit_transaction()
        except Exception:
            self.rollback_transaction()
            raise
    
    def begin_transaction(self):
        """Begin a new transaction"""
        self.execute_query("BEGIN TRANSACTION")
        self._transaction_stack.append(True)
    
    def commit_transaction(self):
        """Commit current transaction"""
        if self._transaction_stack:
            self.execute_query("COMMIT")
            self._transaction_stack.pop()
    
    def rollback_transaction(self):
        """Rollback current transaction"""
        if self._transaction_stack:
            self.execute_query("ROLLBACK")
            self._transaction_stack.pop()
    
    def get_current_user(self) -> str:
        """Get current database user"""
        result = self.execute_query("SELECT CURRENT_USER")
        return result[0][0] if result else 'SYSTEM'

class PostgreSQLDatabase(BaseDatabase):
    """PostgreSQL implementation"""
    
    def connect(self) -> bool:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            self.connection = psycopg2.connect(
                host=self.config.get('host'),
                port=self.config.get('port', 5432),
                user=self.config.get('username'),
                password=self.config.get('password'),
                database=self.config.get('database'),
                cursor_factory=RealDictCursor
            )
            return True
        except Exception as e:
            raise DatabaseError(f"PostgreSQL connection failed: {str(e)}")
    
    def get_databases(self) -> List[str]:
        query = """
        SELECT datname 
        FROM pg_database 
        WHERE datistemplate = false
        ORDER BY datname
        """
        result = self.execute_query(query)
        return [row['datname'] for row in result]
    
    def get_schemas(self, database: str) -> List[str]:
        # Switch to selected database
        self.execute_query(f"\\c {database}")
        
        query = """
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name
        """
        result = self.execute_query(query)
        return [row['schema_name'] for row in result]
    
    def get_tables(self, schema: str) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            table_name,
            table_type
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name
        """
        result = self.execute_query(query, (schema,))
        return [
            {
                'name': row['table_name'],
                'type': row['table_type'],
                'schema': schema
            }
            for row in result
        ]

class MySQLDatabase(BaseDatabase):
    """MySQL implementation"""
    
    def connect(self) -> bool:
        try:
            import mysql.connector
            from mysql.connector import Error
            
            self.connection = mysql.connector.connect(
                host=self.config.get('host'),
                port=self.config.get('port', 3306),
                user=self.config.get('username'),
                password=self.config.get('password'),
                database=self.config.get('database')
            )
            return True
        except Exception as e:
            raise DatabaseError(f"MySQL connection failed: {str(e)}")

class DatabaseFactory:
    """Factory for creating database instances"""
    
    @staticmethod
    def create_database(config: Dict[str, Any], ui) -> BaseDatabase:
        db_type = config.get('db_type', '').lower()
        
        if db_type in ['postgresql', 'postgres']:
            return PostgreSQLDatabase(config, ui)
        elif db_type in ['mysql', 'mariadb']:
            return MySQLDatabase(config, ui)
        # Add other database types here
        else:
            raise ValueError(f"Unsupported database type: {db_type}")