from aiogram import Dispatcher

from sqlalchemy.orm import Session


class BaseHandler:

    def __init__(self, db: Session):
        self.session = db

    def __call__(self, dp: Dispatcher) -> None:
        raise NotImplemented()
