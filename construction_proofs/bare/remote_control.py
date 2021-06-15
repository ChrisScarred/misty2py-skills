from typing import Union

import requests
from pynput import keyboard


misty_ip = "192.168.0.103"

FORW_KEY = keyboard.KeyCode.from_char("w")
BACK_KEY = keyboard.KeyCode.from_char("s")
L_KEY = keyboard.KeyCode.from_char("a")
R_KEY = keyboard.KeyCode.from_char("d")
STOP_KEY = keyboard.KeyCode.from_char("x")
TERM_KEY = keyboard.Key.esc
BASE_VELOCITY = 20
TURN_VELOCITY = 10
BASE_ANGLE = 50


def cancel_skills(misty_ip: str) -> None:
    data = requests.get("http://%s/api/skills/running" % misty_ip).json()
    result = data.get("result", [])
    to_cancel = []
    for dct in result:
        uid = dct.get("uniqueId", "")
        if len(uid) > 0:
            to_cancel.append(uid)
    for skill in to_cancel:
        requests.post("http://%s/api/skills/cancel" % misty_ip, json={"Skill": skill})


def handle_input(key: Union[keyboard.Key, keyboard.KeyCode]) -> None:
    if key == L_KEY:
        left = {
            "LinearVelocity": TURN_VELOCITY,
            "AngularVelocity": BASE_ANGLE,
        }
        requests.post("http://%s/api/drive" % misty_ip, json=left)

    elif key == R_KEY:
        right = {
            "LinearVelocity": TURN_VELOCITY,
            "AngularVelocity": BASE_ANGLE * (-1),
        }
        requests.post("http://%s/api/drive" % misty_ip, json=right)

    elif key == FORW_KEY:
        forw = {
            "LinearVelocity": BASE_VELOCITY,
            "AngularVelocity": 0,
        }
        requests.post("http://%s/api/drive" % misty_ip, json=forw)

    elif key == BACK_KEY:
        back = {
            "LinearVelocity": BASE_VELOCITY * (-1),
            "AngularVelocity": 0,
        }
        requests.post("http://%s/api/drive" % misty_ip, json=back)

    elif key == STOP_KEY:
        requests.post("http://%s/api/drive/stop" % misty_ip, json={})

    elif key == TERM_KEY:
        return False


def cancel_skills(misty_ip: str) -> None:
    data = requests.get("http://%s/api/skills/running" % misty_ip).json()
    result = data.get("result", [])
    to_cancel = []
    for dct in result:
        uid = dct.get("uniqueId", "")
        if len(uid) > 0:
            to_cancel.append(uid)
    for skill in to_cancel:
        requests.post("http://%s/api/skills/cancel" % misty_ip, json={"Skill": skill})


def handle_release(key: keyboard.Key) -> None:
    pass


def remote_control() -> None:
    cancel_skills(misty_ip)
    print(
        f">>> Press {TERM_KEY} to terminate; control the movement via {L_KEY}, {BACK_KEY}, {R_KEY}, {FORW_KEY}; stop moving with {STOP_KEY}. <<<"
    )
    with keyboard.Listener(
        on_press=handle_input, on_release=handle_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    remote_control()
