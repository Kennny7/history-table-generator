"""
Rich-based console user interface
"""

from typing import List, Dict, Any, Optional, Callable
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
import inquirer

from .components import PaginatedTable, DatabaseSelector, SchemaSelector

class ConsoleUI:
    """Main UI controller"""
    
    def __init__(self):
        self.console = Console()
        self.current_database = None
        self.current_schema = None
        
    def display_header(self, title: str):
        """Display application header"""
        self.console.clear()
        self.console.rule(f"[bold blue]{title}[/bold blue]")
        print()
    
    def get_database_config(self, default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get database configuration interactively"""
        self.display_header("Database Configuration")
        
        questions = [
            inquirer.List('db_type',
                message="Select database type",
                choices=['PostgreSQL', 'MySQL', 'SQL Server', 'SQLite', 'Oracle'],
                default=default_config.get('database', {}).get('type', 'PostgreSQL')
            ),
            inquirer.Text('host',
                message="Host address",
                default=default_config.get('database', {}).get('host', 'localhost')
            ),
            inquirer.Text('port',
                message="Port",
                default=default_config.get('database', {}).get('port', 
                    {'PostgreSQL': '5432', 'MySQL': '3306', 'SQL Server': '1433'}.get(
                        default_config.get('database', {}).get('type', 'PostgreSQL'), '5432'
                    )
                )
            ),
            inquirer.Text('username',
                message="Username",
                default=default_config.get('database', {}).get('username', '')
            ),
            inquirer.Password('password',
                message="Password"
            ),
            inquirer.Confirm('ssl',
                message="Use SSL?",
                default=default_config.get('database', {}).get('ssl', False)
            )
        ]
        
        answers = inquirer.prompt(questions)
        
        config = {
            'db_type': answers['db_type'].lower(),
            'host': answers['host'],
            'port': int(answers['port']),
            'username': answers['username'],
            'password': answers['password'],
            'ssl_enabled': answers['ssl']
        }
        
        return config
    
    def select_database_and_schema(self, database) -> bool:
        """Interactive database and schema selection"""
        try:
            # Select database
            databases = database.get_databases()
            if not databases:
                self.display_error("No databases found")
                return False
            
            db_selector = DatabaseSelector(databases, self.console)
            selected_db = db_selector.select()
            
            if not selected_db:
                return False
            
            self.current_database = selected_db
            
            # Select schema
            schemas = database.get_schemas(selected_db)
            if not schemas:
                self.display_error("No schemas found")
                return False
            
            schema_selector = SchemaSelector(schemas, self.console)
            selected_schema = schema_selector.select()
            
            if not selected_schema:
                return False
            
            self.current_schema = selected_schema
            return True
            
        except Exception as e:
            self.display_error(f"Selection failed: {str(e)}")
            return False
    
    def select_tables(self, tables: List[Dict[str, Any]]) -> List[str]:
        """Select tables for history creation"""
        self.display_header("Table Selection")
        
        table_data = []
        for i, table in enumerate(tables, 1):
            table_data.append([
                str(i),
                table['name'],
                table['type'],
                table.get('schema', 'N/A')
            ])
        
        paginated_table = PaginatedTable(
            title="Available Tables",
            headers=["#", "Table Name", "Type", "Schema"],
            data=table_data,
            page_size=15
        )
        
        paginated_table.display()
        
        print("\n[bold cyan]Select tables:[/bold cyan]")
        print("  • Enter table numbers (comma-separated)")
        print("  • Use 'all' for all tables")
        print("  • Use ranges like '1-5,10'")
        print("  • Press Enter to skip")
        
        selection = Prompt.ask("\nYour selection")
        
        if not selection:
            return []
        
        if selection.lower() == 'all':
            return [table['name'] for table in tables]
        
        # Parse selection
        selected_indices = self._parse_selection(selection, len(tables))
        return [tables[i-1]['name'] for i in selected_indices]
    
    def main_menu(self) -> str:
        """Display main menu"""
        self.display_header("History Table Generator")
        
        menu = Table(title="Main Menu", show_header=False, box=None)
        menu.add_column("Option", style="cyan")
        menu.add_column("Description", style="white")
        
        menu.add_row("1", "Preview changes")
        menu.add_row("2", "Apply changes")
        menu.add_row("3", "Rollback changes")
        menu.add_row("4", "Configure settings")
        menu.add_row("5", "Exit")
        
        self.console.print(menu)
        print()
        
        choices = ["1", "2", "3", "4", "5"]
        choice = Prompt.ask(
            "Select option",
            choices=choices,
            show_choices=False
        )
        
        return choice
    
    def display_message(self, message: str, msg_type: str = "info"):
        """Display formatted message"""
        colors = {
            "info": "green",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }
        
        color = colors.get(msg_type, "white")
        panel = Panel(
            message,
            title=msg_type.upper(),
            border_style=color,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def display_error(self, error: str):
        """Display error message"""
        self.display_message(error, "error")
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirm an action"""
        return Confirm.ask(f"[yellow]{message}[/yellow]", default=default)
    
    def _parse_selection(self, selection: str, max_items: int) -> List[int]:
        """Parse user selection string"""
        selected = set()
        parts = selection.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                selected.update(range(start, end + 1))
            elif part.isdigit():
                selected.add(int(part))
        
        # Filter valid indices
        return [i for i in selected if 1 <= i <= max_items]