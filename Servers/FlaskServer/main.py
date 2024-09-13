import multiprocessing
import threading

from FlaskServer.Shared import *
from FlaskServer.download_server import handle_client_connection_video
from FlaskServer.server import handle_client_connection_general, send_frames, send_controls


# Function to start the TCP server
def start_tcp_server(server_ip, server_port, handler_function):
    """
        Starts the TCP server to listen for incoming connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"TCP Server started on {server_ip}:{server_port}")

    while not stop_event.is_set():
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr} at port {server_port}")
        client_handler = threading.Thread(target=handler_function, args=(client_socket,))
        client_handler.start()



if __name__ == "__main__":
    server_ip = "0.0.0.0"
    if internal:
        server_ip = "192.168.1.17"
        print(f"IP for internal connections: {server_ip}:{server_port}")
        print(f"IP for download internal connections: {server_ip}:{server_port}")
    else:
        print(f"IP for external connections: {getExternalIp()}:{server_port}")

    # Start the TCP server in a separate thread
    tcp_server_thread = threading.Thread(target=start_tcp_server, args=(server_ip, server_port, handle_client_connection_general))
    tcp_server_thread.start()

    tcp_download_process = multiprocessing.Process(target=start_tcp_server,
                                                   args=(server_ip, download_server_port, handle_client_connection_video))
    tcp_download_process.start()

    send_frames_thread = threading.Thread(target=send_frames, args=())
    send_frames_thread.start()

    control_send_thread = threading.Thread(target=send_controls)
    control_send_thread.start()

    if not internal:
        monitor_ip_thread = threading.Thread(target=monitorIP)
        monitor_ip_thread.start()

    tcp_server_thread.join()