import soundfile as sf
import speech_recognition as speech_recog
import io


class Recognizer:
    @staticmethod
    def recognize_text(file_bin: io.BytesIO):
        """Распознаёт текст из аудиосообщения"""
        # Конвертация .ogg файла в .wav
        temp_data, samplerate = sf.read(file_bin)
        sf.write('temp_file.wav', temp_data, samplerate)

        sample_audio = speech_recog.AudioFile('temp_file.wav')

        recog = speech_recog.Recognizer()

        with sample_audio as audio_file:
            audio_content = recog.record(audio_file)
        try:
            recognized_data = recog.recognize_google(audio_content, language='ru-RU')
        except speech_recog.RequestError:
            raise ConnectionError("Can't connect to the server!")

        return recognized_data
