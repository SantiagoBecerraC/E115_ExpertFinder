"""
Unit tests for the credibility_system module.

This test suite verifies functionality of credibility_system.
"""

import datetime
import unittest
from unittest.mock import MagicMock, patch

from linkedin_data_processing.credibility_system import CredibilityMetric, EducationMetric, ExperienceMetric


class TestCredibilityMetrics(unittest.TestCase):
    """Tests for the credibility metrics in the credibility system module."""

    def test_experience_metric_with_total_years(self):
        """Test experience metric when total_years_experience is available."""
        metric = ExperienceMetric(weight=1.5)

        # Verify the initialization sets the name and weight correctly
        self.assertEqual(metric.name, "experience")
        self.assertEqual(metric.weight, 1.5)

        # Test with different year values
        self.assertEqual(metric.calculate_score({"total_years_experience": 20}), 3.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 15}), 3.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 12}), 2.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 10}), 2.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 7}), 1.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 5}), 1.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 3}), 0.0)
        self.assertEqual(metric.calculate_score({"total_years_experience": 0}), 0.0)

    def test_experience_metric_with_experiences_array(self):
        """Test experience metric when calculating from experiences array."""
        metric = ExperienceMetric()
        current_year = datetime.datetime.now().year

        # Test with multiple experiences
        data = {
            "experiences": [
                {"start_year": current_year - 5, "end_year": current_year},  # 5 years
                {"start_year": current_year - 10, "end_year": current_year - 5},  # 5 years
                {"start_year": current_year - 12, "end_year": current_year - 10},  # 2 years
            ]
        }
        # Total: 12 years, should return 2.0
        self.assertEqual(metric.calculate_score(data), 2.0)

        # Test with still current position (no end_year)
        data = {"experiences": [{"start_year": current_year - 6, "end_year": None}]}  # 6 years
        # 6 years, should return 1.0
        self.assertEqual(metric.calculate_score(data), 1.0)

        # Test with invalid year data
        data = {
            "experiences": [
                {"start_year": "invalid", "end_year": current_year},
                {"start_year": current_year - 3, "end_year": "invalid"},
            ]
        }
        # Invalid data should be skipped, only counting valid entries
        self.assertEqual(metric.calculate_score(data), 0.0)

        # Test with empty experiences array
        self.assertEqual(metric.calculate_score({"experiences": []}), 0.0)

        # Test with no experiences field
        self.assertEqual(metric.calculate_score({}), 0.0)

    def test_education_metric_with_education_level(self):
        """Test education metric when education_level is available."""
        metric = EducationMetric(weight=1.2)

        # Verify the initialization sets the name and weight correctly
        self.assertEqual(metric.name, "education")
        self.assertEqual(metric.weight, 1.2)

        # Test with different education levels
        self.assertEqual(metric.calculate_score({"education_level": "PhD"}), 3.0)
        self.assertEqual(metric.calculate_score({"education_level": "Doctor of Philosophy"}), 3.0)
        self.assertEqual(metric.calculate_score({"education_level": "Masters"}), 2.0)
        self.assertEqual(metric.calculate_score({"education_level": "Master of Science"}), 2.0)
        self.assertEqual(metric.calculate_score({"education_level": "Bachelor"}), 1.0)
        self.assertEqual(metric.calculate_score({"education_level": "BS in Computer Science"}), 1.0)
        self.assertEqual(metric.calculate_score({"education_level": "High School"}), 0.0)

    def test_education_metric_with_latest_degree(self):
        """Test education metric when latest_degree is available."""
        metric = EducationMetric()

        # Test with different degree values
        self.assertEqual(metric.calculate_score({"latest_degree": "PhD"}), 3.0)
        self.assertEqual(metric.calculate_score({"latest_degree": "Doctor of Engineering"}), 3.0)
        self.assertEqual(metric.calculate_score({"latest_degree": "Master's"}), 2.0)
        self.assertEqual(metric.calculate_score({"latest_degree": "Masters in Computer Science"}), 2.0)
        self.assertEqual(metric.calculate_score({"latest_degree": "Bachelor of Arts"}), 1.0)
        self.assertEqual(metric.calculate_score({"latest_degree": "Associates"}), 0.0)

    def test_education_metric_with_educations_array(self):
        """Test education metric when calculating from educations array."""
        metric = EducationMetric()

        # Test with multiple educations
        data = {
            "educations": [
                {"degree": "Bachelor of Science"},
                {"degree": "Master of Business Administration"},
                {"degree": "High School Diploma"},
            ]
        }
        # Highest is Masters, should return 2.0
        self.assertEqual(metric.calculate_score(data), 2.0)

        # Test with PhD
        data = {"educations": [{"degree": "Bachelor of Science"}, {"degree": "PhD in Computer Science"}]}
        # PhD is highest, should return 3.0
        self.assertEqual(metric.calculate_score(data), 3.0)

        # Test with only Bachelor's
        data = {"educations": [{"degree": "Bachelor of Arts"}, {"degree": "Associate's Degree"}]}
        # Bachelor's is highest, should return 1.0
        self.assertEqual(metric.calculate_score(data), 1.0)

        # Test with no degree field
        data = {"educations": [{"school": "University A"}, {"school": "University B", "field": "Computer Science"}]}
        # No degree specified, should return 0.0
        self.assertEqual(metric.calculate_score(data), 0.0)

        # Test with empty educations array
        self.assertEqual(metric.calculate_score({"educations": []}), 0.0)

        # Test with no educations field
        self.assertEqual(metric.calculate_score({}), 0.0)


if __name__ == "__main__":
    unittest.main()
