import pickle
import sys
import time
from typing import Any, Dict, List, Optional
import os

import smpc_crypto
from shared_config import INTERVAL, PRIME, NUM_SHARES, THRESHOLD, generate_toy_secret
from enum import Enum


class Share:
    """
    Represents a single share of a secret, sent from one party to another.

    Attributes:
        x (int): The x-coordinate of the share (typically associated with the receiving party's id).
        y (int): The y-coordinate (the actual share value).
        prime (int): The prime modulus used in the finite field.
        origin_party_id (int): The ID of the party that originally generated this share.
        name (str): A descriptive name in the format "A_1", "B_2", etc., where the letter corresponds to the origin party.
    """
    x: int
    y: int
    prime: int
    origin_party_id: int
    name: str  # e.g. "A_1", "B_2"

    def __init__(self, x: int, y: int, prime: int, origin_party_id: int, name: Optional[str] = None):
        """
        Initialize a Share instance.

        Args:
            x (int): The x-coordinate of the share, typically indicating the receiving party.
            y (int): The y-coordinate, representing the share value.
            prime (int): The prime modulus used for modular arithmetic.
            origin_party_id (int): The ID of the party that created this share.
        """
        self.x = x
        self.y = y
        self.prime = prime
        self.name = name if name else f"{Party.id_to_letter(origin_party_id)}_{x}"

    def __str__(self) -> str:
        """
        Return a display-friendly representation of the share.

        Returns:
            str: Formatted name and shortened value.
        """
        return f"{self.name}: {Share.short(self.y)}"

    @staticmethod
    def validate_prime_and_x(share: 'Share', valid_prime: int, valid_x: int) -> None:
        """
        Validate that the share has correct prime and x values.

        Args:
            share (Share): The share to be validated.
            valid_prime (int): The expected prime value.
            valid_x (int): The expected x-coordinate value.

        Raises:
            ValueError: If the prime of the incoming share does not match the wanted.
            ValueError: If the x-coordinate of the incoming share differs from the wanted.        
        """
        if share.prime != valid_prime:
            raise ValueError(
                f"Prime mismatch: incoming share uses prime {share.prime}, "
                f"but supposed to use prime {valid_prime}"
            )
        
        if share.x != valid_x:
            raise ValueError(
                f"X-coordinate mismatch: incoming share has x-coordinate {share.x}, "
                f"but supposed to have x-coordinate {valid_x}"
            )
       
    @staticmethod
    def short(val: int) -> str:
        """
        Return a truncated string representation of a value.

        Args:
            val (int): Value to be shortened.

        Returns:
            str: First 5 digits followed by ellipsis if long, else raw string.
        """
        s = str(val)
        return s[:5] + "..." if len(s) > 5 else s


class Action(str, Enum):
    RECEIVE_SHARE = "receive_share"
    RECEIVE_RESULT = "receive_result"


class Communicator:
    """
    Class for handling communication between parties.

    Attributes:
        owner_party_id (int): ID of the current party.
        _inbox_filename (str): Name of the file to store incoming shares when running locally.
    """
    owner_party_id: int
    _inbox_filename: str
 
    def __init__(self, party_id: int):
        self.owner_party_id = party_id
        self._inbox_filename = Communicator.get_inbox_filename(party_id)
        self.clear_state()

    def clear_state(self) -> None:
        """
        Clear the communication state.
        """
        if os.path.exists(self._inbox_filename):
            os.remove(self._inbox_filename)
    
    def read_message(self) -> Optional[Any]:
        """
        Read the first message from inbox, keeping the rest in order.
        """
        filename = self._inbox_filename

        if not os.path.exists(filename):
            return None

        messages = []

        # Read all messages
        with open(filename, "rb") as f:
            while True:
                try:
                    messages.append(pickle.load(f))
                except EOFError:
                    break

        if not messages:
            return None

        # Save remaining back
        with open(filename, "wb") as f:
            for msg in messages[1:]:
                pickle.dump(msg, f)

        return messages[0]

    @staticmethod
    def build_action_message(action: str, share: Share) -> dict:
        return {'action': action, 'share': share}

    @staticmethod
    def send_message(dest_party_id: int, message: dict) -> None:
        """
        Simulate sending a message by appending it to a file, using using pickled message format (the same format as future TCP messages).

        Args:
            party_id (int): ID of the party to send the action to.
            message (dict): message to be sent, typically containing 'action' and other payload.
        """        
        with open(Communicator.get_inbox_filename(dest_party_id), "ab") as f:
            f.write(pickle.dumps(message))

    @staticmethod
    def get_inbox_filename(party_id: int) -> str:
        """
        Generate a filename for the party's inbox based on its ID.

        Args:
            party_id (int): Unique identifier for the party (1-indexed).

        Returns:
            str: Filename for the party's inbox.
        """
        return f"share_inbox_{party_id}.pkl"


