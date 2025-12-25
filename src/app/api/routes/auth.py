from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from models.user import User
from models.technician import Technician
from utils.security.password_utils import verify_password
from utils.mobile_utils import generate_daily_pin
from services.audit_service import AuditService

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class PairingRequest(BaseModel):
    pin: str

@router.post("/login")
async def login(req: LoginRequest):
    """
    Authenticate a user.
    Unified Login: All users (Staff & Techs) login via User table.
    """
    try:
        from peewee import fn
        print(f"DEBUG: Login attempt for username: {req.username}")
        # Case insensitive username lookup
        user = User.get(fn.LOWER(User.username) == req.username.lower())
        
        # Verify Password
        if verify_password(user.password_hash, req.password):
            if not user.is_active:
                 raise HTTPException(status_code=401, detail="Account is disabled")

            print(f"DEBUG: Password verification success for {user.username}")
            
            # DETERMIN ROLE
            role_name = "staff"
            tech_profile = None
            
            # Check if User has a linked Technician Profile
            try:
                tech_profile = Technician.get(Technician.user == user)
                role_name = "technician"
                print(f"DEBUG: User {user.username} is a Technician (ID: {tech_profile.id})")
            except Technician.DoesNotExist:
                # Fallback to RBAC role name if exists
                if user.role:
                    role_name = user.role.name.lower()
            
            # Log Action
            try:
                AuditService.log_action(
                    user=user,
                    action="mobile_login",
                    table_name="users",
                    new_data={"role": role_name, "platform": "mobile", "tech_id": tech_profile.id if tech_profile else None},
                    ip_address="Mobile App"
                )
            except Exception as e:
                print(f"ERROR: Failed to log mobile login: {e}")
                
            response = {
                "status": "success",
                "role": role_name,
                "user": {"id": user.id, "name": user.full_name}
            }
            
            if tech_profile:
                response["tech_id"] = tech_profile.id
                
            return response

    except User.DoesNotExist:
        pass
        
    # Security: Don't reveal if user exists or password failed
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/verify-pairing")
async def verify_pairing(req: PairingRequest):
    """Verify the daily pairing PIN shown on the workshop screen."""
    daily_pin = generate_daily_pin()
    if req.pin == daily_pin:
        from datetime import datetime
        return {
            "status": "success",
            "message": "Pairing successful",
            "paired_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    raise HTTPException(status_code=401, detail="Invalid pairing PIN")
