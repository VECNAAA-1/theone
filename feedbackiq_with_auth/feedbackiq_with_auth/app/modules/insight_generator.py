"""
app/modules/insight_generator.py
Converts raw analysis results into human-readable business insights
"""


class InsightGenerator:
    """Generates actionable insights from sentiment and theme data."""

    def generate(
        self,
        sentiments: dict,
        themes: dict,
        raw_feedback: list[str],
    ) -> dict:
        """
        Build a structured insights report.

        Args:
            sentiments: output from SentimentAnalyzer.analyze_batch()
            themes:     output from ThemeExtractor.extract()
            raw_feedback: original unprocessed feedback list

        Returns:
            dict with summary, recommendations, highlights, and alerts
        """
        summary = self._build_summary(sentiments)
        highlights = self._build_highlights(sentiments, themes)
        recommendations = self._build_recommendations(sentiments, themes)
        alerts = self._build_alerts(sentiments)

        return {
            "summary": summary,
            "highlights": highlights,
            "recommendations": recommendations,
            "alerts": alerts,
            "total_analyzed": len(raw_feedback),
        }

    # ── private builders ────────────────────────────────────────────────────

    def _build_summary(self, sentiments: dict) -> str:
        counts = sentiments.get("counts", {})
        pct = sentiments.get("percentages", {})
        avg_pol = sentiments.get("average_polarity", 0)
        total = sentiments.get("total", 0)

        dominant = max(counts, key=lambda k: counts[k]) if counts else "Neutral"
        tone = (
            "generally positive"
            if avg_pol > 0.2
            else "mixed" if avg_pol > 0
            else "concerning"
        )

        return (
            f"Analysis of {total} feedback items shows a {tone} overall sentiment. "
            f"{pct.get('Positive', 0)}% of responses are positive, "
            f"{pct.get('Negative', 0)}% are negative, and "
            f"{pct.get('Neutral', 0)}% are neutral. "
            f"The dominant sentiment is {dominant} with an average polarity score of {avg_pol}."
        )

    def _build_highlights(self, sentiments: dict, themes: dict) -> list[str]:
        highlights = []

        # Top appreciated keywords
        keywords = themes.get("top_keywords", [])
        if keywords:
            top = ", ".join(k["word"] for k in keywords[:5])
            highlights.append(f"Most frequently mentioned topics: {top}.")

        # Top phrases
        phrases = themes.get("top_phrases", [])
        if phrases:
            top_p = ", ".join(p["phrase"] for p in phrases[:3])
            highlights.append(f"Key themes identified: {top_p}.")

        # Sentiment distribution
        pct = sentiments.get("percentages", {})
        if pct.get("Positive", 0) > 60:
            highlights.append("Strong positive reception — majority of customers are satisfied.")
        elif pct.get("Negative", 0) > 40:
            highlights.append("High negative feedback rate — immediate attention recommended.")

        return highlights

    def _build_recommendations(self, sentiments: dict, themes: dict) -> list[str]:
        recs = []
        counts = sentiments.get("counts", {})
        pct = sentiments.get("percentages", {})

        neg_pct = pct.get("Negative", 0)
        pos_pct = pct.get("Positive", 0)

        if neg_pct > 30:
            recs.append(
                "Investigate and address recurring complaints — over 30% of feedback is negative."
            )
        if pos_pct > 60:
            recs.append(
                "Leverage positive feedback in marketing to highlight customer satisfaction."
            )
        if pct.get("Neutral", 0) > 40:
            recs.append(
                "Follow up with neutral respondents — they may convert to loyal customers with engagement."
            )

        keywords = [k["word"] for k in themes.get("top_keywords", [])[:5]]
        if keywords:
            recs.append(
                f"Focus product/service improvements around key topics: {', '.join(keywords)}."
            )

        if not recs:
            recs.append("Continue monitoring feedback trends for emerging issues.")

        return recs

    def _build_alerts(self, sentiments: dict) -> list[str]:
        alerts = []
        pct = sentiments.get("percentages", {})

        if pct.get("Negative", 0) > 50:
            alerts.append(
                "🔴 CRITICAL: More than half of all feedback is negative. Urgent review needed."
            )
        elif pct.get("Negative", 0) > 30:
            alerts.append(
                "🟡 WARNING: Negative feedback exceeds 30%. Consider a dedicated response plan."
            )

        avg_pol = sentiments.get("average_polarity", 0)
        if avg_pol < -0.2:
            alerts.append(
                "🔴 CRITICAL: Average sentiment polarity is strongly negative."
            )

        return alerts
