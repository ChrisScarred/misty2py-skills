import time
from pymitter import EventEmitter

from misty2py.robot import Misty
from misty2py.utils.env_loader import EnvLoader

from misty2py_skills.utils.utils import get_abs_path


env_loader = EnvLoader(get_abs_path(".env"))

m = Misty(env_loader.get_ip())
ee = EventEmitter()
event_name = "myevent_001"


@ee.on(event_name)
def listener(data):
    # do something with the data here
    pass


d = m.event("subscribe", type="BatteryCharge", name=event_name, event_emitter=ee)

time.sleep(2)

d = m.event("unsubscribe", name=event_name)
