"""
app/modules/preprocessor.py
Text cleaning and preprocessing pipeline
"""

import re
import string
import nltk

# Download required NLTK data (safe to call multiple times)
for pkg in ("stopwords", "punkt", "punkt_tab", "wordnet"):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer


class TextPreprocessor:
    """Cleans and normalises raw customer feedback text."""

    def __init__(self):
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()

    # ── public API ──────────────────────────────────────────────────────────

    def process(self, text: str) -> str:
        """Full preprocessing pipeline for a single string."""
        text = self._to_lowercase(text)
        text = self._remove_urls(text)
        text = self._remove_special_characters(text)
        tokens = self._tokenize(text)
        tokens = self._remove_stopwords(tokens)
        tokens = self._lemmatize(tokens)
        return " ".join(tokens)

    def process_batch(self, texts: list[str]) -> list[str]:
        """Process a list of feedback strings."""
        return [self.process(t) for t in texts]

    # ── private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _to_lowercase(text: str) -> str:
        return text.lower()

    @staticmethod
    def _remove_urls(text: str) -> str:
        return re.sub(r"http\S+|www\S+", "", text)

    @staticmethod
    def _remove_special_characters(text: str) -> str:
        # Keep letters, digits, and spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return word_tokenize(text)

    def _remove_stopwords(self, tokens: list[str]) -> list[str]:
        return [t for t in tokens if t not in self.stop_words and len(t) > 2]

    def _lemmatize(self, tokens: list[str]) -> list[str]:
        return [self.lemmatizer.lemmatize(t) for t in tokens]
