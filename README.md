# 🧩 Fault-Tolerant Distributed Transaction System (2PC)

## 📄 Executive Summary
This project implements a **fault-tolerant distributed transaction system** using the **Two-Phase Commit (2PC) protocol**. It demonstrates core distributed systems concepts such as **atomicity**, **consistency**, **concurrency control**, and **failure recovery** across multiple independent nodes.

The system supports **concurrent client transactions**, handles **node and network failures**, and provides a **web-based interface** for live demonstration and analysis.

---

## 🎯 Key Objectives Achieved
- ✅ Atomic distributed transactions with commit/rollback guarantees  
- ✅ Concurrent client access using lock-based synchronization  
- ✅ Failure detection and recovery in a multi-node environment  
- ✅ Analysis of system trade-offs and runtime behavior  
- ✅ Live demonstration via a web-based UI  

---

## 🏗️ System Components

| Component    | Role                                   | Technology           | Port |
|--------------|----------------------------------------|----------------------|------|
| Client UI    | Web interface for executing transactions | Django + Bootstrap 5 | 8000 |
| Coordinator  | Manages the 2PC protocol and recovery   | Django + Sockets     | 8000 |
| Node 6001    | Participant (Sender – debits funds)     | Python + Threading   | 6001 |
| Node 6002    | Participant (Receiver – credits funds)  | Python + Threading   | 6002 |

---

## 🧱 System Architecture

                ┌─────────────────┐
                │    Client UI    │
                │  (Django Web)   │
                └────────┬────────┘
                         │ HTTP
                         ▼
                ┌─────────────────┐
                │   Coordinator   │
                │  (Django Server)│
                │  • 2PC Manager  │
                │  • Logging      │
                │  • Recovery     │
                └────────┬────────┘
                         │ Sockets (JSON)
           ┌─────────────┼─────────────┐
           │                           │
           ▼                           ▼
  ┌─────────────────┐       ┌─────────────────┐
  │ Participant     │       │ Participant     │
  │ Node 6001       │       │ Node 6002       │
  │ • Account A     │       │ • Account B     │
  │ • Balance       │       │ • Balance       │
  │ • Lock-based    │       │ • Lock-based    │
  │   Concurrency   │       │   Concurrency   │
  └─────────────────┘       └─────────────────┘

---

## 🔄 Transaction Model

**Transaction Type:** Distributed money transfer  

- **From:** Node 6001 (Sender)  
- **To:** Node 6002 (Receiver)  

**Guarantees:**
- **Atomicity:** Both accounts update or neither updates  
- **Consistency:** Total system balance always remains `$2000`  

---

## 📊 Two-Phase Commit (2PC) Protocol

### Phase 1: Prepare (Voting)
Coordinator → Participants:

"Can you commit amount X?"
Participant responses:

✅ { "status": "ready" } — sufficient funds and operational

❌ { "status": "abort"Either:
(B1' = B1 − A) AND (B2' = B2 + A)

Or:
(B1' = B1) AND (B2' = B2)

, "reason": "..." } — unable to proceed

Phase 2: Commit / Rollback
If all nodes vote READY

{ "command": "commit", "amount": X }


If any node votes ABORT
{ "command": "rollback" }


Atomicity Guarantee

The system enforces the following invariant:



If all nodes vote READY
Either:
(B1' = B1 − A) AND (B2' = B2 + A)

Or:
(B1' = B1) AND (B2' = B2)

Invalid states are impossible:
(B1' = B1 − A AND B2' = B2)
(B1' = B1 AND B2' = B2 + A)

Sample Transaction Execution
Transaction TX001 — Transfer $100

Before

Node 6001: $1000

Node 6002: $1000

Phase 1: Prepare

Node 6001 → READY

Node 6002 → READY

Decision: All participants READY → COMMIT

Phase 2: Commit

Node 6001: Debited → $900

Node 6002: Credited → $1100

After

✅ Atomicity preserved

✅ System consistency maintained
Concurrency Control
Lock-Based Synchronization
class DataStore:
    def __init__(self):
        self.balance = 1000
        self.lock = threading.Lock()

    def apply_update(self, amount, operation):
        with self.lock:
            if operation == 'debit' and self.balance >= amount:
                self.balance -= amount
                return True
            elif operation == 'credit':
                self.balance += amount
                return True
        return False

Concurrency Strategy

Thread-safe operations using mutex locks

Deadlock prevention via fixed lock acquisition order (6001 → 6002)

3-second lock timeout to avoid indefinite waiting

Coordinator-side request queueing
Total Transactions Attempted: 5
Successfully Committed: 3 (60%)
Rolled Back: 2 (40%)

Failure Handling & Recovery
Implemented Failure Scenarios

Node crash during prepare

Detected via socket timeout

Triggers global rollback

Insufficient funds

Node votes ABORT with a clear reason

Coordinator initiates rollback

Network timeout

Simulated for large transfer amounts

Treated as an ABORT vote

Coordinator failure

Participants auto-rollback after timeout

Prevents indefinite blocking
#Recovery Mechanisms
Failure detected
    ↓
Coordinator issues ROLLBACK
    ↓
Participants revert prepared state
    ↓
System consistency restored

#Academic Learning Outcomes
Concepts Demonstrated

Distributed transactions and atomic commit protocols

Consensus via Two-Phase Commit

Lock-based concurrency control

Fault detection and recovery

Design trade-offs between consistency, availability, and performance

Practical Skills Developed

Socket-based inter-process communication

Thread synchronization and locking

Distributed protocol design and implementation

Failure injection and testing

System monitoring and logging

Web-based interface development
