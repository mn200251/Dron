# from flask import Flask
import json
import threading
import time

import socket
import struct
import pickle
import cv2

import requests

# app = Flask(__name__)


# @app.route('/')
# def index():
#     return "TCP Socket Server is Running"


phoneConnected = False
droneConnected = False
phoneSocket = None
droneSocket = None


def getInternalIp():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def getExternalIp():
    response = requests.get('https://api.ipify.org?format=json')
    ip_data = response.json()
    ip_address = ip_data['ip']
    return ip_address



def handleCameraStream():
    global phoneSocket, droneSocket, phoneConnected, droneConnected

    # wait for phone to connect
    # while not phoneConnected:
    #     time.sleep(0.2)

    while True:
        try:
            data = b""
            payload_size = struct.calcsize("L")

            while True:
                try:
                    while len(data) < payload_size:
                        packet = droneSocket.recv(4 * 1024)
                        if not packet:
                            break
                        data += packet



                    if len(data) < payload_size:
                        print("Incomplete packet received for message size")
                        break

                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("L", packed_msg_size)[0]


                    while len(data) < msg_size:
                        packet = droneSocket.recv(4 * 1024)
                        if not packet:
                            break
                        data += packet



                    if len(data) < msg_size:
                        print("Incomplete packet received for frame data")
                        break

                    frame_data = data[:msg_size]
                    data = data[msg_size:]

                    print(f"Expected message size: {msg_size}, received data size: {len(data)}")
                    print(f"Received frame data size: {len(frame_data)}")

                    frame = pickle.loads(frame_data)
                    cv2.imshow('Received', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except Exception as e:
                    print(f"Error: {e}")
                    break



        except ConnectionResetError:
            break

    droneConnected = False




# drone
def handleControls():
    global phoneSocket, droneSocket, phoneConnected, droneConnected

    # wait for drone to connect
    # while not droneConnected:
    #     time.sleep(0.2)

    while True:
        try:
            data = phoneSocket.recv(1024).decode('utf-8')

            if not data:
                continue

            start = data.rfind("{")
            end = data.rfind("}")

            if start == -1 or end == -1:
                print("Received invalid JSON!")
                continue

            controlJson = data[start:end + 1]

            try:
                # print(f"Received data: {controlJson}")
                coordinates = json.loads(controlJson)
                print(f"x={coordinates["x"]}, y={coordinates["y"]}, z={coordinates["z"]}")
            except json.JSONDecodeError:
                print("Received invalid data")
                break

            # droneSocket.sendall(controls.encode())


        except ConnectionResetError:
            break

    phoneConnected = False

# Function to handle client connections
def handle_client_connection(client_socket):
    global phoneConnected, droneConnected, droneSocket, phoneSocket

    while True:
        try:
            message = client_socket.recv(1024).decode()

            match message:
                case "drone":
                    if droneConnected:
                        print(f"Error: Drone is already connected!")
                        break
                    droneConnected = True
                    droneSocket = client_socket
                    handleCameraStream()

                case "phone":
                    if phoneConnected:
                        print(f"Error: Phone is already connected!")
                        break

                    phoneConnected = True
                    phoneSocket = client_socket
                    phoneSocket.sendall("0\n".encode())  # everything ok
                    handleControls()

                case _:
                    print(f"Received message: {message}")
                    client_socket.sendall("-1\n".encode())
                    break

            # if message:
            # print(f"Received message: {message}")
            # client_socket.sendall("1".encode()) # everything is ok

            # else:
            # break
        except ConnectionResetError:
            break
    client_socket.close()


# Function to start the TCP server
def start_tcp_server(server_ip, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_socket.bind((server_ip, server_port))
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"TCP Server started on {server_ip}:{server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    server_ip = "0.0.0.0"
    # server_ip = getInternalIp()
    # server_ip = getExternalIp()
    server_port = 6969

    print(f"IP for external connections: {getExternalIp()}:{server_port}")

    # Start the TCP server in a separate thread
    tcp_server_thread = threading.Thread(target=start_tcp_server, args=(server_ip, server_port))
    tcp_server_thread.start()

    tcp_server_thread.join()
    # Start the Flask server
    # app.run(host='0.0.0.0', port=5000)
