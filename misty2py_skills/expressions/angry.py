import time
from typing import Callable, Dict, Union

from misty2py_skills.utils.converse import success_parser_from_dicts

def angry_expression(
    misty: Callable,
    expression: str = "image_anger",
    sound: str = "sound_anger_1",
    led_offset: Union[float, int] = 0.5,
    duration: Union[float, int] = 1.5,
    colours: Dict = {"col1": "red_light", "col2": "orange_light", "time": 200},
) -> Dict:
    """Misty appears angry. Her displayed image changes to 'expression' and 'led_offset' seconds after, led changes to 'colours' and 'sound' is played. Lights last for 'duration' seconds and 'expression' image lasts for 'led_offset'+'duration' seconds.

    Args:
        misty (Callable): an instance of Misty class.
        expression (str, optional): The name of the expression image. Defaults to "image_anger".
        sound (str, optional): The name of the sound. Defaults to "sound_anger_1".
        led_offset (Union[float, int], optional): Time till lights and sound are initiated after the image changed in seconds. Defaults to 0.5.
        duration (Union[float, int], optional): Time of duration for the lights in seconds. Defaults to 1.5.
        colours (Dict, optional): The colours of the light in transition format. Defaults to { "col1": "red_light", "col2": "orange_light", "time": 200 }.
    """
    image_show_1 = misty.perform_action("image_show", data=expression)
    time.sleep(led_offset)
    led_trans = misty.perform_action("led_trans", data=colours)
    audio_enable = misty.perform_action("audio_enable")
    audio_stop = misty.perform_action("audio_stop")   
    audio_play = misty.perform_action("audio_play", data=sound)
    time.sleep(duration)
    led_off = misty.perform_action("led", data="led_off")
    image_show_2 = misty.perform_action("image_show", data="image_content_default")

    return success_parser_from_dicts(
        image_show_1=image_show_1, 
        led_trans=led_trans,
        audio_enable = audio_enable,
        audio_stop = audio_stop,
        audio_play=audio_play,
        led_off=led_off, 
        image_show_2=image_show_2
    )

if __name__ == "__main__":
    from misty2py.robot import Misty
    from misty2py.utils.env_loader import EnvLoader

    env_loader = EnvLoader()
    m = Misty(env_loader.get_ip())
    print(angry_expression(m))