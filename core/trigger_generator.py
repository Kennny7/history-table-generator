"""
Database-specific trigger generation
"""

from typing import List, Dict, Any
from abc import ABC, abstractmethod

class BaseTriggerGenerator(ABC):
    """Abstract base class for trigger generation"""
    
    def __init__(self, database):
        self.database = database
    
    @abstractmethod
    def generate_history_table_ddl(self, schema: str, table_name: str, 
                                   columns: List[Dict[str, Any]], 
                                   config: Dict[str, Any]) -> str:
        """Generate history table DDL"""
        pass
    
    @abstractmethod
    def generate_trigger_ddl(self, schema: str, table_name: str, 
                             config: Dict[str, Any]) -> List[str]:
        """Generate trigger DDL"""
        pass
    
    @abstractmethod
    def generate_backup_ddl(self, schema: str, table_name: str) -> str:
        """Generate backup DDL"""
        pass

class PostgreSQLTriggerGenerator(BaseTriggerGenerator):
    """PostgreSQL-specific trigger generator"""
    
    def generate_history_table_ddl(self, schema: str, table_name: str, 
                                   columns: List[Dict[str, Any]], 
                                   config: Dict[str, Any]) -> str:
        
        suffix = config.get('history_suffix', '_hst')
        history_table = f"{table_name}{suffix}"
        
        # Build column definitions
        column_defs = []
        for col in columns:
            col_def = f"{col['column_name']} {col['data_type']}"
            if col.get('is_nullable', 'YES') == 'NO':
                col_def += " NOT NULL"
            column_defs.append(col_def)
        
        # Add history columns
        column_defs.append(f"{config.get('timestamp_column', 'history_timestamp')} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        column_defs.append(f"{config.get('operation_column', 'history_operation')} VARCHAR(10)")
        column_defs.append(f"{config.get('user_column', 'history_user')} VARCHAR(100)")
        
        # Generate DDL
        ddl = f"""
CREATE TABLE IF NOT EXISTS {schema}.{history_table} (
    {',\n    '.join(column_defs)},
    PRIMARY KEY ({columns[0]['column_name']}, {config.get('timestamp_column', 'history_timestamp')})
);

COMMENT ON TABLE {schema}.{history_table} IS 'History table for {schema}.{table_name}';
        """
        
        return ddl.strip()
    
    def generate_trigger_ddl(self, schema: str, table_name: str, 
                             config: Dict[str, Any]) -> List[str]:
        
        suffix = config.get('history_suffix', '_hst')
        history_table = f"{table_name}{suffix}"
        
        trigger_function = f"""
CREATE OR REPLACE FUNCTION {schema}.{table_name}_history_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO {schema}.{history_table}
        SELECT OLD.*, 
               CURRENT_TIMESTAMP, 
               'DELETE', 
               CURRENT_USER;
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO {schema}.{history_table}
        SELECT OLD.*, 
               CURRENT_TIMESTAMP, 
               'UPDATE', 
               CURRENT_USER;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
        """
        
        create_trigger = f"""
CREATE TRIGGER {table_name}_history_trigger
AFTER UPDATE OR DELETE ON {schema}.{table_name}
FOR EACH ROW
EXECUTE FUNCTION {schema}.{table_name}_history_trigger();
        """
        
        return [trigger_function.strip(), create_trigger.strip()]
    
    def generate_backup_ddl(self, schema: str, table_name: str) -> str:
        """Generate backup DDL for PostgreSQL"""
        return f"\\copy {schema}.{table_name} TO 'backup_{schema}_{table_name}.csv' CSV HEADER;"

class TriggerGenerator:
    """Factory for trigger generators"""
    
    def __init__(self, database):
        self.database = database
        
        # Map database types to generators
        self._generators = {
            'postgresql': PostgreSQLTriggerGenerator,
            'mysql': None,  # Add MySQL generator
            'sqlserver': None  # Add SQL Server generator
        }
        
    def _get_generator(self):
        """Get appropriate trigger generator"""
        db_type = self.database.config.get('db_type', '').lower()
        generator_class = self._generators.get(db_type)
        
        if not generator_class:
            raise ValueError(f"No trigger generator for database type: {db_type}")
        
        return generator_class(self.database)
    
    def generate_history_table_ddl(self, *args, **kwargs):
        generator = self._get_generator()
        return generator.generate_history_table_ddl(*args, **kwargs)
    
    def generate_trigger_ddl(self, *args, **kwargs):
        generator = self._get_generator()
        return generator.generate_trigger_ddl(*args, **kwargs)
    
    def generate_backup_ddl(self, *args, **kwargs):
        generator = self._get_generator()
        return generator.generate_backup_ddl(*args, **kwargs)