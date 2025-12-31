"""
Grievance Tracking Module for eFile Sathi
Track and manage citizen grievances from documents
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class GrievancePriority(Enum):
    """Grievance priority levels"""
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class GrievanceStatus(Enum):
    """Grievance status"""
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


@dataclass
class Grievance:
    """Grievance record"""
    id: str
    subject: str
    details: str
    priority: GrievancePriority
    status: GrievanceStatus
    submitted_date: datetime
    due_date: datetime
    resolved_date: Optional[datetime] = None
    assigned_to: str = ""
    department: str = ""
    citizen_name: str = ""
    contact: str = ""
    source_doc_id: str = ""
    updates: List[Dict] = field(default_factory=list)


class GrievanceTracker:
    """
    Manages citizen grievances extracted from documents
    Compatible with CPGRAMS (Centralized Public Grievance Redress and Monitoring System)
    """
    
import json
import sqlite3
from modules.database import get_db_connection, init_db

class GrievanceTracker:
    """
    Manages citizen grievances using SQLite database
    """
    
    def __init__(self):
        # Initialize DB if needed (though main.py does it, safe to do here)
        self._ensure_tables()
        self._add_sample_data()
    
    def _ensure_tables(self):
        """Ensure tables exist (lightweight check)"""
        try:
            init_db()
        except Exception as e:
            print(f"Database init warning: {e}")
    
    def _add_sample_data(self):
        """Add sample grievances if DB is empty"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM grievances")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Initialization: Adding sample grievances...")
            samples = [
                {
                    'subject': 'Delay in pension disbursement',
                    'details': 'Pension not received for 3 months',
                    'priority': GrievancePriority.URGENT.value,
                    'status': GrievanceStatus.PENDING.value,
                    'days_ago': 3,
                    'department': 'Department of Pension'
                },
                {
                    'subject': 'Request for ration card correction',
                    'details': 'Name spelling error in ration card',
                    'priority': GrievancePriority.HIGH.value,
                    'status': GrievanceStatus.PROCESSING.value,
                    'days_ago': 6,
                    'department': 'Food & Civil Supplies'
                },
                {
                    'subject': 'Property tax assessment query',
                    'details': 'Dispute regarding property valuation',
                    'priority': GrievancePriority.NORMAL.value,
                    'status': GrievanceStatus.RESOLVED.value,
                    'days_ago': 11,
                    'resolved_days_ago': 5,
                    'department': 'Municipal Corporation'
                }
            ]
            
            for i, sample in enumerate(samples):
                submitted = datetime.now() - timedelta(days=sample['days_ago'])
                due = submitted + timedelta(days=15)
                grv_id = f"GRV-{datetime.now().year}-{1000+i+1:04d}"
                
                resolved_date = None
                if sample['status'] == 'resolved':
                    resolved_date = (datetime.now() - timedelta(days=sample.get('resolved_days_ago', 1))).isoformat()
                
                cursor.execute("""
                    INSERT INTO grievances (
                        id, subject, details, priority, status, 
                        submitted_date, due_date, resolved_date, department, updates_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    grv_id, sample['subject'], sample['details'], sample['priority'], sample['status'],
                    submitted.isoformat(), due.isoformat(), resolved_date, sample['department'],
                    json.dumps([])
                ))
            
            conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        """Generate unique grievance ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM grievances")
        count = cursor.fetchone()[0]
        conn.close()
        
        year = datetime.now().year
        return f"GRV-{year}-{count + 1001:04d}"
    
    def register_grievance(
        self,
        subject: str,
        details: str,
        priority: str = "normal",
        citizen_name: str = "",
        department: str = "",
        source_doc_id: str = ""
    ) -> Grievance:
        """Register a new grievance"""
        grv_id = self._generate_id()
        now = datetime.now()
        
        # Calculate due date
        priority_enum = GrievancePriority(priority)
        if priority == "urgent":
            due_days = 7
        elif priority == "high":
            due_days = 10
        else:
            due_days = 15
        
        due_date = now + timedelta(days=due_days)
        
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO grievances (
                id, subject, details, priority, status, 
                submitted_date, due_date, citizen_name, department, source_doc_id, updates_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            grv_id, subject, details, priority, GrievanceStatus.PENDING.value,
            now.isoformat(), due_date.isoformat(), citizen_name, department, source_doc_id,
            json.dumps([])
        ))
        conn.commit()
        conn.close()
        
        return self.get_grievance(grv_id)
    
    def update_status(self, grv_id: str, new_status: str, note: str = "") -> Optional[Grievance]:
        """Update grievance status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT updates_json FROM grievances WHERE id = ?", (grv_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        updates = json.loads(row['updates_json']) if row['updates_json'] else []
        
        resolved_date = None
        if new_status == "resolved":
            resolved_date = datetime.now().isoformat()
        
        if note:
            updates.append({
                'timestamp': datetime.now().isoformat(),
                'status': new_status,
                'note': note
            })
        
        query = "UPDATE grievances SET status = ?, updates_json = ?"
        params = [new_status, json.dumps(updates)]
        
        if resolved_date:
            query += ", resolved_date = ?"
            params.append(resolved_date)
            
        query += " WHERE id = ?"
        params.append(grv_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return self.get_grievance(grv_id)
    
    def get_grievance(self, grv_id: str) -> Optional[Grievance]:
        """Get grievance by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM grievances WHERE id = ?", (grv_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return self._row_to_grievance(row)
    
    def get_all_grievances(self, status_filter: Optional[str] = None) -> List[Grievance]:
        """Get all grievances"""
        conn = get_db_connection()
        query = "SELECT * FROM grievances"
        params = []
        
        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter)
            
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        grievances = [self._row_to_grievance(row) for row in rows]
        
        # Sort in python for complex priority logic or in SQL?
        # SQL sorting: ORDER BY CASE priority WHEN 'urgent' THEN 1 ...
        # For simplicity, stick to Python sort to match previous logic exactly
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2}
        grievances.sort(
            key=lambda g: (priority_order.get(g.priority.value, 2), g.submitted_date),
            reverse=False
        )
        return grievances
    
    def get_overdue_grievances(self) -> List[Grievance]:
        """Get overdue grievances"""
        conn = get_db_connection()
        now_str = datetime.now().isoformat()
        cursor = conn.execute("""
            SELECT * FROM grievances 
            WHERE due_date < ? AND status NOT IN ('resolved', 'closed')
        """, (now_str,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_grievance(row) for row in rows]

    def _row_to_grievance(self, row) -> Grievance:
        """Convert DB row to Grievance object"""
        return Grievance(
            id=row['id'],
            subject=row['subject'],
            details=row['details'],
            priority=GrievancePriority(row['priority']),
            status=GrievanceStatus(row['status']),
            submitted_date=datetime.fromisoformat(row['submitted_date']),
            due_date=datetime.fromisoformat(row['due_date']),
            resolved_date=datetime.fromisoformat(row['resolved_date']) if row['resolved_date'] else None,
            department=row['department'] or "",
            citizen_name=row['citizen_name'] or "",
            source_doc_id=row['source_doc_id'] or "",
            updates=json.loads(row['updates_json']) if row['updates_json'] else []
        )
    
    def get_stats(self) -> Dict:
        """Get statistics directly from DB"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        cursor.execute("SELECT count(*) FROM grievances")
        stats['total'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM grievances WHERE status='pending'")
        stats['pending'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM grievances WHERE status='processing'")
        stats['processing'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM grievances WHERE status='resolved'")
        stats['resolved'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(*) FROM grievances WHERE priority='urgent'")
        stats['urgent'] = cursor.fetchone()[0]
        
        now_str = datetime.now().isoformat()
        cursor.execute("SELECT count(*) FROM grievances WHERE due_date < ? AND status NOT IN ('resolved', 'closed')", (now_str,))
        stats['overdue'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def extract_grievances_from_document(self, text: str, doc_id: str = "") -> List[Grievance]:
        """delegate to original logic but persist to DB via register_grievance"""
        import re
        extracted = []
        grievance_patterns = [
            (r'complaint[s]?\s+(?:regarding|about|for)\s+(.+?)(?:\.|$)', 'normal'),
            (r'grievance[s]?\s+(?:regarding|about)\s+(.+?)(?:\.|$)', 'normal'),
            (r'urgent\s+(?:attention|action)\s+(?:required|needed)\s+(?:for|on)\s+(.+?)(?:\.|$)', 'urgent'),
            (r'शिकायत\s+(.+?)(?:।|$)', 'normal'),
            (r'तत्काल\s+(.+?)(?:।|$)', 'urgent')
        ]
        
        for pattern, priority in grievance_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:3]:
                if len(match) > 10:
                    grievance = self.register_grievance(
                        subject=match[:100],
                        details=f"Extracted from document: {match}",
                        priority=priority,
                        source_doc_id=doc_id
                    )
                    extracted.append(grievance)
        return extracted


# Singleton instance
grievance_tracker = GrievanceTracker()


def register_grievance(subject: str, details: str, priority: str = "normal", **kwargs) -> dict:
    """Convenience function"""
    grievance = grievance_tracker.register_grievance(subject, details, priority, **kwargs)
    return {
        'id': grievance.id,
        'subject': grievance.subject,
        'details': grievance.details,
        'priority': grievance.priority.value,
        'status': grievance.status.value,
        'submitted_date': grievance.submitted_date.isoformat(),
        'due_date': grievance.due_date.isoformat()
    }


def get_grievances(status: Optional[str] = None) -> List[dict]:
    """Get all grievances"""
    grievances = grievance_tracker.get_all_grievances(status)
    return [
        {
            'id': g.id,
            'subject': g.subject,
            'priority': g.priority.value,
            'status': g.status.value,
            'submitted_date': g.submitted_date.isoformat(),
            'due_date': g.due_date.isoformat(),
            'resolved_date': g.resolved_date.isoformat() if g.resolved_date else None,
            'department': g.department
        }
        for g in grievances
    ]


def get_grievance_stats() -> dict:
    return grievance_tracker.get_stats()


if __name__ == "__main__":
    from modules.database import init_db
    init_db()  # Initialize locally for test
    
    print("Grievance Tracker Module Test (SQLite)")
    print("-" * 50)
    
    # Register a new grievance
    result = register_grievance(
        subject="Water supply issue",
        details="No water supply for 5 days",
        priority="urgent",
        department="Water Works"
    )
    print(f"Registered: {result['id']}")
    
    # Get all grievances
    all_grv = get_grievances()
    print(f"\nTotal grievances: {len(all_grv)}")
    
    for g in all_grv[:3]:
        print(f"  {g['id']}: {g['subject']} [{g['status']}]")
    
    stats = get_grievance_stats()
    print(f"\nStats: {stats}")

