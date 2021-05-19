import time
from typing import Union
from pynput import keyboard

from misty2py.robot import Misty
from misty2py.utils.env_loader import EnvLoader
from misty2py.utils.messages import message_parser

env_loader = EnvLoader()
misty = Misty(env_loader.get_ip())

FORW_KEY = keyboard.KeyCode.from_char("w")
BACK_KEY = keyboard.KeyCode.from_char("s")
L_KEY = keyboard.KeyCode.from_char("a")
R_KEY = keyboard.KeyCode.from_char("d")
STOP_KEY = keyboard.KeyCode.from_char("x")
TERM_KEY = keyboard.Key.esc


def move_forward():
    forw = {
        "LinearVelocity": 20,
        "AngularVelocity": 0,
    }
    resp = misty.perform_action("drive", data=forw)
    print(message_parser(resp))


def move_backward():
    back = {
        "LinearVelocity": -20,
        "AngularVelocity": 0,
    }
    resp = misty.perform_action("drive", data=back)
    print(message_parser(resp))


def move_left():
    left = {
        "LinearVelocity": 10,
        "AngularVelocity": 50,
    }
    resp = misty.perform_action("drive", data=left)
    print(message_parser(resp))


def move_right():
    right = {
        "LinearVelocity": 10,
        "AngularVelocity": -50,
    }
    resp = misty.perform_action("drive", data=right)
    print(message_parser(resp))


def stop():
    resp = misty.perform_action("drive_stop")
    print(message_parser(resp))


def handle_movement(key: Union[keyboard.Key, keyboard.KeyCode]):
    if key == L_KEY:
        move_left()
    elif key == R_KEY:
        move_right()
    elif key == FORW_KEY:
        move_forward()
    elif key == BACK_KEY:
        move_backward()
    elif key == STOP_KEY:
        stop()
    elif key == TERM_KEY:
        return False


def handle_release(key: keyboard.Key):
    pass


def movement():
    print(
        f">>> Press {TERM_KEY} to terminate; control the movement via {L_KEY}, {BACK_KEY}, {R_KEY}, {FORW_KEY} <<<"
    )
    with keyboard.Listener(
        on_press=handle_movement, on_release=handle_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    movement()
