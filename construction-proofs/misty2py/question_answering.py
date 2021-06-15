import datetime
import os
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple

import speech_recognition as sr
from dotenv import dotenv_values
from num2words import num2words
from pymitter import EventEmitter

from misty2py.robot import Misty
from misty2py.utils.base64 import *
from misty2py.utils.generators import get_random_string


class Status:
    def __init__(
        self,
        init_status: Any = "initialised",
        init_data: Any = "",
        init_time: float = 0,
    ) -> None:
        self.status = init_status
        self.data = init_data
        self.time = init_time

    def set_(self, **content) -> None:
        potential_data = content.get("data")
        if not isinstance(potential_data, type(None)):
            self.data = potential_data

        potential_time = content.get("time")
        if not isinstance(potential_time, type(None)):
            self.time = potential_time

        potential_status = content.get("status")
        if not isinstance(potential_status, type(None)):
            self.status = potential_status

    def get_(self, content_type: str) -> Any:
        if content_type == "data":
            return self.data
        if content_type == "time":
            return self.time
        if content_type == "status":
            return self.status

    def parse_to_message(self) -> Dict:
        message = {}
        if isinstance(self.status, bool):
            if self.status:
                message["status"] = "Success"
            else:
                message["status"] = "Failed"
        if self.time != 0:
            message["time"] = self.time
        if self.data != "":
            message["data"] = self.data
        return message


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


ee = EventEmitter()
misty = Misty("192.168.0.103")
status = Status()
event_name = "user_speech_" + get_random_string(6)
values = dotenv_values("./")
speech_transcripter = SpeechTranscripter(values.get("WIT_AI_KEY", ""))

SAVE_DIR = "data"
SPEECH_FILE = "capture_Dialogue.wav"


class StatusLabels(Enum):
    REINIT = "reinit"
    LISTEN = "listening"
    PREP = "prepare_reply"
    INFER = "infering"
    STOP = "stop"
    SPEAK = "ready_to_speak"


@ee.on(event_name)
def listener(data: Dict) -> None:
    if data.get("errorCode", -1) == 0:
        status.set_(status=StatusLabels.INFER)

    if data.get("errorCode", -1) == 3:
        status.set_(status=StatusLabels.REINIT)


def get_files_in_dir(abs_dir: str) -> List[str]:
    return [
        os.path.join(abs_dir, f)
        for f in os.listdir(abs_dir)
        if os.path.isfile(os.path.join(abs_dir, f))
    ]


def get_base_fname_without_ext(fname: str) -> str:
    base = os.path.basename(fname)
    return os.path.splitext(base)[0]


def get_next_file_name(dir_: str) -> str:
    files = get_files_in_dir(dir_)
    highest = 0
    if len(files) > 0:
        highest = max([int(get_base_fname_without_ext(f).lstrip("0")) for f in files])
    return os.path.join(dir_, "%s.wav" % str(highest + 1).zfill(4))


def get_all_audio_file_names() -> List[str]:
    dict_list = misty.get_info("audio_list").get("result", [])
    audio_list = []
    for d in dict_list:
        audio_list.append(d.get("name"))
    return audio_list


def speech_capture() -> None:
    print("Listening")

    audio_status = misty.get_info("audio_status")

    if not audio_status.get("result"):
        enable_audio = misty.perform_action("audio_enable")
        if not enable_audio.get("result"):
            status.set_(status=StatusLabels.STOP)
            return

    misty.perform_action("volume_settings", data="low_volume")

    misty.perform_action(
        "speech_capture", data={"RequireKeyPhrase": False}
    )
    status.set_(status=StatusLabels.LISTEN)


