import csv
import requests
import time
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8888')

def get_existing_projects():
    """Get list of existing projects"""
    try:
        response = requests.get(f"{API_BASE_URL}/projects")
        if response.status_code == 200:
            return {project['name']: project['id'] for project in response.json()}
        else:
            print(f"Error fetching existing projects: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        return {}

def ingest_projects(projects_file):
    """Ingest initial projects from the projects file"""
    print("Fetching existing projects...")
    existing_projects = get_existing_projects()
    
    new_count = 0
    skip_count = 0
    error_count = 0
    
    with open(projects_file, 'r') as f:
        reader = csv.DictReader(f)
        total_projects = sum(1 for row in reader)
        f.seek(0)  # Reset file pointer
        next(reader)  # Skip header row
        
        for i, row in enumerate(reader, 1):
            name = row['name'].strip()
            description = row['description'].strip()
            
            if not name:
                continue
                
            if name in existing_projects:
                print(f"[{i}/{total_projects}] Skipping existing project: {name}")
                skip_count += 1
                continue
                
            response = requests.post(
                f"{API_BASE_URL}/projects",
                json={
                    "name": name,
                    "description": description
                }
            )
            
            if response.status_code in [200, 201]:
                print(f"[{i}/{total_projects}] Created new project: {name}")
                new_count += 1
            else:
                print(f"[{i}/{total_projects}] Error creating project {name}: {response.status_code}")
                print(f"Response: {response.text}")
                error_count += 1
            
            time.sleep(0.5)  # Small delay to avoid overwhelming the API
    
    print(f"\nProject ingestion summary:")
    print(f"- New projects created: {new_count}")
    print(f"- Existing projects skipped: {skip_count}")
    print(f"- Errors encountered: {error_count}")

def ingest_notes(notes_file):
    """Ingest notes from CSV file one at a time"""
    success_count = 0
    error_count = 0
    
    with open(notes_file, 'r') as f:
        reader = csv.DictReader(f)
        total_notes = sum(1 for row in reader)  # Count total notes
        f.seek(0)  # Reset file pointer
        next(reader)  # Skip header row
        
        for i, row in enumerate(reader, 1):
            note = row['content'].strip()
            if not note:
                continue
                
            response = requests.post(
                f"{API_BASE_URL}/notes",
                json={"content": note}
            )
            
            if response.status_code in [200, 201]:
                print(f"[{i}/{total_notes}] Ingested note: {note[:50]}...")
                success_count += 1
            else:
                print(f"[{i}/{total_notes}] Error ingesting note: {response.status_code}")
                print(f"Response: {response.text}")
                error_count += 1
            
            time.sleep(0.5)  # Small delay to avoid overwhelming the API
    
    print(f"\nNote ingestion summary:")
    print(f"- Successfully ingested: {success_count}")
    print(f"- Errors encountered: {error_count}")
    print(f"- Total processed: {success_count + error_count}")

def main():
    data_dir = Path(__file__).parent.parent / 'data'
    projects_file = data_dir / 'initial_projects.txt'
    notes_file = data_dir / 'sample_notes.csv'
    
    if not data_dir.exists():
        print("Creating data directory...")
        data_dir.mkdir(parents=True)
    
    if not projects_file.exists():
        print(f"Error: Projects file not found at {projects_file}")
        return
        
    if not notes_file.exists():
        print(f"Error: Notes file not found at {notes_file}")
        return
    
    print("Starting data ingestion process...")
    print("=" * 50)
    
    print("\nStep 1: Ingesting projects...")
    ingest_projects(projects_file)
    
    print("\nStep 2: Ingesting notes...")
    ingest_notes(notes_file)
    
    print("\nData ingestion process complete!")
    print("=" * 50)

if __name__ == "__main__":
    main() 