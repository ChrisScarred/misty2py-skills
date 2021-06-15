import time
from typing import Dict, Union

import requests


def listening_expression(
    misty_ip: str,
    colour: Dict = {"red": "0", "green": "125", "blue": "255"},
    sound: Dict = {"FileName": "s_SystemWakeWord.wav"},
    duration: Union[float, int] = 1.5,
) -> None:
    requests.post("http://%s/api/led" % misty_ip, json=colour)
    requests.post("http://%s/api/audio/play" % misty_ip, json=sound)

    time.sleep(duration)

    requests.post(
        "http://%s/api/led" % misty_ip, json={"red": "0", "green": "0", "blue": "0"}
    )


if __name__ == "__main__":
    listening_expression("192.168.0.103")
