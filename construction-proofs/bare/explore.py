from typing import Union

import requests
from pynput import keyboard


misty_ip = "192.168.0.103"
INFO_KEY = keyboard.KeyCode.from_char("i")
START_KEY = keyboard.Key.home
TERM_KEY = keyboard.Key.esc
HELP_KEY = keyboard.KeyCode.from_char("h")


def get_slam_info() -> None:
    enabled = requests.get("http://%s/api/services/slam" % misty_ip)
    if enabled.json().get("result"):
        print("SLAM enabled.")
    else:
        print("SLAM disabled.")
        return

    status = requests.get("http://%s/api/slam/status" % misty_ip)
    result = status.json().get("status")
    if result == "Success":
        info = status.json().get("result")
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
    stat = requests.get("http://%s/api/services/slam" % misty_ip)

    if stat.json().get("status") == "Failed":
        print("SLAM disabled, terminating the program.")
        return False

    if key == START_KEY:
        resp = requests.post("http://%s/api/slam/map/start" % misty_ip, json={})
        print(resp.json())
        print(f"{key} processed.")

    elif key == INFO_KEY:
        get_slam_info()
        print(f"{key} processed.")

    elif key == HELP_KEY:
        get_instructions()
        print(f"{key} processed.")

    elif key == TERM_KEY:
        resp = requests.post("http://%s/api/slam/map/stop" % misty_ip, json={})
        print(resp.json())
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