def perform_inference() -> None:
    print("Analysing")
    label = StatusLabels.REINIT
    data = ""

    if SPEECH_FILE in get_all_audio_file_names():
        speech_json = misty.get_info(
            "audio_file", params={"FileName": SPEECH_FILE, "Base64": "true"}
        )
        speech_base64 = speech_json.get("result", {}).get("base64", "")
        if len(speech_base64) > 0:
            f_name = get_next_file_name(SAVE_DIR)
            base64_to_content(speech_base64, save_path=f_name)
            speech_wav = speech_transcripter.load_wav(f_name)
            speech_text = speech_transcripter.audio_to_text(speech_wav, show_all=True)
            label = StatusLabels.PREP
            data = speech_text

    status.set_(status=label, data=data)


def get_intents_keywords(entities: Dict) -> Tuple[List[str], List[str]]:
    intents = []
    keywords = []
    for key, val in entities.items():
        if key == "intent":
            intents.extend([dct.get("value") for dct in val])
        else:
            keywords.append(key)
    return intents, keywords


def choose_reply() -> None:
    print("Preparing the reply")

    data = status.get_("data")
    if isinstance(data, Dict):
        data = data.get("content", {})

    intents, keywords = get_intents_keywords(data.get("entities", {}))
    utterance_type = "unknown"

    if "greet" in intents:
        if "hello" in keywords:
            utterance_type = "hello"
        elif "goodbye" in keywords:
            utterance_type = "goodbye"
        else:
            utterance_type = "hello"

    elif "datetime" in intents:
        if "date" in keywords:
            utterance_type = "date"
        elif "month" in keywords:
            utterance_type = "month"
        elif "year" in keywords:
            utterance_type = "year"

    elif "test" in intents:
        utterance_type = "test"

    status.set_(status=StatusLabels.SPEAK, data=utterance_type)


def speak(utterance: str) -> None:
    print(utterance)

    misty.perform_action(
        "speak",
        data={"Text": utterance, "Flush": "true"},
    )

    label = StatusLabels.REINIT
    if status.get_("data") == "goodbye":
        label = StatusLabels.STOP

    status.set_(status=label)


def perform_reply() -> None:
    print("Replying")
    utterance_type = status.get_("data")

    if utterance_type == "test":
        speak("I received your test.")

    elif utterance_type == "unknown":
        speak("I am sorry, I do not understand.")

    elif utterance_type == "hello":
        speak("Hello!")

    elif utterance_type == "goodbye":
        speak("Goodbye!")

    elif utterance_type == "year":
        now = datetime.datetime.now()
        speak("It is the year %s." % num2words(now.year))

    elif utterance_type == "month":
        now = datetime.datetime.now()
        speak("It is the month of %s." % now.strftime("%B"))

    elif utterance_type == "date":
        now = datetime.datetime.now()
        speak(
            "It is the %s of %s, year %s."
            % (
                num2words(now.day, to="ordinal"),
                now.strftime("%B"),
                num2words(now.year),
            )
        )


def subscribe() -> None:
    misty.event(
        "subscribe", type="VoiceRecord", name=event_name, event_emitter=ee
    )


def unsubscribe() -> None:
    misty.event("unsubscribe", name=event_name)


def cancel_skills(misty: Callable) -> None:
    data = misty.get_info("skills_running")
    result = data.get("result", [])
    to_cancel = []
    for dct in result:
        uid = dct.get("uniqueId", "")
        if len(uid) > 0:
            to_cancel.append(uid)
    for skill in to_cancel:
        misty.perform_action("skill_cancel", data={"Skill": skill})


def question_answering() -> None:
    cancel_skills(misty)
    subscribe()
    status.set_(status=StatusLabels.REINIT)

    while status.get_("status") != StatusLabels.STOP:
        current_status = status.get_("status")

        if current_status == StatusLabels.REINIT:
            speech_capture()

        elif current_status == StatusLabels.INFER:
            perform_inference()

        elif current_status == StatusLabels.PREP:
            choose_reply()

        elif current_status == StatusLabels.SPEAK:
            perform_reply()

    unsubscribe()


if __name__ == "__main__":
    question_answering()
