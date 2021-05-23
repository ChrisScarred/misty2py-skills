from typing import Dict

import speech_recognition as sr


class SpeechTranscripter:
    def __init__(self, wit_ai_key: str) -> None:
        self.key = wit_ai_key
        self.recogniser = sr.Recognizer()

    def load_wav(self, audio_path: str) -> sr.AudioFile:
        with sr.AudioFile(audio_path) as source:
            return self.recogniser.record(source)

    def audio_to_text(self, audio: sr.AudioSource, show_all: bool = False) -> Dict:
        try:
            transcription = self.recogniser.recognize_wit(
                audio, key=self.key, show_all=show_all
            )
            return {"status": "Success", "content": transcription}

        except sr.UnknownValueError:
            return {"status": "Success", "content": "unknown"}

        except sr.RequestError as e:
            return {
                "status": "Failed",
                "content": "Invalid request.",
                "error_details": str(e),
            }
