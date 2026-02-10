"""
Database models and data classes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json

class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    MARIADB = "mariadb"

class TableType(Enum):
    """Table types"""
    TABLE = "TABLE"
    VIEW = "VIEW"
    SYSTEM_TABLE = "SYSTEM TABLE"
    GLOBAL_TEMPORARY = "GLOBAL TEMPORARY"
    LOCAL_TEMPORARY = "LOCAL TEMPORARY"
    ALIAS = "ALIAS"
    SYNONYM = "SYNONYM"

class ColumnDataType(Enum):
    """Common column data types"""
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    REAL = "REAL"
    DOUBLE = "DOUBLE"
    FLOAT = "FLOAT"
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    INTERVAL = "INTERVAL"
    JSON = "JSON"
    JSONB = "JSONB"
    UUID = "UUID"
    BYTEA = "BYTEA"
    BLOB = "BLOB"
    CLOB = "CLOB"

@dataclass
class ColumnDefinition:
    """Column definition model"""
    name: str
    data_type: str
    is_nullable: bool = True
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    check_constraint: Optional[str] = None
    comment: Optional[str] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    
    def to_sql(self, db_type: DatabaseType) -> str:
        """Convert to SQL definition"""
        # Base column definition
        sql = f"{self.name} {self.data_type}"
        
        # Add length/precision if specified
        if self.length and 'VARCHAR' in self.data_type.upper():
            sql += f"({self.length})"
        elif self.precision and self.scale and 'DECIMAL' in self.data_type.upper():
            sql += f"({self.precision},{self.scale})"
        elif self.precision and 'NUMERIC' in self.data_type.upper():
            sql += f"({self.precision})"
        
        # Add constraints
        if not self.is_nullable:
            sql += " NOT NULL"
        
        if self.default_value:
            sql += f" DEFAULT {self.default_value}"
        
        if self.is_unique:
            sql += " UNIQUE"
        
        return sql
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnDefinition':
        """Create from dictionary"""
        return cls(
            name=data.get('column_name', ''),
            data_type=data.get('data_type', ''),
            is_nullable=data.get('is_nullable', 'YES') == 'YES',
            default_value=data.get('column_default'),
            is_primary_key=data.get('is_primary_key', False),
            is_foreign_key=data.get('is_foreign_key', False),
            is_unique=data.get('is_unique', False),
            check_constraint=data.get('check_constraint'),
            comment=data.get('comment'),
            length=data.get('character_maximum_length'),
            precision=data.get('numeric_precision'),
            scale=data.get('numeric_scale')
        )

@dataclass
class TableDefinition:
    """Table definition model"""
    name: str
    schema_name: str
    columns: List[ColumnDefinition] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    table_type: TableType = TableType.TABLE
    comment: Optional[str] = None
    row_count: Optional[int] = None
    size_mb: Optional[float] = None
    
    def get_column_names(self) -> List[str]:
        """Get list of column names"""
        return [col.name for col in self.columns]
    
    def get_primary_key_columns(self) -> List[ColumnDefinition]:
        """Get primary key columns"""
        return [col for col in self.columns if col.is_primary_key]
    
    def to_create_sql(self, db_type: DatabaseType) -> str:
        """Generate CREATE TABLE SQL"""
        # Column definitions
        column_defs = [col.to_sql(db_type) for col in self.columns]
        
        # Primary key constraint
        if self.primary_keys:
            pk_def = f"PRIMARY KEY ({', '.join(self.primary_keys)})"
            column_defs.append(pk_def)
        
        # Foreign key constraints
        for fk in self.foreign_keys:
            fk_def = f"FOREIGN KEY ({fk['column_name']}) "
            fk_def += f"REFERENCES {fk['referenced_table']}({fk['referenced_column']})"
            if fk.get('on_delete'):
                fk_def += f" ON DELETE {fk['on_delete']}"
            if fk.get('on_update'):
                fk_def += f" ON UPDATE {fk['on_update']}"
            column_defs.append(fk_def)
        
        # Build SQL
        sql = f"CREATE TABLE {self.schema_name}.{self.name} (\n"
        sql += ",\n".join(f"    {defn}" for defn in column_defs)
        sql += "\n);"
        
        # Add comment if exists
        if self.comment:
            if db_type == DatabaseType.POSTGRESQL:
                sql += f"\nCOMMENT ON TABLE {self.schema_name}.{self.name} "
                sql += f"IS '{self.comment}';"
        
        return sql
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableDefinition':
        """Create from dictionary"""
        columns = [
            ColumnDefinition.from_dict(col_data) 
            for col_data in data.get('columns', [])
        ]
        
        return cls(
            name=data['name'],
            schema_name=data.get('schema_name', 'public'),
            columns=columns,
            primary_keys=data.get('primary_keys', []),
            foreign_keys=data.get('foreign_keys', []),
            indexes=data.get('indexes', []),
            table_type=TableType(data.get('table_type', 'TABLE')),
            comment=data.get('comment'),
            row_count=data.get('row_count'),
            size_mb=data.get('size_mb')
        )

@dataclass
class HistoryTableDefinition(TableDefinition):
    """History table definition (extends TableDefinition)"""
    original_table: str
    history_suffix: str = "_hst"
    timestamp_column: str = "history_timestamp"
    operation_column: str = "history_operation"
    user_column: str = "history_user"
    
    def __post_init__(self):
        """Add history-specific columns after initialization"""
        # Add history columns if not already present
        history_columns = [
            ColumnDefinition(
                name=self.timestamp_column,
                data_type="TIMESTAMP",
                default_value="CURRENT_TIMESTAMP"
            ),
            ColumnDefinition(
                name=self.operation_column,
                data_type="VARCHAR(10)"
            ),
            ColumnDefinition(
                name=self.user_column,
                data_type="VARCHAR(100)"
            )
        ]
        
        # Check if history columns already exist
        existing_names = {col.name for col in self.columns}
        for hcol in history_columns:
            if hcol.name not in existing_names:
                self.columns.append(hcol)

@dataclass
class TriggerDefinition:
    """Trigger definition model"""
    name: str
    table_name: str
    schema_name: str
    timing: str  # BEFORE, AFTER, INSTEAD OF
    events: List[str]  # INSERT, UPDATE, DELETE
    function_name: str
    function_body: str
    enabled: bool = True
    comment: Optional[str] = None
    
    def to_create_sql(self, db_type: DatabaseType) -> str:
        """Generate CREATE TRIGGER SQL"""
        if db_type == DatabaseType.POSTGRESQL:
            # Create function first
            sql = f"CREATE OR REPLACE FUNCTION {self.schema_name}.{self.function_name}()\n"
            sql += f"RETURNS TRIGGER AS $$\n"
            sql += f"BEGIN\n"
            sql += f"{self.function_body}\n"
            sql += f"END;\n"
            sql += f"$$ LANGUAGE plpgsql;\n\n"
            
            # Create trigger
            sql += f"CREATE TRIGGER {self.name}\n"
            sql += f"{' '.join(self.events)} ON {self.schema_name}.{self.table_name}\n"
            sql += f"FOR EACH ROW\n"
            sql += f"EXECUTE FUNCTION {self.schema_name}.{self.function_name}();"
            
            return sql
        else:
            # Generic SQL for other databases
            events_str = " OR ".join(self.events)
            sql = f"CREATE TRIGGER {self.name}\n"
            sql += f"{self.timing} {events_str} ON {self.schema_name}.{self.table_name}\n"
            sql += f"FOR EACH ROW\n"
            sql += f"{self.function_body}"
            
            return sql

@dataclass
class DatabaseConnection:
    """Database connection model"""
    db_type: DatabaseType
    host: str
    port: int
    username: str
    password: str
    database: Optional[str] = None
    schema: Optional[str] = None
    ssl_enabled: bool = False
    ssl_cert: Optional[str] = None
    timeout: int = 30
    pool_size: int = 5
    connection_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    
    def get_connection_string(self) -> str:
        """Get connection string for database"""
        if self.db_type == DatabaseType.POSTGRESQL:
            conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}"
            if self.database:
                conn_str += f"/{self.database}"
            if self.ssl_enabled:
                conn_str += "?sslmode=require"
            return conn_str
        elif self.db_type == DatabaseType.MYSQL:
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"{self.db_type.value}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """Convert to dictionary (optionally excluding password)"""
        data = {
            'db_type': self.db_type.value,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'database': self.database,
            'schema': self.schema,
            'ssl_enabled': self.ssl_enabled,
            'ssl_cert': self.ssl_cert,
            'timeout': self.timeout,
            'pool_size': self.pool_size,
            'connection_id': self.connection_id,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None
        }
        
        if include_password:
            data['password'] = self.password
        
        return data

@dataclass
class OperationLog:
    """Operation log model"""
    id: str
    operation_type: str  # CREATE_HISTORY, DROP_TRIGGER, etc.
    schema_name: str
    table_name: str
    status: str  # SUCCESS, FAILED, PENDING
    sql_statements: List[str]
    executed_by: str
    executed_at: datetime
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    rollback_sql: Optional[List[str]] = None
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        data = {
            'id': self.id,
            'operation_type': self.operation_type,
            'schema_name': self.schema_name,
            'table_name': self.table_name,
            'status': self.status,
            'sql_statements': self.sql_statements,
            'executed_by': self.executed_by,
            'executed_at': self.executed_at.isoformat(),
            'duration_ms': self.duration_ms,
            'error_message': self.error_message,
            'rollback_sql': self.rollback_sql
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'OperationLog':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(
            id=data['id'],
            operation_type=data['operation_type'],
            schema_name=data['schema_name'],
            table_name=data['table_name'],
            status=data['status'],
            sql_statements=data['sql_statements'],
            executed_by=data['executed_by'],
            executed_at=datetime.fromisoformat(data['executed_at']),
            duration_ms=data.get('duration_ms'),
            error_message=data.get('error_message'),
            rollback_sql=data.get('rollback_sql')
        )

@dataclass
class ApplicationConfig:
    """Application configuration model"""
    # History table settings
    history_suffix: str = "_hst"
    timestamp_column: str = "history_timestamp"
    operation_column: str = "history_operation"
    user_column: str = "history_user"
    
    # Behavior settings
    include_system_tables: bool = False
    include_views: bool = False
    auto_commit: bool = False
    backup_before_changes: bool = True
    default_schema: str = "public"
    
    # Performance settings
    max_retries: int = 3
    retry_delay: int = 2
    query_timeout: int = 30
    connection_pool_size: int = 5
    
    # UI settings
    page_size: int = 15
    show_progress: bool = True
    color_scheme: str = "default"
    confirm_destructive: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/history_generator.log"
    max_log_size_mb: int = 10
    log_backup_count: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'history_suffix': self.history_suffix,
            'timestamp_column': self.timestamp_column,
            'operation_column': self.operation_column,
            'user_column': self.user_column,
            'include_system_tables': self.include_system_tables,
            'include_views': self.include_views,
            'auto_commit': self.auto_commit,
            'backup_before_changes': self.backup_before_changes,
            'default_schema': self.default_schema,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'query_timeout': self.query_timeout,
            'connection_pool_size': self.connection_pool_size,
            'page_size': self.page_size,
            'show_progress': self.show_progress,
            'color_scheme': self.color_scheme,
            'confirm_destructive': self.confirm_destructive,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'max_log_size_mb': self.max_log_size_mb,
            'log_backup_count': self.log_backup_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})