from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State

from .base import BaseHandler
from logic.recognition import Recognizer
from logic.generation import generate_voice_message


class StaffForm(StatesGroup):
    """
    Форма создания нового объекта сотрудника
    """
    surname = State()
    name = State()
    patronymic = State()
    birth_date = State()
    age = State()


class CheckKeyboard:
    def __init__(self, text, message):
        self.keyboard = types.InlineKeyboardMarkup(row_width=2)
        yes = types.InlineKeyboardButton(text='Подтвердить', callback_data=text, message=message)
        no = types.InlineKeyboardButton(text='Отменить', callback_data='no')
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

    async def voice_message_handler(self, message: types.Message) -> None:
        voice = await message.voice.get_file()
        file = await message.bot.get_file(voice.file_id)
        file_path = file.file_path
        file_on_disk = f'media/{voice.file_unique_id}.ogg'
        await message.bot.download_file(file_path, destination=file_on_disk)
        text = Recognizer.recognize_text(file_on_disk)
        print(text)
        if text == 'создать нового сотрудника':
            voice_message = await generate_voice_message('Введите фамилию сотрудника')
            await StaffForm.surname.set()
            await message.answer_voice(voice_message)
        else:
            voice_message = await generate_voice_message('Не получилось распознать сообщение')
            await message.answer_voice(voice_message)

    async def surname_voice_message_handler(self, message: types.Message, state: FSMContext) -> None:
        voice = await message.voice.get_file()
        file = await message.bot.get_file(voice.file_id)
        file_path = file.file_path
        file_on_disk = f'media/{voice.file_unique_id}.ogg'
        await message.bot.download_file(file_path, destination=file_on_disk)
        text = Recognizer.recognize_text(file_on_disk)
        print(text)
        reply_markup = CheckKeyboard(text, message)
        await message.answer(f'Вы ввели: {text}', reply_markup=reply_markup())

    async def check_callback(self, callback: types.CallbackQuery, state: FSMContext):
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
            async with state.proxy() as data:
                data[state_name] = callback.data
            if state_name == 'age':
                result = ''
                for key, value in data.items():
                    result += f'{key}: {value}\n'
                await callback.message.answer(f'**Данные формы**\n'
                                              f'{result}')
            else:
                voice_message = await generate_voice_message(next_texts[state_name])
                await StaffForm.next()
                await callback.message.answer_voice(voice_message)

    def __call__(self, dp: Dispatcher):
        dp.register_message_handler(self.voice_message_handler, content_types=types.ContentType.VOICE)
        dp.register_message_handler(self.surname_voice_message_handler, content_types=types.ContentType.VOICE,
                                    state=StaffForm.states)
        dp.register_callback_query_handler(self.check_callback, state=StaffForm.states)
