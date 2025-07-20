import socket
import pickle
import threading
import signal
import sys
from typing import Any, Callable, Optional, Tuple, Dict
from abc import ABC, abstractmethod

BUFFER_SIZE = 4096

class BaseServer(ABC):
    """Base class for TCP servers with common functionality"""
    
    def __init__(self, host: str, port: int, name: str):
        self.host = host
        self.port = port
        self.name = name
        self.shutdown_flag = threading.Event()
        self.server_socket: Optional[socket.socket] = None
        self.setup_signal_handler()

    def setup_signal_handler(self):
        """Setup signal handler for clean shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C signal"""
        print(f"\n[{self.name}] Caught Ctrl+C. Shutting down...")
        self.shutdown_flag.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        sys.exit(0)
    
    def send_data(self, host: str, port: int, data: Any) -> None:
        """Send data to another node"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(pickle.dumps(data))
    
    def start_server(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.server_socket.settimeout(1.0)

            print(f"[{self.name}] Listening on {self.host}:{self.port}...")

            while not self.shutdown_flag.is_set():
                try:
                    conn, _ = self.server_socket.accept()
                    with conn:
                        data = b""
                        while True:
                            chunk = conn.recv(BUFFER_SIZE)
                            if not chunk:
                                break
                            data += chunk
                        try:
                            obj = pickle.loads(data)
                            self.handle_incoming(obj)
                        except Exception as e:
                            print(f"[{self.name}] Failed to process data: {e}")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[{self.name}] Server error: {e}")
                    continue

        finally:
            print(f"[{self.name}] Clean shutdown.")
            if self.server_socket:
                self.server_socket.close()
    
    @abstractmethod
    def handle_incoming(self, data: dict):
        """Handle incoming data - to be implemented by subclasses"""
        pass


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
