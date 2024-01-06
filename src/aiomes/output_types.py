from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HouseworkType(BaseModel):
    subject_name: str
    hw_date: datetime
    description: str
    attached_tests: list
    attached_files: list


class ScheduleType(BaseModel):
    name: str
    room_number: Optional[str]
    marks: Optional[list]
    start_time: str
    end_time: str
    is_replaced: bool


class ShortScheduleType(BaseModel):
    name: str
    start_time: str
    end_time: str


class BaseMarkType(BaseModel):
    subject_name: str
    mark_date: datetime
    value: str
    weight: int
    reason: Optional[str]


class TrimesterMarksType(BaseModel):
    subject_name: str
    average_mark: str
    final_mark: Optional[str]
    marks: list


class SchoolInfoType(BaseModel):
    name: str
    principal: str
    address: str
    site: Optional[str]
    email: str
    branches: int


class DocumentType(BaseModel):
    type_id: int
    series: Optional[str]
    number: Optional[str]
    issue_date: Optional[str]
    issuer: str


class MealType(BaseModel):
    name: str
    ingredients: str
    calories: float


class ComplexMealType(BaseModel):
    title: str
    price: float
    composition: List[MealType]


class BuffetMenuType(BaseModel):
    name: str
    full_name: str
    is_available: bool
    price: float


class VisitType(BaseModel):
    visit_date: str
    in_time: str
    out_time: str
    duration: str


class RankingType(BaseModel):
    rank_date: str
    place: int


class NotificationType(BaseModel):
    event_date: datetime
    event_name: str
    subject_name: str
    hw_description: Optional[str]
    mark_value: Optional[str]
    mark_weight: Optional[int]


class PrevYearMarksType(BaseModel):
    subject_name: str
    final_mark: Optional[int]


class PeriodsScheduleType(BaseModel):
    name: str
    starts: Optional[str]
    ends: Optional[str]
