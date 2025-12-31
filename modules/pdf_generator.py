"""
PDF Generator Module for eFile Sathi
Generates PDF reports from extracted text; RTI letters and document exports
"""
import io
from datetime import datetime
from fpdf import FPDF
from pathlib import Path


class PDFGenerator(FPDF):
    """Custom PDF class with government styling"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        """Add header to each page"""
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'eFile Sathi - Government Document AI System', border=0, align='C')
        self.ln(5)
        self.set_font('Helvetica', '', 8)
        self.cell(0, 10, 'Digital India Initiative | Ministry of Electronics & IT', border=0, align='C')
        self.ln(10)
        # Line separator
        self.set_draw_color(255, 153, 51)  # Saffron color
        self.set_line_width(0.5)
        self.line(10, 25, 200, 25)
        self.ln(5)
        
    def footer(self):
        """Add footer to each page"""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}', 
                  border=0, align='C')


def generate_text_pdf(text: str, doc_id: str = None, title: str = "Extracted Document") -> bytes:
    """
    Generate a PDF from extracted text
    
    Args:
        text: The extracted text content
        doc_id: Optional document ID
        title: Document title
        
    Returns:
        PDF file as bytes
    """
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(0, 51, 102)  # Government blue
    pdf.cell(0, 10, title, ln=True)
    
    # Document info
    if doc_id:
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f'Document ID: {doc_id}', ln=True)
    
    pdf.ln(5)
    
    # Content
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    # Handle unicode by encoding text
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_text)
    
    return pdf.output()


def generate_summary_pdf(
    text: str,
    summaries: dict,
    actions: list = None,
    doc_id: str = None
) -> bytes:
    """
    Generate a comprehensive summary PDF
    
    Args:
        text: Original text
        summaries: Dictionary with secretary/director/officer summaries
        actions: List of extracted action items
        doc_id: Optional document ID
        
    Returns:
        PDF file as bytes
    """
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, 'Document Summary Report', ln=True)
    
    if doc_id:
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f'Document ID: {doc_id} | Generated: {datetime.now().strftime("%d-%m-%Y")}', ln=True)
    
    pdf.ln(5)
    
    # Summaries section
    for level, summary in summaries.items():
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, f'{level.title()} Level Summary:', ln=True)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        content = summary.get('content', '') if isinstance(summary, dict) else str(summary)
        safe_content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, safe_content)
        pdf.ln(3)
    
    # Actions section
    if actions:
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, 'Action Items', ln=True)
        
        for i, action in enumerate(actions, 1):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(0, 0, 0)
            
            who = action.get('who', 'Unknown')
            what = action.get('what', '')
            priority = action.get('priority', 'medium')
            
            pdf.cell(0, 6, f'{i}. [{priority.upper()}] {who}', ln=True)
            
            pdf.set_font('Helvetica', '', 10)
            safe_what = what.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, f'   {safe_what}')
            pdf.ln(2)
    
    return pdf.output()


def generate_rti_pdf(
    letter_content: str,
    applicant_name: str,
    query: str,
    relevant_docs: list = None
) -> bytes:
    """
    Generate a formal RTI response letter PDF
    
    Args:
        letter_content: The RTI response letter text
        applicant_name: Name of the applicant
        query: Original RTI query
        relevant_docs: List of relevant documents referenced
        
    Returns:
        PDF file as bytes
    """
    pdf = PDFGenerator()
    pdf.add_page()
    
    # RTI Header
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, 'Right to Information (RTI) Response', ln=True, align='C')
    pdf.ln(5)
    
    # Reference info
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'Date: {datetime.now().strftime("%d-%m-%Y")}', ln=True)
    pdf.cell(0, 6, f'To: {applicant_name}', ln=True)
    pdf.ln(5)
    
    # Query summary
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 6, 'Subject:', ln=True)
    pdf.set_font('Helvetica', '', 10)
    safe_query = query[:200].encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, safe_query)
    pdf.ln(5)
    
    # Letter content
    pdf.set_font('Helvetica', '', 11)
    safe_letter = letter_content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, safe_letter)
    
    # References
    if relevant_docs:
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 6, 'Referenced Documents:', ln=True)
        pdf.set_font('Helvetica', '', 10)
        for doc in relevant_docs[:5]:
            doc_title = doc.get('title', doc.get('doc_id', 'Document'))
            pdf.cell(0, 5, f'  - {doc_title}', ln=True)
    
    return pdf.output()


# Singleton instance
pdf_generator = PDFGenerator
