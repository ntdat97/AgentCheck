"""
Script to create sample PDF certificates for testing.
Uses PyMuPDF (fitz) to generate realistic certificate PDFs.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF is required. Install with: pip install pymupdf")
    sys.exit(1)


def create_certificate_pdf(
    output_path: Path,
    university_name: str,
    candidate_name: str,
    degree_name: str,
    issue_date: str,
    certificate_id: str = "CERT-2023-001"
):
    """Create a certificate PDF with the given details."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size
    
    # Colors
    navy = (0.1, 0.2, 0.4)
    gold = (0.8, 0.6, 0.2)
    black = (0, 0, 0)
    gray = (0.4, 0.4, 0.4)
    
    # Draw border
    border_rect = fitz.Rect(30, 30, 582, 762)
    page.draw_rect(border_rect, color=gold, width=3)
    inner_rect = fitz.Rect(40, 40, 572, 752)
    page.draw_rect(inner_rect, color=navy, width=1)
    
    # University name (header)
    page.insert_text(
        (306, 100),
        university_name.upper(),
        fontsize=24,
        fontname="helv",
        color=navy,
        rotate=0,
    )
    # Center the text manually
    text_width = fitz.get_text_length(university_name.upper(), fontname="helv", fontsize=24)
    page.insert_text(
        (306 - text_width/2, 100),
        university_name.upper(),
        fontsize=24,
        fontname="helv",
        color=navy,
    )
    
    # Certificate title
    title = "CERTIFICATE OF GRADUATION"
    title_width = fitz.get_text_length(title, fontname="helv", fontsize=20)
    page.insert_text(
        (306 - title_width/2, 160),
        title,
        fontsize=20,
        fontname="helv",
        color=navy,
    )
    
    # Decorative line
    page.draw_line((150, 180), (462, 180), color=gold, width=2)
    
    # "This is to certify that"
    certify_text = "This is to certify that"
    certify_width = fitz.get_text_length(certify_text, fontname="helv", fontsize=14)
    page.insert_text(
        (306 - certify_width/2, 240),
        certify_text,
        fontsize=14,
        fontname="helv",
        color=black,
    )
    
    # Candidate name (large, prominent)
    name_width = fitz.get_text_length(candidate_name.upper(), fontname="helv", fontsize=28)
    page.insert_text(
        (306 - name_width/2, 300),
        candidate_name.upper(),
        fontsize=28,
        fontname="helv",
        color=navy,
    )
    
    # Decorative line under name
    page.draw_line((200, 315), (412, 315), color=gold, width=1)
    
    # "has successfully completed all requirements for"
    completed_text = "has successfully completed all requirements for the degree of"
    completed_width = fitz.get_text_length(completed_text, fontname="helv", fontsize=12)
    page.insert_text(
        (306 - completed_width/2, 370),
        completed_text,
        fontsize=12,
        fontname="helv",
        color=black,
    )
    
    # Degree name
    degree_width = fitz.get_text_length(degree_name.upper(), fontname="helv", fontsize=18)
    page.insert_text(
        (306 - degree_width/2, 420),
        degree_name.upper(),
        fontsize=18,
        fontname="helv",
        color=navy,
    )
    
    # Issue date
    date_text = f"Conferred on {issue_date}"
    date_width = fitz.get_text_length(date_text, fontname="helv", fontsize=14)
    page.insert_text(
        (306 - date_width/2, 480),
        date_text,
        fontsize=14,
        fontname="helv",
        color=black,
    )
    
    # Certificate ID
    id_text = f"Certificate ID: {certificate_id}"
    id_width = fitz.get_text_length(id_text, fontname="helv", fontsize=10)
    page.insert_text(
        (306 - id_width/2, 520),
        id_text,
        fontsize=10,
        fontname="helv",
        color=gray,
    )
    
    # Signature lines
    page.draw_line((100, 650), (250, 650), color=black, width=1)
    page.draw_line((362, 650), (512, 650), color=black, width=1)
    
    # Signature labels
    page.insert_text((130, 670), "University Registrar", fontsize=10, fontname="helv", color=gray)
    page.insert_text((400, 670), "Dean of Faculty", fontsize=10, fontname="helv", color=gray)
    
    # University seal placeholder
    seal_center = (306, 600)
    page.draw_circle(seal_center, 40, color=gold, width=2)
    seal_text = "[UNIVERSITY SEAL]"
    seal_width = fitz.get_text_length(seal_text, fontname="helv", fontsize=8)
    page.insert_text(
        (306 - seal_width/2, 603),
        seal_text,
        fontsize=8,
        fontname="helv",
        color=gold,
    )
    
    # Footer
    footer_text = "This certificate is issued in accordance with the university's academic regulations."
    footer_width = fitz.get_text_length(footer_text, fontname="helv", fontsize=8)
    page.insert_text(
        (306 - footer_width/2, 730),
        footer_text,
        fontsize=8,
        fontname="helv",
        color=gray,
    )
    
    # Save
    doc.save(str(output_path))
    doc.close()
    print(f"Created: {output_path}")


def main():
    """Create all sample certificate PDFs."""
    output_dir = Path(__file__).parent.parent / "data" / "sample_pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Certificate 1: Verified scenario (University of Example)
    create_certificate_pdf(
        output_path=output_dir / "certificate_verified.pdf",
        university_name="University of Example",
        candidate_name="John Smith",
        degree_name="Bachelor of Science in Computer Science",
        issue_date="May 15, 2023",
        certificate_id="UOE-2023-CS-0042"
    )
    
    # Certificate 2: Not verified / Denied scenario (Global Tech Institute)
    create_certificate_pdf(
        output_path=output_dir / "certificate_denied.pdf",
        university_name="Global Tech Institute",
        candidate_name="Jane Doe",
        degree_name="Master of Business Administration",
        issue_date="December 10, 2022",
        certificate_id="GTI-2022-MBA-0128"
    )
    
    # Certificate 3: Unknown university scenario
    create_certificate_pdf(
        output_path=output_dir / "certificate_unknown.pdf",
        university_name="Unknown Academy of Sciences",
        candidate_name="Alex Johnson",
        degree_name="Diploma in Data Analytics",
        issue_date="August 20, 2023",
        certificate_id="UAS-2023-DA-0007"
    )
    
    print(f"\nAll sample PDFs created in: {output_dir}")
    print("\nYou can now delete the old .txt files:")
    for txt_file in output_dir.glob("*.txt"):
        print(f"  - {txt_file.name}")


if __name__ == "__main__":
    main()
