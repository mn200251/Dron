import threading
import time

import cv2
import socket
import base64
import struct

from FlaskServer.Shared import *


def stream_video_to_server(video_path, client_socket):
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    i = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Reached the end of the video, restarting...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to the first frame
            continue

        # Encode the frame as a JPEG image
        _, encoded_image = cv2.imencode('.jpg', frame)

        # Convert the encoded image to bytes and then to base64
        encoded_bytes = encoded_image.tobytes()
        encoded_base64 = base64.b64encode(encoded_bytes)

        # Send the size of the frame first
        frame_size = len(encoded_base64)
        client_socket.sendall(struct.pack('>I', frame_size))

        if i % 60 == 0:
            print("Sent 60 frames")
            i = 0

        # Send the actual frame data
        client_socket.sendall(encoded_base64)

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

    receiver_thread = threading.Thread(target=receive_json_data, args=(client_socket,))
    receiver_thread.daemon = True
    receiver_thread.start()
    print("Receiver thread started.")

    stream_video_to_server(video_path, client_socket)


if __name__ == "__main__":
    # Example usage
    VIDEO_PATH = 'FlaskServer/stock-footage_1280x720.mp4'

    if internal:
        SERVER_IP = '192.168.1.17'
    else:
        SERVER_IP = getExternalIp()

    try:
        start_dummy(VIDEO_PATH, SERVER_IP, server_port)
    except Exception as e:
        print("Streamer died " + str(e))
