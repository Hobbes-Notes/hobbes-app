# Action Items MVP Plan


## Key Strategic Decision

**Action Items as First-Class Citizens**: Treat action items as independent entities rather than project-dependent items. This provides greater flexibility and simpler user mental model.

---

## User Flow

### Primary Flow: Note-to-Action Item
1. **User writes/updates a note** in hobbes-app
2. **CapA automatically analyzes** note content in background
3. **System extracts action items** and stores them independently
4. **Action items appear in dedicated view** for management
5. **User can update status** (pending → completed/cancelled)

---

## CapA: Action Item Management

### Purpose
Automatically extract and manage action items from notes

### Trigger Point
- When user creates or updates a note

### Inputs
- `note_content`: The note content to analyze
- `existing_action_items`: List of current user's action items  
- `user_id`: User identifier

### Processing
- AI analyzes note content using ACTION_MANAGEMENT use case
- Extracts structured action items with rich metadata

### Outputs
- List of ActionItem objects with fields:
  - `task`: What needs to be done
  - `doer`: Who should do the task
  - `theme`: Category/theme of the task
  - `context`: Additional context
  - `status`: pending, completed, cancelled
  - `type`: task, reminder, follow-up, etc.

### API Endpoints
- `GET /action-items`: List user's action items with filters
- `POST /action-items`: Create new action item
- `PUT /action-items/{id}`: Update existing action item  
- `DELETE /action-items/{id}`: Delete action item

---

## CapB: Project Tagging

### Purpose
Automatic project classification and tagging (planned for future)

### Status
⏳ **Planning Phase** - Will integrate with CapA action items as tags/filters

---

**Status**: CapA Implementation Complete, CapB Planning Phase 