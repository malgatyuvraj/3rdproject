"""
Document Classifier Module for eFile Sathi
Classifies government documents into categories based on content analysis
"""
import re
from enum import Enum
from typing import Tuple, List, Dict
from dataclasses import dataclass


class DocumentCategory(Enum):
    """Government document categories"""
    CIRCULAR = "circular"
    ORDER = "order"
    MEMO = "memo"
    BUDGET = "budget"
    POLICY = "policy"
    NOTIFICATION = "notification"
    LETTER = "letter"
    REPORT = "report"
    TENDER = "tender"
    MINUTES = "minutes"
    OTHER = "other"


@dataclass
class ClassificationResult:
    """Classification result with confidence"""
    category: DocumentCategory
    confidence: float
    keywords_found: List[str]
    suggested_categories: List[Tuple[str, float]]


# Keyword patterns for each category
CATEGORY_PATTERNS: Dict[DocumentCategory, List[str]] = {
    DocumentCategory.CIRCULAR: [
        r'\bcircular\b', r'\b(office\s+)?memorandum\b', r'\bom\s+no\.?\b',
        r'\bcirculated\b', r'\bfor\s+information\b', r'\ball\s+concerned\b',
        r'\bgeneral\s+circular\b', r'\bपरिपत्र\b', r'\bसर्कुलर\b'
    ],
    DocumentCategory.ORDER: [
        r'\border\b', r'\boffice\s+order\b', r'\bgovernment\s+order\b',
        r'\bg\.?o\.?\b', r'\bhereby\s+ordered\b', r'\bdirected\b',
        r'\bआदेश\b', r'\bकार्यालय\s+आदेश\b'
    ],
    DocumentCategory.MEMO: [
        r'\bmemo(randum)?\b', r'\binternal\s+memo\b', r'\boffice\s+note\b',
        r'\bd\.?o\.?\s+letter\b', r'\bnote\s+for\b', r'\bटिप्पणी\b'
    ],
    DocumentCategory.BUDGET: [
        r'\bbudget\b', r'\ballocation\b', r'\bexpenditure\b', r'\bfunds?\b',
        r'\bfinancial\s+(year|estimates)\b', r'\bsanctioned\b', r'\bcrore\b',
        r'\blakh\b', r'\brupees\b', r'\b₹\b', r'\bबजट\b', r'\bव्यय\b'
    ],
    DocumentCategory.POLICY: [
        r'\bpolicy\b', r'\bguidelines?\b', r'\bframework\b', r'\bstandard\b',
        r'\bprocedure\b', r'\bsop\b', r'\bniti\b', r'\bनीति\b', r'\bनियम\b'
    ],
    DocumentCategory.NOTIFICATION: [
        r'\bnotification\b', r'\bgazette\b', r'\bpublished\b', r'\bnotified\b',
        r'\bw\.?e\.?f\.?\b', r'\beffective\s+from\b', r'\bअधिसूचना\b'
    ],
    DocumentCategory.LETTER: [
        r'\bletter\b', r'\bdear\s+sir\b', r'\bkindly\b', r'\brequest(ed)?\b',
        r'\bregards\b', r'\bsincerely\b', r'\bपत्र\b'
    ],
    DocumentCategory.REPORT: [
        r'\breport\b', r'\bfindings\b', r'\banalysis\b', r'\breview\b',
        r'\bassessment\b', r'\bstudy\b', r'\bरिपोर्ट\b', r'\bप्रतिवेदन\b'
    ],
    DocumentCategory.TENDER: [
        r'\btender\b', r'\bbid(ding)?\b', r'\bprocurement\b', r'\bquotation\b',
        r'\brfp\b', r'\brfq\b', r'\beoi\b', r'\bनिविदा\b'
    ],
    DocumentCategory.MINUTES: [
        r'\bminutes?\b', r'\bmeeting\b', r'\bproceedings\b', r'\battendees?\b',
        r'\bagenda\b', r'\bresolution\b', r'\bकार्यवृत्त\b', r'\bबैठक\b'
    ]
}


