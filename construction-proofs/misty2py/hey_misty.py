import time
from typing import Any, Callable, Dict, Union

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


ee = EventEmitter()
event_name = "keyphrase_greeting_%s" % get_random_string(6)
misty = Misty("192.168.0.103")
status = Status(init_status=False, init_data="keyphrase not detected")


def listening_expression(
    misty: Callable,
    colour: str = "azure_light",
    sound: str = "sound_wake",
    duration: Union[float, int] = 1.5,
) -> None:
    misty.perform_action("led", data=colour)
    misty.perform_action("audio_play", data=sound)

    time.sleep(duration)

    misty.perform_action("led", data="led_off")


@ee.on(event_name)
def listener(data: Dict) -> None:
    conf = data.get("confidence")
    if isinstance(conf, int):
        if conf >= 60:
            success = listening_expression(misty)
            status.set_(
                status=success.pop("overall_success", False),
                data={
                    "keyphrase detected": True,
                    "keyphrase_reaction_details": success,
                },
            )
            print("Hello!")


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


def greet() -> None:
    cancel_skills(misty)
    misty.perform_action("audio_enable")
    keyphrase_start = misty.perform_action(
        "keyphrase_recognition_start", data={"CaptureSpeech": "false"}
    )

    if not keyphrase_start.get("result"):
        keyphrase_start["status"] = "Failed"
        return keyphrase_start

    misty.event(
        "subscribe", type="KeyPhraseRecognized", name=event_name, event_emitter=ee
    )

    print("Keyphrase recognition started.")
    time.sleep(1)
    input("\n>>> Press enter to terminate, do not force quit <<<\n")

    print("Keyphrase recognition ended.")
    misty.event("unsubscribe", name=event_name)
    misty.perform_action("keyphrase_recognition_stop")
    misty.perform_action("audio_disable")


if __name__ == "__main__":
    greet()
