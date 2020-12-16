# diy-sonoff
Self-made Sonoff-like WIFI switch using ESP01 and MicroPython

## Installation
1. Enable webrepl using the serial REPL prompt by typing
`import webrepl_setup`
2. Add a `credentials.py` file to the esp8266 flash memory
containing your WIFI credentials. This file should look
like this:
  ```
  ESSID = "your WIFI name"
  Password = "your WIFI password"
  ```
3. Add `umqtt` from the [umqtt.simple][1] repository to the
esp8266 flash.

[1]: https://github.com/micropython/micropython-lib/tree/master/umqtt.simple
