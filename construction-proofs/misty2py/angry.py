import time
from typing import Callable, Dict, Union

from misty2py.robot import Misty


def angry_expression(
    misty: Callable,
    expression: str = "image_anger",
    sound: str = "sound_anger_1",
    led_offset: Union[float, int] = 0.5,
    duration: Union[float, int] = 1.5,
    colours: Dict = {"col1": "red_light", "col2": "orange_light", "time": 200},
) -> None:
    misty.perform_action("image_show", data=expression)

    time.sleep(led_offset)

    misty.perform_action("led_trans", data=colours)
    misty.perform_action("audio_play", data=sound)

    time.sleep(duration)

    misty.perform_action("led", data="led_off")
    misty.perform_action("image_show", data="image_content_default")


if __name__ == "__main__":
    angry_expression(Misty("192.168.0.103"))
