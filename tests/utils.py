import os
from typing import Callable
from misty2py.robot import Misty
from misty2py.utils.env_loader import EnvLoader

def get_misty() -> Callable:
    env_loader = EnvLoader(env_path=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), ".env"))
    return Misty(env_loader.get_ip())