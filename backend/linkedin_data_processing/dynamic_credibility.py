import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .credibility_stats import CredibilityStats
from .credibility_system import CredibilityMetric, EducationMetric, ExperienceMetric


class OnDemandCredibilityCalculator:
    """
    Calculator for on-demand credibility that references the entire database.
    Uses pre-computed statistics to calculate relative credibility.
    """

    def __init__(self, stats_file: str = None, percentile_thresholds: Dict[int, float] = None):
        """
        Initialize the calculator with optional parameters.

        Args:
            stats_file: Path to the stats file
            percentile_thresholds: Optional custom thresholds for levels
        """
        # Initialize metrics with default weights
        self.metrics: List[CredibilityMetric] = [ExperienceMetric(1.0), EducationMetric(1.0)]

        # Default percentile thresholds for levels
        self.percentile_thresholds = percentile_thresholds or {
            5: 95,  # Top 5% get level 5
            4: 80,  # Next 15% get level 4
            3: 50,  # Next 30% get level 3
            2: 20,  # Next 30% get level 2
            1: 0,  # Bottom 20% get level 1
        }

        # Initialize stats manager
        self.stats_manager = CredibilityStats(stats_file)

    def add_metric(self, metric: CredibilityMetric):
        """Add a new metric to the calculator."""
        self.metrics.append(metric)

    def calculate_raw_score(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate raw scores for each metric.

        Args:
            profile: Expert profile data

        Returns:
            Dict with raw scores and metadata
        """
        metric_scores = {}
        total_score = 0.0

        for metric in self.metrics:
            score = metric.calculate_score(profile) * metric.weight
            metric_scores[metric.name] = score
            total_score += score

        # Get years of experience
        years_experience = 0
        if "years_experience" in profile:
            try:
                years_experience = float(profile["years_experience"])
            except (ValueError, TypeError):
                pass
        elif "metadata" in profile and "years_experience" in profile["metadata"]:
            try:
                years_experience = float(profile["metadata"]["years_experience"])
            except (ValueError, TypeError):
                pass

        return {"total_raw_score": total_score, "metric_scores": metric_scores, "years_experience": years_experience}

    def calculate_credibility(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate credibility for a single profile using database-wide statistics.

        Args:
            profile: Expert profile to calculate credibility for

        Returns:
            Dict with credibility data
        """
        # Calculate raw scores
        scores = self.calculate_raw_score(profile)

        # Calculate percentile based on years of experience
        years = scores["years_experience"]
        percentile = self.stats_manager.get_percentile_from_years(years)

        # Determine level
        level = self.stats_manager.get_level_from_percentile(percentile, self.percentile_thresholds)

        # Return credibility data
        return {
            "raw_scores": scores["metric_scores"],
            "total_raw_score": scores["total_raw_score"],
            "percentile": percentile,
            "level": level,
            "years_experience": years,
        }

    def fetch_profiles_and_update_stats(self, chroma_collection=None):
        """
        Fetch all profiles from the database and update the statistics.
        This should be called periodically to keep stats up to date.

        Args:
            chroma_collection: Optional ChromaDB collection to use
                              (if None, will create a new connection)

        Returns:
            bool: True if successful
        """
        try:
            # Import here to avoid circular imports
            from utils.chroma_db_utils import ChromaDBManager

            # Create a new connection if not provided
            if chroma_collection is None:
                chroma_manager = ChromaDBManager(collection_name="linkedin")
                chroma_collection = chroma_manager.collection

            # Get all profiles (just metadata)
            results = chroma_collection.get(include=["metadatas"])

            if not results or not results["metadatas"]:
                print("No profiles found in collection")
                return False

            # Extract the profiles and update stats
            print(f"Updating credibility stats from {len(results['metadatas'])} profiles")
            self.stats_manager.update_from_profiles(results["metadatas"])
            return True

        except Exception as e:
            print(f"Error updating credibility stats: {e}")
            return False

    def update_stats_if_needed(self, force=False):
        """
        Check if stats file exists and update if needed.

        Args:
            force: Force update even if file exists

        Returns:
            bool: True if update was performed
        """
        if not os.path.exists(self.stats_manager.stats_file) or force:
            print("Credibility stats file not found or forced update requested")
            return self.fetch_profiles_and_update_stats()
        return False
