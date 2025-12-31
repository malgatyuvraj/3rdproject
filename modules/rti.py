"""
RTI Automation Module for Government Document AI System
Auto-generates formal RTI response letters with redaction
Reduces 30-day process to 5 minutes
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


@dataclass
class RTIResponse:
    """Generated RTI response"""
    letter_content: str
    relevant_documents: List[Dict]
    redacted_items: List[str]
    response_date: str
    appeal_info: str
    word_count: int


class RTIGenerator:
    """
    RTI Response Generator for government offices
    Automatically generates formal response letters
    """
    
    def __init__(self, office_name: str = "Office of the Under Secretary"):
        """
        Initialize RTI generator
        
        Args:
            office_name: Name of the responding office
        """
        self.office_name = office_name
        
        # Sensitive information patterns for redaction
        self.redaction_patterns = {
            'aadhaar': r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            'pan': r'\b[A-Z]{5}\d{4}[A-Z]\b',
            'phone': r'\b(?:\+91|0)?[6-9]\d{9}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'bank_account': r'\b\d{9,18}\b',
            'address': r'(?i)(?:house|flat|plot)[\s\w,.-]+(?:pin|pincode)?\s*:?\s*\d{6}',
        }
        
        # RTI response templates
        self.templates = {
            'standard': self._get_standard_template(),
            'partial_disclosure': self._get_partial_disclosure_template(),
            'transfer': self._get_transfer_template(),
            'denial': self._get_denial_template(),
        }
    
    def generate_response(
        self,
        query: str,
        relevant_docs: List[Dict],
        applicant_name: str = "Applicant",
        application_number: str = None,
        response_type: str = "standard"
    ) -> RTIResponse:
        """
        Generate RTI response letter
        
        Args:
            query: RTI query/request
            relevant_docs: List of relevant documents
            applicant_name: Name of RTI applicant
            application_number: RTI application number
            response_type: Type of response (standard, partial, transfer, denial)
            
        Returns:
            RTIResponse object
        """
        # Generate application number if not provided
        if not application_number:
            application_number = f"RTI/{datetime.now().strftime('%Y%m%d')}/{self._generate_id()}"
        
        # Prepare document excerpts
        doc_excerpts, redacted_items = self._prepare_documents(relevant_docs)
        
        # Generate response letter
        letter = self._generate_letter(
            query=query,
            applicant_name=applicant_name,
            application_number=application_number,
            doc_excerpts=doc_excerpts,
            response_type=response_type
        )
        
        # Generate appeal information
        appeal_info = self._generate_appeal_info()
        
        return RTIResponse(
            letter_content=letter,
            relevant_documents=[
                {
                    'title': doc.get('title', 'Untitled'),
                    'excerpt': doc_excerpts.get(doc.get('doc_id', ''), '')[:200]
                }
                for doc in relevant_docs
            ],
            redacted_items=redacted_items,
            response_date=datetime.now().strftime('%d/%m/%Y'),
            appeal_info=appeal_info,
            word_count=len(letter.split())
        )
    
    def _prepare_documents(self, docs: List[Dict]) -> tuple:
        """Prepare and redact document excerpts"""
        excerpts = {}
        redacted_items = []
        
        for doc in docs:
            doc_id = doc.get('doc_id', str(len(excerpts)))
            text = doc.get('text', doc.get('matched_section', ''))
            
            # Redact sensitive information
            redacted_text, items = self._redact_sensitive_info(text)
            
            excerpts[doc_id] = redacted_text
            redacted_items.extend(items)
        
        return excerpts, list(set(redacted_items))
    
    def _redact_sensitive_info(self, text: str) -> tuple:
        """Redact sensitive information from text"""
        redacted_items = []
        redacted_text = text
        
        for info_type, pattern in self.redaction_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                redacted_items.append(f"{info_type}: {len(matches)} item(s)")
                redacted_text = re.sub(
                    pattern,
                    f'[REDACTED-{info_type.upper()}]',
                    redacted_text,
                    flags=re.IGNORECASE
                )
        
        return redacted_text, redacted_items
    
    def _generate_letter(
        self,
        query: str,
        applicant_name: str,
        application_number: str,
        doc_excerpts: Dict[str, str],
        response_type: str
    ) -> str:
        """Generate the formal response letter"""
        
        current_date = datetime.now().strftime('%d %B %Y')
        
        # Header
        letter = f"""
{self.office_name}
Government of India

File No.: {application_number}
Date: {current_date}

To,
{applicant_name}
(RTI Applicant)

Subject: Response to RTI Application - {application_number}

Reference: Your RTI application dated _________ seeking information regarding:
"{query[:200]}{'...' if len(query) > 200 else ''}"

Sir/Madam,

"""
        
        if response_type == "standard":
            letter += self._standard_body(doc_excerpts)
        elif response_type == "partial_disclosure":
            letter += self._partial_disclosure_body(doc_excerpts)
        elif response_type == "transfer":
            letter += self._transfer_body()
        elif response_type == "denial":
            letter += self._denial_body()
        
        # Footer with appeal info
        letter += self._letter_footer()
        
        return letter.strip()
    
    def _standard_body(self, doc_excerpts: Dict[str, str]) -> str:
        """Standard response body with full disclosure"""
        body = """With reference to your RTI application cited above, the information sought is furnished as under:

"""
        
        if doc_excerpts:
            for i, (doc_id, excerpt) in enumerate(doc_excerpts.items(), 1):
                body += f"""
Point {i}:
{excerpt[:500]}{'...' if len(excerpt) > 500 else ''}

