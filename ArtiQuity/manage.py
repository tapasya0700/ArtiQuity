#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArtiQuity.settings')

    try:
        # Import the management command for database creation dynamically
        from django.core.management import execute_from_command_line, call_command
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Check if the current command is a relevant Django command (e.g., migrate, runserver, etc.)
    if len(sys.argv) > 1 and sys.argv[1] in ["migrate", "runserver", "makemigrations"]:
        # Automatically create the database before running these commands
        try:
            print("Creating the database if it doesn't exist...")
            call_command('create_db')  # This runs the custom create_db command
        except Exception as e:
            print(f"An error occurred while creating the database: {e}")

    # Continue with the standard Django command execution
    execute_from_command_line(sys.argv)

if __name__ == '__main__':  # Corrected the if statement
    main()