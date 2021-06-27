from typing import Dict, Union

from misty2py.basic_skills.cancel_skills import cancel_skills
from misty2py.basic_skills.movement import Movement
from misty2py.response import success_of_action_list
from misty2py.utils.status import ActionLog
from misty2py.utils.utils import get_misty
from pynput import keyboard

misty = get_misty()
moves = Movement()
actions = ActionLog()

FORW_KEY = keyboard.KeyCode.from_char("w")
BACK_KEY = keyboard.KeyCode.from_char("s")
L_KEY = keyboard.KeyCode.from_char("a")
R_KEY = keyboard.KeyCode.from_char("d")
STOP_KEY = keyboard.KeyCode.from_char("x")
TERM_KEY = keyboard.Key.esc
BASE_VELOCITY = 20
TURN_VELOCITY = 10
BASE_ANGLE = 50


def handle_input(key: Union[keyboard.Key, keyboard.KeyCode]):
    if key == L_KEY:
        actions.append_(
            {"drive_left": moves.drive_left(misty, TURN_VELOCITY, BASE_ANGLE)}
        )
    elif key == R_KEY:
        actions.append_(
            {"drive_right": moves.drive_right(misty, TURN_VELOCITY, BASE_ANGLE)}
        )
    elif key == FORW_KEY:
        actions.append_({"drive_forward": moves.drive_forward(misty, BASE_VELOCITY)})
    elif key == BACK_KEY:
        actions.append_({"drive_backward": moves.drive_backward(misty, BASE_VELOCITY)})
    elif key == STOP_KEY:
        actions.append_({"stop_driving": moves.stop_driving(misty)})
    elif key == TERM_KEY:
        return False


def handle_release(key: keyboard.Key):
    pass


def remote_control() -> Dict:
    cancel_skills(misty)
    print(
        f">>> Press {TERM_KEY} to terminate; control the movement via {L_KEY}, {BACK_KEY}, {R_KEY}, {FORW_KEY}; stop moving with {STOP_KEY}. <<<"
    )
    with keyboard.Listener(
        on_press=handle_input, on_release=handle_release
    ) as listener:
        listener.join()

    return success_of_action_list(actions.get_())


if __name__ == "__main__":
    print(remote_control())
