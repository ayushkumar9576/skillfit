"""
app/schemas/profile.py
----------------------
Schemas for profile completion and updates.
"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

class ProfileUpdateSchema(BaseModel):
    branch: Optional[str] = Field(None, max_length=100, description="Academic branch (Student)")
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="CGPA out of 10 (Student)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number (Student)")
    department: Optional[str] = Field(None, max_length=150, description="Academic department (Faculty)")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL (Student)")
    github_url: Optional[HttpUrl] = Field(None, description="GitHub profile URL (Student)")
    portfolio_url: Optional[HttpUrl] = Field(None, description="Personal portfolio URL (Student)")
