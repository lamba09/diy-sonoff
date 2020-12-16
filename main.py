import time
import network
import credentials
import ubinascii
import machine
import json

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("connecting to network..")
wlan.connect(credentials.ESSID, credentials.Password)
while not wlan.isconnected():
    time.sleep(0.5)
print("connected.")

import ntptime
ntptime.settime()

relay = machine.Pin(0, machine.Pin.OUT)
relay.off()

MQTT_CONFIG = {
     "USER": "",
     "PASSWORD": "",
     "PORT": 1883,
     "TOPIC": b"loggia",
     # unique identifier of the chip
     "CLIENT_ID": b"esp8266_" + ubinascii.hexlify(machine.unique_id())
}

newMessage = None

def onMQTTMessage(topic, msg):
    global newMessage
    print("Topic: %s, Message: %s" % (topic, msg))
    if msg == b"on":
        relay.on()
    elif msg == b"off":
        relay.off()
    
    newMessage = msg

def current_time():
    return list(time.localtime()[3:6])

def ftime(t):
    return b"{0:02d}:{1:02d}:{2:02d}".format(*t)

def set_time(newMessage):
    _, set_time = newMessage.split(b"/")
    t_list = set_time.split(b":")
    if len(t_list) != 3:
        return
    h, m, s = t_list
    if not (h.isdigit() and m.isdigit() and s.isdigit()):
        return
    return [int(h), int(m), int(s)]

def save_time(name, time):
    with open(name, "w") as f:
        json.dump(time, f)

def load_time(name):
    with open(name, "r") as f:
        time = json.load(f)
    return time

def its_on_time(now):
    if on_time < off_time:
        return on_time < now < off_time
    if off_time < on_time:
        return not(off_time < now < on_time)
    return False

on_time = load_time("on_time")
off_time = load_time("off_time")
timed_on = False
timed_off = False
time_updated = False

def each_loop(client):
    global newMessage
    global on_time
    global off_time
    global timed_on
    global time_updated
    if newMessage in [b'on', b'off']:
        client.publish(MQTT_CONFIG['TOPIC'] + b'/state', newMessage)
        newMessage = None
    elif newMessage == b"time":
        print("it's", current_time())
        client.publish(MQTT_CONFIG['TOPIC'] + b'/time', ftime(current_time()))
        client.publish(MQTT_CONFIG['TOPIC'] + b'/on_time', ftime(on_time))
        client.publish(MQTT_CONFIG['TOPIC'] + b'/off_time', ftime(off_time))
        newMessage = None
    elif newMessage is not None and newMessage.startswith(b"set_on_time/"):
        ntptime.settime()
        t = set_time(newMessage)
        if t is not None:
            print(t)
            on_time = t
            save_time("on_time", t)
            client.publish(MQTT_CONFIG['TOPIC'] + b'/on_time', ftime(t))
            newMessage = None
    elif newMessage is not None and newMessage.startswith(b"set_off_time/"):
        ntptime.settime()
        t = set_time(newMessage)
        if t is not None:
            print(t)
            off_time = t
            save_time("off_time", t)
            client.publish(MQTT_CONFIG['TOPIC'] + b'/off_time', ftime(t))
            newMessage = None

    now = current_time()
    if its_on_time(now) and not timed_on:
        print("timed ON")
        relay.on()
        client.publish(MQTT_CONFIG['TOPIC'] + b'/state', b"on")
        timed_on = True
    elif not its_on_time(now) and timed_on:
        print("timed OFF")
        relay.off()
        client.publish(MQTT_CONFIG['TOPIC'] + b'/state', b"off")
        timed_on = False
    
    if [12, 0, 0] < now < [13, 0, 0] and not time_updated:
        ntptime.settime()
        time_updated = True
    elif now > [14, 0, 0]:
        time_updated = False

    time.sleep(0.5)
        

from mqtt import listen
try:
    listen(onMQTTMessage, each_loop, MQTT_CONFIG)
except Exception as e:
    with open("bugreport.txt", "w") as f:
        f.write(repr(e))
