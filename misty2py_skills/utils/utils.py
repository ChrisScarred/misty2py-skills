from dotenv import dotenv_values
import os


def get_project_folder(env_path: str = ".env") -> str:
    values = dotenv_values(env_path)
    potential_path = values.get("PROJECT_DIR", "./")
    if os.path.isdir(potential_path):
        return os.path.abspath(potential_path)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_abs_path(rel_path: str) -> str:
    return os.path.join(get_project_folder(), rel_path)