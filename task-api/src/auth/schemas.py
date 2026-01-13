from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str


class UserDTO(BaseModel):
    id: UUID
    email: EmailStr
    is_deleted: bool
    is_verified: bool
    is_superuser: bool
    model_config = ConfigDict(from_attributes=True)
