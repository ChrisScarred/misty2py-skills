"""This module implements a SLAM mapping skill.
"""
from typing import Union

from misty2py.utils.utils import get_misty
from pynput import keyboard

misty = get_misty()

INFO_KEY = keyboard.KeyCode.from_char("i")
"""The key to print for SLAM information."""
START_KEY = keyboard.Key.home
"""The key to print to start exploring."""
TERM_KEY = keyboard.Key.esc
"""The key to print to terminate the skill."""
HELP_KEY = keyboard.KeyCode.from_char("h")
"""The key to print for help information."""


def get_slam_info():
    """Obtains and prints the SLAM status."""
    enabled = misty.get_info("slam_enabled").parse_to_dict().get("rest_response", {})
    if enabled.get("success"):
        print("SLAM enabled.")
    else:
        print("SLAM disabled.")
        return

    status = misty.get_info("slam_status").parse_to_dict().get("rest_response", {})
    result = status.get("success")
    if result:
        info = status.get("result")
        if info:
            print(f"SLAM status: {info}")
    else:
        print("SLAM status unknown.")


def get_instructions():
    """Prints the instructions."""
    print(
        f"\n>>> INSTRUCTIONS <<<\n \
    - press {START_KEY} to start exploring (SLAM mapping) \n \
    - press {INFO_KEY} to see current exploration status (SLAM status) \n \
    - press {TERM_KEY} to stop this program; do not force-quit \
    "
    )


def handle_press(key: Union[keyboard.Key, keyboard.KeyCode]) -> bool:
    """Handles responses to pressing a key.

    Args:
        key (Union[keyboard.Key, keyboard.KeyCode]): The pressed key.

    Returns:
        bool: `False` upon termination.
    """
    print(f"{key} registered.")
    stat = misty.get_info("slam_enabled").parse_to_dict().get("rest_response", {})

    if not stat.get("success"):
        print("SLAM disabled, terminating the program.")
        return False

    if key == START_KEY:
        resp = misty.perform_action("slam_mapping_start").parse_to_dict()
        print(resp)
        print(f"{key} processed.")

    elif key == INFO_KEY:
        get_slam_info()
        print(f"{key} processed.")

    elif key == HELP_KEY:
        get_instructions()
        print(f"{key} processed.")

    elif key == TERM_KEY:
        resp = misty.perform_action("slam_mapping_stop").parse_to_dict()
        print(resp)
        print(f"{key} processed.")
        return False


def handle_release(key: keyboard.Key):
    """The method required by the keyboard package but not used in this skill."""
    pass


def explore():
    """Attempts to perform SLAM mapping."""
    get_instructions()
    with keyboard.Listener(
        on_press=handle_press, on_release=handle_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    explore()
