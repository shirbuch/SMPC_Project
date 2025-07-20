# comm_layer.py
import socket
import pickle
from typing import Any, Callable

BUFFER_SIZE = 4096

def send_data(host: str, port: int, data: Any) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(pickle.dumps(data))

def receive_data(host: str, port: int, handler_fn: Callable[[Any], None]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[COMM] Listening on {host}:{port}...")
        while True:
            conn, _ = s.accept()
            with conn:
                data = b""
                while True:
                    packet = conn.recv(BUFFER_SIZE)
                    if not packet:
                        break
                    data += packet
                try:
                    obj = pickle.loads(data)
                    handler_fn(obj)
                except Exception as e:
                    print(f"[COMM] Error handling data: {e}")
