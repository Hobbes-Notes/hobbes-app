"""
AI Repository Interface

This module defines the interface for AI configuration repositories.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from api.models.ai import AIConfiguration, AIUseCase

class AIRepository(ABC):
    """
    Repository interface for AI configurations.
    """
    
    @abstractmethod
    async def get_configuration(self, use_case: AIUseCase, version: int) -> Optional[AIConfiguration]:
        """
        Get a specific configuration by use case and version.
        
        Args:
            use_case: The use case to get the configuration for
            version: The version of the configuration
            
        Returns:
            The configuration if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_active_configuration(self, use_case: AIUseCase) -> AIConfiguration:
        """
        Get the active configuration for a use case.
        If no active configuration exists, a default one will be created.
        
        Args:
            use_case: The use case to get the configuration for
            
        Returns:
            The active configuration (never null)
        """
        pass
    
    @abstractmethod
    async def get_all_configurations(self, use_case: AIUseCase) -> List[AIConfiguration]:
        """
        Get all configurations for a use case.
        
        Args:
            use_case: The use case to get configurations for
            
        Returns:
            List of configurations for the use case
        """
        pass
    
    @abstractmethod
    async def create_configuration(self, configuration: AIConfiguration) -> AIConfiguration:
        """
        Create a new configuration.
        
        Args:
            configuration: The configuration to create
            
        Returns:
            The created configuration
        """
        pass
    
    @abstractmethod
    async def delete_configuration(self, use_case: AIUseCase, version: int) -> bool:
        """
        Delete a configuration.
        
        Args:
            use_case: The use case of the configuration
            version: The version of the configuration
            
        Returns:
            True if the configuration was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def set_active_configuration(self, use_case: AIUseCase, version: int) -> AIConfiguration:
        """
        Set the active configuration for a use case.
        
        Args:
            use_case: The use case to set the configuration for
            version: The version of the configuration
            
        Returns:
            The set configuration
        """
        pass 