#### Imports ####

from pprint import pprint as pr
from pyudev import Context
from evdev import ecodes

import evdev
import asyncio

import struct
import socket

### Static Vars ###

encode_types = {
    0: 'bb', # Mouse Movement
    1: 'BB', # Click Event
    2: 'Bb' # Scroll Event
}

server = ('192.168.100.178', 12345)

### Functions ###

def get_devices() -> list[evdev.InputDevice]:

    context = Context()
    event_list = []

    for dev in context.list_devices(ID_INPUT_MOUSE=1, ID_INPUT_TOUCHPAD=1):
        devices = dict(dev.properties)

        if "DEVNAME" in devices and "/dev/input/event" in devices["DEVNAME"]:
            event_list.append(devices["DEVNAME"])

    if not event_list:
        raise Exception

    inputdevices = [evdev.InputDevice(path) for path in event_list]
    for i in inputdevices:
        print(f"Found: {i.name} ({i.phys})")

    return inputdevices

def send_data(data: list, server_addr: tuple) -> None:

    if not all(isinstance(n, int) for n in data):
        print(f"Arguments must be integers: \n{data}")
        raise Exception
    
    datatype = data[0]
    if datatype not in encode_types:
        raise Exception

    encode = 'b' + encode_types[datatype]
    if not len(data) <= struct.calcsize(encode):
        print(f"Invalid data length: {len(data)}")
        raise Exception

    bytedata = struct.pack(encode, *data)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(bytedata, server_addr)


################

async def handle_device(device):

    prev_timestamp = None
    tmp_list = []

    mouse_wheel = [
        ecodes.REL_WHEEL, 
        #ecodes.REL_WHEEL_HI_RES, 
        ecodes.REL_HWHEEL, 
        #ecodes.REL_HWHEEL_HI_RES 
    ]
    
    mouse_rel = [
        ecodes.REL_X,
        ecodes.REL_Y 
    ]

    mouse_abs = [
        ecodes.ABS_X,
        ecodes.ABS_Y 
    ]

    async for event in device.async_read_loop():

        # Handle mouse clicks
        if event.type == 1:
            clickData = [1, event.value]
            
            match event.code:
                case x if x in [ecodes.BTN_LEFT, ecodes.BTN_MOUSE]:
                    clickData.insert(1, 0)
                    print("Left Button ", + event.value)

                case ecodes.BTN_RIGHT:
                    clickData.insert(1, 1)
                    print("Right Button ", + event.value)
                case _:
                    raise Exception

            send_data(clickData, server)

        # Handle Scrollwheel
        if event.type == 2 and event.code in mouse_wheel:
            scrollData = [2, event.value]

            match event.code:
                case ecodes.REL_WHEEL:
                    scrollData.insert(1, 0)
                    print('Scrollwheel: ' + str(event.value))

                case ecodes.REL_HWHEEL:
                    scrollData.insert(1, 1)
                    print('Horizontal Scrollwheel: ' + str(event.value))
                case _:
                    raise Exception

            send_data(scrollData, server)

        # Handle Relative Mouse Movement
        if event.type == 2 and event.code in mouse_rel:

            data = {
                "timestamp": event.timestamp(),
                "type": event.type,
                "code": event.code,
                "value": event.value
            }

            if prev_timestamp is None or prev_timestamp == event.timestamp():
                tmp_list.append(data)

            if prev_timestamp != event.timestamp():
                pr(tmp_list)

                x = 0
                y = 0

                for i in tmp_list:
                    match i.get("code"):
                        case ecodes.REL_X:
                            x = i.get("value")
                        case ecodes.REL_Y:
                            y = i.get("value")

                # Move mouse here with x, y values
                print(x, y)
                print("")

                relMouse = [0, x, y]
                send_data(relMouse, server)

                tmp_list.clear()
                tmp_list.append(data)

            prev_timestamp = event.timestamp()
        

async def main(): 

    devices = get_devices()
    tasks = [handle_device(device) for device in devices]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(
        main()
    )
