import base64
import json
import os
import queue
import struct
import threading
import cv2
import numpy as np
import multiprocessing as mp

from Shared import *

# video streaming
video_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
current_frame = None
FRAME_RATE = 30
# FRAME_WIDTH, FRAME_HEIGHT = 1280, 720
FRAME_WIDTH, FRAME_HEIGHT = 1920, 1080

# video download
video_writer_proc = None
video_frame_queue = None

# command streaming
command_dict = {
    "type": InstructionType.JOYSTICK.value,
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "rotation": 0.0
}
control_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
connections = {'drone': None, 'phone': None}

# To remember the states
isPIDOn = True
isPoweredOn = False
phone_state = PhoneState.PILOTING
record_video = RecordState.NOT_RECORDING

# Events
send_event = threading.Event()



# Instruction_recording
macro_name = None
isRecordingMacro = False
start_time = None
previous_time = None
instructions = []

# video recording
video_name = None

# Autopilot
isAutopilotAcive = False
allowed_instructions = [InstructionType.HEARTBEAT.value, InstructionType.START_RECORDING_VIDEO.value,
                        InstructionType.STOP_RECORDING_VIDEO.value]


# FUNCTIONS

def save_instructions_to_file():
    global instructions, start_time
    # Create a unique filename with the datetime
    filename = f"{script_dir}/{macro_name}"

    # Save instructions to the file
    with open(filename, 'w') as f:
        json.dump(instructions, f, indent=4)


# THREADS AND THEIR CREATION
def send_frames():
    """
    Timer-based function that sends the current frame every 1/30th of a second.
    If an error occurs during sending, it retries until the stop_event is set.
    The function ensures that the process is stopped gracefully when the stop_event is triggered.
    """
    global stop_event, current_frame, connections
    cnt = 0

    while not stop_event.is_set():
        try:
            # Wait for the next frame interval (1/30 seconds for 30 FPS)
            time.sleep(1.0 / FRAME_RATE)

            # Check if there is a valid current frame to send
            if current_frame is None:
                continue

            phone_socket = connections["phone"]

            jpeg_bytes = current_frame

            # Send the frame size followed by the actual frame data
            phone_socket.sendall(struct.pack('>I', len(jpeg_bytes)))
            phone_socket.sendall(jpeg_bytes)

            if record_video == RecordState.RECORDING:
                video_frame_queue.put(jpeg_bytes)

            # Print status every 30 frames
            # if cnt % 30 == 0:
            #     print(str(cnt) + " send_frames sent batch" + str(time.time()))
            #
            # cnt += 1

        except socket.error:
            # Handle errors related to sending data over the socket
            print("Socket error occurred in send_frames, retrying...")
            continue
        except AttributeError:
            # Handle case where phone connection is not established
            print(f"Phone not connected")
        except Exception as e:
            # Catch any unexpected errors and log them
            print(f"Unexpected error in send_frames_timer: {e}")
            continue

def video_writer_process(video_frame_queue, frame_size, fps, output_file):
    """Process that handles writing video frames to a file."""
    print("Saving started ")
    try:
        video_writer = None
        while True:
            frame = video_frame_queue.get()
            if frame is None:  # Sentinel value to stop the process
                break
            if video_writer is None:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(output_file, fourcc, fps, frame_size)

            npimg = np.frombuffer(frame, np.uint8)

            if npimg is None:
                print('npimg is none')

            source = cv2.imdecode(npimg, 1)
            video_writer.write(source)

        if video_writer is not None:
            video_writer.release()
            video_frame_queue = None
    except  Exception as e:
        print("Video saving died: " + str(e))


