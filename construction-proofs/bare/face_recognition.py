import json
import random
import string
import threading
import time
from enum import Enum, Union
from typing import Any, Callable, Dict, List

import requests
import websocket
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


class UserResponses:
    YES = frozenset(["yes", "y"])
    NO = frozenset(["no", "n"])
    STOP = frozenset(["stop", "s", "terminate"])


class StatusLabels(Enum):
    MAIN = "running_main"
    PROMPT = "running_train_prompt"
    TRAIN = "running_training"
    INIT = "running_training_initialisation"
    GREET = "running_greeting"
    TALK = "talking"


def get_random_string(n: int) -> str:
    return "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(n)
    )


ee = EventEmitter()
misty_ip = "192.168.0.103"
status = Status()
event_face_rec_name = "face_rec_%s" % get_random_string(6)
event_face_train_name = "face_train_%s" % get_random_string(6)
event_face_train = None

UPDATE_TIME = 1
UNKNOWN_LABEL = "unknown person"
TESTING_NAME = "chris"


@ee.on(event_face_rec_name)
def listener(data: Dict) -> None:
    if status.get_("status") == StatusLabels.MAIN:
        prev_time = status.get_("time")
        prev_label = status.get_("data")
        curr_label = data.get("label")
        curr_time = time.time()
        if curr_time - prev_time > UPDATE_TIME:
            handle_recognition(misty_ip, curr_label, curr_time)
        elif curr_label != prev_label:
            handle_recognition(misty_ip, curr_label, curr_time)
        status.set_(time=curr_time)


@ee.on(event_face_train_name)
def listener(data: Dict) -> None:
    if data.get("message") == "Face training embedding phase complete.":
        speak_wrapper(misty_ip, "Thank you, the training is complete now.")
        status.set_(status=StatusLabels.MAIN)
        event_face_train.unsubscribe()


def speak(misty_ip: str, utterance: str) -> None:
    print(utterance)
    requests.post(
        "http://%s/api/tts/speak" % misty_ip,
        json={"Text": utterance, "UtteranceId": "utterance_" + get_random_string(6)},
    )


def user_from_face_id(face_id: str) -> str:
    return face_id.split("_")[0].capitalize()


def training_prompt(misty_ip: str) -> None:
    status.set_(status=StatusLabels.PROMPT)
    speak_wrapper(
        misty_ip,
        "Hello! I do not know you yet, do you want to begin the face training session?",
    )
    print("An unknown face detected.\nDo you want to start training (yes/no)? [no]")


def speak_wrapper(misty_ip: str, utterance: str) -> None:
    prev_stat = status.get_("status")
    status.set_(status=StatusLabels.TALK)
    print(speak(misty_ip, utterance))
    status.set_(status=prev_stat)


def handle_greeting(misty_ip: str, user_name: str) -> None:
    status.set_(status=StatusLabels.GREET)
    utterance = f"Hello, {user_from_face_id(user_name)}!"
    speak_wrapper(misty_ip, utterance)
    status.set_(status=StatusLabels.MAIN)


def handle_recognition(misty_ip: str, label: str, det_time: float) -> None:
    status.set_(data=label, time=det_time)
    if label == UNKNOWN_LABEL:
        training_prompt(misty_ip)
    else:
        handle_greeting(misty_ip, label)


def initialise_training(misty_ip: str) -> None:
    status.set_(status=StatusLabels.INIT)
    speak_wrapper(
        misty_ip,
        "<p>How should I call you?</p><p>Please enter your name in the terminal.</p>",
    )
    print("Enter your name (the first name suffices)")


def perform_training(misty_ip: str, name: str) -> None:
    global event_face_train
    status.set_(status=StatusLabels.TRAIN)
    d = requests.get("http://%s/api/faces" % misty_ip).json()
    new_name = name
    if not d.get("result") is None:
        while new_name in d.get("result"):
            new_name = name + "_" + get_random_string(3)
        if new_name != name:
            print(f"The name {name} is already in use, using {new_name} instead.")
    if new_name == "":
        new_name = get_random_string(6)
        print(f"The name {name} is invalid, using {new_name} instead.")

    d = requests.post(
        "http://%s/api/faces/training/start" % misty_ip, json={"FaceId": new_name}
    ).json()
    speak_wrapper(misty_ip, "The training has commenced, please do not look away now.")
    event_face_train = MistyEvent(
        misty_ip, "FaceTraining", event_face_train_name, None, 250, 10, ee
    )


def handle_user_input(misty_ip: str, user_input: str) -> None:
    if user_input in UserResponses.YES and status.get_("status") == StatusLabels.PROMPT:
        initialise_training(misty_ip)

    elif (
        status.get_("status") == StatusLabels.INIT
        and not user_input in UserResponses.STOP
    ):
        perform_training(misty_ip, user_input)

    elif (
        status.get_("status") == StatusLabels.INIT and user_input in UserResponses.STOP
    ):
        requests.post("http://%s/api/faces/training/cancel" % misty_ip, json={})
        status.set_(status=StatusLabels.MAIN)

    elif (
        status.get_("status") == StatusLabels.TALK and user_input in UserResponses.STOP
    ):
        requests.post("http://%s/api/tts/stop" % misty_ip, json={})
        status.set_(status=StatusLabels.MAIN)

    elif status.get_("status") == StatusLabels.PROMPT:
        print("Training not initialised.")
        status.set_(status=StatusLabels.MAIN)


def purge_testing_faces(misty_ip: str, known_faces: List) -> None:
    for face in known_faces:
        if face.startswith(TESTING_NAME):
            requests.delete("http://%s/api/faces?FaceId=%s" % (misty_ip, face))


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


def face_recognition(misty_ip: str) -> None:
    cancel_skills(misty_ip)
    requests.post("http://%s/api/audio/volume" % misty_ip, json={"Volume": "5"})

    get_faces_known = requests.get("http://%s/api/faces" % misty_ip).json()
    known_faces = get_faces_known.get("result")
    if not known_faces is None:
        print("Your misty currently knows these faces: %s." % ", ".join(known_faces))
        purge_testing_faces(misty_ip, known_faces)
    else:
        print("Your Misty currently does not know any faces.")

    requests.post("http://%s/api/faces/recognition/start" % misty_ip, json={})

    face_rec = MistyEvent(
        misty_ip, "FaceRecognition", event_face_rec_name, None, 250, 10, ee
    )
    status.set_(status=StatusLabels.MAIN)

    print(">>> Type 'stop' to terminate <<<")
    user_input = ""
    while not (
        user_input in UserResponses.STOP and status.get_("status") == StatusLabels.MAIN
    ):
        user_input = input().lower()
        handle_user_input(misty_ip, user_input)

    face_rec.unsubscribe()

    requests.post("http://%s/api/faces/recognition/stop" % misty_ip, json={})

    speak_wrapper(misty_ip, "Bye!")


if __name__ == "__main__":
    face_recognition(misty_ip)
