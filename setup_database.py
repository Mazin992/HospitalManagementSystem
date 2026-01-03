#!/usr/bin/env python
"""
PostgreSQL Database Creation Script
Creates database using existing user credentials from .env file
PREREQUISITE: User must exist with CREATEDB privilege (see DATABASE_SETUP.md)
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_config():
    """Load database configuration from environment variables"""
    config = {
        'db_user': os.environ.get('DB_USER', 'hospital_user'),
        'db_password': os.environ.get('DB_PASSWORD', '123'),
        'db_host': os.environ.get('DB_HOST', 'localhost'),
        'db_port': os.environ.get('DB_PORT', '5432'),
        'db_name': os.environ.get('DB_NAME', 'hospital_db'),
    }

    # Validate configuration
    if not config['db_user'] or not config['db_password']:
        print("❌ ERROR: DB_USER and DB_PASSWORD must be set in .env file")
        sys.exit(1)

    return config


def connect_to_postgres(config):
    """Connect to PostgreSQL using credentials from .env"""
    try:
        print(f"Connecting to PostgreSQL as '{config['db_user']}'...")
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Connected successfully")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n" + "=" * 70)
        print("⚠️  CANNOT CONNECT TO POSTGRESQL")
        print("=" * 70)
        print("\nPossible reasons:")
        print("  • User does not exist")
        print("  • Invalid password")
        print("  • PostgreSQL service is not running")
        print("  • Wrong host or port")
        print("\n📖 See DATABASE_SETUP.md for user creation instructions")
        print("=" * 70)
        sys.exit(1)


def database_exists(cursor, dbname):
    """Check if database exists"""
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (dbname,)
    )
    return cursor.fetchone() is not None


def create_database(cursor, dbname):
    """Create database if it doesn't exist"""
    if database_exists(cursor, dbname):
        print(f"ℹ️  Database '{dbname}' already exists")
        return False

    try:
        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname))
        )
        print(f"✅ Created database '{dbname}'")
        return True
    except psycopg2.ProgrammingError as e:
        if "permission denied" in str(e).lower():
            print(f"❌ Permission denied: User '{cursor.connection.info.user}' cannot create databases")
            print("\nGrant CREATEDB privilege to the user:")
            print(f"   ALTER USER {cursor.connection.info.user} CREATEDB;")
        else:
            print(f"❌ Failed to create database: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        sys.exit(1)


def verify_connection(config):
    """Verify connection to the newly created/existing database"""
    try:
        print(f"\nVerifying connection to '{config['db_name']}'...")
        test_conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )

        cursor = test_conn.cursor()
        cursor.execute("SELECT current_user, current_database(), version();")
        user, db, version = cursor.fetchone()
        cursor.close()
        test_conn.close()

        print(f"✅ Connection successful!")
        print(f"   • User:     {user}")
        print(f"   • Database: {db}")
        print(f"   • Version:  {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"❌ Connection verification failed: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 70)
    print("PostgreSQL Database Creation")
    print("=" * 70)
    print()

    # Load configuration
    config = get_env_config()

    print("Configuration:")
    print(f"  • Host:     {config['db_host']}:{config['db_port']}")
    print(f"  • User:     {config['db_user']}")
    print(f"  • Database: {config['db_name']}")
    print()

    # Connect to PostgreSQL
    print("-" * 70)
    print("Step 1: Connecting to PostgreSQL")
    print("-" * 70)
    conn = connect_to_postgres(config)
    cursor = conn.cursor()
    print()

    # Create database
    print("-" * 70)
    print("Step 2: Creating Database")
    print("-" * 70)
    db_created = create_database(cursor, config['db_name'])
    print()

    # Close connection
    cursor.close()
    conn.close()

    # Verify connection to new database
    print("-" * 70)
    print("Step 3: Verifying Database Access")
    print("-" * 70)
    verify_success = verify_connection(config)
    print()

    # Summary
    print("=" * 70)
    if verify_success:
        print("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
    else:
        print("⚠️  DATABASE CREATED BUT VERIFICATION FAILED")
    print("=" * 70)
    print()

    print("📋 Summary:")
    print(f"   • Database: {config['db_name']} {'(created)' if db_created else '(already exists)'}")
    print(f"   • User:     {config['db_user']}")
    print(f"   • Host:     {config['db_host']}:{config['db_port']}")
    print()

    print("🔗 Connection String:")
    print(f"   postgresql://{config['db_user']}:***@{config['db_host']}:{config['db_port']}/{config['db_name']}")
    print()



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)