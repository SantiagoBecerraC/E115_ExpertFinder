import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class CredibilityStats:
    """
    Class to manage and store credibility statistics for the entire expert database.
    These statistics are used for calculating relative credibility scores.
    """

    def __init__(self, stats_file: str = None):
        """
        Initialize with an optional stats file path.

        Args:
            stats_file: Path to the JSON file storing the statistics
        """
        if stats_file is None:
            # Default location in the same directory as this file
            current_dir = Path(__file__).parent
            stats_file = current_dir / "credibility_stats.json"

        self.stats_file = stats_file
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        """Load statistics from the JSON file or return defaults if file doesn't exist."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading stats file: {e}")

        # Default stats if file doesn't exist or has errors
        return {
            "total_profiles": 0,
            "metrics": {
                "experience": {"max_years": 0, "distribution": {"0-5": 0, "5-10": 0, "10-15": 0, "15+": 0}},
                "education": {"distribution": {"bachelor": 0, "master": 0, "phd": 0, "other": 0}},
            },
        }

    def save_stats(self):
        """Save the current stats to the JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)

            with open(self.stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)

            print(f"Stats saved to {self.stats_file}")
            return True
        except IOError as e:
            print(f"Error saving stats file: {e}")
            return False

    def update_from_profiles(self, profiles: List[Dict[str, Any]]):
        """
        Update statistics based on a list of profiles.

        Args:
            profiles: List of expert profiles to analyze
        """
        # Update total profiles count
        self.stats["total_profiles"] = len(profiles)

        # Reset distributions
        self.stats["metrics"]["experience"]["distribution"] = {"0-5": 0, "5-10": 0, "10-15": 0, "15+": 0}
        self.stats["metrics"]["education"]["distribution"] = {"bachelor": 0, "master": 0, "phd": 0, "other": 0}

        # Maximum years of experience
        max_years = 0

        # Process each profile
        for profile in profiles:
            # Experience metrics
            years_exp = self._get_years_experience(profile)
            if years_exp > max_years:
                max_years = years_exp

            # Update experience distribution
            if years_exp < 5:
                self.stats["metrics"]["experience"]["distribution"]["0-5"] += 1
            elif years_exp < 10:
                self.stats["metrics"]["experience"]["distribution"]["5-10"] += 1
            elif years_exp < 15:
                self.stats["metrics"]["experience"]["distribution"]["10-15"] += 1
            else:
                self.stats["metrics"]["experience"]["distribution"]["15+"] += 1

            # Education metrics
            education_level = self._get_education_level(profile)
            if education_level:
                self.stats["metrics"]["education"]["distribution"][education_level] += 1

        # Update max years
        self.stats["metrics"]["experience"]["max_years"] = max_years

        # Save updated stats
        self.save_stats()

    def _get_years_experience(self, profile: Dict[str, Any]) -> float:
        """Extract years of experience from a profile."""
        # First check if it's already calculated
        if "years_experience" in profile and profile["years_experience"]:
            try:
                return float(profile["years_experience"])
            except (ValueError, TypeError):
                pass

        # Try metadata if this is from vector DB
        if "metadata" in profile and "years_experience" in profile["metadata"]:
            try:
                return float(profile["metadata"]["years_experience"])
            except (ValueError, TypeError):
                pass

        # For credibility field
        if "credibility" in profile and "years_experience" in profile["credibility"]:
            try:
                return float(profile["credibility"]["years_experience"])
            except (ValueError, TypeError):
                pass

        # Default to 0 if not found
        return 0.0

    def _get_education_level(self, profile: Dict[str, Any]) -> Optional[str]:
        """Extract education level from a profile."""
        education_level = None

        # Direct field
        if "education_level" in profile:
            education_level = profile["education_level"]
        # From metadata
        elif "metadata" in profile and "education_level" in profile["metadata"]:
            education_level = profile["metadata"]["education_level"]
        # From latest_degree
        elif "latest_degree" in profile:
            education_level = profile["latest_degree"]

        # Convert to standard categories
        if education_level:
            education_level = education_level.lower()
            if "phd" in education_level or "doctor" in education_level:
                return "phd"
            elif "master" in education_level:
                return "master"
            elif "bachelor" in education_level:
                return "bachelor"
            else:
                return "other"

        return None

    def get_percentile_from_years(self, years: float) -> float:
        """
        Calculate the percentile for years of experience.

        Args:
            years: Years of experience

        Returns:
            float: Percentile value (0-100)
        """
        # Use the distribution data to calculate percentile
        dist = self.stats["metrics"]["experience"]["distribution"]

        # If no data, return middle percentile
        if self.stats["total_profiles"] == 0:
            return 50.0

        # Calculate how many profiles have fewer years
        profiles_below = 0

        if years < 5:
            # Count portion of 0-5 bracket
            portion = years / 5.0  # What portion of the bracket
            profiles_below = dist["0-5"] * portion
        elif years < 10:
            # All in 0-5 bracket + portion of 5-10
            profiles_below = dist["0-5"] + (dist["5-10"] * (years - 5) / 5.0)
        elif years < 15:
            # All in 0-5 and 5-10 brackets + portion of 10-15
            profiles_below = dist["0-5"] + dist["5-10"] + (dist["10-15"] * (years - 10) / 5.0)
        else:
            # All lower brackets + portion of 15+ based on max years
            max_years = self.stats["metrics"]["experience"]["max_years"]
            if max_years <= 15:  # Avoid division by zero
                profiles_below = dist["0-5"] + dist["5-10"] + dist["10-15"]
            else:
                profiles_below = (
                    dist["0-5"]
                    + dist["5-10"]
                    + dist["10-15"]
                    + (dist["15+"] * min(1.0, (years - 15) / (max_years - 15)))
                )

        # Calculate percentile
        percentile = (profiles_below / self.stats["total_profiles"]) * 100.0
        return percentile

    def get_level_from_percentile(self, percentile: float, thresholds: Dict[int, float] = None) -> int:
        """
        Determine credibility level based on percentile.

        Args:
            percentile: The percentile value (0-100)
            thresholds: Optional custom thresholds dict {level: min_percentile}

        Returns:
            int: Credibility level (1-5)
        """
        if thresholds is None:
            # Default thresholds
            thresholds = {
                5: 95,  # Top 5% get level 5
                4: 80,  # Next 15% get level 4
                3: 50,  # Next 30% get level 3
                2: 20,  # Next 30% get level 2
                1: 0,  # Bottom 20% get level 1
            }

        for level in sorted(thresholds.keys(), reverse=True):
            if percentile >= thresholds[level]:
                return level

        return 1  # Default to lowest level
