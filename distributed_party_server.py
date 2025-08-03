#!/usr/bin/env python3
"""
Distributed Party Server for Global SMPC

This server allows SMPC parties to run on different machines across the internet.
Each party runs as an independent HTTP server that can communicate with other
parties via REST API calls.

Features:
- HTTP API for party operations
- Communication between distributed parties
- RESTful endpoints for SMPC protocol phases
- Configuration for global deployment
- Authentication and security
"""

import json
import time
import requests
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
import logging
from urllib.parse import urljoin
import argparse
import os

# Import our SMPC modules
import smpc_crypto as crypto
from party import Share


@dataclass
class PartyConfig:
    """Configuration for a distributed party"""
    party_id: int
    host: str
    port: int
    secret_value: int
    threshold: int
    total_parties: int
    prime: int
    other_parties: List[Dict[str, any]]  # List of other party endpoints


@dataclass
class DistributedShare:
    """Share that can be serialized for network transmission"""
    value: int
    x_coord: int
    secret_owner_id: int
    share_holder_id: int

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class DistributedPartyServer:
    """
    HTTP server for a distributed SMPC party.

    Each party runs as an independent server that can communicate
    with other parties across the internet via HTTP REST API.
    """

    def __init__(self, config: PartyConfig):
        self.config = config
        self.app = Flask(f"SMPC_Party_{config.party_id}")

        # Party state
        self.my_secret_shares: List[DistributedShare] = []
        self.received_shares: Dict[int, DistributedShare] = {}
        self.sum_share: Optional[DistributedShare] = None

        # Protocol state
        self.shares_distributed = False
        self.all_shares_received = False
        self.sum_computed = False

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Party_{config.party_id}")

        # Setup routes
        self._setup_routes()

        self.logger.info(f"Party {config.party_id} initialized on {config.host}:{config.port}")

    def _setup_routes(self):
        """Setup HTTP API routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "party_id": self.config.party_id,
                "timestamp": time.time(),
                "protocol_state": {
                    "shares_distributed": self.shares_distributed,
                    "all_shares_received": self.all_shares_received,
                    "sum_computed": self.sum_computed
                }
            })

        @self.app.route('/api/v1/create_shares', methods=['POST'])
        def create_shares():
            """Create and distribute shares of this party's secret"""
            try:
                self.logger.info("Creating and distributing shares...")

                # Create shares
                raw_shares = crypto.create_shares(
                    self.config.secret_value,
                    self.config.threshold,
                    self.config.total_parties,
                    self.config.prime
                )

                # Convert to distributed shares
                self.my_secret_shares = []
                for x_coord, share_value in raw_shares:
                    share = DistributedShare(
                        value=share_value,
                        x_coord=x_coord,
                        secret_owner_id=self.config.party_id,
                        share_holder_id=x_coord
                    )
                    self.my_secret_shares.append(share)

                # Distribute shares to all parties
                distribution_results = []
                for share in self.my_secret_shares:
                    result = self._send_share_to_party(share)
                    distribution_results.append(result)

                self.shares_distributed = all(distribution_results)

                return jsonify({
                    "success": self.shares_distributed,
                    "message": "Shares created and distributed",
                    "shares_sent": len(self.my_secret_shares)
                })

            except Exception as e:
                self.logger.error(f"Share creation failed: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/v1/receive_share', methods=['POST'])
        def receive_share():
            """Receive a share from another party"""
            try:
                data = request.get_json()
                share_data = data.get('share')

                if not share_data:
                    return jsonify({"success": False, "error": "No share data provided"}), 400

                # Convert to DistributedShare
                share = DistributedShare.from_dict(share_data)

                # Store the share
                self.received_shares[share.secret_owner_id] = share

                self.logger.info(f"Received share from Party {share.secret_owner_id}")

                # Check if we have all shares
                expected_senders = set(range(1, self.config.total_parties + 1))
                received_senders = set(self.received_shares.keys())
                self.all_shares_received = (expected_senders == received_senders)

                return jsonify({
                    "success": True,
                    "message": f"Share received from Party {share.secret_owner_id}",
                    "all_shares_received": self.all_shares_received,
                    "received_from": list(received_senders),
                    "still_waiting_for": list(expected_senders - received_senders)
                })

            except Exception as e:
                self.logger.error(f"Share reception failed: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/v1/compute_sum', methods=['POST'])
        def compute_sum():
            """Compute this party's share of the final sum"""
            try:
                if not self.all_shares_received:
                    return jsonify({
                        "success": False,
                        "error": "Cannot compute sum - missing shares"
                    }), 400

                self.logger.info("Computing sum share...")

                # Sum all share values (homomorphic addition)
                sum_value = 0
                for secret_owner_id, share in self.received_shares.items():
                    sum_value = crypto.add_shares([sum_value, share.value], self.config.prime)

                # Create sum share
                self.sum_share = DistributedShare(
                    value=sum_value,
                    x_coord=self.config.party_id,
                    secret_owner_id=0,  # 0 indicates sum share
                    share_holder_id=self.config.party_id
                )

                self.sum_computed = True

                self.logger.info("Sum share computed successfully")

                return jsonify({
                    "success": True,
                    "message": "Sum share computed",
                    "sum_share": self.sum_share.to_dict()
                })

            except Exception as e:
                self.logger.error(f"Sum computation failed: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/v1/get_sum_share', methods=['GET'])
        def get_sum_share():
            """Get this party's sum share for final reconstruction"""
            try:
                if not self.sum_computed or not self.sum_share:
                    return jsonify({
                        "success": False,
                        "error": "Sum share not ready"
                    }), 400

                return jsonify({
                    "success": True,
                    "sum_share": self.sum_share.to_dict(),
                    "x_coord": self.sum_share.x_coord,
                    "share_value": self.sum_share.value
                })

            except Exception as e:
                self.logger.error(f"Failed to get sum share: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            """Get detailed party status"""
            return jsonify({
                "party_id": self.config.party_id,
                "shares_distributed": self.shares_distributed,
                "shares_received": len(self.received_shares),
                "expected_shares": self.config.total_parties,
                "all_shares_received": self.all_shares_received,
                "sum_computed": self.sum_computed,
                "ready_for_reconstruction": self.sum_computed,
                "received_from_parties": list(self.received_shares.keys())
            })

    # Fix for the self-share bug in distributed_party_server.py

    def _send_share_to_party(self, share: DistributedShare) -> bool:
        """Send a share to the appropriate party with robust error handling"""
        try:
            # Find the target party
            target_party_id = share.share_holder_id

            if target_party_id == self.config.party_id:
                # Send to ourselves (local storage)
                self.received_shares[share.secret_owner_id] = share
                self.logger.info(f"Stored own share locally")

                # CRITICAL FIX: Update the all_shares_received flag
                expected_senders = set(range(1, self.config.total_parties + 1))
                received_senders = set(self.received_shares.keys())
                self.all_shares_received = (expected_senders == received_senders)

                # Log the status update
                if self.all_shares_received:
                    self.logger.info("✅ All shares received!")
                else:
                    missing = expected_senders - received_senders
                    self.logger.info(f"Still waiting for shares from: {list(missing)}")

                return True

            # Rest of the method remains the same...
            target_endpoint = None
            for party_info in self.config.other_parties:
                if party_info['party_id'] == target_party_id:
                    target_endpoint = f"http://{party_info['host']}:{party_info['port']}"
                    break

            if not target_endpoint:
                self.logger.error(f"No endpoint found for Party {target_party_id}")
                return False

            # Send HTTP request with retries
            url = urljoin(target_endpoint, '/api/v1/receive_share')
            payload = {
                "share": share.to_dict(),
                "sender_id": self.config.party_id
            }

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Sending share to Party {target_party_id} at {url} (attempt {attempt + 1})")

                    response = requests.post(
                        url,
                        json=payload,
                        timeout=15,
                        headers={'Content-Type': 'application/json'}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        success = result.get('success', False)
                        if success:
                            self.logger.info(f"✅ Share sent to Party {target_party_id}")
                            return True
                        else:
                            self.logger.error(f"Party {target_party_id} rejected share: {result}")
                            return False
                    else:
                        self.logger.warning(f"HTTP {response.status_code} from Party {target_party_id}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        else:
                            return False

                except requests.exceptions.Timeout:
                    self.logger.warning(f"Timeout sending to Party {target_party_id} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        self.logger.error(
                            f"Timeout sending share to Party {target_party_id} after {max_retries} attempts")
                        return False

                except requests.exceptions.ConnectionError:
                    self.logger.warning(f"Connection error to Party {target_party_id} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        self.logger.error(
                            f"Connection error sending share to Party {target_party_id} after {max_retries} attempts")
                        return False

            return False

        except Exception as e:
            self.logger.error(f"Unexpected error sending share to Party {target_party_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, debug=False):
        """Start the HTTP server"""
        self.logger.info(f"Starting Party {self.config.party_id} server on {self.config.host}:{self.config.port}")
        self.app.run(
            host=self.config.host,
            port=self.config.port,
            debug=debug,
            threaded=True
        )


class DistributedSMPCCoordinator:
    """
    Coordinator for distributed SMPC protocol across multiple servers.

    This class orchestrates the protocol execution by making HTTP calls
    to distributed party servers.
    """

    def __init__(self, party_endpoints: List[Dict], threshold: int, prime: int):
        self.party_endpoints = party_endpoints
        self.threshold = threshold
        self.prime = prime
        self.logger = logging.getLogger("SMPC_Coordinator")

    def run_distributed_protocol(self) -> Tuple[int, bool]:
        """
        Execute the distributed SMPC protocol across multiple servers.

        Returns:
            Tuple[int, bool]: (final_sum, success)
        """
        try:
            self.logger.info("Starting distributed SMPC protocol...")

            # Phase 1: Share Distribution
            if not self._phase1_distribute_shares():
                return 0, False

            # Phase 2: Sum Computation
            if not self._phase2_compute_sums():
                return 0, False

            # Phase 3: Final Reconstruction
            final_sum = self._phase3_reconstruct_sum()
            if final_sum is None:
                return 0, False

            self.logger.info(f"Distributed SMPC completed successfully: {final_sum}")
            return final_sum, True

        except Exception as e:
            self.logger.error(f"Distributed protocol failed: {e}")
            return 0, False

    def _phase1_distribute_shares(self) -> bool:
        """Phase 1: Each party creates and distributes shares"""
        self.logger.info("Phase 1: Distributed share creation and distribution")

        # Trigger share creation on all parties
        results = []
        for party in self.party_endpoints:
            try:
                url = f"http://{party['host']}:{party['port']}/api/v1/create_shares"
                response = requests.post(url, timeout=60)

                if response.status_code == 200:
                    result = response.json()
                    results.append(result.get('success', False))
                    self.logger.info(
                        f"Party {party['party_id']}: Share distribution {'successful' if result.get('success') else 'failed'}")
                else:
                    results.append(False)
                    self.logger.error(f"Party {party['party_id']}: HTTP {response.status_code}")

            except Exception as e:
                self.logger.error(f"Failed to contact Party {party['party_id']}: {e}")
                results.append(False)

        # Wait for share reception to complete
        time.sleep(2)

        # Check if all parties received all shares
        all_ready = self._wait_for_all_shares_received()

        return all(results) and all_ready

    def _phase2_compute_sums(self) -> bool:
        """Phase 2: Each party computes sum shares"""
        self.logger.info("Phase 2: Computing sum shares on all parties")

        results = []
        for party in self.party_endpoints:
            try:
                url = f"http://{party['host']}:{party['port']}/api/v1/compute_sum"
                response = requests.post(url, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    results.append(result.get('success', False))
                    self.logger.info(
                        f"Party {party['party_id']}: Sum computation {'successful' if result.get('success') else 'failed'}")
                else:
                    results.append(False)
                    self.logger.error(f"Party {party['party_id']}: HTTP {response.status_code}")

            except Exception as e:
                self.logger.error(f"Failed to trigger sum computation on Party {party['party_id']}: {e}")
                results.append(False)

        return all(results)

    def _phase3_reconstruct_sum(self) -> Optional[int]:
        """Phase 3: Reconstruct final sum from threshold parties"""
        self.logger.info("Phase 3: Reconstructing final sum")

        # Collect sum shares from threshold parties
        sum_shares = []
        parties_used = []

        for i, party in enumerate(self.party_endpoints[:self.threshold]):
            try:
                url = f"http://{party['host']}:{party['port']}/api/v1/get_sum_share"
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        x_coord = result['x_coord']
                        share_value = result['share_value']
                        sum_shares.append((x_coord, share_value))
                        parties_used.append(party['party_id'])
                        self.logger.info(f"Collected sum share from Party {party['party_id']}")
                    else:
                        self.logger.error(f"Party {party['party_id']}: Sum share not ready")
                        return None
                else:
                    self.logger.error(f"Party {party['party_id']}: HTTP {response.status_code}")
                    return None

            except Exception as e:
                self.logger.error(f"Failed to get sum share from Party {party['party_id']}: {e}")
                return None

        if len(sum_shares) < self.threshold:
            self.logger.error(f"Insufficient sum shares: got {len(sum_shares)}, need {self.threshold}")
            return None

        # Reconstruct final sum
        try:
            final_sum = crypto.reconstruct_secret(sum_shares, self.prime)
            self.logger.info(f"Final sum reconstructed from parties {parties_used}: {final_sum}")
            return final_sum
        except Exception as e:
            self.logger.error(f"Sum reconstruction failed: {e}")
            return None

    def _wait_for_all_shares_received(self, max_wait=30) -> bool:
        """Wait for all parties to receive all shares"""
        self.logger.info("Waiting for all parties to receive all shares...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            all_ready = True

            for party in self.party_endpoints:
                try:
                    url = f"http://{party['host']}:{party['port']}/api/v1/status"
                    response = requests.get(url, timeout=10)

                    if response.status_code == 200:
                        status = response.json()
                        if not status.get('all_shares_received', False):
                            all_ready = False
                            break
                    else:
                        all_ready = False
                        break

                except Exception:
                    all_ready = False
                    break

            if all_ready:
                self.logger.info("All parties have received all shares")
                return True

            time.sleep(1)

        self.logger.warning("Timeout waiting for share reception")
        return False


def create_party_config_from_file(config_file: str) -> PartyConfig:
    """Load party configuration from JSON file"""
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    return PartyConfig(**config_data)


def main():
    """Main entry point for distributed party server"""
    parser = argparse.ArgumentParser(description='Distributed SMPC Party Server')
    parser.add_argument('--config', '-c', required=True, help='Party configuration file (JSON)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')

    args = parser.parse_args()

    # Load configuration
    try:
        config = create_party_config_from_file(args.config)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return 1

    # Create and run party server
    party_server = DistributedPartyServer(config)

    try:
        party_server.run(debug=args.debug)
    except KeyboardInterrupt:
        print(f"\nParty {config.party_id} server stopped")
        return 0
    except Exception as e:
        print(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())