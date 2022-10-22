from aiogram import types
from aiogram import Dispatcher
from io import BytesIO
from gtts import gTTS


async def start_command(message: types.Message) -> None:
    """
    Приветствие
    :param message: сообщение от пользователя
    """
    await message.answer(
        text=f"Привет!"
    )


def register_command_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(start_command, commands=["start", "help"])
