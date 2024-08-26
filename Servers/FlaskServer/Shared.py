import socket
import threading
import time
from enum import Enum

import requests
from github import Github

from FlaskServer.serverPrivateData import *


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
    GET_VIDEOS = 8  # start the video download and request video using inedex
    DOWNLOAD_VIDEO = 9
    KILL_SWITCH = 10
    JOYSTICK = 11
    GET_LINK = 12
    TURN_OFF = 13
    GET_STATUS = 14  # da proveri stanje jer neke instrukcije mozda nisu prosle npr pocni snimanje
    BACK = 15  # povratak iz browsinga videa/letova?
    RECORD_INST_START = 16
    RECORD_INST_STOP = 17


# Constants
MAX_QUEUE_SIZE = 200
TIMEOUT = 10
QUEUE_TIMEOUT = 5

# Directoriums
video_dir = "videos"
script_dir = "flight_scripts"

# Server port
server_port = 6969
download_port = 6970

# Flag to determine if the server is internal or external
internal = True

# Interval to update the IP address on GitHub (in seconds)
ip_update_interval = 60 * 10

stop_event = threading.Event()


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