def handleDroneMessages(droneSocket):
    """
    Funkcija je zaduzena da prima poruke od drona.
    Trenutno to podrazumeva u petlji na cekanje na pocetak streama i primanje frejmova i njihovo stavljanje u video_queue.
    Funkcija takodje obuhvata cuvanje videa po potrebi.
    U slucaju prekida konekcije funkcija se zavrsava.
    :param droneSocket:
    :return:
    """
    global record_video, phone_state, video_writer_proc, video_frame_queue, video_name,current_frame
    video_writer = None
    # stream alive
    flag = True
    cnt=0
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
                jpeg_bytes = frame_data
                current_frame = jpeg_bytes

                # npimg = np.frombuffer(frame_data, np.uint8)
                #
                # if npimg is None:
                #     print('npimg is none')
                #
                # source = cv2.imdecode(npimg, 1)
                # cv2.imshow("Stream", source)

                # if cnt % 30 == 0:
                #     print(str(cnt)+" receive_frames got batch" + str(time.time()))
                # cnt += 1
                # Check if recording needs to be started or restarted in new thread because of a disconnected
                if record_video == RecordState.START_RECORDING:
                    print("Start recording")
                    if video_writer_proc is None or not video_writer_proc.is_alive():
                        video_frame_queue = mp.Queue(maxsize=10)

                        output_file = f'videos/{video_name}'
                        video_writer_proc = mp.Process(target=video_writer_process, args=(
                            video_frame_queue, (FRAME_WIDTH, FRAME_HEIGHT), FRAME_RATE, output_file))
                        video_writer_proc.start()
                        record_video = RecordState.RECORDING

                if record_video == RecordState.STOP_RECORDING:
                    print("End recording")
                    if video_writer_proc is not None and video_frame_queue is not None:
                        video_frame_queue.put(None)  # Stop the writer process
                        # we will not block and just hope that it finishes
                        # video_writer_proc.join()
                        video_writer_proc = None
                    record_video = RecordState.NOT_RECORDING

                i = i + 1

            except ConnectionResetError:
                print("ConnectionResetError in handleCameraStream")
                break
            except KeyboardInterrupt:
                print("KeyboardInterrupt in handleCameraStream")
                break
            except Exception as e:
                print('Exception in handleCameraStream ' + str(e))
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
    global stop_event, connections, send_event, command_dict, previous_time

    while not stop_event.is_set():
        send_event.wait()
        send_event.clear()
        try:
            data_to_send = json.dumps(command_dict).encode('utf-8')
            drone_socket = connections["drone"]
            drone_socket.sendall(data_to_send)
            if isRecordingMacro:
                # Calculate delta time
                current_time = time.time()
                delta_time = current_time - previous_time
                previous_time = current_time

                # Create joystick instruction
                joystick_instruction = {
                    "type": InstructionType.JOYSTICK.value,
                    "x": command_dict['x'],
                    "y": command_dict['y'],
                    "z": command_dict['z'],
                    "rotation": command_dict['rotation'],
                    "delta_time": delta_time
                }

                # Append to the instructions list
                instructions.append(joystick_instruction)
            command_dict["type"] = InstructionType.JOYSTICK.value
        except AttributeError as e:
            print(f"Drone not connected: {e}")
        except Exception as e:
            print(f"Failed to send data from send_controls: {e}")

            continue

    print("ZATVORIO")

# drone
def handleControls(phoneSocket):
    """
       Handles control messages from the phone and forwards them to the queue.
    """
    global send_event, isAutopilotAcive, allowed_instructions
    buffer = ""
    flag = True
    while flag:
        try:
            data = phoneSocket.recv(1024).decode('utf-8')

            if not data:
                continue

            buffer += data
            flag_pass_commands = False
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
                    if instruction_type != InstructionType.HEARTBEAT.value:
                        print(instruction_data)
                    # cancel autopilot and switch back to manual mode
                    if isAutopilotAcive and instruction_type not in allowed_instructions:
                        isAutopilotAcive = False

                    if not isAutopilotAcive or instruction_type in allowed_instructions:
                        flag_pass_commands = process_instruction(instruction_data)

                except json.JSONDecodeError:
                    print("Received invalid JSON data")
            if flag_pass_commands:
                send_event.set()
        except Exception as e:
            flag = False
            print(f"Phone connection lost in handleControls: {e}")
            break


def process_instruction(instruction_data):
    global isPoweredOn, isPIDOn, record_video, video_name, start_time, previous_time, macro_name, isRecordingMacro, instructions, response, phone_state, command_dict
    instruction_type = instruction_data.get("type")
    flag_pass_commands = False
    if instruction_type is None:
        print("Invalid instruction")
    elif instruction_type == InstructionType.HEARTBEAT.value:
        pass
    elif instruction_type == InstructionType.START_RECORDING_VIDEO.value:
        record_video = RecordState.START_RECORDING
        video_name = instruction_data.get("name", f'recording_{int(time.time() * 1000)}') + ".mp4"
    elif instruction_type == InstructionType.STOP_RECORDING_VIDEO.value:
        record_video = RecordState.STOP_RECORDING
    elif instruction_type == InstructionType.JOYSTICK.value:
        tmp = command_dict["type"]
        command_dict = instruction_data
        command_dict["type"] = tmp
        flag_pass_commands = True
    elif instruction_type == InstructionType.START_RECORDING_MACRO.value:
        start_time = time.time()
        previous_time = start_time
        macro_name = instruction_data.get("name", f"script_{time.strftime('%Y%m%d_%H%M%S')}") + ".json"
        isRecordingMacro = True
    elif instruction_type == InstructionType.STOP_RECORDING_MACRO.value:
        if not macro_name is None:
            isRecordingMacro = False
            save_instructions_to_file()
            previous_time = None
            start_time = None
            instructions = []
            macro_name = None
    elif instruction_type == InstructionType.TURN_ON.value:
        isPoweredOn=True
        command_dict["type"] = instruction_type
        flag_pass_commands = True
    elif instruction_type == InstructionType.TURN_OFF.value:
        isPoweredOn=False
        command_dict["type"] = instruction_type
        flag_pass_commands = True
    elif instruction_type == InstructionType.START_MACRO.value:
        autopilot_thread = threading.Thread(target=fly_autopilot, args=(instruction_data['name'],))
        autopilot_thread.start()
    elif instruction_type == InstructionType.PID_ON.value:
        isPIDOn=True
        command_dict["type"] = instruction_type
        flag_pass_commands = True
    elif instruction_type == InstructionType.PID_OFF.value:
        isPIDOn=False
        command_dict["type"] = instruction_type
        flag_pass_commands = True
    else:
        print("Unkown instruction in handle controls")
    return flag_pass_commands

