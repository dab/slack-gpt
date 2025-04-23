import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import pytest_asyncio
import asyncio
import logging
from unittest.mock import patch, MagicMock

from app.services.knowledge_base import KnowledgeBaseService

# Fixture for a valid temporary PDF directory
@pytest.fixture
def tmp_pdf_dir(tmp_path, monkeypatch):
    # Create one PDF and one non-PDF file
    pdf = tmp_path / "a.pdf"
    pdf.write_text("dummy")
    txt = tmp_path / "b.txt"
    txt.write_text("dummy")
    return tmp_path

# Fixture for a service instance
@pytest.fixture
def kb_service(tmp_pdf_dir):
    return KnowledgeBaseService(str(tmp_pdf_dir))

# --- Tests for _scan_pdf_files ---

def test_scan_pdf_files_success(kb_service, tmp_pdf_dir):
    files = kb_service._scan_pdf_files()
    assert isinstance(files, list)
    assert any(str(tmp_pdf_dir / 'a.pdf') == f for f in files)
    assert not any(f.endswith('.txt') for f in files)


def test_scan_pdf_files_invalid_dir(monkeypatch):
    svc = KnowledgeBaseService("/nonexistent")
    # Force isdir to False
    monkeypatch.setattr(os.path, 'isdir', lambda p: False)
    result = svc._scan_pdf_files()
    assert result == []

# --- Tests for _extract_text_from_pdf ---

class DummyPage:
    def __init__(self, text):
        self._text = text
    def get_text(self):
        return self._text

class DummyDoc:
    def __init__(self, pages):
        self._pages = [DummyPage(p) for p in pages]
    def __iter__(self):
        return iter(self._pages)
    def close(self):
        pass


def test_extract_text_from_pdf_success(kb_service, monkeypatch):
    dummy = DummyDoc(["one", "two"])
    monkeypatch.setattr('app.services.knowledge_base.fitz.open', lambda path: dummy)
    text = kb_service._extract_text_from_pdf("dummy.pdf")
    assert "one" in text and "two" in text
    # Caching: second call returns same (should not error)
    text2 = kb_service._extract_text_from_pdf("dummy.pdf")
    assert text2 == text


def test_extract_text_from_pdf_error(kb_service, monkeypatch):
    # Simulate fitz.open raising
    def bad_open(path):
        raise RuntimeError("bad pdf")
    monkeypatch.setattr('app.services.knowledge_base.fitz.open', bad_open)
    # Capture logging
    with patch('logging.error') as log_err:
        text = kb_service._extract_text_from_pdf("bad.pdf")
        assert text == ""
        log_err.assert_called()

# --- Tests for find_relevant_context ---

@pytest.mark.asyncio
async def test_find_relevant_context_success(monkeypatch, kb_service):
    # Mock scan and extract
    monkeypatch.setattr(kb_service, '_scan_pdf_files', lambda: ["f1.pdf", "f2.pdf"])
    # f1 contains no match, f2 contains one
    monkeypatch.setattr(kb_service, '_extract_text_from_pdf', lambda p: (
        "no match here" if p.endswith('f1.pdf') else "context chunk\n\nanswer chunk\n\nmore text"
    ))
    result = await kb_service.find_relevant_context("answer")
    assert "answer chunk" in result
    # Ensure result is truncated by default max_chars
    assert len(result) <= 2000

@pytest.mark.asyncio
async def test_find_relevant_context_handles_error(monkeypatch, kb_service):
    monkeypatch.setattr(kb_service, '_scan_pdf_files', lambda: ["e.pdf"])
    # _extract_text throws
    monkeypatch.setattr(kb_service, '_extract_text_from_pdf', lambda p: (_ for _ in ()).throw(ValueError("fail")))
    with patch('logging.error') as log_err:
        result = await kb_service.find_relevant_context("anything")
        assert result == ""
        log_err.assert_called()

@pytest.mark.asyncio
async def test_find_relevant_context_max_chars(monkeypatch, kb_service):
    monkeypatch.setattr(kb_service, '_scan_pdf_files', lambda: ["f.pdf"])
    long_text = "chunk " * 1000  # creates more than 2000 chars
    monkeypatch.setattr(kb_service, '_extract_text_from_pdf', lambda p: long_text)
    result = await kb_service.find_relevant_context("chunk", max_chars=100)
    assert len(result) <= 100 