class ComputationState:
    """
    Class for storing computation state.

    Attributes:
        owner_party_id (int): The ID of the party that owns this computation state.
        _secret (Optional[int]): The secret to be shared by this party.
        _threshold (Optional[int]): Minimum number of shares required to reconstruct the secret.
        _num_shares (Optional[int]): Total number of shares to create.
        _prime (Optional[int]): Prime modulus for finite field operations.
        _secret_shares (List[Share]): Shares created by this party.
        _gathered_shares (List[Share]): Shares received from self and other parties, validated matching x and prime.
        _local_result (Optional[Share]): Result share computed by this party.
        _gathered_results (List[Share]): Result Shares received from self and other parties, validated matching x and prime.
    """
    owner_party_id: int
    _secret: Optional[int] = None
    
    threshold: Optional[int] = None
    num_shares: Optional[int] = None
    prime: Optional[int] = None
    
    _secret_shares: List[Share] = []
    _gathered_shares: List[Share] = []
    _local_result: Optional[Share] = None
    _gathered_results: List[Share] = []

    ### Initialization and clearing
    def __init__(self, owner_party_id: int):
        self.owner_party_id = owner_party_id
        self.clear_state()

    def set_state(self, secret: int, threshold: int, num_shares: int, prime: int):
        """
        Set the computation state.

        Args:
            secret (int): The secret to be shared by this party.
            threshold (int): Minimum number of shares required to reconstruct the secret.
            num_shares (int): Total number of shares to create.
            prime (int): Prime modulus for finite field operations.
        
        Raises:
            ValueError: If the computation state is not empty.
        """
        if not self.is_empty():
            raise ValueError("Computation state is not empty.")
        
        self._secret = secret
        self.threshold = threshold
        self.num_shares = num_shares
        self.prime = prime

    def clear_state(self) -> None:
        """
        Reset the computation state, clearing secret, shares, ...
        """
        self._secret = None
        self.threshold = None
        self.num_shares = None
        self.prime = None

        self._secret_shares.clear()
        self._gathered_shares.clear()
        self._local_result = None
        self._gathered_results.clear()

    ### State checks
    def is_empty(self) -> bool:
        """
        Check if the computation state is empty.

        Returns:
            bool: True if the computation state is empty, False otherwise.
        """
        return (
            self._secret is None
            and self.threshold is None
            and self.num_shares is None
            and self.prime is None
            
            and self._secret_shares == []
            and self._gathered_shares == []
            and self._local_result is None
            and self._gathered_results == []
        )

    def is_set(self) -> bool:
        """
        Check if the computation state is set.

        Returns:
            bool: True if the computation state is set, False otherwise.
        """
        return (
            self._secret is not None
            and self.threshold is not None
            and self.num_shares is not None
            and self.prime is not None
        )

    def is_ready_to_receive_share(self) -> bool:
        """
        Check if the computation state is ready to receive a share.

        Returns:
            bool: True if the computation state is ready to receive a share, False otherwise.
        """        
        return self.is_set()       

    def is_finished_creating_secret_shares(self) -> bool:
        """
        Check if the computation already happened.

        Returns:
            bool: True if no computation happend yet, False otherwise.
        """
        return self.is_set() and (
            self._secret_shares != []
        ) 

    def is_ready_for_create_shares(self) -> bool:
        """
        Check if the computation state is ready for computation.

        Returns:
            bool: True if the computation state is set and ready for computation, False otherwise.
        """
        return self.is_set() and self._secret_shares == []
    
    def is_ready_to_compute(self) -> bool:
        """
        Check if the computation state is ready for computation.

        Returns:
            bool: True if the computation state is set and ready for computation, False otherwise.
        """
        return self.is_set() and not self.is_finished_creating_secret_shares() and self._received_all_shares(self._gathered_shares)
    
    def is_ready_to_reconstruct(self) -> bool:
        """
        Check if the computation state is ready to reconstruct.

        Returns:
            bool: True if the computation state is set and ready to reconstruct, False otherwise.
        """
        return self._local_result is not None and self._received_all_shares(self._gathered_results)
    
    def _received_all_shares(self, shares: List[Share]) -> bool:
        """
        Check if the party has received all shares.

        Args:
            shares (List[Share]): List of received shares.

        Returns:
            bool: True if the party has received all shares, False otherwise.

        Raises:
            ValueError: If the number of shares is not set.
        """
        if self.num_shares is None:
            raise ValueError("Number of shares not set.")
        
        return len(shares) >= self.num_shares

    ### Geters and existance validators
    def get_party_assigned_share_from_list(self, party_id: int, shares: List[Share]) -> Optional[Share]:
        """
        Get the share assigned to the party's ID (x-value) form shares list.

        Returns:
            Share: The share assigned to the party after secret shares were computed. If not exsiting, None.
        
        Raises:
            ValueError: If shares list is None.
        """
        # Check if secret shares are computed
        if not shares:
            raise ValueError(f"Shares list is None.")

        # Find the share that corresponds to the party's ID
        for share in shares:
            if share.x == party_id:
                return share
        
        # If not found
        return None
    
    def validate_and_get_party_assigned_share(self, party_id: int) -> Share:
        """
        Get the share assigned to the party's ID (x-value).

        Returns:
            Share: The share assigned to the party after secret shares were computed.
        
        Raises:
            ValueError: If secret shares not computed yet.
            ValueError: If party-assigned share was not found.
        """
        party_assigned_share = self.get_party_assigned_share_from_list(party_id, self._secret_shares)

        if not party_assigned_share:
            raise ValueError(f"Share of Party {party_id} not found.")
        else:
            return party_assigned_share

    def validate_and_get_local_result(self) -> Share:
        """
        Get the computed result share.

        Returns:
            Share: The result share if computed.

        Raises:
            ValueError: If the local result was not computed yet in the current context.
        """
        if not self._local_result:
            raise ValueError(f"No local result computed.")
        
        return self._local_result

    ### Recievers and share validators
    def receive_share(self, share: Share) -> None:
        """ 
        Add an incoming share to the gathered shares for secure computation.

        This method performs the following validations before accepting the share:
        - Ensures that the share use the same prime modulus for consistent field operations.
        - Verifies that the share correspond to the same x-coordinate (i.e., the same evaluation point).

        Args:
            share (Share): The share to be validated and inserted.

        Raises:
            ValueError: If the prime of the incoming share does not match the existing shares'.
            ValueError: If the x-coordinate of the incoming share differs from existing shares.
        """
        if not self.is_ready_to_receive_share(): # next lines can ignore (optional values) due to this validation
            raise ValueError("Computation state is not ready to recieve share.")
        
        Share.validate_prime_and_x(share, self.prime, self.owner_party_id) # type: ignore

        self._gathered_shares.append(share)

    def receive_result(self, result_share: Share) -> None:
        """ 
        Add an incoming result share to the gathered shares for secure computation.

        This method performs the following validations before accepting the result share:
        - Ensures that the result share use the same prime modulus for consistent field operations.
        - Verifies that the result share correspond to the same x-coordinate (i.e., the same evaluation point).

        Args:
            result_share (Share): The result share to be validated and inserted.

        Raises:
            ValueError: If owner party did not compute the local result.
            ValueError: If the prime of the incoming result share does not match the existing shares'.
            ValueError: If the x-coordinate of the incoming result share differs from existing shares.
        """
        local_result_share = self.validate_and_get_local_result()  # next lines can ignore (optional values) due to this validation

        Share.validate_prime_and_x(result_share, local_result_share.prime, local_result_share.x) # type: ignore

        self._gathered_results.append(result_share)

    ### Computation logic
    def create_secret_shares(self) -> None:
        """
        Create and saves shares for the secret,
        and saves the share corrisponding to owner party (with same x as the party's ID) in _gathered_shares.
        
        Raises:
            ValueError: If the computation state is not ready or owner party does not have an assigned share.
        """
        if not self.is_ready_for_create_shares(): # next lines can ignore (optional values) due to this validation
            raise ValueError("Computation state must be set for computation before creating shares")
        
        raw_shares = smpc_crypto.create_shares(self._secret, self.threshold, self.num_shares, self.prime) # type: ignore
        self._secret_shares = [Share(x, y, self.prime, origin_party_id=self.owner_party_id) for (x, y) in raw_shares] # type: ignore
        
        # Add owner party's share to _gathered_shares
        owner_party_assigned_share = self.validate_and_get_party_assigned_share(self.owner_party_id)
        self._gathered_shares.append(owner_party_assigned_share)

    def compute_sum(self) -> None:
        """
        Compute the modular sum of all y-values in stored shares_to_compute.

        This function aggregates the y-components of the collected shares
        and computes their sum modulo the prime field defined by the first share.

        Returns:
            share: The sum of the stored shares to compute in the party as a Share, modulo the prime.

        Raises:
            ValueError: If not enough shares are available to compute the sum.
        """
        owner_party_assigned_share = self.validate_and_get_party_assigned_share(self.owner_party_id)

        if not self.is_ready_to_compute():
            raise ValueError(f"Not enough shares to compute sum.")

        share_values = [share.y for share in self._gathered_shares]
        sum_value = smpc_crypto.add_shares(share_values, owner_party_assigned_share.prime)

        local_result = Share(x=0, y=sum_value, prime=owner_party_assigned_share.prime, origin_party_id=self.owner_party_id)
        self._local_result = local_result
        self._gathered_results.append(local_result)  # Store the result for reconstruction later
    
    def reconstruct_secret(self) -> int:
        """
        Reconstruct the secret from the _gathered_results.
        
        Returns:
            int: The reconstructed secret value.
        
        Raises:
            ValueError: If not enough result shares are available for reconstruction.
        """
        local_result = self.validate_and_get_local_result()

        if not self._received_all_shares(self._gathered_results):
            raise ValueError(f"Not enough result shares to reconstruct secret.")
         
        result_share_values = [(share.x, share.y) for share in self._gathered_results]
        return smpc_crypto.reconstruct_secret(result_share_values, local_result.prime)


