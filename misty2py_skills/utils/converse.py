from typing import Any, Callable, Dict, List, Tuple

from misty2py.utils.generators import get_random_string
from misty2py.utils.messages import message_parser


def success_parser_message(message: Any) -> Tuple[Dict, bool]:
    st = message.pop("status", None)
    if st == "Success":
        return {"successful": True, "message": message}, True
    return {"successful": False, "message": message}, False


def success_parser_from_dicts(**messages) -> Dict:
    status_dict = {}
    overall_success = True
    for name, message in messages.items():
        new_message, success = success_parser_message(message)
        status_dict[name] = new_message
        if not success:
            overall_success = False
    status_dict["overall_success"] = overall_success
    return status_dict


def success_parser_from_list(message_list: List[Dict]) -> Dict:
    status_dict = {"actions": []}
    overall_success = True
    for event in message_list:
        for name, message in event.items():
            new_message, success = success_parser_message(message)
        status_dict["actions"].append((name, new_message))
        if not success:
            overall_success = False
    status_dict["overall_success"] = overall_success
    return status_dict


def speak(misty: Callable, utterance: str) -> None:
    print(utterance)
    result = misty.perform_action(
        "speak",
        data={"Text": utterance, "UtteranceId": "utterance_" + get_random_string(6)},
    )
    return message_parser(
        result, success_message="Talking successful.", fail_message="Talking failed."
    )
