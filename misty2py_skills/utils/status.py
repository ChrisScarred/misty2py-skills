from typing import Tuple


class Status:
    def __init__(
        self,
        init_status: str = "initialised",
        init_data: str = "",
        init_time: float = 0,
    ) -> None:
        self.status = init_status
        self.data = init_data
        self.time = init_time

    def update_data_time(self, det_data: str, det_time: float) -> None:
        self.data = det_data
        self.time = det_time

    def set_status(self, det_status: str) -> None:
        self.status = det_status

    def set_time(self, det_time: float) -> None:
        self.time = det_time

    def get_data_time(self) -> Tuple[str, float]:
        return self.data, self.time

    def get_status(self) -> str:
        return self.status
