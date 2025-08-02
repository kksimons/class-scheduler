# Database utilities for dataset persistence using Turso
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from libsql_client import create_client


class SchedulerDatabase:
    def __init__(self):
        self.client = None
        self.is_initialized = False

    async def initialize_database(self):
        """Initialize the Turso database connection"""
        try:
            # Get credentials from environment variables
            database_url = os.getenv('TURSO_DATABASE_URL')
            auth_token = os.getenv('TURSO_AUTH_TOKEN')
            
            if not database_url or not auth_token:
                raise Exception('Missing Turso database credentials. Please check TURSO_DATABASE_URL and TURSO_AUTH_TOKEN environment variables.')
            
            # Initialize Turso client - convert WebSocket URL to HTTP URL for better compatibility
            http_url = database_url.replace('libsql://', 'https://').replace(':443', '')
            print(f'🔧 Connecting to Turso database: {http_url}')
            
            self.client = create_client(
                url=http_url,
                auth_token=auth_token
            )

            # Create tables if they don't exist
            await self.create_tables()
            self.is_initialized = True
            print('✅ Database initialized successfully')
        except Exception as error:
            print(f'❌ Database initialization failed: {error}')
            raise error

    async def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            # Create datasets table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    program TEXT NOT NULL,
                    term TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            # Create courses table
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    course_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
                )
            """)

            # Create index for better performance
            await self.client.execute("""
                CREATE INDEX IF NOT EXISTS idx_courses_dataset_id ON courses (dataset_id)
            """)

            print('✅ Database tables created/verified')
        except Exception as error:
            print(f'❌ Failed to create tables: {error}')
            raise error

    def generate_id(self):
        """Generate a unique ID"""
        return str(uuid.uuid4())

    def validate_dataset(self, dataset):
        """Validate dataset structure"""
        errors = []

        # Basic validation
        if not dataset.get('program') or not isinstance(dataset['program'], str):
            errors.append('Program name is required and must be a string')

        if not dataset.get('term') or not isinstance(dataset['term'], str):
            errors.append('Term is required and must be a string')

        if not dataset.get('courses') or not isinstance(dataset['courses'], list):
            errors.append('Courses must be an array')

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'sanitized_dataset': dataset
        }

    async def save_dataset(self, dataset):
        """Save a new dataset to the database"""
        if not self.is_initialized:
            await self.initialize_database()

        validation = self.validate_dataset(dataset)
        if not validation['is_valid']:
            raise Exception(f"Dataset validation failed: {', '.join(validation['errors'])}")

        sanitized_dataset = validation['sanitized_dataset']
        dataset_id = self.generate_id()
        now = datetime.now().isoformat()

        try:
            # Insert dataset
            await self.client.execute(
                "INSERT INTO datasets (id, name, program, term, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    dataset_id,
                    f"{sanitized_dataset['program']} - {sanitized_dataset['term']}",
                    sanitized_dataset['program'],
                    sanitized_dataset['term'],
                    now,
                    now
                ]
            )

            # Insert courses
            for course in sanitized_dataset['courses']:
                course_id = self.generate_id()
                await self.client.execute(
                    "INSERT INTO courses (id, dataset_id, course_name, course_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        course_id,
                        dataset_id,
                        course['course'],
                        json.dumps(course),
                        now,
                        now
                    ]
                )

            print(f'✅ Dataset saved successfully: {dataset_id}')
            return {'success': True, 'datasetId': dataset_id}

        except Exception as error:
            print(f'❌ Failed to save dataset: {error}')
            raise error

    async def load_dataset(self, dataset_id):
        """Load a specific dataset from the database"""
        if not self.is_initialized:
            await self.initialize_database()

        try:
            # Get dataset info
            dataset_result = await self.client.execute(
                'SELECT * FROM datasets WHERE id = ? AND is_active = 1',
                [dataset_id]
            )

            if not dataset_result.rows:
                raise Exception('Dataset not found')

            dataset = dataset_result.rows[0]

            # Get courses
            courses_result = await self.client.execute(
                'SELECT * FROM courses WHERE dataset_id = ? ORDER BY course_name',
                [dataset_id]
            )

            courses = []
            for row in courses_result.rows:
                try:
                    course_data = json.loads(row['course_data'])
                    courses.append(course_data)
                except Exception as error:
                    print(f'Failed to parse course data: {error}')
                    continue

            return {
                'id': dataset['id'],
                'name': dataset['name'],
                'program': dataset['program'],
                'term': dataset['term'],
                'courses': courses,
                'createdAt': dataset['created_at'],
                'updatedAt': dataset['updated_at']
            }

        except Exception as error:
            print(f'❌ Failed to load dataset: {error}')
            raise error

    async def list_datasets(self):
        """List all active datasets"""
        if not self.is_initialized:
            await self.initialize_database()

        try:
            result = await self.client.execute("""
                SELECT d.*, COUNT(c.id) as course_count 
                FROM datasets d 
                LEFT JOIN courses c ON d.id = c.dataset_id 
                WHERE d.is_active = 1 
                GROUP BY d.id 
                ORDER BY d.updated_at DESC
            """)

            datasets = []
            for row in result.rows:
                datasets.append({
                    'id': row['id'],
                    'name': row['name'],
                    'program': row['program'],
                    'term': row['term'],
                    'courseCount': row['course_count'],
                    'createdAt': row['created_at'],
                    'updatedAt': row['updated_at']
                })

            return datasets

        except Exception as error:
            print(f'❌ Failed to list datasets: {error}')
            raise error

    async def update_dataset(self, dataset_id, dataset):
        """Update an existing dataset"""
        if not self.is_initialized:
            await self.initialize_database()

        validation = self.validate_dataset(dataset)
        if not validation['is_valid']:
            raise Exception(f"Dataset validation failed: {', '.join(validation['errors'])}")

        sanitized_dataset = validation['sanitized_dataset']
        now = datetime.now().isoformat()

        try:
            # Update dataset
            await self.client.execute(
                "UPDATE datasets SET program = ?, term = ?, name = ?, updated_at = ? WHERE id = ?",
                [
                    sanitized_dataset['program'],
                    sanitized_dataset['term'],
                    f"{sanitized_dataset['program']} - {sanitized_dataset['term']}",
                    now,
                    dataset_id
                ]
            )

            # Delete existing courses
            await self.client.execute(
                'DELETE FROM courses WHERE dataset_id = ?',
                [dataset_id]
            )

            # Insert updated courses
            for course in sanitized_dataset['courses']:
                course_id = self.generate_id()
                await self.client.execute(
                    "INSERT INTO courses (id, dataset_id, course_name, course_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        course_id,
                        dataset_id,
                        course['course'],
                        json.dumps(course),
                        now,
                        now
                    ]
                )

            print(f'✅ Dataset updated successfully: {dataset_id}')
            return {'success': True, 'datasetId': dataset_id}

        except Exception as error:
            print(f'❌ Failed to update dataset: {error}')
            raise error

    async def delete_dataset(self, dataset_id):
        """Delete a dataset (soft delete)"""
        if not self.is_initialized:
            await self.initialize_database()

        try:
            # Soft delete - just mark as inactive
            await self.client.execute(
                'UPDATE datasets SET is_active = 0, updated_at = ? WHERE id = ?',
                [datetime.now().isoformat(), dataset_id]
            )

            print(f'✅ Dataset deleted successfully: {dataset_id}')
            return {'success': True}

        except Exception as error:
            print(f'❌ Failed to delete dataset: {error}')
            raise error