import json

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InputFile
from bs4 import BeautifulSoup

from logic.recognition import Recognizer, TextParser
from logic.generation import generate_voice_message


class Form(StatesGroup):
    """ Форма создания нового объекта """
    pass


class CheckKeyboard:
    def __init__(self, text, message):
        self.keyboard = types.InlineKeyboardMarkup(row_width=2)
        yes = types.InlineKeyboardButton(text='Подтвердить ✅', callback_data=text, message=message)
        no = types.InlineKeyboardButton(text='Отменить ❌', callback_data='no')
        self.keyboard.add(yes)
        self.keyboard.add(no)

    def __call__(self, *args, **kwargs):
        return self.keyboard


class HtmlHandler:
    def __init__(self, fields):
        self.fields = fields
        for field in fields:
            setattr(Form, field, State())
        self.states = [state for state in Form.__dict__ if not state.startswith('_')]
        self.data = {}
        self.create_commands = ('добавить', 'заполнить', 'создать')
        self.update_commands = ('изменить',)
        self.get_commands = ('получить', 'извлечь', 'найти')

        com_stop_word_dict = {
            self.create_commands: ['нового'],
            self.update_commands: [],
            self.get_commands: []
        }
        self.parser = TextParser(com_stop_word_dict)

    async def create_command_handler(self, message: types.Message, state: FSMContext) -> None:

        voice_message = await generate_voice_message(f'Введите {self.states[0]}.'
                                                     f'{self.fields[self.states[0]]["описание"]}')
        await message.answer_voice(voice_message)

        await state.set_state(self.states[0])

    async def get_result_text(self, file_on_disk: str) -> str:
        """ Получение текста для отправки пользователю ответа """
        try:
            text = Recognizer.recognize_text(file_on_disk)
            return text
        except ConnectionError:
            return 'Не удалось распознать текст. Проверьте подключение к интернету'
        except ValueError:
            return 'Текст не распознан'

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
        if callback.data == 'no':
            await callback.message.answer('Повторите ввод')
        else:
            state_name = (await state.get_state()).split(':')[-1]
            self.data[state_name] = callback.data
            field_type = self.fields[self.states[self.states.index(state_name)]]["тип"]
            if 'int' in field_type:
                try:
                    field_value = int(callback.data)
                    if 'positive' in field_type and field_value < 0:
                        raise ValueError()
                    self.data[state_name] = field_value
                except ValueError:
                    voice_message = await generate_voice_message('Некорректное число')
                    await callback.message.answer_voice(voice_message)
                    return
            if field_type == 'date':
                try:
                    field_value = self.parser.parse_date(callback.data).strftime('%Y-%m-%d')
                    self.data[state_name] = field_value
                except ValueError:
                    voice_message = await generate_voice_message('Некорректная дата')
                    await callback.message.answer_voice(voice_message)
                    return
            try:
                new_state = self.states.index(state_name) + 1
                voice_message = await generate_voice_message(f'Введите {self.states[new_state]}.'
                                                             f'{self.fields[self.states[new_state]]["описание"]}')
                await callback.message.answer_voice(voice_message)
                await state.set_state(self.states[new_state])
            except IndexError:
                await state.finish()
                with open('index.html', encoding='utf8') as file:
                    soup = BeautifulSoup(file, 'lxml')
                for key, value in self.data.items():
                    element = soup.find("input", {"id": key})
                    element['value'] = value
                with open(f'media/{callback.id}.html', 'w', encoding='utf8') as file:
                    file.write(str(soup))
                await callback.message.answer_document(InputFile(f'media/{callback.id}.html'))

    def __call__(self, dp: Dispatcher):
        dp.register_message_handler(self.create_command_handler, commands=['create'])
        dp.register_message_handler(self.voice_message_with_state_handler, content_types=types.ContentType.VOICE,
                                    state=self.states)
        dp.register_callback_query_handler(self.check_callback, state=self.states)
