"""
Custom exceptions for the ML pipeline.
"""


class MLPipelineError(Exception):
    """Base exception for ML pipeline errors."""
    pass


class DataFetchError(MLPipelineError):
    """Raised when data fetching fails after retries."""
    
    def __init__(self, source: str, reason: str, status_code: int | None = None):
        self.source = source
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"Failed to fetch from {source}: {reason}")


class DataValidationError(MLPipelineError):
    """Raised when data fails schema or frequency validation."""
    
    def __init__(self, dataset: str, issues: list[str]):
        self.dataset = dataset
        self.issues = issues
        super().__init__(f"Validation failed for {dataset}: {', '.join(issues)}")


class ModelTrainingError(MLPipelineError):
    """Raised when model training fails."""
    
    def __init__(self, model_name: str, reason: str):
        self.model_name = model_name
        self.reason = reason
        super().__init__(f"Training failed for {model_name}: {reason}")


class ModelNotFoundError(MLPipelineError):
    """Raised when a champion model is not found in registry."""
    
    def __init__(self, asset: str):
        self.asset = asset
        super().__init__(f"No champion model found for asset: {asset}")
