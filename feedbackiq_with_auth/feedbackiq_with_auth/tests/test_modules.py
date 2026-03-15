"""
tests/test_modules.py
Unit tests for the core NLP modules
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.modules.preprocessor import TextPreprocessor
from app.modules.sentiment import SentimentAnalyzer
from app.modules.theme_extractor import ThemeExtractor
from app.modules.insight_generator import InsightGenerator


SAMPLE_FEEDBACK = [
    "The product quality is amazing! Very satisfied.",
    "Delivery was extremely slow and packaging was damaged.",
    "Average experience, nothing special.",
    "Great customer support, resolved my issue quickly!",
    "The app keeps crashing. Very frustrating.",
]


# ── Preprocessor ─────────────────────────────────────────────────────────────

class TestTextPreprocessor:
    def setup_method(self):
        self.pp = TextPreprocessor()

    def test_lowercase(self):
        assert self.pp.process("HELLO WORLD") == self.pp.process("hello world")

    def test_url_removed(self):
        result = self.pp.process("Visit https://example.com for more info")
        assert "http" not in result

    def test_special_chars_removed(self):
        result = self.pp.process("Hello!!! @#$ World???")
        for ch in "!@#$?":
            assert ch not in result

    def test_batch_returns_same_length(self):
        cleaned = self.pp.process_batch(SAMPLE_FEEDBACK)
        assert len(cleaned) == len(SAMPLE_FEEDBACK)


# ── Sentiment Analyzer ────────────────────────────────────────────────────────

class TestSentimentAnalyzer:
    def setup_method(self):
        self.sa = SentimentAnalyzer()

    def test_positive_label(self):
        result = self.sa.analyze("This is absolutely wonderful and amazing!")
        assert result["label"] == "Positive"

    def test_negative_label(self):
        result = self.sa.analyze("This is terrible and completely broken garbage.")
        assert result["label"] == "Negative"

    def test_polarity_range(self):
        result = self.sa.analyze("The product is okay.")
        assert -1.0 <= result["polarity"] <= 1.0

    def test_batch_counts_sum(self):
        result = self.sa.analyze_batch(SAMPLE_FEEDBACK)
        counts = result["counts"]
        assert sum(counts.values()) == len(SAMPLE_FEEDBACK)

    def test_batch_total_field(self):
        result = self.sa.analyze_batch(SAMPLE_FEEDBACK)
        assert result["total"] == len(SAMPLE_FEEDBACK)


# ── Theme Extractor ───────────────────────────────────────────────────────────

class TestThemeExtractor:
    def setup_method(self):
        self.te = ThemeExtractor()
        pp = TextPreprocessor()
        self.cleaned = pp.process_batch(SAMPLE_FEEDBACK)

    def test_returns_top_keywords(self):
        result = self.te.extract(self.cleaned)
        assert "top_keywords" in result
        assert isinstance(result["top_keywords"], list)

    def test_returns_word_freq(self):
        result = self.te.extract(self.cleaned)
        assert "word_freq" in result
        assert isinstance(result["word_freq"], dict)

    def test_empty_input(self):
        result = self.te.extract([])
        assert result["top_keywords"] == []

    def test_keyword_has_count(self):
        result = self.te.extract(self.cleaned)
        for kw in result["top_keywords"]:
            assert "word" in kw and "count" in kw


# ── Insight Generator ─────────────────────────────────────────────────────────

class TestInsightGenerator:
    def setup_method(self):
        self.ig = InsightGenerator()
        sa = SentimentAnalyzer()
        te = ThemeExtractor()
        pp = TextPreprocessor()
        self.sentiments = sa.analyze_batch(SAMPLE_FEEDBACK)
        self.themes = te.extract(pp.process_batch(SAMPLE_FEEDBACK))

    def test_summary_is_string(self):
        insights = self.ig.generate(self.sentiments, self.themes, SAMPLE_FEEDBACK)
        assert isinstance(insights["summary"], str)
        assert len(insights["summary"]) > 0

    def test_recommendations_list(self):
        insights = self.ig.generate(self.sentiments, self.themes, SAMPLE_FEEDBACK)
        assert isinstance(insights["recommendations"], list)
        assert len(insights["recommendations"]) > 0

    def test_alerts_list(self):
        insights = self.ig.generate(self.sentiments, self.themes, SAMPLE_FEEDBACK)
        assert isinstance(insights["alerts"], list)

    def test_total_analyzed(self):
        insights = self.ig.generate(self.sentiments, self.themes, SAMPLE_FEEDBACK)
        assert insights["total_analyzed"] == len(SAMPLE_FEEDBACK)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
