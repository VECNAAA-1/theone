"""
app/modules/visualizer.py
Generates base64-encoded chart images for the dashboard
"""

import io
import base64
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from wordcloud import WordCloud


class Visualizer:
    """Creates all charts/graphs returned as base64 PNG strings."""

    COLORS = {
        "Positive": "#22c55e",
        "Neutral": "#f59e0b",
        "Negative": "#ef4444",
    }

    # ── public API ──────────────────────────────────────────────────────────

    def generate_all(self, sentiments: dict, themes: dict) -> dict:
        """Generate all charts and return as base64 strings."""
        return {
            "pie_chart": self._sentiment_pie(sentiments),
            "bar_chart": self._sentiment_bar(sentiments),
            "keyword_bar": self._keyword_bar(themes),
            "word_cloud": self._word_cloud(themes),
            "polarity_histogram": self._polarity_histogram(sentiments),
        }

    # ── chart builders ──────────────────────────────────────────────────────

    def _sentiment_pie(self, sentiments: dict) -> str:
        counts = sentiments.get("counts", {})
        labels = [k for k, v in counts.items() if v > 0]
        sizes = [counts[k] for k in labels]
        colors = [self.COLORS.get(k, "#94a3b8") for k in labels]

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=140,
            wedgeprops={"edgecolor": "white", "linewidth": 2},
        )
        ax.set_title("Sentiment Distribution", fontsize=14, fontweight="bold", pad=15)
        return self._to_base64(fig)

    def _sentiment_bar(self, sentiments: dict) -> str:
        counts = sentiments.get("counts", {})
        labels = list(counts.keys())
        values = list(counts.values())
        colors = [self.COLORS.get(k, "#94a3b8") for k in labels]

        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=1.5)
        ax.bar_label(bars, padding=3, fontsize=11)
        ax.set_title("Feedback Count by Sentiment", fontsize=14, fontweight="bold")
        ax.set_ylabel("Number of Feedback Items")
        ax.set_ylim(0, max(values, default=1) * 1.2)
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        return self._to_base64(fig)

    def _keyword_bar(self, themes: dict) -> str:
        keywords = themes.get("top_keywords", [])[:10]
        if not keywords:
            return ""

        words = [k["word"] for k in keywords]
        counts = [k["count"] for k in keywords]

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh(words[::-1], counts[::-1], color="#6366f1", edgecolor="white")
        ax.set_title("Top Keywords in Feedback", fontsize=14, fontweight="bold")
        ax.set_xlabel("Frequency")
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        return self._to_base64(fig)

    def _word_cloud(self, themes: dict) -> str:
        word_freq = themes.get("word_freq", {})
        if not word_freq:
            return ""

        wc = WordCloud(
            width=700,
            height=350,
            background_color="white",
            colormap="viridis",
            max_words=60,
        ).generate_from_frequencies(word_freq)

        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title("Feedback Word Cloud", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return self._to_base64(fig)

    def _polarity_histogram(self, sentiments: dict) -> str:
        items = sentiments.get("items", [])
        if not items:
            return ""

        polarities = [item["polarity"] for item in items]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(polarities, bins=20, color="#6366f1", edgecolor="white", alpha=0.85)
        ax.axvline(0, color="#ef4444", linestyle="--", linewidth=1.5, label="Neutral boundary")
        ax.set_title("Polarity Score Distribution", fontsize=14, fontweight="bold")
        ax.set_xlabel("Polarity Score")
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        return self._to_base64(fig)

    # ── utility ─────────────────────────────────────────────────────────────

    @staticmethod
    def _to_base64(fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
