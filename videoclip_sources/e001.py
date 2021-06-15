from misty2py.robot import Misty

misty = Misty("192.168.0.103")
misty.perform_action("led", data="azure_light")
