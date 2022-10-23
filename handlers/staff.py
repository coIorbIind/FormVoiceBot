import datetime

import pydantic
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ParseMode
from sqlalchemy.exc import InvalidRequestError

from .base import BaseHandler
from logic.recognition import Recognizer
from logic.generation import generate_voice_message
from db.crud import create_staff_user


class StaffForm(StatesGroup):
    """ Форма создания нового объекта сотрудника """
    surname = State()
    name = State()
    patronymic = State()
    birth_date = State()
    age = State()


class CheckKeyboard:
    def __init__(self, text, message):
        self.keyboard = types.InlineKeyboardMarkup(row_width=2)
        yes = types.InlineKeyboardButton(text='Подтвердить ✅', callback_data=text, message=message)
        no = types.InlineKeyboardButton(text='Отменить ❌', callback_data='no')
        self.keyboard.add(yes)
        self.keyboard.add(no)

    def __call__(self, *args, **kwargs):
        return self.keyboard


class ModelFactory:
    class ModelForm(StatesGroup):
        pass

    def __init__(self, model_name):
        self.fields = [field for field in model_name.__dict__.keys() if not field.starts_with('_')]

    def __call__(self, *args, **kwargs):
        form = self.ModelForm()
        for field in self.fields:
            form.__setattr__(field, State())
        return form


class VoicesHandler(BaseHandler):
    async def get_result_text(self, file_on_disk: str) -> str:
        """ Получение текста для отправки пользователю ответа """
        try:
            text = Recognizer.recognize_text(file_on_disk)
            return text
        except ConnectionError:
            return 'Не удалось распознать текст. Проверьте подключение к интернету'
        except ValueError:
            return 'Текст не распознан'

    async def voice_message_handler(self, message: types.Message) -> None:
        """ Обработка команды """
        voice = await message.voice.get_file()
        file = await message.bot.get_file(voice.file_id)
        file_path = file.file_path
        file_on_disk = f'media/{voice.file_unique_id}.ogg'
        await message.bot.download_file(file_path, destination=file_on_disk)
        text = await self.get_result_text(file_on_disk)
        try:
            comm, prep_text = self.parser.parse_command(text)
        except ValueError:
            voice_message = await generate_voice_message('Команда нераспознана')
            await message.answer_voice(voice_message)
            return

        if comm in self.create_commands:
            try:
                table_name = self.parser.parse_table_name(self.table_names, prep_text)
            except ValueError:
                voice_message = await generate_voice_message('Таблица не найдена')
                await message.answer_voice(voice_message)
                return
            if table_name == 'Сотрудник':
                voice_message = await generate_voice_message('Введите фамилию сотрудника')
                await StaffForm.surname.set()
                await message.answer_voice(voice_message)
        else:
            voice_message = await generate_voice_message(text)
            await message.answer_voice(voice_message)

    async def voice_message_with_state_handler(self, message: types.Message, state: FSMContext) -> None:
        """ Обработка установки значения для поля формы """
        voice = await message.voice.get_file()
        file = await message.bot.get_file(voice.file_id)
        file_path = file.file_path
        file_on_disk = f'media/{voice.file_unique_id}.ogg'
        await message.bot.download_file(file_path, destination=file_on_disk)
        text = await self.get_result_text(file_on_disk)
        reply_markup = CheckKeyboard(text, message)
        await message.answer(f'Вы ввели: {text}', reply_markup=reply_markup())

    async def check_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """ Подтверждение заполнения поля """
        await callback.answer()
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        next_texts = {
            'surname': 'Введите имя сотрудника',
            'name': 'Введите отчество сотрудника',
            'patronymic': 'Введите дату рождения сотрудника',
            'birth_date': 'Введите возраст сотрудника'
        }
        state_name = (await state.get_state()).split(':')[-1]
        if callback.data == 'no':
            await callback.message.answer(f'Повторите ввод')
        else:
            field_value = callback.data
            if state_name == 'age':
                try:
                    field_value = int(callback.data)
                except ValueError:
                    voice_message = await generate_voice_message('Возраст должен быть числом')
                    await callback.message.answer_voice(voice_message)
                    return
            if state_name == 'birth_date':
                field_value = datetime.date(day=1, month=1, year=2020)

            async with state.proxy() as data:
                data[state_name] = field_value
            if state_name == 'age':
                try:
                    new_staff_user = create_staff_user(self.session, data)
                except (pydantic.ValidationError, InvalidRequestError):
                    voice_message = await generate_voice_message('Некорретные даные. '
                                                                 'Не удалось создать такого сотрудника}')
                    await callback.message.answer_voice(voice_message)
                    return
                dct = new_staff_user.__class__.__dict__
                result = ''
                for key in dct.keys():
                    if not key.startswith('_') and key in data:
                        result += f'{dct[key].name}: {data[key]}\n'
                await callback.message.answer(f'<b>Cоздан новый сотрудник</b>\n'
                                              f'{result}', parse_mode=ParseMode.HTML)
            else:
                voice_message = await generate_voice_message(next_texts[state_name])
                await StaffForm.next()
                await callback.message.answer_voice(voice_message)

    def __call__(self, dp: Dispatcher):
        dp.register_message_handler(self.voice_message_handler, content_types=types.ContentType.VOICE)
        dp.register_message_handler(self.voice_message_with_state_handler, content_types=types.ContentType.VOICE,
                                    state=StaffForm.states)
        dp.register_callback_query_handler(self.check_callback, state=StaffForm.states)
