import json
import random
import string
import threading
import time
from typing import Callable, Dict, Union

import websocket
from pymitter import EventEmitter


ee = EventEmitter()
event_name = "battery_loader_" + "".join(
    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(6)
)
DEFAULT_DURATION = 2


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

    def on_error(self, ws, error) -> None:
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


@ee.on(event_name)
def listener(data: Dict) -> None:
    print(data)


def battery_printer(
    misty_ip: str, duration: Union[int, float] = DEFAULT_DURATION
) -> None:
    me = MistyEvent(misty_ip, "BatteryCharge", event_name, None, 250, 10, ee)
    time.sleep(duration)
    me.unsubscribe()


if __name__ == "__main__":
    battery_printer("192.168.0.103")
