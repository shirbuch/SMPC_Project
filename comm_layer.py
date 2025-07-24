import socket
import pickle
import threading
import signal
import ssl
import sys
import os
from typing import Any, Optional
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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(pickle.dumps(data))

    def start_server(self):
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
        thread = threading.Thread(target=self.start_server, daemon=True)
        thread.start()

    def stop_listener(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', self.port))
                s.close()
        except Exception as e:
            print(f"[{self.name}] Error stopping listener: {e}")

    @abstractmethod
    def handle_incoming(self, data: dict):
        pass


class SecureBaseServer(BaseServer):
    def __init__(self, host: str, port: int, name: str, cert_path=None, key_path=None, ca_path="certs/ca_cert.pem"):
        super().__init__(host, port, name)
        self.cert_path = cert_path or f"certs/{name}_cert.pem"
        self.key_path = key_path or f"certs/{name}_key.pem"
        self.ca_path = ca_path

        if not all(os.path.exists(p) for p in [self.cert_path, self.key_path, self.ca_path]):
            raise FileNotFoundError(f"[{self.name}] Missing TLS cert/key/ca files. Expected:\n"
                                    f"  {self.cert_path}\n  {self.key_path}\n  {self.ca_path}")

    def send_data(self, host: str, port: int, data: Any) -> None:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.ca_path)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                ssock.sendall(pickle.dumps(data))

    def start_server(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        context.load_verify_locations(self.ca_path)

        try:
            bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            bindsocket.bind((self.host, self.port))
            bindsocket.listen()
            bindsocket.settimeout(1.0)
            self.server_socket = bindsocket
            print(f"[{self.name}] Listening on {self.host}:{self.port} with TLS")

            while not self.shutdown_flag.is_set():
                try:
                    conn, _ = bindsocket.accept()
                    try:
                        conn = context.wrap_socket(conn, server_side=True)
                    except ssl.SSLError as e:
                        print(f"[{self.name}] TLS handshake failed: {e}")
                        conn.close()
                        continue
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
