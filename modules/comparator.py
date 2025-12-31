"""
Document Comparator Module for eFile Sathi
Compares two documents and highlights differences
"""
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff


@dataclass
class DiffLine:
    """A line in the diff output"""
    text: str
    type: str  # 'added', 'removed', 'unchanged'
    line_number: int


@dataclass
class ComparisonResult:
    """Result of document comparison"""
    similarity_score: float  # 0-100
    doc1_lines: List[DiffLine]
    doc2_lines: List[DiffLine]
    additions: int
    deletions: int
    changes_summary: str


class DocumentComparator:
    """
    Compares two documents and identifies differences
    Useful for tracking policy changes between versions
    """
    
    def __init__(self):
        pass
    
    def compare(self, doc1_text: str, doc2_text: str) -> ComparisonResult:
        """
        Compare two documents and highlight differences
        
        Args:
            doc1_text: Original document text
            doc2_text: Updated document text
            
        Returns:
            ComparisonResult with diff details
        """
        # Normalize texts
        doc1_lines = self._normalize_text(doc1_text)
        doc2_lines = self._normalize_text(doc2_text)
        
        # Calculate similarity
        similarity = self._calculate_similarity(doc1_text, doc2_text)
        
        # Generate diff
        doc1_diff, doc2_diff, additions, deletions = self._generate_diff(doc1_lines, doc2_lines)
        
        # Create summary
        if similarity >= 95:
            summary = "Documents are nearly identical"
        elif similarity >= 80:
            summary = f"Minor changes detected ({additions} additions, {deletions} deletions)"
        elif similarity >= 50:
            summary = f"Significant changes detected ({additions} additions, {deletions} deletions)"
        else:
            summary = f"Major revision - documents differ substantially ({additions} additions, {deletions} deletions)"
        
        return ComparisonResult(
            similarity_score=round(similarity, 1),
            doc1_lines=doc1_diff,
            doc2_lines=doc2_diff,
            additions=additions,
            deletions=deletions,
            changes_summary=summary
        )
    
    def _normalize_text(self, text: str) -> List[str]:
        """Normalize text into lines for comparison"""
        # Remove extra whitespace and split into lines
        lines = text.strip().split('\n')
        normalized = []
        
        for line in lines:
            # Clean up the line
            cleaned = ' '.join(line.split())
            if cleaned:  # Only keep non-empty lines
                normalized.append(cleaned)
        
        return normalized
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate overall similarity percentage"""
        # Use SequenceMatcher for ratio
        ratio = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return ratio * 100
    
    def _generate_diff(self, lines1: List[str], lines2: List[str]) -> Tuple[List[DiffLine], List[DiffLine], int, int]:
        """Generate diff between two sets of lines"""
        matcher = SequenceMatcher(None, lines1, lines2)
        
        doc1_diff: List[DiffLine] = []
        doc2_diff: List[DiffLine] = []
        additions = 0
        deletions = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are the same
                for idx, i in enumerate(range(i1, i2)):
                    doc1_diff.append(DiffLine(
                        text=lines1[i],
                        type='unchanged',
                        line_number=i + 1
                    ))
                for idx, j in enumerate(range(j1, j2)):
                    doc2_diff.append(DiffLine(
                        text=lines2[j],
                        type='unchanged',
                        line_number=j + 1
                    ))
            
            elif tag == 'replace':
                # Lines changed
                for i in range(i1, i2):
                    doc1_diff.append(DiffLine(
                        text=lines1[i],
                        type='removed',
                        line_number=i + 1
                    ))
                    deletions += 1
                
                for j in range(j1, j2):
                    doc2_diff.append(DiffLine(
                        text=lines2[j],
                        type='added',
                        line_number=j + 1
                    ))
                    additions += 1
            
            elif tag == 'delete':
                # Lines only in doc1
                for i in range(i1, i2):
                    doc1_diff.append(DiffLine(
                        text=lines1[i],
                        type='removed',
                        line_number=i + 1
                    ))
                    deletions += 1
            
            elif tag == 'insert':
                # Lines only in doc2
                for j in range(j1, j2):
                    doc2_diff.append(DiffLine(
                        text=lines2[j],
                        type='added',
                        line_number=j + 1
                    ))
                    additions += 1
        
        return doc1_diff, doc2_diff, additions, deletions
    
    def get_key_changes(self, doc1_text: str, doc2_text: str) -> Dict:
        """
        Extract key changes between documents
        Focuses on important government document elements
        """
        changes = {
            'date_changes': [],
            'amount_changes': [],
            'deadline_changes': [],
            'reference_changes': []
        }
        
        # Extract dates
        date_pattern = r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}'
        doc1_dates = set(re.findall(date_pattern, doc1_text))
        doc2_dates = set(re.findall(date_pattern, doc2_text))
        
        changes['date_changes'] = {
            'removed': list(doc1_dates - doc2_dates),
            'added': list(doc2_dates - doc1_dates)
        }
        
        # Extract amounts
        amount_pattern = r'₹\s*[\d,]+(?:\.\d{2})?|Rs\.?\s*[\d,]+(?:\.\d{2})?'
        doc1_amounts = set(re.findall(amount_pattern, doc1_text))
        doc2_amounts = set(re.findall(amount_pattern, doc2_text))
        
        changes['amount_changes'] = {
            'removed': list(doc1_amounts - doc2_amounts),
            'added': list(doc2_amounts - doc1_amounts)
        }
        
        return changes


# Singleton instance
comparator = DocumentComparator()


def compare_documents(doc1_text: str, doc2_text: str) -> dict:
    """
    Convenience function to compare two documents
    
    Args:
        doc1_text: Original document text
        doc2_text: Updated document text
        
    Returns:
        Dictionary with comparison results
    """
    result = comparator.compare(doc1_text, doc2_text)
    key_changes = comparator.get_key_changes(doc1_text, doc2_text)
    
    return {
        'similarity_score': result.similarity_score,
        'additions': result.additions,
        'deletions': result.deletions,
        'changes_summary': result.changes_summary,
        'doc1_diff': [
            {'text': d.text, 'type': d.type, 'line': d.line_number}
            for d in result.doc1_lines[:50]  # Limit for performance
        ],
        'doc2_diff': [
            {'text': d.text, 'type': d.type, 'line': d.line_number}
            for d in result.doc2_lines[:50]
        ],
        'key_changes': key_changes
    }


if __name__ == "__main__":
    print("Document Comparator Module Test")
    print("-" * 50)
    
    doc1 = """
    Government of India
    Ministry of Finance
    
    Subject: Budget allocation guidelines
    
    The budget for FY 2023-24 is Rs. 5,00,000 crore.
    Deadline for submission: 15th December 2023.
    
    All departments must comply.
    """
    
    doc2 = """
    Government of India
    Ministry of Finance
    
    Subject: Revised Budget allocation guidelines
    
    The budget for FY 2024-25 is Rs. 6,50,000 crore.
    Deadline for submission: 15th January 2025.
    
    All departments and autonomous bodies must comply.
    Additional reporting requirements have been added.
    """
    
    result = compare_documents(doc1, doc2)
    
    print(f"Similarity: {result['similarity_score']}%")
    print(f"Summary: {result['changes_summary']}")
    print(f"Additions: {result['additions']}, Deletions: {result['deletions']}")
    print("\nKey Changes:")
    print(f"  Dates: {result['key_changes']['date_changes']}")
    print(f"  Amounts: {result['key_changes']['amount_changes']}")
