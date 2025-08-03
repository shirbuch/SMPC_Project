##############################################
#####       Crypto configurations        #####
##############################################

# Prime for finite field operations used as the configuration
PRIME = 9512877328449817248258228130152522619816140017822452000805054231448967888346523667624163391241464483184662919134703814711465525446147934530009615013560291

# Default parameters for the SMPC protocol for testing and simple operation
NUM_PARTIES = 3  # Default number of parties in the SMPC protocol
NUM_SHARES = NUM_PARTIES  # Default number of shares to create for each secret
THRESHOLD = NUM_SHARES - 1  # Default threshold for reconstruction

SECRETS = [100, 200, 300]  # Example secrets to be shared

# Generate a toy secret for testing and simple operation
import random

SECRET_MIN = 0
SECRET_MAX = 500
SECRET_STEP = 50

def generate_toy_secret() -> int:
    """
    Generate a random secret between SECRET_MIN and SECRET_MAX,
    constrained to be a multiple of SECRET_STEP (e.g., 0, 50, 100, ..., 500).

    Returns:
        int: A randomly chosen secret value.
    """
    choices = list(range(SECRET_MIN, SECRET_MAX + 1, SECRET_STEP))
    return random.choice(choices)


##############################################
#####        Network configurations      #####
##############################################

INTERVAL = 1  # Default interval for periodic tasks in seconds

HOST = '0.0.0.0'
BASE_POST = 8000

def get_party_port(party_id: int) -> int:
    """
    Calculate the port number for a given party ID.

    Args:
        party_id (int): Unique identifier for the party (1-indexed).

    Returns:
        int: Port number for the party.
    """
    return BASE_POST + party_id

