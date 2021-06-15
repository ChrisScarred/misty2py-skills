import time
from typing import Callable, Dict, Union

from pymitter import EventEmitter

from misty2py.robot import Misty
from misty2py.utils.generators import get_random_string


ee = EventEmitter()
event_name = "battery_loader_" + get_random_string(6)
DEFAULT_DURATION = 2


@ee.on(event_name)
def listener(data: Dict) -> None:
    print(data)


def battery_printer(
    misty: Callable, duration: Union[int, float] = DEFAULT_DURATION
) -> None:
    misty.event("subscribe", type="BatteryCharge", name=event_name, event_emitter=ee)
    time.sleep(duration)
    misty.event("unsubscribe", name=event_name)


if __name__ == "__main__":
    battery_printer(Misty("192.168.0.103"))
