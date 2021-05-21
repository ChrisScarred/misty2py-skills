from typing import Callable, Dict, Union
import time

from misty2py_skills.utils.converse import success_parser_from_dicts


def listening_expression(
    misty: Callable,
    colour: str = "azure_light",
    sound: str = "sound_wake",
    duration: Union[float, int] = 1.5,
) -> Dict:
    """Misty plays a sound and lights up to appear interested / listening. Lights last for 'duration' seconds. The sound is played in the begining right after the lights are lit.

    Args:
        misty (Callable): an instance of Misty class.
        colour (str, optional): The led colour. Defaults to "azure_light".
        sound (str, optional): The sound. Defaults to "sound_wake".
        duration (Union[float, int], optional): The duration of lights in seconds. Defaults to 1.5.
    """
    led_show = misty.perform_action("led", data=colour)

    audio_enable = misty.perform_action("audio_enable")
    audio_stop = misty.perform_action("audio_stop")    
    audio_play = misty.perform_action("audio_play", data=sound)
    
    time.sleep(duration)
    
    led_off = misty.perform_action("led", data="led_off")

    return success_parser_from_dicts(
        led_show = led_show, 
        audio_enable = audio_enable,
        audio_stop = audio_stop,
        audio_play = audio_play, 
        led_off = led_off
    )


if __name__ == "__main__":
    from misty2py_skills.utils.utils import get_misty
    print(listening_expression(get_misty()))
