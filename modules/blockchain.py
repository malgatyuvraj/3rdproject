"""
Blockchain Verification Module for Government Document AI System
Tamper-proof audit trail for document verification
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import BLOCKCHAIN_DIR


@dataclass
class Block:
    """Blockchain block"""
    index: int
    timestamp: str
    doc_id: str
    doc_hash: str
    action: str  # 'created', 'accessed', 'modified', 'verified'
    user: str
    previous_hash: str
    hash: str


@dataclass
class VerificationResult:
    """Document verification result"""
    doc_id: str
    is_valid: bool
    original_hash: str
    current_hash: str
    created_at: str
    last_accessed: str
    access_count: int
    modification_detected: bool
    chain_valid: bool


class BlockchainVerifier:
    """
    Blockchain-based document verification system
    Creates immutable audit trail for government documents
    """
    
    def __init__(self, ledger_path: Path = None):
        """
        Initialize blockchain verifier
        
        Args:
            ledger_path: Path to blockchain ledger file
        """
        self.ledger_path = ledger_path or (BLOCKCHAIN_DIR / "ledger.json")
        self.chain: List[Block] = []
        self.document_index: Dict[str, Dict] = {}
        
        # Load existing chain
        self._load_chain()
        
        # Create genesis block if chain is empty
        if not self.chain:
            self._create_genesis_block()
    
    def register_document(self, doc_id: str, content: str, user: str = "system") -> Block:
        """
        Register a new document on the blockchain
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            user: User registering the document
            
        Returns:
            Created block
        """
        doc_hash = self._hash_content(content)
        
        block = self._add_block(
            doc_id=doc_id,
            doc_hash=doc_hash,
            action="created",
            user=user
        )
        
        # Update document index
        self.document_index[doc_id] = {
            'original_hash': doc_hash,
            'created_at': block.timestamp,
            'created_by': user,
            'access_count': 0,
            'last_accessed': None
        }
        
        self._save_chain()
        return block
    
    def record_access(self, doc_id: str, user: str = "anonymous") -> Optional[Block]:
        """
        Record document access event
        
        Args:
            doc_id: Document identifier
            user: User accessing the document
            
        Returns:
            Created block or None if document not found
        """
        if doc_id not in self.document_index:
            return None
        
        block = self._add_block(
            doc_id=doc_id,
            doc_hash=self.document_index[doc_id]['original_hash'],
            action="accessed",
            user=user
        )
        
        # Update access statistics
        self.document_index[doc_id]['access_count'] += 1
        self.document_index[doc_id]['last_accessed'] = block.timestamp
        
        self._save_chain()
        return block
    
    def verify_document(self, doc_id: str, current_content: str) -> VerificationResult:
        """
        Verify document integrity
        
        Args:
            doc_id: Document identifier
            current_content: Current document content
            
        Returns:
            VerificationResult with verification details
        """
        if doc_id not in self.document_index:
            return VerificationResult(
                doc_id=doc_id,
                is_valid=False,
                original_hash="",
                current_hash=self._hash_content(current_content),
                created_at="",
                last_accessed="",
                access_count=0,
                modification_detected=True,
                chain_valid=self._verify_chain()
            )
        
        doc_info = self.document_index[doc_id]
        current_hash = self._hash_content(current_content)
        
        # Check if content matches original
        is_valid = current_hash == doc_info['original_hash']
        
        # Record verification
        self._add_block(
            doc_id=doc_id,
            doc_hash=current_hash,
            action="verified",
            user="verification_system"
        )
        self._save_chain()
        
        return VerificationResult(
            doc_id=doc_id,
            is_valid=is_valid,
            original_hash=doc_info['original_hash'],
            current_hash=current_hash,
            created_at=doc_info['created_at'],
            last_accessed=doc_info.get('last_accessed', 'Never'),
            access_count=doc_info['access_count'],
            modification_detected=not is_valid,
            chain_valid=self._verify_chain()
        )
    
    def get_document_history(self, doc_id: str) -> List[Dict]:
        """
        Get complete access history for a document
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of history entries
        """
        history = []
        
        for block in self.chain:
            if block.doc_id == doc_id:
                history.append({
                    'timestamp': block.timestamp,
                    'action': block.action,
                    'user': block.user,
                    'hash': block.doc_hash[:16] + '...',
                    'block_index': block.index
                })
        
        return history
    
    def get_audit_report(self, doc_id: str) -> Dict:
        """
        Generate audit report for a document
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Audit report dictionary
        """
        if doc_id not in self.document_index:
            return {'error': 'Document not found'}
        
        history = self.get_document_history(doc_id)
        doc_info = self.document_index[doc_id]
        
        return {
            'doc_id': doc_id,
            'registered_on': doc_info['created_at'],
            'registered_by': doc_info['created_by'],
            'original_hash': doc_info['original_hash'][:16] + '...',
            'total_accesses': doc_info['access_count'],
            'last_accessed': doc_info.get('last_accessed', 'Never'),
            'chain_integrity': 'Valid' if self._verify_chain() else 'Compromised',
            'history': history,
            'total_events': len(history)
        }
    
    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _hash_block(self, block_data: Dict) -> str:
        """Generate hash for a block"""
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def _create_genesis_block(self):
        """Create the first block in the chain"""
        genesis = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            doc_id="GENESIS",
            doc_hash="0" * 64,
            action="genesis",
            user="system",
            previous_hash="0" * 64,
            hash=""
        )
        
        genesis.hash = self._hash_block({
            'index': genesis.index,
            'timestamp': genesis.timestamp,
            'doc_id': genesis.doc_id,
            'doc_hash': genesis.doc_hash,
            'action': genesis.action,
            'user': genesis.user,
            'previous_hash': genesis.previous_hash
        })
        
        self.chain.append(genesis)
        self._save_chain()
    
    def _add_block(self, doc_id: str, doc_hash: str, action: str, user: str) -> Block:
        """Add a new block to the chain"""
        previous_block = self.chain[-1]
        
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            doc_id=doc_id,
            doc_hash=doc_hash,
            action=action,
            user=user,
            previous_hash=previous_block.hash,
            hash=""
        )
        
        new_block.hash = self._hash_block({
            'index': new_block.index,
            'timestamp': new_block.timestamp,
            'doc_id': new_block.doc_id,
            'doc_hash': new_block.doc_hash,
            'action': new_block.action,
            'user': new_block.user,
            'previous_hash': new_block.previous_hash
        })
        
        self.chain.append(new_block)
        return new_block
    
    def _verify_chain(self) -> bool:
        """Verify the integrity of the entire chain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Verify previous hash link
            if current.previous_hash != previous.hash:
                return False
            
            # Verify current block hash
            calculated_hash = self._hash_block({
                'index': current.index,
                'timestamp': current.timestamp,
                'doc_id': current.doc_id,
                'doc_hash': current.doc_hash,
                'action': current.action,
                'user': current.user,
                'previous_hash': current.previous_hash
            })
            
            if current.hash != calculated_hash:
                return False
        
        return True
    
    def _save_chain(self):
        """Save blockchain to disk"""
        data = {
            'chain': [asdict(block) for block in self.chain],
            'document_index': self.document_index
        }
        
        with open(self.ledger_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_chain(self):
        """Load blockchain from disk"""
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, 'r') as f:
                    data = json.load(f)
                    
                    self.chain = [
                        Block(**block_data)
                        for block_data in data.get('chain', [])
                    ]
                    self.document_index = data.get('document_index', {})
                    
                print(f"✓ Loaded blockchain with {len(self.chain)} blocks")
            except Exception as e:
                print(f"Failed to load blockchain: {e}")
                self.chain = []
                self.document_index = {}
    
    def get_stats(self) -> Dict:
        """Get blockchain statistics"""
        return {
            'total_blocks': len(self.chain),
            'total_documents': len(self.document_index),
            'chain_valid': self._verify_chain(),
            'last_block_time': self.chain[-1].timestamp if self.chain else None
        }


