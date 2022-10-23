from aiogram import Dispatcher

from sqlalchemy.orm import Session

from logic.recognition import TextParser
from db.models import Base


class BaseHandler:

    def __init__(self, db: Session):
        self.session = db
        self.create_commands = ('добавить', 'заполнить', 'создать')
        self.update_commands = ('изменить', )
        self.table_names = [table.__tablename__ for table in Base.__subclasses__()]

        com_stop_word_dict = {
            self.create_commands: ['нового'],
            self.update_commands: [],
        }
        self.parser = TextParser(com_stop_word_dict)

    def __call__(self, dp: Dispatcher) -> None:
        raise NotImplemented()
