"""This module implements a face recognition skill that allows Misty to greet people with their chosen name.
"""
import time
from enum import Enum
from typing import Dict, List

from misty2py.basic_skills.cancel_skills import cancel_skills
from misty2py.basic_skills.speak import speak
from misty2py.response import success_of_action_dict
from misty2py.robot import Misty
from misty2py.utils.generators import get_random_string
from misty2py.utils.status import Status
from misty2py.utils.utils import get_misty
from pymitter import EventEmitter

ee = EventEmitter()
misty_glob = get_misty()
status = Status()
event_face_rec = "face_rec_%s" % get_random_string(6)
event_face_train = "face_train_%s" % get_random_string(6)

UPDATE_TIME = 1
"""The minimum amount of time (in seconds) that must pass between Misty greets the same person again."""
UNKNOWN_LABEL = "unknown person"
"""The label used by Misty's REST API for an unknown face."""
TESTING_NAME = "chris"
"""The name of the person testing this module. For convenience, the faces commencing with this name are forgotten in at beginning of the skill so they can be learnt again."""


class UserResponses:
    """Represents responses that a user can give to different prompts used in this skill."""

    YES = frozenset(["yes", "y"])
    NO = frozenset(["no", "n"])
    STOP = frozenset(["stop", "s", "terminate"])


class StatusLabels(Enum):
    """Represents states in which the skill can be."""

    MAIN = "running_main"
    """The main state of waiting for a face recognition event."""
    PROMPT = "running_train_prompt"
    """The state of running the training prompt and waiting for the user's response."""
    TRAIN = "running_training"
    """The face training state."""
    INIT = "running_training_initialisation"
    """The state of the initialisation of face training."""
    GREET = "running_greeting"
    """The state of greeting a person."""
    TALK = "talking"
    """The state of talking."""


@ee.on(event_face_rec)
def listener(data: Dict) -> None:
    """Reacts to a face recognition event.

    Only greets a person if the current status of the skill is not training, talking or greeting. Does not greet the person if they were greeted the previous time less than `UPDATE_TIME` seconds ago. Greets the person if they are a different person than the person greeted the previous time less than `UPDATE_TIME` seconds ago.

    Args:
        data (Dict): The data received from Misty's WebSocket API along with the face recognition event.
    """
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
    """Handles face training events and terminates the training session if the data states the training is complete.

    Args:
        data (Dict): The data received from Misty's WebSocket API along with the face training event.
    """
    if data.get("message") == "Face training embedding phase complete.":
        speak_wrapper(misty_glob, "Thank you, the training is complete now.")
        status.set_(status=StatusLabels.MAIN)
        d = misty_glob.event("unsubscribe", name=event_face_train).parse_to_dict()
        print(d)


def user_from_face_id(face_id: str) -> str:
    """Returns the name from a face ID."""
    return face_id.split("_")[0].capitalize()


def training_prompt(misty: Misty):
    """Misty asks whether to begin a face training session."""
    status.set_(status=StatusLabels.PROMPT)
    speak_wrapper(
        misty,
        "Hello! I do not know you yet, do you want to begin the face training session?",
    )
    print("An unknown face detected.\nDo you want to start training (yes/no)? [no]")


def speak_wrapper(misty: Misty, utterance: str) -> None:
    """Changes status to `StatusLabels.TALK` while Misty is talking."""
    prev_stat = status.get_("status")
    status.set_(status=StatusLabels.TALK)
    print(speak(misty, utterance))
    status.set_(status=prev_stat)


def handle_greeting(misty: Misty, user_name: str) -> None:
    """Greets a person."""
    status.set_(status=StatusLabels.GREET)
    utterance = f"Hello, {user_from_face_id(user_name)}!"
    speak_wrapper(misty, utterance)
    status.set_(status=StatusLabels.MAIN)


def handle_recognition(misty: Misty, label: str, det_time: float) -> None:
    """Handles recognition of a face."""
    status.set_(data=label, time=det_time)
    if label == UNKNOWN_LABEL:
        training_prompt(misty)
    else:
        handle_greeting(misty, label)


def initialise_training(misty: Misty):
    """Initialises the face training session, including prompting the user to enter their name."""
    status.set_(status=StatusLabels.INIT)
    speak_wrapper(
        misty,
        "<p>How should I call you?</p><p>Please enter your name in the terminal.</p>",
    )
    print("Enter your name (the first name suffices)")


