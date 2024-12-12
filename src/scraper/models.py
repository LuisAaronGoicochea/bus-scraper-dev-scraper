from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict

class Bus(BaseModel):
    """Model representing a school bus listing."""
    id: Optional[int] = Field(None, description="Unique identifier for the bus")
    title: Optional[str] = Field(None, max_length=256, description="Title of the bus listing")
    year: Optional[str] = Field(None, max_length=10, description="Year of manufacture")
    make: Optional[str] = Field(None, max_length=25, description="Make of the bus")
    model: Optional[str] = Field(None, max_length=50, description="Model of the bus")
    body: Optional[str] = Field(None, max_length=25, description="Body type of the bus")
    chassis: Optional[str] = Field(None, max_length=25, description="Chassis type")
    engine: Optional[str] = Field(None, max_length=60, description="Engine type")
    transmission: Optional[str] = Field(None, max_length=60, description="Transmission type")
    mileage: Optional[str] = Field(None, max_length=100, description="Mileage of the bus")
    passengers: Optional[str] = Field(None, max_length=60, description="Passenger capacity")
    wheelchair: Optional[str] = Field(None, max_length=60, description="Wheelchair accessibility")
    color: Optional[str] = Field(None, max_length=60, description="Color of the bus")
    interior_color: Optional[str] = Field(None, max_length=60, description="Interior color")
    exterior_color: Optional[str] = Field(None, max_length=60, description="Exterior color")
    published: Optional[bool] = Field(False, description="Whether the bus is published")
    featured: Optional[bool] = Field(False, description="Whether the bus is featured")
    sold: Optional[bool] = Field(False, description="Whether the bus is sold")
    scraped: Optional[bool] = Field(False, description="Whether the bus is scraped")
    draft: Optional[bool] = Field(False, description="Whether the bus is a draft")
    source: Optional[str] = Field(None, max_length=300, description="Source of the listing")
    source_url: Optional[str] = Field(None, max_length=1000, description="Source URL")
    price: Optional[str] = Field(None, max_length=30, description="Price of the bus")
    vin: Optional[str] = Field(None, max_length=60, description="Vehicle Identification Number")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    gvwr: Optional[str] = Field(None, max_length=50, description="Gross Vehicle Weight Rating")
    dimensions: Optional[str] = Field(None, max_length=300, description="Bus dimensions")
    luggage: Optional[bool] = Field(False, description="Whether the bus has luggage storage")
    state_bus_standard: Optional[str] = Field(None, max_length=25, description="State bus standard")
    airconditioning: Optional[str] = Field("NONE", description="Air conditioning type")
    location: Optional[str] = Field(None, max_length=30, description="Location of the bus")
    brake: Optional[str] = Field(None, max_length=30, description="Brake type")
    contact_email: Optional[str] = Field(None, max_length=100, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=100, description="Contact phone")
    us_region: Optional[str] = Field("OTHER", description="US region")
    description: Optional[str] = Field(None, description="Description of the bus")
    score: Optional[int] = Field(0, description="Score of the bus")
    category_id: Optional[int] = Field(0, description="Category ID")

    @validator("title")
    def validate_title(cls, value):
        if not value.strip():
            raise ValueError("Title cannot be empty or whitespace.")
        return value

class BusOverview(BaseModel):
    """Model representing an overview of a bus."""
    id: Optional[int] = Field(None, description="Unique identifier for the bus overview")
    bus_id: Optional[int] = Field(None, description="Foreign key to Bus")
    mdesc: Optional[str] = Field(None, description="Main description")
    intdesc: Optional[str] = Field(None, description="Interior description")
    extdesc: Optional[str] = Field(None, description="Exterior description")
    features: Optional[str] = Field(None, description="Features of the bus")
    specs: Optional[str] = Field(None, description="Specifications of the bus")

class BusImage(BaseModel):
    """Model representing images of a bus."""
    id: Optional[int] = Field(None, description="Unique identifier for the bus image")
    name: Optional[str] = Field(None, max_length=64, description="Name of the image")
    url: Optional[str] = Field(None, max_length=1000, description="URL of the image")
    description: Optional[str] = Field(None, description="Description of the image")
    image_index: Optional[int] = Field(0, description="Index of the image")
    bus_id: Optional[int] = Field(None, description="Foreign key to Bus")