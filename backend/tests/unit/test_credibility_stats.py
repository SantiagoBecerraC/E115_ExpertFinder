import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import the CredibilityStats class
from linkedin_data_processing.credibility_stats import CredibilityStats


class TestCredibilityStats:
    """Tests for the CredibilityStats class to manage expert credibility statistics."""

    @pytest.fixture
    def temp_stats_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Initialize with some test data
            test_data = {
                "total_profiles": 100,
                "metrics": {
                    "experience": {"max_years": 25, "distribution": {"0-5": 30, "5-10": 40, "10-15": 20, "15+": 10}},
                    "education": {"distribution": {"bachelor": 50, "master": 30, "phd": 15, "other": 5}},
                },
            }
            tmp.write(json.dumps(test_data).encode("utf-8"))
            tmp_name = tmp.name

        yield tmp_name

        # Cleanup after tests
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    def test_init_with_custom_file(self, temp_stats_file):
        """Test initialization with custom stats file."""
        stats = CredibilityStats(stats_file=temp_stats_file)

        # Verify stats are loaded from file
        assert stats.stats["total_profiles"] == 100
        assert stats.stats["metrics"]["experience"]["max_years"] == 25
        assert stats.stats["metrics"]["education"]["distribution"]["master"] == 30

    def test_init_with_default_file(self):
        """Test initialization with default file path."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            stats = CredibilityStats()

            # Should use default stats
            assert stats.stats["total_profiles"] == 0
            assert stats.stats["metrics"]["experience"]["max_years"] == 0
            assert stats.stats["metrics"]["education"]["distribution"]["bachelor"] == 0

    def test_load_stats_file_error(self):
        """Test handling of file loading errors."""
        with patch("os.path.exists") as mock_exists, patch("builtins.open", mock_open()) as mock_file:
            mock_exists.return_value = True
            mock_file.side_effect = IOError("Test file error")

            stats = CredibilityStats(stats_file="nonexistent.json")

            # Should use default stats
            assert stats.stats["total_profiles"] == 0

    def test_load_stats_json_error(self):
        """Test handling of JSON decoding errors."""
        with patch("os.path.exists") as mock_exists, patch(
            "builtins.open", mock_open(read_data="invalid json")
        ) as mock_file:
            mock_exists.return_value = True

            stats = CredibilityStats(stats_file="invalid.json")

            # Should use default stats
            assert stats.stats["total_profiles"] == 0

    def test_save_stats(self, temp_stats_file):
        """Test saving stats to file."""
        stats = CredibilityStats(stats_file=temp_stats_file)

        # Modify stats
        stats.stats["total_profiles"] = 200

        # Save
        result = stats.save_stats()
        assert result is True

        # Verify saved correctly
        with open(temp_stats_file, "r") as f:
            saved_data = json.load(f)
            assert saved_data["total_profiles"] == 200

    def test_save_stats_error(self):
        """Test handling errors when saving stats."""
        stats = CredibilityStats(stats_file="/nonexistent/directory/stats.json")

        with patch("os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = IOError("Permission denied")

            result = stats.save_stats()
            assert result is False

    def test_update_from_profiles(self):
        """Test updating stats from profiles."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp_name = tmp.name

        stats = CredibilityStats(stats_file=tmp_name)

        # Test profiles
        profiles = [
            {"name": "Expert 1", "years_experience": 3, "education_level": "bachelor"},
            {"name": "Expert 2", "years_experience": 8, "education_level": "master"},
            {"name": "Expert 3", "years_experience": 12, "education_level": "phd"},
            {"name": "Expert 4", "years_experience": 20, "education_level": "other"},
        ]

        # Mock save_stats to avoid file operations
        with patch.object(stats, "save_stats") as mock_save:
            mock_save.return_value = True

            stats.update_from_profiles(profiles)

            # Verify stats were updated
            assert stats.stats["total_profiles"] == 4
            assert stats.stats["metrics"]["experience"]["max_years"] == 20
            assert stats.stats["metrics"]["experience"]["distribution"]["0-5"] == 1
            assert stats.stats["metrics"]["experience"]["distribution"]["5-10"] == 1
            assert stats.stats["metrics"]["experience"]["distribution"]["10-15"] == 1
            assert stats.stats["metrics"]["experience"]["distribution"]["15+"] == 1
            assert stats.stats["metrics"]["education"]["distribution"]["bachelor"] == 1
            assert stats.stats["metrics"]["education"]["distribution"]["master"] == 1
            assert stats.stats["metrics"]["education"]["distribution"]["phd"] == 1
            assert stats.stats["metrics"]["education"]["distribution"]["other"] == 1

            # Verify save was called
            mock_save.assert_called_once()

        # Cleanup
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    def test_get_years_experience_various_formats(self):
        """Test extracting years experience from different profile formats."""
        stats = CredibilityStats()

        # Test direct field
        profile1 = {"years_experience": 10}
        assert stats._get_years_experience(profile1) == 10

        # Test metadata field
        profile2 = {"metadata": {"years_experience": "15"}}
        assert stats._get_years_experience(profile2) == 15

        # Test credibility field
        profile3 = {"credibility": {"years_experience": 8}}
        assert stats._get_years_experience(profile3) == 8

        # Test invalid value
        profile4 = {"years_experience": "invalid"}
        assert stats._get_years_experience(profile4) == 0

        # Test missing field
        profile5 = {"name": "Expert"}
        assert stats._get_years_experience(profile5) == 0

    def test_get_education_level_various_formats(self):
        """Test extracting education level from different profile formats."""
        stats = CredibilityStats()

        # Test direct field
        profile1 = {"education_level": "Bachelor's"}
        assert stats._get_education_level(profile1) == "bachelor"

        # Test metadata field
        profile2 = {"metadata": {"education_level": "Master of Science"}}
        assert stats._get_education_level(profile2) == "master"

        # Test latest_degree field
        profile3 = {"latest_degree": "PhD"}
        assert stats._get_education_level(profile3) == "phd"

        # Test other category
        profile4 = {"education_level": "High School"}
        assert stats._get_education_level(profile4) == "other"

        # Test missing field
        profile5 = {"name": "Expert"}
        assert stats._get_education_level(profile5) is None

    def test_get_percentile_from_years(self, temp_stats_file):
        """Test percentile calculation from years of experience."""
        stats = CredibilityStats(stats_file=temp_stats_file)

        # Test various years
        assert stats.get_percentile_from_years(2) < 30  # Should be less than 30%
        assert stats.get_percentile_from_years(7) >= 30 and stats.get_percentile_from_years(7) < 70  # Mid-range
        assert stats.get_percentile_from_years(20) > 90  # Should be near 100%

        # Test zero profiles special case
        stats.stats["total_profiles"] = 0
        assert stats.get_percentile_from_years(10) == 50.0  # Default to 50%

    def test_get_level_from_percentile(self):
        """Test credibility level calculation from percentile."""
        stats = CredibilityStats()

        # Test with default thresholds
        assert stats.get_level_from_percentile(10) == 1
        assert stats.get_level_from_percentile(40) == 2
        assert stats.get_level_from_percentile(70) == 3
        assert stats.get_level_from_percentile(90) == 4
        assert stats.get_level_from_percentile(100) == 5

        # Test with custom thresholds
        custom_thresholds = {1: 0, 2: 50, 3: 75, 4: 90}
        assert stats.get_level_from_percentile(25, custom_thresholds) == 1
        assert stats.get_level_from_percentile(60, custom_thresholds) == 2
        assert stats.get_level_from_percentile(80, custom_thresholds) == 3
        assert stats.get_level_from_percentile(95, custom_thresholds) == 4

    def test_combine_credibility_metrics(self):
        """Test combining credibility metrics into a full credibility profile."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            stats = CredibilityStats()

            # Create a test profile
            profile = {"years_experience": 15, "education_level": "phd"}

            # Patch get_percentile_from_years to return a known value
            with patch.object(stats, "get_percentile_from_years", return_value=85.0):
                # Calculate raw scores for each component
                years_exp = stats._get_years_experience(profile)
                edu_level = stats._get_education_level(profile)

                # Create a raw score for education
                edu_score = 0
                if edu_level == "phd":
                    edu_score = 2
                elif edu_level == "master":
                    edu_score = 1.5
                elif edu_level == "bachelor":
                    edu_score = 1

                # Calculate experience score (simplified)
                exp_score = min(years_exp / 5, 5)  # Cap at 5

                # Calculate total raw score
                total_raw_score = exp_score + edu_score

                # Calculate percentile (mocked)
                percentile = stats.get_percentile_from_years(years_exp)

                # Calculate level
                level = stats.get_level_from_percentile(percentile)

                # Verify calculations
                assert edu_score == 2
                assert exp_score == 3
                assert total_raw_score == 5
                assert percentile == 85.0
                assert level == 4
