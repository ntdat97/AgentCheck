"""
PDF Parser Service
Extracts text from PDF certificates using LLM Vision API.

Design Decision:
  - Uses LLM Vision API for ALL PDFs (both digital and scanned)
  - PyMuPDF is only used to render PDF pages to images
  - Prioritizes accuracy over speed/cost for compliance verification
"""
import base64
from typing import Optional
from pathlib import Path

try:
    import fitz  # PyMuPDF - used only for rendering PDF to images
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFParser:
    """Service for parsing PDF certificates using LLM Vision."""
    
    def __init__(self, data_dir: str = "./data", llm_client=None):
        self.data_dir = Path(data_dir)
        self.sample_pdfs_dir = self.data_dir / "sample_pdfs"
        self.llm_client = llm_client
    
    def set_llm_client(self, llm_client):
        """Set the LLM client for Vision-based extraction."""
        self.llm_client = llm_client
    
    def parse_pdf(self, pdf_path: str) -> dict:
        """
        Parse a PDF file and extract text using LLM Vision.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with raw_text and metadata
        """
        path = Path(pdf_path)
        
        # Try to find the file
        if not path.exists():
            # Check in sample_pdfs directory
            sample_path = self.sample_pdfs_dir / path.name
            if sample_path.exists():
                path = sample_path
            else:
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Validate it's a PDF
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF: {path.name}")
        
        # Check dependencies
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError(
                "PyMuPDF is required to process PDFs. "
                "Install with: pip install pymupdf"
            )
        
        if not self.llm_client or not self.llm_client.is_available():
            raise RuntimeError(
                "LLM client is required for PDF text extraction. "
                "Please configure GROQ_API_KEY or OPENAI_API_KEY in .env"
            )
        
        return self._extract_with_vision(path)
    
    def _extract_with_vision(self, path: Path) -> dict:
        """
        Extract text from PDF using LLM Vision API.
        
        Process:
        1. Render each PDF page to high-resolution image
        2. Send image to LLM Vision API
        3. Combine extracted text from all pages
        4. Parse document quality information from Vision response
        """
        import json
        
        doc = fitz.open(str(path))
        page_count = len(doc)
        
        extracted_texts = []
        document_quality = {
            "confidence": 1.0,
            "is_damaged": False,
            "issues": []
        }
        
        for page_num, page in enumerate(doc):
            # Render page to high-resolution image (2x zoom)
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to base64 PNG
            img_bytes = pix.tobytes("png")
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            
            # Extract text using Vision API
            response = self.llm_client.extract_text_from_image(base64_image)
            if response:
                # Try to parse as JSON (new format with quality info)
                try:
                    parsed = json.loads(response)
                    if isinstance(parsed, dict):
                        # Extract text from JSON response
                        text = parsed.get("extracted_text", "")
                        if text:
                            extracted_texts.append(text)
                        
                        # Extract quality info (use lowest confidence across pages)
                        quality = parsed.get("document_quality", {})
                        page_confidence = quality.get("confidence", 1.0)
                        if page_confidence < document_quality["confidence"]:
                            document_quality["confidence"] = page_confidence
                        
                        if quality.get("is_damaged", False):
                            document_quality["is_damaged"] = True
                        
                        page_issues = quality.get("issues", [])
                        if isinstance(page_issues, list):
                            document_quality["issues"].extend(page_issues)
                    else:
                        # Response is not a dict, use as raw text
                        extracted_texts.append(response)
                except json.JSONDecodeError:
                    # Not JSON, use response as raw text (backward compatible)
                    extracted_texts.append(response)
        
        doc.close()
        
        raw_text = "\n\n".join(extracted_texts).strip()
        
        if not raw_text:
            raise ValueError(
                "Could not extract text from PDF. "
                "Please ensure the document is readable and not corrupted."
            )
        
        # Deduplicate issues
        document_quality["issues"] = list(set(document_quality["issues"]))
        
        return {
            "raw_text": raw_text,
            "page_count": page_count,
            "filename": path.name,
            "file_path": str(path),
            "extraction_method": "vision_api",
            "document_quality": document_quality  # NEW: quality info from Vision API
        }
    
    def list_sample_pdfs(self) -> list:
        """List available sample PDFs."""
        if not self.sample_pdfs_dir.exists():
            return []
        
        return [
            str(f) for f in self.sample_pdfs_dir.iterdir()
            if f.suffix.lower() == '.pdf'
        ]
