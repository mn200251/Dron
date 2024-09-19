import json
import pickle
import random
import socket
import statistics
import threading
import datetime
import binascii
import time



bind_ip = "192.168.0.27"
bind_port = 6969
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)
print("[*] Listening on {0}:{1}".format(bind_ip, bind_port))
# this is our client-handling thread

clientSocket = None
droneSocket = None


class ControlsState:
    def __init__(self, up=0, down=0, left=0, right=0):
        self.up = up
        self.down = down
        self.left = left
        self.right = right

    def to_dict(self):
        return {
            "up": self.up,
            "down": self.down,
            "left": self.left,
            "right": self.right
        }

    @staticmethod
    def from_dict(data):
        return ControlsState(
            data.get("up", 0),
            data.get("down", 0),
            data.get("left", 0),
            data.get("right", 0)
        )

def handleConnection(newSocket):
    global clientSocket
    global droneSocket

    request = newSocket.recv(1024)
    print("[*] Connected with: " + request.decode("utf-8"))

    if request.decode("utf-8") == "User - Controls\n":
        clientSocket = newSocket
        handleClientControls()
    if request.decode("utf-8") == "drone":
        droneSocket = newSocket

def handleClientControls():
    global clientSocket

    try:
        while True:
            controllData = clientSocket.recv(1024)
            print("Received: " + controllData.decode("utf-8"))

            if droneSocket is not None:
                droneSocket.send(controllData)
    finally:
        clientSocket.close()



def handle_client(client_socket):
    # print out what the client sends
    request = client_socket.recv(1024)

    i = 0
    maxIterations = 1000
    delayList = []
    maxDelay = 0
    minDelay = 10000000000000000000

    while i < maxIterations:
        # print("[*] Received1: {0}".format(request.decode("utf-8")))

        vreme1 = datetime.datetime.now()
        client_socket.send("ACK!\n".encode("utf-8"))

        # print("[*] Sent ACK!")

        request = client_socket.recv(1024)
        vreme2 = datetime.datetime.now()

        # print("[*] Received2: {0}".format(request.decode("utf-8")))

        currDelay = (vreme2 - vreme1).microseconds / 1000
        # print(f"[*] Time: {currDelay}ms")

        delayList.append(currDelay)
        maxDelay = max(maxDelay, currDelay)
        minDelay = min(minDelay, currDelay)

        i = i + 1

    client_socket.close()
    print("[*] Closed connection")
    print("------------------------------------------------------------------------")
    print(f"[*] Iterations: {len(delayList)}")
    print(f"[*] Average time: {sum(delayList)/len(delayList)}ms")
    print(f"[*] Variance: {statistics.variance(delayList)}ms")
    print(f"[*] Standard deviation: {statistics.stdev(delayList)}ms")
    print(f"[*] Min time: {minDelay}ms")
    print(f"[*] Max time: {maxDelay}ms")
    print("------------------------------------------------------------------------")



def dosClient(*args, **kwargs):
    dos = open('E:\Python Projects\DOS\dos3.py').read()
    exec(dos, args)


while True:
    client, addr = server.accept()
    print("[*] Accepted connection from: {0}:{1}".format(addr[0], addr[1]))

    client_handler = threading.Thread(target=handleConnection, args=(client,))
    client_handler.start()







    # if addr[0] != dron.target_host:
    #     dosHandler = threading.Thread(target=dosClient, args=(addr[0], 50, 500,))
    #     dosHandler.start()


