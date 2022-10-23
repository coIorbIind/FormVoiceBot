import soundfile as sf
import speech_recognition as speech_recog
from nltk.stem import SnowballStemmer
import re
from datetime import date


class Recognizer:
    @staticmethod
    def recognize_text(file_path: str):
        """Распознаёт текст из аудиосообщения"""
        name = file_path.split('/')[-1].split('.')[0]
        # Конвертация .ogg файла в .wav
        temp_data, samplerate = sf.read(file_path)
        sf.write(f'media/{name}.wav', temp_data, samplerate)

        sample_audio = speech_recog.AudioFile(f'media/{name}.wav')

        recog = speech_recog.Recognizer()

        with sample_audio as audio_file:
            audio_content = recog.record(audio_file)
        try:
            recognized_data = recog.recognize_google(audio_content, language='ru-RU')
        except speech_recog.RequestError:
            raise ConnectionError('Can\'t connect to the server')
        except speech_recog.UnknownValueError:
            raise ValueError()
        return recognized_data


class TextParser:
    def __init__(self, com_stop_word_dict: dict):
        # commands_dict -> {command: [stop_words]}
        self.stemmer = SnowballStemmer(language='russian')
        # Применяем стемминг к стоп словам команд

        self.all_commands = dict()

        # Создаём словарь, где ключ - слово, а значение - список стемматизированных стоп слов
        for item in com_stop_word_dict:
            if type(item) is tuple:
                stemmed_words = [self.stemmer.stem(token) for token in com_stop_word_dict[item]]
                for cmd in item:
                    self.all_commands[cmd] = stemmed_words
            else:
                self.all_commands[item] = [self.stemmer.stem(token) for token in com_stop_word_dict[item]]

    def parse_command(self, raw_text: str) -> tuple:
        """ Находит команду в тексте """
        tokens = raw_text.split(' ')

        cmd_value = list(filter(lambda x: self.stemmer.stem(x.lower()) == self.stemmer.stem(tokens[0].lower()),
                                self.all_commands.keys()))

        if not cmd_value:
            raise ValueError('Command isn\'t found in the raw text!')

        # К списку уже применён стемминг
        cmd_stop_list = self.all_commands[cmd_value[0]]

        temp_word_ind = 1
        # Пропускаем стоп-слова
        while temp_word_ind < len(tokens) and self.stemmer.stem(tokens[temp_word_ind]) in cmd_stop_list:
            temp_word_ind += 1

        return cmd_value[0], ' '.join(tokens[temp_word_ind:])

    def parse_table_name(self, table_names: list, prep_text: str) -> str:
        """ Находит название таблицы и отделяет его от остального текста """
        tokens = prep_text.split(' ')

        result_table_name = None

        # Ищем слова, близкие к началу предложения, которые похожи на имена форм
        for token in tokens[-3:]:
            result_table_name = list(filter(lambda x: self.stemmer.stem(x.lower()) == self.stemmer.stem(token.lower()),
                                            table_names))

        if not result_table_name:
            raise ValueError('No such table!')

        return result_table_name[0]

    def parse_fields(self, possible_fields: list, prep_text: str):
        """ Находит название поля, которое есть в этой строке """
        tokens = prep_text.split(' ')

        # Отбираем слова, которые похожи на названия полей
        found_fields = list()

        for token in tokens:
            # Проверяем похоже ли слово на название поля
            field_token = list(filter(lambda x: self.stemmer.stem(x.lower()) == self.stemmer.stem(token.lower()),
                                      possible_fields))
            if field_token:
                found_fields.append(field_token[0])

        return found_fields

    @staticmethod
    def parse_date(prep_text):

        month_word_dict = {
            'январь': 1,
            'февраль': 2,
            'март': 3,
            'апрель': 4,
            'май': 5,
            'июнь': 6,
            'июль': 7,
            'август': 8,
            'сентябрь': 9,
            'октябрь': 10,
            'ноябрь': 11,
            'декабрь': 12
        }

        day_match = re.search(r'\d\d?', prep_text)
        year_match = re.search(r'\d{4}', prep_text)
        month = None

        stemmer = SnowballStemmer(language='russian')

        for month_name, num_value in month_word_dict.items():
            stemmed_month = stemmer.stem(month_name)

            month_match = re.search(stemmed_month, prep_text, re.IGNORECASE)
            if month_match:
                month = num_value

        try:
            if not day_match or not year_match or not month:
                raise ValueError

            year = int(prep_text[year_match.start(): year_match.end()])
            day = int(prep_text[day_match.start(): day_match.end()])

            result = date(year, month, day)
        except ValueError:
            raise ValueError('Wrong date message!')

        return result
