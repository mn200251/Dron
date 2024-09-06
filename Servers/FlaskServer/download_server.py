import base64
import json
import os
import struct

import cv2
import requests

from FlaskServer.Shared import *


def generate_thumbnail(video_path):
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()
    if success:
        _, buffer = cv2.imencode('.jpg', frame)
        thumbnail_bytes = buffer.tobytes()
        return base64.b64encode(thumbnail_bytes).decode('utf-8')
    return None


def get_video_list():
    video_dir = 'videos'
    video_list = []
    for filename in os.listdir(video_dir):
        if filename.endswith(".mp4"):  # Check if the file is a video
            video_path = os.path.join(video_dir, filename)
            thumbnail = generate_thumbnail(video_path)
            video_list.append({
                'filename': filename,
                'thumbnail': thumbnail
            })
    return video_list


def get_video_names():
    """
    Get the list of video filenames without generating thumbnails.
    """
    video_dir = 'videos'
    video_list = []
    for filename in os.listdir(video_dir):
        if filename.endswith(".mp4"):  # Check if the file is a video
            video_list.append(filename)
    return video_list


def handle_video_listing(phoneSocket):
    """
       Handles requests to get the list of videos, including their thumbnails, and sends them one by one to avoid overflow.
       """
    global video_list
    buffer = ""
    print("in")
    try:
        while True:
            # Receive data from the socket
            data = phoneSocket.recv(1024).decode('utf-8')
            if not data:
                continue

            buffer += data
            # Extract the last complete JSON object
            start = buffer.rfind("{")
            end = buffer.rfind("}")

            if start == -1 or end == -1:
                continue

            json_str = buffer[start:end + 1]

            try:
                instruction_data = json.loads(json_str)
                instruction_type = instruction_data.get("type")
                print("Received instruction:", instruction_data)

                if instruction_type is None:
                    print("Invalid instruction")
                elif instruction_type == InstructionType.GET_VIDEOS.value:
                    index = instruction_data.get("index")
                    if index is None:
                        video_list = get_video_names()
                        phoneSocket.sendall(str(len(video_list)).encode('utf-8'))
                        print("Number of videos is " + str(len(video_list)))
                    elif index is not None and 0 <= index < len(video_list):
                        video_name = video_list[index]
                        thumbnail = generate_thumbnail(os.path.join('videos', video_name))
                        video_data = {
                            'filename': video_name,
                            'thumbnail': thumbnail
                        }
                        video_json = json.dumps(video_data).encode('utf-8')
                        json_length = len(video_json)

                        # Send the length of the JSON
                        phoneSocket.sendall(struct.pack('>I', json_length))

                        # Send the actual JSON data
                        phoneSocket.sendall(video_json)
                        print(f"Sent video metadata for index {index}")
                else:
                    print(f"Unknown instruction type: {instruction_type}")

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue

    except Exception as e:
        print(f"An error occurred in video requests handler: {e}")


def handle_video_download(phoneSocket):
    """
    Handles the incoming control instructions like GET_STATUS, TURN_OFF, GET_LINK.
    """
    global response
    buffer = ""
    is_active = True
    status = ""
    try:
        while is_active:
            # Receive data from the socket
            data = phoneSocket.recv(1024).decode('utf-8')
            if not data:
                continue

            buffer += data
            # Process all complete JSON objects in the buffer
            while True:
                start = buffer.find("{")
                end = buffer.find("}")

                if start == -1 or end == -1:
                    break

                json_str = buffer[start:end + 1]
                buffer = buffer[end + 1:]

                try:
                    instruction_data = json.loads(json_str)
                    instruction_type = instruction_data.get("type")
                    print("Received instruction:", instruction_data)

                    if instruction_type is None:
                        print("Invalid instruction")
                    elif instruction_type == InstructionType.DOWNLOAD_VIDEO.value:
                        try:
                            response = None
                            print('Handle video download.')
                            video_name = instruction_data.get("video_name")
                            file_path = f"videos/{video_name}"

                            # Upload the file
                            with open(file_path, 'rb') as file:
                                response = requests.post('https://file.io/', files={'file': file})

                            status = -1
                            file_url = ''
                            # Check if the upload was successful
                            if response.status_code == 200:
                                # Get the download link from the response
                                file_url = response.json().get('link')
                                status = 200
                                print(f'File uploaded successfully. Download URL: {file_url}')
                            else:
                                print('File upload failed.')
                            response = {
                                'status': status,
                                'link': file_url
                            }
                            flag = False
                            # DUMMY
                            # time.sleep(5)
                            # response = {
                            #     'status': 200,
                            #     'link': 'https://www.google.com/'
                            # }

                        except Exception as e:
                            print("An error occurred in controls: " + str(e))
                    elif instruction_type == InstructionType.GET_STATUS.value:
                        if response is None:
                            status = "no"
                        else:
                            status = "ok"
                        phoneSocket.sendall(status.encode('utf-8'))
                    elif instruction_type == InstructionType.GET_LINK.value:
                        json_data = json.dumps(response).encode('utf-8')
                        # Send JSON data
                        print(json_data)
                        phoneSocket.sendall(json_data)
                        print("Phone informed of the results: ")
                    else:
                        print(f"Unknown instruction type in regard to video download: {instruction_type}")

                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

    except Exception as e:
        print(f"An error occurred in video download handler: {e}")


def handle_client_connection_video(client_socket):
    """
        Handles incoming client connections for video-related cases.
    """
    global connections
    while True:
        try:
            message = client_socket.recv(1024).decode()
            client_socket.settimeout(TIMEOUT)
            match message:
                case "video_download":
                    client_socket.sendall("0\n".encode())  # everything ok
                    handle_video_download(client_socket)
                case "video_listing":
                    client_socket.sendall("0\n".encode())  # everything ok
                    handle_video_listing(client_socket)
                case _:
                    print(f"Received invalid message for video handler: {message}")
                    client_socket.sendall("-1\n".encode())
                    break
            break
        except Exception as e:
            print(f"Connection failed to establish in video handler: {e}")
            break
    client_socket.close()
