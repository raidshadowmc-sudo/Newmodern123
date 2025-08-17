#!/usr/bin/env python3
"""
Database migration script to add missing columns to existing tables
"""

from app import app, db
import sqlite3
import os
from sqlalchemy import inspect
from sqlalchemy.sql import text

def migrate_database():
    """Migrate database to add missing columns"""
    db_path = os.path.join('instance', 'bedwars_leaderboard.db')

    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        with app.app_context():
            db.create_all()
        print("New database created successfully!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting database migration...")

        # Check if admin_custom_role table exists and add missing columns
        inspector = inspect(db.engine)
        if 'admin_custom_role' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('admin_custom_role')]

            if 'emoji_url' not in columns:
                print("Adding emoji_url column to admin_custom_role table...")
                db.engine.execute(text("ALTER TABLE admin_custom_role ADD COLUMN emoji_url VARCHAR(256)"))

            if 'emoji_class' not in columns:
                print("Adding emoji_class column to admin_custom_role table...")
                db.engine.execute(text("ALTER TABLE admin_custom_role ADD COLUMN emoji_class VARCHAR(64)"))

            if 'emoji_is_animated' not in columns:
                print("Adding emoji_is_animated column to admin_custom_role table...")
                db.engine.execute(text("ALTER TABLE admin_custom_role ADD COLUMN emoji_is_animated BOOLEAN DEFAULT 0"))

        print("Database migration completed successfully!")

    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()