from typing import Any, Callable, Dict, List, Union

from pynput import keyboard

from misty2py.robot import Misty


class Movement:
    def __init__(
        self,
        max_velocity=100,
        min_velocity=1,
        stagnant_velocity=0,
        max_angle=100,
        min_angle=1,
        stagnant_angle=0,
    ) -> None:
        self.max_velocity = max_velocity
        self.min_velocity = min_velocity
        self.stagnant_velocity = stagnant_velocity
        self.max_angle = max_angle
        self.min_angle = min_angle
        self.stagnant_angle = stagnant_angle

    def _parse_value(
        self, value: int, max: int, min: int, negative: bool = False, both: bool = False
    ) -> int:
        if both:
            if value > max:
                return max
            if value < max * (-1):
                return max * (-1)
            return value

        if negative:
            if value > max:
                # velocity over max
                return max * (-1)
            if value > min:
                # velocity over min below max
                return value * (-1)
            if value > max * (-1):
                # velocity below min, over negative max
                return value
            # velocity over negative max
            return max * (-1)

        if value < min:
            return min
        if value > max:
            return max
        return value

    def _parse_velocity(
        self, velocity: int, negative: bool = False, both: bool = False
    ) -> int:
        return self._parse_value(
            velocity, self.max_velocity, self.min_velocity, negative=negative, both=both
        )

    def _parse_angle(
        self, angle: int, negative: bool = False, both: bool = False
    ) -> int:
        return self._parse_value(
            angle, self.max_angle, self.min_angle, negative=negative, both=both
        )

    def drive_forward(self, misty: Callable, velocity: int) -> Dict:
        forw = {
            "LinearVelocity": self._parse_velocity(velocity),
            "AngularVelocity": self.stagnant_angle,
        }
        return misty.perform_action("drive", data=forw)

    def drive_backward(self, misty: Callable, velocity: int):
        back = {
            "LinearVelocity": self._parse_velocity(velocity, negative=True),
            "AngularVelocity": self.stagnant_angle,
        }
        return misty.perform_action("drive", data=back)

    def drive_left(self, misty: Callable, velocity: int, angle: int):
        left = {
            "LinearVelocity": self._parse_velocity(velocity),
            "AngularVelocity": self._parse_angle(angle),
        }
        return misty.perform_action("drive", data=left)

    def drive_right(self, misty: Callable, velocity: int, angle: int):
        velocity = self._parse_velocity(velocity)
        right = {
            "LinearVelocity": self._parse_velocity(velocity),
            "AngularVelocity": self._parse_angle(angle, negative=True),
        }
        return misty.perform_action("drive", data=right)

    def stop_driving(self, misty: Callable):
        return misty.perform_action("drive_stop")


misty = Misty("192.168.0.103")
moves = Movement()

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
        moves.drive_left(misty, TURN_VELOCITY, BASE_ANGLE)
        
    elif key == R_KEY:
        moves.drive_right(misty, TURN_VELOCITY, BASE_ANGLE)
        
    elif key == FORW_KEY:
       moves.drive_forward(misty, BASE_VELOCITY)

    elif key == BACK_KEY:
        moves.drive_backward(misty, BASE_VELOCITY)

    elif key == STOP_KEY:
        moves.stop_driving(misty)

    elif key == TERM_KEY:
        return False


def cancel_skills(misty: Callable) -> None:
    data = misty.get_info("skills_running")
    result = data.get("result", [])
    to_cancel = []
    for dct in result:
        uid = dct.get("uniqueId", "")
        if len(uid) > 0:
            to_cancel.append(uid)
    for skill in to_cancel:
        misty.perform_action("skill_cancel", data={"Skill": skill})


def handle_release(key: keyboard.Key) -> None:
    pass


def remote_control() -> None:
    cancel_skills(misty)
    print(
        f">>> Press {TERM_KEY} to terminate; control the movement via {L_KEY}, {BACK_KEY}, {R_KEY}, {FORW_KEY}; stop moving with {STOP_KEY}. <<<"
    )
    with keyboard.Listener(
        on_press=handle_input, on_release=handle_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    remote_control()
