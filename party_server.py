# party_server.py
import sys
import socket
import pickle
import signal
import threading
from smpc_system import Party, Share
from smpc_crypto import SMPCCrypto
from comm_layer import send_data

party_id = int(sys.argv[1])
host = '0.0.0.0'
port = 8000 + party_id
controller_host = 'localhost'
controller_port = 9000
BUFFER_SIZE = 4096

# Initialize party and crypto system
party = Party(id=party_id, name=f"Party_{party_id}")
crypto = SMPCCrypto()
shutdown_flag = threading.Event()
server_socket = None  # Will hold the main socket

def _short(val: int) -> str:
    s = str(val)
    return s[:5] + "..." if len(s) > 5 else s

def handle_incoming(data):
    action = data.get('action')
    comp_id = data.get('computation_id')
    print(f"[{party.name}] Received action '{action}' for computation '{comp_id}'")

    if action == 'store_shares':
        received = [Share(name=n, value=v, party_id=party_id) for n, v in data['shares']]
        party.receive_shares(comp_id, received)
        for share in received:
            print(f"   Stored: {share}")

    elif action == 'compute_sum':
        party.compute_and_store_local_sum(comp_id, crypto.get_prime())
        share = party.local_sum_shares[comp_id]
        print(f"[{party.name}] Local sum: {share}")
        send_data(controller_host, controller_port, {
            'party_id': party_id,
            'computation_id': comp_id,
            'sum': share.value
        })
        print(f"[{party.name}] Sent result back to controller.")

def signal_handler(sig, frame):
    print(f"\n[{party.name}] Caught Ctrl+C. Shutting down...")
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

        print(f"[{party.name}] Listening on {host}:{port}...")

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
                    obj = pickle.loads(data)
                    handle_incoming(obj)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[{party.name}] Error: {e}")
                continue

    finally:
        print(f"[{party.name}] Clean shutdown.")
        if server_socket:
            server_socket.close()

if __name__ == '__main__':
    main()
