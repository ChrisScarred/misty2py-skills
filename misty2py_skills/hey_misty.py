import time
from typing import Dict

from misty2py.basic_skills.cancel_skills import cancel_skills
from misty2py.basic_skills.expression import expression
from misty2py.response import success_of_action_dict
from misty2py.utils.generators import get_random_string
from misty2py.utils.status import Status
from misty2py.utils.utils import get_misty
from pymitter import EventEmitter

ee = EventEmitter()
event_name = "keyphrase_greeting_%s" % get_random_string(6)
misty = get_misty()
status = Status(init_status=False, init_data="keyphrase not detected")


@ee.on(event_name)
def listener(data: Dict):
    conf = data.get("confidence")
    if isinstance(conf, int):
        if conf >= 60:
            success = expression(misty, colour="azure_light", sound="sound_wake")
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
    enable_audio = misty.perform_action("audio_enable").parse_to_dict()
    keyphrase_start = misty.perform_action(
        "keyphrase_recognition_start", data = {"CaptureSpeech": "false"}
    ).parse_to_dict()

    if not keyphrase_start.get("rest_response", {}).get("result"):
        keyphrase_start["rest_response"] = {"success": False}
        return success_of_action_dict(
            enable_audio = enable_audio,
            keyphrase_start = keyphrase_start
        )

    keyphrase_subscribe = misty.event(
        "subscribe", type="KeyPhraseRecognized", name = event_name, event_emitter=ee
    ).parse_to_dict()

    print("Keyphrase recognition started.")
    time.sleep(1)
    input("\n>>> Press enter to terminate, do not force quit <<<\n")

    print("Keyphrase recognition ended.")
    keyphrase_unsubscribe = misty.event("unsubscribe", name=event_name).parse_to_dict()
    keyphrase_stop = misty.perform_action("keyphrase_recognition_stop").parse_to_dict()
    disable_audio = misty.perform_action("audio_disable").parse_to_dict()

    reaction = status.parse_to_message()
    if reaction.get("status") == "Success":        
        print(reaction)
    else:
        print("Keyphrase not recognised.")

    return success_of_action_dict(
        enable_audio=enable_audio,
        keyphrase_start=keyphrase_start_origin,
        keyphrase_subscribe=keyphrase_subscribe,
        keyphrase_unsubscribe=keyphrase_unsubscribe,
        keyphrase_stop=keyphrase_stop,
        disable_audio=disable_audio,
    )


if __name__ == "__main__":
    print(greet())
