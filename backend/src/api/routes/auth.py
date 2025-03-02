from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Request
from ..auth import validate_google_token, get_current_user, get_user_activities, log_user_activity
from ..models import User, UserActivity, ActivityResponse
from ..jwt import create_tokens, verify_token
from typing import List, Dict
import boto3
import os
from datetime import datetime

router = APIRouter()

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-west-2'),
    endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://dynamodb-local:7777')
)

def log_activity(user_id: str, user_name: str, activity_type: str, details: dict = None):
    """Log user activity with additional details"""
    try:
        activity_table = dynamodb.Table('UserActivity')
        timestamp = datetime.utcnow().isoformat()
        
        activity = {
            'user_id': user_id,
            'user_name': user_name,
            'activity': activity_type,
            'timestamp': timestamp,
            'details': details or {}
        }
        
        activity_table.put_item(Item=activity)
        return activity
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        raise

@router.post("/google", response_model=Dict)
async def google_auth(token: Dict[str, str] = Body(...), response: Response = None):
    """Handle Google OAuth authentication"""
    if not token or 'token' not in token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
        
    user = await validate_google_token(token['token'])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Create JWT tokens
    tokens = create_tokens({
        "sub": user.id,
        "email": user.email,
        "name": user.name
    })
    
    # Set cookies
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 days
        secure=False,  # Set to True in production
        samesite="lax"
    )
    
    # Log login activity
    log_activity(user.id, user.name, "login")
    
    return {
        "access_token": tokens["access_token"],
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token from cookie"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    
    try:
        payload = verify_token(refresh_token)
        tokens = create_tokens({
            "sub": payload["sub"],
            "email": payload["email"],
            "name": payload["name"]
        })
        
        # Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            secure=False,  # Set to True in production
            samesite="lax"
        )
        
        return {
            "access_token": tokens["access_token"],
            "token_type": "bearer"
        }
    except:
        # Delete the invalid refresh token cookie
        response.delete_cookie(key="refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Handle user logout"""
    try:
        # Clear refresh token cookie
        response.delete_cookie(key="refresh_token")
        
        log_activity(current_user.id, current_user.name, "logout")
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/activity", response_model=ActivityResponse)
async def get_activities(current_user: User = Depends(get_current_user)):
    """Get user's activity log"""
    try:
        print("=== Activity Request ===")
        print(f"User ID: {current_user.id}")
        print(f"User Email: {current_user.email}")
        
        activity_table = dynamodb.Table('UserActivity')
        print("Querying DynamoDB...")
        
        response = activity_table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': current_user.id},
            ScanIndexForward=False,  # Sort in descending order (latest first)
            Limit=100  # Limit to last 100 activities
        )
        
        activities = response.get('Items', [])
        print(f"Found {len(activities)} activities")
        
        # Validate and clean up activities
        validated_activities = []
        for activity in activities:
            try:
                # Ensure required fields exist
                if not all(key in activity for key in ['user_id', 'user_name', 'activity', 'timestamp']):
                    print(f"Skipping activity missing required fields: {activity}")
                    continue
                
                # Ensure details is a dict with expected structure
                details = activity.get('details', {})
                if not isinstance(details, dict):
                    details = {}
                
                # Create activity in new format
                validated_activity = {
                    'timestamp': str(activity['timestamp']),
                    'user': {
                        'id': str(activity['user_id']),
                        'name': str(activity['user_name'])
                    },
                    'activity': str(activity['activity']),
                    'details': details
                }
                validated_activities.append(validated_activity)
            except Exception as e:
                print(f"Error validating activity: {str(e)}")
                print(f"Skipping invalid activity: {activity}")
                continue
        
        print(f"Returning {len(validated_activities)} validated activities")
        if validated_activities:
            print("Sample activity:", validated_activities[0])
            
        return {
            "status": "success",
            "data": validated_activities
        }
        
    except Exception as e:
        print("=== Error in get_activities ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"User ID: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user", response_model=User)
async def get_current_user_data(current_user: User = Depends(get_current_user)):
    """Get current user data"""
    return current_user 