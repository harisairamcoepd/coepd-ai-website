from pydantic import BaseModel, ConfigDict, Field


class ChatPayload(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: str = Field(default="web_user", min_length=2, max_length=100)


class LeadPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=8, max_length=20)
    email: str = Field(min_length=5, max_length=120)
    location: str = Field(default="", max_length=120)
    interested_domain: str = Field(default="", max_length=120)
    experience: str = Field(default="", max_length=80)
    demo_day: str = Field(default="", max_length=60)
    whatsapp: str = Field(default="", max_length=20)
    working_status: str = Field(default="", max_length=50)
    preferred_batch: str = Field(default="", max_length=50)
    source: str = Field(default="webpage", max_length=50)
    created_at: str | None = Field(default=None, max_length=40)


class ContactPayload(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    phone: str = Field(min_length=8, max_length=20)
    location: str = Field(default="", max_length=120)
    interested_domain: str = Field(default="", max_length=120)
    experience: str = Field(default="", max_length=80)
    demo_day: str = Field(default="", max_length=60)
    whatsapp: str = Field(default="", max_length=20)
    source: str = Field(default="webpage", max_length=50)
    created_at: str | None = Field(default=None, max_length=40)
