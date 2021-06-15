from typing import Union

from pynput import keyboard

from misty2py.robot import Misty


misty = Misty("192.168.0.103")
INFO_KEY = keyboard.KeyCode.from_char("i")
START_KEY = keyboard.Key.home
TERM_KEY = keyboard.Key.esc
HELP_KEY = keyboard.KeyCode.from_char("h")


def get_slam_info() -> None:
    enabled = misty.get_info("slam_enabled")
    if enabled.get("result"):
        print("SLAM enabled.")
    else:
        print("SLAM disabled.")
        return

    status = misty.get_info("slam_status")
    result = status.get("status")
    if result == "Success":
        info = status.get("result")
        if info:
            print(f"SLAM status: {info}")
    else:
        print("SLAM status unknown.")


def get_instructions() -> None:
    print(
        f"\n>>> INSTRUCTIONS <<<\n \
    - press {START_KEY} to start exploring (SLAM mapping) \n \
    - press {INFO_KEY} to see current exploration status (SLAM status) \n \
    - press {TERM_KEY} to stop this program; do not force-quit \
    "
    )


def handle_press(key: Union[keyboard.Key, keyboard.KeyCode]) -> None:
    print(f"{key} registered.")
    stat = misty.get_info("slam_enabled")

    if stat.get("status") == "Failed":
        print("SLAM disabled, terminating the program.")
        return False

    if key == START_KEY:
        resp = misty.perform_action("slam_mapping_start")
        print(resp)
        print(f"{key} processed.")

    elif key == INFO_KEY:
        get_slam_info()
        print(f"{key} processed.")

    elif key == HELP_KEY:
        get_instructions()
        print(f"{key} processed.")

    elif key == TERM_KEY:
        resp = misty.perform_action("slam_mapping_stop")
        print(resp)
        print(f"{key} processed.")
        return False


def handle_release(key: keyboard.Key) -> None:
    pass


def explore() -> None:
    get_instructions()
    with keyboard.Listener(
        on_press=handle_press, on_release=handle_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    explore()
