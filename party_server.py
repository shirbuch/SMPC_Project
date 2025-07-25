"""
Party Server Module

Extends the SMPC Party node with TCP server capabilities for real-time secure computation.
Each party server listens for computation requests from a controller and returns local results.
"""

import sys
from typing import List
from party import Party, Share
from comm_layer import BaseServer


class PartyServer(BaseServer, Party):
    """
    Party server that inherits from both BaseServer (for TCP comms)
    and Party (for local computation logic).

    Listens for 'compute_sum' requests and responds with modular sum.
    """

    def __init__(self, party_id: int, controller_host: str = 'localhost', controller_port: int = 9000):
        """
        Initialize the PartyServer.

        Args:
            party_id (int): Unique party identifier (1-indexed).
            controller_host (str): Hostname of the controller to respond to.
            controller_port (int): Port number of the controller server.
        """
        host = '0.0.0.0'
        port = 8000 + party_id

        Party.__init__(self, party_id)
        BaseServer.__init__(self, host, port, self.get_name())
        
        self.controller_host = controller_host
        self.controller_port = controller_port
    
    def handle_incoming(self, data: dict):
        """
        Handle incoming data from the controller.

        If the action is 'compute_sum', the party:
        - Unpacks the request
        - Computes the sum of its shares mod prime
        - Sends the result back to the controller

        Args:
            data (dict): Incoming payload with action and data fields.
        """
        action = data.get('action')
        print(f"[{self.name}] Received action '{action}'")

        if action == 'compute_sum':
            try:
                shares, prime = self.unpack_compute_sum_request(data)
                
                print(f"[{self.name}] Received {len(shares)} shares:")
                for share in shares:
                    print(f"   {share}")

                local_sum = self.compute_sum(shares, prime)
                print(f"[{self.name}] Computed local sum: {Share.short(local_sum)}")

                self.send_data(self.controller_host, self.controller_port, {
                    'party_id': self.id,
                    'sum': local_sum
                })
                print(f"[{self.name}] Sent result back to controller.")
                
            except ValueError as e:
                print(f"[{self.name}] Error: {e}")


def main():
    """
    Entry point to launch a party server from command line.
    Requires a party ID as an argument.
    """
    if len(sys.argv) != 2:
        print("Usage: python party_server.py <party_id>")
        sys.exit(1)
    
    party_id = int(sys.argv[1])
    server = PartyServer(party_id)
    server.start_server()


if __name__ == '__main__':
    main()
