import time
from enum import Enum
from typing import Any, Callable, Dict, List

from pymitter import EventEmitter

from misty2py.robot import Misty
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


ee = EventEmitter()
misty_glob = Misty("192.168.0.103")
status = Status()
event_face_rec = "face_rec_%s" % get_random_string(6)
event_face_train = "face_train_%s" % get_random_string(6)

UPDATE_TIME = 1
UNKNOWN_LABEL = "unknown person"
TESTING_NAME = "chris"


@ee.on(event_face_rec)
def listener(data: Dict) -> None:
    if status.get_("status") == StatusLabels.MAIN:
        prev_time = status.get_("time")
        prev_label = status.get_("data")
        curr_label = data.get("label")
        curr_time = time.time()
        if curr_time - prev_time > UPDATE_TIME:
            handle_recognition(misty_glob, curr_label, curr_time)
        elif curr_label != prev_label:
            handle_recognition(misty_glob, curr_label, curr_time)
        status.set_(time=curr_time)


@ee.on(event_face_train)
def listener(data: Dict) -> None:
    if data.get("message") == "Face training embedding phase complete.":
        speak_wrapper(misty_glob, "Thank you, the training is complete now.")
        status.set_(status=StatusLabels.MAIN)
        misty_glob.event("unsubscribe", name=event_face_train)


def speak(misty: Callable, utterance: str) -> None:
    print(utterance)
    misty.perform_action(
        "speak",
        data={"Text": utterance, "UtteranceId": "utterance_" + get_random_string(6)},
    )


def user_from_face_id(face_id: str) -> str:
    return face_id.split("_")[0].capitalize()


def training_prompt(misty: Callable) -> None:
    status.set_(status=StatusLabels.PROMPT)
    speak_wrapper(
        misty,
        "Hello! I do not know you yet, do you want to begin the face training session?",
    )
    print("An unknown face detected.\nDo you want to start training (yes/no)? [no]")


def speak_wrapper(misty: Callable, utterance: str) -> None:
    prev_stat = status.get_("status")
    status.set_(status=StatusLabels.TALK)
    print(speak(misty, utterance))
    status.set_(status=prev_stat)


def handle_greeting(misty: Callable, user_name: str) -> None:
    status.set_(status=StatusLabels.GREET)
    utterance = f"Hello, {user_from_face_id(user_name)}!"
    speak_wrapper(misty, utterance)
    status.set_(status=StatusLabels.MAIN)


def handle_recognition(misty: Callable, label: str, det_time: float) -> None:
    status.set_(data=label, time=det_time)
    if label == UNKNOWN_LABEL:
        training_prompt(misty)
    else:
        handle_greeting(misty, label)


def initialise_training(misty: Callable) -> None:
    status.set_(status=StatusLabels.INIT)
    speak_wrapper(
        misty,
        "<p>How should I call you?</p><p>Please enter your name in the terminal.</p>",
    )
    print("Enter your name (the first name suffices)")


def perform_training(misty: Callable, name: str) -> None:
    status.set_(status=StatusLabels.TRAIN)
    d = misty.get_info("faces_known")
    new_name = name
    if not d.get("result") is None:
        while new_name in d.get("result"):
            new_name = name + "_" + get_random_string(3)
        if new_name != name:
            print(f"The name {name} is already in use, using {new_name} instead.")
    if new_name == "":
        new_name = get_random_string(6)
        print(f"The name {name} is invalid, using {new_name} instead.")

    d = misty.perform_action("face_train_start", data={"FaceId": new_name})
    speak_wrapper(misty, "The training has commenced, please do not look away now.")
    misty.event(
        "subscribe", type="FaceTraining", name=event_face_train, event_emitter=ee
    )


def handle_user_input(misty: Callable, user_input: str) -> None:
    if user_input in UserResponses.YES and status.get_("status") == StatusLabels.PROMPT:
        initialise_training(misty)

    elif (
        status.get_("status") == StatusLabels.INIT
        and not user_input in UserResponses.STOP
    ):
        perform_training(misty, user_input)

    elif (
        status.get_("status") == StatusLabels.INIT and user_input in UserResponses.STOP
    ):
        misty.perform_action("face_train_cancel")
        status.set_(status=StatusLabels.MAIN)

    elif (
        status.get_("status") == StatusLabels.TALK and user_input in UserResponses.STOP
    ):
        misty.perform_action("speak_stop")
        status.set_(status=StatusLabels.MAIN)

    elif status.get_("status") == StatusLabels.PROMPT:
        print("Training not initialised.")
        status.set_(status=StatusLabels.MAIN)


def purge_testing_faces(misty: Callable, known_faces: List) -> None:
    for face in known_faces:
        if face.startswith(TESTING_NAME):
            misty.perform_action("face_delete", data={"FaceId": face})


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


def face_recognition(misty: Callable) -> None:
    cancel_skills(misty)
    misty.perform_action("volume_settings", data="low_volume")

    get_faces_known = misty.get_info("faces_known")
    known_faces = get_faces_known.get("result")
    if not known_faces is None:
        print("Your misty currently knows these faces: %s." % ", ".join(known_faces))
        purge_testing_faces(misty, known_faces)
    else:
        print("Your Misty currently does not know any faces.")

    misty.perform_action("face_recognition_start")

    misty.event(
        "subscribe", type="FaceRecognition", name=event_face_rec, event_emitter=ee
    )
    status.set_(status=StatusLabels.MAIN)

    print(">>> Type 'stop' to terminate <<<")
    user_input = ""
    while not (
        user_input in UserResponses.STOP and status.get_("status") == StatusLabels.MAIN
    ):
        user_input = input().lower()
        handle_user_input(misty, user_input)

    misty.event("unsubscribe", name=event_face_rec)

    misty.perform_action("face_recognition_stop")

    speak_wrapper(misty, "Bye!")


if __name__ == "__main__":
    face_recognition(misty_glob)
