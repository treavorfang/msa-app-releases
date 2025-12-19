"""BranchService - Organization Branch Management.

This service manages multiple branch locations for the business.
"""

from typing import List, Optional
from interfaces.ibranch_service import IBranchService
from repositories.branch_repository import BranchRepository
from models.branch import Branch
from models.user import User
from services.audit_service import AuditService


class BranchService(IBranchService):
    """Service class for Branch operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize BranchService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self.repository = BranchRepository()
        self.audit_service = audit_service
        
    def create_branch(self, branch_data: dict, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> Branch:
        """Create a new branch location."""
        branch = self.repository.create(branch_data)
        self.audit_service.log_action(
            user=current_user,
            action="branch_create",
            table_name="branches",
            new_data={
                'branch_id': branch.id,
                'name': branch.name,
                'address': branch.address
            },
            ip_address=ip_address
        )
        return branch
        
    def get_branch(self, branch_id: int) -> Optional[Branch]:
        """Get a branch by ID."""
        return self.repository.get(branch_id)
        
    def update_branch(self, branch_id: int, update_data: dict, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> Optional[Branch]:
        """Update a branch's details."""
        old_branch = self.repository.get(branch_id)
        branch = self.repository.update(branch_id, update_data)
        if branch and old_branch:
            self.audit_service.log_action(
                user=current_user,
                action="branch_update",
                table_name="branches",
                old_data={
                    'name': old_branch.name,
                    'address': old_branch.address,
                    'phone': old_branch.phone
                },
                new_data={
                    'name': branch.name,
                    'address': branch.address,
                    'phone': branch.phone
                },
                ip_address=ip_address
            )
        return branch
        
    def delete_branch(self, branch_id: int, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> bool:
        """Delete a branch."""
        branch = self.repository.get(branch_id)
        if not branch:
            return False
            
        success = self.repository.delete(branch_id)
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="branch_delete",
                table_name="branches",
                old_data={
                    'branch_id': branch.id,
                    'name': branch.name
                },
                ip_address=ip_address
            )
        return success
        
    def list_branches(self) -> List[Branch]:
        """List all branches."""
        return self.repository.list_all()
        
    def search_branches(self, search_term: str) -> List[Branch]:
        """Search branches by name or address."""
        return self.repository.search(search_term)