def perform_training(misty: Misty, name: str) -> None:
    """Performs the training.

    Args:
        misty (Misty): The Misty to learn the user's face.
        name (str): The name of the user.
    """
    status.set_(status=StatusLabels.TRAIN)
    d = misty.get_info("faces_known").parse_to_dict().get("rest_response", {})
    new_name = name
    if not d.get("result") is None:
        while new_name in d.get("result"):
            new_name = name + "_" + get_random_string(3)
        if new_name != name:
            print(f"The name {name} is already in use, using {new_name} instead.")
    if new_name == "":
        new_name = get_random_string(6)
        print(f"The name {name} is invalid, using {new_name} instead.")

    d = misty.perform_action(
        "face_train_start", data={"FaceId": new_name}
    ).parse_to_dict()
    print(d)
    speak_wrapper(misty, "The training has commenced, please do not look away now.")
    misty.event(
        "subscribe", type="FaceTraining", name=event_face_train, event_emitter=ee
    )


def handle_user_input(misty: Misty, user_input: str) -> None:
    """Handles keyboard inputs."""
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
        d = misty.perform_action("face_train_cancel").parse_to_dict()
        print(d)
        status.set_(status=StatusLabels.MAIN)

    elif (
        status.get_("status") == StatusLabels.TALK and user_input in UserResponses.STOP
    ):
        d = misty.perform_action("speak_stop").parse_to_dict()
        print(d)
        status.set_(status=StatusLabels.MAIN)

    elif status.get_("status") == StatusLabels.PROMPT:
        print("Training not initialised.")
        status.set_(status=StatusLabels.MAIN)


def purge_testing_faces(misty: Misty, known_faces: List) -> None:
    """Forgets the faces of users that start with `TESTING NAME`."""
    for face in known_faces:
        if face.startswith(TESTING_NAME):
            d = (
                misty.perform_action("face_delete", data={"FaceId": face})
                .parse_to_dict()
                .get("rest_response", {})
            )
            if d.get("success"):
                print("Successfully forgot the face of %s." % face)
            else:
                print("Failed to forget the face of %s." % face)


def face_recognition(misty: Misty) -> Dict:
    """Misty detects a face, if she knows the person, she greets them by their name, else she prompts them to join a face training session.

    Args:
        misty (Misty): The Misty to perform the skill.

    Returns:
        Dict: The dictionary with `"overall_success"` key (bool) and keys for every action performed (dictionarised Misty2pyResponse).
    """
    cancel_skills(misty)
    set_volume = misty.perform_action(
        "volume_settings", data="low_volume"
    ).parse_to_dict()

    get_faces_known = (
        misty.get_info("faces_known").parse_to_dict().get("rest_response", {})
    )
    known_faces = get_faces_known.get("result")
    if not known_faces is None:
        print("Your misty currently knows these faces: %s." % ", ".join(known_faces))
        purge_testing_faces(misty, known_faces)
    else:
        print("Your Misty currently does not know any faces.")

    start_face_recognition = misty.perform_action(
        "face_recognition_start"
    ).parse_to_dict()

    subscribe_face_recognition = misty.event(
        "subscribe", type="FaceRecognition", name=event_face_rec, event_emitter=ee
    ).parse_to_dict()
    status.set_(status=StatusLabels.MAIN)
    print(subscribe_face_recognition)

    print(">>> Type 'stop' to terminate <<<")
    user_input = ""
    while not (
        user_input in UserResponses.STOP and status.get_("status") == StatusLabels.MAIN
    ):
        user_input = input().lower()
        handle_user_input(misty, user_input)

    unsubscribe_face_recognition = misty.event(
        "unsubscribe", name=event_face_rec
    ).parse_to_dict()
    print(unsubscribe_face_recognition)

    face_recognition_stop = misty.perform_action(
        "face_recognition_stop"
    ).parse_to_dict()

    speak_wrapper(misty, "Bye!")

    return success_of_action_dict(
        set_volume=set_volume,
        get_faces_known=get_faces_known,
        start_face_recognition=start_face_recognition,
        subscribe_face_recognition=subscribe_face_recognition,
        unsubscribe_face_recognition=unsubscribe_face_recognition,
        face_recognition_stop=face_recognition_stop,
    )


if __name__ == "__main__":
    print(face_recognition(misty_glob))
