"""
app/modules/sentiment.py
Sentiment analysis using TextBlob
"""

from textblob import TextBlob


class SentimentAnalyzer:
    """
    Classifies each piece of feedback as Positive, Negative, or Neutral
    and returns polarity / subjectivity scores.
    """

    POSITIVE_THRESHOLD = 0.1
    NEGATIVE_THRESHOLD = -0.1

    def analyze(self, text: str) -> dict:
        """Analyse a single feedback string."""
        blob = TextBlob(text)
        polarity = round(blob.sentiment.polarity, 4)
        subjectivity = round(blob.sentiment.subjectivity, 4)
        label = self._classify(polarity)

        return {
            "text": text,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "label": label,
        }

    def analyze_batch(self, texts: list[str]) -> dict:
        """
        Analyse a list of feedback strings.
        Returns per-item results plus aggregated counts.
        """
        results = [self.analyze(t) for t in texts]

        counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for r in results:
            counts[r["label"]] += 1

        total = len(results)
        percentages = {
            k: round((v / total) * 100, 1) if total else 0
            for k, v in counts.items()
        }

        avg_polarity = round(
            sum(r["polarity"] for r in results) / total if total else 0, 4
        )

        return {
            "items": results,
            "counts": counts,
            "percentages": percentages,
            "average_polarity": avg_polarity,
            "total": total,
        }

    # ── private ─────────────────────────────────────────────────────────────

    def _classify(self, polarity: float) -> str:
        if polarity >= self.POSITIVE_THRESHOLD:
            return "Positive"
        if polarity <= self.NEGATIVE_THRESHOLD:
            return "Negative"
        return "Neutral"
