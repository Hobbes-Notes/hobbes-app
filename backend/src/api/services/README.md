# Services Architecture

## Overview

This directory implements a clean dependency injection architecture following enterprise patterns.

## Files and Responsibilities

### `providers.py` (NEW - Primary DI Configuration)
- **Purpose**: Central location for all dependency injection providers
- **Benefits**: 
  - No circular import dependencies
  - Proper singleton caching for stateless services  
  - Clear separation between service definitions and DI configuration
  - Follows enterprise DI patterns

### `dependencies.py` (DEPRECATED - Compatibility Layer)
- **Purpose**: Backwards compatibility wrapper around providers.py
- **Status**: Will be removed in future versions
- **Usage**: Existing controllers continue to work unchanged

### Service Classes (`*_service.py`)
- **Purpose**: Plain business logic classes with constructor injection
- **Pattern**: Services are pure classes, DI happens in providers.py

## Service Lifetimes

### Singletons (Stateless Services)
- ✅ **AuthService**: Token validation, no mutable state
- ✅ **MonitoringService**: Metrics collection, stateless
- ✅ **AIService**: LLM interactions, stateless

### Request-Scoped (Stateful/Per-Request)
- **UserService**: May have request-specific state
- **ActionItemService**: Repository-backed, per-request
- **NoteService**: Complex business logic, per-request

## Dependency Flow

```
Controller
    ↓ (FastAPI Depends)
providers.py  
    ↓ (Constructor Injection)
Service Classes
    ↓ (Constructor Injection)  
Repository Classes
```

## Example Usage

```python
# In Controller
@router.post("/auth")
async def authenticate(
    auth_service: AuthServiceDep  # Type alias from dependencies.py
):
    return await auth_service.validate_token(token)

# In providers.py
def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> AuthService:
    # Singleton pattern for stateless service
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService(user_service=user_service)
    return _auth_service_instance
```

## Migration Notes

### ✅ What Changed:
1. **AuthService**: Now accepts UserService as constructor parameter
2. **UserService**: Now accepts ProjectService as constructor parameter  
3. **Caching**: Stateless services are properly cached as singletons
4. **Import Separation**: No more circular dependency risks

### ✅ What Stayed The Same:
1. **Controller Interfaces**: All existing controller code works unchanged
2. **Service APIs**: No changes to service method signatures
3. **Type Aliases**: Same `*ServiceDep` patterns for clean controller signatures

## Benefits of New Architecture

1. **Performance**: Singleton caching for stateless services
2. **Maintainability**: Clear separation of DI configuration from business logic
3. **Testability**: Easy to mock dependencies in constructor
4. **Scalability**: No circular import risks as codebase grows
5. **Standards**: Follows enterprise dependency injection patterns 