class DocumentClassifier:
    """Classifies government documents into categories"""
    
    def __init__(self):
        self.patterns = {
            category: [re.compile(pattern, re.IGNORECASE) 
                      for pattern in patterns]
            for category, patterns in CATEGORY_PATTERNS.items()
        }
    
    def classify(self, text: str) -> ClassificationResult:
        """
        Classify a document based on its text content
        
        Args:
            text: Document text to classify
            
        Returns:
            ClassificationResult with category and confidence
        """
        if not text or len(text.strip()) < 10:
            return ClassificationResult(
                category=DocumentCategory.OTHER,
                confidence=0.0,
                keywords_found=[],
                suggested_categories=[]
            )
        
        # Calculate scores for each category
        scores: Dict[DocumentCategory, float] = {}
        keywords_by_category: Dict[DocumentCategory, List[str]] = {}
        
        text_lower = text.lower()
        text_length = len(text)
        
        for category, patterns in self.patterns.items():
            matches = []
            score = 0.0
            
            for pattern in patterns:
                found = pattern.findall(text)
                if found:
                    matches.extend(found)
                    # Weight by frequency and position
                    first_match = pattern.search(text)
                    if first_match:
                        # Earlier matches get higher weight
                        position_weight = 1.0 - (first_match.start() / text_length) * 0.5
                        score += len(found) * position_weight
            
            if matches:
                scores[category] = score
                keywords_by_category[category] = list(set(matches))[:5]
        
        if not scores:
            return ClassificationResult(
                category=DocumentCategory.OTHER,
                confidence=0.1,
                keywords_found=[],
                suggested_categories=[]
            )
        
        # Normalize scores
        total_score = sum(scores.values())
        normalized_scores = {
            cat: score / total_score 
            for cat, score in scores.items()
        }
        
        # Get top category
        top_category = max(normalized_scores.items(), key=lambda x: x[1])
        
        # Get suggestions (top 3 excluding the main one)
        sorted_scores = sorted(
            normalized_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        suggestions = [
            (cat.value, round(score, 2)) 
            for cat, score in sorted_scores[1:4]
            if score > 0.1
        ]
        
        return ClassificationResult(
            category=top_category[0],
            confidence=round(min(top_category[1] * 2, 0.95), 2),  # Scale and cap confidence
            keywords_found=keywords_by_category.get(top_category[0], []),
            suggested_categories=suggestions
        )
    
    def get_category_display_name(self, category: DocumentCategory) -> str:
        """Get display-friendly category name"""
        names = {
            DocumentCategory.CIRCULAR: "Circular / परिपत्र",
            DocumentCategory.ORDER: "Government Order / आदेश",
            DocumentCategory.MEMO: "Memorandum / ज्ञापन",
            DocumentCategory.BUDGET: "Budget Document / बजट",
            DocumentCategory.POLICY: "Policy / नीति",
            DocumentCategory.NOTIFICATION: "Notification / अधिसूचना",
            DocumentCategory.LETTER: "Official Letter / पत्र",
            DocumentCategory.REPORT: "Report / प्रतिवेदन",
            DocumentCategory.TENDER: "Tender / निविदा",
            DocumentCategory.MINUTES: "Meeting Minutes / कार्यवृत्त",
            DocumentCategory.OTHER: "General Document / सामान्य"
        }
        return names.get(category, category.value.title())


# Singleton instance
classifier = DocumentClassifier()


def classify_document(text: str) -> dict:
    """
    Convenience function to classify a document
    
    Args:
        text: Document text
        
    Returns:
        Dictionary with classification results
    """
    result = classifier.classify(text)
    return {
        'category': result.category.value,
        'confidence': result.confidence,
        'keywords_found': result.keywords_found,
        'suggested_categories': result.suggested_categories,
        'display_name': classifier.get_category_display_name(result.category)
    }
