"""
Configuration management module
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    SQLITE = "sqlite"
    ORACLE = "oracle"

@dataclass
class DatabaseConfig:
    """Database configuration dataclass"""
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

@dataclass
class AppConfig:
    """Application configuration dataclass"""
    history_suffix: str = "_hst"
    timestamp_column: str = "history_timestamp"
    operation_column: str = "history_operation"
    user_column: str = "history_user"
    include_system_tables: bool = False
    include_views: bool = False
    auto_commit: bool = False
    backup_before_changes: bool = True
    default_schema: str = "public"
    max_retries: int = 3
    retry_delay: int = 2

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.yaml"
        self.config: Dict[str, Any] = {}
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            
            # Set defaults if not present
            defaults = {
                'app': asdict(AppConfig()),
                'database': {},
                'logging': {
                    'level': 'INFO',
                    'file': 'logs/history_generator.log',
                    'max_size_mb': 10,
                    'backup_count': 5
                }
            }
            
            # Merge with defaults
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
                elif isinstance(value, dict):
                    self.config[key] = {**value, **self.config[key]}
            
            return self.config
            
        except Exception as e:
            raise Exception(f"Failed to load configuration: {str(e)}")
    
    def save_config(self):
        """Save configuration to YAML file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
                
        except Exception as e:
            raise Exception(f"Failed to save configuration: {str(e)}")
    
    def update_interactive_config(self):
        """Update configuration interactively"""
        from rich.prompt import Prompt, Confirm
        
        print("\n[bold cyan]Configuration Update[/bold cyan]")
        
        # Update app config
        app_config = self.config.get('app', {})
        
        app_config['history_suffix'] = Prompt.ask(
            "History table suffix",
            default=app_config.get('history_suffix', '_hst')
        )
        
        app_config['auto_commit'] = Confirm.ask(
            "Auto-commit changes?",
            default=app_config.get('auto_commit', False)
        )
        
        self.config['app'] = app_config
        self.save_config()
        print("[green]Configuration updated successfully![/green]")