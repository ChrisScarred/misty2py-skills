import json
import random
import string
import threading
import time
from typing import Any, Callable, Dict, Union

import requests
import websocket
from pymitter import EventEmitter


class Status:
    def __init__(
        self,
        init_status: Any = "initialised",
        init_data: Any = "",
        init_time: float = 0,
    ) -> None:
        self.status = init_status
        self.data = init_data
        self.time = init_time

    def set_(self, **content) -> None:
        potential_data = content.get("data")
        if not isinstance(potential_data, type(None)):
            self.data = potential_data

        potential_time = content.get("time")
        if not isinstance(potential_time, type(None)):
            self.time = potential_time

        potential_status = content.get("status")
        if not isinstance(potential_status, type(None)):
            self.status = potential_status

    def get_(self, content_type: str) -> Any:
        if content_type == "data":
            return self.data
        if content_type == "time":
            return self.time
        if content_type == "status":
            return self.status

    def parse_to_message(self) -> Dict:
        message = {}
        if isinstance(self.status, bool):
            if self.status:
                message["status"] = "Success"
            else:
                message["status"] = "Failed"
        if self.time != 0:
            message["time"] = self.time
        if self.data != "":
            message["data"] = self.data
        return message


class MistyEvent:
    def __init__(
        self,
        ip: str,
        type_str: str,
        event_name: str,
        return_property: str,
        debounce: int,
        len_data_entries: int,
        event_emitter: Union[Callable, None],
    ) -> None:
        self.server = "ws://%s/pubsub" % ip
        self.data = []
        self.type_str = type_str
        self.event_name = event_name
        self.return_property = return_property
        self.debounce = debounce
        self.log = []
        self.len_data_entries = len_data_entries
        event_thread = threading.Thread(target=self.run, daemon=True)
        event_thread.start()
        if event_emitter:
            self.ee = event_emitter
        else:
            self.ee = False

    def run(self) -> None:
        self.ws = websocket.WebSocketApp(
            self.server,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()

    def on_message(self, ws, message) -> None:
        message = json.loads(message)
        mes = message["message"]
        if len(self.data) > self.len_data_entries:
            self.data = self.data[1:-1]
        self.data.append(mes)

        if self.ee:
            self.ee.emit(self.event_name, mes)

    def on_error(self, ws, error):
        if len(self.log) > self.len_data_entries:
            self.log = self.log[1:-1]
        self.log.append(error)

        if self.ee:
            self.ee.emit("error_%s" % self.event_name, error)

    def on_close(self, ws) -> None:
        mes = "Closed"
        if len(self.log) > self.len_data_entries:
            self.log = self.log[1:-1]
        self.log.append(mes)

        if self.ee:
            self.ee.emit("close_%s" % self.event_name, mes)

    def on_open(self, ws) -> None:
        self.log.append("Opened")
        self.subscribe()
        ws.send("")

        if self.ee:
            self.ee.emit("open_%s" % self.event_name)

    def subscribe(self) -> None:
        msg = {
            "Operation": "subscribe",
            "Type": self.type_str,
            "DebounceMs": self.debounce,
            "EventName": self.event_name,
            "ReturnProperty": self.return_property,
        }
        msg_str = json.dumps(msg, separators=(",", ":"))
        self.ws.send(msg_str)

    def unsubscribe(self) -> None:
        msg = {"Operation": "unsubscribe", "EventName": self.event_name, "Message": ""}
        msg_str = json.dumps(msg, separators=(",", ":"))
        self.ws.send(msg_str)
        self.ws.close()


ee = EventEmitter()
event_name = "keyphrase_greeting_%s" % "".join(
    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(6)
)
misty_ip = "192.168.0.103"
status = Status(init_status=False, init_data="keyphrase not detected")


def listening_expression(
    misty: Callable,
    colour: str = "azure_light",
    sound: str = "sound_wake",
    duration: Union[float, int] = 1.5,
) -> None:
    misty.perform_action("led", data=colour)
    misty.perform_action("audio_play", data=sound)

    time.sleep(duration)

    misty.perform_action("led", data="led_off")


@ee.on(event_name)
def listener(data: Dict) -> None:
    conf = data.get("confidence")
    if isinstance(conf, int):
        if conf >= 60:
            success = listening_expression(misty_ip)
            status.set_(
                status=success.pop("overall_success", False),
                data={
                    "keyphrase detected": True,
                    "keyphrase_reaction_details": success,
                },
            )
            print("Hello!")


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


def greet() -> None:
    cancel_skills(misty_ip)
    requests.post("http://%s/api/services/audio/enable" % misty_ip, json={})

    keyphrase_start = requests.post(
        "http://%s/api/audio/keyphrase/start" % misty_ip,
        json={"CaptureSpeech": "false"},
    ).json()

    if not keyphrase_start.get("result"):
        keyphrase_start["status"] = "Failed"
        return keyphrase_start

    keyphrase = MistyEvent(
        misty_ip, "KeyPhraseRecognized", event_name, None, 250, 10, ee
    )

    print("Keyphrase recognition started.")
    time.sleep(1)
    input("\n>>> Press enter to terminate, do not force quit <<<\n")

    print("Keyphrase recognition ended.")
    keyphrase.unsubscribe()
    requests.post(
        "http://%s/api/audio/keyphrase/stop" % misty_ip, json={}
    ).json()
    requests.post("http://%s/api/services/audio/disable" % misty_ip, json={})


if __name__ == "__main__":
    greet()
