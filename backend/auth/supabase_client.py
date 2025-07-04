"""
Supabase client configuration for Derivagent
Handles authentication, team management, and RLS data isolation
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import logging

logger = logging.getLogger(__name__)

class SupabaseAuth:
    """Handles Supabase authentication and team management"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        # Configure client with security options
        options = ClientOptions(
            persist_session=True,
            auto_refresh_token=True,
            detect_session_in_url=False
        )
        
        self.client: Client = create_client(self.url, self.key, options)
        logger.info("🔐 Supabase client initialized")
    
    async def sign_up(self, email: str, password: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Register new user account"""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            
            if response.user:
                logger.info(f"✅ User registered: {email}")
                return {
                    "success": True,
                    "user": response.user,
                    "session": response.session
                }
            else:
                return {"success": False, "error": "Registration failed"}
                
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return {"success": False, "error": str(e)}
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Get user's team memberships
                teams = await self.get_user_teams(response.user.id)
                
                logger.info(f"✅ User authenticated: {email}")
                return {
                    "success": True,
                    "user": response.user,
                    "session": response.session,
                    "teams": teams
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return {"success": False, "error": str(e)}
    
    async def sign_out(self) -> Dict[str, Any]:
        """Sign out current user"""
        try:
            self.client.auth.sign_out()
            logger.info("✅ User signed out")
            return {"success": True}
        except Exception as e:
            logger.error(f"❌ Sign out error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        try:
            user = self.client.auth.get_user()
            if user and user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "metadata": user.user.user_metadata,
                    "created_at": user.user.created_at
                }
            return None
        except Exception as e:
            logger.error(f"❌ Get user error: {e}")
            return None
    
    async def create_team(self, user_id: str, team_name: str, 
                         team_type: str = "individual") -> Dict[str, Any]:
        """Create new team and add user as owner"""
        try:
            # Create team record
            team_response = self.client.table('teams').insert({
                "name": team_name,
                "type": team_type,  # individual, small_firm, enterprise
                "owner_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "settings": {
                    "max_members": 1 if team_type == "individual" else 50,
                    "risk_limits": {
                        "max_position_size": 10000 if team_type == "individual" else 100000,
                        "max_daily_trades": 20 if team_type == "individual" else 200
                    }
                }
            }).execute()
            
            if team_response.data:
                team_id = team_response.data[0]['id']
                
                # Add user as team member with owner role
                await self.add_team_member(team_id, user_id, "owner")
                
                logger.info(f"✅ Team created: {team_name} (ID: {team_id})")
                return {
                    "success": True,
                    "team": team_response.data[0]
                }
            else:
                return {"success": False, "error": "Failed to create team"}
                
        except Exception as e:
            logger.error(f"❌ Team creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_team_member(self, team_id: str, user_id: str, 
                            role: str = "member") -> Dict[str, Any]:
        """Add user to team with specified role"""
        try:
            response = self.client.table('team_members').insert({
                "team_id": team_id,
                "user_id": user_id,
                "role": role,  # owner, admin, trader, viewer
                "joined_at": datetime.utcnow().isoformat(),
                "permissions": self._get_role_permissions(role)
            }).execute()
            
            if response.data:
                logger.info(f"✅ User {user_id} added to team {team_id} as {role}")
                return {"success": True, "membership": response.data[0]}
            else:
                return {"success": False, "error": "Failed to add team member"}
                
        except Exception as e:
            logger.error(f"❌ Add team member error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all teams user belongs to"""
        try:
            response = self.client.table('team_members').select(
                "*, teams(*)"
            ).eq('user_id', user_id).execute()
            
            if response.data:
                teams = []
                for membership in response.data:
                    team_data = membership['teams']
                    team_data['user_role'] = membership['role']
                    team_data['joined_at'] = membership['joined_at']
                    teams.append(team_data)
                
                logger.info(f"✅ Found {len(teams)} teams for user {user_id}")
                return teams
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Get user teams error: {e}")
            return []
    
    async def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all members of a team"""
        try:
            response = self.client.table('team_members').select(
                "*, auth.users(email, created_at, user_metadata)"
            ).eq('team_id', team_id).execute()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} members for team {team_id}")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Get team members error: {e}")
            return []
    
    async def set_active_team(self, user_id: str, team_id: str) -> Dict[str, Any]:
        """Set user's active team for RLS context"""
        try:
            # Verify user is member of team
            membership = self.client.table('team_members').select('*').eq(
                'user_id', user_id
            ).eq('team_id', team_id).execute()
            
            if not membership.data:
                return {"success": False, "error": "User not member of team"}
            
            # Update user's active team
            response = self.client.table('user_profiles').upsert({
                "user_id": user_id,
                "active_team_id": team_id,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Set RLS context for subsequent queries
            self.client.rpc('set_active_team_context', {'team_id': team_id}).execute()
            
            logger.info(f"✅ Active team set: {team_id} for user {user_id}")
            return {"success": True, "active_team_id": team_id}
            
        except Exception as e:
            logger.error(f"❌ Set active team error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_role_permissions(self, role: str) -> Dict[str, bool]:
        """Get permissions for user role"""
        permissions = {
            "owner": {
                "manage_team": True,
                "manage_members": True,
                "manage_brokers": True,
                "execute_trades": True,
                "view_positions": True,
                "view_analytics": True
            },
            "admin": {
                "manage_team": False,
                "manage_members": True,
                "manage_brokers": True,
                "execute_trades": True,
                "view_positions": True,
                "view_analytics": True
            },
            "trader": {
                "manage_team": False,
                "manage_members": False,
                "manage_brokers": False,
                "execute_trades": True,
                "view_positions": True,
                "view_analytics": True
            },
            "viewer": {
                "manage_team": False,
                "manage_members": False,
                "manage_brokers": False,
                "execute_trades": False,
                "view_positions": True,
                "view_analytics": True
            }
        }
        
        return permissions.get(role, permissions["viewer"])

# Global client instance
supabase_auth = None

def get_supabase_auth() -> SupabaseAuth:
    """Get global Supabase auth instance"""
    global supabase_auth
    if supabase_auth is None:
        supabase_auth = SupabaseAuth()
    return supabase_auth