"""Language detection for translation."""

from __future__ import annotations

import regex
from typing import Literal

from .config import SUPPORTED_LANGUAGES, CJK_LANGUAGES, DEFAULT_LANGUAGES

# Pattern for Han characters (CJK Unified Ideographs + Extensions)
HAN_PATTERN = regex.compile(r'[\p{Han}]')

# Pattern for Latin alphabet characters
LATIN_PATTERN = regex.compile(r'[a-zA-Z]')

# Pattern for Japanese Hiragana/Katakana
JAPANESE_PATTERN = regex.compile(r'[\p{Hiragana}\p{Katakana}]')

# Pattern for Korean Hangul
KOREAN_PATTERN = regex.compile(r'[\p{Hangul}]')

# Pattern for Arabic script
ARABIC_PATTERN = regex.compile(r'[\p{Arabic}]')

# Pattern for Devanagari (Hindi, Marathi, etc.)
DEVANAGARI_PATTERN = regex.compile(r'[\p{Devanagari}]')

# Pattern for Thai
THAI_PATTERN = regex.compile(r'[\p{Thai}]')

# Pattern for Cyrillic (Russian, Ukrainian, etc.)
CYRILLIC_PATTERN = regex.compile(r'[\p{Cyrillic}]')


def detect_script_language(text: str) -> str | None:
    """
    Detect language based on script patterns.
    
    Returns the most likely language code based on character scripts,
    or None if detection is ambiguous.
    """
    if not text or not text.strip():
        return None
    
    # Count character types
    han_count = len(HAN_PATTERN.findall(text))
    latin_count = len(LATIN_PATTERN.findall(text))
    japanese_count = len(JAPANESE_PATTERN.findall(text))
    korean_count = len(KOREAN_PATTERN.findall(text))
    arabic_count = len(ARABIC_PATTERN.findall(text))
    devanagari_count = len(DEVANAGARI_PATTERN.findall(text))
    thai_count = len(THAI_PATTERN.findall(text))
    cyrillic_count = len(CYRILLIC_PATTERN.findall(text))
    
    # Japanese detection (has Hiragana/Katakana)
    if japanese_count > 0:
        return "ja"
    
    # Korean detection (has Hangul)
    if korean_count > 0:
        return "ko"
    
    # Arabic script
    if arabic_count > 5:
        return "ar"
    
    # Devanagari script (Hindi by default)
    if devanagari_count > 5:
        return "hi"
    
    # Thai script
    if thai_count > 5:
        return "th"
    
    # Cyrillic script (Russian by default)
    if cyrillic_count > 5:
        return "ru"
    
    # Chinese (Han characters without Japanese kana)
    if han_count > 0:
        total = han_count + latin_count
        if total > 0 and han_count / total > 0.3:
            # Default to Cantonese for this CLI's primary use case
            # Could be zh or yue - use yue as default for this CLI
            return "yue"
    
    # Latin script (default to English)
    if latin_count > 0:
        return "en"
    
    return None


def detect_language(text: str, configured_langs: tuple[str, str] | None = None) -> str:
    """
    Detect whether input belongs to the first or second language in the configured pair.
    
    For yue ↔ en (default):
    - Han characters → yue
    - Latin characters → en
    
    Args:
        text: Input text to analyze
        configured_langs: Language pair tuple (lang1, lang2). Defaults to config.
        
    Returns:
        Language code from the configured pair
    """
    if configured_langs is None:
        configured_langs = DEFAULT_LANGUAGES
    
    lang1, lang2 = configured_langs
    
    if not text or not text.strip():
        return lang2  # Default to second language for empty input
    
    # Detect based on script
    detected = detect_script_language(text)
    
    if detected is None:
        return lang2  # Default to second language
    
    # Map detected script to configured language pair
    # Check if detected language is CJK
    if detected in CJK_LANGUAGES:
        # Return whichever language in the pair is CJK
        if lang1 in CJK_LANGUAGES:
            return lang1
        elif lang2 in CJK_LANGUAGES:
            return lang2
        else:
            return lang1  # Fallback
    else:
        # Non-CJK detected - return whichever language in pair is non-CJK
        if lang1 not in CJK_LANGUAGES:
            return lang1
        elif lang2 not in CJK_LANGUAGES:
            return lang2
        else:
            return lang2  # Fallback
    
    return detected if detected in (lang1, lang2) else lang1


def get_target_language(source: str, configured_langs: tuple[str, str] | None = None) -> str:
    """
    Return the opposite language in the configured pair.
    
    Args:
        source: Source language code
        configured_langs: Language pair tuple (lang1, lang2). Defaults to config.
        
    Returns:
        Target language code (opposite of source in the pair)
    """
    if configured_langs is None:
        configured_langs = DEFAULT_LANGUAGES
    
    lang1, lang2 = configured_langs
    
    if source == lang1:
        return lang2
    elif source == lang2:
        return lang1
    else:
        # Source not in pair - return second language as default target
        return lang2


def format_language_indicator(source: str, target: str) -> str:
    """
    Format a human-readable language direction indicator.
    
    Args:
        source: Source language code
        target: Target language code
        
    Returns:
        Formatted string like "[yue→en]"
    """
    return f"[{source}→{target}]"


def get_language_name(code: str) -> str:
    """
    Get human-readable language name.
    
    Args:
        code: Language code
        
    Returns:
        Human-readable name
    """
    return SUPPORTED_LANGUAGES.get(code, code)


def is_valid_language(code: str) -> bool:
    """Check if a language code is supported."""
    return code in SUPPORTED_LANGUAGES


def list_languages() -> dict[str, str]:
    """Return all supported languages as {code: name} dict."""
    return SUPPORTED_LANGUAGES.copy()
