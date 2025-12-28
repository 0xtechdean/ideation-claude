"""Tests for utility functions."""

import pytest


class TestUtilityFunctions:
    """Tests for various utility functions."""

    def test_score_extraction_patterns(self):
        """Test score extraction regex patterns."""
        import re
        
        patterns = [
            r"\*\*TOTAL\*\*[:\s]*\*\*(\d+\.?\d*)/10\*\*",
            r"TOTAL[:\s]*(\d+\.?\d*)/10",
            r"Total Score[:\s]*(\d+\.?\d*)",
            r"Score[:\s]*(\d+\.?\d*)/10",
        ]
        
        test_cases = [
            ("**TOTAL**: **6.5/10**", 6.5),
            ("TOTAL: 7.0/10", 7.0),
            ("Total Score: 8.5", 8.5),
            ("Score: 5.0/10", 5.0),
        ]
        
        for text, expected_score in test_cases:
            found = False
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    score = float(match.group(1))
                    assert score == expected_score
                    found = True
                    break
            assert found, f"Pattern not found for: {text}"

    def test_elimination_detection(self):
        """Test elimination keyword detection."""
        elimination_keywords = ["ELIMINATE", "eliminate", "ELIMINATED"]
        
        for keyword in elimination_keywords:
            assert keyword.upper() in "ELIMINATE"
        
        assert "PASS" not in "ELIMINATE"

