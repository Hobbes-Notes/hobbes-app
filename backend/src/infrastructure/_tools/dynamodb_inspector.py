#!/usr/bin/env python3
"""
DynamoDB Inspector Utility

A utility script to inspect DynamoDB tables, their contents, and status.
Can be run from within the Docker container for debugging and testing.

This tool is part of infrastructure tooling since it has dependencies
on infrastructure modules.

Usage:
  python infrastructure/_tools/dynamodb_inspector.py --help
  python infrastructure/_tools/dynamodb_inspector.py list-tables
  python infrastructure/_tools/dynamodb_inspector.py describe-table Notes
  python infrastructure/_tools/dynamodb_inspector.py scan-table Notes --limit 5
  python infrastructure/_tools/dynamodb_inspector.py table-status
"""

import argparse
import json
import sys
import os
from typing import Dict, List, Any, Optional

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from infrastructure.dynamodb_client import get_dynamodb_client


class DynamoDBInspector:
    """Utility class for inspecting DynamoDB tables."""
    
    def __init__(self):
        self.client = get_dynamodb_client()
    
    def list_tables(self) -> List[str]:
        """List all DynamoDB tables."""
        try:
            tables = self.client.list_tables()
            return sorted(tables)
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []
    
    def describe_table(self, table_name: str) -> Optional[Dict]:
        """Get detailed information about a table."""
        try:
            if not self.client.table_exists(table_name):
                print(f"Table '{table_name}' does not exist")
                return None
            
            description = self.client.describe_table(table_name)
            return description
        except Exception as e:
            print(f"Error describing table '{table_name}': {e}")
            return None
    
    def scan_table(self, table_name: str, limit: Optional[int] = None) -> List[Dict]:
        """Scan a table and return items."""
        try:
            if not self.client.table_exists(table_name):
                print(f"Table '{table_name}' does not exist")
                return []
            
            if limit:
                items = self.client.scan(table_name, limit=limit).get('Items', [])
            else:
                items = self.client.scan_all(table_name)
            
            return items
        except Exception as e:
            print(f"Error scanning table '{table_name}': {e}")
            return []
    
    def get_item_count(self, table_name: str) -> int:
        """Get the number of items in a table."""
        try:
            description = self.describe_table(table_name)
            if description:
                return description.get('ItemCount', 0)
            return 0
        except Exception as e:
            print(f"Error getting item count for '{table_name}': {e}")
            return 0
    
    def table_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all tables and their status."""
        tables = self.list_tables()
        summary = {
            'total_tables': len(tables),
            'tables': {}
        }
        
        for table_name in tables:
            description = self.describe_table(table_name)
            if description:
                summary['tables'][table_name] = {
                    'status': description.get('TableStatus', 'Unknown'),
                    'item_count': description.get('ItemCount', 0),
                    'size_bytes': description.get('TableSizeBytes', 0),
                    'key_schema': description.get('KeySchema', []),
                    'global_secondary_indexes': len(description.get('GlobalSecondaryIndexes', [])),
                    'local_secondary_indexes': len(description.get('LocalSecondaryIndexes', []))
                }
        
        return summary
    
    def pretty_print_json(self, data: Any, indent: int = 2) -> None:
        """Pretty print JSON data."""
        print(json.dumps(data, indent=indent, default=str, sort_keys=True))


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="DynamoDB Inspector - Inspect tables, contents, and status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list-tables
  %(prog)s describe-table Notes
  %(prog)s scan-table Notes --limit 5
  %(prog)s table-status
  %(prog)s scan-table action_items --pretty
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List tables command
    subparsers.add_parser('list-tables', help='List all DynamoDB tables')
    
    # Describe table command
    describe_parser = subparsers.add_parser('describe-table', help='Describe a specific table')
    describe_parser.add_argument('table_name', help='Name of the table to describe')
    
    # Scan table command
    scan_parser = subparsers.add_parser('scan-table', help='Scan items from a table')
    scan_parser.add_argument('table_name', help='Name of the table to scan')
    scan_parser.add_argument('--limit', type=int, help='Limit number of items returned')
    scan_parser.add_argument('--pretty', action='store_true', help='Pretty print the output')
    
    # Table status command
    subparsers.add_parser('table-status', help='Show status summary of all tables')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    inspector = DynamoDBInspector()
    
    try:
        if args.command == 'list-tables':
            tables = inspector.list_tables()
            if tables:
                print("DynamoDB Tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("No tables found")
        
        elif args.command == 'describe-table':
            description = inspector.describe_table(args.table_name)
            if description:
                inspector.pretty_print_json(description)
        
        elif args.command == 'scan-table':
            items = inspector.scan_table(args.table_name, args.limit)
            if items:
                print(f"Found {len(items)} items in table '{args.table_name}':")
                if args.pretty:
                    inspector.pretty_print_json(items)
                else:
                    for i, item in enumerate(items, 1):
                        print(f"\nItem {i}:")
                        inspector.pretty_print_json(item)
            else:
                print(f"No items found in table '{args.table_name}'")
        
        elif args.command == 'table-status':
            summary = inspector.table_status_summary()
            print("DynamoDB Tables Status Summary:")
            inspector.pretty_print_json(summary)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 