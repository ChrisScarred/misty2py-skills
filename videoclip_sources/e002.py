import requests

IP = "192.168.0.103"
requests.post(
    "http://%s/api/led" % IP, json={"red": "0", "green": "125", "blue": "255"}
)
