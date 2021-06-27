"""This module contains a skill that allows the user to remotely control Misty using a keyboard.
"""
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
"""The key for driving forward."""
BACK_KEY = keyboard.KeyCode.from_char("s")
"""The key for driving backward."""
L_KEY = keyboard.KeyCode.from_char("a")
"""The key for driving left."""
R_KEY = keyboard.KeyCode.from_char("d")
"""The key for driving right."""
STOP_KEY = keyboard.KeyCode.from_char("x")
"""The key for stopping Misty's movement."""
TERM_KEY = keyboard.Key.esc
"""The key for terminating the skill."""
BASE_VELOCITY = 20
"""The default velocity of the remote-controlled Misty."""
TURN_VELOCITY = 10
"""The default turning velocity of the remote-controlled Misty."""
BASE_ANGLE = 50
"""The default angle of turning."""


def handle_input(key: Union[keyboard.Key, keyboard.KeyCode]):
    """Receives the kyboard inputs and transforms them into Misty's actions.

    Args:
        key (Union[keyboard.Key, keyboard.KeyCode]): the key pressed.
    """
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
    """The method required by the keyboard package but not used in this skill."""
    pass


def remote_control() -> Dict:
    """A skill that allows the user to remotely control Misty using a keyboard.

    Returns:
        Dict: The dictionary with `"overall_success"` key (bool) and keys for every action performed (dictionarised Misty2pyResponse).
    """
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
