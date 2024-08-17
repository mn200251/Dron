# from flask import Flask
import base64
import json
import os
import queue
import struct
import threading
import time

import socket
import cv2
import numpy as np

import requests

from github import Github

from serverPrivateData import *

from enum import Enum



class RecordState(Enum):
    NOT_RECORDING = 0
    START_RECORDING = 1
    RECORDING = 2
    STOP_RECORDING = 3


class PhoneState(Enum):
    STARTED = 0  # on main screen
    AUTOPILOT = 1  # recreating flight
    PILOTING = 2  # client is controling the drone
    BROWSING_VIDEOS = 3  # not needed
    BROWSING_FLIGHTS = 4  #
    DOWNLOADING_VIDEO = 5  #


class InstructionType(Enum):
    HEARTBEAT = 1
    START_RECORDING = 2
    STOP_RECORDING = 3
    START_FLIGHT = 4
    END_FLIGHT = 5
    GET_FLIGHTS = 6
    START_PREVIOUS_FLIGHT = 7
    GET_VIDEOS = 8
    DOWNLOAD_VIDEO = 9
    KILL_SWITCH = 10
    JOYSTICK = 11

    TURN_OFF = 13
    GET_STATUS = 14  # da proveri stanje jer neke instrukcije mozda nisu prosle npr pocni snimanje
    BACK = 15  # povratak iz browsinga videa/letova?


# Constants
MAX_QUEUE_SIZE = 120
TIMEOUT = 3
QUEUE_TIMEOUT = 5
video_dir = "videos"
# Global variables to manage connections
phoneConnected = False
droneConnected = False
video_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
command_dict = {
    "type": InstructionType.JOYSTICK.value,
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "rotation": 0.0
}
control_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
connections = {'drone': None, 'phone': None}
# Interval to update the IP address on GitHub (in seconds)
ip_update_interval = 60 * 10

# Server port
server_port = 6969

# Flag to determine if the server is internal or external
internal = True

# To remember the states
phone_state = PhoneState.STARTED
record_video = RecordState.NOT_RECORDING

stop_event = threading.Event()
send_event = threading.Event()
# For video download
cap = None
frame_count =0
frame= None
current_frame = 0
lock=threading.Lock()
# FUNCTIONS
def changeServerIP(newIP):
    """
        Updates the server IP address stored in a GitHub repository.
    """
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
    """
        Retrieves the internal IP address of the server.
    """
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def getExternalIp():
    """
        Retrieves the external IP address of the server.
    """
    response = requests.get('https://api.ipify.org?format=json')
    ip_data = response.json()
    ip_address = ip_data['ip']
    return ip_address


def monitorIP():
    """
        Periodically updates the server's external IP address on GitHub.
    """
    while True:
        newIP = getExternalIp() + ":" + str(server_port)
        changeServerIP(newIP)

        time.sleep(ip_update_interval)


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

def handle_video_download(cap, phoneSocket)->bool:
    # sends the video (continue where the old thread left off in case of disconnect)
    # to not skip frames either
    # the cap.set must be used to move to the previous frame - i chose this
    # or have the frame as global
    global current_frame, frame_count, phone_state,lock
    print("F:" +str(frame_count))
    with lock:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        try:
            while frame_count > current_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                _, jpeg = cv2.imencode('.jpg', frame)
                frame_data = jpeg.tobytes()
                frame_size = len(frame_data)

                # Send frame size and frame data
                phoneSocket.sendall(struct.pack('>I', frame_size))
                phoneSocket.sendall(frame_data)

                current_frame += 1
                if current_frame%4==0:
                    print(frame_size)
                    signal_message = phoneSocket.recv(1).decode('utf-8')
            frame_count = 0
            current_frame = 0
            cap.release()
            cv2.destroyAllWindows()
            phone_state = PhoneState.BROWSING_VIDEOS
            print("Finished sending video")
            return True
        except Exception as e:
            print("An error occured in video sending at frame "+str(current_frame))
    return False



