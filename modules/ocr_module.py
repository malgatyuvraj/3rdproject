"""
OCR Module for Government Document AI System
Extracts text from PDFs and images with Hindi + English support
Includes handwritten text detection and confidence scoring
"""
import os
import io
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0

# Import config
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import TESSERACT_CMD, SUPPORTED_LANGUAGES

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


@dataclass
class OCRResult:
    """Result from OCR processing"""
    text: str
    confidence: float
    language: str
    page_count: int
    word_count: int
    has_handwriting: bool
    blocks: List[Dict]


@dataclass
class TextBlock:
    """Individual text block with position and confidence"""
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int
    block_type: str  # 'printed' or 'handwritten'


class OCRProcessor:
    """
    OCR Processor for government documents
    Supports Hindi, English, and mixed documents
    """
    
    def __init__(self, languages: str = "hin+eng"):
        """
        Initialize OCR processor
        
        Args:
            languages: Tesseract language codes (e.g., "hin+eng" for Hindi+English)
        """
        self.languages = languages
        self.tesseract_available = self._validate_tesseract()
    
    def _validate_tesseract(self) -> bool:
        """Validate Tesseract is installed and configured"""
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract version: {version}")
            return True
        except Exception as e:
            print(f"⚠ Tesseract not found. Install with: brew install tesseract tesseract-lang")
            print(f"  OCR features will be disabled until Tesseract is installed.")
            return False
    
    def process_pdf(self, pdf_path: str) -> OCRResult:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            OCRResult with extracted text and metadata
        """
        # Check if Tesseract is available
        if not self.tesseract_available:
            return self._demo_result(pdf_path)
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        return self._process_images(images)
    
    def process_pdf_bytes(self, pdf_bytes: bytes) -> OCRResult:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if not self.tesseract_available:
            return self._demo_result("uploaded_pdf")
        
        images = convert_from_bytes(pdf_bytes, dpi=300)
        return self._process_images(images)
    
    def process_image(self, image_path: str) -> OCRResult:
        """
        Extract text from image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if not self.tesseract_available:
            return self._demo_result(image_path)
        
        image = Image.open(image_path)
        return self._process_images([image])
    
    def process_image_bytes(self, image_bytes: bytes) -> OCRResult:
        """
        Extract text from image bytes
        
        Args:
            image_bytes: Image file as bytes
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if not self.tesseract_available:
            return self._demo_result("uploaded_image")
        
        image = Image.open(io.BytesIO(image_bytes))
        return self._process_images([image])
    
    def _demo_result(self, file_path: str) -> OCRResult:
        """
        Return demo result when Tesseract is unavailable
        """
        demo_text = """GOVERNMENT OF INDIA
MINISTRY OF FINANCE
DEPARTMENT OF EXPENDITURE

Office Memorandum No. F.12/4/2024-E.II(A)
Dated: 15th January 2024

Subject: Revised guidelines for budget allocation and expenditure control for FY 2024-25

The undersigned is directed to inform all Ministries/Departments that the following revised guidelines shall be applicable for the financial year 2024-25:

1. All departments must submit their quarterly expenditure reports by the 15th of the following month.

2. The Finance Secretary shall review all major procurement proposals exceeding Rs. 500 crore.

3. Deadline for submission of revised estimates: 31st March 2024.

4. The Joint Secretary (Budget) is hereby authorized to approve reallocations up to Rs. 100 crore.

Action Required:
- All Secretaries to ensure compliance by 28th February 2024
- Director (Finance) to prepare consolidated report
- Under Secretary to circulate to all attached offices

