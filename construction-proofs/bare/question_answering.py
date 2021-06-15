import base64
import datetime
import json
import os
import random
import string
import threading
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple, Union

import requests
import speech_recognition as sr
import websocket
from dotenv import dotenv_values
from num2words import num2words
from pymitter import EventEmitter


class MistyEvent:
    def __init__(
        self,
        ip: str,
        type_str: str,
        event_name: str,
        return_property: str,
        debounce: int,
        len_data_entries: int,
        event_emitter: Union[Callable, None],
    ) -> None:
        self.server = "ws://%s/pubsub" % ip
        self.data = []
        self.type_str = type_str
        self.event_name = event_name
        self.return_property = return_property
        self.debounce = debounce
        self.log = []
        self.len_data_entries = len_data_entries
        event_thread = threading.Thread(target=self.run, daemon=True)
        event_thread.start()
        if event_emitter:
            self.ee = event_emitter
        else:
            self.ee = False

    def run(self) -> None:
        self.ws = websocket.WebSocketApp(
            self.server,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()

    def on_message(self, ws, message) -> None:
        message = json.loads(message)
        mes = message["message"]
        if len(self.data) > self.len_data_entries:
            self.data = self.data[1:-1]
        self.data.append(mes)

        if self.ee:
            self.ee.emit(self.event_name, mes)

    def on_error(self, ws, error) -> None:
        if len(self.log) > self.len_data_entries:
            self.log = self.log[1:-1]
        self.log.append(error)

        if self.ee:
            self.ee.emit("error_%s" % self.event_name, error)

    def on_close(self, ws) -> None:
        mes = "Closed"
        if len(self.log) > self.len_data_entries:
            self.log = self.log[1:-1]
        self.log.append(mes)

        if self.ee:
            self.ee.emit("close_%s" % self.event_name, mes)

    def on_open(self, ws) -> None:
        self.log.append("Opened")
        self.subscribe()
        ws.send("")

        if self.ee:
            self.ee.emit("open_%s" % self.event_name)

    def subscribe(self) -> None:
        msg = {
            "Operation": "subscribe",
            "Type": self.type_str,
            "DebounceMs": self.debounce,
            "EventName": self.event_name,
            "ReturnProperty": self.return_property,
        }
        msg_str = json.dumps(msg, separators=(",", ":"))
        self.ws.send(msg_str)

    def unsubscribe(self) -> None:
        msg = {"Operation": "unsubscribe", "EventName": self.event_name, "Message": ""}
        msg_str = json.dumps(msg, separators=(",", ":"))
        self.ws.send(msg_str)
        self.ws.close()


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
misty_ip = "192.168.0.103"
status = Status()
event_name = "user_speech_" + "".join(
    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(6)
)
voice_record_event = None
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
    dict_list = (
        requests.get("http://%s/api/audio/list" % misty_ip).json().get("result", [])
    )
    audio_list = []
    for d in dict_list:
        audio_list.append(d.get("name"))
    return audio_list


def speech_capture() -> None:
    print("Listening")

    audio_status = requests.get("http://%s/api/services/audio" % misty_ip).json()

    if not audio_status.get("result"):
        enable_audio = requests.post(
            "http://%s/api/services/audio/enable" % misty_ip, json={}
        ).json()
        if not enable_audio.get("result"):
            status.set_(status=StatusLabels.STOP)
            return

    requests.post("http://%s/api/audio/volume" % misty_ip, json={"Volume": "5"}).json()

    requests.post(
        "http://%s/api/audio/speech/capture" % misty_ip,
        json={"RequireKeyPhrase": False},
    ).json()
    status.set_(status=StatusLabels.LISTEN)


def base64_to_content(
    input_str: str, is_path: bool = False, save_path: Union[str, bool] = False
) -> str:
    if is_path:
        try:
            data = open(input_str, "rb").read()
        except:
            return "Error reading the file `%s`" % input_str
    else:
        data = input_str.encode()
    decoded = base64.b64decode(data)
    if save_path:
        try:
            with open(save_path, "wb") as f:
                f.write(decoded)
            return "Successfully saved to `%s`" % save_path
        except:
            return "Error saving to `%s`" % save_path
    return decoded.decode("utf-8")


def perform_inference() -> None:
    print("Analysing")
    label = StatusLabels.REINIT
    data = ""

    if SPEECH_FILE in get_all_audio_file_names():
        speech_json = requests.get(
            "http://%s/api/audio/speech/capture?FileName=%s&Base64=%s"
            % (misty_ip, SPEECH_FILE, "true")
        ).json()
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

    requests.post(
        "http://%s/api/tts/speak" % misty_ip, json={"Text": utterance, "Flush": "true"}
    ).json()

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
    global voice_record_event
    voice_record_event = MistyEvent(
        misty_ip, "VoiceRecord", event_name, None, 250, 10, ee
    )


def unsubscribe() -> None:
    voice_record_event.unsubscribe()


def cancel_skills(misty_ip: str) -> None:
    data = requests.get("http://%s/api/skills/running" % misty_ip).json()
    result = data.get("result", [])
    to_cancel = []
    for dct in result:
        uid = dct.get("uniqueId", "")
        if len(uid) > 0:
            to_cancel.append(uid)
    for skill in to_cancel:
        requests.post("http://%s/api/skills/cancel" % misty_ip, json={"Skill": skill})


def question_answering() -> None:
    cancel_skills(misty_ip)
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
