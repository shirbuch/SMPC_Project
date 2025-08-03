#!/usr/bin/env python3
"""
Distributed SMPC Coordinator

This script coordinates SMPC protocol execution across multiple distributed
party servers running on different machines/servers globally.

Features:
- Orchestrates protocol phases across distributed parties
- Monitors party health and readiness
- Handles network failures and retries
- Provides REST API for protocol management
- Real-time status monitoring
- FIXED: Automatic startup wait to prevent first-run timeouts
"""

import json
import time
import requests
import argparse
import logging
from typing import List, Dict, Optional, Tuple
from flask import Flask, jsonify, request
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import smpc_crypto as crypto
from distributed_party_server import DistributedSMPCCoordinator


def wait_for_servers_ready(party_endpoints: List[Dict], max_wait: int = 30) -> bool:
    """
    Wait for all party servers to be ready before starting protocol.

    This fixes the first-run timeout issue where the coordinator tries to connect
    before the Flask servers have fully started up.

    Args:
        party_endpoints: List of party configurations
        max_wait: Maximum time to wait in seconds

    Returns:
        bool: True if all servers are ready, False if timeout
    """
    print("⏳ Waiting for party servers to be ready...")

    start_time = time.time()
    last_status_report = 0

    while time.time() - start_time < max_wait:
        all_ready = True
        ready_parties = []
        failed_parties = []

        for party in party_endpoints:
            try:
                url = f"http://{party['host']}:{party['port']}/health"
                response = requests.get(url, timeout=3)

                if response.status_code == 200:
                    ready_parties.append(party['party_id'])
                else:
                    all_ready = False
                    failed_parties.append(f"Party {party['party_id']} (HTTP {response.status_code})")

            except requests.exceptions.ConnectionError:
                all_ready = False
                failed_parties.append(f"Party {party['party_id']} (not started)")
            except requests.exceptions.Timeout:
                all_ready = False
                failed_parties.append(f"Party {party['party_id']} (timeout)")
            except Exception as e:
                all_ready = False
                failed_parties.append(f"Party {party['party_id']} (error: {type(e).__name__})")

        if all_ready:
            elapsed = time.time() - start_time
            print(f"✅ All {len(party_endpoints)} parties are ready! (took {elapsed:.1f}s)")
            return True

        # Progress reporting every 3 seconds
        elapsed = time.time() - start_time
        if elapsed - last_status_report >= 3:
            ready_count = len(ready_parties)
            total_count = len(party_endpoints)
            print(f"   📊 {elapsed:.0f}s: {ready_count}/{total_count} parties ready...")

            if failed_parties:
                print(f"   ⏳ Still waiting for: {', '.join(failed_parties[:3])}")
                if len(failed_parties) > 3:
                    print(f"      ... and {len(failed_parties) - 3} more")

            last_status_report = elapsed

        time.sleep(1)  # Check every second

    # Timeout reached
    ready_count = len(ready_parties)
    total_count = len(party_endpoints)
    print(f"❌ Timeout: Only {ready_count}/{total_count} parties ready after {max_wait}s")

    if ready_count > 0:
        print(f"   ✅ Ready: {ready_parties}")
    if failed_parties:
        print(f"   ❌ Failed: {failed_parties}")

    return False


def robust_http_request(url: str, method: str = 'GET', json_data: Dict = None,
                        max_retries: int = 3, timeout: int = 10) -> Tuple[Optional[requests.Response], bool]:
    """
    Make HTTP request with automatic retries and exponential backoff.

    Args:
        url: Target URL
        method: HTTP method ('GET', 'POST', etc.)
        json_data: JSON payload for POST requests
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds

    Returns:
        Tuple[Optional[requests.Response], bool]: (response, success)
    """
    for attempt in range(max_retries + 1):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response, True

        except requests.exceptions.ConnectionError:
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                time.sleep(wait_time)
                continue
            else:
                return None, False

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                time.sleep(1)
                continue
            else:
                return None, False

        except Exception:
            return None, False

    return None, False


