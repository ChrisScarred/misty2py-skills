from typing import Callable, Dict

from misty2py.basic_skills.expression import expression
from misty2py.utils.utils import get_misty


def angry_expression(misty: Callable) -> Dict:
    return expression(
        misty,
        image = "image_anger",
        sound = "sound_anger_1",
        colours = {"col1": "red_light", "col2": "orange_light", "time": 200},
        colour_type = "trans",
        colour_offset = 0.5,
        duration = 2
    )


def listening_expression(misty: Callable) -> Dict:
    return expression(
        misty,
        colour="azure_light",
        sound="sound_wake"
    )


if __name__=="__main__":
    print(angry_expression(get_misty()))
