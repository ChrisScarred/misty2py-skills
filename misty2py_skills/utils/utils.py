from dotenv import dotenv_values
import os
from typing import Callable


def get_project_folder(env_path: str = ".env") -> str:
    values = dotenv_values(env_path)
    potential_path = values.get("PROJECT_DIR", "./")
    if os.path.isdir(potential_path):
        return os.path.abspath(potential_path)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_abs_path(rel_path: str) -> str:
    return os.path.join(get_project_folder(), rel_path)


def get_misty() -> Callable:
    from misty2py.robot import Misty
    from misty2py.utils.env_loader import EnvLoader

    env_loader = EnvLoader(get_abs_path(".env"))
    return Misty(env_loader.get_ip())
