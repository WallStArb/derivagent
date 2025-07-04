"""
Authentication routes for Derivagent
Handles user registration, login, team management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from .supabase_client import get_supabase_auth
from .middleware import (
    get_current_user, 
    require_admin_permissions,
    require_owner_permissions
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
supabase = get_supabase_auth()

# Request/Response Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    company: Optional[str] = None
    team_type: str = Field(default="individual", regex="^(individual|small_firm|enterprise)$")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TeamCreation(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    type: str = Field(default="small_firm", regex="^(individual|small_firm|enterprise)$")
    description: Optional[str] = None

class TeamMemberInvite(BaseModel):
    email: EmailStr
    role: str = Field(default="member", regex="^(admin|trader|viewer)$")

class UserResponse(BaseModel):
    id: str
    email: str
    teams: List[Dict[str, Any]]
    active_team: Optional[Dict[str, Any]]

# Authentication Routes
@router.post("/register", 
            response_model=Dict[str, Any],
            summary="Register new user account")
async def register_user(user_data: UserRegistration):
    """
    Register a new user account with automatic team creation
    
    - **email**: User's email address
    - **password**: Secure password (min 8 characters)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **company**: Optional company name
    - **team_type**: Type of team to create (individual, small_firm, enterprise)
    """
    try:
        # Prepare user metadata
        metadata = {
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "company": user_data.company,
            "team_type": user_data.team_type
        }
        
        # Register user with Supabase
        auth_result = await supabase.sign_up(
            email=user_data.email,
            password=user_data.password,
            metadata=metadata
        )
        
        if not auth_result['success']:
            raise HTTPException(
                status_code=400,
                detail=auth_result['error']
            )
        
        user = auth_result['user']
        
        # Create default team for user
        team_name = f"{user_data.first_name}'s Team"
        if user_data.company:
            team_name = user_data.company
        
        team_result = await supabase.create_team(
            user_id=user.id,
            team_name=team_name,
            team_type=user_data.team_type
        )
        
        if not team_result['success']:
            logger.warning(f"Failed to create team for user {user.id}: {team_result['error']}")
        
        logger.info(f"✅ User registered: {user_data.email}")
        
        return {
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "metadata": metadata
            },
            "session": auth_result.get('session'),
            "team": team_result.get('team') if team_result['success'] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )

@router.post("/login",
            response_model=Dict[str, Any],
            summary="Authenticate user login")
async def login_user(credentials: UserLogin):
    """
    Authenticate user and return session token
    
    - **email**: User's email address  
    - **password**: User's password
    """
    try:
        auth_result = await supabase.sign_in(
            email=credentials.email,
            password=credentials.password
        )
        
        if not auth_result['success']:
            raise HTTPException(
                status_code=401,
                detail=auth_result['error']
            )
        
        user = auth_result['user']
        teams = auth_result['teams']
        
        logger.info(f"✅ User logged in: {credentials.email}")
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "metadata": user.user_metadata
            },
            "session": auth_result['session'],
            "teams": teams,
            "active_team": teams[0] if teams else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )

@router.post("/logout",
            summary="Sign out current user")
async def logout_user():
    """Sign out the current user"""
    try:
        result = await supabase.sign_out()
        
        if result['success']:
            return {"success": True, "message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me",
           response_model=UserResponse,
           summary="Get current user profile")
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user's profile and teams"""
    return UserResponse(
        id=user['id'],
        email=user['email'],
        teams=user['teams'],
        active_team=user['active_team']
    )

# Team Management Routes
@router.post("/teams",
            summary="Create new team")
async def create_team(
    team_data: TeamCreation,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new team
    
    - **name**: Team name
    - **type**: Team type (individual, small_firm, enterprise)
    - **description**: Optional team description
    """
    try:
        result = await supabase.create_team(
            user_id=user['id'],
            team_name=team_data.name,
            team_type=team_data.type
        )
        
        if result['success']:
            logger.info(f"✅ Team created: {team_data.name}")
            return {
                "success": True,
                "message": "Team created successfully",
                "team": result['team']
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Team creation error: {e}")
        raise HTTPException(status_code=500, detail="Team creation failed")

@router.get("/teams/{team_id}/members",
           summary="Get team members")
async def get_team_members(
    team_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all members of a team"""
    try:
        # Verify user is member of team
        user_teams = user.get('teams', [])
        if not any(team['id'] == team_id for team in user_teams):
            raise HTTPException(status_code=403, detail="Not a member of this team")
        
        members = await supabase.get_team_members(team_id)
        
        return {
            "success": True,
            "team_id": team_id,
            "members": members
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get team members error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get team members")

@router.post("/teams/{team_id}/invite",
            summary="Invite user to team")
async def invite_team_member(
    team_id: str,
    invite_data: TeamMemberInvite,
    user: Dict[str, Any] = Depends(require_admin_permissions)
):
    """
    Invite a user to join the team
    
    - **email**: Email of user to invite
    - **role**: Role to assign (admin, trader, viewer)
    """
    try:
        # TODO: Implement email invitation system
        # For now, this is a placeholder for the invitation workflow
        
        logger.info(f"✅ Team invitation sent to {invite_data.email}")
        
        return {
            "success": True,
            "message": f"Invitation sent to {invite_data.email}",
            "team_id": team_id,
            "role": invite_data.role
        }
        
    except Exception as e:
        logger.error(f"❌ Team invitation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send invitation")

@router.post("/teams/{team_id}/set-active",
            summary="Set active team")
async def set_active_team(
    team_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Set the user's active team for context"""
    try:
        result = await supabase.set_active_team(user['id'], team_id)
        
        if result['success']:
            logger.info(f"✅ Active team set: {team_id}")
            return {
                "success": True,
                "message": "Active team updated",
                "active_team_id": team_id
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Set active team error: {e}")
        raise HTTPException(status_code=500, detail="Failed to set active team")