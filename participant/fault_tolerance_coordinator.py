import socket
import json
import uuid
import threading
import time
from queue import Queue
from collections import defaultdict

class FaultTolerantCoordinator:
    """Coordinator that handles concurrent transactions and failures"""
    
    def __init__(self):
        self.nodes = [
            {'host': 'localhost', 'port': 6001, 'operation': 'debit', 'name': 'Sender'},
            {'host': 'localhost', 'port': 6002, 'operation': 'credit', 'name': 'Receiver'}
        ]
        self.timeout = 5
        self.transaction_queue = Queue()
        self.active_transactions = {}
        self.transaction_lock = threading.Lock()
        self.concurrency_limit = 3  # Max concurrent transactions
        
    def send_to_node(self, node, message, timeout=None):
        """Send message with timeout handling"""
        timeout = timeout or self.timeout
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((node['host'], node['port']))
            sock.send(json.dumps(message).encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            return json.loads(response)
        except socket.timeout:
            return {'status': 'timeout', 'error': 'Connection timed out'}
        except ConnectionRefusedError:
            return {'status': 'error', 'error': 'Connection refused - node down?'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def crash_node(self, port):
        """Simulate node crash"""
        for node in self.nodes:
            if node['port'] == port:
                response = self.send_to_node(node, {'command': 'crash'}, timeout=2)
                return response
        return {'status': 'error', 'message': 'Node not found'}
    
    def restart_node(self, port):
        """Restart crashed node"""
        for node in self.nodes:
            if node['port'] == port:
                response = self.send_to_node(node, {'command': 'restart'}, timeout=2)
                return response
        return {'status': 'error', 'message': 'Node not found'}
    
    def get_balances(self):
        """Get balances from all nodes"""
        balances = {}
        for node in self.nodes:
            response = self.send_to_node(node, {'command': 'balance'}, timeout=2)
            if response.get('status') == 'success':
                balances[node['port']] = {
                    'balance': response.get('balance', 0),
                    'is_failed': response.get('is_failed', False)
                }
            else:
                balances[node['port']] = {
                    'balance': 'Unknown',
                    'is_failed': True
                }
        return balances
    
    def execute_single_transaction(self, amount, tx_id=None):
        """Execute one transaction with failure handling"""
        if not tx_id:
            tx_id = str(uuid.uuid4())[:8]
        
        logs = []
        
        # Get initial balances
        initial_balances = self.get_balances()
        logs.append(f"TX {tx_id}: Started - Transfer ${amount}")
        logs.append(f"TX {tx_id}: Initial - Sender=${initial_balances[6001]['balance']}, Receiver=${initial_balances[6002]['balance']}")
        
        # PHASE 1: Prepare (with timeout simulation)
        logs.append(f"TX {tx_id}: PHASE 1 - PREPARE")
        votes = {}
        all_ready = True
        
        for node in self.nodes:
            prepare_msg = {
                'command': 'prepare',
                'tx_id': tx_id,
                'amount': amount,
                'operation': node['operation']
            }
            
            # Add random delay to simulate network issues
            if node['port'] == 6001 and amount > 500:
                prepare_msg['delay'] = 3  # Simulate slow network for large amounts
            
            response = self.send_to_node(node, prepare_msg)
            
            if response.get('status') == 'ready':
                votes[node['port']] = True
                logs.append(f"TX {tx_id}: ✓ {node['name']} ready")
            else:
                votes[node['port']] = False
                reason = response.get('reason', response.get('error', 'Unknown'))
                logs.append(f"TX {tx_id}: ✗ {node['name']} failed: {reason}")
                all_ready = False
        
        # PHASE 2: Decision
        logs.append(f"TX {tx_id}: PHASE 2 - DECISION")
        
        if all_ready:
            logs.append(f"TX {tx_id}: ✓ All ready → COMMIT")
            
            commit_success = True
            for node in self.nodes:
                commit_msg = {
                    'command': 'commit',
                    'tx_id': tx_id,
                    'amount': amount,
                    'operation': node['operation']
                }
                
                response = self.send_to_node(node, commit_msg)
                if response.get('status') == 'committed':
                    logs.append(f"TX {tx_id}: ✓ {node['name']} committed. Balance: ${response.get('balance', '?')}")
                else:
                    logs.append(f"TX {tx_id}: ✗ {node['name']} commit failed")
                    commit_success = False
            
            if commit_success:
                logs.append(f"TX {tx_id}: ✓ TRANSACTION COMMITTED")
            else:
                logs.append(f"TX {tx_id}: ✗ Partial commit - needs recovery")
                
        else:
            logs.append(f"TX {tx_id}: ✗ Not all ready → ROLLBACK")
            
            for node in self.nodes:
                rollback_msg = {
                    'command': 'rollback',
                    'tx_id': tx_id
                }
                response = self.send_to_node(node, rollback_msg)
                if response.get('status') == 'rolled_back':
                    logs.append(f"TX {tx_id}: ✓ {node['name']} rolled back")
            
            logs.append(f"TX {tx_id}: ✓ TRANSACTION ROLLED BACK")
        
        # Get final balances
        final_balances = self.get_balances()
        logs.append(f"TX {tx_id}: Final - Sender=${final_balances[6001]['balance']}, Receiver=${final_balances[6002]['balance']}")
        
        return logs
    
    def execute_concurrent_transactions(self, transactions):
        """Execute multiple transactions concurrently"""
        logs = []
        results = []
        
        logs.append(f"=== STARTING {len(transactions)} CONCURRENT TRANSACTIONS ===")
        
        # Create threads for concurrent execution
        threads = []
        results_lock = threading.Lock()
        
        def worker(amount, tx_index):
            tx_id = f"TX{tx_index:03d}"
            try:
                tx_logs = self.execute_single_transaction(amount, tx_id)
                with results_lock:
                    results.append({'tx_id': tx_id, 'logs': tx_logs, 'success': any('COMMITTED' in log for log in tx_logs)})
            except Exception as e:
                with results_lock:
                    results.append({'tx_id': tx_id, 'logs': [f"Error: {str(e)}"], 'success': False})
        
        # Start transactions
        for i, amount in enumerate(transactions, 1):
            thread = threading.Thread(target=worker, args=(amount, i))
            threads.append(thread)
            thread.start()
            
            # Limit concurrency
            if len(threads) >= self.concurrency_limit:
                for t in threads:
                    t.join()
                threads = []
        
        # Wait for remaining threads
        for thread in threads:
            thread.join()
        
        # Collect results
        committed = sum(1 for r in results if r['success'])
        rolled_back = len(results) - committed
        
        logs.append(f"=== CONCURRENT TRANSACTIONS COMPLETE ===")
        logs.append(f"Total: {len(results)} | Committed: {committed} | Rolled back: {rolled_back}")
        
        # Add individual transaction summaries
        for result in results:
            status = "✓ COMMITTED" if result['success'] else "✗ ROLLED BACK"
            logs.append(f"{result['tx_id']}: {status}")
        
        return logs
    
    def demonstrate_failure_scenarios(self):
        """Demonstrate different failure scenarios"""
        logs = []
        
        logs.append("=== DEMONSTRATING FAILURE SCENARIOS ===")
        
        # Scenario 1: Node crash during prepare
        logs.append("SCENARIO 1: Node crash during prepare phase")
        self.crash_node(6001)
        logs1 = self.execute_single_transaction(100, "FAIL-001")
        logs.extend(logs1)
        self.restart_node(6001)
        
        # Scenario 2: Insufficient funds
        logs.append("\nSCENARIO 2: Insufficient funds")
        logs2 = self.execute_single_transaction(2000, "FAIL-002")  # More than balance
        logs.extend(logs2)
        
        # Scenario 3: Network timeout
        logs.append("\nSCENARIO 3: Network timeout (simulated)")
        logs3 = self.execute_single_transaction(600, "FAIL-003")  # Will trigger delay
        logs.extend(logs3)
        
        # Scenario 4: Concurrent transactions with failures
        logs.append("\nSCENARIO 4: Concurrent transactions with random failures")
        concurrent_logs = self.execute_concurrent_transactions([100, 200, 300, 400, 500])
        logs.extend(concurrent_logs)
        
        logs.append("=== FAILURE DEMONSTRATION COMPLETE ===")
        
        return logs