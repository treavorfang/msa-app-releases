"""TechnicianService - Technician Management Logic.

This service manages technician profiles using DTOs.
"""

from typing import List, Optional, Any, Dict
from interfaces.itechnician_service import ITechnicianService
from repositories.technician_repository import TechnicianRepository
from models.technician import Technician
from services.audit_service import AuditService
from dtos.technician_dto import TechnicianDTO


class TechnicianService(ITechnicianService):
    """Service class for Technician operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize TechnicianService."""
        self.repository = TechnicianRepository()
        self.audit_service = audit_service
        
    def create_technician(self, technician_data: dict, current_user=None, ip_address=None) -> TechnicianDTO:
        """Create a new technician profile and linked User account."""
        from models.user import User
        from models.role import Role
        from utils.security.password_utils import hash_password

        # 1. Prepare User Data
        email = technician_data.get('email')
        full_name = technician_data.get('full_name', 'Unknown')
        password_plain = technician_data.get('password') # Plain text from form
        
        # Generate username if not provided (from email or name)
        username = email.split('@')[0] if email else full_name.lower().replace(" ", ".")
        
        # Check if user already exists
        existing_user = None
        if email:
            existing_user = User.get_or_none(User.email == email)
        if not existing_user and username:
            existing_user = User.get_or_none(User.username == username)
            
        linked_user = existing_user
        
        if not linked_user:
            # Create NEW User
            tech_role = Role.get_or_none(Role.name == "Technician")
            
            # Hash password if provided, else default?
            # Note: Tech model previously stored hash or plain? 
            # Controller usually sends what it got. If it's a new tech form, it's likely plain.
            # We must hash it for User table.
            
            pwd_hash = hash_password(password_plain) if password_plain else hash_password("ChangeMe123!")
            
            try:
                linked_user = User.create(
                    username=username,
                    full_name=full_name,
                    email=email,
                    password_hash=pwd_hash,
                    role=tech_role,
                    is_active=technician_data.get('is_active', True)
                )
            except Exception as e:
                # Handle username collision by appending random?
                # For now let it bubble or fail if strict
                print(f"Failed to create user for tech: {e}")
                raise e
        
        # 2. Link User to Tech Data
        technician_data['user'] = linked_user
        # We can also sync fields to ensure consistency
        
        # 3. Create Tech
        technician = self.repository.create(technician_data)
        dto = TechnicianDTO.from_model(technician)
        
        self.audit_service.log_action(
            user=current_user,
            action="technician_create",
            table_name="technicians",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_technician(self, technician_id: int) -> Optional[TechnicianDTO]:
        """Get a technician by ID."""
        tech = self.repository.get(technician_id)
        return TechnicianDTO.from_model(tech) if tech else None
        
    def get_technician_by_user(self, user_id: int) -> Optional[TechnicianDTO]:
        """Get a technician profile linked to a user ID."""
        tech = self.repository.get_by_user(user_id)
        return TechnicianDTO.from_model(tech) if tech else None
        
    def update_technician(self, technician_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[TechnicianDTO]:
        """Update a technician's profile and sync to User."""
        from utils.security.password_utils import hash_password

        old_tech = self.repository.get(technician_id)
        if not old_tech:
            return None
            
        old_dto = TechnicianDTO.from_model(old_tech)
        
        # 1. Sync User Fields
        if old_tech.user:
            user = old_tech.user
            user_changed = False
            
            if 'full_name' in update_data:
                user.full_name = update_data['full_name']
                user_changed = True
            
            if 'email' in update_data and update_data['email'] != user.email:
                user.email = update_data['email']
                user_changed = True
                
            if 'is_active' in update_data:
                user.is_active = update_data['is_active']
                user_changed = True
                
            if 'password' in update_data and update_data['password']:
                # Assume plaintext if being updated
                user.password_hash = hash_password(update_data['password'])
                user_changed = True
                
            if user_changed:
                user.save()
        
        # 2. Update Tech Fields
        technician = self.repository.update(technician_id, update_data)
        
        if technician:
            new_dto = TechnicianDTO.from_model(technician)
            self.audit_service.log_action(
                user=current_user,
                action="technician_update",
                table_name="technicians",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_technician(self, technician_id: int, current_user=None, ip_address=None) -> bool:
        """Deactivate a technician and linked User (soft delete)."""
        tech = self.repository.get(technician_id)
        if not tech:
            return False
            
        dto = TechnicianDTO.from_model(tech)
        
        # 1. Deactivate User
        if tech.user:
            tech.user.deactivate()
            
        # 2. Deactivate Tech
        success = self.repository.deactivate(technician_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="technician_delete",
                table_name="technicians",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def get_all_technicians(self) -> List[TechnicianDTO]:
        """List all technicians."""
        # Defaults to all (both active and inactive usually, or just active? Interface said get_all)
        # Service list_technicians had active_only default True.
        # I'll implement get_all (all) and get_active separately or via argument 
        # But Interface defined get_all and get_active
        techs = self.repository.list_all(active_only=False)
        return [TechnicianDTO.from_model(t) for t in techs]
        
    def get_active_technicians(self) -> List[TechnicianDTO]:
        """List active technicians."""
        techs = self.repository.list_all(active_only=True)
        return [TechnicianDTO.from_model(t) for t in techs]
        
    def search_technicians(self, query: str) -> List[TechnicianDTO]:
        """Search technicians."""
        techs = self.repository.search(query)
        return [TechnicianDTO.from_model(t) for t in techs]