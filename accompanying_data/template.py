from typing import Callable, Dict


def do_something(misty: Callable) -> Dict:
    """Do something with Misty here.

    Args:
        misty (Callable): an instance of Misty class.
    """
    return {}


if __name__ == "__main__":
    from misty2py.utils.utils import get_misty

    print(do_something(get_misty()))
