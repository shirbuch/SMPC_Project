"""
Communication Layer Module for SMPC.

Provides a base TCP server class (`BaseServer`) with capabilities for listening,
handling shutdowns, receiving and sending data using sockets, and delegating
data processing to subclasses via `handle_incoming`.

Used as a foundation for building secure multi-party computation components like
controller and party servers.
"""

import socket
import pickle
import threading
import signal
import sys
from typing import Any, Callable, Optional, Tuple, Dict
from abc import ABC, abstractmethod

BUFFER_SIZE = 4096

class BaseServer(ABC):
    """
    Abstract base class for TCP servers in the SMPC system.

    Provides common functionality such as:
    - Listening for incoming TCP connections
    - Graceful shutdown via signal handling
    - Sending data to remote hosts
    - Receiving and deserializing incoming data
    - Delegating processing to the subclass via `handle_incoming`

    Subclasses must implement:
        - handle_incoming(data: dict): Method to process received data.
    """

    def __init__(self, host: str, port: int, name: str):
        """
        Initialize the server with host, port, and display name.

        Args:
            host (str): The IP address to bind the server socket.
            port (int): The TCP port to listen on.
            name (str): Human-readable name used in logs.
        """
        self.host = host
        self.port = port
        self.name = name
        self.shutdown_flag = threading.Event()
        self.server_socket: Optional[socket.socket] = None
        self.setup_signal_handler()

    def setup_signal_handler(self):
        """
        Setup signal handler for Ctrl+C to allow graceful shutdown.
        """
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        """
        Handle SIGINT (Ctrl+C) signal.

        Args:
            sig: Signal number.
            frame: Current stack frame.
        """
        print(f"\n[{self.name}] Caught Ctrl+C. Shutting down...")
        self.shutdown_flag.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        sys.exit(0)
    
    def send_data(self, host: str, port: int, data: Any) -> None:
        """
        Send serialized data to a given host and port.

        Args:
            host (str): Target host.
            port (int): Target port.
            data (Any): Data object to send (must be pickle-serializable).
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(pickle.dumps(data))

    def start_server(self):
        """
        Start the TCP server and handle incoming connections in a loop.

        Deserializes incoming data and delegates handling to `handle_incoming`.
        The loop terminates on a shutdown event (e.g., Ctrl+C).
        """
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

    def start_listener(self):
        """
        Launch the server in a separate background thread.
        Useful for non-blocking mode in distributed settings.
        """
        thread = threading.Thread(
            target=self.start_server,
            daemon=True
        )
        thread.start()

    def stop_listener(self):
        """
        Trigger shutdown sequence and stop listener thread.
        Connects to the server to break the accept loop.
        """
        try:
            # Attempt to close the socket if it's still open
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 9000))
                s.close()
        except Exception as e:
            print(f"[{self.name}] Error stopping listener: {e}")
        print("[{self.name}] Listener stopped.")
     
    @abstractmethod
    def handle_incoming(self, data: dict):
        """
        Abstract method to handle incoming deserialized data.
        Must be implemented by subclasses.

        Args:
            data (dict): Parsed incoming data payload.
        """
        pass
