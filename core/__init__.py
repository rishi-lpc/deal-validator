"""
Core validation package for deal validation.
"""
from .json_driven_validator import JSONValidator
from .salesforce_fetcher import SalesforceFetcher

__all__ = ['JSONValidator', 'SalesforceFetcher']
