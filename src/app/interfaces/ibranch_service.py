# src/app/interfaces/ibranch_service.py
from abc import ABC, abstractmethod
from models.branch import Branch
from typing import Optional, List

class IBranchService(ABC):
    @abstractmethod
    def create_branch(self, branch_data: dict) -> Branch:
        pass
        
    @abstractmethod
    def get_branch(self, branch_id: int) -> Optional[Branch]:
        pass
        
    @abstractmethod
    def update_branch(self, branch_id: int, update_data: dict) -> Optional[Branch]:
        pass
        
    @abstractmethod
    def delete_branch(self, branch_id: int) -> bool:
        pass
        
    @abstractmethod
    def list_branches(self) -> List[Branch]:
        pass
        
    @abstractmethod
    def search_branches(self, search_term: str) -> List[Branch]:
        pass