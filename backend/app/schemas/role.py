from pydantic import BaseModel
from typing import List, Optional

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

class RoleCreate(RoleBase):
    permissions: Optional[List[RolePermissionCreate]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    permissions: List[RolePermissionResponse] = []
    class Config:
        from_attributes = True
