"""
Document Compliance Checker Module for eFile Sathi
Validates government documents against standards and mandatory requirements
"""
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance severity levels"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


@dataclass
class ComplianceCheck:
    """Individual compliance check result"""
    name: str
    passed: bool
    message: str
    level: ComplianceLevel
    details: str = ""


@dataclass
class ComplianceReport:
    """Complete compliance report"""
    score: float  # 0-100
    checks: List[ComplianceCheck]
    passed_count: int
    failed_count: int
    grade: str  # A, B, C, D, F
    recommendations: List[str]
    has_digital_signature: bool = False


class DocumentComplianceChecker:
    """
    Checks government documents for compliance with standards
    Based on Government of India document guidelines and eOffice standards
    """
    
    def __init__(self):
        # Mandatory field patterns
        self.mandatory_patterns = {
            'file_number': {
                'patterns': [
                    r'file\s*(?:no\.?|number)\s*[:\-]?\s*[\w\-\/]+',
                    r'फ़ाइल\s*(?:न|नं|संख्या)[:\-]?\s*[\w\-\/]+',
                    r'F\.?\s*No\.?\s*[\w\-\/]+'
                ],
                'level': ComplianceLevel.CRITICAL,
                'message': 'File Number / फ़ाइल संख्या'
            },
            'date': {
                'patterns': [
                    r'dated?\s*[:\-]?\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
                    r'दिनांक\s*[:\-]?\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
                    r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[,\s]+\d{4}'
                ],
                'level': ComplianceLevel.CRITICAL,
                'message': 'Document Date / दिनांक'
            },
            'subject': {
                'patterns': [
                    r'subject\s*[:\-]',
                    r'sub\s*[:\-]',
                    r'विषय\s*[:\-]'
                ],
                'level': ComplianceLevel.CRITICAL,
                'message': 'Subject Line / विषय'
            },
            'reference': {
                'patterns': [
                    r'ref(?:erence)?\s*[:\-]',
                    r'संदर्भ\s*[:\-]'
                ],
                'level': ComplianceLevel.MAJOR,
                'message': 'Reference Number / संदर्भ'
            },
            'signature_block': {
                'patterns': [
                    r'(?:yours?\s+)?(?:faithfully|sincerely|obediently)',
                    r'(?:sd[\/\-]?|signed)',
                    r'हस्ताक्षर',
                    r'\([a-zA-Z\s\.]+\)\s*\n\s*[a-zA-Z\s,]+'  # Name in brackets followed by designation
                ],
                'level': ComplianceLevel.CRITICAL,
                'message': 'Signature Block / हस्ताक्षर'
            },
            'designation': {
                'patterns': [
                    r'(?:secretary|director|under\s+secretary|deputy\s+secretary|joint\s+secretary)',
                    r'(?:officer|commissioner|collector|magistrate)',
                    r'(?:सचिव|निदेशक|उप\s*सचिव|संयुक्त\s*सचिव)'
                ],
                'level': ComplianceLevel.MAJOR,
                'message': 'Officer Designation / पदनाम'
            },
            'ministry_department': {
                'patterns': [
                    r'(?:ministry|department|government)\s+of',
                    r'(?:मंत्रालय|विभाग|सरकार)',
                    r'भारत\s+सरकार',
                    r'Government\s+of\s+India'
                ],
                'level': ComplianceLevel.MAJOR,
                'message': 'Ministry/Department Header / मंत्रालय'
            },
            'addressee': {
                'patterns': [
                    r'to\s*[,:\-]',
                    r'प्रति\s*[,:\-]',
                    r'(?:the|shri|smt|dr\.?)\s+[a-zA-Z\s]+,?\s*\n'
                ],
                'level': ComplianceLevel.MINOR,
                'message': 'Addressee / प्रति'
            }
        }
        
        # Document format checks
        self.format_checks = [
            ('proper_salutation', r'(?:sir|madam|महोदय|महोदया)', 'Proper Salutation / अभिवादन'),
            ('closing_remarks', r'(?:action\s+|for\s+|kindly\s+|please\s+)', 'Closing Remarks / समापन टिप्पणी'),
            ('copy_to', r'(?:copy\s+to|cc\s*[:\-]|प्रतिलिपि)', 'Copy To / प्रतिलिपि')
        ]
        
        # Digital signature patterns
        self.digital_signature_patterns = [
            r'digitally\s+signed',
            r'e[\-\s]?sign(?:ed|ature)?',
            r'डिजिटल\s+हस्ताक्षर',
            r'DSC',
            r'Certificate\s+Serial\s+No'
        ]
    
    def check_compliance(self, text: str) -> ComplianceReport:
        """
        Check document compliance with government standards
        
        Args:
            text: Document text to check
            
        Returns:
            ComplianceReport with detailed results
        """
        checks: List[ComplianceCheck] = []
        text_lower = text.lower()
        
        # Check mandatory fields
        for field_name, field_config in self.mandatory_patterns.items():
            found = False
            for pattern in field_config['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    break
            
            checks.append(ComplianceCheck(
                name=field_name,
                passed=found,
                message=field_config['message'],
                level=field_config['level'],
                details="Found" if found else "Missing"
            ))
        
        # Check format elements
        for check_name, pattern, message in self.format_checks:
            found = bool(re.search(pattern, text, re.IGNORECASE))
            checks.append(ComplianceCheck(
                name=check_name,
                passed=found,
                message=message,
                level=ComplianceLevel.INFO,
                details="Present" if found else "Not found"
            ))
        
        # Check for digital signature
        has_digital_signature = any(
            re.search(pattern, text, re.IGNORECASE) 
            for pattern in self.digital_signature_patterns
        )
        
        # Calculate score
        passed_count = sum(1 for c in checks if c.passed)
        failed_count = len(checks) - passed_count
        
        # Weighted scoring
        total_weight = 0
        earned_weight = 0
        
        weight_map = {
            ComplianceLevel.CRITICAL: 25,
            ComplianceLevel.MAJOR: 15,
            ComplianceLevel.MINOR: 5,
            ComplianceLevel.INFO: 2
        }
        
        for check in checks:
            weight = weight_map[check.level]
            total_weight += weight
            if check.passed:
                earned_weight += weight
        
        score = (earned_weight / total_weight * 100) if total_weight > 0 else 0
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 40:
            grade = "D"
        else:
            grade = "F"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(checks)
        
        return ComplianceReport(
            score=round(score, 1),
            checks=checks,
            passed_count=passed_count,
            failed_count=failed_count,
            grade=grade,
            recommendations=recommendations,
            has_digital_signature=has_digital_signature
        )
    
    def _generate_recommendations(self, checks: List[ComplianceCheck]) -> List[str]:
        """Generate recommendations based on failed checks"""
        recommendations = []
        
        for check in checks:
            if not check.passed:
                if check.level == ComplianceLevel.CRITICAL:
                    recommendations.append(f"⚠️ CRITICAL: Add {check.message} - Required for official validity")
                elif check.level == ComplianceLevel.MAJOR:
                    recommendations.append(f"❗ Important: Include {check.message} for completeness")
                elif check.level in [ComplianceLevel.MINOR, ComplianceLevel.INFO]:
                    recommendations.append(f"💡 Suggestion: Consider adding {check.message}")
        
        if not recommendations:
            recommendations.append("✅ Document meets all compliance requirements!")
        
        return recommendations[:5]  # Limit to top 5


# Singleton instance
compliance_checker = DocumentComplianceChecker()


def check_document_compliance(text: str) -> dict:
    """
    Convenience function to check document compliance
    
    Args:
        text: Document text
        
    Returns:
        Dictionary with compliance results
    """
    report = compliance_checker.check_compliance(text)
    
    return {
        'score': report.score,
        'grade': report.grade,
        'passed_count': report.passed_count,
        'failed_count': report.failed_count,
        'total_checks': report.passed_count + report.failed_count,
        'has_digital_signature': report.has_digital_signature,
        'checks': [
            {
                'name': c.name,
                'passed': c.passed,
                'message': c.message,
                'level': c.level.value,
                'details': c.details
            }
            for c in report.checks
        ],
        'recommendations': report.recommendations
    }


if __name__ == "__main__":
    print("Compliance Checker Module Test")
    print("-" * 50)
    
    test_doc = """
    Government of India
    Ministry of Finance
    Department of Expenditure
    
    F. No. 12/4/2024-E.II(A)
    Dated: 25th December 2024
    
    OFFICE MEMORANDUM
    
    Subject: Revised guidelines for budget allocation for FY 2024-25
    
    Reference: Previous OM No. 10/2/2024-E.II(A) dated 15.06.2024
    
    The undersigned is directed to inform all Ministries/Departments that...
    
    Yours faithfully,
    
    (Sd/-)
    (Rajesh Kumar)
    Under Secretary to the Government of India
    
    Copy to:
    1. All Ministries/Departments
    2. CAG Office
    """
    
    result = check_document_compliance(test_doc)
    
    print(f"Compliance Score: {result['score']}%")
    print(f"Grade: {result['grade']}")
    print(f"Passed: {result['passed_count']}/{result['total_checks']}")
    print(f"Digital Signature: {'Yes' if result['has_digital_signature'] else 'No'}")
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  {rec}")
