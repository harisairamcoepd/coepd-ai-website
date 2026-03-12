from pydantic import BaseModel, Field


class UserCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=120)
    role: str = Field(default="staff", max_length=20)


class UserRoleUpdatePayload(BaseModel):
    role: str = Field(min_length=5, max_length=20)


class UserActiveUpdatePayload(BaseModel):
    is_active: bool


class LeadStatusPayload(BaseModel):
    working_status: str = Field(min_length=1, max_length=80)


class StaffCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=120)
    role: str = Field(default="staff", max_length=20)


class StaffPasswordUpdatePayload(BaseModel):
    password: str = Field(min_length=6, max_length=120)
