import configparser

from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from aiogram.utils.exceptions import ValidationError
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from handlers.commands import register_command_handlers


async def on_startup(_):
    print("Start")
    try:
        admin_id = int(config['ADMIN SETTINGS']['AdminId'])
        await bot.send_message(chat_id=admin_id, text="Бот запущен")
    except ValueError:
        exit("[ERROR] Admin id invalid")


if __name__ == "__main__":
    """
    Создается объект бота, диспатчера и хранилища данных.
    Регистрация обработчиков пользователесного ввода.
    Запуск long polling'а
    """
    # Создание объекта для чтения настроек
    config = configparser.ConfigParser()
    config.read('config.ini')
    # Создание хранилища данных
    storage = MemoryStorage()
    # Создание бота
    try:
        bot_token = config['BOT SETTINGS']['BotToken']

        bot = Bot(token=bot_token)
        dp = Dispatcher(bot, storage=storage)

        # Регистрания handlers
        register_command_handlers(dp)

        # Запуск поллинга
        executor.start_polling(dp, on_startup=on_startup)
    except KeyError:
        print("[ERROR] No token provided")
    except ValidationError:
        print("[ERROR] Invalid bot token")
