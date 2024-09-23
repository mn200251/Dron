import json
from multiprocessing import Manager, Process

import requests
import socket
import threading
import socket
import cv2
import struct
import pickle
import base64

from github import Github
from picamera2 import Picamera2
import time

from flight_controller import run

cameraResolution = (1280, 720)
cameraFramerate = 1 / 60


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


# Function to handle receiving data
def receive_controls(sock, shared_dict:Manager.dict):
    """Function to receive controls from a socket and update shared dictionary."""
    while True:
        try:
            data = sock.recv(1024).decode("utf-8")
            if not data:
                continue

            print("Received controls:", data)

            # Assume data is JSON formatted and parse it
            try:
                controls = json.loads(data)  # Parse JSON data

                # Update the shared dictionary
                shared_dict.update(controls)
                print("Updated shared dictionary:", shared_dict)

            except json.JSONDecodeError:
                print("Received invalid JSON")

        except Exception as e:
            print(f"Error receiving data: {e}")
            break


# Main function to create socket and start threads
internal=True
server_port=6969
def main():
    while True:
        server_address = None
        if internal:
            server_ip = "192.168.1.17"
            print(f"IP for internal connections: {server_ip}:{server_port}")
            print(f"IP for download internal connections: {server_ip}:{server_port}")

        if server_address is None:
            print("Server IP is None!")
            time.sleep(60)
            continue


        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        s.connect((server_ip, server_port))
        print("Connected to server!")

        authenticateDrone(s)

        print("Authenticated as drone!")

        manager = Manager()
        shared_dict = manager.dict()  # Shared dictionary to store controls
        shared_dict.update({'type':11, 'x':0.0, 'y':0.0,'z':0.0,'rotation':0.0})
        # Start a separate process for the socket server
        fc = Process(target=run, args=(shared_dict,))
        # Create and start threads for sending and receiving data
        send_thread = threading.Thread(target=send_camera_stream2, args=(s,))
        receive_thread = threading.Thread(target=receive_controls, args=(s,))

        send_thread.start()
        receive_thread.start()

        # Wait for threads to complete
        send_thread.join()
        receive_thread.join()



if __name__ == "__main__":
    main()
