import importlib.util
import zipfile
from pathlib import Path


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _build_minimal_docx(path: Path, lines: list[str]) -> None:
    rels_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink\" Target=\"https://jobs.lever.co/acme/123\" TargetMode=\"External\"/>
</Relationships>
"""
    content_types = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
</Types>
"""
    root_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>
"""

    paragraphs = []
    for line in lines:
        paragraphs.append(
            f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>"
        )
    paragraphs.append(
        """
<w:p>
  <w:r><w:t>Apply: </w:t></w:r>
  <w:hyperlink r:id="rId1"><w:r><w:t>https://jobs.lever.co/acme/123</w:t></w:r></w:hyperlink>
</w:p>
"""
    )
    document_xml = (
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
  <w:body>
"""
        + "\n".join(paragraphs)
        + """
  </w:body>
</w:document>
"""
    )

    with zipfile.ZipFile(path, "w") as out:
        out.writestr("[Content_Types].xml", content_types)
        out.writestr("_rels/.rels", root_rels)
        out.writestr("word/document.xml", document_xml)
        out.writestr("word/_rels/document.xml.rels", rels_xml)


def test_build_jobs_from_doc_and_zip(tmp_path: Path):
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/build_jobs_from_doc_sources.py",
        "build_jobs_from_doc_sources",
    )

    docx_path = tmp_path / "source.docx"
    _build_minimal_docx(
        docx_path,
        [
            "1. Acme Trading",
            "Roles: Software Engineering Intern",
            "Locations: Singapore",
            "Details: Internship role for new grads",
        ],
    )

    zip_path = tmp_path / "source_bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as out:
        out.write(docx_path, arcname="inside.docx")

    payload = module.build_jobs_from_sources(
        [docx_path, zip_path],
        non_usa_only=True,
        sectors={"tech", "banks", "trading"},
    )

    assert payload["section_count"] >= 2
    assert payload["jobs"]
    first = payload["jobs"][0]
    assert first["apply_url"].startswith("https://jobs.lever.co/")
    assert first["internship_pass"] is True
    assert first["non_usa_pass"] is True
    assert first["discovery_method"] in {"known_api", "direct_link"}


def test_internship_and_non_usa_filters():
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/build_jobs_from_doc_sources.py",
        "build_jobs_filters",
    )

    assert module.is_internship_entry_level("Software Engineering Intern")
    assert not module.is_internship_entry_level("Senior Software Engineer")
    assert module.is_non_usa_job("Location: London, Singapore")
    assert not module.is_non_usa_job("Location: New York, United States")