def verify_document(doc_id: str, content: str) -> Dict:
    """
    Convenience function for document verification
    
    Args:
        doc_id: Document identifier
        content: Current document content
        
    Returns:
        Verification result as dictionary
    """
    verifier = BlockchainVerifier()
    result = verifier.verify_document(doc_id, content)
    
    return {
        'doc_id': result.doc_id,
        'is_valid': result.is_valid,
        'modification_detected': result.modification_detected,
        'chain_valid': result.chain_valid,
        'created_at': result.created_at,
        'access_count': result.access_count
    }


if __name__ == "__main__":
    print("Blockchain Verifier Module Test")
    print("-" * 50)
    
    verifier = BlockchainVerifier()
    
    # Register a test document
    doc_content = "This is a test government order dated 2024."
    block = verifier.register_document(
        doc_id="TEST001",
        content=doc_content,
        user="test_officer"
    )
    print(f"✓ Registered document: {block.doc_id}")
    print(f"  Hash: {block.doc_hash[:16]}...")
    
    # Record access
    verifier.record_access("TEST001", "reader1")
    verifier.record_access("TEST001", "reader2")
    print("✓ Recorded 2 access events")
    
    # Verify unmodified document
    result = verifier.verify_document("TEST001", doc_content)
    print(f"\n✓ Verification (unmodified): {result.is_valid}")
    
    # Verify modified document
    result = verifier.verify_document("TEST001", doc_content + " TAMPERED")
    print(f"✓ Verification (modified): {result.is_valid}")
    print(f"  Modification detected: {result.modification_detected}")
    
    # Get audit report
    report = verifier.get_audit_report("TEST001")
    print(f"\n📋 Audit Report:")
    print(f"  Total events: {report['total_events']}")
    print(f"  Chain integrity: {report['chain_integrity']}")
    
    # Get stats
    stats = verifier.get_stats()
    print(f"\n📊 Blockchain Stats:")
    print(f"  Total blocks: {stats['total_blocks']}")
    print(f"  Documents: {stats['total_documents']}")
