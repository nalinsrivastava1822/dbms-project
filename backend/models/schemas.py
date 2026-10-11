"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# --- Hotel ---
class HotelCreate(BaseModel):
    hotel_id: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    rating: float = Field(..., ge=0, le=5)


# --- Room Category ---
class RoomCategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=50)
    rent: float = Field(..., gt=0)


# --- Room ---
class RoomCreate(BaseModel):
    room_no: int = Field(..., gt=0)
    status: str = Field(default="Available")
    hotel_id: str = Field(..., min_length=1)
    category_name: str = Field(..., min_length=1)


class RoomStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(Available|Occupied|Maintenance)$")


# --- Department ---
class DepartmentCreate(BaseModel):
    dept_id: str = Field(..., min_length=1, max_length=10)
    d_head: str = Field(..., min_length=1, max_length=100)
    d_role: str = Field(..., min_length=1, max_length=100)
    contact_info: str = Field(..., min_length=1, max_length=20)
    hotel_id: str = Field(..., min_length=1)


# --- Staff ---
class StaffCreate(BaseModel):
    staff_id: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., gt=0, lt=100)
    salary: float = Field(..., gt=0)
    contact_info: str = Field(..., min_length=1, max_length=20)
    dept_id: str = Field(..., min_length=1)


# --- Guest ---
class GuestCreate(BaseModel):
    guest_id: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    contact_info: str = Field(..., min_length=1, max_length=20)
    nationality: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., pattern=r"^(Male|Female|Other)$")


# --- Reservation ---
class ReservationCreate(BaseModel):
    res_id: str = Field(..., min_length=1, max_length=10)
    check_in_date: date
    check_out_date: date
    guest_id: str = Field(..., min_length=1)
    room_no: int = Field(..., gt=0)
    staff_id: str = Field(..., min_length=1)


# --- Room Search ---
class RoomSearch(BaseModel):
    hotel_id: Optional[str] = None
    category_name: Optional[str] = None
    max_rent: Optional[float] = None
    status: Optional[str] = None
