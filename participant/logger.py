import time

class TransactionLogger:
    """Simple transaction logger"""
    
    def __init__(self):
        self.logs = []
    
    def log(self, tx_id, status, message=""):
        """Add log entry"""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"{timestamp} | TX={tx_id} | {status} | {message}"
        self.logs.append(entry)
        print(entry)
        return entry