"""
Tests for PDF Parser Service

The PDFParser now uses LLM Vision API for text extraction from PDFs.
These tests mock the LLM client to avoid real API calls.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.pdf_parser import PDFParser


class MockLLMClient:
    """Mock LLM client for testing Vision API calls."""
    
    def __init__(self, extract_text_return: str = "Sample extracted text"):
        self._extract_text_return = extract_text_return
    
    def is_available(self) -> bool:
        return True
    
    def extract_text_from_image(self, base64_image: str) -> str:
        """Mock Vision API call."""
        return self._extract_text_return


class TestPDFParser:
    """Tests for PDF parser functionality."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return MockLLMClient(
            extract_text_return="""
UNIVERSITY OF EXAMPLE
Certificate of Completion

This is to certify that
JOHN SMITH
has successfully completed the requirements for
Bachelor of Science in Computer Science
Issue Date: 2023-05-15
"""
        )
    
    @pytest.fixture
    def parser(self, tmp_path, mock_llm_client):
        """Create parser with test data directory and mock LLM client."""
        return PDFParser(str(tmp_path), llm_client=mock_llm_client)
    
    def test_init(self, parser):
        """Test parser initialization."""
        assert parser is not None
        assert parser.llm_client is not None
    
    def test_init_without_llm_client(self, tmp_path):
        """Test parser initialization without LLM client."""
        parser = PDFParser(str(tmp_path))
        assert parser is not None
        assert parser.llm_client is None
    
    def test_set_llm_client(self, tmp_path, mock_llm_client):
        """Test setting LLM client after initialization."""
        parser = PDFParser(str(tmp_path))
        assert parser.llm_client is None
        
        parser.set_llm_client(mock_llm_client)
        assert parser.llm_client is not None
        assert parser.llm_client.is_available()
    
    def test_parse_pdf_requires_pdf_extension(self, parser, tmp_path):
        """Test that non-PDF files are rejected."""
        txt_file = tmp_path / "sample_pdfs" / "test.txt"
        txt_file.parent.mkdir(parents=True, exist_ok=True)
        txt_file.write_text("Test content")
        
        with pytest.raises(ValueError, match="File must be a PDF"):
            parser.parse_pdf(str(txt_file))
    
    def test_parse_pdf_file_not_found(self, parser):
        """Test error when PDF doesn't exist."""
        with pytest.raises(FileNotFoundError, match="PDF not found"):
            parser.parse_pdf("nonexistent.pdf")
    
    def test_parse_pdf_without_llm_client(self, tmp_path):
        """Test error when LLM client is not configured."""
        parser = PDFParser(str(tmp_path), llm_client=None)
        
        # Create a dummy PDF file
        pdf_dir = tmp_path / "sample_pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        dummy_pdf = pdf_dir / "test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 dummy content")
        
        with pytest.raises(RuntimeError, match="LLM client is required"):
            parser.parse_pdf(str(dummy_pdf))
    
    def test_parse_pdf_with_unavailable_llm(self, tmp_path):
        """Test error when LLM client is not available."""
        mock_client = Mock()
        mock_client.is_available.return_value = False
        parser = PDFParser(str(tmp_path), llm_client=mock_client)
        
        # Create a dummy PDF file
        pdf_dir = tmp_path / "sample_pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        dummy_pdf = pdf_dir / "test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 dummy content")
        
        with pytest.raises(RuntimeError, match="LLM client is required"):
            parser.parse_pdf(str(dummy_pdf))
    
    def test_list_sample_pdfs_empty(self, parser, tmp_path):
        """Test listing sample PDFs when directory doesn't exist."""
        result = parser.list_sample_pdfs()
        assert result == []
    
    def test_list_sample_pdfs(self, parser, tmp_path):
        """Test listing sample PDFs."""
        # Create sample PDFs directory with some files
        pdf_dir = tmp_path / "sample_pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        (pdf_dir / "test1.pdf").write_bytes(b"%PDF-1.4")
        (pdf_dir / "test2.pdf").write_bytes(b"%PDF-1.4")
        (pdf_dir / "test.txt").write_text("not a pdf")
        
        result = parser.list_sample_pdfs()
        
        # Should only list .pdf files
        assert len(result) == 2
        assert all(f.endswith('.pdf') for f in result)


