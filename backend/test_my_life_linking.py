#!/usr/bin/env python3
"""
Test script to verify My Life project auto-linking for action items
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api.services.action_item_service import ActionItemService
from api.services.project_service import ProjectService
from api.models.action_item import ActionItemCreate
from api.repositories.impl.action_item_repository_impl import DynamoDBActionItemRepository
from api.repositories.impl.project_repository_impl import DynamoDBProjectRepository

async def test_my_life_linking():
    """Test that action items are automatically linked to My Life project"""
    
    print("🧪 Testing My Life project auto-linking for action items...")
    
    # Create services
    action_item_repo = DynamoDBActionItemRepository()
    project_repo = DynamoDBProjectRepository()
    
    project_service = ProjectService(
        project_repository=project_repo,
        ai_service=None,
        capb_service=None
    )
    
    action_item_service = ActionItemService(
        action_item_repository=action_item_repo,
        project_service=project_service
    )
    
    # Test user ID (replace with a real user ID from your system)
    test_user_id = "test-user-123"
    
    try:
        # 1. Ensure My Life project exists for test user
        print(f"1. Creating/getting My Life project for user {test_user_id}...")
        my_life_project = await project_service.get_or_create_my_life_project(test_user_id)
        if my_life_project:
            print(f"✅ My Life project: {my_life_project.id} - '{my_life_project.name}'")
        else:
            print("❌ Failed to create/get My Life project")
            return
        
        # 2. Create an action item WITHOUT specifying projects
        print(f"2. Creating action item without projects (should auto-link to My Life)...")
        action_item_data = ActionItemCreate(
            task="Test action item for My Life linking",
            doer="Test User",
            theme="Testing",
            context="This is a test action item to verify auto-linking",
            status="open",
            type="task",
            projects=[],  # Empty - should auto-link to My Life
            user_id=test_user_id
        )
        
        created_action_item = await action_item_service.create_action_item(action_item_data)
        print(f"✅ Created action item: {created_action_item.id}")
        print(f"✅ Action item projects: {created_action_item.projects}")
        
        # 3. Verify the action item is linked to My Life project
        if my_life_project.id in created_action_item.projects:
            print(f"🎉 SUCCESS: Action item automatically linked to My Life project!")
        else:
            print(f"❌ FAILURE: Action item NOT linked to My Life project")
            print(f"   Expected: [{my_life_project.id}]")
            print(f"   Actual: {created_action_item.projects}")
        
        # 4. Create an action item WITH existing projects (should not override)
        print(f"3. Creating action item with existing projects (should preserve existing)...")
        action_item_with_projects = ActionItemCreate(
            task="Test action item with existing projects",
            doer="Test User",
            theme="Testing",
            context="This action item already has projects",
            status="open",
            type="task",
            projects=["existing-project-123"],  # Has projects - should NOT auto-link
            user_id=test_user_id
        )
        
        created_with_projects = await action_item_service.create_action_item(action_item_with_projects)
        print(f"✅ Created action item with existing projects: {created_with_projects.id}")
        print(f"✅ Action item projects: {created_with_projects.projects}")
        
        # Verify it kept the existing projects and didn't add My Life
        if "existing-project-123" in created_with_projects.projects and my_life_project.id not in created_with_projects.projects:
            print(f"🎉 SUCCESS: Action item with existing projects preserved correctly!")
        else:
            print(f"❌ FAILURE: Action item with existing projects was modified incorrectly")
            print(f"   Expected: ['existing-project-123'] (without My Life)")
            print(f"   Actual: {created_with_projects.projects}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_my_life_linking()) 