"""
Test configuration for ckanext-blob-storage.

Ensures that plugin migrations are applied after database rebuilds.
"""
import pytest
from ckan import model


@pytest.fixture
def clean_db_with_migrations(clean_db):
    """
    Extends the standard clean_db fixture to also apply activity plugin schema changes.
    
    The clean_db fixture rebuilds the database with only core CKAN migrations.
    For tests that require the activity plugin, we need to explicitly add
    the permission_labels column to the activity table after the database is rebuilt.
    """
    # clean_db has already run and rebuilt the database
    # Now add the permission_labels column that activity plugin migrations would add
    # In CKAN 2.11, permission_labels should be a text array (text[]), not text
    
    # Execute SQL to add the missing column if it doesn't exist
    model.Session.execute("""
        ALTER TABLE activity 
        ADD COLUMN IF NOT EXISTS permission_labels text[];
    """)
    model.Session.commit()
    
    return clean_db
