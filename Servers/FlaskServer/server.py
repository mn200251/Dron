
import base64
import json
import queue
import struct
import threading
import cv2
import numpy as np
import multiprocessing as mp


from Shared import *

#video streaming
video_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

#video download
video_writer_proc = None
video_frame_queue = None

#command streaming
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
isPoweredOn = False
phone_state = PhoneState.PILOTING
record_video = RecordState.NOT_RECORDING

# Events
send_event = threading.Event()

# For video download
lock = threading.Lock()
response = None

#Video listing
video_list = []

# Instruction_recording
isRecordingMacro = False
start_time = None
previous_time = None
instructions = []

# Autopilot
isAutopilotAcive = False

# FUNCTIONS

def save_instructions_to_file():
    global instructions, start_time
    # Create a unique filename with the datetime
    filename = f"{script_dir}/script_{time.strftime('%Y%m%d_%H%M%S')}.json"

    # Save instructions to the file
    with open(filename, 'w') as f:
        json.dump({
            "start_time": start_time,
            "instructions": instructions
        }, f, indent=4)

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
            #print(len(jpeg_bytes))
            phone_socket.sendall(struct.pack('>I', len(jpeg_bytes)))
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

            video_writer.write(frame)

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
    global record_video, phone_state, video_writer_proc, video_frame_queue
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
                #print("size "+str(size))
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
                if record_video == RecordState.START_RECORDING:

                    print("Start recording")
                    if video_writer_proc is None or not video_writer_proc.is_alive():
                        video_frame_queue = mp.Queue(maxsize=10)
                        frame_width, frame_height = source.shape[1], source.shape[0]
                        fps = 30  # Frames per second
                        output_file = f'videos/recording_{int(time.time() * 1000)}.mp4'
                        video_writer_proc = mp.Process(target=video_writer_process, args=(
                        video_frame_queue, (frame_width, frame_height), fps, output_file))
                        video_writer_proc.start()
                        record_video = RecordState.RECORDING

                if record_video == RecordState.RECORDING:
                    video_frame_queue.put(source)

                if record_video == RecordState.STOP_RECORDING:
                    print("End recording")
                    if video_writer_proc is not None and video_frame_queue is not None:
                        video_frame_queue.put(None)  # Stop the writer process
                        # we will not block and just hope that it finishes
                        #video_writer_proc.join()
                        video_writer_proc = None
                    record_video = RecordState.NOT_RECORDING

                #cv2.imshow("Stream", source)

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
                    "type": InstructionType.RECORD_JOYSTICK,
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
            print(f"Drone not connected")
        except Exception as e:
            print(f"Failed to send data from send_controls: {e}")

            continue



# drone
def handleControls(phoneSocket):
    """
       Handles control messages from the phone and forwards them to the queue.
    """
    global send_event, isAutopilotAcive
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
                    print(instruction_data)
                    # cancel autopilot and switch back to manual mode
                    if isAutopilotAcive and instruction_type != InstructionType.HEARTBEAT.value:
                        isAutopilotAcive = False
                    # handle manual instructions
                    if not isAutopilotAcive:
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
    global record_video, start_time, previous_time, isRecordingMacro, instructions, response, phone_state, command_dict
    instruction_type = instruction_data.get("type")
    flag_pass_commands=False
    if instruction_type is None:
        print("Invalid instruction")
    elif instruction_type == InstructionType.HEARTBEAT.value:
        pass
    # elif instruction_type == InstructionType.START_RECORDING.value:
    #     record_video = RecordState.START_RECORDING
    #     if recording:
    #         start_instruction = {
    #             "type": instruction_type,
    #             "delta_time": time.time() - previous_time
    #         }
    #         instructions.append(start_instruction)
    # elif instruction_type == InstructionType.STOP_RECORDING.value:
    #     record_video = RecordState.STOP_RECORDING
    #     if recording:
    #         stop_instruction = {
    #             "type": instruction_type,
    #             "delta_time": time.time() - previous_time
    #         }
    #         instructions.append(stop_instruction)
    elif instruction_type == InstructionType.START_PREVIOUS_FLIGHT.value:
        autopilot_thread = threading.Thread(target=handleAutopilot, args=(instruction_data['file'],))
        autopilot_thread.start()
    elif instruction_type == InstructionType.JOYSTICK.value:
        tmp = command_dict["type"]
        command_dict = instruction_data
        command_dict["type"] = tmp
        flag_pass_commands = True
    elif instruction_type == InstructionType.RECORD_INST_START.value:
        start_time = time.time()
        previous_time = start_time
        isRecordingMacro = True
    elif instruction_type == InstructionType.RECORD_INST_STOP.value:
        isRecordingMacro = False
        save_instructions_to_file()
        previous_time = None
        start_time = None
        instructions = []
    # else:
    #     print("Bad")
    return flag_pass_commands

def handleAutopilot(instruction_file):
    """
    Autopilot to replay a previous flight from file.
    Saved instructions should not allow for instructions that can fail,
    so a try catch or retry is not needed

    :param instruction_file:
    :return:
    """
    global isAutopilotAcive, previous_time, send_event

    isAutopilotAcive = True
    with open(instruction_file, 'r') as f:
        data = json.load(f)
        instructions_list = data['instructions']

    for instruction in instructions_list:
        if not isAutopilotAcive:
            break

        flag, flag_pass_command= process_instruction(instruction)
        if flag_pass_command:
            send_event.set()
        time.sleep(instruction["delta_time"])
    isAutopilotAcive = False


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
                    connections["drone"] = client_socket
                    handleDroneMessages(client_socket)
                case "phone":
                    connections["phone"] = client_socket
                    client_socket.sendall("0\n".encode())  # everything ok
                    sendDroneStatus(client_socket)
                    handleControls(client_socket)
                case _:
                    print(f"Received message: {message}")
                    client_socket.sendall("-1\n".encode())
                    break
            break
        except Exception as e:
            print(f"Connection failed to establish: {e}")
            break
    client_socket.close()



def sendDroneStatus(socket):
    """
        Sends critical drone booleans to phone client:
        1. If drone is powered on
        2. If recording is active
        3. If macro replay is active
    """
    isPoweredOnByte = b'\x01' if isPoweredOn else b'\x00'
    socket.sendall(isPoweredOnByte)

    isRecordingVideoByte = b'\x01' if (record_video == RecordState.RECORDING
                                       or record_video == RecordState.START_RECORDING) else b'\x00'
    socket.sendall(isRecordingVideoByte)

    isRecordingMacroByte = b'\x01' if isRecordingMacro else b'\x00'
    socket.sendall(isRecordingMacroByte)





