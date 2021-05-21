from os import stat
from typing import Callable, Dict, List, Tuple
import time
from misty2py.robot import Misty
from misty2py.utils.env_loader import EnvLoader
from pymitter import EventEmitter
from misty2py.utils.generators import get_random_string
from misty2py.utils.messages import message_parser
from misty2py_skills.utils.status import Status
from misty2py_skills.utils.converse import speak, success_parser_from_dicts

ee = EventEmitter()
env_loader = EnvLoader()
misty_glob = Misty(env_loader.get_ip())
status = Status()

# main event name used for face detection and recognition
event_name = "face_rec_%s" % get_random_string(6)
# event name used during training
sub_event_name = "face_train_%s" % get_random_string(6)
# the minimal time between greeting the same user in seconds
UPDT_TIME = 1
# the label used for an unknown face by Misty API
UNKNW_LABEL = "unknown person"
# custom status labels to keep track of the state the skill is in
STATUS_LABELS = {
    "main": "running_main",
    "prompt": "running_train_prompt",
    "train": "running_training",
    "init_train": "running_training_initialisation",
    "greet": "running_greeting",
    "talk": "talking",
}
# mapping multiple possible responses to one response type
USER_RESPONSES = {
    "yes": ["yes", "y"],
    "no": ["no", "n"],
    "stop": ["stop", "s", "terminate"],
}
# faces that begin with TESTING_NAME get forgotten before the skill starts (useful for testing purposes)
TESTING_NAME = "chris"


@ee.on(event_name)
def listener(data: Dict) -> None:
    if status.get_status() == STATUS_LABELS["main"]:
        prev_label, prev_time = status.get_data_time()
        curr_label = data.get("label")
        curr_time = time.time()
        if curr_time - prev_time > UPDT_TIME:
            handle_recognition(misty_glob, curr_label, curr_time)
        elif curr_label != prev_label:
            handle_recognition(misty_glob, curr_label, curr_time)
        status.set_time(curr_time)


@ee.on(sub_event_name)
def listener(data: Dict) -> None:
    if data.get("message") == "Face training embedding phase complete.":
        speak_wrapper(misty_glob, "Thank you, the training is complete now.")
        status.set_status(STATUS_LABELS["main"])
        d = misty_glob.event("unsubscribe", name=sub_event_name)
        print(message_parser(d))


def user_from_face_id(face_id: str) -> str:
    return face_id.split("_")[0].capitalize()


def training_prompt(misty: Callable):
    status.set_status(STATUS_LABELS["prompt"])
    speak_wrapper(
        misty,
        "Hello! I do not know you yet, do you want to begin the face training session?",
    )
    print("An unknown face detected.\nDo you want to start training (yes/no)? [no]")


def speak_wrapper(misty: Callable, utterance: str) -> None:
    prev_stat = status.get_status()
    status.set_status(STATUS_LABELS["talk"])
    print(speak(misty, utterance))
    status.set_status(prev_stat)


def handle_greeting(misty: Callable, user_name: str) -> None:
    status.set_status(STATUS_LABELS["greet"])
    utterance = f"Hello, {user_from_face_id(user_name)}!"
    speak_wrapper(misty, utterance)
    status.set_status(STATUS_LABELS["main"])


def handle_recognition(misty: Callable, label: str, det_time: float) -> None:
    status.update_data_time(label, det_time)
    if label == UNKNW_LABEL:
        training_prompt(misty)
    else:
        handle_greeting(misty, label)


def initialise_training(misty: Callable):
    status.set_status(STATUS_LABELS["init_train"])
    speak_wrapper(
        misty,
        "<p>How should I call you?</p><p>Please enter your name in the terminal.</p>",
    )
    print("Enter your name (the first name suffices)")


def perform_training(misty: Callable, name: str) -> None:
    status.set_status(STATUS_LABELS["train"])
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
    print(message_parser(d))
    speak_wrapper(misty, "The training has commenced, please do not look away now.")
    misty.event("subscribe", type="FaceTraining", name=sub_event_name, event_emitter=ee)


def handle_user_input(misty: Callable, user_input: str) -> None:
    if (
        user_input in USER_RESPONSES["yes"]
        and status.get_status() == STATUS_LABELS["prompt"]
    ):
        initialise_training(misty)

    elif (
        status.get_status() == STATUS_LABELS["init_train"]
        and not user_input in USER_RESPONSES["stop"]
    ):
        perform_training(misty, user_input)

    elif (
        status.get_status() == STATUS_LABELS["init_train"]
        and user_input in USER_RESPONSES["stop"]
    ):
        d = misty.perform_action("face_train_cancel")
        print(message_parser(d))
        status.set_status(STATUS_LABELS["main"])

    elif (
        status.get_status() == STATUS_LABELS["talk"]
        and user_input in USER_RESPONSES["stop"]
    ):
        d = misty.perform_action("speak_stop")
        print(message_parser(d))
        status.set_status(STATUS_LABELS["main"])

    elif status.get_status() == STATUS_LABELS["prompt"]:
        print("Training not initialised.")
        status.set_status(STATUS_LABELS["main"])


def purge_testing_faces(misty: Callable, known_faces: List) -> None:
    # TODO: informative return
    for face in known_faces:
        if face.startswith(TESTING_NAME):
            d = misty.perform_action("face_delete", data={"FaceId": face})
            print(
                message_parser(
                    d,
                    success_message=f"Successfully forgot the face of {face}.",
                    fail_message=f"Failed to forget the face of {face}.",
                )
            )


def face_recognition(misty: Callable) -> Dict:
    set_volume = misty.perform_action("volume_settings", data="low_volume")
    
    get_faces_known = misty.get_info("faces_known")
    known_faces = get_faces_known.get("result")
    if not known_faces is None:
        print("Your misty currently knows these faces: %s." % ", ".join(known_faces))
        purge_testing_faces(misty, known_faces)
    else:
        print("Your Misty currently does not know any faces.")

    start_face_recognition = misty.perform_action("face_recognition_start")
    
    subscribe_face_recognition = misty.event(
        "subscribe", type="FaceRecognition", name=event_name, event_emitter=ee
    )
    status.set_status(STATUS_LABELS["main"])
    print(message_parser(subscribe_face_recognition))

    print(">>> Type 'stop' to terminate <<<")
    user_input = ""
    while not (
        user_input in USER_RESPONSES["stop"]
        and status.get_status() == STATUS_LABELS["main"]
    ):
        user_input = input().lower()
        handle_user_input(misty, user_input)

    unsubscribe_face_recognition = misty.event("unsubscribe", name=event_name)
    print(message_parser(unsubscribe_face_recognition))

    face_recognition_stop = misty.perform_action("face_recognition_stop")
    
    speak_wrapper(misty, "Bye!")

    return success_parser_from_dicts(
        set_volume=set_volume, 
        get_faces_known=get_faces_known,
        start_face_recognition=start_face_recognition,
        subscribe_face_recognition=subscribe_face_recognition,
        unsubscribe_face_recognition=unsubscribe_face_recognition,
        face_recognition_stop=face_recognition_stop
    )

def main() -> Dict:
    """Creates an instance of Misty class and calls the skill function."""
    success = face_recognition(misty_glob)
    return success


if __name__ == "__main__":
    main()
