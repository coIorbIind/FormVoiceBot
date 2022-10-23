from sqlalchemy import Column, Integer, String, Date

from .database import Base


class Staff(Base):
    __tablename__ = "Сотрудник"

    id = Column(Integer, name='id', primary_key=True, autoincrement=True, index=True,)
    surname = Column(String, name='Фамилия', index=True)
    name = Column(String, name='Имя', index=True)
    patronymic = Column(String, name='Отчество', index=True)
    birth_date = Column(Date, name='Дата рождения', index=True)
    age = Column(Integer, name='Возраст', index=True)
