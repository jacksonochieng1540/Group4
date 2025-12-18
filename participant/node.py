import socket
import threading
import sys
import json
from .datastore import DataStore
from .logger import TransactionLogger

class ParticipantNode:
    """Participant node for distributed transactions"""
    
    def __init__(self, port):
        self.port = port
        self.store = DataStore(port)
        self.logger = TransactionLogger()
        self.running = True
        
    def handle_request(self, conn):
        """Handle incoming request"""
        try:
            # Receive and decode message
            data = conn.recv(1024).decode('utf-8').strip()
            
            if not data:
                return
            
            # Parse as JSON
            try:
                message = json.loads(data)
                command = message.get('command')
                tx_id = message.get('tx_id', 'unknown')
                
                if command == 'prepare':
                    amount = message.get('amount', 0)
                    operation = message.get('operation', 'debit')
                    
                    self.logger.log(tx_id, "PREPARE", f"{operation} ${amount}")
                    
                    if self.store.prepare(amount, operation):
                        response = {'status': 'ready', 'tx_id': tx_id}
                    else:
                        response = {'status': 'abort', 'tx_id': tx_id, 'reason': 'Insufficient funds'}
                    
                elif command == 'commit':
                    amount = message.get('amount', 0)
                    operation = message.get('operation', 'debit')
                    
                    new_balance = self.store.commit(amount, operation)
                    self.logger.log(tx_id, "COMMITTED", f"Balance: ${new_balance}")
                    response = {'status': 'committed', 'tx_id': tx_id, 'balance': new_balance}
                    
                elif command == 'rollback':
                    self.logger.log(tx_id, "ROLLBACK", "Transaction aborted")
                    response = {'status': 'aborted', 'tx_id': tx_id}
                    
                elif command == 'balance':
                    balance = self.store.get_balance()
                    response = {'status': 'success', 'balance': balance, 'port': self.port}
                    
                elif command == 'reset':
                    balance = self.store.reset()
                    response = {'status': 'success', 'balance': balance, 'message': 'Reset to $1000'}
                    
                else:
                    response = {'status': 'error', 'message': f'Unknown command: {command}'}
                    
            except json.JSONDecodeError:
                # Handle plain text commands for compatibility
                if data == 'ping':
                    response = {'status': 'alive', 'port': self.port}
                elif data == 'balance':
                    balance = self.store.get_balance()
                    response = {'status': 'success', 'balance': balance, 'port': self.port}
                else:
                    response = {'status': 'error', 'message': f'Invalid command: {data}'}
            
            # Send response
            conn.send(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"[NODE {self.port}] Error: {e}")
        finally:
            conn.close()
    
    def start(self):
        """Start the node server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', self.port))
        server.listen(5)
        
        print(f"[NODE {self.port}] Started on port {self.port}")
        print(f"[NODE {self.port}] Initial balance: ${self.store.get_balance()}")
        
        while self.running:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=self.handle_request, args=(conn,), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[NODE {self.port}] Accept error: {e}")
        
        server.close()
        print(f"[NODE {self.port}] Stopped")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m participant.node <port>")
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
        node = ParticipantNode(port)
        node.start()
    except ValueError:
        print("Error: Port must be a number")
    except Exception as e:
        print(f"Error starting node: {e}")