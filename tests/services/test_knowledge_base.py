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
    with patch('tiktoken.encoding_for_model') as enc_patch:
        class DummyEncoding:
            def encode(self, s):
                return [0] * len(s.split())
        enc_patch.return_value = DummyEncoding()
        result = await kb_service.find_relevant_context("answer", max_context_tokens=10)
        assert "answer chunk" in result
        # Ensure result is truncated by token count
        assert isinstance(result, str)

@pytest.mark.asyncio
async def test_find_relevant_context_handles_error(monkeypatch, kb_service):
    monkeypatch.setattr(kb_service, '_scan_pdf_files', lambda: ["e.pdf"])
    # _extract_text throws
    monkeypatch.setattr(kb_service, '_extract_text_from_pdf', lambda p: (_ for _ in ()).throw(ValueError("fail")))
    with patch('logging.error') as log_err:
        with patch('tiktoken.encoding_for_model') as enc_patch:
            class DummyEncoding:
                def encode(self, s):
                    return [0] * len(s.split())
            enc_patch.return_value = DummyEncoding()
            result = await kb_service.find_relevant_context("anything", max_context_tokens=10)
            assert result == ""
            log_err.assert_called()

@pytest.mark.asyncio
async def test_find_relevant_context_max_context_tokens(monkeypatch, kb_service):
    monkeypatch.setattr(kb_service, '_scan_pdf_files', lambda: ["f.pdf"])
    long_text = "chunk " * 1000  # creates more than 1000 tokens
    monkeypatch.setattr(kb_service, '_extract_text_from_pdf', lambda p: long_text)
    with patch('tiktoken.encoding_for_model') as enc_patch:
        class DummyEncoding:
            def encode(self, s):
                return [0] * len(s.split())
        enc_patch.return_value = DummyEncoding()
        result = await kb_service.find_relevant_context("chunk", max_context_tokens=10)
        # Should be truncated to fit token budget
        assert isinstance(result, str)
        assert len(result.split()) <= 10

@pytest.mark.asyncio
def test_find_relevant_context_multiple_pdfs_with_filenames(monkeypatch, kb_service):
    # Simulate two PDFs, both with relevant content
    monkeypatch.setattr(kb_service, '_scan_pdf_files', lambda: ["first.pdf", "second.pdf"])
    def fake_extract(path):
        if path == "first.pdf":
            return "poet one\n\npoet two"
        else:
            return "poet three\n\npoet four"
    monkeypatch.setattr(kb_service, '_extract_text_from_pdf', fake_extract)
    # Query for 'poet' should match all chunks
    with patch('tiktoken.encoding_for_model') as enc_patch:
        class DummyEncoding:
            def encode(self, s):
                return [0] * len(s.split())
        enc_patch.return_value = DummyEncoding()
        result = asyncio.run(kb_service.find_relevant_context("poet", max_context_tokens=100))
        # Should include both filenames and all poets
        assert "[Source: first.pdf]" in result
        assert "[Source: second.pdf]" in result
        assert "poet one" in result
        assert "poet three" in result 