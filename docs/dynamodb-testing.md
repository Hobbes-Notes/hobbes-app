# DynamoDB Testing and Inspection

This document describes the utilities available for testing and inspecting DynamoDB tables in the Hobbes application.

## Overview

The Hobbes application uses DynamoDB Local for development and testing. We provide utilities to easily inspect table contents, schema, and status without needing to write custom scripts.

## Quick Start

### List All Tables
```bash
./scripts/dynamodb-inspect.sh list-tables
```

### Check Table Status Summary
```bash
./scripts/dynamodb-inspect.sh table-status
```

### Describe a Specific Table
```bash
./scripts/dynamodb-inspect.sh describe-table action_items
```

### Scan Table Contents
```bash
# Scan all items
./scripts/dynamodb-inspect.sh scan-table Notes

# Limit results
./scripts/dynamodb-inspect.sh scan-table Notes --limit 5

# Pretty print output
./scripts/dynamodb-inspect.sh scan-table Notes --limit 10 --pretty
```

## Available Tables

The application currently uses these DynamoDB tables:

| Table Name | Purpose | Key Schema | GSI Count |
|------------|---------|------------|-----------|
| `Users` | User accounts | `id` (HASH) | 0 |
| `Projects` | User projects | `id` (HASH) | 2 |
| `Notes` | User notes | `id` (HASH) | 1 |
| `ProjectNotes` | Project-note associations | `project_id` (HASH), `note_id` (RANGE) | 0 |
| `action_items` | Action items | `id` (HASH) | 1 |

## Utilities

### 1. DynamoDB Inspector Script
**Location**: `scripts/dynamodb-inspect.sh`

A convenient wrapper script that runs the DynamoDB inspector inside the Docker container.

**Features**:
- Automatic container status checking
- Colored output for better readability
- Built-in help and examples
- Error handling

### 2. DynamoDB Inspector Python Module
**Location**: `backend/src/utils/dynamodb_inspector.py`

The core Python utility that provides programmatic access to DynamoDB inspection features.

**Features**:
- List all tables
- Describe table schema and metadata
- Scan table contents with optional limits
- Get item counts and table status
- Pretty-print JSON output

## Usage Examples

### Check if Action Items Table Exists
```bash
./scripts/dynamodb-inspect.sh list-tables | grep action_items
```

### Verify Table Schema
```bash
./scripts/dynamodb-inspect.sh describe-table action_items | jq '.KeySchema'
```

### Check Table Item Counts
```bash
./scripts/dynamodb-inspect.sh table-status | jq '.tables | to_entries[] | {table: .key, items: .value.item_count}'
```

### Scan Recent Items (if timestamps exist)
```bash
./scripts/dynamodb-inspect.sh scan-table Notes --limit 5 --pretty
```

## Running from Inside Docker

You can also run the inspector directly inside the backend container:

```bash
# Enter the container
docker exec -it hobbes-app-backend-1 bash

# Run the inspector
python utils/dynamodb_inspector.py list-tables
python utils/dynamodb_inspector.py table-status
python utils/dynamodb_inspector.py scan-table Notes --limit 5
```

## Troubleshooting

### Container Not Running
If you get a "Backend container is not running" error:

```bash
docker compose up -d backend
```

### Permission Errors
If you encounter permission errors with DynamoDB Local:

```bash
# Fix permissions inside the container
docker compose exec dynamodb-local chown -R dynamodblocal:dynamodblocal /home/dynamodblocal/data

# Restart DynamoDB Local
docker compose restart dynamodb-local
```

### Import Errors
If you get Python import errors when running the inspector:

```bash
# Make sure you're in the backend container with the right path
docker exec -it hobbes-app-backend-1 bash
cd /code
python utils/dynamodb_inspector.py --help
```

## Development Tips

### Adding New Tables
When adding new tables to the application:

1. Implement the table creation in the repository
2. Test table creation with: `./scripts/dynamodb-inspect.sh list-tables`
3. Verify schema with: `./scripts/dynamodb-inspect.sh describe-table <table_name>`
4. Update this documentation

### Debugging Data Issues
1. Check table status: `./scripts/dynamodb-inspect.sh table-status`
2. Inspect table schema: `./scripts/dynamodb-inspect.sh describe-table <table_name>`
3. Sample table data: `./scripts/dynamodb-inspect.sh scan-table <table_name> --limit 5`
4. Check application logs: `docker compose logs backend --tail=50`

### Performance Monitoring
Use the table status command to monitor table growth:

```bash
# Check table sizes
./scripts/dynamodb-inspect.sh table-status | jq '.tables | to_entries[] | {table: .key, size_bytes: .value.size_bytes, items: .value.item_count}'
```

## Advanced Usage

### Custom Filtering with jq
```bash
# Get only active tables
./scripts/dynamodb-inspect.sh table-status | jq '.tables | to_entries[] | select(.value.status == "ACTIVE") | .key'

# Get tables with GSI
./scripts/dynamodb-inspect.sh table-status | jq '.tables | to_entries[] | select(.value.global_secondary_indexes > 0) | {table: .key, gsi_count: .value.global_secondary_indexes}'
```

### Batch Operations
```bash
# Check all tables for specific attributes
for table in $(./scripts/dynamodb-inspect.sh list-tables | grep -v "DynamoDB Tables:" | sed 's/.*- //'); do
  echo "=== $table ==="
  ./scripts/dynamodb-inspect.sh describe-table $table | jq '.KeySchema'
done
``` 