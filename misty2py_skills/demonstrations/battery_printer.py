"""This module implements a skill that prints the battery status every 250ms for the duration specified by the system argument.
"""
import sys
import time
from typing import Dict, Union

from misty2py.basic_skills.cancel_skills import cancel_skills
from misty2py.response import success_of_action_list
from misty2py.robot import Misty
from misty2py.utils.generators import get_random_string
from misty2py.utils.status import ActionLog
from pymitter import EventEmitter

actions = ActionLog()
ee = EventEmitter()
event_name = "battery_loader_" + get_random_string(6)
DEFAULT_DURATION = 2
"""The defaults duration of the skill in seconds."""


def status_of_battery_event(data: Dict) -> bool:
    """Verifies whether the receives data indicates a valid battery status."""
    for required in [
        "chargePercent",
        "created",
        "current",
        "healthPercent",
        "isCharging",
        "sensorId",
        "state",
        "temperature",
        "trained",
        "voltage",
    ]:
        if isinstance(data.get(required), type(None)):
            return False
    return True


@ee.on(event_name)
def listener(data: Dict):
    """Prints received battery data and appends it to the list of actions."""
    print(data)
    actions.append_(
        {"battery_status": {"message": data, "status": status_of_battery_event(data)}}
    )


def battery_printer(
    misty: Misty, duration: Union[int, float] = DEFAULT_DURATION
) -> Dict:
    """Prints the battery status every 250ms for `duration` seconds.

    Args:
        misty (Misty): The Misty whose battery status to print.
        duration (Union[int, float], optional): The duration of the skill. Defaults to DEFAULT_DURATION.

    Returns:
        Dict: The dictionary with `"overall_success"` key (bool) and keys for every action performed (dictionarised Misty2pyResponse).
    """
    cancel_skills(misty)

    events = []
    event_type = "BatteryCharge"

    subscription = misty.event(
        "subscribe", type=event_type, name=event_name, event_emitter=ee
    ).parse_to_dict()
    events.append({"subscription": subscription})

    time.sleep(duration)
    events.extend(actions.get_())

    unsubscription = misty.event("unsubscribe", name=event_name).parse_to_dict()
    events.append({"unsubscription": unsubscription})

    return success_of_action_list(events)


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        arg_1 = args[1]
        try:
            arg_1 = float(arg_1)
        except:
            raise TypeError("This script expects a single integer or float argument")
        duration = arg_1
    else:
        duration = DEFAULT_DURATION

    from misty2py.utils.utils import get_misty

    print(battery_printer(get_misty(), duration))
