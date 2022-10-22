from aiogram import types
from aiogram import Dispatcher

from .base import BaseHandler


class CommandsHandler(BaseHandler):
    async def start_command(self, message: types.Message) -> None:
        """
        Приветствие
        :param message: сообщение от пользователя
        """
        await message.answer(
            text=f"Привет!"
        )

    def __call__(self, dp: Dispatcher) -> None:
        dp.register_message_handler(self.start_command, commands=["start", "help"])
