import os
from typing import Callable, List

from dotenv import dotenv_values


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


def get_wit_ai_key(env_path: str = ".env") -> str:
    values = dotenv_values(env_path)
    return values.get("WIT_AI_KEY", "")


def get_files_in_dir(abs_dir: str) -> List[str]:
    return [os.path.join(abs_dir, f) for f in os.listdir(abs_dir) if os.path.isfile(os.path.join(abs_dir, f))]


def get_base_fname_without_ext(fname: str) -> str:
    base = os.path.basename(fname)
    return os.path.splitext(base)[0]


def cancel_skills(misty: Callable):
    data = misty.get_info("skills_running")
    result = data.get("result", [])
    to_cancel = []
    for dct in result:
        uid = dct.get("uniqueId", "")
        if len(uid) > 0:
            to_cancel.append(uid)
    for skill in to_cancel:
        misty.perform_action("skill_cancel", data={"Skill": skill})