# THREADS AND THEIR CREATION
def send_frames():
    """
    Funkcija send_frames preuzima frejmove iz video_queue i šalje ih na telefon.
    Ako dođe do greške tokom slanja, red se prazni kako bi se izbegli zastare frejmovi.
    Funkcija koristi timeout kako bi se izbeglo blokiranje i osigurava da se zaustavi kada je signalizovano putem stop_event.

    :return:
    """
    global stop_event, connections
    while not stop_event.is_set():
        try:
            jpeg_bytes = video_queue.get(timeout=QUEUE_TIMEOUT)
            phone_socket = connections["phone"]
            phone_socket.sendall(len(jpeg_bytes).to_bytes(4, byteorder='big', signed=False))
            phone_socket.sendall(jpeg_bytes)
        except queue.Empty:
            # Queue is empty, no frames to send
            continue
        except socket.error:
            # Error occurred during sending
            # Clear the queue on error
            with video_queue.mutex:
                video_queue.queue.clear()
            continue
        except AttributeError as e:
            print(f"Phone not connected")
        except Exception as e:
            print(f"Unexpected error in send_frames: {e}")
            continue



def handleDroneMessages(droneSocket):
    """
    Funkcija je zaduzena da prima poruke od drona.
    Trenutno to podrazumeva u petlji na cekanje na pocetak streama i primanje frejmova i njihovo stavljanje u video_queue.
    Funkcija takodje obuhvata cuvanje videa po potrebi.
    U slucaju prekida konekcije funkcija se zavrsava.
    :param droneSocket:
    :return:
    """
    global record_video, phone_state
    video_writer = None
    # stream alive
    flag = True
    while flag and not stop_event.is_set():
        i = 0
        # receiving the stream
        while phone_state == PhoneState.AUTOPILOT or phone_state == PhoneState.PILOTING:
            try:
                size = droneSocket.recv(4)

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

                _, jpeg = cv2.imencode('.jpg', source)
                jpeg_bytes = jpeg.tobytes()

                video_queue.put(jpeg_bytes)

                # Check if recording needs to be started or restarted in new thread because of a disconnected
                if record_video == RecordState.START_RECORDING or (
                        video_writer is None and record_video == RecordState.RECORDING):
                    # Initialize video writer
                    fourcc = cv2.VideoWriter_fourcc(*'H264')  # Codec for mp4
                    frame_width = source.shape[1]
                    frame_height = source.shape[0]
                    fps = 60  # Frames per second
                    video_writer = cv2.VideoWriter(f'videos/recording_{int(time.time() * 1000)}.mp4', fourcc, fps,
                                                   (frame_width, frame_height))
                    record_video = RecordState.RECORDING

                if record_video == RecordState.RECORDING:
                    video_writer.write(source)

                if record_video == RecordState.STOP_RECORDING:
                    if video_writer is not None:
                        video_writer.release()
                        video_writer = None
                    record_video = RecordState.NOT_RECORDING

                cv2.imshow("Stream", source)

                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                i = i + 1

            except ConnectionResetError:
                print("ConnectionResetError in handleCameraStream")
                break
            except KeyboardInterrupt:
                print("KeyboardInterrupt in handleCameraStream")
                break
            except:
                print('Exception in handleCameraStream')
                break
            finally:
                # stream died because of a disconnect
                flag = False

        print(f"broj frejmova: {i}")

        if video_writer is not None:
            video_writer.release()

        cv2.destroyAllWindows()


# Function to handle sending control messages to the drone
def send_controls():
    """
    Funkcija send_controls preuzima instrukcije iz deljenog objekta i šalje ih na dron.
    Ako dođe do greške tokom slanja, pokusa ponovo.
    Funkcija koristi timeout kako bi se izbeglo blokiranje i osigurava da se zaustavi kada je signalizovano putem stop_event.


    :return:
    """
    global stop_event, connections,send_event

    while not stop_event.is_set():
        send_event.wait()
        send_event.clear()
        try:
            data_to_send = json.dumps(command_dict).encode('utf-8')
            drone_socket = connections["drone"]
            drone_socket.sendall(data_to_send)
            command_dict["type"] = InstructionType.JOYSTICK.value
        except AttributeError as e:
            print(f"Drone not connected")
        except Exception as e:
            print(f"Failed to send data from send_controls: {e}")

            continue



