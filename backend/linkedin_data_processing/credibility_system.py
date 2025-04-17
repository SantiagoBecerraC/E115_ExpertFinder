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
