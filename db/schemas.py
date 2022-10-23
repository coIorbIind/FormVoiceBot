import datetime

from pydantic import BaseModel


class StaffCreate(BaseModel):
    surname: str
    name: str
    patronymic: str
    birth_date: datetime.date
    age: int


class StaffGet(StaffCreate):
    id: int