class TestPDFParserWithRealPDF:
    """Tests that require creating a real PDF file."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client with verified certificate text."""
        return MockLLMClient(
            extract_text_return="""
UNIVERSITY OF EXAMPLE

CERTIFICATE OF GRADUATION

This is to certify that

JOHN SMITH

has successfully completed all requirements for the degree of

BACHELOR OF SCIENCE IN COMPUTER SCIENCE

Conferred on May 15, 2023

[University Seal]
[Registrar Signature]
"""
        )
    
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create a minimal valid PDF for testing."""
        try:
            import fitz  # PyMuPDF
            
            pdf_dir = tmp_path / "sample_pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / "certificate_verified.pdf"
            
            # Create a simple PDF with text
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "UNIVERSITY OF EXAMPLE\nCertificate for JOHN SMITH")
            doc.save(str(pdf_path))
            doc.close()
            
            return pdf_path
        except ImportError:
            pytest.skip("PyMuPDF not available")
    
    @patch('api.services.pdf_parser.PYMUPDF_AVAILABLE', True)
    def test_parse_pdf_with_vision_api(self, tmp_path, sample_pdf, mock_llm_client):
        """Test parsing a real PDF using mocked Vision API."""
        parser = PDFParser(str(tmp_path), llm_client=mock_llm_client)
        
        result = parser.parse_pdf(str(sample_pdf))
        
        assert "raw_text" in result
        assert "UNIVERSITY OF EXAMPLE" in result["raw_text"]
        assert "JOHN SMITH" in result["raw_text"]
        assert result["extraction_method"] == "vision_api"
        assert result["filename"] == "certificate_verified.pdf"
        assert result["page_count"] == 1
    
    @patch('api.services.pdf_parser.PYMUPDF_AVAILABLE', True)
    def test_parse_pdf_finds_file_in_sample_dir(self, tmp_path, sample_pdf, mock_llm_client):
        """Test that parser can find PDFs in sample_pdfs directory."""
        parser = PDFParser(str(tmp_path), llm_client=mock_llm_client)
        
        # Use just the filename, parser should find it in sample_pdfs
        result = parser.parse_pdf("certificate_verified.pdf")
        
        assert "raw_text" in result
        assert result["extraction_method"] == "vision_api"


class TestPDFParserEdgeCases:
    """Test edge cases and error handling."""
    
    def test_pymupdf_not_available(self, tmp_path):
        """Test error when PyMuPDF is not installed."""
        mock_client = MockLLMClient()
        parser = PDFParser(str(tmp_path), llm_client=mock_client)
        
        # Create a dummy PDF file
        pdf_dir = tmp_path / "sample_pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        dummy_pdf = pdf_dir / "test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 dummy")
        
        with patch('api.services.pdf_parser.PYMUPDF_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="PyMuPDF is required"):
                parser.parse_pdf(str(dummy_pdf))
    
    def test_vision_api_returns_empty_text(self, tmp_path):
        """Test error when Vision API returns no text."""
        mock_client = MockLLMClient(extract_text_return="")
        parser = PDFParser(str(tmp_path), llm_client=mock_client)
        
        try:
            import fitz
            
            # Create a valid PDF
            pdf_dir = tmp_path / "sample_pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / "empty.pdf"
            
            doc = fitz.open()
            doc.new_page()
            doc.save(str(pdf_path))
            doc.close()
            
            with pytest.raises(ValueError, match="Could not extract text"):
                parser.parse_pdf(str(pdf_path))
        except ImportError:
            pytest.skip("PyMuPDF not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
