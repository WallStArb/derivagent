"""
Authentication middleware for Derivagent FastAPI
Handles JWT validation and team context setting
"""

import os
import jwt
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .supabase_client import get_supabase_auth
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
JWT_ALGORITHM = 'HS256'

security = HTTPBearer()

class AuthMiddleware:
    """Handles authentication and authorization"""
    
    def __init__(self):
        self.supabase = get_supabase_auth()
    
    async def get_current_user(self, 
                              credentials: HTTPAuthorizationCredentials = Depends(security)
                              ) -> Dict[str, Any]:
        """Extract and validate user from JWT token"""
        try:
            token = credentials.credentials
            
            # Decode JWT token
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True}
            )
            
            user_id = payload.get('sub')
            email = payload.get('email')
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Get user teams and active team
            teams = await self.supabase.get_user_teams(user_id)
            active_team = self._get_active_team(teams, payload)
            
            user_data = {
                "id": user_id,
                "email": email,
                "teams": teams,
                "active_team": active_team,
                "metadata": payload.get('user_metadata', {}),
                "role": payload.get('role', 'authenticated')
            }
            
            logger.info(f"✅ User authenticated: {email}")
            return user_data
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def require_permissions(self, 
                                 required_permissions: list,
                                 user: Dict[str, Any] = Depends(get_current_user)
                                 ) -> Dict[str, Any]:
        """Check if user has required permissions"""
        try:
            active_team = user.get('active_team')
            if not active_team:
                raise HTTPException(status_code=403, detail="No active team selected")
            
            user_role = active_team.get('user_role', 'viewer')
            permissions = self.supabase._get_role_permissions(user_role)
            
            # Check each required permission
            for permission in required_permissions:
                if not permissions.get(permission, False):
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Permission denied: {permission}"
                    )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Permission check error: {e}")
            raise HTTPException(status_code=403, detail="Permission check failed")
    
    async def set_team_context(self, 
                              team_id: str,
                              user: Dict[str, Any] = Depends(get_current_user)
                              ) -> Dict[str, Any]:
        """Set active team context for RLS"""
        try:
            # Verify user is member of team
            user_teams = user.get('teams', [])
            team_found = any(team['id'] == team_id for team in user_teams)
            
            if not team_found:
                raise HTTPException(status_code=403, detail="Not a member of this team")
            
            # Set active team in Supabase
            result = await self.supabase.set_active_team(user['id'], team_id)
            
            if result['success']:
                # Update user context
                user['active_team'] = next(
                    team for team in user_teams if team['id'] == team_id
                )
                logger.info(f"✅ Team context set: {team_id}")
                return user
            else:
                raise HTTPException(status_code=400, detail=result['error'])
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Set team context error: {e}")
            raise HTTPException(status_code=400, detail="Failed to set team context")
    
    def _get_active_team(self, teams: list, jwt_payload: dict) -> Optional[Dict[str, Any]]:
        """Get user's active team from teams list"""
        if not teams:
            return None
        
        # Check if there's a preferred team in JWT
        preferred_team_id = jwt_payload.get('active_team_id')
        if preferred_team_id:
            for team in teams:
                if team['id'] == preferred_team_id:
                    return team
        
        # Default to first team (usually the user's personal team)
        return teams[0] if teams else None

# Dependency injection helpers
auth_middleware = AuthMiddleware()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    return await auth_middleware.get_current_user(credentials)

async def require_trader_permissions(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require trader-level permissions"""
    return await auth_middleware.require_permissions(['execute_trades'], user)

async def require_admin_permissions(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require admin-level permissions"""
    return await auth_middleware.require_permissions(['manage_members'], user)

async def require_owner_permissions(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require owner-level permissions"""
    return await auth_middleware.require_permissions(['manage_team'], user)

# Optional auth for public endpoints
async def get_current_user_optional(
    request: Request
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None if not"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        credentials = HTTPAuthorizationCredentials(
            scheme='Bearer',
            credentials=auth_header.split(' ')[1]
        )
        
        return await auth_middleware.get_current_user(credentials)
    except:
        return None