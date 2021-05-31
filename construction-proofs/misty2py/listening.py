import time
from typing import Callable, Union

from misty2py.robot import Misty


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


if __name__ == "__main__":
    listening_expression(Misty("192.168.0.103"))
