"""
Service for scanning PDF directory, extracting text, and retrieving relevant context.
"""

import os
import logging
import asyncio
import re
from typing import List, Dict

import fitz  # PyMuPDF
import tiktoken
from app.utils.config import MAX_CONTEXT_TOKENS


class KnowledgeBaseService:
    """
    Handles scanning PDFs in a directory, extracting their text, and finding relevant text chunks.
    """
    def __init__(self, pdf_data_dir: str):
        self.pdf_data_dir = pdf_data_dir
        self._text_cache: Dict[str, str] = {}
        if not os.path.isdir(self.pdf_data_dir):
            logging.error(f"Invalid PDF data directory: {self.pdf_data_dir}")
        else:
            logging.info(f"KnowledgeBaseService initialized with directory: {self.pdf_data_dir}")

    def _scan_pdf_files(self) -> List[str]:
        """
        Scans the configured directory for .pdf files.
        """
        pdfs: List[str] = []
        if not os.path.isdir(self.pdf_data_dir):
            logging.error(f"Cannot scan PDF files, directory does not exist: {self.pdf_data_dir}")
            return pdfs
        try:
            for entry in os.listdir(self.pdf_data_dir):
                path = os.path.join(self.pdf_data_dir, entry)
                if os.path.isfile(path) and entry.lower().endswith(".pdf"):
                    pdfs.append(path)
            logging.info(f"Found {len(pdfs)} PDF files in {self.pdf_data_dir}")
        except Exception as e:
            logging.error(f"Error scanning PDF directory {self.pdf_data_dir}: {e}")
        return pdfs

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts text content from a single PDF, with caching.
        """
        if pdf_path in self._text_cache:
            return self._text_cache[pdf_path]
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            logging.info(f"Extracted text from {pdf_path}")
        except Exception as e:
            logging.error(f"Error extracting text from {pdf_path}: {e}")
        self._text_cache[pdf_path] = text
        return text

    async def find_relevant_context(self, question: str, max_context_tokens: int = None, request_id: str = "") -> str:
        """
        Finds and returns relevant text chunks from PDFs based on the question.
        Aggregates from all PDFs, prefixes each chunk with its PDF filename, and truncates based on token count.
        """
        log_message = f"Performing PDF search for question: {question}"
        if request_id:
            log_message += f" | request_id={request_id}"
        logging.info(log_message)

        if max_context_tokens is None:
            max_context_tokens = MAX_CONTEXT_TOKENS

        # Use tiktoken encoding for gpt-4o-mini
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o")
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")

        pdf_files = await asyncio.to_thread(self._scan_pdf_files)
        keywords = set(re.findall(r"\w+", question.lower()))
        relevant_chunks = []
        chunk_token_counts = []

        # Collect all relevant chunks from all PDFs
        for pdf_path in pdf_files:
            try:
                text = await asyncio.to_thread(self._extract_text_from_pdf, pdf_path)
                chunks = text.split("\n\n")
                for chunk in chunks:
                    low = chunk.lower()
                    if any(word in low for word in keywords):
                        chunk_with_source = f"[Source: {os.path.basename(pdf_path)}]\n{chunk.strip()}"
                        tokens = len(encoding.encode(chunk_with_source))
                        relevant_chunks.append(chunk_with_source)
                        chunk_token_counts.append(tokens)
            except Exception as e:
                logging.error(f"Error processing PDF {pdf_path}: {e}")

        # Select chunks until token budget is reached
        selected_chunks = []
        total_tokens = 0
        for chunk, tokens in zip(relevant_chunks, chunk_token_counts):
            if total_tokens + tokens > max_context_tokens:
                logging.info(f"Context truncated at {total_tokens} tokens (limit: {max_context_tokens})")
                break
            selected_chunks.append(chunk)
            total_tokens += tokens

        result = "\n\n".join(selected_chunks)
        logging.info(f"Selected {len(selected_chunks)} chunks, total tokens: {total_tokens}")
        return result 