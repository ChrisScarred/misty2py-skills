from typing import Any, Dict, List


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

    def get(self, content_type: str) -> Any:
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


class ActionLog:
    def __init__(self) -> None:
        self.actions = []

    def append_(self, value: Any):
        self.actions.append(value)

    def get_(self) -> List:
        return self.actions