def handleAutopilotSetup(client_socket):
    global isAutopilotAcive
    buffer = ""
    flag = True
    while flag:
        try:
            data = client_socket.recv(1024).decode('utf-8')

            if not data:
                continue

            buffer += data
            flag_pass_commands = False
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

                    if instruction_type == InstructionType.GET_MACROS.value:
                        file_list = os.listdir(script_dir)

                        # remove ".json" from the end of the names
                        for i in range(0, len(file_list)):
                            file_list[i] = file_list[i][:-5]

                        json_data = json.dumps(file_list).encode('utf-8')
                        data_length = len(json_data)
                        client_socket.sendall(struct.pack('>I', data_length))

                        # Send the actual JSON data
                        client_socket.sendall(json_data)
                        print(f"Sent {data_length} bytes of JSON data AutopilotSetup.")
                    else:
                        print("Unknown instruction in AutopilotSetup")

                except json.JSONDecodeError:
                    print("Received invalid JSON data")
        except Exception as e:
            flag = False
            print(f"Phone connection lost in handleControls: {e}")
            break


def fly_autopilot(instruction_file):
    """
    Autopilot to replay a previous flight from file.
    Saved instructions should not allow for instructions that can fail,
    so a try catch or retry is not needed

    :param instruction_file:
    :return:
    """
    global isAutopilotAcive, previous_time, send_event
    print("Autopilot started")
    isAutopilotAcive = True
    with open(f"{script_dir}/{instruction_file}.json", 'r') as f:
        instructions_list = json.load(f)

    for instruction in instructions_list:
        if not isAutopilotAcive:
            break

        flag_pass_command = process_instruction(instruction)
        # always sends to drone so if is checking the flag is unneeded
        send_event.set()
        time.sleep(instruction["delta_time"])
    isAutopilotAcive = False
    print("Autopilot finished")


# Function to handle client connections
def handle_client_connection_general(client_socket):
    """
        Handles incoming client connections and directs them to the appropriate handler.
    """
    global connections
    while True:
        try:
            message = client_socket.recv(1024).decode()
            client_socket.settimeout(TIMEOUT)
            match message:
                case "drone":
                    sendDroneStatusToDrone(client_socket)
                    connections["drone"] = client_socket
                    handleDroneMessages(client_socket)
                case "phone":
                    client_socket.sendall("0\n".encode())  # everything ok
                    sendDroneStatus(client_socket)
                    connections["phone"] = client_socket
                    handleControls(client_socket)
                case "macro":
                    connections["macro"] = client_socket
                    handleAutopilotSetup(client_socket)
                case _:
                    print(f"Received message: {message}")
                    client_socket.sendall("-1\n".encode())
                    break
            break
        except Exception as e:
            print(f"Connection failed to establish: {e}")
            break
    # client_socket.close()

def sendDroneStatusToDrone(socket):
    status = {
        "type": InstructionType.GET_STATUS.value,
        "isPoweredOn": isPoweredOn,
        "isPIDOn": isPIDOn
    }
    status_json = json.dumps(status)

    # Send the length of the JSON (as a 4-byte integer)
    json_length = len(status_json)
    socket.sendall(json_length.to_bytes(4, byteorder='big'))

    # Send the actual JSON data
    socket.sendall(status_json.encode('utf-8'))
    print(f"Sent drone status: {status_json}")

def sendDroneStatus(socket):
    """
        Sends critical drone booleans to phone client:
        1. If drone is powered on
        2. If recording is active
        3. If macro replay is active

        :param socket:
        :return:
    """

    isPoweredOnByte = "1\n" if isPoweredOn else "0\n"
    socket.sendall(isPoweredOnByte.encode())

    isRecordingVideoByte = "1\n" if (record_video == RecordState.RECORDING
                                     or record_video == RecordState.START_RECORDING) else "0\n"
    socket.sendall(isRecordingVideoByte.encode())

    isRecordingMacroByte = "1\n" if isRecordingMacro else "0\n"
    socket.sendall(isRecordingMacroByte.encode())
