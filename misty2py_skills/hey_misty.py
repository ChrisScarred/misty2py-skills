import time
from typing import Dict

from misty2py.robot import Misty
from misty2py.skills.listening_expression import listening_expression
from misty2py.utils.env_loader import EnvLoader
from misty2py.utils.generators import get_random_string
from misty2py.utils.messages import message_parser
from pymitter import EventEmitter

ee = EventEmitter()
event_name = "listening_greeting_%s" % get_random_string(6)
env_loader = EnvLoader()
misty = Misty(env_loader.get_ip())


@ee.on(event_name)
def listener(data: Dict):
    """Prints received data every time 'event_name' emits data.

    Args:
        data (Dict): the json data received by the event subscription handler.
    """
    conf = data.get("confidence")
    if isinstance(conf, int):
        if conf >= 60:
            listening_expression(misty)
    print(data)


def greet():
    """TODO: Document"""
    result = misty.perform_action(
        "keyphrase_recognition_start", data={"CaptureSpeech": "false"}
    )
    print(message_parser(result))
    event_type = "KeyPhraseRecognized"
    d = misty.event("subscribe", type=event_type, name=event_name, event_emitter=ee)
    print(message_parser(d))
    time.sleep(15)
    input(">>> Press any key to terminate <<<")
    d = misty.event("unsubscribe", name=event_name)
    print(message_parser(d))
    result = misty.perform_action("keyphrase_recognition_stop")
    print(message_parser(result))


def main():
    """Calls the greeting function."""
    greet()


if __name__ == "__main__":
    main()
