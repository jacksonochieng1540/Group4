import threading

class DataStore:
    """Simple thread-safe data store for participant nodes"""
    
    def __init__(self, node_port):
        self.node_port = node_port
        self.balance = 1000  # Initial balance
        self.lock = threading.Lock()
        self.transactions = []
        
    def prepare(self, amount, operation):
        """Check if transaction can proceed"""
        with self.lock:
            if operation == "debit" and self.balance >= amount:
                return True
            elif operation == "credit":
                return True
            return False
    
    def commit(self, amount, operation):
        """Apply the transaction"""
        with self.lock:
            if operation == "debit":
                self.balance -= amount
            elif operation == "credit":
                self.balance += amount
            
            self.transactions.append({
                'amount': amount,
                'operation': operation,
                'balance': self.balance
            })
            
            print(f"[NODE {self.node_port}] {operation} ${amount}. New balance: ${self.balance}")
            return self.balance
    
    def get_balance(self):
        """Get current balance"""
        with self.lock:
            return self.balance
    
    def reset(self):
        """Reset to initial balance"""
        with self.lock:
            self.balance = 1000
            self.transactions = []
            return self.balance