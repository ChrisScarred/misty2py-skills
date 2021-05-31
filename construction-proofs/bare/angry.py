import time
import requests
from typing import Dict, Union


def angry_expression(
    misty_ip: str,
    expression: Dict = {"FileName": "e_Anger.jpg"},
    sound: Dict = {"FileName": "s_Anger.wav"},
    led_offset: Union[float, int] = 0.5,
    duration: Union[float, int] = 1.5,
    colours: Dict = {
        "Red": "255",
        "Green": "0",
        "Blue": "0",
        "Red2": "255",
        "Green2": "125",
        "Blue2": "0",
        "TransitionType": "Breathe",
        "TimeMS": 200,
    },
) -> None:
    requests.post("http://%s/api/images/display" % misty_ip, json=expression)

    time.sleep(led_offset)

    requests.post("http://%s/api/led/transition" % misty_ip, json=colours)
    requests.post("http://%s/api/audio/play" % misty_ip, json=sound)

    time.sleep(duration)

    requests.post(
        "http://%s/api/led" % misty_ip, json={"red": "0", "green": "0", "blue": "0"}
    )
    requests.post(
        "http://%s/images/display" % misty_ip,
        json={"FileName": "e_DefaultContent.jpg"}
    )


if __name__ == "__main__":
    angry_expression("192.168.0.103")
