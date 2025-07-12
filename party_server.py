import sys
import socket
import pickle
import signal
from smpc_crypto import SMPCCrypto

party_id = int(sys.argv[1])
host = '0.0.0.0'
port = 8000 + party_id
controller_host = 'localhost'
controller_port = 9000

party_shares = {}
crypto = SMPCCrypto()
BUFFER_SIZE = 4096

def _short(val: int) -> str:
    s = str(val)
    return s[:5] + "..." if len(s) > 5 else s

print(f"[PARTY {party_id}] Starting server on {host}:{port}")
print(f"[PARTY {party_id}] Prime used: {_short(crypto.get_prime())}")

def send_data(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(pickle.dumps(data))

def handle_incoming(data):
    action = data.get('action')
    comp_id = data.get('computation_id')
    print(f"[PARTY {party_id}] Received action '{action}' for computation '{comp_id}'")

    if action == 'store_shares':
        party_shares[comp_id] = data['shares']
        print(f"[PARTY {party_id}] Stored shares for {comp_id}:")
        for name, value in data['shares']:
            print(f"   Share name: {name}, value: {_short(value)}")

    elif action == 'compute_sum':
        shares = party_shares.get(comp_id, [])
        local_sum = sum(v for _, v in shares) % crypto.get_prime()
        print(f"[PARTY {party_id}] Local sum for {comp_id}: {_short(local_sum)}")
        send_data(controller_host, controller_port, {
            'party_id': party_id,
            'computation_id': comp_id,
            'sum': local_sum
        })
        print(f"[PARTY {party_id}] Sent result back to controller. Shutting down.")
        sys.exit(0)

    elif action == 'clear':
        party_shares.clear()
        print(f"[PARTY {party_id}] Cleared all data")

def main():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            s.settimeout(1.0)
            print(f"[PARTY {party_id}] Listening for incoming connections...")
            while True:
                try:
                    conn, addr = s.accept()
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
    except KeyboardInterrupt:
        print(f"\n[PARTY {party_id}] Shutting down on Ctrl+C")
        sys.exit(0)

if __name__ == '__main__':
    main()
