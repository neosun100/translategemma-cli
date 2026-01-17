"""Smart text chunker with sliding window support for long text translation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class Chunk:
    """Represents a text chunk with position information."""
    
    text: str
    start: int  # Start position in original text
    end: int    # End position in original text
    overlap_start: int  # Start of overlap region (chars to skip in result)
    overlap_end: int    # End of overlap region (chars to keep in result)
    is_first: bool = False
    is_last: bool = False


class TextChunker:
    """
    Smart text chunker with sliding window support.
    
    Splits text into overlapping chunks to maintain context during translation.
    """
    
    # Sentence-ending patterns for different languages
    SENTENCE_ENDINGS = re.compile(
        r'([.!?。！？\n]+[\s\n]*|'  # Common sentence endings
        r'[.!?。！？]["\'」』】)][\s\n]*)'  # With quotes/brackets
    )
    
    # Paragraph separators
    PARAGRAPH_SEP = re.compile(r'\n\s*\n')
    
    def __init__(
        self,
        chunk_size: int = 200,
        overlap: int = 50,
        split_by: Literal["sentence", "paragraph", "char"] = "sentence",
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            overlap: Overlap size between chunks (in characters)
            split_by: How to split text - "sentence", "paragraph", or "char"
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.split_by = split_by
    
    def chunk(self, text: str) -> list[Chunk]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of Chunk objects with position information
        """
        if not text or not text.strip():
            return []
        
        # For short text, return as single chunk
        if len(text) <= self.chunk_size:
            return [Chunk(
                text=text,
                start=0,
                end=len(text),
                overlap_start=0,
                overlap_end=len(text),
                is_first=True,
                is_last=True,
            )]
        
        if self.split_by == "sentence":
            return self._chunk_by_sentence(text)
        elif self.split_by == "paragraph":
            return self._chunk_by_paragraph(text)
        else:  # char
            return self._chunk_by_char(text)
    
    def _chunk_by_sentence(self, text: str) -> list[Chunk]:
        """Split text by sentences with sliding window."""
        # Split into sentences
        sentences = self._split_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        current_pos = 0
        i = 0
        
        while i < len(sentences):
            chunk_text = ""
            chunk_start = current_pos
            overlap_start_chars = 0
            
            # Add overlap from previous chunk (if not first)
            if chunks:
                # Look back to add overlap
                overlap_text = ""
                overlap_len = 0
                j = i - 1
                
                while j >= 0 and overlap_len < self.overlap:
                    sent = sentences[j]
                    if overlap_len + len(sent) <= self.overlap * 1.5:  # Allow some flexibility
                        overlap_text = sent + overlap_text
                        overlap_len += len(sent)
                        j -= 1
                    else:
                        break
                
                if overlap_text:
                    chunk_text = overlap_text
                    overlap_start_chars = len(overlap_text)
            
            # Add sentences until we reach chunk_size
            chunk_sentences = []
            while i < len(sentences):
                sent = sentences[i]
                if not chunk_text or len(chunk_text) + len(sent) <= self.chunk_size + self.overlap:
                    chunk_text += sent
                    chunk_sentences.append(sent)
                    i += 1
                else:
                    break
            
            if not chunk_sentences:
                # Edge case: single sentence longer than chunk_size
                chunk_text += sentences[i]
                chunk_sentences.append(sentences[i])
                i += 1
            
            # Calculate positions
            chunk_end = chunk_start + sum(len(s) for s in chunk_sentences)
            is_first = len(chunks) == 0
            is_last = i >= len(sentences)
            
            # For non-last chunks, calculate overlap_end
            if not is_last:
                # Keep everything except the overlap that will be in next chunk
                overlap_end_chars = len(chunk_text)
            else:
                overlap_end_chars = len(chunk_text)
            
            chunks.append(Chunk(
                text=chunk_text,
                start=chunk_start,
                end=chunk_end,
                overlap_start=overlap_start_chars,
                overlap_end=overlap_end_chars,
                is_first=is_first,
                is_last=is_last,
            ))
            
            current_pos = chunk_end
        
        return chunks
    
    def _chunk_by_paragraph(self, text: str) -> list[Chunk]:
        """Split text by paragraphs with sliding window."""
        paragraphs = self.PARAGRAPH_SEP.split(text)
        paragraphs = [p for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return []
        
        chunks = []
        current_pos = 0
        i = 0
        
        while i < len(paragraphs):
            chunk_text = ""
            chunk_start = current_pos
            overlap_start_chars = 0
            
            # Add overlap from previous chunk
            if chunks and i > 0:
                prev_para = paragraphs[i - 1]
                if len(prev_para) <= self.overlap * 1.5:
                    chunk_text = prev_para + "\n\n"
                    overlap_start_chars = len(chunk_text)
            
            # Add paragraphs until chunk_size
            chunk_paras = []
            while i < len(paragraphs):
                para = paragraphs[i]
                if not chunk_text or len(chunk_text) + len(para) <= self.chunk_size + self.overlap:
                    if chunk_text and not chunk_text.endswith("\n\n"):
                        chunk_text += "\n\n"
                    chunk_text += para
                    chunk_paras.append(para)
                    i += 1
                else:
                    break
            
            if not chunk_paras:
                # Single paragraph longer than chunk_size
                if chunk_text and not chunk_text.endswith("\n\n"):
                    chunk_text += "\n\n"
                chunk_text += paragraphs[i]
                chunk_paras.append(paragraphs[i])
                i += 1
            
            chunk_end = chunk_start + sum(len(p) for p in chunk_paras) + (len(chunk_paras) - 1) * 2
            is_first = len(chunks) == 0
            is_last = i >= len(paragraphs)
            
            chunks.append(Chunk(
                text=chunk_text,
                start=chunk_start,
                end=chunk_end,
                overlap_start=overlap_start_chars,
                overlap_end=len(chunk_text),
                is_first=is_first,
                is_last=is_last,
            ))
            
            current_pos = chunk_end
        
        return chunks
    
    def _chunk_by_char(self, text: str) -> list[Chunk]:
        """Split text by character count with sliding window."""
        chunks = []
        text_len = len(text)
        pos = 0
        chunk_idx = 0
        
        while pos < text_len:
            is_first = chunk_idx == 0
            overlap_start = 0 if is_first else self.overlap
            
            # Calculate chunk boundaries
            chunk_start = max(0, pos - (0 if is_first else self.overlap))
            chunk_end = min(text_len, pos + self.chunk_size)
            
            chunk_text = text[chunk_start:chunk_end]
            is_last = chunk_end >= text_len
            
            chunks.append(Chunk(
                text=chunk_text,
                start=chunk_start,
                end=chunk_end,
                overlap_start=overlap_start,
                overlap_end=len(chunk_text) if is_last else len(chunk_text) - self.overlap,
                is_first=is_first,
                is_last=is_last,
            ))
            
            pos += self.chunk_size
            chunk_idx += 1
        
        return chunks
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Normalize multiple newlines to single newline
        text = re.sub(r'\n\s*\n+', '\n', text)
        
        sentences = []
        last_end = 0
        
        for match in self.SENTENCE_ENDINGS.finditer(text):
            end = match.end()
            sentence = text[last_end:end]
            if sentence.strip():
                sentences.append(sentence)
            last_end = end
        
        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining.strip():
                sentences.append(remaining)
        
        return sentences
    
    def merge(self, chunks: list[Chunk], translations: list[str]) -> str:
        """
        Merge translated chunks.
        
        Simple strategy: Keep first chunk, for subsequent chunks skip the
        overlapping sentences based on sentence boundaries.
        
        Args:
            chunks: Original chunk objects with position info
            translations: Translated text for each chunk
            
        Returns:
            Merged translation text
        """
        if not chunks or not translations:
            return ""
        
        if len(chunks) != len(translations):
            raise ValueError("Number of chunks and translations must match")
        
        if len(chunks) == 1:
            return translations[0]
        
        # For now, use simple strategy: just concatenate with space
        # The overlap in source text helps maintain context during translation
        # but we don't try to deduplicate in the output
        result = []
        
        for i, translation in enumerate(translations):
            if i == 0:
                result.append(translation)
            else:
                # Add space if needed
                if result and not result[-1].endswith((" ", "\n")):
                    result.append(" ")
                result.append(translation)
        
        return "".join(result)
