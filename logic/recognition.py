import soundfile as sf
import speech_recognition as speech_recog


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
            return 'текст нераспознан'
        except speech_recog.UnknownValueError:
            return 'текст нераспознан'
        return recognized_data
