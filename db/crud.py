from sqlalchemy.orm import Session

from . import models, schemas


def create_staff_user(db: Session, staff: dict) -> models.Staff:
    pydantic_user = schemas.StaffCreate(**staff)
    db_user = models.Staff(
        surname=pydantic_user.surname,
        name=pydantic_user.name,
        patronymic=pydantic_user.patronymic,
        birth_date=pydantic_user.birth_date,
        age=pydantic_user.age)
    db.add(db_user)
    db.commit()
    return db_user
