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
    room_id: Optional[str] = Field(None, min_length=1, max_length=20)
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
    guest_id: Optional[str] = Field(None, min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    contact_info: str = Field(..., min_length=1, max_length=100)
    nationality: str = Field(default="Indian", min_length=1, max_length=50)
    gender: str = Field(default="Other", pattern=r"^(Male|Female|Other)$")
    password: Optional[str] = Field(None, min_length=4, max_length=100)


# --- Reservation ---
class ReservationCreate(BaseModel):
    res_id: Optional[str] = Field(None, min_length=1, max_length=20)
    check_in_date: date
    check_out_date: date
    guest_id: str = Field(..., min_length=1)
    room_id: Optional[str] = Field(None, min_length=1, max_length=20)
    room_no: Optional[int] = Field(None, gt=0)
    staff_id: Optional[str] = Field(default="S001", min_length=1)


# --- Room Search ---
class RoomSearch(BaseModel):
    hotel_id: Optional[str] = None
    location: Optional[str] = None
    category_name: Optional[str] = None
    max_rent: Optional[float] = None
    status: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
