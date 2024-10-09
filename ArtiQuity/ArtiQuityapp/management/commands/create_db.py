from django.core.management.base import BaseCommand
from django.conf import settings
import pyodbc

class Command(BaseCommand):
    help = 'Creates the database dynamically if it does not exist'

    def handle(self, *args, **kwargs):
        # Extract database configuration from settings
        db_settings = settings.DATABASES['default']
        server = db_settings['HOST']  # Correct key for server name
        database = db_settings['NAME']  # Correct key for database name

        driver = db_settings['OPTIONS'].get('driver', 'ODBC Driver 17 for SQL Server')

        # Establish a connection to the master database to issue CREATE DATABASE command
        conn_str = f'DRIVER={driver};SERVER={server};Trusted_Connection=yes;DATABASE=master;'
        connection = pyodbc.connect(conn_str, autocommit=True)
        
        cursor = connection.cursor()

        # Check if the database already exists
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{database}'")
        db_exists = cursor.fetchone()

        if not db_exists:
            # If the database does not exist, create it
            self.stdout.write(f"Creating database '{database}'...")
            cursor.execute(f"CREATE DATABASE {database}")
            self.stdout.write(f"Database '{database}' created successfully!")
        else:
            self.stdout.write(f"Database '{database}' already exists.")

        # Close the connection
        cursor.close()
        connection.close()