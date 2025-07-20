import sys
from typing import List
from party import Party, Share
from comm_layer import BaseServer


class PartyServer(BaseServer, Party):
    """Party server that inherits from both BaseServer and Party"""
    
    def __init__(self, party_id: int, controller_host: str = 'localhost', controller_port: int = 9000):
        host = '0.0.0.0'
        port = 8000 + party_id
        
        # Initialize both parent classes
        BaseServer.__init__(self, host, port, f"Party_{Party.id_to_letter(party_id)}")
        Party.__init__(self, party_id)
        
        self.controller_host = controller_host
        self.controller_port = controller_port
    
    def handle_incoming(self, data: dict):
        action = data.get('action')
        print(f"[{self.get_name()}] Received action '{action}'")

        if action == 'compute_sum':
            try:
                shares, prime = self.unpack_compute_sum_request(data)
                
                print(f"[{self.get_name()}] Received {len(shares)} shares:")
                for share in shares:
                    print(f"   {share}")

                local_sum = self.compute_sum(shares, prime)
                print(f"[{self.get_name()}] Computed local sum: {Share.short(local_sum)}")

                self.send_data(self.controller_host, self.controller_port, {
                    'party_id': self.id,
                    'sum': local_sum
                })
                print(f"[{self.get_name()}] Sent result back to controller.")
                
            except ValueError as e:
                print(f"[{self.get_name()}] Error: {e}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python party_server.py <party_id>")
        sys.exit(1)
    
    party_id = int(sys.argv[1])
    server = PartyServer(party_id)
    server.start_server()


if __name__ == '__main__':
    main()
