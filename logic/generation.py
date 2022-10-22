from io import BytesIO
from gtts import gTTS


async def generate_voice_message(text: str, langauge: str = 'ru') -> BytesIO:
    """
    Перевод текста в голосовое сообщение
    :param text: текста для сообщения
    :param langauge: язык
    :return: file in memory с голосовым сообщением
    """
    mp3_file = BytesIO()
    tts = gTTS(text, lang=langauge)
    tts.write_to_fp(mp3_file)
    mp3_file.seek(0)
    return mp3_file
