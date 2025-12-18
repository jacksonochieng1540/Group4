import socket
import json
import uuid
import time

class Coordinator:
    """Distributed transaction coordinator using Two-Phase Commit"""
    
    def __init__(self):
        self.nodes = [
            {'host': 'localhost', 'port': 5001, 'operation': 'debit', 'name': 'Node 5001 (Sender)'},
            {'host': 'localhost', 'port': 5002, 'operation': 'credit', 'name': 'Node 5002 (Receiver)'}
        ]
        self.timeout = 3
    
    def send_to_node(self, node, message):
        """Send message to a node and get response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((node['host'], node['port']))
            
            sock.send(json.dumps(message).encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            return json.loads(response)
        except socket.timeout:
            return {'status': 'timeout', 'error': 'Connection timed out'}
        except ConnectionRefusedError:
            return {'status': 'error', 'error': 'Connection refused'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_node_balance(self, port):
        """Get balance from a specific node"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', port))
            
            sock.send(json.dumps({'command': 'balance'}).encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            data = json.loads(response)
            if data.get('status') == 'success':
                return data.get('balance', 'Unknown')
        except:
            pass
        return 'Offline'
    
    def execute_transaction(self, amount):
        """Execute a distributed money transfer transaction"""
        tx_id = str(uuid.uuid4())[:8]
        logs = []
        
        # Get initial balances
        initial_balances = {}
        for node in self.nodes:
            balance = self.get_node_balance(node['port'])
            initial_balances[node['port']] = balance
        
        logs.append(f"Transaction {tx_id} started")
        logs.append(f"Transferring ${amount} from {self.nodes[0]['name']} to {self.nodes[1]['name']}")
        
        # PHASE 1: Prepare
        logs.append("--- PHASE 1: PREPARE ---")
        votes = []
        
        for node in self.nodes:
            prepare_msg = {
                'command': 'prepare',
                'tx_id': tx_id,
                'amount': amount,
                'operation': node['operation']
            }
            
            response = self.send_to_node(node, prepare_msg)
            
            if response.get('status') == 'ready':
                votes.append(True)
                logs.append(f"✓ {node['name']}: READY to {node['operation']} ${amount}")
            else:
                votes.append(False)
                reason = response.get('reason', response.get('error', 'Unknown error'))
                logs.append(f"✗ {node['name']}: NOT READY - {reason}")
        
        # PHASE 2: Commit or Rollback
        logs.append("--- PHASE 2: DECISION ---")
        
        if all(votes):
            # All nodes ready - COMMIT
            logs.append("✓ All nodes ready → COMMITTING")
            
            for node in self.nodes:
                commit_msg = {
                    'command': 'commit',
                    'tx_id': tx_id,
                    'amount': amount,
                    'operation': node['operation']
                }
                
                response = self.send_to_node(node, commit_msg)
                if response.get('status') == 'committed':
                    new_balance = response.get('balance', 'Unknown')
                    logs.append(f"✓ {node['name']}: {node['operation'].upper()}ED ${amount}. New balance: ${new_balance}")
                else:
                    logs.append(f"✗ {node['name']}: Commit failed")
            
            logs.append(f"✓ Transaction {tx_id} COMMITTED successfully")
            
        else:
            # Some node not ready - ROLLBACK
            logs.append("✗ Some nodes not ready → ROLLING BACK")
            
            for node in self.nodes:
                rollback_msg = {
                    'command': 'rollback',
                    'tx_id': tx_id
                }
                self.send_to_node(node, rollback_msg)
            
            logs.append(f"✗ Transaction {tx_id} ABORTED")
            logs.append("✓ All nodes rolled back successfully")
        
        # Get final balances
        final_balances = {}
        for node in self.nodes:
            balance = self.get_node_balance(node['port'])
            final_balances[node['port']] = balance
        
        logs.append("--- SUMMARY ---")
        logs.append(f"Initial balances: Node 5001=${initial_balances.get(5001, '?')}, Node 5002=${initial_balances.get(5002, '?')}")
        logs.append(f"Final balances: Node 5001=${final_balances.get(5001, '?')}, Node 5002=${final_balances.get(5002, '?')}")
        
        return logs