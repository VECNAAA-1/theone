"""
app/modules/theme_extractor.py
Topic / theme extraction using TF-IDF and frequency analysis
"""

from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class ThemeExtractor:
    """
    Extracts recurring themes, keywords, and topics from
    preprocessed customer feedback.
    """

    def __init__(self, top_n: int = 15, ngram_range: tuple = (1, 2)):
        self.top_n = top_n
        self.ngram_range = ngram_range

    # ── public API ──────────────────────────────────────────────────────────

    def extract(self, cleaned_texts: list[str]) -> dict:
        """
        Extract themes from preprocessed feedback texts.

        Returns:
            top_keywords  – top single words by frequency
            top_phrases   – top bi-grams by TF-IDF
            word_freq     – full word frequency table (for word cloud)
        """
        if not cleaned_texts or all(t.strip() == "" for t in cleaned_texts):
            return {"top_keywords": [], "top_phrases": [], "word_freq": {}}

        top_keywords = self._top_keywords(cleaned_texts)
        top_phrases = self._tfidf_phrases(cleaned_texts)
        word_freq = self._word_frequencies(cleaned_texts)

        return {
            "top_keywords": top_keywords,
            "top_phrases": top_phrases,
            "word_freq": word_freq,
        }

    # ── private helpers ─────────────────────────────────────────────────────

    def _word_frequencies(self, texts: list[str]) -> dict:
        """Count individual word occurrences across all texts."""
        all_words = " ".join(texts).split()
        counter = Counter(all_words)
        # Return top 50 for word cloud
        return dict(counter.most_common(50))

    def _top_keywords(self, texts: list[str]) -> list[dict]:
        """Return top N words sorted by frequency."""
        all_words = " ".join(texts).split()
        counter = Counter(all_words)
        return [
            {"word": word, "count": count}
            for word, count in counter.most_common(self.top_n)
        ]

    def _tfidf_phrases(self, texts: list[str]) -> list[dict]:
        """Extract top N phrases using TF-IDF (supports n-grams)."""
        valid = [t for t in texts if t.strip()]
        if len(valid) < 2:
            return []

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=self.ngram_range,
                max_features=200,
                min_df=1,
            )
            tfidf_matrix = vectorizer.fit_transform(valid)
            feature_names = vectorizer.get_feature_names_out()
            mean_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

            top_indices = mean_scores.argsort()[-self.top_n:][::-1]
            return [
                {"phrase": feature_names[i], "score": round(float(mean_scores[i]), 4)}
                for i in top_indices
            ]
        except Exception:
            return []
