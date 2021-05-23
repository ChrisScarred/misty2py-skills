import time
from typing import Dict

from misty2py_skills.expressions.listening import listening_expression
from misty2py.utils.generators import get_random_string
from pymitter import EventEmitter

from misty2py_skills.utils.status import Status
from misty2py_skills.utils.converse import success_parser_from_dicts
from misty2py_skills.utils.utils import cancel_skills, get_misty

ee = EventEmitter()
event_name = "keyphrase_greeting_%s" % get_random_string(6)
misty = get_misty()
status = Status(init_status=False, init_data="keyphrase not detected")


@ee.on(event_name)
def listener(data: Dict):
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


def greet() -> Dict:
    cancel_skills(misty)
    enable_audio = misty.perform_action("audio_enable")
    keyphrase_start = misty.perform_action(
        "keyphrase_recognition_start", data={"CaptureSpeech": "false"}
    )

    if not keyphrase_start.get("result"):
        keyphrase_start["status"] = "Failed"
        return success_parser_from_dicts(
            enable_audio=enable_audio, keyphrase_start=keyphrase_start
        )

    keyphrase_subscribe = misty.event(
        "subscribe", type="KeyPhraseRecognized", name=event_name, event_emitter=ee
    )

    print("Keyphrase recognition started.")
    time.sleep(1)
    input("\n>>> Press enter to terminate, do not force quit <<<\n")

    print("Keyphrase recognition ended.")
    keyphrase_unsubscribe = misty.event("unsubscribe", name=event_name)
    keyphrase_stop = misty.perform_action("keyphrase_recognition_stop")
    disable_audio = misty.perform_action("audio_disable")

    return success_parser_from_dicts(
        enable_audio=enable_audio,
        keyphrase_start=keyphrase_start,
        keyphrase_subscribe=keyphrase_subscribe,
        keyphrase_reaction=status.parse_to_message(),
        keyphrase_unsubscribe=keyphrase_unsubscribe,
        keyphrase_stop=keyphrase_stop,
        disable_audio=disable_audio,
    )


if __name__ == "__main__":
    print(greet())
