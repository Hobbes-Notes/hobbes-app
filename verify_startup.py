# #!/usr/bin/env python3
# """
# Script to verify that all DynamoDB tables are properly set up.
# """
# 
# import asyncio
# import sys
# import os
# 
# # Add the backend src path to Python path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))
# 
# from infrastructure.dynamodb_client import get_dynamodb_client
# 
# async def verify_tables():
#     """Verify that all required tables exist."""
#     
#     print("🔍 Verifying DynamoDB Tables")
#     print("=" * 40)
#     
#     try:
#         dynamodb_client = get_dynamodb_client()
#         
#         # Expected tables
#         expected_tables = [
#             'Users',
#             'Projects', 
#             'Notes',
#             'ProjectNotes',
#             'action_items',
#             'ai_configurations'
#         ]
#         
#         # Get existing tables
#         existing_tables = dynamodb_client.list_tables()
#         
#         print(f"📊 Found {len(existing_tables)} tables total")
#         
#         # Check each expected table
#         all_good = True
#         for table_name in expected_tables:
#             if table_name in existing_tables:
#                 print(f"✅ {table_name}")
#             else:
#                 print(f"❌ {table_name} - MISSING")
#                 all_good = False
#         
#         # List any extra tables
#         extra_tables = [t for t in existing_tables if t not in expected_tables]
#         if extra_tables:
#             print(f"\n📋 Additional tables found:")
#             for table in extra_tables:
#                 print(f"   • {table}")
#         
#         print(f"\n{'🎉 All required tables present!' if all_good else '⚠️  Some tables are missing'}")
#         return all_good
#         
#     except Exception as e:
#         print(f"❌ Error verifying tables: {e}")
#         import traceback
#         traceback.print_exc()
#         return False
# 
# if __name__ == "__main__":
#     success = asyncio.run(verify_tables())
#     sys.exit(0 if success else 1)

# VERIFICATION SCRIPT COMMENTED OUT - NOT NEEDED YET
# This script can be uncommented later when needed for infrastructure debugging 