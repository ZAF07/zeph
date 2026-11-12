from io import BytesIO
from typing import Any

from fastapi.testclient import TestClient
from pypdf import PdfWriter


def pdf_with_text(*lines: str) -> bytes:
    """Build a one-page PDF that shows the given lines of text."""
    text_ops = " 0 -16 Td ".join(f"({line}) Tj" for line in lines)
    stream = f"BT /F1 12 Tf 72 720 Td {text_ops} ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref_at = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    pdf += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objects) + 1)
    pdf += b"startxref\n%d\n%%%%EOF\n" % xref_at
    return pdf


def blank_pdf() -> bytes:
    """Build a one-page PDF with no text, like a scanned page."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def upload_document(
    client: TestClient,
    admin: dict[str, str],
    file_name: str,
    content: bytes,
    title: str = "Dhammapada",
    source: str = "trans. Max Müller",
    tradition: str = "Buddhism",
) -> Any:
    """Upload a Knowledge document through the admin API and return the response."""
    return client.post(
        "/api/admin/knowledge-documents",
        files={"file": (file_name, content)},
        data={"title": title, "source": source, "tradition": tradition},
        headers=admin,
    )


def list_documents(client: TestClient, admin: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch every Knowledge document through the admin API."""
    response = client.get("/api/admin/knowledge-documents", headers=admin)
    assert response.status_code == 200, response.text
    documents: list[dict[str, Any]] = response.json()["documents"]
    return documents


def document_text(
    client: TestClient, admin: dict[str, str], document_id: str
) -> str | None:
    """Fetch the text a Knowledge document's replies draw on, or None."""
    response = client.get(
        f"/api/admin/knowledge-documents/{document_id}", headers=admin
    )
    assert response.status_code == 200, response.text
    text: str | None = response.json()["text"]
    return text
