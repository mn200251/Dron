import time

import cv2
import socket
import base64
import struct


def stream_video_to_server(video_path, server_ip, server_port):
    # Create a client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.sendall("drone".encode('utf-8'))
    print(f"Connected to server at {server_ip}:{server_port}")

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video file or error in reading the frame.")
            break

        # Encode the frame as a JPEG image
        _, encoded_image = cv2.imencode('.jpg', frame)

        # Convert the encoded image to bytes and then to base64
        encoded_bytes = encoded_image.tobytes()
        encoded_base64 = base64.b64encode(encoded_bytes)

        # Send the size of the frame first
        frame_size = len(encoded_base64)
        client_socket.sendall(struct.pack('>I', frame_size))
        print(frame_size)
        # Send the actual frame data
        client_socket.sendall(encoded_base64)

        # Add some delay to simulate real-time streaming
        time.sleep(0.2)

    # Release resources
    cap.release()
    client_socket.close()
    print("Video streaming finished.")


if __name__ == "__main__":
    # Example usage
    VIDEO_PATH = 'videos/VID_20230416_123915.mp4'  # Replace with the path to your video file
    SERVER_IP = '192.168.1.17'  # Replace with your server's IP address
    SERVER_PORT = 6969  # Replace with your server's port
    try:
        stream_video_to_server(VIDEO_PATH, SERVER_IP, SERVER_PORT)
    except Exception as e:
        print("Streamer died " + str(e))
