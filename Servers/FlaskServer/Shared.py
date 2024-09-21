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
    START_RECORDING_VIDEO = 2
    STOP_RECORDING_VIDEO = 3
    START_RECORDING_MACRO = 4
    STOP_RECORDING_MACRO = 5
    GET_MACROS = 6
    START_MACRO = 7
    GET_VIDEOS = 8  # start the video download and request video using inedex
    DOWNLOAD_VIDEO = 9
    TURN_ON = 10
    JOYSTICK = 11
    GET_LINK = 12
    TURN_OFF = 13
    GET_STATUS = 14  # da proveri stanje jer neke instrukcije mozda nisu prosle npr pocni snimanje
    BACK = 15  # povratak iz browsinga videa/letova?


# Constants
MAX_QUEUE_SIZE = 200
TIMEOUT = 10
QUEUE_TIMEOUT = 5

# Directoriums
video_dir = "videos"
script_dir = "flight_scripts"


# Flag to determine if the server is internal or external
internal = False

# Interval to update the IP address on GitHub (in seconds)
ip_update_interval = 60 * 10

stop_event = threading.Event()


def changeServerIP(newIP, path):
    """
        Updates the server IP address stored in a GitHub repository.
    """

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    try:
        file = repo.get_contents(path, ref=BRANCH_NAME)
    except Exception as e:
        if "404" in str(e):
            repo.create_file(FILE_PATH, f'Created file with current IP: {newIP}', newIP,
                             branch=BRANCH_NAME)
            return
        else:
            print(f"An error occurred: {e}")
            return

    currentIP = file.decoded_content.decode()
    if currentIP == newIP:
        print("changeServerIP - Server IP didn't change")
        return

    repo.update_file(file.path, f'Updated server_ip.txt with new IP: {newIP}', newIP, file.sha,
                     branch=BRANCH_NAME)
    print(f"Updated {path} IP")


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
        ipAddr = getExternalIp()
        newIP = ipAddr + ":" + str(server_port)
        newDownloadIp = ipAddr + ":" + str(download_server_port)

        changeServerIP(newIP, FILE_PATH)
        changeServerIP(newDownloadIp, DOWNLOAD_FILE_PATH)

        time.sleep(ip_update_interval)
