import sys
import socket
import pickle
import signal
import threading
from typing import List
from party import Party, Share
from comm_layer import send_data

party_id = int(sys.argv[1])
host = '0.0.0.0'
port = 8000 + party_id
controller_host = 'localhost'
controller_port = 9000
BUFFER_SIZE = 4096

party = Party(party_id)
shutdown_flag = threading.Event()
server_socket = None


def handle_incoming(data: dict):
    action = data.get('action')
    print(f"[{party.get_name()}] Received action '{action}'")

    if action == 'compute_sum':
        raw_shares = data.get('shares', [])
        prime = data.get('prime')
        if not isinstance(prime, int):
            print(f"[{party.get_name()}] Error: Missing or invalid prime field.")
            return

        if not isinstance(raw_shares, list) or not all(isinstance(s, Share) for s in raw_shares):
            print(f"[{party.get_name()}] Error: Invalid share data received.")
            return

        shares: List[Share] = raw_shares
        print(f"[{party.get_name()}] Received {len(shares)} shares:")
        for share in shares:
            print(f"   {share}")

        local_sum = party.compute_sum(shares, prime)
        print(f"[{party.get_name()}] Computed local sum: {Share.short(local_sum)}")

        send_data(controller_host, controller_port, {
            'party_id': party_id,
            'sum': local_sum
        })
        print(f"[{party.get_name()}] Sent result back to controller.")


def signal_handler(sig, frame):
    print(f"\n[{party.get_name()}] Caught Ctrl+C. Shutting down...")
    shutdown_flag.set()
    if server_socket:
        try:
            server_socket.close()
        except Exception:
            pass
    sys.exit(0)


def main():
    global server_socket
    signal.signal(signal.SIGINT, signal_handler)

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        server_socket.settimeout(1.0)

        print(f"[{party.get_name()}] Listening on {host}:{port}...")

        while not shutdown_flag.is_set():
            try:
                conn, _ = server_socket.accept()
                with conn:
                    data = b""
                    while True:
                        chunk = conn.recv(BUFFER_SIZE)
                        if not chunk:
                            break
                        data += chunk
                    try:
                        obj = pickle.loads(data)
                        handle_incoming(obj)
                    except Exception as e:
                        print(f"[{party.get_name()}] Failed to process data: {e}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[{party.get_name()}] Server error: {e}")
                continue

    finally:
        print(f"[{party.get_name()}] Clean shutdown.")
        if server_socket:
            server_socket.close()


if __name__ == '__main__':
    main()