class Party:
    """
    Represents a single participant in a Secure Multi-Party Computation (SMPC) session.

    The Party class acts as the main orchestrator for the SMPC protocol from the perspective
    of one party. It manages the lifecycle of a secure computation round, including:

    - Setting up its local secret and configuration.
    - Creating secret shares using Shamir's Secret Sharing.
    - Sending and receiving shares and result fragments to/from other parties.
    - Computing its local share of the result.
    - Reconstructing the final result once all fragments have been received.

    This class delegates communication and computation responsibilities to:
    - `Communicator`: Handles message I/O (currently via local file simulation).
    - `ComputationState`: Maintains all local computation state and logic.

    Attributes:
        id (int): The unique party ID (1-indexed).
        name (str): A human-readable name for the party (e.g., "Party_A").
        _communicator (Communicator): Responsible for message transmission and reception.
        _computation_state (ComputationState): Maintains computation-specific data and logic.
    """
    id: int
    name: str  # e.g. "Party_A", "Party_B"

    _communicator: Communicator  # Communicator instance for inter-party communication
    _computation_state: ComputationState  # Computation state instance for storing current computation details

    ### Initialization and State Management
    def __init__(self, party_id: int):
        """
        Initialize a Party instance.

        Args:
            party_id (int): Unique identifier for the party (1-indexed).
        """
        self.id = party_id
        self.name = self.id_to_name(self.id)

        self._communicator = Communicator(party_id)
        self._computation_state = ComputationState(party_id)

        self.clear_state()

    def clear_state(self) -> None:
        """
        Reset the party's internal state, clearing computation state and communication state.
        This is useful for resetting the party's state before starting a new computation.
        """
        self._communicator.clear_state()
        self._computation_state.clear_state()

    def set_computation_state(self, secret: int, threshold: int, num_shares: int, prime: int) -> None:
        """
        Reset the previous state and Set the computation state for the party.

        Args:
            secret (int): The secret to be shared by the party.
            threshold (int): Minimum number of shares required to reconstruct the secret.
            num_shares (int): Total number of shares to create.
            prime (int): Prime modulus for finite field operations.
        """
        self._computation_state.set_state(secret, threshold, num_shares, prime)

    def shutdown(self) -> None:
        self.clear_state()

    ### Compitation state wrappers 
    def create_secret_shares(self) -> None:
        self._computation_state.create_secret_shares()

    def compute_sum(self) -> None:
        self._computation_state.compute_sum()

    def reconstruct_secret(self) -> int:
        return self._computation_state.reconstruct_secret()

    ### Send shares and result
    def distribute_secret_shares(self) -> None:
        """
        Distribute shares to other parties.

        This method sends the party's shares to all other parties,
        excluding its own share.
        """
        if not self._computation_state.is_finished_creating_secret_shares(): # next lines can ignore (optional values) due to this validation
            raise ValueError(f"Don't have shares to distribute.")
        
        for party_id in range(1, self._computation_state.num_shares + 1): # type: ignore
            if party_id != self.id:  # Filter out own share, that was already added
                share = self._computation_state.validate_and_get_party_assigned_share(party_id)
                message = Communicator.build_action_message(Action.RECEIVE_SHARE, share)
                print(f"Sending share to {party_id}")
                self._communicator.send_message(party_id, message)

    def distribute_result(self) -> None:
        """
        Distribute result share to other parties.
        This method sends the computed result share to all other parties.
        """
        local_result = self._computation_state.validate_and_get_local_result() # next lines can ignore (optional values) due to this validation

        for party_id in range(1, self._computation_state.num_shares + 1): # type: ignore
            if party_id != self.id:  # Filter out own share, that was already added
                message = Communicator.build_action_message(Action.RECEIVE_RESULT, local_result)
                print(f"Sending result to {party_id}")
                self._communicator.send_message(party_id, message)

    ### Handle incoming
    def _handle_message(self, message: Any) -> None:
        """
        Handle an incoming message by processing its action.

        Args:
            message (Any): The incoming message, expected to be a dictionary with 'action' and other fields.
        """
        action = message.get("action")

        if action == Action.RECEIVE_SHARE:
            self._computation_state.receive_share(message["share"])
        elif action == Action.RECEIVE_RESULT:
            self._computation_state.receive_result(message["share"])
        else:
            raise ValueError(f"[{self.name}] Unknown action '{action}' in message: {message}")

    def _read_message(self) -> None:
        time.sleep(INTERVAL)
        message = self._communicator.read_message()
        if message:
            self._handle_message(message)    
        
    def wait_and_receive_all_secret_shares(self) -> None:
        """
        Wait until the party has received a sufficient number of shares to compute.
        This method blocks until the recieved all shares,
        indicating that all parties have sent their shares.
        """
        while not self._computation_state.is_ready_to_compute():
            self._read_message()

    def wait_and_receive_all_result_shares(self) -> None:
        """
        Wait until the party has received a sufficient number of result shares.
        This method blocks until the recieved all result shares,
        indicating that all parties have sent their result shares.
        """
        while not self._computation_state.is_ready_to_reconstruct():
            self._read_message()

    ### Main Logic
    def run_session(self, secret: int = generate_toy_secret(), threshold: int = THRESHOLD, num_shares: int = NUM_SHARES, prime: int = PRIME) -> None:
        """
        Run the party's operations: set secret, create shares, distribute them, calculate and send the result.
        
        Args:
            secret (int): The secret value to be shared. If None, a random toy secret is generated.
            threshold (int): Minimum number of shares required to reconstruct the secret. If not provided, uses shared_config THRESHOLD.
            num_shares (int): Total number of shares to create. If not provided, uses shared_config NUM_SHARES.
            prime (int): Prime modulus for finite field operations. If not provided, uses shared_config PRIME.
        """
        ### Setup
        self.clear_state()  # Clear previous state

        print()
        print(f"[{self.name}] Session setting up...")
        self.set_computation_state(secret, threshold, num_shares, prime)
        print(f"[{self.name}] Session set.")

        input("Press enter to create secret shares...")

        ### Create secret shares
        print()
        print(f"[{self.name}] Creating secret shares...")
        self.create_secret_shares()
        print(f"[{self.name}] Secret Shares created.")
        
        # todo tcp: Start listening for incoming shares.

        # todo tcp: Wait for a signal that all others are listening.
        
        print()        
        print(f"[{self.name}] Distributing secret shares...")
        self.distribute_secret_shares()
        print(f"[{self.name}] Secret shares distributed.")

        print()
        print(f"[{self.name}] Gathering all secret shares...")
        self.wait_and_receive_all_secret_shares()
        print(f"[{self.name}] Gathered secret shares.")
        
        print()
        self.compute_sum()
        print(f"[{self.name}] Computed sum: {self._computation_state.validate_and_get_local_result()}")

        print()
        print(f"[{self.name}] Distributing result...")
        self.distribute_result()
        print(f"[{self.name}] Result distributed.")

        print()
        print(f"[{self.name}] Gathering all results...")
        self.wait_and_receive_all_result_shares() 
        print(f"[{self.name}] Gathered results.")

        print()
        reconstructed_secret = self.reconstruct_secret()
        print(f"[{self.name}] Reconstructed secret: {reconstructed_secret}")

    @staticmethod
    def id_to_name(party_id: int) -> str:
        """
        Return the human-readable name of the party (e.g., "Party_A").

        Returns:
            str: Name of the party.
        """
        return f"Party_{Party.id_to_letter(party_id)}"

    @staticmethod
    def id_to_letter(id: int) -> str:
        """
        Convert a party ID (1-indexed) to a corresponding uppercase letter.

        Args:
            id (int): Numeric ID starting at 1.

        Returns:
            str: Corresponding uppercase letter (1 -> A).
        """
        return f"{chr(64 + id)}"


def main():
    """
    Entry point to launch a party server from command line.
    Requires a party ID as an argument.
    """
    if len(sys.argv) != 2:
        print("Usage: python party_server.py <party_id>")
        sys.exit(1)
    
    party_id = int(sys.argv[1])
    party = Party(party_id)
    try:
        party.run_session()
    except KeyboardInterrupt:
        print(f"\n[Caught Ctrl+C. Shutting down...")
        party.shutdown()
        sys.exit(0)


if __name__ == '__main__':
    main()
