import os

from misty2py.robot import Misty
from misty2py.utils.env_loader import EnvLoader

BASEDIR = "D:/School/thesis/misty2py-skills/"

env_loader = EnvLoader(os.path.join(BASEDIR, ".env"))
misty = Misty(env_loader.get_ip())