(Sample document for demonstration - Tesseract OCR not configured)
"""
        return OCRResult(
            text=demo_text,
            confidence=85.0,
            language='en',
            page_count=1,
            word_count=len(demo_text.split()),
            has_handwriting=False,
            blocks=[{'text': demo_text, 'confidence': 85.0, 'x': 0, 'y': 0, 'width': 800, 'height': 1000, 'page': 1, 'block_type': 'printed'}]
        )
    
    def _process_images(self, images: List[Image.Image]) -> OCRResult:
        """
        Process multiple images and combine results
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            Combined OCRResult
        """
        all_text = []
        all_blocks = []
        total_confidence = 0
        confidence_count = 0
        has_handwriting = False
        
        for page_num, image in enumerate(images, 1):
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(
                processed_image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Extract text and confidence
            page_text = []
            for i, text in enumerate(ocr_data['text']):
                if text.strip():
                    conf = float(ocr_data['conf'][i])
                    if conf > 0:  # Valid confidence
                        page_text.append(text)
                        total_confidence += conf
                        confidence_count += 1
                        
                        # Create text block
                        block = {
                            'text': text,
                            'confidence': conf,
                            'x': ocr_data['left'][i],
                            'y': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i],
                            'page': page_num,
                            'block_type': 'printed'
                        }
                        all_blocks.append(block)
            
            all_text.append(' '.join(page_text))
            
            # Check for handwriting (low confidence + irregular spacing)
            if self._detect_handwriting(ocr_data):
                has_handwriting = True
                # Re-process with handwriting-optimized settings
                hw_text = self._process_handwriting(processed_image)
                if hw_text:
                    all_text[-1] += f"\n[Handwritten Section]\n{hw_text}"
        
        # Combine all text
        full_text = '\n\n'.join(all_text)
        
        # Calculate average confidence
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
        
        # Detect primary language
        try:
            detected_lang = detect(full_text) if full_text.strip() else 'unknown'
        except:
            detected_lang = 'mixed'
        
        return OCRResult(
            text=full_text,
            confidence=round(avg_confidence, 2),
            language=detected_lang,
            page_count=len(images),
            word_count=len(full_text.split()),
            has_handwriting=has_handwriting,
            blocks=all_blocks
        )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to grayscale
        gray = image.convert('L')
        
        # Increase contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.5)
        
        # Sharpen
        enhancer = ImageEnhance.Sharpness(enhanced)
        sharpened = enhancer.enhance(2.0)
        
        return sharpened
    
    def _detect_handwriting(self, ocr_data: Dict) -> bool:
        """
        Detect if image contains handwritten text
        
        Uses heuristics:
        - Low confidence scores
        - Irregular character spacing
        - Non-standard character sizes
        
        Args:
            ocr_data: Tesseract OCR data
            
        Returns:
            True if handwriting detected
        """
        confidences = [c for c in ocr_data['conf'] if c > 0]
        
        if not confidences:
            return False
        
        # Check for low average confidence (handwriting typically <70%)
        avg_conf = sum(confidences) / len(confidences)
        low_conf_ratio = sum(1 for c in confidences if c < 50) / len(confidences)
        
        # Handwriting indicators
        if avg_conf < 60 or low_conf_ratio > 0.3:
            return True
        
        return False
    
    def _process_handwriting(self, image: Image.Image) -> str:
        """
        Process handwritten text with optimized settings
        
        Args:
            image: Preprocessed image
            
        Returns:
            Extracted handwritten text
        """
        # Use different PSM mode for handwriting
        config = '--psm 11 --oem 1'  # Sparse text, LSTM only
        
        try:
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config=config
            )
            return text.strip()
        except:
            return ""
    
    def get_confidence_report(self, result: OCRResult) -> Dict:
        """
        Generate confidence report for OCR result
        
        Args:
            result: OCR result
            
        Returns:
            Confidence report with statistics
        """
        if not result.blocks:
            return {
                'overall_confidence': result.confidence,
                'quality': 'unknown',
                'recommendations': ['No text blocks detected']
            }
        
        confidences = [b['confidence'] for b in result.blocks]
        
        # Calculate statistics
        avg_conf = sum(confidences) / len(confidences)
        min_conf = min(confidences)
        max_conf = max(confidences)
        
        # Determine quality
        if avg_conf >= 90:
            quality = 'excellent'
        elif avg_conf >= 80:
            quality = 'good'
        elif avg_conf >= 60:
            quality = 'fair'
        else:
            quality = 'poor'
        
        # Generate recommendations
        recommendations = []
        if avg_conf < 80:
            recommendations.append('Consider using higher quality scans')
        if result.has_handwriting:
            recommendations.append('Handwritten sections detected - manual verification recommended')
        if min_conf < 50:
            recommendations.append('Some text blocks have low confidence - review highlighted sections')
        
        return {
            'overall_confidence': round(avg_conf, 2),
            'min_confidence': round(min_conf, 2),
            'max_confidence': round(max_conf, 2),
            'quality': quality,
            'total_blocks': len(result.blocks),
            'has_handwriting': result.has_handwriting,
            'recommendations': recommendations
        }


# Convenience function for quick OCR
def extract_text(file_path: str, languages: str = "hin+eng") -> str:
    """
    Quick text extraction from file
    
    Args:
        file_path: Path to PDF or image
        languages: Tesseract language codes
        
    Returns:
        Extracted text
    """
    processor = OCRProcessor(languages=languages)
    
    ext = Path(file_path).suffix.lower()
    if ext == '.pdf':
        result = processor.process_pdf(file_path)
    else:
        result = processor.process_image(file_path)
    
    return result.text


if __name__ == "__main__":
    # Test OCR module
    print("OCR Module Test")
    print("-" * 50)
    
    processor = OCRProcessor()
    print("✓ OCR Processor initialized")
    print(f"  Languages: {processor.languages}")
