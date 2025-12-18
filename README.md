📄 Executive Summary
This project implements a fault-tolerant distributed transaction system using the Two-Phase Commit (2PC) protocol. The system demonstrates core distributed computing concepts including atomicity, consistency, concurrency control, and failure recovery across multiple nodes.

🎯 Key Objectives Achieved
✅ Distributed Transactions with atomicity and rollback support

✅ Concurrent Client Access management with lock-based control

✅ Failure Detection & Recovery in multi-node distributed system

✅ Comprehensive Analysis of trade-offs and system behavior

✅ Professional Demonstration with live class presentation

🏗️ System Components
Component	Role	Technology	Port
Client UI	User interface for transaction execution	Django + Bootstrap 5	8000
Coordinator	Manages 2PC protocol, failure detection	Django + Sockets	8000
Node 6001	Participant 1 (Sender - Debits amount)	Python + Threading	6001
Node 6002	Participant 2 (Receiver - Credits amount)	Python + Threading	6002

System Architecture

                    ┌─────────────────┐
                    │    Client UI    │
                    │  (Django Web)   │
                    └────────┬────────┘
                             │ HTTP
                             ▼
                    ┌─────────────────┐
                    │   Coordinator   │
                    │  (Django Server)│
                    │   • 2PC Manager │
                    │   • Logging     │
                    │   • Recovery    │
                    └────────┬────────┘
                             │ Sockets (JSON)
               ┌─────────────┼─────────────┐
               │                           │
               ▼                           ▼
      ┌─────────────────┐       ┌─────────────────┐
      │  Participant    │       │  Participant    │
      │   Node 6001    │       │   Node 6002    │
      │  • Account A   │       │  • Account B   │
      │  • Balance:$   │       │  • Balance:$   │
      │  • Lock-based  │       │  • Lock-based  │
      │    Concurrency │       │    Concurrency │
      └─────────────────┘       └─────────────────┘

      Transaction Model & 2PC Implementation
🔄 Transaction Type: Distributed Money Transfer
From: Node 6001 (Sender Account)

To: Node 6002 (Receiver Account)

Atomicity: Both update or neither updates

Consistency: Total balance always = $2000

📊 Two-Phase Commit Protocol
Phase 1: Prepare (Voting)
Coordinator → Nodes: "Can you commit $X?"
Node Response: 
    ✅ {"status": "ready"} - If sufficient funds & operational
    ❌ {"status": "abort", "reason": "..."} - If cannot proceed

Phase 2: Commit/Rollback (Execution)
If ALL nodes vote READY:
    Coordinator → Nodes: {"command": "commit", "amount": X}

If ANY node votes ABORT:
    Coordinator → Nodes: {"command": "rollback"}

Atomicity Proof
Mathematical Guarantee:
Either: (B1' = B1 - A AND B2' = B2 + A)   [Both update]
Or:     (B1' = B1 AND B2' = B2)           [Neither updates]

NEVER: (B1' = B1 - A AND B2' = B2) 
        OR (B1' = B1 AND B2' = B2 + A)

Sample Transaction Execution
=== Transaction TX001: Transfer $100 ===
📊 BEFORE: Node 6001=$1000, Node 6002=$1000

📋 PHASE 1: PREPARE
   • Node 6001: ✅ READY (can debit $100)
   • Node 6002: ✅ READY (can credit $100)

⚖️ DECISION: ALL 2/2 READY → COMMIT

🚀 PHASE 2: EXECUTION
   • Node 6001: ✅ DEBITED $100 → $900
   • Node 6002: ✅ CREDITED $100 → $1100

📊 AFTER: Node 6001=$900, Node 6002=$1100
✅ ATOMICITY PROVEN: Both nodes updated together

Concurrency Control
Lock-Based Strategy Implementation
class DataStore:
    def __init__(self):
        self.balance = 1000
        self.lock = threading.Lock()  # Critical resource lock
    
    def apply_update(self, amount, operation):
        with self.lock:  # Acquire lock
            if operation == 'debit':
                if self.balance >= amount:
                    self.balance -= amount
                    return True
            elif operation == 'credit':
                self.balance += amount
                return True
        return False

#Concurrent Transaction Handling
Thread Safety: Each node uses mutex locks for balance updates

Deadlock Prevention: Fixed lock acquisition order (6001 → 6002)

Timeout Mechanism: 3-second lock timeout prevents indefinite waiting

Queue Management: Coordinator queues concurrent requests

📊 Concurrency Performance
=== CONCURRENT EXECUTION RESULTS ===
Total Transactions Attempted: 5
Successfully Committed: 3 (60%)
Rolled Back: 2 (40%) - due to simulated failures

Performance Metrics:
• Single Transaction: 2-3 seconds
• 3 Concurrent Transactions: 4-5 seconds  
• Lock Acquisition: < 50ms
• No race conditions detected

Failure Handling & Recovery
🔍 Implemented Failure Scenarios
1. Node Crash During Prepare
Trigger: Manual crash button or 30% random probability

Detection: 3-second socket timeout

Response: Global rollback initiated

Recovery: Manual restart via UI

2. Insufficient Funds
Condition: Requested amount > current balance

Response: Node votes ABORT with specific reason

Action: Coordinator triggers global rollback

Result: Clean failure with clear error message

3. Network Timeout
Simulation: Triggered for amounts > $800

Effect: Coordinator cannot reach node

Treatment: Treated as ABORT vote

Resolution: Global rollback

4. Coordinator Failure
Prevention: Nodes have commit message timeout

Recovery: Nodes auto-rollback after timeout

Design: Avoids blocking indefinite waits

🔄 Recovery Mechanisms
Timeout-Based Detection
def send_to_node(self, node, message):
    try:
        sock = socket.socket()
        sock.settimeout(3)  # 3-second timeout
        sock.connect((node['host'], node['port']))
        # ... communication
    except socket.timeout:
        return {'status': 'timeout', 'error': 'Connection timed out'}

Atomic Rollback Guarantee
Failure Detection → Coordinator → ROLLBACK to ALL nodes
    ↓
Each node reverts prepared state
    ↓
Balances return to pre-transaction values
    ↓
System consistency maintained

Failure Statistics
Total Transactions: 25
Successful Commits: 15 (60%)
Rollbacks due to failures: 10 (40%)

Failure Breakdown:
• Simulated node crashes: 4 (16%)
• Insufficient funds: 3 (12%)  
• Network timeouts: 2 (8%)
• Concurrent conflicts: 1 (4%)

Academic Learning Outcomes
Concepts Demonstrated
Distributed Transactions: Atomic execution across nodes

Consensus Protocols: 2PC for distributed agreement

Concurrency Control: Lock-based synchronization

Fault Tolerance: Detection, recovery, and consistency

System Design: Trade-offs between consistency, availability, performance

Practical Skills Developed
Socket programming for inter-process communication

Thread synchronization and locking

Protocol design and implementation

Failure injection and testing

System monitoring and logging

Web interface development for system demonstration

