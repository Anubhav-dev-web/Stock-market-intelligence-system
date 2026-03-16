# sql_loader.py
# Utility to load SQL files from the sql/ directory
import os

# Resolve the project root (parent of pipelines/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SQL_DIR = os.path.join(_PROJECT_ROOT, 'sql')


def load_sql(relative_path: str) -> str:
    """
    Read a .sql file from the sql/ directory.

    Args:
        relative_path: Path relative to sql/, e.g. 'setup_and_load/create_schema.sql'

    Returns:
        The SQL text content of the file.
    """
    full_path = os.path.join(_SQL_DIR, relative_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()
