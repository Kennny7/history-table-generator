"""
Main history table management logic
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .trigger_generator import TriggerGenerator
from utils.logger import get_logger

class HistoryManager:
    """Manages history table creation and triggers"""
    
    def __init__(self, database, ui, config: Dict[str, Any]):
        self.database = database
        self.ui = ui
        self.config = config
        self.logger = get_logger()
        self.trigger_gen = TriggerGenerator(database)
        self._changes_applied = []
        
    def preview_changes(self):
        """Preview changes without applying"""
        try:
            schema = self.ui.current_schema
            tables = self.database.get_tables(schema)
            
            if not tables:
                self.ui.display_message("No tables found in selected schema")
                return
            
            selected_tables = self.ui.select_tables(tables)
            
            if not selected_tables:
                self.ui.display_message("No tables selected")
                return
            
            self._display_preview(selected_tables, schema)
            
        except Exception as e:
            self.logger.error(f"Preview failed: {str(e)}")
            self.ui.display_error(f"Preview failed: {str(e)}")
    
    def apply_changes(self):
        """Apply history table changes"""
        try:
            schema = self.ui.current_schema
            tables = self.database.get_tables(schema)
            
            if not tables:
                self.ui.display_message("No tables found in selected schema")
                return
            
            selected_tables = self.ui.select_tables(tables)
            
            if not selected_tables:
                self.ui.display_message("No tables selected")
                return
            
            # Confirm action
            if not self.ui.confirm_action(
                f"Create history tables and triggers for {len(selected_tables)} tables?",
                default=False
            ):
                return
            
            # Backup if configured
            if self.config.get('app', {}).get('backup_before_changes', True):
                self._create_backup(selected_tables, schema)
            
            # Apply changes
            with self.database.transaction():
                for table_name in selected_tables:
                    self._create_history_table(table_name, schema)
                    self._create_triggers(table_name, schema)
            
            self.ui.display_message(
                f"Successfully created history for {len(selected_tables)} tables",
                "success"
            )
            
        except Exception as e:
            self.logger.error(f"Apply changes failed: {str(e)}")
            self.ui.display_error(f"Apply changes failed: {str(e)}")
            raise
    
    def rollback_changes(self):
        """Rollback applied changes"""
        try:
            if not self._changes_applied:
                self.ui.display_message("No changes to rollback")
                return
            
            self.ui.display_header("Rollback Changes")
            
            # Show changes that can be rolled back
            table = Table(title="Applied Changes", show_lines=True)
            table.add_column("#", style="cyan")
            table.add_column("Table", style="green")
            table.add_column("Schema", style="yellow")
            table.add_column("Action", style="white")
            table.add_column("Timestamp", style="blue")
            
            for i, change in enumerate(self._changes_applied, 1):
                table.add_row(
                    str(i),
                    change['table'],
                    change['schema'],
                    change['action'],
                    change['timestamp']
                )
            
            self.ui.console.print(table)
            
            if self.ui.confirm_action("Rollback all changes?", default=False):
                # Execute rollback queries
                pass
                
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            self.ui.display_error(f"Rollback failed: {str(e)}")
    
    def _create_history_table(self, table_name: str, schema: str):
        """Create history table for given table"""
        app_config = self.config.get('app', {})
        
        # Get original table structure
        columns = self.database.get_table_columns(schema, table_name)
        
        # Build history table creation query
        query = self.trigger_gen.generate_history_table_ddl(
            schema, table_name, columns, app_config
        )
        
        # Execute query
        self.database.execute_query(query)
        
        # Log change
        self._log_change(schema, table_name, "CREATE_HISTORY_TABLE")
    
    def _create_triggers(self, table_name: str, schema: str):
        """Create triggers for history table"""
        app_config = self.config.get('app', {})
        
        # Generate trigger queries
        queries = self.trigger_gen.generate_trigger_ddl(
            schema, table_name, app_config
        )
        
        # Execute queries
        for query in queries:
            self.database.execute_query(query)
        
        # Log change
        self._log_change(schema, table_name, "CREATE_TRIGGERS")
    
    def _display_preview(self, tables: List[str], schema: str):
        """Display preview of changes"""
        self.ui.display_header("Preview Changes")
        
        for table_name in tables:
            # Generate preview SQL
            columns = self.database.get_table_columns(schema, table_name)
            history_table_ddl = self.trigger_gen.generate_history_table_ddl(
                schema, table_name, columns, self.config.get('app', {})
            )
            trigger_ddl = self.trigger_gen.generate_trigger_ddl(
                schema, table_name, self.config.get('app', {})
            )
            
            # Display in panels
            self.ui.console.print(Panel(
                history_table_ddl,
                title=f"[bold]History Table: {table_name}[/bold]",
                border_style="cyan"
            ))
            
            for i, trigger in enumerate(trigger_ddl, 1):
                self.ui.console.print(Panel(
                    trigger,
                    title=f"[bold]Trigger {i}[/bold]",
                    border_style="yellow"
                ))
    
    def _create_backup(self, tables: List[str], schema: str):
        """Create backup of original tables"""
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Creating backup...", total=len(tables))
            
            backup_queries = []
            for table in tables:
                backup_queries.append(
                    self.trigger_gen.generate_backup_ddl(schema, table)
                )
                progress.update(task, advance=1)
        
        # Save to file
        with open(backup_file, 'w') as f:
            f.write('\n'.join(backup_queries))
        
        self.logger.info(f"Backup saved to {backup_file}")
    
    def _log_change(self, schema: str, table: str, action: str):
        """Log applied change"""
        change = {
            'schema': schema,
            'table': table,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'user': self.database.get_current_user()
        }
        self._changes_applied.append(change)
        
        # Also log to file
        self.logger.info(f"Applied {action} on {schema}.{table}")