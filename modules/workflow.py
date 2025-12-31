"""
Document Workflow Tracker Module for eFile Sathi
Track document status through approval chain
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class WorkflowStatus(Enum):
    """Document workflow status"""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    ARCHIVED = "archived"


@dataclass
class WorkflowStep:
    """Individual workflow step"""
    status: WorkflowStatus
    timestamp: datetime
    officer: str
    remarks: str = ""
    department: str = ""


@dataclass
class DocumentWorkflow:
    """Complete document workflow"""
    doc_id: str
    title: str
    current_status: WorkflowStatus
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime
    priority: str = "normal"
    expected_completion: Optional[datetime] = None


import json
import sqlite3
from modules.database import get_db_connection, init_db

class WorkflowTracker:
    """
    Tracks document through government approval chain using SQLite
    """
    
    def __init__(self):
        self.workflow_templates = {
            'standard': [
                WorkflowStatus.SUBMITTED,
                WorkflowStatus.UNDER_REVIEW,
                WorkflowStatus.PENDING_APPROVAL,
                WorkflowStatus.APPROVED,
                WorkflowStatus.ARCHIVED
            ],
            'fast_track': [
                WorkflowStatus.SUBMITTED,
                WorkflowStatus.PENDING_APPROVAL,
                WorkflowStatus.APPROVED
            ],
            'review_required': [
                WorkflowStatus.SUBMITTED,
                WorkflowStatus.UNDER_REVIEW,
                WorkflowStatus.RETURNED,
                WorkflowStatus.UNDER_REVIEW,
                WorkflowStatus.PENDING_APPROVAL,
                WorkflowStatus.APPROVED
            ]
        }
        
        # Initialize tables if not exist (handled by database.init_db)
        try:
            init_db()
        except Exception as e:
            print(f"Database init warning: {e}")
            
        self._add_sample_data()
    
    def _add_sample_data(self):
        """Add sample workflows if DB is empty"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM workflows")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Initialization: Adding sample workflows...")
            
            # Sample 1
            now = datetime.now()
            doc1_id = 'DOC-2024-0001'
            cursor.execute("""
                INSERT INTO workflows (doc_id, title, current_status, created_at, updated_at, priority, expected_completion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc1_id, 'Budget Revision Proposal Q4', WorkflowStatus.PENDING_APPROVAL.value,
                (now - timedelta(days=5)).isoformat(), (now - timedelta(days=1)).isoformat(),
                'high', (now + timedelta(days=3)).isoformat()
            ))
            
            steps1 = [
                (WorkflowStatus.SUBMITTED.value, (now - timedelta(days=5)).isoformat(), "Clerk (Entry)", "Document received"),
                (WorkflowStatus.UNDER_REVIEW.value, (now - timedelta(days=3)).isoformat(), "Section Officer", "Under examination"),
                (WorkflowStatus.PENDING_APPROVAL.value, (now - timedelta(days=1)).isoformat(), "Deputy Secretary", "Forwarded")
            ]
            
            for status, ts, officer, rem in steps1:
                cursor.execute("INSERT INTO workflow_steps (doc_id, status, timestamp, officer, remarks) VALUES (?, ?, ?, ?, ?)",
                               (doc1_id, status, ts, officer, rem))
            
            # Sample 2
            doc2_id = 'DOC-2024-0002'
            cursor.execute("""
                INSERT INTO workflows (doc_id, title, current_status, created_at, updated_at, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc2_id, 'Transfer Order - Batch 2024', WorkflowStatus.ARCHIVED.value,
                (now - timedelta(days=10)).isoformat(), (now - timedelta(days=2)).isoformat(), 'normal'
            ))
            
            steps2 = [
                (WorkflowStatus.SUBMITTED.value, (now - timedelta(days=10)).isoformat(), "Dealing Assistant", ""),
                (WorkflowStatus.UNDER_REVIEW.value, (now - timedelta(days=8)).isoformat(), "Section Officer", ""),
                (WorkflowStatus.PENDING_APPROVAL.value, (now - timedelta(days=5)).isoformat(), "Director", ""),
                (WorkflowStatus.APPROVED.value, (now - timedelta(days=3)).isoformat(), "Joint Secretary", "Approved"),
                (WorkflowStatus.ARCHIVED.value, (now - timedelta(days=2)).isoformat(), "Record Room", "")
            ]
            
            for status, ts, officer, rem in steps2:
                cursor.execute("INSERT INTO workflow_steps (doc_id, status, timestamp, officer, remarks) VALUES (?, ?, ?, ?, ?)",
                               (doc2_id, status, ts, officer, rem))
            
            conn.commit()
        conn.close()

    def create_workflow(
        self,
        doc_id: str,
        title: str,
        priority: str = "normal",
        template: str = "standard"
    ) -> DocumentWorkflow:
        """Create new workflow"""
        now = datetime.now()
        
        # Calculate expected completion
        if priority == "urgent":
            expected_days = 3
        elif priority == "high":
            expected_days = 7
        else:
            expected_days = 14
        
        expected = now + timedelta(days=expected_days)
        
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO workflows (doc_id, title, current_status, created_at, updated_at, priority, expected_completion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, title, WorkflowStatus.SUBMITTED.value,
            now.isoformat(), now.isoformat(), priority, expected.isoformat()
        ))
        
        # Initial step
        conn.execute("""
            INSERT INTO workflow_steps (doc_id, status, timestamp, officer, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            doc_id, WorkflowStatus.SUBMITTED.value, now.isoformat(), "System", "Document submitted"
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_workflow(doc_id)
    
    def advance_workflow(
        self,
        doc_id: str,
        new_status: str,
        officer: str,
        remarks: str = ""
    ) -> Optional[DocumentWorkflow]:
        """Advance workflow"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT 1 FROM workflows WHERE doc_id = ?", (doc_id,))
        if not cursor.fetchone():
            conn.close()
            return None
            
        now = datetime.now()
        
        # Add step
        cursor.execute("""
            INSERT INTO workflow_steps (doc_id, status, timestamp, officer, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, new_status, now.isoformat(), officer, remarks))
        
        # Update workflow
        cursor.execute("""
            UPDATE workflows SET current_status = ?, updated_at = ?
            WHERE doc_id = ?
        """, (new_status, now.isoformat(), doc_id))
        
        conn.commit()
        conn.close()
        
        return self.get_workflow(doc_id)
    
    def get_workflow(self, doc_id: str) -> Optional[DocumentWorkflow]:
        """Get workflow by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workflows WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
            
        # Get steps
        cursor.execute("SELECT * FROM workflow_steps WHERE doc_id = ? ORDER BY timestamp ASC", (doc_id,))
        step_rows = cursor.fetchall()
        conn.close()
        
        steps = [
            WorkflowStep(
                status=WorkflowStatus(s['status']),
                timestamp=datetime.fromisoformat(s['timestamp']),
                officer=s['officer'],
                remarks=s['remarks'],
                department=""
            ) for s in step_rows
        ]
        
        return DocumentWorkflow(
            doc_id=row['doc_id'],
            title=row['title'],
            current_status=WorkflowStatus(row['current_status']),
            steps=steps,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            priority=row['priority'],
            expected_completion=datetime.fromisoformat(row['expected_completion']) if row['expected_completion'] else None
        )
    
    def get_workflow_status(self, doc_id: str) -> Dict:
        """Get detailed status for UI"""
        workflow = self.get_workflow(doc_id)
        if not workflow:
            return {'found': False, 'doc_id': doc_id}
            
        standard_flow = self.workflow_templates['standard']
        current_index = -1
        
        for i, status in enumerate(standard_flow):
            if status == workflow.current_status:
                current_index = i
                break
        
        progress = ((current_index + 1) / len(standard_flow) * 100) if current_index >= 0 else 0
        
        timeline = []
        for step in workflow.steps:
            timeline.append({
                'status': step.status.value,
                'timestamp': step.timestamp.isoformat(),
                'officer': step.officer,
                'remarks': step.remarks,
                'is_current': step.status == workflow.current_status
            })
            
        days_in_process = (datetime.now() - workflow.created_at).days
        days_remaining = None
        if workflow.expected_completion:
            days_remaining = max(0, (workflow.expected_completion - datetime.now()).days)
            
        return {
            'found': True,
            'doc_id': workflow.doc_id,
            'title': workflow.title,
            'current_status': workflow.current_status.value,
            'priority': workflow.priority,
            'progress': round(progress),
            'timeline': timeline,
            'days_in_process': days_in_process,
            'days_remaining': days_remaining,
            'expected_completion': workflow.expected_completion.isoformat() if workflow.expected_completion else None,
            'is_delayed': days_remaining is not None and days_remaining < 0
        }

    def get_pending_documents(self) -> List[Dict]:
        """Get pending documents"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        active = "('submitted', 'under_review', 'pending_approval')"
        cursor.execute(f"SELECT * FROM workflows WHERE current_status IN {active}")
        rows = cursor.fetchall()
        conn.close()
        
        pending = []
        for row in rows:
            updated_at = datetime.fromisoformat(row['updated_at'])
            pending.append({
                'doc_id': row['doc_id'],
                'title': row['title'],
                'status': row['current_status'],
                'priority': row['priority'],
                'days_pending': (datetime.now() - updated_at).days
            })
            
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2}
        pending.sort(key=lambda x: (priority_order.get(x['priority'], 2), -x['days_pending']))
        
        return pending

    def get_stats(self) -> Dict:
        """Get stats"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        cursor.execute("SELECT count(*) FROM workflows")
        stats['total'] = cursor.fetchone()[0]
        
        for status in WorkflowStatus:
            cursor.execute("SELECT count(*) FROM workflows WHERE current_status = ?", (status.value,))
            stats[status.value] = cursor.fetchone()[0]
            
        conn.close()
        return stats


# Singleton instance
workflow_tracker = WorkflowTracker()


def get_workflow_status(doc_id: str) -> dict:
    """Get workflow status for a document"""
    return workflow_tracker.get_workflow_status(doc_id)


def create_workflow(doc_id: str, title: str, priority: str = "normal") -> dict:
    """Create new workflow"""
    workflow = workflow_tracker.create_workflow(doc_id, title, priority)
    return get_workflow_status(doc_id)


def get_pending_documents() -> List[dict]:
    """Get pending documents"""
    return workflow_tracker.get_pending_documents()


def get_workflow_stats() -> dict:
    """Get workflow statistics"""
    return workflow_tracker.get_stats()


if __name__ == "__main__":
    from modules.database import init_db
    init_db()
    
    print("Workflow Tracker Module Test (SQLite)")
    print("-" * 50)
    
    # Test existing workflow
    status = get_workflow_status('DOC-2024-0001')
    print(f"Document: {status['doc_id']}")
    print(f"Status: {status['current_status']}")
    
    # Test pending
    pending = get_pending_documents()
    print(f"\nPending documents: {len(pending)}")
    
    # Test stats
    stats = get_workflow_stats()
    print(f"Stats: {stats}")


# Singleton instance
workflow_tracker = WorkflowTracker()


def get_workflow_status(doc_id: str) -> dict:
    """Get workflow status for a document"""
    return workflow_tracker.get_workflow_status(doc_id)


def create_workflow(doc_id: str, title: str, priority: str = "normal") -> dict:
    """Create new workflow"""
    workflow = workflow_tracker.create_workflow(doc_id, title, priority)
    return get_workflow_status(doc_id)


def get_pending_documents() -> List[dict]:
    """Get pending documents"""
    return workflow_tracker.get_pending_documents()


def get_workflow_stats() -> dict:
    """Get workflow statistics"""
    return workflow_tracker.get_stats()


if __name__ == "__main__":
    print("Workflow Tracker Module Test")
    print("-" * 50)
    
    # Test existing workflow
    status = get_workflow_status('DOC-2024-0001')
    print(f"Document: {status['doc_id']}")
    print(f"Status: {status['current_status']}")
    print(f"Progress: {status['progress']}%")
    print(f"Days in process: {status['days_in_process']}")
    
    print("\nTimeline:")
    for step in status['timeline']:
        marker = "→" if step['is_current'] else "✓"
        print(f"  {marker} {step['status']}: {step['officer']}")
    
    # Test pending documents
    pending = get_pending_documents()
    print(f"\nPending documents: {len(pending)}")
    
    # Test stats
    stats = get_workflow_stats()
    print(f"Stats: {stats}")
