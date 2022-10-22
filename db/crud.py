from sqlalchemy.orm import Session

from . import models, schemas


def create_user(db: Session, staff: schemas.StaffCreate):
    db_user = models.Staff(
        surname=staff.surname,
        name=staff.name,
        patronymic=staff.patronymic,
        birth_date=staff.birth_date,
        age=staff.age)
    db.add(db_user)
    db.commit()
