"""
Input validation utilities
"""

import re
import ipaddress
from typing import Union, Optional, Callable, Any
from urllib.parse import urlparse
import socket

class ValidationError(Exception):
    """Custom validation exception"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)

def validate_hostname(hostname: str) -> bool:
    """
    Validate hostname or IP address
    
    Args:
        hostname: Hostname or IP to validate
        
    Returns:
        bool: True if valid
    """
    if not hostname or not isinstance(hostname, str):
        return False
    
    # Try to parse as IP address
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    
    # Validate as hostname
    if len(hostname) > 255:
        return False
    
    # Allow localhost
    if hostname.lower() == "localhost":
        return True
    
    # Validate hostname pattern
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    
    allowed = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$", re.IGNORECASE)
    return allowed.match(hostname) is not None

def validate_port(port: Union[int, str]) -> bool:
    """
    Validate port number
    
    Args:
        port: Port number to validate
        
    Returns:
        bool: True if valid
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False

def validate_database_name(name: str) -> bool:
    """
    Validate database name
    
    Args:
        name: Database name to validate
        
    Returns:
        bool: True if valid
    """
    if not name or not isinstance(name, str):
        return False
    
    # Length constraints
    if len(name) > 63:  # Common database limit
        return False
    
    # Check for valid characters (alphanumeric and underscores)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False
    
    # Check for reserved keywords (basic check)
    reserved_keywords = {
        'database', 'table', 'select', 'insert', 'update', 'delete',
        'create', 'drop', 'alter', 'where', 'from', 'into', 'values'
    }
    
    if name.lower() in reserved_keywords:
        return False
    
    return True

def validate_schema_name(name: str) -> bool:
    """
    Validate schema name
    
    Args:
        name: Schema name to validate
        
    Returns:
        bool: True if valid
    """
    # Schema names often have similar rules to database names
    return validate_database_name(name)

def validate_table_name(name: str) -> bool:
    """
    Validate table name
    
    Args:
        name: Table name to validate
        
    Returns:
        bool: True if valid
    """
    if not name or not isinstance(name, str):
        return False
    
    # Length constraints
    if len(name) > 128:  # Common table name limit
        return False
    
    # Check for valid characters
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False
    
    # Check for SQL injection patterns
    injection_patterns = [
        r'--', r'/\*', r'\*/', r';', r'\bUNION\b', r'\bSELECT\b.*\bFROM\b',
        r'\bINSERT\b', r'\bDELETE\b', r'\bDROP\b', r'\bUPDATE\b',
        r'\bALTER\b', r'\bCREATE\b'
    ]
    
    name_upper = name.upper()
    for pattern in injection_patterns:
        if re.search(pattern, name_upper, re.IGNORECASE):
            return False
    
    return True

def validate_connection_string(conn_str: str, db_type: str) -> bool:
    """
    Validate database connection string
    
    Args:
        conn_str: Connection string
        db_type: Database type
        
    Returns:
        bool: True if valid
    """
    if not conn_str or not isinstance(conn_str, str):
        return False
    
    db_type = db_type.lower()
    
    if db_type in ['postgresql', 'postgres']:
        pattern = r'^postgres(ql)?://[^:]+:[^@]+@[^:/]+(:\d+)?/[^?]+(\?.*)?$'
        return re.match(pattern, conn_str, re.IGNORECASE) is not None
    
    elif db_type in ['mysql', 'mariadb']:
        pattern = r'^mysql(://[^:]+:[^@]+@[^:/]+(:\d+)?/[^?]+(\?.*)?)?$'
        return re.match(pattern, conn_str, re.IGNORECASE) is not None
    
    return False

def validate_ssl_config(config: dict) -> bool:
    """
    Validate SSL configuration
    
    Args:
        config: SSL configuration dictionary
        
    Returns:
        bool: True if valid
    """
    if not isinstance(config, dict):
        return False
    
    ssl_enabled = config.get('ssl_enabled', False)
    
    if not ssl_enabled:
        return True
    
    # Check for required SSL files if enabled
    ssl_cert = config.get('ssl_cert')
    ssl_key = config.get('ssl_key')
    ssl_ca = config.get('ssl_ca')
    
    if ssl_cert:
        # Check if file exists and is readable
        import os
        if not os.path.exists(ssl_cert) or not os.access(ssl_cert, os.R_OK):
            return False
    
    return True

def validate_user_input(input_str: str, min_length: int = 1, 
                       max_length: int = 255, allowed_pattern: str = None) -> bool:
    """
    Validate general user input
    
    Args:
        input_str: Input string to validate
        min_length: Minimum length
        max_length: Maximum length
        allowed_pattern: Regex pattern for allowed characters
        
    Returns:
        bool: True if valid
    """
    if not isinstance(input_str, str):
        return False
    
    # Check length
    if not (min_length <= len(input_str) <= max_length):
        return False
    
    # Check pattern if provided
    if allowed_pattern:
        if not re.match(allowed_pattern, input_str):
            return False
    
    # Check for common injection patterns
    dangerous_patterns = [
        r'<script>', r'javascript:', r'onload=', r'onerror=',
        r'<?php', r'<\?', r'<%.*%>', r'--', r'/\*.*\*/',
        r'\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\b'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            return False
    
    return True

def validate_email(email: str) -> bool:
    """
    Validate email address
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """
    Validate URL
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_positive_number(value: Union[int, float, str]) -> bool:
    """
    Validate positive number
    
    Args:
        value: Number to validate
        
    Returns:
        bool: True if valid positive number
    """
    try:
        num = float(value) if isinstance(value, str) else value
        return num > 0
    except (ValueError, TypeError):
        return False

def validate_integer_range(value: Union[int, str], min_val: int, 
                          max_val: int) -> bool:
    """
    Validate integer within range
    
    Args:
        value: Integer to validate
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        bool: True if valid
    """
    try:
        num = int(value) if isinstance(value, str) else value
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False

class Validator:
    """Composite validator for multiple validation rules"""
    
    def __init__(self):
        self.rules = []
    
    def add_rule(self, rule_func: Callable, error_message: str, 
                field: Optional[str] = None):
        """Add a validation rule"""
        self.rules.append({
            'func': rule_func,
            'message': error_message,
            'field': field
        })
        return self
    
    def validate(self, value: Any) -> list:
        """
        Validate value against all rules
        
        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []
        
        for rule in self.rules:
            try:
                if not rule['func'](value):
                    errors.append({
                        'field': rule['field'],
                        'message': rule['message']
                    })
            except Exception as e:
                errors.append({
                    'field': rule['field'],
                    'message': f"Validation error: {str(e)}"
                })
        
        return errors
    
    @classmethod
    def create_database_validator(cls) -> 'Validator':
        """Create validator for database configuration"""
        validator = cls()
        
        validator.add_rule(
            lambda x: isinstance(x.get('host'), str) and x.get('host'),
            "Host is required",
            'host'
        ).add_rule(
            lambda x: validate_hostname(x.get('host', '')),
            "Invalid hostname or IP address",
            'host'
        ).add_rule(
            lambda x: validate_port(x.get('port', 0)),
            "Invalid port number",
            'port'
        ).add_rule(
            lambda x: isinstance(x.get('username'), str) and x.get('username'),
            "Username is required",
            'username'
        ).add_rule(
            lambda x: validate_user_input(x.get('username', ''), 1, 50, r'^[a-zA-Z0-9_]+$'),
            "Invalid username format",
            'username'
        ).add_rule(
            lambda x: validate_ssl_config(x),
            "Invalid SSL configuration",
            'ssl_config'
        )
        
        return validator