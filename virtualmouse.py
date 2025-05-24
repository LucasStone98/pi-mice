import socket
import struct

import hupper

def live_reloader():
    reloader = hupper.start_reloader('main.main')

encode_types = {
        0: 'bb', # Mouse Movement
        1: 'BB', # Click Event
        2: 'Bb' # Scroll Event
}

def main():
    print("Starting Hupper")
    live_reloader()
    print("UDP Server Listening...")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_address = ('0.0.0.0', 12345)
    server_socket.bind(server_address)

    while True:
        data, client_address = server_socket.recvfrom(1024)
        if not data or len(data) != 3:
            print(f"Unknown data packet: {data}")
            continue

        header = struct.unpack('b', data[:1])[0]
        match header:
            case 0:
                x, y = struct.unpack(encode_types[0], data[1:])
                print(f"Mouse: {x}, {y}\n")

            case 1:
                button, value = struct.unpack(encode_types[2], data[1:])
                match button:
                    case 0:
                        print("Left Button " + str(value))
                    case 1:
                        print("Right Button " + str(value))

            case 2:
                wheeltype, value = struct.unpack(encode_types[2], data[1:])
                print(f"Scrollwheel {wheeltype}: {value}\n")

            case _:
                print(f"Unknown data type in header byte:\n{data}\n{data[:1]}")
                continue

if __name__ == "__main__":
    main()
