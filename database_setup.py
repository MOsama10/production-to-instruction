# database_setup.py
from langchain.utilities import SQLDatabase

# Database setup
SQLITE_URI = "sqlite:///Materials.db"
db = SQLDatabase.from_uri(SQLITE_URI, include_tables=['materials'], sample_rows_in_table_info=5)
