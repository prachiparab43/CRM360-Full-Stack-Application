from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class RolePermissionBase(BaseModel):
    module: str
    action: str
    data_scope: str

class RolePermissionCreate(RolePermissionBase):
    pass

class RolePermissionResponse(RolePermissionBase):
    id: int
    role_id: int
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "Active"
    is_system: Optional[bool] = False

class RoleCreate(RoleBase):
    permissions: Optional[List[RolePermissionCreate]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[List[RolePermissionCreate]] = None

class RoleResponse(RoleBase):
    id: int
    is_system: bool = False
    permissions: List[RolePermissionResponse] = []
    class Config:
        from_attributes = True

class RoleCatalogResponse(BaseModel):
    modules: List[str]
    actions: Dict[str, List[str]]
    scopes: List[str]
    restricted_scopes: Dict[str, List[str]]

class PermissionHistoryItem(BaseModel):
    id: int
    timestamp: Optional[Any] = None
    user_id: Optional[int] = None
    action: str
    old_permissions: Optional[List[Dict[str, Any]]] = None
    new_permissions: Optional[List[Dict[str, Any]]] = None
