"""
UI Components for interactive console interface
"""

from typing import List, Optional, Callable, Any, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import box
import inquirer

class PaginatedTable:
    """Display paginated tables with navigation"""
    
    def __init__(self, title: str, headers: List[str], data: List[List[Any]], 
                 page_size: int = 10, console: Optional[Console] = None):
        self.title = title
        self.headers = headers
        self.data = data
        self.page_size = page_size
        self.console = console or Console()
        self.current_page = 0
        self.total_pages = max(1, (len(data) + page_size - 1) // page_size)
    
    def display(self, page: Optional[int] = None):
        """Display table for specific page"""
        if page is not None:
            self.current_page = max(0, min(page, self.total_pages - 1))
        
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.data))
        
        # Create table
        table = Table(title=f"{self.title} (Page {self.current_page + 1}/{self.total_pages})",
                     box=box.ROUNDED, show_lines=True)
        
        # Add headers
        for header in self.headers:
            table.add_column(header, style="cyan" if header == "#" else "white")
        
        # Add data rows
        for i in range(start_idx, end_idx):
            row = self.data[i]
            # Highlight every other row for readability
            style = "bright_white" if (i % 2) == 0 else "white"
            table.add_row(*[str(cell) for cell in row], style=style)
        
        self.console.print(table)
        
        # Display navigation instructions if there are multiple pages
        if self.total_pages > 1:
            self._display_navigation()
    
    def _display_navigation(self):
        """Display navigation controls"""
        nav_text = Text()
        nav_text.append("Navigation: ", style="bold cyan")
        
        if self.current_page > 0:
            nav_text.append("◀ Previous ", style="bold yellow")
        
        if self.current_page < self.total_pages - 1:
            nav_text.append("▶ Next ", style="bold yellow")
        
        nav_text.append("[N] Go to page ", style="bold white")
        nav_text.append("[Q] Back to menu", style="bold red")
        
        self.console.print(Panel(nav_text, border_style="blue"))
    
    def interactive_navigation(self) -> Optional[str]:
        """Handle interactive navigation"""
        while True:
            key = Prompt.ask(
                "Action",
                choices=['n', 'p', 'N', 'q', 'Q'] + [str(i) for i in range(1, self.total_pages + 1)],
                show_choices=False,
                default='q'
            ).lower()
            
            if key == 'q':
                return 'quit'
            elif key == 'n' and self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.display()
            elif key == 'p' and self.current_page > 0:
                self.current_page -= 1
                self.display()
            elif key.isdigit():
                page_num = int(key) - 1
                if 0 <= page_num < self.total_pages:
                    self.current_page = page_num
                    self.display()
            else:
                self.console.print("[yellow]Invalid option[/yellow]")
                continue

class DatabaseSelector:
    """Interactive database selector"""
    
    def __init__(self, databases: List[str], console: Console):
        self.databases = databases
        self.console = console
    
    def select(self) -> Optional[str]:
        """Select database interactively"""
        if not self.databases:
            self.console.print("[yellow]No databases available[/yellow]")
            return None
        
        # Use inquirer for selection
        questions = [
            inquirer.List(
                'database',
                message="Select a database",
                choices=self.databases,
                carousel=True
            )
        ]
        
        try:
            answers = inquirer.prompt(questions)
            if answers:
                self.console.print(f"[green]Selected database: {answers['database']}[/green]")
                return answers['database']
        except Exception as e:
            self.console.print(f"[red]Selection error: {str(e)}[/red]")
        
        return None

class SchemaSelector:
    """Interactive schema selector"""
    
    def __init__(self, schemas: List[str], console: Console):
        self.schemas = schemas
        self.console = console
    
    def select(self) -> Optional[str]:
        """Select schema interactively"""
        if not self.schemas:
            self.console.print("[yellow]No schemas available[/yellow]")
            return None
        
        # Add an "All" option
        choices = self.schemas.copy()
        choices.append("[ALL SCHEMAS]")
        
        questions = [
            inquirer.List(
                'schema',
                message="Select a schema (or ALL for all schemas)",
                choices=choices,
                carousel=True
            )
        ]
        
        try:
            answers = inquirer.prompt(questions)
            if answers:
                selected = answers['schema']
                if selected == "[ALL SCHEMAS]":
                    self.console.print("[green]Selected: All schemas[/green]")
                    return None  # Return None to indicate all schemas
                else:
                    self.console.print(f"[green]Selected schema: {selected}[/green]")
                    return selected
        except Exception as e:
            self.console.print(f"[red]Selection error: {str(e)}[/red]")
        
        return None

class ProgressDisplay:
    """Display progress with rich animations"""
    
    def __init__(self, console: Console):
        self.console = console
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def show_progress(self, title: str, total: int, 
                     callback: Callable[[int], Any]) -> Any:
        """Show progress bar for a task"""
        from rich.progress import Progress, SpinnerColumn, TextColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console,
            expand=True
        ) as progress:
            
            task = progress.add_task(f"[cyan]{title}", total=total)
            
            # Execute callback with progress updates
            result = callback(lambda inc: progress.update(task, advance=inc))
            
            progress.update(task, completed=total)
            
            return result

class ConfirmationDialog:
    """Interactive confirmation dialog"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def confirm_destructive_action(self, action: str, 
                                  details: Optional[str] = None) -> bool:
        """Confirm a destructive action with warning"""
        self.console.print("\n" + "="*60)
        self.console.print(f"[bold red]WARNING: DESTRUCTIVE ACTION[/bold red]")
        self.console.print("="*60)
        
        self.console.print(f"\n[bold]Action:[/bold] {action}")
        
        if details:
            self.console.print(f"\n[bold]Details:[/bold]")
            self.console.print(Panel(details, border_style="red"))
        
        self.console.print("\n[yellow]This action cannot be undone![/yellow]")
        
        # Require explicit confirmation
        confirmation = Prompt.ask(
            "Type 'YES' to confirm or anything else to cancel",
            default="NO"
        )
        
        return confirmation.upper() == "YES"

class QueryResultViewer:
    """Display SQL query results"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def display_results(self, results: List[Dict[str, Any]], 
                       title: str = "Query Results"):
        """Display query results in a table"""
        if not results:
            self.console.print("[yellow]No results found[/yellow]")
            return
        
        # Create table
        table = Table(title=title, box=box.ROUNDED, show_lines=True)
        
        # Add columns based on first result
        for column in results[0].keys():
            table.add_column(str(column), style="cyan")
        
        # Add rows
        for i, row in enumerate(results):
            style = "bright_white" if (i % 2) == 0 else "white"
            table.add_row(*[str(value) for value in row.values()], style=style)
        
        self.console.print(table)
        self.console.print(f"[green]Found {len(results)} row(s)[/green]")