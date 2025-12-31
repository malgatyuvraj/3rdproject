"""
Government Document AI Modules - eFile Sathi
"""
from .ocr_module import OCRProcessor
from .summarizer import DocumentSummarizer
from .extractor import ActionExtractor
from .search import SemanticSearch
from .rti import RTIGenerator
from .blockchain import BlockchainVerifier

# NEW: Hackathon Feature Modules
from .chatbot import DocumentChatbot, chat_with_document
from .compliance import DocumentComplianceChecker, check_document_compliance
from .comparator import DocumentComparator, compare_documents
from .grievance import GrievanceTracker, register_grievance, get_grievances
from .workflow import WorkflowTracker, get_workflow_status, create_workflow

__all__ = [
    "OCRProcessor",
    "DocumentSummarizer", 
    "ActionExtractor",
    "SemanticSearch",
    "RTIGenerator",
    "BlockchainVerifier",
    # New modules
    "DocumentChatbot",
    "chat_with_document",
    "DocumentComplianceChecker",
    "check_document_compliance",
    "DocumentComparator",
    "compare_documents",
    "GrievanceTracker",
    "register_grievance",
    "get_grievances",
    "WorkflowTracker",
    "get_workflow_status",
    "create_workflow"
]
