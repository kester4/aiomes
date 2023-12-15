from pydantic import BaseModel
from typing import Optional


class HouseworkType(BaseModel):
    subject_name: str
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
    value: str
    weight: int
    reason: Optional[str]


class TrimesterMarksType(BaseModel):
    subject_name: str
    average_mark: str
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


class VisitType(BaseModel):
    visit_date: str
    in_time: str
    out_time: str
    duration: str


class RankingType(BaseModel):
    rank_date: str
    place: int


class PrevYearMarksType(BaseModel):
    subject_name: str
    final_mark: Optional[int]


class PeriodsScheduleType(BaseModel):
    name: str
    starts: Optional[str]
    ends: Optional[str]
