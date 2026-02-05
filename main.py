#!/usr/bin/env python3
"""
Main entry point for History Table Generator
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from ui.console_ui import ConsoleUI
from core.database import DatabaseFactory
from core.history_manager import HistoryManager
from config.settings import ConfigManager
from utils.logger import setup_logger

def main():
    """Main application entry point"""
    try:
        # Setup logging
        logger = setup_logger()
        logger.info("Starting History Table Generator")
        
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize UI
        ui = ConsoleUI()
        
        # Get database connection details
        db_config = ui.get_database_config(config)
        
        # Connect to database
        db_factory = DatabaseFactory()
        database = db_factory.create_database(db_config, ui)
        
        if not database.connect():
            ui.display_error("Failed to connect to database")
            return
        
        # Select database and schema
        if not ui.select_database_and_schema(database):
            ui.display_error("Database/schema selection cancelled")
            database.disconnect()
            return
        
        # Initialize history manager
        history_manager = HistoryManager(database, ui, config)
        
        # Main workflow
        while True:
            choice = ui.main_menu()
            
            if choice == "1":  # Preview changes
                history_manager.preview_changes()
            elif choice == "2":  # Apply changes
                history_manager.apply_changes()
            elif choice == "3":  # Rollback changes
                history_manager.rollback_changes()
            elif choice == "4":  # Configure settings
                config_manager.update_interactive_config()
            elif choice == "5":  # Exit
                ui.display_message("Goodbye!")
                break
        
        database.disconnect()
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()