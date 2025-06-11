from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
import re


class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    CLIENT = "client"


class UserPermissions(str, Enum):
    CREATE_BOOKING = "create_booking"
    VIEW_BOOKING = "view_booking"
    CANCEL_BOOKING = "cancel_booking"
    MANAGE_USERS = "manage_users"
    VIEW_REPORTS = "view_reports"
    MANAGE_ROOMS = "manage_rooms"
    PROCESS_PAYMENTS = "process_payments"
    VIEW_ANALYTICS = "view_analytics"


class RoleSchema(BaseModel):
    name: UserRole
    permissions: List[UserPermissions] = []

    class Config:
        use_enum_values = True


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")
    email: EmailStr
    telephone: Optional[str] = Field(None, description="Número de teléfono")

    @validator('telephone')
    def validate_telephone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=50, description="Contraseña del usuario")
    role: UserRole = UserRole.CLIENT

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    telephone: Optional[str] = None

    @validator('telephone')
    def validate_telephone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v


class UserResponse(UserBase):
    id: str
    roles: List[RoleSchema] = []
    active: bool = Field(alias="is_active")  # Mapear 'active' a 'is_active'
    is_verified: bool = False
    creation_date: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True  # Permite usar tanto 'active' como 'is_active'


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str


class TokenData(BaseModel):
    """Schema para datos del token"""
    email: Optional[str] = None
    user_id: Optional[str] = None


class TokenResponse(BaseModel):
    """Schema para respuesta de autenticación"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hora en segundos
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """Schema para solicitud de reset de contraseña"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema para reset de contraseña"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=50)
    confirm_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


class UserListResponse(BaseModel):
    """Schema para lista de usuarios (admin)"""
    users: List[UserResponse]
    total: int
    page: int
    limit: int