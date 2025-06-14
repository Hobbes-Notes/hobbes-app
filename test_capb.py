#!/usr/bin/env python3
"""
Test script for CapB (Project Tagging) functionality.

This script tests the ability to automatically tag action items with relevant projects
based on semantic similarity.
"""

import asyncio
import json
import sys
import os

# Add the backend src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from api.services.note_service import NoteService
from api.services.action_item_service import ActionItemService
from api.services.project_service import ProjectService
from api.models.note import NoteCreate
from api.models.project import ProjectCreate
from api.repositories.impl import (
    get_note_repository,
    get_project_repository,
    get_ai_service,
    get_action_item_service,
    get_capb_service
)

async def test_capb():
    """Test CapB functionality with various scenarios."""
    
    print("🚀 Starting CapB (Project Tagging) Test")
    print("=" * 50)
    
    # Initialize services
    try:
        ai_service = get_ai_service()
        action_item_service = get_action_item_service()
        capb_service = get_capb_service()
        project_service = ProjectService(ai_service=ai_service, capb_service=capb_service)
        note_repository = get_note_repository()
        project_repository = get_project_repository()
        
        note_service = NoteService(
            note_repository=note_repository,
            project_repository=project_repository,
            project_service=project_service,
            ai_service=ai_service,
            action_item_service=action_item_service,
            capb_service=capb_service
        )
        
        print("✅ Services initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return False
    
    # Test user ID
    test_user_id = "test-user-123"
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Project Creation and Tagging",
            "projects": [
                {
                    "name": "Dental Health",
                    "description": "Managing dental appointments and oral health"
                },
                {
                    "name": "Work Tasks",
                    "description": "Professional responsibilities and work-related tasks"
                },
                {
                    "name": "Personal Errands",
                    "description": "Personal tasks and errands"
                }
            ],
            "notes": [
                {
                    "content": "I need to call the dentist tomorrow to schedule an appointment. Also should buy groceries this weekend and finish the quarterly report by Friday.",
                    "expected_project_tags": {
                        "dental": ["Dental Health"],
                        "work": ["Work Tasks"],
                        "personal": ["Personal Errands"]
                    }
                }
            ]
        },
        {
            "name": "Multiple Projects Tagging",
            "notes": [
                {
                    "content": "The quarterly report needs to be reviewed by the team before the client meeting on Wednesday. Also need to schedule a follow-up with the dentist about the root canal.",
                    "expected_project_tags": {
                        "work": ["Work Tasks"],
                        "dental": ["Dental Health"]
                    }
                }
            ]
        },
        {
            "name": "Project Updates and Re-tagging",
            "project_updates": [
                {
                    "name": "Dental Health",
                    "new_description": "Dental appointments, treatments, and insurance matters"
                }
            ],
            "notes": [
                {
                    "content": "Need to check dental insurance coverage for the root canal procedure and prepare presentation for the client meeting.",
                    "expected_project_tags": {
                        "dental": ["Dental Health"],
                        "work": ["Work Tasks"]
                    }
                }
            ]
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Test {i}: {scenario['name']}")
        
        try:
            # Create projects if specified
            if "projects" in scenario:
                print("\n🏗️  Creating test projects:")
                for project_data in scenario["projects"]:
                    project = ProjectCreate(
                        name=project_data["name"],
                        description=project_data["description"],
                        user_id=test_user_id
                    )
                    created_project = await project_service.create_project(project)
                    print(f"✅ Created project: {created_project.name}")
            
            # Update projects if specified
            if "project_updates" in scenario:
                print("\n🔄 Updating test projects:")
                for update in scenario["project_updates"]:
                    # Get existing project
                    projects = await project_service.get_projects(test_user_id)
                    project = next((p for p in projects if p.name == update["name"]), None)
                    if project:
                        # Update project
                        updated_project = await project_service.update_project(
                            project.id,
                            {"description": update["new_description"]}
                        )
                        print(f"✅ Updated project: {updated_project.name}")
            
            # Process notes
            for note_data in scenario["notes"]:
                print(f"\n📝 Processing note: {note_data['content'][:100]}...")
                
                # Get initial action items
                initial_items = await action_item_service.get_action_items_by_user(test_user_id)
                initial_count = len(initial_items)
                print(f"📊 Initial action items: {initial_count}")
                
                # Create note (this should trigger CapA and CapB)
                note = NoteCreate(
                    content=note_data["content"],
                    user_id=test_user_id
                )
                
                created_note = await note_service.create_note(note)
                print(f"✅ Created note: {created_note.id}")
                
                # Wait for processing
                await asyncio.sleep(2)  # Give time for CapA and CapB to process
                
                # Get final action items
                final_items = await action_item_service.get_action_items_by_user(test_user_id)
                final_count = len(final_items)
                
                print(f"📊 Final action items: {final_count}")
                print(f"📈 Change: {final_count - initial_count} action items")
                
                # Show tagged action items
                if final_items:
                    print("\n🏷️  Tagged Action Items:")
                    for item in final_items[-3:]:  # Show last 3 items
                        print(f"\n   📌 {item.task[:60]}...")
                        if item.projects:
                            print(f"      📂 Projects: {', '.join(item.projects)}")
                        else:
                            print("      ⚠️  No projects tagged")
                
                # Verify project tags
                if "expected_project_tags" in note_data:
                    print("\n🔍 Verifying project tags:")
                    for category, expected_projects in note_data["expected_project_tags"].items():
                        matching_items = [
                            item for item in final_items
                            if any(p in item.projects for p in expected_projects)
                        ]
                        print(f"   {category}: {len(matching_items)} items tagged with {expected_projects}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 CapB Test Complete")
    
    # Final summary
    try:
        all_items = await action_item_service.get_action_items_by_user(test_user_id)
        tagged_items = [item for item in all_items if item.projects]
        untagged_items = [item for item in all_items if not item.projects]
        
        print(f"\n📊 Final Summary:")
        print(f"   Total Action Items: {len(all_items)}")
        print(f"   Tagged Items: {len(tagged_items)}")
        print(f"   Untagged Items: {len(untagged_items)}")
        
        # Show metrics
        metrics = capb_service.get_metrics()
        print(f"\n📈 CapB Metrics:")
        print(f"   Total Runs: {metrics['total_runs']}")
        print(f"   Successful Runs: {metrics['successful_runs']}")
        print(f"   Failed Runs: {metrics['failed_runs']}")
        print(f"   Total Items Processed: {metrics['total_action_items_processed']}")
        print(f"   Total Items Tagged: {metrics['total_action_items_tagged']}")
        print(f"   Average Processing Time: {metrics['average_processing_time']:.2f}s")
        
        if metrics['error_counts']:
            print("\n⚠️  Error Counts:")
            for error_type, count in metrics['error_counts'].items():
                print(f"   {error_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get final summary: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_capb())
    sys.exit(0 if success else 1) 