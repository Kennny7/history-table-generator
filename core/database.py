"""
Database abstraction layer
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import threading
from contextlib import contextmanager
from enum import Enum
from utils.logger import get_logger

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
        self.logger = get_logger(f"database.{self.__class__.__name__}")
        self.logger.info(f"Initializing {self.__class__.__name__} with config: {self._safe_config()}")
    
    def _safe_config(self) -> Dict[str, Any]:
        """Return config with sensitive data masked"""
        safe_config = self.config.copy()
        if 'password' in safe_config:
            safe_config['password'] = '******'
        if 'username' in safe_config:
            safe_config['username'] = safe_config['username'][:3] + '***' if len(safe_config['username']) > 3 else '***'
        return safe_config
    
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
            self.logger.debug("Transaction committed successfully")
        except Exception as e:
            self.logger.error(f"Transaction failed, rolling back: {str(e)}")
            self.rollback_transaction()
            raise
    
    def begin_transaction(self):
        """Begin a new transaction"""
        self.execute_query("BEGIN TRANSACTION")
        self._transaction_stack.append(True)
        self.logger.debug("Transaction begun")
    
    def commit_transaction(self):
        """Commit current transaction"""
        if self._transaction_stack:
            self.execute_query("COMMIT")
            self._transaction_stack.pop()
            self.logger.debug("Transaction committed")
    
    def rollback_transaction(self):
        """Rollback current transaction"""
        if self._transaction_stack:
            self.execute_query("ROLLBACK")
            self._transaction_stack.pop()
            self.logger.warning("Transaction rolled back")
    
    def get_current_user(self) -> str:
        """Get current database user"""
        try:
            result = self.execute_query("SELECT CURRENT_USER")
            return result[0][0] if result else 'SYSTEM'
        except Exception as e:
            self.logger.warning(f"Failed to get current user: {str(e)}")
            return 'UNKNOWN'
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.connection is not None and self.connection.closed == 0
    
    def ping(self) -> bool:
        """Check database connection"""
        try:
            self.execute_query("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Database ping failed: {str(e)}")
            return False

class PostgreSQLDatabase(BaseDatabase):
    """PostgreSQL implementation"""
    
    def connect(self) -> bool:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            self.logger.info(f"Connecting to PostgreSQL at {self.config.get('host')}:{self.config.get('port', 5432)}")
            
            # Build connection parameters
            conn_params = {
                'host': self.config.get('host'),
                'port': self.config.get('port', 5432),
                'user': self.config.get('username'),
                'password': self.config.get('password'),
                'cursor_factory': RealDictCursor
            }
            
            # Add database if specified
            if self.config.get('database'):
                conn_params['database'] = self.config.get('database')
            
            # Add SSL if enabled
            if self.config.get('ssl_enabled', False):
                conn_params['sslmode'] = 'require'
                if self.config.get('ssl_cert'):
                    conn_params['sslcert'] = self.config.get('ssl_cert')
            
            self.connection = psycopg2.connect(**conn_params)
            self.logger.info("PostgreSQL connection established successfully")
            return True
            
        except ImportError:
            self.logger.error("psycopg2 module not found. Install with: pip install psycopg2-binary")
            raise DatabaseError("PostgreSQL driver not installed")
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL connection failed: {str(e)}")
            raise DatabaseError(f"PostgreSQL connection failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {str(e)}")
            raise DatabaseError(f"Connection error: {str(e)}")
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            try:
                self.connection.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing connection: {str(e)}")
        self.connection = None
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a SQL query"""
        if not self.is_connected():
            self.logger.error("Cannot execute query: Not connected to database")
            raise DatabaseError("Not connected to database")
        
        cursor = None
        try:
            with self.lock:
                cursor = self.connection.cursor()
                self.logger.debug(f"Executing query: {query[:100]}{'...' if len(query) > 100 else ''}")
                
                if params:
                    self.logger.debug(f"Query parameters: {params}")
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Handle different query types
                if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESC', 'DESCRIBE')):
                    result = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(result)} rows")
                    return result
                else:
                    self.connection.commit()
                    affected = cursor.rowcount
                    self.logger.debug(f"Query affected {affected} rows")
                    return affected
                    
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            self.logger.debug(f"Failed query: {query}")
            if params:
                self.logger.debug(f"Parameters: {params}")
            self.connection.rollback()
            raise DatabaseError(f"Query execution failed: {str(e)}")
        finally:
            if cursor:
                cursor.close()
    
    def execute_many(self, queries: List[str]):
        """Execute multiple SQL queries"""
        if not queries:
            self.logger.warning("No queries to execute")
            return
        
        self.logger.info(f"Executing {len(queries)} queries in batch")
        
        with self.lock:
            cursor = None
            try:
                cursor = self.connection.cursor()
                for i, query in enumerate(queries, 1):
                    try:
                        self.logger.debug(f"Executing query {i}/{len(queries)}: {query[:50]}...")
                        cursor.execute(query)
                    except Exception as e:
                        self.logger.error(f"Failed to execute query {i}: {str(e)}")
                        raise DatabaseError(f"Query {i} failed: {str(e)}")
                
                self.connection.commit()
                self.logger.info(f"Successfully executed {len(queries)} queries")
                
            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"Batch execution failed: {str(e)}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def get_databases(self) -> List[str]:
        """Get list of databases"""
        query = """
        SELECT datname 
        FROM pg_database 
        WHERE datistemplate = false
        AND datname NOT IN ('postgres', 'template0', 'template1')
        ORDER BY datname
        """
        try:
            result = self.execute_query(query)
            databases = [row['datname'] for row in result]
            self.logger.info(f"Found {len(databases)} databases")
            return databases
        except Exception as e:
            self.logger.error(f"Failed to get databases: {str(e)}")
            raise DatabaseError(f"Failed to get databases: {str(e)}")
    
    def get_schemas(self, database: str) -> List[str]:
        """Get list of schemas in database"""
        # First, switch to the specified database if we're not already connected to it
        current_db = self.connection.info.dbname if self.connection else None
        if current_db != database:
            self.logger.info(f"Switching from database '{current_db}' to '{database}'")
            try:
                self.disconnect()
                # Update config with new database
                self.config['database'] = database
                self.connect()
            except Exception as e:
                self.logger.error(f"Failed to switch to database '{database}': {str(e)}")
                raise DatabaseError(f"Failed to switch to database '{database}': {str(e)}")
        
        query = """
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name
        """
        try:
            result = self.execute_query(query)
            schemas = [row['schema_name'] for row in result]
            self.logger.info(f"Found {len(schemas)} schemas in database '{database}'")
            return schemas
        except Exception as e:
            self.logger.error(f"Failed to get schemas: {str(e)}")
            raise DatabaseError(f"Failed to get schemas: {str(e)}")
    
    def get_tables(self, schema: str) -> List[Dict[str, Any]]:
        """Get list of tables in schema"""
        query = """
        SELECT 
            table_name,
            table_type
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name
        """
        try:
            result = self.execute_query(query, (schema,))
            tables = [
                {
                    'name': row['table_name'],
                    'type': row['table_type'],
                    'schema': schema
                }
                for row in result
            ]
            self.logger.info(f"Found {len(tables)} tables in schema '{schema}'")
            return tables
        except Exception as e:
            self.logger.error(f"Failed to get tables for schema '{schema}': {str(e)}")
            raise DatabaseError(f"Failed to get tables: {str(e)}")
    
    def get_table_columns(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a specific table"""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            ordinal_position
        FROM information_schema.columns 
        WHERE table_schema = %s 
        AND table_name = %s
        ORDER BY ordinal_position
        """
        try:
            result = self.execute_query(query, (schema, table_name))
            columns = [
                {
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'is_nullable': row['is_nullable'],
                    'column_default': row['column_default'],
                    'character_maximum_length': row['character_maximum_length'],
                    'numeric_precision': row['numeric_precision'],
                    'numeric_scale': row['numeric_scale'],
                    'ordinal_position': row['ordinal_position']
                }
                for row in result
            ]
            self.logger.debug(f"Found {len(columns)} columns for table '{schema}.{table_name}'")
            return columns
        except Exception as e:
            self.logger.error(f"Failed to get columns for table '{schema}.{table_name}': {str(e)}")
            raise DatabaseError(f"Failed to get table columns: {str(e)}")
    
    def get_table_constraints(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get constraints for a specific table"""
        query = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        LEFT JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.table_schema = %s
        AND tc.table_name = %s
        ORDER BY tc.constraint_type, tc.constraint_name
        """
        try:
            result = self.execute_query(query, (schema, table_name))
            constraints = [
                {
                    'constraint_name': row['constraint_name'],
                    'constraint_type': row['constraint_type'],
                    'column_name': row['column_name'],
                    'foreign_table_schema': row['foreign_table_schema'],
                    'foreign_table_name': row['foreign_table_name'],
                    'foreign_column_name': row['foreign_column_name']
                }
                for row in result
            ]
            self.logger.debug(f"Found {len(constraints)} constraints for table '{schema}.{table_name}'")
            return constraints
        except Exception as e:
            self.logger.warning(f"Failed to get constraints for table '{schema}.{table_name}': {str(e)}")
            return []

class MySQLDatabase(BaseDatabase):
    """MySQL implementation"""
    
    def connect(self) -> bool:
        try:
            import mysql.connector
            from mysql.connector import Error
            
            self.logger.info(f"Connecting to MySQL at {self.config.get('host')}:{self.config.get('port', 3306)}")
            
            self.connection = mysql.connector.connect(
                host=self.config.get('host'),
                port=self.config.get('port', 3306),
                user=self.config.get('username'),
                password=self.config.get('password'),
                database=self.config.get('database'),
                autocommit=False
            )
            self.logger.info("MySQL connection established successfully")
            return True
        except ImportError:
            self.logger.error("mysql-connector-python module not found. Install with: pip install mysql-connector-python")
            raise DatabaseError("MySQL driver not installed")
        except Exception as e:
            self.logger.error(f"MySQL connection failed: {str(e)}")
            raise DatabaseError(f"MySQL connection failed: {str(e)}")
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                self.logger.info("MySQL connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing MySQL connection: {str(e)}")
        self.connection = None
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a SQL query"""
        if not self.connection or not self.connection.is_connected():
            self.logger.error("Cannot execute query: Not connected to database")
            raise DatabaseError("Not connected to database")
        
        cursor = None
        try:
            with self.lock:
                cursor = self.connection.cursor(dictionary=True)
                self.logger.debug(f"Executing MySQL query: {query[:100]}...")
                
                if params:
                    self.logger.debug(f"Query parameters: {params}")
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Handle different query types
                if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESC', 'DESCRIBE')):
                    result = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(result)} rows")
                    return result
                else:
                    self.connection.commit()
                    affected = cursor.rowcount
                    self.logger.debug(f"Query affected {affected} rows")
                    return affected
                    
        except Exception as e:
            self.logger.error(f"MySQL query execution failed: {str(e)}")
            self.connection.rollback()
            raise DatabaseError(f"Query execution failed: {str(e)}")
        finally:
            if cursor:
                cursor.close()
    
    def execute_many(self, queries: List[str]):
        """Execute multiple SQL queries"""
        if not queries:
            self.logger.warning("No queries to execute")
            return
        
        self.logger.info(f"Executing {len(queries)} MySQL queries in batch")
        
        with self.lock:
            cursor = None
            try:
                cursor = self.connection.cursor()
                for i, query in enumerate(queries, 1):
                    try:
                        self.logger.debug(f"Executing MySQL query {i}/{len(queries)}: {query[:50]}...")
                        cursor.execute(query)
                    except Exception as e:
                        self.logger.error(f"Failed to execute MySQL query {i}: {str(e)}")
                        raise DatabaseError(f"Query {i} failed: {str(e)}")
                
                self.connection.commit()
                self.logger.info(f"Successfully executed {len(queries)} MySQL queries")
                
            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"MySQL batch execution failed: {str(e)}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def get_databases(self) -> List[str]:
        """Get list of databases"""
        query = "SHOW DATABASES"
        try:
            result = self.execute_query(query)
            databases = [row['Database'] for row in result]
            self.logger.info(f"Found {len(databases)} MySQL databases")
            return databases
        except Exception as e:
            self.logger.error(f"Failed to get MySQL databases: {str(e)}")
            raise DatabaseError(f"Failed to get databases: {str(e)}")
    
    def get_schemas(self, database: str) -> List[str]:
        """Get list of schemas in database"""
        # In MySQL, schemas are equivalent to databases
        # We need to switch to the specified database
        try:
            self.connection.database = database
            self.logger.info(f"Switched to MySQL database '{database}'")
            
            # Get tables to infer schemas (in MySQL, each database is like a schema)
            query = "SHOW TABLES"
            result = self.execute_query(query)
            
            # Return the database name as the primary schema
            schemas = [database]
            self.logger.info(f"Using database '{database}' as schema in MySQL")
            return schemas
            
        except Exception as e:
            self.logger.error(f"Failed to switch to MySQL database '{database}': {str(e)}")
            raise DatabaseError(f"Failed to switch to database '{database}': {str(e)}")
    
    def get_tables(self, schema: str) -> List[Dict[str, Any]]:
        """Get list of tables in schema"""
        # In MySQL, schema is the database name
        try:
            self.connection.database = schema
            query = "SHOW TABLES"
            result = self.execute_query(query)
            
            tables = []
            for row in result:
                table_name = list(row.values())[0]  # Get the first column value
                tables.append({
                    'name': table_name,
                    'type': 'BASE TABLE',  # MySQL doesn't distinguish much in SHOW TABLES
                    'schema': schema
                })
            
            self.logger.info(f"Found {len(tables)} tables in MySQL schema '{schema}'")
            return tables
        except Exception as e:
            self.logger.error(f"Failed to get MySQL tables for schema '{schema}': {str(e)}")
            raise DatabaseError(f"Failed to get tables: {str(e)}")
    
    def get_table_columns(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a specific table"""
        try:
            self.connection.database = schema
            query = f"DESCRIBE `{table_name}`"
            result = self.execute_query(query)
            
            columns = []
            for row in result:
                columns.append({
                    'column_name': row['Field'],
                    'data_type': row['Type'],
                    'is_nullable': 'YES' if row['Null'] == 'YES' else 'NO',
                    'column_default': row['Default'],
                    'extra': row['Extra']
                })
            
            self.logger.debug(f"Found {len(columns)} columns for MySQL table '{schema}.{table_name}'")
            return columns
        except Exception as e:
            self.logger.error(f"Failed to get columns for MySQL table '{schema}.{table_name}': {str(e)}")
            raise DatabaseError(f"Failed to get table columns: {str(e)}")

class DatabaseFactory:
    """Factory for creating database instances"""
    
    @staticmethod
    def create_database(config: Dict[str, Any], ui) -> BaseDatabase:
        db_type = config.get('db_type', '').lower()
        logger = get_logger("DatabaseFactory")
        
        logger.info(f"Creating database instance of type: {db_type}")
        
        if db_type in ['postgresql', 'postgres']:
            logger.debug("Creating PostgreSQLDatabase instance")
            return PostgreSQLDatabase(config, ui)
        elif db_type in ['mysql', 'mariadb']:
            logger.debug("Creating MySQLDatabase instance")
            return MySQLDatabase(config, ui)
        # Add other database types here
        else:
            error_msg = f"Unsupported database type: {db_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)