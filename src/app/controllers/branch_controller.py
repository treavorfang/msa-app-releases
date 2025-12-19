# src/app/controllers/branch_controller.py
from PySide6.QtCore import QObject, Signal
from models.branch import Branch
from typing import List, Optional

class BranchController(QObject):
    branch_created = Signal(Branch)
    branch_updated = Signal(Branch)
    branch_deleted = Signal(int)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.branch_service = container.branch_service
        
    def create_branch(self, branch_data: dict) -> Optional[Branch]:
        branch = self.branch_service.create_branch(branch_data)
        if branch:
            self.branch_created.emit(branch)
        return branch
        
    def get_branch(self, branch_id: int) -> Optional[Branch]:
        return self.branch_service.get_branch(branch_id)
        
    def update_branch(self, branch_id: int, update_data: dict) -> Optional[Branch]:
        branch = self.branch_service.update_branch(branch_id, update_data)
        if branch:
            self.branch_updated.emit(branch)
        return branch
        
    def delete_branch(self, branch_id: int) -> bool:
        success = self.branch_service.delete_branch(branch_id)
        if success:
            self.branch_deleted.emit(branch_id)
        return success
        
    def list_branches(self) -> List[Branch]:
        return self.branch_service.list_branches()
        
    def search_branches(self, search_term: str) -> List[Branch]:
        return self.branch_service.search_branches(search_term)