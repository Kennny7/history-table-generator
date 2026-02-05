# 🗃️ History Table Generator



<div align="center">



![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

![License](https://img.shields.io/badge/License-MIT-green)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-blue)

![MySQL](https://img.shields.io/badge/MySQL-Supported-orange)

![Rich](https://img.shields.io/badge/UI-Rich%20Terminal-ff69b4)



**Automated History Table & Trigger Management System**



[![License](https://img.shields.io/badge/LICENSE-MIT-blue?style=for-the-badge)](LICENSE)

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://python.org)

[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black?style=for-the-badge)](https://github.com/psf/black)



</div>



## ✨ Overview



**History Table Generator** is a sophisticated, production-grade tool that automates the creation of audit trails for your database tables. Never lose track of data changes again! With an elegant terminal interface powered by Rich, this tool automatically generates history tables with comprehensive triggers for UPDATE and DELETE operations, complete with metadata about who changed what and when.



Think of it as a **time machine for your data** – preserving every change while keeping your application logic clean and simple.



## 🚀 Features



### 🎯 **Core Capabilities**

- **Automated History Tables**: Create audit tables with a single command

- **Multi-Database Support**: PostgreSQL, MySQL, SQL Server, and more

- **Smart Triggers**: Automatic trigger generation for UPDATE/DELETE operations

- **Interactive UI**: Beautiful terminal interface with pagination and navigation

- **Transaction Safe**: Rollback support and preview before applying



### 🛡️ **Safety First**

- **Preview Mode**: See exactly what will be created before making changes

- **Auto-Backup**: Automatic backups before any modifications

- **Transaction Management**: Full ACID compliance with rollback capability

- **Validation**: Comprehensive validation of all operations



### 🎨 **User Experience**

- **Rich Terminal UI**: Colorful, interactive interface with progress bars

- **Intuitive Navigation**: Move freely between options with keyboard

- **Pagination**: Handle large databases with ease

- **Real-time Feedback**: Immediate feedback on all operations



## 📋 Prerequisites



- Python 3.8 or higher

- Database server (PostgreSQL, MySQL, etc.)

- Required permissions to create tables and triggers

- 100MB free disk space



## 🔧 Installation



### Quick Install (Recommended)



```bash

# Clone the repository

git clone https://github.com/yourusername/history-table-generator.git

cd history-table-generator



# Create virtual environment

python -m venv venv



# Activate virtual environment

# On Windows:

venvScriptsactivate

# On macOS/Linux:

source venv/bin/activate



# Install dependencies

pip install -r requirements.txt

```



### Docker Installation



```bash

# Build and run with Docker

docker build -t history-generator .

docker run -it --rm history-generator

```



## ⚙️ Configuration



<details>

<summary><b>📁 Default Configuration Structure</b></summary>



```yaml

app:

&nbsp; # History table naming convention

&nbsp; history_suffix: "_hst"           # Suffix for history tables

&nbsp; timestamp_column: "history_timestamp"  # Column for change timestamp

&nbsp; operation_column: "history_operation"  # Column for operation type

&nbsp; user_column: "history_user"      # Column for user who made change

&nbsp; 

&nbsp; # Behavior settings

&nbsp; include_system_tables: false     # Include system/internal tables

&nbsp; include_views: false             # Include database views

&nbsp; auto_commit: false               # Auto-commit changes (false for safety)

&nbsp; backup_before_changes: true      # Create backup before modifications

&nbsp; default_schema: "public"         # Default schema to use

&nbsp; 

&nbsp; # Performance settings

&nbsp; max_retries: 3                   # Max retries for failed operations

&nbsp; retry_delay: 2                   # Delay between retries (seconds)



database:

&nbsp; # Connection settings (can be overridden at runtime)

&nbsp; type: "postgresql"              # postgresql, mysql, sqlserver, sqlite

&nbsp; host: "localhost"               # Database host

&nbsp; port: 5432                      # Default port for database type

&nbsp; timeout: 30                     # Connection timeout in seconds

&nbsp; pool_size: 5                    # Connection pool size



logging:

&nbsp; level: "INFO"                   # DEBUG, INFO, WARNING, ERROR

&nbsp; file: "logs/history_generator.log"  # Log file location

&nbsp; max_size_mb: 10                 # Max log file size

&nbsp; backup_count: 5                 # Number of backup logs to keep

&nbsp; format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

```



</details>



## 🎮 Usage



### First-Time Setup



1. **Start the application**:

&nbsp;  ```bash

&nbsp;  python main.py

&nbsp;  ```



2. **Configure database connection**:

&nbsp;  - Select your database type (PostgreSQL, MySQL, etc.)

&nbsp;  - Enter connection details (host, port, credentials)

&nbsp;  - Test connection immediately



3. **Select database and schema**:

&nbsp;  - Browse available databases with pagination

&nbsp;  - Navigate with arrow keys and Enter

&nbsp;  - Select the target schema



### Main Workflow



<details>

<summary><b>📊 Preview Mode (Safe)</b></summary>



**Use this to see what will be created without making changes:**



```bash

┌─────────────────────────────────────────────────────────────┐

│                     PREVIEW MODE                            │

├─────────────────────────────────────────────────────────────┤

│                                                             │

│  • Shows exact SQL that will be executed                    │

│  • Displays history table structure                         │

│  • Shows trigger definitions                                │

│  • No changes are made to database                          │

│                                                             │

│  Perfect for:                                               │

│    - Review before production                               │

│    - Getting approval from DBA                              │

│    - Understanding the impact                               │

│                                                             │

└─────────────────────────────────────────────────────────────┘

```



</details>



<details>

<summary><b>⚡ Apply Changes</b></summary>



**Apply history tables and triggers to selected tables:**



```bash

┌─────────────────────────────────────────────────────────────┐

│                     APPLY CHANGES                           │

├─────────────────────────────────────────────────────────────┤

│                                                             │

│  1. Select tables (interactive checkbox interface)          │

│  2. Confirm action (safety check)                           │

│  3. Automatic backup creation (if enabled)                  │

│  4. Transaction begins                                      │

│  5. History tables created                                  │

│  6. Triggers created and enabled                            │

│  7. Transaction commits                                     │

│  8. Success summary displayed                               │

│                                                             │

│  Features:                                                  │

│    • Progress bars for long operations                      │

│    • Real-time status updates                               │

│    • Automatic error recovery                               │

│    • Detailed completion report                             │

│                                                             │

└─────────────────────────────────────────────────────────────┘

```



</details>



<details>

<summary><b>↩️ Rollback Changes</b></summary>



**Undo previously applied changes:**



```bash

┌─────────────────────────────────────────────────────────────┐

│                     ROLLBACK                                │

├─────────────────────────────────────────────────────────────┤

│                                                             │

│  What can be rolled back:                                   │

│    • History tables (dropped)                               │

│    • Triggers (dropped)                                     │

│    • Backup restoration (optional)                          │

│                                                             │

│  Safety features:                                           │

│    • Shows what will be removed                             │

│    • Requires confirmation                                  │

│    • Transaction protected                                  │

│    • Logs all rollback actions                              │

│                                                             │

│  Note: Original table data is never affected               │

│                                                             │

└─────────────────────────────────────────────────────────────┘

```



</details>



## 📁 Project Structure



<details>

<summary><b>Click to expand project structure</b></summary>



```

history_table_generator/

│

├── main.py                          # Application entry point

├── requirements.txt                 # Python dependencies

├── LICENSE                          # MIT License

│

├── config/                          # Configuration management

│   ├── __init__.py

│   ├── settings.py                  # Config classes and managers

│   └── config.yaml                  # Default configuration

│

├── core/                            # Business logic core

│   ├── __init__.py

│   ├── database.py                  # Database abstraction layer

│   ├── history_manager.py           # Main history table logic

│   └── trigger_generator.py         # Database-specific SQL generation

│

├── ui/                              # User interface

│   ├── __init__.py

│   ├── console_ui.py                # Main UI controller

│   └── components.py                # Reusable UI components

│

├── utils/                           # Utilities and helpers

│   ├── __init__.py

│   ├── logger.py                    # Logging configuration

│   ├── validators.py                # Input validation

│   └── decorators.py                # Python decorators

│

├── models/                          # Data models

│   ├── __init__.py

│   └── database_models.py           # Database schema models

│

├── scripts/                         # Utility scripts

│   ├── sample_config.yaml           # Example configuration

│   ├── backup_cleanup.py            # Backup management

│   └── health_check.py              # System health checks

│

├── logs/                            # Application logs (auto-created)

│   └── .gitkeep

│

├── backups/                         # Automatic backups (auto-created)

│   └── .gitkeep

│

└── tests/                           # Test suite

&nbsp;   ├── __init__.py

&nbsp;   ├── test_database.py

&nbsp;   ├── test_history_manager.py

&nbsp;   └── test_ui.py

```



</details>



## 🎨 User Interface Guide



### Navigation Controls



```

┌─────────────────────────────────────────────────────────────┐

│                   NAVIGATION GUIDE                          │

├─────────────────────────────────────────────────────────────┤

│                                                             │

│  ↑/↓ : Move selection up/down                              │

│  ←/→ : Previous/Next page (when paginated)                 │

│  Enter : Select/Confirm                                    │

│  Space : Toggle selection (in multi-select)                │

│  Tab : Move between form fields                            │

│  Ctrl+C : Cancel/Exit                                      │

│  F1 : Help                                                 │

│                                                             │

│  Color Guide:                                              │

│    • Green : Success/Confirmation                          │

│    • Yellow : Warning/Attention needed                     │

│    • Red : Error/Critical                                  │

│    • Cyan : Information/Headers                            │

│    • Blue : Active selection                               │

│                                                             │

└─────────────────────────────────────────────────────────────┘

```



## 🔍 What Gets Created?



### History Table Structure



When you apply history tracking to a table like `employees`, here's what gets created:



<details>

<summary><b>📊 Example: Original Table</b></summary>



```sql

-- Original table

CREATE TABLE employees (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   name VARCHAR(100) NOT NULL,

&nbsp;   email VARCHAR(255) UNIQUE,

&nbsp;   department VARCHAR(50),

&nbsp;   salary DECIMAL(10,2),

&nbsp;   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

```



</details>



<details>

<summary><b>🕰️ Generated History Table</b></summary>



```sql

-- Generated history table

CREATE TABLE employees_hst (

&nbsp;   -- All original columns preserved

&nbsp;   id INTEGER NOT NULL,

&nbsp;   name VARCHAR(100) NOT NULL,

&nbsp;   email VARCHAR(255),

&nbsp;   department VARCHAR(50),

&nbsp;   salary DECIMAL(10,2),

&nbsp;   created_at TIMESTAMP,

&nbsp;   

&nbsp;   -- Added history metadata

&nbsp;   history_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

&nbsp;   history_operation VARCHAR(10),  -- 'UPDATE' or 'DELETE'

&nbsp;   history_user VARCHAR(100),      -- User who made the change

&nbsp;   

&nbsp;   -- Composite primary key

&nbsp;   PRIMARY KEY (id, history_timestamp)

);



-- Index for faster queries

CREATE INDEX idx_employees_hst_timestamp ON employees_hst(history_timestamp);

CREATE INDEX idx_employees_hst_operation ON employees_hst(history_operation);

```



</details>



<details>

<summary><b>⚡ Generated Trigger Function</b></summary>



```sql

-- Trigger function (PostgreSQL example)

CREATE OR REPLACE FUNCTION employees_history_trigger()

RETURNS TRIGGER AS $$

BEGIN

&nbsp;   IF (TG_OP = 'DELETE') THEN

&nbsp;       INSERT INTO employees_hst

&nbsp;       SELECT OLD.*, 

&nbsp;              CURRENT_TIMESTAMP, 

&nbsp;              'DELETE', 

&nbsp;              CURRENT_USER;

&nbsp;       RETURN OLD;

&nbsp;   ELSIF (TG_OP = 'UPDATE') THEN

&nbsp;       INSERT INTO employees_hst

&nbsp;       SELECT OLD.*, 

&nbsp;              CURRENT_TIMESTAMP, 

&nbsp;              'UPDATE', 

&nbsp;              CURRENT_USER;

&nbsp;       RETURN NEW;

&nbsp;   END IF;

&nbsp;   RETURN NULL;

END;

$$ LANGUAGE plpgsql;



-- Attach trigger to original table

CREATE TRIGGER employees_history_trigger

AFTER UPDATE OR DELETE ON employees

FOR EACH ROW

EXECUTE FUNCTION employees_history_trigger();

```



</details>



## 📊 Querying History Data



After setup, you can query historical data like:



```sql

-- Get all changes for employee ID 123

SELECT * FROM employees_hst 

WHERE id = 123 

ORDER BY history_timestamp DESC;



-- See who changed salaries

SELECT history_timestamp, history_user, salary 

FROM employees_hst 

WHERE history_operation = 'UPDATE' 

ORDER BY history_timestamp DESC;



-- Restore deleted record

INSERT INTO employees 

SELECT id, name, email, department, salary, created_at 

FROM employees_hst 

WHERE id = 456 AND history_operation = 'DELETE' 

ORDER BY history_timestamp DESC 

LIMIT 1;

```



## 🧪 Testing



Run the test suite to ensure everything works:



```bash

# Run all tests

python -m pytest tests/



# Run with coverage

python -m pytest --cov=history_table_generator tests/



# Run specific test module

python -m pytest tests/test_database.py -v

```



## 🐳 Docker Support



### Quick Start with Docker Compose



```yaml

# docker-compose.yml

version: '3.8'

services:

&nbsp; history-generator:

&nbsp;   build: .

&nbsp;   environment:

&nbsp;     - DB_HOST=postgres

&nbsp;     - DB_PORT=5432

&nbsp;   depends_on:

&nbsp;     - postgres

&nbsp;   volumes:

&nbsp;     - ./config:/app/config

&nbsp;     - ./backups:/app/backups

&nbsp;     - ./logs:/app/logs

&nbsp; 

&nbsp; postgres:

&nbsp;   image: postgres:15

&nbsp;   environment:

&nbsp;     POSTGRES_PASSWORD: example

&nbsp;   volumes:

&nbsp;     - postgres_data:/var/lib/postgresql/data



volumes:

&nbsp; postgres_data:

```



Run with:

```bash

docker-compose up

```



## 🚀 Performance Considerations



### For Large Databases

1. **Batch Processing**: The tool processes tables in batches

2. **Index Optimization**: Automatic index creation on history columns

3. **Memory Efficient**: Streamlined operations to minimize memory usage

4. **Connection Pooling**: Reuses database connections



### Recommended Practices

- Apply to high-activity tables during maintenance windows

- Consider partitioning for very large history tables

- Regularly archive old history data

- Monitor disk space for history tables



## 🛠️ Extending the Tool



### Adding New Database Support



1. Create a new database class in `core/database.py`:

```python

class NewDatabase(BaseDatabase):

&nbsp;   def connect(self):

&nbsp;       # Implementation

&nbsp;   

&nbsp;   def get_tables(self, schema):

&nbsp;       # Implementation

```



2. Add trigger generator in `core/trigger_generator.py`:

```python

class NewDBTriggerGenerator(BaseTriggerGenerator):

&nbsp;   def generate_history_table_ddl(self):

&nbsp;       # Database-specific DDL

```



3. Register in factories:

```python

# In DatabaseFactory

if db_type == 'newdb':

&nbsp;   return NewDatabase(config, ui)

```



## 🤝 Contributing



We love contributions! Here's how to help:



1. **Fork** the repository

2. **Create a feature branch**: `git checkout -b feature/amazing-feature`

3. **Commit your changes**: `git commit -m 'Add amazing feature'`

4. **Push to branch**: `git push origin feature/amazing-feature`

5. **Open a Pull Request**



### Development Setup

```bash

# Install development dependencies

pip install -r requirements-dev.txt



# Install pre-commit hooks

pre-commit install



# Run code quality checks

black .

flake8 .

mypy .

```



## 📈 Roadmap



- [x] PostgreSQL support

- [x] MySQL support

- [ ] SQL Server support

- [ ] Oracle Database support

- [ ] SQLite support

- [ ] Web interface (FastAPI)

- [ ] Scheduled backups

- [ ] Data retention policies

- [ ] Change data capture (CDC)

- [ ] Real-time notifications

- [ ] API for programmatic access



## 🆘 Troubleshooting



<details>

<summary><b>Common Issues and Solutions</b></summary>



### Connection Issues

**Problem**: Can't connect to database

**Solution**:

- Check if database server is running

- Verify credentials

- Check firewall settings

- Ensure SSL is properly configured if required



### Permission Errors

**Problem**: "Permission denied" when creating tables

**Solution**:

- Ensure user has CREATE TABLE privilege

- Check schema permissions

- Try connecting as superuser for initial setup



### Trigger Creation Fails

**Problem**: Triggers not being created

**Solution**:

- Check if user has TRIGGER privilege

- Verify trigger function language is installed (plpgsql for PostgreSQL)

- Check for naming conflicts



### Performance Issues

**Problem**: Application is slow with many tables

**Solution**:

- Increase connection pool size in config

- Process tables in smaller batches

- Consider running during off-peak hours



</details>



## 📚 Documentation



- [API Documentation](docs/api.md) - Complete API reference

- [Database Guides](docs/databases/) - Database-specific guides

- [Best Practices](docs/best-practices.md) - Implementation recommendations

- [Migration Guide](docs/migration.md) - Upgrading between versions



## 👥 Authors



- **Your Name** - *Initial work* - [@yourusername](https://github.com/yourusername)

- **Contributors** - [See contributors](https://github.com/yourusername/history-table-generator/graphs/contributors)



## 📄 License



This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



## 🙏 Acknowledgments



- [Rich](https://github.com/Textualize/rich) for beautiful terminal output

- [SQLAlchemy](https://www.sqlalchemy.org/) for database abstraction

- [Inquirer](https://github.com/magmax/python-inquirer) for interactive prompts

- All our contributors and users



---



<div align="center">



### ⭐ Found this useful? Give us a star on GitHub!



[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/history-table-generator&type=Date)](https://star-history.com/#yourusername/history-table-generator&Date)



**"The palest ink is better than the best memory."** - Chinese Proverb



</div>