"""
        else:
            body += """No specific documents were found matching your query. However, the following general information is provided:

[Information to be filled by the CPIO]

"""
        
        body += """
The above information is being provided under Section 7(1) of the Right to Information Act, 2005.

"""
        return body
    
    def _partial_disclosure_body(self, doc_excerpts: Dict[str, str]) -> str:
        """Partial disclosure response"""
        body = """With reference to your RTI application, partial information is being provided as follows:

"""
        
        for i, (doc_id, excerpt) in enumerate(doc_excerpts.items(), 1):
            body += f"""Information Point {i}:
{excerpt[:300]}

Note: Certain personal information has been redacted under Section 8(1)(j) of the RTI Act, 2005.

"""
        
        body += """
The redacted information pertains to personal details of third parties, disclosure of which would constitute unwarranted invasion of privacy. This information is exempt under Section 8(1)(j) of the RTI Act, 2005.

"""
        return body
    
    def _transfer_body(self) -> str:
        """Transfer to another department response"""
        return """With reference to your RTI application, it is informed that the information sought pertains to:

[Name of the relevant Department/Ministry]

Accordingly, your application is being transferred to the concerned Public Information Officer of the above department under Section 6(3) of the RTI Act, 2005.

The details of the transferred office are:
CPIO: [Name]
Department: [Department Name]
Address: [Address]

You will receive the response directly from the concerned department.

"""
    
    def _denial_body(self) -> str:
        """Denial of information response"""
        return """With reference to your RTI application, it is regretted to inform that the information sought cannot be provided for the following reasons:

1. The information is exempted under Section 8(1) of the RTI Act, 2005.
   [Specify the applicable clause: (a) to (j)]

2. Specific grounds for exemption:
   [Provide specific justification]

You have the right to appeal against this decision as per the procedure outlined below.

"""
    
    def _letter_footer(self) -> str:
        """Common letter footer"""
        appeal_deadline = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')
        
        return f"""
APPEAL MECHANISM:
If you are not satisfied with this response, you may file a First Appeal with the Appellate Authority within 30 days of receipt of this letter (i.e., by {appeal_deadline}).

First Appellate Authority:
[Name of the Appellate Authority]
[Designation]
[Address]

If not satisfied with the decision of the FAA, you may file a Second Appeal with the Central Information Commission within 90 days.

Central Information Commission
August Kranti Bhawan, Bhikaji Cama Place
New Delhi - 110066
Website: https://cic.gov.in

No fee is required for filing an appeal.


Yours faithfully,


(Digital Signature)
Central Public Information Officer
{self.office_name}

Encl: As stated above

Copy to:
1. Guard file
2. RTI Cell for record
"""
    
    def _generate_appeal_info(self) -> str:
        """Generate appeal information"""
        return """
APPEAL RIGHTS UNDER RTI ACT, 2005:

1. FIRST APPEAL (Section 19(1)):
   - Timeline: Within 30 days of receiving this response
   - To: First Appellate Authority of this office
   - No fee required

2. SECOND APPEAL (Section 19(3)):
   - Timeline: Within 90 days of First Appellate Authority decision
   - To: Central Information Commission (CIC)
   - Address: August Kranti Bhawan, Bhikaji Cama Place, New Delhi - 110066
   - Website: https://cic.gov.in
   - Online filing available

3. COMPLAINT (Section 18):
   - If no response received within 30 days
   - Directly to Central Information Commission
"""
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import random
        import string
        return ''.join(random.choices(string.digits, k=6))
    
    def _get_standard_template(self) -> str:
        return "standard"
    
    def _get_partial_disclosure_template(self) -> str:
        return "partial_disclosure"
    
    def _get_transfer_template(self) -> str:
        return "transfer"
    
    def _get_denial_template(self) -> str:
        return "denial"


def generate_rti_response(query: str, documents: List[Dict]) -> Dict:
    """
    Convenience function for generating RTI response
    
    Args:
        query: RTI query
        documents: Relevant documents from search
        
    Returns:
        RTI response as dictionary
    """
    generator = RTIGenerator()
    response = generator.generate_response(query, documents)
    
    return {
        'letter': response.letter_content,
        'documents': response.relevant_documents,
        'redacted': response.redacted_items,
        'date': response.response_date,
        'appeal_info': response.appeal_info
    }


if __name__ == "__main__":
    print("RTI Generator Module Test")
    print("-" * 50)
    
    # Test RTI generation
    test_query = "Please provide details of all recruitment orders issued in 2024"
    
    test_docs = [
        {
            'doc_id': 'DOC001',
            'title': 'Recruitment Order 2024',
            'text': 'The Ministry hereby announces recruitment for 500 posts. Contact: recruitment@gov.in, Phone: 9876543210'
        },
        {
            'doc_id': 'DOC002',
            'title': 'Vacancy Freeze Order',
            'text': 'All vacancies frozen until March 2025. Aadhaar verification: 1234 5678 9012 required.'
        }
    ]
    
    generator = RTIGenerator(office_name="Ministry of Personnel")
    response = generator.generate_response(
        query=test_query,
        relevant_docs=test_docs,
        applicant_name="Shri Ram Kumar",
        response_type="partial_disclosure"
    )
    
    print("\n" + "="*60)
    print("GENERATED RTI RESPONSE")
    print("="*60)
    print(response.letter_content)
    print("\n" + "-"*40)
    print(f"Redacted items: {response.redacted_items}")
    print(f"Word count: {response.word_count}")
