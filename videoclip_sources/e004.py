import time

from misty2py.robot import Misty
from misty2py.utils.env_loader import EnvLoader

from misty2py_skills.utils.utils import get_abs_path


env_loader = EnvLoader(get_abs_path(".env"))
m = Misty(env_loader.get_ip())

d = m.event("subscribe", type="BatteryCharge")
e_name = d.get("event_name")

time.sleep(1)

d = m.event("get_data", name=e_name)
# do something with the data here
d = m.event("unsubscribe", name=e_name)
