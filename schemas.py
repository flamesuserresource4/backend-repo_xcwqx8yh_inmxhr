"""
Database Schemas for the Bariatric & General Surgery site

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., Testimonial -> "testimonial").
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class Testimonial(BaseModel):
    name: str = Field(..., description="Patient name or initials")
    procedure: Optional[str] = Field(None, description="Procedure performed")
    rating: int = Field(5, ge=1, le=5, description="Rating from 1 to 5")
    text: str = Field(..., description="Review content")
    city: Optional[str] = Field(None, description="Patient city")

class BeforeAfter(BaseModel):
    patient_code: Optional[str] = Field(None, description="Internal patient code or initials")
    procedure: Optional[str] = Field(None, description="Procedure performed")
    weight_before: Optional[float] = Field(None, ge=0)
    weight_after: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    image_before_url: Optional[str] = None
    image_after_url: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, description="Contact phone")
    message: str

class Surgery(BaseModel):
    name: str
    type: str = Field(..., description="bariatric | general")
    description: Optional[str] = None

# Optional informational schema (not persisted by default)
class DoctorProfile(BaseModel):
    full_name: str
    title: str
    bio: str
    experience_years: int
    clinic_name: str
    clinic_address: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
