"""Base workflow class for MASW 2D processing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional


class BaseWorkflow(ABC):
    """Abstract base class for MASW 2D workflows.
    
    Subclasses must implement the run() method.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize workflow with configuration.
        
        Parameters
        ----------
        config : dict
            Survey configuration dictionary
        """
        self.config = config
        self._progress_callback = None
    
    @property
    def name(self) -> str:
        """Workflow name."""
        return self.__class__.__name__
    
    @property
    def survey_name(self) -> str:
        """Survey name from config."""
        return self.config.get("survey_name", "Unnamed Survey")
    
    def set_progress_callback(
        self,
        callback: Optional[Callable[[int, int, str], None]]
    ) -> None:
        """Set progress callback function.
        
        Parameters
        ----------
        callback : callable
            Function(current, total, message) for progress updates
        """
        self._progress_callback = callback
    
    def _report_progress(self, current: int, total: int, message: str = "") -> None:
        """Report progress if callback is set."""
        if self._progress_callback:
            self._progress_callback(current, total, message)
    
    @abstractmethod
    def run(
        self,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the workflow.
        
        Parameters
        ----------
        output_dir : str, optional
            Override output directory from config
        
        Returns
        -------
        dict
            Summary of workflow execution including status, files, etc.
        """
        pass
    
    def validate(self) -> tuple:
        """Validate configuration for this workflow.
        
        Returns
        -------
        tuple
            (is_valid: bool, errors: list of str)
        """
        from ..config.schema import validate_config
        return validate_config(self.config)
    
    def __repr__(self) -> str:
        return f"{self.name}(survey='{self.survey_name}')"
