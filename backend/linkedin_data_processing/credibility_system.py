from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from abc import ABC, abstractmethod

class CredibilityMetric(ABC):
    """Abstract base class for credibility metrics."""
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight
    
    @abstractmethod
    def calculate_score(self, data: dict) -> float:
        """Calculate the raw score for this metric."""
        pass

class ExperienceMetric(CredibilityMetric):
    """Metric for scoring based on years of experience."""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("experience", weight)
    
    def calculate_score(self, data: dict) -> float:
        """Calculate score based on years of experience."""
        # Use pre-calculated total_years_experience if available
        if 'total_years_experience' in data and data['total_years_experience']:
            years = float(data['total_years_experience'])
            
            if years >= 15: return 3.0
            if years >= 10: return 2.0
            if years >= 5: return 1.0
            return 0.0
        
        # Fallback to calculating manually from experiences
        years = 0.0
        if 'experiences' in data and data['experiences']:
            current_year = datetime.now().year
            
            for exp in data['experiences']:
                start_year = exp.get('start_year')
                end_year = exp.get('end_year', current_year)  # Use current year if still in position
                
                if start_year is not None:
                    try:
                        start_year = int(start_year)
                        end_year = int(end_year) if end_year is not None else current_year
                        years += end_year - start_year
                    except (ValueError, TypeError):
                        pass
        
        if years >= 15: return 3.0
        if years >= 10: return 2.0
        if years >= 5: return 1.0
        return 0.0

class EducationMetric(CredibilityMetric):
    """Metric for scoring based on education level."""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("education", weight)
    
    def calculate_score(self, data: dict) -> float:
        """Calculate score based on highest education level."""
        # Check if education_level is already available
        if 'education_level' in data:
            level = data['education_level'].lower()
            if 'phd' in level or 'doctor' in level:
                return 3.0
            elif 'master' in level:
                return 2.0
            elif 'bachelor' in level:
                return 1.0
            return 0.0
        
        # Look at the latest_degree field
        if 'latest_degree' in data:
            degree = data['latest_degree'].lower()
            if 'phd' in degree or 'doctor' in degree:
                return 3.0
            elif 'master' in degree:
                return 2.0
            elif 'bachelor' in degree:
                return 1.0
            return 0.0
        
        # Look through educations array if available
        highest_score = 0.0
        if 'educations' in data and data['educations']:
            for edu in data['educations']:
                if 'degree' in edu:
                    degree = edu['degree'].lower()
                    if 'phd' in degree or 'doctor' in degree:
                        highest_score = max(highest_score, 3.0)
                    elif 'master' in degree:
                        highest_score = max(highest_score, 2.0)
                    elif 'bachelor' in degree:
                        highest_score = max(highest_score, 1.0)
        
        return highest_score

class DynamicCredibilityCalculator:
    """Calculator for dynamic credibility scores based on percentiles."""
    
    def __init__(self):
        self.metrics: List[CredibilityMetric] = [
            ExperienceMetric(1.0),
            EducationMetric(1.0)
        ]
        
        self.percentile_thresholds = {
            5: 95,  # Top 5% get level 5
            4: 80,  # Next 15% get level 4
            3: 50,  # Next 30% get level 3
            2: 20,  # Next 30% get level 2
            1: 0    # Bottom 20% get level 1
        }
    
    def add_metric(self, metric: CredibilityMetric):
        """Add a new metric to the calculator."""
        self.metrics.append(metric)
    
    def calculate_raw_score(self, profile: dict) -> Dict[str, Any]:
        """Calculate raw scores for each metric and total."""
        metric_scores = {}
        total_score = 0.0
        
        for metric in self.metrics:
            score = metric.calculate_score(profile) * metric.weight
            metric_scores[metric.name] = score
            total_score += score
        
        # Get years of experience
        years_experience = 0
        if 'total_years_experience' in profile:
            years_experience = profile['total_years_experience']
        
        return {
            'total_raw_score': total_score,
            'metric_scores': metric_scores,
            'years_experience': years_experience
        }
    
    def get_percentile(self, score: float, all_scores: List[float]) -> float:
        """Calculate the percentile of a score within all scores."""
        if not all_scores:
            return 0.0
        
        # Handle the case where all scores are the same
        if len(set(all_scores)) == 1:
            # If all scores are the same, distribute percentiles evenly
            return 50.0  # Default to middle level (3)
        
        # Count how many scores are less than or equal to the given score
        count = sum(1 for s in all_scores if s <= score)
        
        # Calculate percentile
        percentile = (count / len(all_scores)) * 100.0
        return percentile
    
    def get_level_from_percentile(self, percentile: float) -> int:
        """Determine credibility level based on percentile."""
        for level in sorted(self.percentile_thresholds.keys(), reverse=True):
            if percentile >= self.percentile_thresholds[level]:
                return level
        return 1
    
    def process_profiles(self, profiles: List[dict]) -> List[dict]:
        """Process a batch of profiles and assign credibility levels."""
        # Calculate raw scores for all profiles
        profile_scores = [self.calculate_raw_score(profile) for profile in profiles]
        total_scores = [scores['total_raw_score'] for scores in profile_scores]
        
        # Handle the case where there are no profiles
        if not total_scores:
            return profiles
        
        # Assign levels and update profiles
        for profile, scores in zip(profiles, profile_scores):
            percentile = self.get_percentile(scores['total_raw_score'], total_scores)
            level = self.get_level_from_percentile(percentile)
            
            profile['credibility'] = {
                'raw_scores': scores['metric_scores'],
                'total_raw_score': scores['total_raw_score'],
                'percentile': percentile,
                'level': level,
                'years_experience': scores['years_experience']
            }
        
        return profiles