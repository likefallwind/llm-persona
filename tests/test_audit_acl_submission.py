import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "submission_audit", ROOT / "scripts/audit_acl_submission.py"
)
submission_audit = importlib.util.module_from_spec(module_spec)
assert module_spec.loader is not None
module_spec.loader.exec_module(submission_audit)


def test_pdfinfo_parser_preserves_blank_metadata():
    fields = submission_audit.pdfinfo_fields("Title:   \nAuthor:  \nPages: 9\n")
    assert fields == {"Title": "", "Author": "", "Pages": "9"}


def test_font_parser_supports_type1_and_cid_rows():
    text = """name type encoding emb sub uni object ID
----- ---- -------- --- --- --- ---------
A Type 1 Custom yes yes yes 1 0
B CID TrueType Identity-H yes yes yes 2 0
"""
    rows = submission_audit.font_rows(text)
    assert len(rows) == 2
    assert all(row[-5] == "yes" for row in rows)
    assert all("Type 3" not in " ".join(row) for row in rows)


def test_current_acl_pdf_passes_structural_audit():
    report = submission_audit.audit(
        ROOT,
        ROOT / "paper/submission/main.tex",
        ROOT / "paper/submission/submission.pdf",
    )
    assert report["pages"] == 9
    assert report["passed"], report
