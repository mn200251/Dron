# from flask import Flask
import base64
import json
import threading
import time

import socket
import cv2
import numpy as np

import requests

from github import Github

from serverPrivateData import *

phoneConnected = False
droneConnected = False
phoneSocket: socket = None
droneSocket: socket = None

ip_update_interval = 60 * 10


def changeServerIP(newIP):
    # Authenticate to GitHub
    g = Github(GITHUB_TOKEN)

    # Get the repository
    repo = g.get_repo(REPO_NAME)

    # Get the file contents
    try:
        file = repo.get_contents(FILE_PATH, ref=BRANCH_NAME)
    except Exception as e:
        if "404" in str(e):
            repo.create_file(FILE_PATH, f'Created server_ip.txt with current IP: {newIP}', newIP,
                             branch=BRANCH_NAME)
            return
        else:
            # Other errors
            print(f"An error occurred: {e}")
            return

    currentIP = file.decoded_content.decode()

    if currentIP == newIP:
        print("changeServerIP - Server IP didn't change")
        return

    # Commit and push the changes
    repo.update_file(file.path, f'Updated server_ip.txt with new IP: {newIP}', newIP, file.sha,
                     branch=BRANCH_NAME)


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
    while not phoneConnected:
        if droneSocket is None:
            droneConnected = False
            return

        time.sleep(0.2)

    i = 0

    while True:
        try:
            size = droneSocket.recv(4)

            if size == b'' or size is None:
                continue

            # Convert bytes back to integer
            size = int.from_bytes(size, byteorder='big', signed=False)

            # Receive the actual frame
            frame_data = b''
            while len(frame_data) < size:
                packet = droneSocket.recv(size - len(frame_data))
                if not packet:
                    break
                frame_data += packet

            img = base64.b64decode(frame_data)

            if img is None:
                print('img is none')

            npimg = np.frombuffer(img, np.uint8)

            if npimg is None:
                print('npimg is none')

            source = cv2.imdecode(npimg, 1)

            # with open(f"test{i}.jpg", "wb") as f:
            #     f.write(npimg)

            _, jpeg = cv2.imencode('.jpg', source)
            jpeg_bytes = jpeg.tobytes()

            while phoneSocket is None:
                continue

            try:
                phoneSocket.sendall(len(jpeg_bytes).to_bytes(4, byteorder='big', signed=False))
                phoneSocket.sendall(jpeg_bytes)
            except:
                print('Phone not connected to send image!')

            cv2.imshow("Stream", source)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            i = i + 1

        except ConnectionResetError:
            print("ConnectionResetError in handleCameraStream")
            break
        except KeyboardInterrupt:
            cv2.destroyAllWindows()
            break
        except:
            print('Exception in handleCameraStream')
            break

    print(f"broj frejmova: {i}")

    droneConnected = False
    droneSocket = None


# drone
def handleControls():
    global phoneSocket, droneSocket, phoneConnected, droneConnected

    # wait for drone to connect
    while not droneConnected:
        time.sleep(0.2)

    while True:
        try:
            data = phoneSocket.recv(1024).decode('utf-8')

            if not data:
                continue

            if not phoneConnected:
                time.sleep(0.05)

            droneSocket.sendall(data.encode('utf-8'))

            start = data.rfind("{")
            end = data.rfind("}")

            if start == -1 or end == -1:
                print("Received invalid JSON!")
                continue

            controlJson = data[start:end + 1]

            # droneSocket.sendall(controlJson.encode('utf-8'))

            try:
                # print(f"Received data: {controlJson}")
                coordinates = json.loads(controlJson)
                print(f"x={coordinates["x"]}, y={coordinates["y"]}, z={coordinates["z"]}, rotation={coordinates["rotation"]}")
            except json.JSONDecodeError:
                print("Received invalid data")
                break


        except ConnectionResetError:
            print("ConnectionResetError in handleControls")
            break

    phoneConnected = False
    phoneSocket = None


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


def monitorIP():
    while True:
        newIP = getExternalIp() + ":" + str(server_port)
        changeServerIP(newIP)

        time.sleep(ip_update_interval)


if __name__ == "__main__":
    server_ip = "0.0.0.0"

    print(f"IP for external connections: {getExternalIp()}:{server_port}")

    # Start the TCP server in a separate thread
    tcp_server_thread = threading.Thread(target=start_tcp_server, args=(server_ip, server_port))
    tcp_server_thread.start()

    monitor_ip_thread = threading.Thread(target=monitorIP)
    monitor_ip_thread.start()

    tcp_server_thread.join()
