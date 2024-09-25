import json
import threading
import time

import cv2
import socket
import base64
import struct

from FlaskServer.Shared import *
from FlaskServer.server import FRAME_RATE


def stream_video_to_server(video_path, client_socket):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    i = 0

    encodeParams = [cv2.IMWRITE_JPEG_QUALITY, 80]

    lastTime = time.time()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Reached the end of the video, restarting...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to the first frame
            continue

        # Encode the frame as a JPEG image
        # _, encoded_image = cv2.imencode('.jpg', frame)
        encoded, encoded_image = cv2.imencode('.jpg', frame, encodeParams)

        # Convert the encoded image to bytes and then to base64
        encoded_bytes = encoded_image.tobytes()

        # Send the size of the frame first
        frame_size = len(encoded_bytes)
        client_socket.sendall(struct.pack('>I', frame_size))

        if i % FRAME_RATE == 0:
            print("Frames " + str(FRAME_RATE) + " Time: " + str(time.time() - lastTime))
            lastTime = time.time()
            i = 0

        # Send the actual frame data
        client_socket.sendall(encoded_bytes)

        # Add some delay to simulate real-time streaming
        # time.sleep(1 / 60)
        i += 1

    # Release resources
    cap.release()
    client_socket.close()
    print("Video streaming finished.")


def receive_json_data(server_socket):
    while True:
        try:
            # Receive the data in chunks (here 1024 bytes per chunk)
            data = server_socket.recv(1024).decode('utf-8')
            if not data:
                print("No data received. Connection might be closed.")
                break

            # Dummy operation: do nothing with the received JSON data
            print(f"Received data: {data}")  # Just printing, can be removed if no output is needed

        except Exception as e:
            print(f"Error receiving data: {e}")
            break

    print("Receiver done")


def start_dummy(video_path, server_ip, server_port):
    # Create a client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.sendall("drone".encode('utf-8'))
    print(f"Connected to server at {server_ip}:{server_port}")
    #length_bytes = client_socket.recv(4)
    # if not length_bytes:
    #     return None

    # Convert the 4-byte length into an integer
    #json_length = struct.unpack('>I', length_bytes)[0]
    json_data = client_socket.recv(1024).decode('utf-8')
    status = json.loads(json_data)
    print(f"Received drone status: {status}")
    if status['isPoweredOn']==False:
        print("Power off")
    else:
        print("on")

    receiver_thread = threading.Thread(target=receive_json_data, args=(client_socket,))
    receiver_thread.daemon = True
    receiver_thread.start()
    print("Receiver thread started.")

    stream_video_to_server(video_path, client_socket)


if __name__ == "__main__":
    # Example usage
    VIDEO_PATH = 'stock_footage.mp4'
    if internal:
        SERVER_IP = '192.168.1.17'
    else:
        SERVER_IP = getExternalIp()

    try:
        start_dummy(VIDEO_PATH, SERVER_IP, server_port)
    except Exception as e:
        print("Streamer died " + str(e))
