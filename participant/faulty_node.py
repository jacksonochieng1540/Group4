import socket
import threading
import json
import sys
import time
import random

class FaultyNode:
    """Node that can simulate failures for demo purposes"""
    
    def __init__(self, port, fail_probability=0.3):
        self.port = port
        self.balance = 1000
        self.lock = threading.Lock()
        self.transaction_log = []
        self.fail_probability = fail_probability  # Probability of failing during prepare
        self.is_failed = False  # Simulate node crash
        self.active_transactions = {}
        
    def simulate_failure(self, operation):
        """Simulate random failures for demo"""
        if self.is_failed:
            return True  # Node is "crashed"
        
        # Fail during prepare with given probability
        if operation == 'prepare' and random.random() < self.fail_probability:
            print(f"[NODE {self.port}] SIMULATED FAILURE during prepare!")
            return True
        return False
    
    def crash_node(self):
        """Simulate node crash"""
        self.is_failed = True
        print(f"[NODE {self.port}] NODE CRASHED (simulated)")
        return True
    
    def restart_node(self):
        """Restart node after crash"""
        self.is_failed = False
        print(f"[NODE {self.port}] NODE RESTARTED")
        return True
    
    def handle_client(self, conn):
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                return
                
            msg = json.loads(data)
            command = msg.get('command')
            tx_id = msg.get('tx_id', 'unknown')
            response = {}
            
            print(f"[NODE {self.port}] Received {command} for TX {tx_id}")
            
            if command == 'balance':
                with self.lock:
                    response = {
                        'status': 'success', 
                        'balance': self.balance, 
                        'port': self.port,
                        'is_failed': self.is_failed
                    }
                    
            elif command == 'prepare':
                amount = msg.get('amount', 0)
                operation = msg.get('operation', 'debit')
                
                # Store transaction in active list
                self.active_transactions[tx_id] = {
                    'amount': amount,
                    'operation': operation,
                    'status': 'preparing'
                }
                
                # Check for simulated failure
                if self.simulate_failure('prepare'):
                    response = {'status': 'error', 'reason': 'Node failure during prepare'}
                    self.active_transactions[tx_id]['status'] = 'failed'
                else:
                    with self.lock:
                        if operation == 'debit' and self.balance >= amount:
                            # Hold the funds temporarily
                            self.balance -= amount
                            self.active_transactions[tx_id]['held_amount'] = amount
                            response = {'status': 'ready', 'tx_id': tx_id}
                            self.active_transactions[tx_id]['status'] = 'prepared'
                        elif operation == 'credit':
                            response = {'status': 'ready', 'tx_id': tx_id}
                            self.active_transactions[tx_id]['status'] = 'prepared'
                        else:
                            response = {'status': 'abort', 'reason': 'Insufficient funds'}
                            self.active_transactions[tx_id]['status'] = 'rejected'
                            
            elif command == 'commit':
                if tx_id not in self.active_transactions:
                    response = {'status': 'error', 'reason': 'Unknown transaction'}
                else:
                    tx = self.active_transactions[tx_id]
                    
                    # Finalize the transaction
                    if tx['status'] == 'prepared':
                        if tx['operation'] == 'debit':
                            # Amount already deducted during prepare
                            pass  # Nothing to do, already deducted
                        elif tx['operation'] == 'credit':
                            with self.lock:
                                self.balance += tx['amount']
                        
                        tx['status'] = 'committed'
                        self.transaction_log.append(tx.copy())
                        response = {'status': 'committed', 'balance': self.balance}
                    else:
                        response = {'status': 'error', 'reason': 'Transaction not prepared'}
                        
            elif command == 'rollback':
                if tx_id in self.active_transactions:
                    tx = self.active_transactions[tx_id]
                    
                    # Rollback: Return held funds
                    if tx.get('held_amount'):
                        with self.lock:
                            self.balance += tx['held_amount']
                    
                    tx['status'] = 'rolled_back'
                    response = {'status': 'rolled_back'}
                else:
                    response = {'status': 'error', 'reason': 'Transaction not found'}
                    
            elif command == 'crash':
                self.crash_node()
                response = {'status': 'crashed', 'port': self.port}
                
            elif command == 'restart':
                self.restart_node()
                response = {'status': 'restarted', 'port': self.port}
                
            elif command == 'delay':
                # Simulate network delay
                delay = msg.get('delay', 2)
                time.sleep(delay)
                response = {'status': 'delayed', 'delay': delay}
                
            else:
                response = {'status': 'error', 'message': 'Unknown command'}
            
            # Clean up old transactions
            self.cleanup_old_transactions()
            
            conn.send(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"[NODE {self.port}] Error: {e}")
            try:
                conn.send(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            conn.close()
    
    def cleanup_old_transactions(self):
        """Remove old completed transactions"""
        completed = [tx_id for tx_id, tx in self.active_transactions.items() 
                    if tx['status'] in ['committed', 'rolled_back', 'failed']]
        for tx_id in completed:
            self.active_transactions.pop(tx_id, None)
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', self.port))
        server.listen(10)  # Increased for concurrent connections
        
        print(f"[NODE {self.port}] Started on port {self.port}")
        print(f"[NODE {self.port}] Initial balance: ${self.balance}")
        print(f"[NODE {self.port}] Failure probability: {self.fail_probability*100}%")
        
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn,))
                thread.daemon = True
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[NODE {self.port}] Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python faulty_node.py <port> [fail_probability]")
        sys.exit(1)
    
    port = int(sys.argv[1])
    fail_prob = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    
    node = FaultyNode(port, fail_prob)
    node.start()