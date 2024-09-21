import requests
import socket
import threading
import cv2
import struct
import pickle
import base64
import json
import time

from github import Github
#from picamera2 import Picamera2
import time
import multiprocessing

from dronePrivateData import *

cameraResolution = (1280, 720)
cameraFramerate = 1 / 60


def getServerIP():
    # Authenticate to GitHub
    g = Github(GITHUB_TOKEN)

    # Get the repository
    repo = g.get_repo(REPO_NAME)

    # Get the file contents
    try:
        file = repo.get_contents(FILE_PATH, ref=BRANCH_NAME)
        currentIP = file.decoded_content.decode()

        return currentIP

    except Exception as e:
        if "404" in str(e):
            print(f"{FILE_PATH} not found on GitHub!")
            return None
        else:
            # Other errors
            print(f"An error occurred: {e}")
            return


def authenticateDrone(sock):
    sock.sendall("drone".encode())


def send_camera_stream2(client_socket: socket):
    picam2 = Picamera2()
    # picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
    # picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (1920, 1080)}))
    picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": cameraResolution}))
    picam2.start()

    while True:
        try:
            frame = picam2.capture_array()

            encoded, buffer = cv2.imencode('.jpg', frame)

            jpg_as_text = base64.b64encode(buffer)

            # size = int(len(jpg_as_text) / 1024) + 1
            size = len(jpg_as_text).to_bytes(4, byteorder='big', signed=False)

            client_socket.sendall(size)


            client_socket.sendall(jpg_as_text)

        except:
            break

    picam2.stop()
    cv2.destroyAllWindows()

class UserInputDataClass:

    def __init__(self):
        self.data = dict()

user_input = UserInputDataClass()

# Function to handle receiving data
def receiveControls(sock):
    
    # type:
    # 10 -- upali se
    # 13 -- ugasi se
    # 11 -- radi djojstik

    while True:
        data = sock.recv(1024).decode("utf-8")

        if not data: continue

        start = data.find("{")
        end = data.find("}")

        json_str = data[start:end + 1]
        data2 = json.loads(json_str)
        #print(f"data: {data}")
        #print(f"data2: {data2}")
        user_input.data = {
            "y_left": -float(data2["rotation"]),
            "x_left": float(data2["z"]),
            "y_right": -float(data2["y"]),
            "x_right": float(data2["x"]),
            "state:": int(data2["type"])
        }
        #print(user_input.data)


# Main function to create socket and start threads
def start_server_connection():
    while True:
        server_address = getServerIP()

        if server_address is None:
            print("Server IP is None!")
            time.sleep(60)
            continue

        server_ip = server_address.split(":")[0]
        serverPort = int(server_address.split(":")[1])

        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        s.connect((server_ip, serverPort))
        print("Connected to server!")

        authenticateDrone(s)

        print("Authenticated as drone!")

        # Create and start threads for sending and receiving data
        #send_thread = multiprocessing.Process(target=send_camera_stream2, args=(s,))
        #receive_thread = multiprocessing.Process(target=receiveControls, args=(s,))
        receive_thread = threading.Thread(target=receiveControls, args=(s,))

        #send_thread.start()
        receive_thread.start()

        # Wait for threads to complete
        #send_thread.join()
        #receive_thread.join()
        return

if __name__ == "__main__":
    start_server_connection()