# drone
def handleControls(phoneSocket):
    """
       Handles control messages from the phone and forwards them to the queue.
    """
    global command_dict,record_video, phone_state, cap, frame_count, send_event
    buffer = ""
    flag = True
    while flag:
        try:

            if phone_state == PhoneState.DOWNLOADING_VIDEO:
                flag=handle_video_download(cap, phoneSocket)
                continue

            data = phoneSocket.recv(1024).decode('utf-8')

            if not data:
                continue

            buffer += data
            flag_pass_commands=False
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
                    print(instruction_data)
                    if instruction_type is None:
                        print("Invalid instruction")
                    elif instruction_type == InstructionType.HEARTBEAT.value:
                        pass
                    elif instruction_type == InstructionType.START_RECORDING.value:
                        record_video = RecordState.START_RECORDING
                    elif instruction_type == InstructionType.STOP_RECORDING.value:
                        record_video = RecordState.STOP_RECORDING
                    elif instruction_type == InstructionType.START_FLIGHT.value:
                        phone_state = PhoneState.PILOTING
                        # send the pi to start streaming
                        pass
                    elif instruction_type == InstructionType.END_FLIGHT.value:
                        phone_state = PhoneState.STARTED
                        # send the pi to stop streaming
                        pass
                    elif instruction_type == InstructionType.GET_FLIGHTS.value:
                        phone_state = PhoneState.BROWSING_FLIGHTS
                        pass
                    elif instruction_type == InstructionType.START_PREVIOUS_FLIGHT.value:
                        phone_state = PhoneState.AUTOPILOT
                        # send the pi to start streaming
                        # start sending previous instructions
                        pass
                    elif instruction_type == InstructionType.GET_VIDEOS.value:
                        phone_state = PhoneState.BROWSING_VIDEOS
                        video_list_json = json.dumps(get_video_list()).encode('utf-8')
                        json_length = len(video_list_json)
                        print(json_length)
                        phoneSocket.sendall(struct.pack('>I', json_length))
                        phoneSocket.sendall(video_list_json)
                        print("Finished Sending Video List")
                    # sets up the cv2 and video and frame counter
                    elif instruction_type == InstructionType.DOWNLOAD_VIDEO.value:
                        pass
                        try:
                            video_name = instruction_data.get("video_name")
                            cap = cv2.VideoCapture(f"videos/{video_name}")
                            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            # Send video metadata
                            frame_count_bytes = struct.pack('>I', frame_count)
                            print(f"Sending frame count: {frame_count}")
                            phoneSocket.sendall(frame_count_bytes)
                            phone_state = PhoneState.DOWNLOADING_VIDEO
                            print("Start sending video")
                        except Exception as e:
                            cap.release()
                            cv2.destroyAllWindows()
                    elif instruction_type == InstructionType.GET_STATUS.value:
                        pass
                    elif instruction_type == InstructionType.BACK.value:
                        pass
                    elif instruction_type == InstructionType.JOYSTICK.value:
                        tmp=command_dict["type"]
                        command_dict=instruction_data
                        command_dict["type"]=tmp
                        flag_pass_commands=True
                    else:
                        print("Bad")

                except json.JSONDecodeError:
                    print("Received invalid JSON data")
            if flag_pass_commands:
                send_event.set()
        except Exception as e:
            flag = False
            print(f"Phone connection lost in handleControls: {e}")
            break




# Function to handle client connections
def handle_client_connection(client_socket):
    """
        Handles incoming client connections and directs them to the appropriate handler.
    """
    global connections
    trying=True
    while True:
        try:
            message = client_socket.recv(1024).decode()
            client_socket.settimeout(TIMEOUT)
            match message:
                case "drone":
                    connections["drone"] = client_socket
                    handleDroneMessages(client_socket)
                    trying = False
                case "phone":
                    connections["phone"] = client_socket
                    client_socket.sendall("0\n".encode())  # everything ok
                    handleControls(client_socket)
                    trying = False

                case _:
                    print(f"Received message: {message}")
                    client_socket.sendall("-1\n".encode())
                    break


        except Exception as e:
            print(f"Connection failed to establish: {e}")
            break
    client_socket.close()


# Function to start the TCP server
def start_tcp_server(server_ip, server_port):
    """
        Starts the TCP server to listen for incoming connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"TCP Server started on {server_ip}:{server_port}")

    while not stop_event.is_set():
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    server_ip = "0.0.0.0"
    if internal:
        server_ip = "192.168.1.17"
        print(f"IP for external connections: {getExternalIp()}:{server_port}")
    else:
        print(f"IP for external connections: {getExternalIp()}:{server_port}")

    # Start the TCP server in a separate thread
    tcp_server_thread = threading.Thread(target=start_tcp_server, args=(server_ip, server_port))
    tcp_server_thread.start()

    send_frames_thread = threading.Thread(target=send_frames, args=())
    send_frames_thread.start()

    control_send_thread = threading.Thread(target=send_controls)
    control_send_thread.start()

    if not internal:
        monitor_ip_thread = threading.Thread(target=monitorIP)
        monitor_ip_thread.start()

    tcp_server_thread.join()
