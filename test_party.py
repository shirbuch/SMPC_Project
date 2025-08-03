import unittest
from party import Share, ComputationState, Party
from shared_config import PRIME

class TestShare(unittest.TestCase):

    def test_initialization_and_str(self):
        share = Share(x=1, y=123456, prime=PRIME, origin_party_id=1)
        self.assertEqual(share.x, 1)
        self.assertTrue(str(share).startswith("A_1:"))

    def test_validate_prime_and_x_success(self):
        share = Share(x=2, y=100, prime=PRIME, origin_party_id=1)
        Share.validate_prime_and_x(share, PRIME, 2)

    def test_validate_prime_and_x_failure(self):
        share = Share(x=2, y=100, prime=PRIME + 1, origin_party_id=1)
        with self.assertRaises(ValueError):
            Share.validate_prime_and_x(share, PRIME, 2)

class TestComputationState(unittest.TestCase):

    def setUp(self):
        self.state = ComputationState(owner_party_id=1)

    def test_state_empty_and_set(self):
        self.assertTrue(self.state.is_empty())
        self.state.set_state(secret=123, threshold=2, num_shares=3, prime=PRIME)
        self.assertTrue(self.state.is_set())

    def test_create_and_validate_share(self):
        self.state.set_state(secret=123, threshold=2, num_shares=3, prime=PRIME)
        self.state.create_secret_shares()
        share = self.state.validate_and_get_party_assigned_share(1)
        self.assertEqual(share.x, 1)

class TestParty(unittest.TestCase):

    def test_party_init_and_name(self):
        party = Party(1)
        self.assertEqual(party.name, "Party_A")

if __name__ == "__main__":
    unittest.main()