class GlobalSMPCCoordinator:
    """
    Global coordinator for distributed SMPC protocol.

    Manages protocol execution across parties running on different
    servers worldwide with enhanced monitoring and error handling.
    """

    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        self.party_endpoints = self.config['parties']
        self.threshold = self.config['threshold']
        self.prime = self.config.get('prime', crypto.get_prime(512))

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("GlobalSMPCCoordinator")

        # Flask app for management API
        self.app = Flask("SMPC_Global_Coordinator")
        self._setup_management_api()

        # Protocol state
        self.protocol_running = False
        self.protocol_result = None
        self.protocol_status = "idle"

        self.logger.info(f"Global SMPC Coordinator initialized with {len(self.party_endpoints)} parties")

    def _load_config(self, config_file: str) -> Dict:
        """Load global configuration from JSON file"""
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Validate configuration
        required_fields = ['parties', 'threshold']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in config: {field}")

        if len(config['parties']) < config['threshold']:
            raise ValueError("Threshold cannot exceed number of parties")

        return config

    def _setup_management_api(self):
        """Setup REST API for protocol management"""

        @self.app.route('/api/v1/status', methods=['GET'])
        def get_global_status():
            """Get global protocol status"""
            return jsonify({
                "protocol_status": self.protocol_status,
                "protocol_running": self.protocol_running,
                "total_parties": len(self.party_endpoints),
                "threshold": self.threshold,
                "result": self.protocol_result,
                "parties": [
                    {
                        "party_id": p['party_id'],
                        "endpoint": f"http://{p['host']}:{p['port']}",
                        "status": self._check_party_health(p)
                    }
                    for p in self.party_endpoints
                ]
            })

        @self.app.route('/api/v1/health', methods=['GET'])
        def health_check():
            """Health check for coordinator"""
            party_health = self._check_all_parties_health()
            healthy_parties = sum(1 for status in party_health.values() if status == "healthy")

            return jsonify({
                "coordinator_status": "healthy",
                "parties_healthy": healthy_parties,
                "parties_total": len(self.party_endpoints),
                "all_parties_ready": healthy_parties >= self.threshold,
                "party_details": party_health
            })

        @self.app.route('/api/v1/start_protocol', methods=['POST'])
        def start_protocol():
            """Start the distributed SMPC protocol"""
            if self.protocol_running:
                return jsonify({
                    "success": False,
                    "error": "Protocol already running"
                }), 400

            # Start protocol in background thread
            def run_protocol():
                self.protocol_running = True
                self.protocol_status = "running"
                try:
                    # Wait for servers to be ready first
                    if not wait_for_servers_ready(self.party_endpoints):
                        raise Exception("Party servers not ready")

                    coordinator = DistributedSMPCCoordinator(
                        self.party_endpoints,
                        self.threshold,
                        self.prime
                    )
                    result, success = coordinator.run_distributed_protocol()

                    self.protocol_result = {
                        "result": result,
                        "success": success,
                        "timestamp": time.time()
                    }
                    self.protocol_status = "completed" if success else "failed"

                except Exception as e:
                    self.logger.error(f"Protocol execution failed: {e}")
                    self.protocol_result = {
                        "result": None,
                        "success": False,
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    self.protocol_status = "failed"
                finally:
                    self.protocol_running = False

            thread = threading.Thread(target=run_protocol)
            thread.start()

            return jsonify({
                "success": True,
                "message": "Protocol started",
                "status": "running"
            })

        @self.app.route('/api/v1/party/<int:party_id>/status', methods=['GET'])
        def get_party_status(party_id):
            """Get status of specific party"""
            party = self._find_party_by_id(party_id)
            if not party:
                return jsonify({"error": "Party not found"}), 404

            try:
                url = f"http://{party['host']}:{party['port']}/api/v1/status"
                response, success = robust_http_request(url, timeout=10)

                if success and response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"Party returned {response.status_code}" if response else "Connection failed"
                    return jsonify({"error": error_msg}), 502

            except Exception as e:
                return jsonify({"error": str(e)}), 502

    def _find_party_by_id(self, party_id: int) -> Optional[Dict]:
        """Find party configuration by ID"""
        for party in self.party_endpoints:
            if party['party_id'] == party_id:
                return party
        return None

    def _check_party_health(self, party: Dict) -> str:
        """Check health of a single party"""
        try:
            url = f"http://{party['host']}:{party['port']}/health"
            response, success = robust_http_request(url, timeout=5)

            if success and response.status_code == 200:
                return "healthy"
            elif response:
                return f"unhealthy_http_{response.status_code}"
            else:
                return "unreachable"

        except Exception as e:
            return f"error_{type(e).__name__}"

    def _check_all_parties_health(self) -> Dict[int, str]:
        """Check health of all parties concurrently"""
        health_status = {}

        with ThreadPoolExecutor(max_workers=len(self.party_endpoints)) as executor:
            # Submit health checks for all parties
            future_to_party = {
                executor.submit(self._check_party_health, party): party['party_id']
                for party in self.party_endpoints
            }

            # Collect results
            for future in as_completed(future_to_party):
                party_id = future_to_party[future]
                try:
                    health_status[party_id] = future.result()
                except Exception as e:
                    health_status[party_id] = f"check_failed_{type(e).__name__}"

        return health_status

    def run_interactive_protocol(self):
        """Run protocol with interactive monitoring - FIXED VERSION"""
        print("🌐 Global Distributed SMPC Protocol")
        print("=" * 60)

        # CRITICAL FIX: Wait for all party servers to be ready first
        print("\n🚀 Step 1: Waiting for party servers to start...")
        if not wait_for_servers_ready(self.party_endpoints, max_wait=45):
            print("❌ Failed to connect to all parties!")
            print("💡 Make sure all party servers are running:")
            for party in self.party_endpoints:
                print(
                    f"   - Party {party['party_id']}: python distributed_party_server.py --config configs/party_{party['party_id']}_config.json")
            return False

        # Step 2: Double-check party health
        print("\n🔍 Step 2: Verifying party health...")
        health_status = self._check_all_parties_health()

        healthy_count = 0
        for party_id, status in health_status.items():
            emoji = "✅" if status == "healthy" else "❌"
            party = self._find_party_by_id(party_id)
            endpoint = f"{party['host']}:{party['port']}" if party else "unknown"
            print(f"  {emoji} Party {party_id} ({endpoint}): {status}")
            if status == "healthy":
                healthy_count += 1

        if healthy_count < self.threshold:
            print(f"\n❌ Insufficient healthy parties: {healthy_count}/{self.threshold} required")
            return False

        print(f"\n✅ {healthy_count}/{len(self.party_endpoints)} parties healthy (≥{self.threshold} required)")

        # Step 3: Start protocol
        print("\n🚀 Step 3: Starting distributed SMPC protocol...")

        coordinator = DistributedSMPCCoordinator(
            self.party_endpoints,
            self.threshold,
            self.prime
        )

        start_time = time.time()
        result, success = coordinator.run_distributed_protocol()
        execution_time = time.time() - start_time

        print("\n" + "=" * 60)
        if success:
            print("🎉 DISTRIBUTED SMPC COMPLETED SUCCESSFULLY!")
            print(f"📊 Final Result: {result}")
            print(f"⏱️  Execution Time: {execution_time:.2f}s")
            print(f"🌐 Parties Used: {len(self.party_endpoints)}")
            print(f"🔒 Threshold Security: {self.threshold}")
        else:
            print("❌ DISTRIBUTED SMPC FAILED")
            print(f"⏱️  Time Before Failure: {execution_time:.2f}s")
            print("\n💡 Troubleshooting tips:")
            print("  1. Make sure all party servers are running and healthy")
            print("  2. Check network connectivity between parties")
            print("  3. Verify configuration files are correct")

        print("=" * 60)
        return success

    def run_management_server(self, host='0.0.0.0', port=8080):
        """Run the management API server"""
        self.logger.info(f"Starting management server on {host}:{port}")
        self.app.run(host=host, port=port, threaded=True)


def create_sample_configs():
    """Create sample configuration files for distributed SMPC"""

    # Global coordinator configuration
    global_config = {
        "parties": [
            {
                "party_id": 1,
                "host": "server1.example.com",
                "port": 5001,
                "secret_value": 100000
            },
            {
                "party_id": 2,
                "host": "server2.example.com",
                "port": 5002,
                "secret_value": 200000
            },
            {
                "party_id": 3,
                "host": "server3.example.com",
                "port": 5003,
                "secret_value": 300000
            }
        ],
        "threshold": 2,
        "prime": None  # Will be generated automatically
    }

    # Individual party configurations
    party_configs = []

    for i, party in enumerate(global_config["parties"]):
        # Create configuration for each party
        other_parties = [p for p in global_config["parties"] if p["party_id"] != party["party_id"]]

        party_config = {
            "party_id": party["party_id"],
            "host": "0.0.0.0",  # Listen on all interfaces
            "port": party["port"],
            "secret_value": party["secret_value"],
            "threshold": global_config["threshold"],
            "total_parties": len(global_config["parties"]),
            "prime": 0,  # Will be set by coordinator
            "other_parties": other_parties
        }

        party_configs.append(party_config)

    # Save configurations
    with open('global_config.json', 'w') as f:
        json.dump(global_config, f, indent=2)

    for i, config in enumerate(party_configs):
        filename = f'party_{config["party_id"]}_config.json'
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

    print("Sample configuration files created:")
    print("  - global_config.json (for coordinator)")
    print("  - party_1_config.json (for party 1)")
    print("  - party_2_config.json (for party 2)")
    print("  - party_3_config.json (for party 3)")


def main():
    """Main entry point for global coordinator"""
    parser = argparse.ArgumentParser(description='Global Distributed SMPC Coordinator')
    parser.add_argument('--config', '-c', help='Global configuration file (JSON)')
    parser.add_argument('--mode', '-m', choices=['interactive', 'server', 'create-configs'],
                        default='interactive', help='Operation mode')
    parser.add_argument('--host', default='0.0.0.0', help='Management server host')
    parser.add_argument('--port', type=int, default=8080, help='Management server port')

    args = parser.parse_args()

    if args.mode == 'create-configs':
        create_sample_configs()
        return 0

    if not args.config:
        print("Error: Configuration file required for interactive/server mode")
        print("Use --mode create-configs to generate sample configurations")
        return 1

    try:
        coordinator = GlobalSMPCCoordinator(args.config)

        if args.mode == 'interactive':
            success = coordinator.run_interactive_protocol()
            return 0 if success else 1
        elif args.mode == 'server':
            coordinator.run_management_server(args.host, args.port)
            return 0

    except KeyboardInterrupt:
        print("\nCoordinator interrupted")
        return 0
    except Exception as e:
        print(f"Coordinator error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())