import sys
import time
from typing import Callable, Dict, Union

from misty2py.utils.generators import get_random_string
from misty2py_skills.utils.converse import success_parser_from_list
from misty2py_skills.utils.status import ActionLog
from misty2py_skills.utils.utils import cancel_skills
from pymitter import EventEmitter

actions = ActionLog()
ee = EventEmitter()
event_name = "battery_loader_" + get_random_string(6)
DEFAULT_DURATION = 2


def status_of_battery_event(data: Dict) -> str:
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
            return "Failed"
    return "Success"


@ee.on(event_name)
def listener(data: Dict):
    print(data)
    actions.append_(
        {"battery_status": {"message": data, "status": status_of_battery_event(data)}}
    )


def battery_printer(
    misty: Callable, duration: Union[int, float] = DEFAULT_DURATION
) -> Dict:
    cancel_skills(misty)
    events = []
    event_type = "BatteryCharge"

    subscription = misty.event(
        "subscribe", type=event_type, name=event_name, event_emitter=ee
    )
    events.append({"subscription": subscription})

    time.sleep(duration)
    events.extend(actions.get_())

    unsubscription = misty.event("unsubscribe", name=event_name)
    events.append({"unsubscription": unsubscription})

    return success_parser_from_list(events)


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

    from misty2py_skills.utils.utils import get_misty

    print(battery_printer(get_misty(), duration))
