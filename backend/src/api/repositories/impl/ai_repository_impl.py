"""
AI Repository Implementation

This module provides an in-memory implementation of the AI repository interface.
"""

import logging
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
from decimal import Decimal

from ...repositories.ai_repository import AIRepository
from ...models.ai import AIConfiguration, AIUseCase
from ...config.default_ai_configs import DEFAULT_CONFIGS

# Set up logging
logger = logging.getLogger(__name__)

class AIRepositoryImpl(AIRepository):
    """
    Implementation of the AI repository with in-memory caching and DynamoDB persistence.
    """
    
    def __init__(self, table_name: str = "ai_configurations"):
        """
        Initialize the repository.
        """
        self._table_name = table_name
        self._cache: Dict[str, AIConfiguration] = {}
        self._active_cache: Dict[AIUseCase, AIConfiguration] = {}
        
        # Initialize DynamoDB
        self._init_dynamodb()
        
        # Initialize default configurations
        # self._init_default_configurations()
    
    def _init_dynamodb(self):
        """
        Initialize DynamoDB connection.
        """
        try:
            # Get region from environment or use default
            region = os.environ.get("AWS_REGION", "us-east-1")
            
            # Get endpoint URL for local development
            endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL") or os.environ.get("DYNAMODB_ENDPOINT")
            
            # Initialize DynamoDB resource
            kwargs = {"region_name": region}
            if endpoint_url:
                kwargs["endpoint_url"] = endpoint_url
            
            self._dynamodb = boto3.resource("dynamodb", **kwargs)
            self._table = self._dynamodb.Table(self._table_name)
            
            logger.info(f"Initialized DynamoDB connection to table: {self._table_name}")
        except Exception as e:
            logger.error(f"Error initializing DynamoDB: {str(e)}")
            # We'll continue with in-memory only
            self._dynamodb = None
            self._table = None
    
    async def create_table(self):
        """
        Create the DynamoDB table for AI configurations if it doesn't exist.
        """
        if not self._dynamodb:
            logger.warning("DynamoDB not initialized, skipping table creation")
            return
        
        try:
            # Check if table exists
            existing_tables = self._dynamodb.meta.client.list_tables()["TableNames"]
            
            if self._table_name not in existing_tables:
                logger.info(f"Creating table: {self._table_name}")
                
                # Create the table
                table = self._dynamodb.create_table(
                    TableName=self._table_name,
                    KeySchema=[
                        {"AttributeName": "PK", "KeyType": "HASH"},
                        {"AttributeName": "SK", "KeyType": "RANGE"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "PK", "AttributeType": "S"},
                        {"AttributeName": "SK", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST"
                )
                
                # Wait for table to be created
                table.meta.client.get_waiter("table_exists").wait(TableName=self._table_name)
                logger.info(f"Table created: {self._table_name}")
            else:
                logger.info(f"Table already exists: {self._table_name}")
                
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
    
    async def _init_default_configurations(self):
        """
        Initialize default configurations if they don't exist.
        """
        for use_case, config_data in DEFAULT_CONFIGS.items():
            # Check if we have any configurations for this use case
            configs = await self.get_all_configurations(use_case)
            
            if not configs:
                # Create default configuration
                config = AIConfiguration(
                    use_case=use_case,
                    version=1,  # Start with version 1
                    model=config_data["model"],
                    system_prompt=config_data["system_prompt"],
                    user_prompt_template=config_data["user_prompt_template"],
                    max_tokens=config_data["max_tokens"],
                    temperature=config_data["temperature"],
                    description=config_data["description"],
                    created_at=datetime.now().isoformat(),
                    is_active=True
                )
                
                await self.create_configuration(config)
                logger.info(f"Created default configuration for use case: {use_case}")
    
    def _configuration_to_item(self, configuration: AIConfiguration) -> Dict[str, Any]:
        """
        Convert a configuration to a DynamoDB item.
        """
        return {
            "PK": f"USECASE#{configuration.use_case}",
            "SK": f"VERSION#{configuration.version}",
            "use_case": configuration.use_case,
            "version": configuration.version,
            "model": configuration.model,
            "system_prompt": configuration.system_prompt,
            "user_prompt_template": configuration.user_prompt_template,
            "max_tokens": configuration.max_tokens,
            "temperature": Decimal(str(configuration.temperature)),
            "description": configuration.description or "",
            "created_at": configuration.created_at or datetime.now().isoformat(),
            "is_active": configuration.is_active
        }
    
    def _item_to_configuration(self, item: Dict[str, Any]) -> AIConfiguration:
        """
        Convert a DynamoDB item to a configuration.
        """
        return AIConfiguration(
            use_case=item["use_case"],
            version=int(item["version"]),
            model=item["model"],
            system_prompt=item["system_prompt"],
            user_prompt_template=item["user_prompt_template"],
            max_tokens=item["max_tokens"],
            temperature=item["temperature"],
            description=item.get("description", ""),
            created_at=item.get("created_at", datetime.now().isoformat()),
            is_active=item.get("is_active", False)
        )
    
    async def get_configuration(self, use_case: AIUseCase, version: int) -> Optional[AIConfiguration]:
        """
        Get a specific configuration by use case and version.
        """
        # Check cache first
        cache_key = f"{use_case}:{version}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # If DynamoDB is available, try to get from there
        if self._table:
            try:
                response = self._table.get_item(
                    Key={
                        "PK": f"USECASE#{use_case}",
                        "SK": f"VERSION#{version}"
                    }
                )
                
                if "Item" in response:
                    config = self._item_to_configuration(response["Item"])
                    self._cache[cache_key] = config
                    return config
            except Exception as e:
                logger.error(f"Error getting configuration from DynamoDB: {str(e)}")
        
        return None
    
    async def get_active_configuration(self, use_case: AIUseCase) -> AIConfiguration:
        """
        Get the active configuration for a use case.
        """
        # Check cache first
        if use_case in self._active_cache:
            return self._active_cache[use_case]
        
        # If DynamoDB is available, try to get from there
        if self._table:
            try:
                response = self._table.query(
                    KeyConditionExpression=Key("PK").eq(f"USECASE#{use_case}"),
                    FilterExpression=Attr("is_active").eq(True)
                )
                
                if response["Items"]:
                    config = self._item_to_configuration(response["Items"][0])
                    self._active_cache[use_case] = config
                    self._cache[f"{use_case}:{config.version}"] = config
                    return config
            except Exception as e:
                logger.error(f"Error getting active configuration from DynamoDB: {str(e)}")
        
        # If we get here, we need to create a default configuration
        config_data = DEFAULT_CONFIGS.get(use_case)
        if not config_data:
            raise ValueError(f"No default configuration available for use case: {use_case}")
        
        # Create a new configuration with the default values
        config = AIConfiguration(
            use_case=use_case,
            version=1,  # Start with version 1
            model=config_data["model"],
            system_prompt=config_data["system_prompt"],
            user_prompt_template=config_data["user_prompt_template"],
            max_tokens=config_data["max_tokens"],
            temperature=config_data["temperature"],
            description=config_data["description"],
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        
        # Create and return the configuration
        return await self.create_configuration(config)
    
    async def get_all_configurations(self, use_case: AIUseCase) -> List[AIConfiguration]:
        """
        Get all configurations for a use case.
        """
        configs = []
        
        # If DynamoDB is available, try to get from there
        if self._table:
            try:
                response = self._table.query(
                    KeyConditionExpression=Key("PK").eq(f"USECASE#{use_case}")
                )
                
                for item in response["Items"]:
                    config = self._item_to_configuration(item)
                    self._cache[f"{use_case}:{config.version}"] = config
                    if config.is_active:
                        self._active_cache[use_case] = config
                    configs.append(config)
            except Exception as e:
                logger.error(f"Error getting configurations from DynamoDB: {str(e)}")
        
        return configs
    
    async def create_configuration(self, configuration: AIConfiguration) -> AIConfiguration:
        """
        Create a new configuration.
        """
        # Always generate a new version
        configuration.version = await self._generate_new_version(configuration.use_case)
        
        # Set created_at if not provided
        if not configuration.created_at:
            configuration.created_at = datetime.now().isoformat()
        
        # If this is active, deactivate other configurations
        if configuration.is_active:
            await self._deactivate_other_configurations(configuration.use_case, configuration.version)
        
        # Update cache
        cache_key = f"{configuration.use_case}:{configuration.version}"
        self._cache[cache_key] = configuration
        
        if configuration.is_active:
            self._active_cache[configuration.use_case] = configuration
        
        # If DynamoDB is available, save there
        if self._table:
            try:
                item = self._configuration_to_item(configuration)
                self._table.put_item(Item=item)
            except Exception as e:
                logger.error(f"Error saving configuration to DynamoDB: {str(e)}")
        
        return configuration
    
    async def delete_configuration(self, use_case: AIUseCase, version: int) -> bool:
        """
        Delete a configuration.
        """
        # Check if configuration exists
        config = await self.get_configuration(use_case, version)
        if not config:
            return False
        
        # Cannot delete active configuration
        if config.is_active:
            return False
        
        # Remove from cache
        cache_key = f"{use_case}:{version}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # If DynamoDB is available, delete from there
        if self._table:
            try:
                self._table.delete_item(
                    Key={
                        "PK": f"USECASE#{use_case}",
                        "SK": f"VERSION#{version}"
                    }
                )
            except Exception as e:
                logger.error(f"Error deleting configuration from DynamoDB: {str(e)}")
                return False
        
        return True
    
    async def set_active_configuration(self, use_case: AIUseCase, version: int) -> AIConfiguration:
        """
        Set the active configuration for a use case.
        """
        # Check if configuration exists
        config = await self.get_configuration(use_case, version)
        if not config:
            raise ValueError(f"Configuration not found for use case: {use_case}, version: {version}")
        
        # If already active, just return it
        if config.is_active:
            return config
        
        # Set as active
        config.is_active = True
        
        # Deactivate other configurations
        await self._deactivate_other_configurations(use_case, version)
        
        # Update cache
        self._cache[f"{use_case}:{version}"] = config
        self._active_cache[use_case] = config
        
        # If DynamoDB is available, update there
        if self._table:
            try:
                self._table.update_item(
                    Key={
                        "PK": f"USECASE#{use_case}",
                        "SK": f"VERSION#{version}"
                    },
                    UpdateExpression="SET is_active = :is_active",
                    ExpressionAttributeValues={
                        ":is_active": True
                    }
                )
            except Exception as e:
                logger.error(f"Error updating configuration in DynamoDB: {str(e)}")
        
        return config
    
    async def _deactivate_other_configurations(self, use_case: AIUseCase, active_version: int):
        """
        Deactivate other configurations for a use case.
        """
        # Get all configurations for the use case
        configs = await self.get_all_configurations(use_case)
        
        for config in configs:
            if config.version != active_version and config.is_active:
                # Deactivate
                config.is_active = False
                
                # Update cache
                self._cache[f"{use_case}:{config.version}"] = config
                
                # If DynamoDB is available, update there
                if self._table:
                    try:
                        self._table.update_item(
                            Key={
                                "PK": f"USECASE#{use_case}",
                                "SK": f"VERSION#{config.version}"
                            },
                            UpdateExpression="SET is_active = :is_active",
                            ExpressionAttributeValues={
                                ":is_active": False
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error updating configuration in DynamoDB: {str(e)}")
    
    async def _generate_new_version(self, use_case: AIUseCase) -> int:
        """
        Generate a new version for a use case.
        
        Args:
            use_case: The use case to generate a new version for
            
        Returns:
            The new version number
        """
        # Get all configurations for the use case
        configs = await self.get_all_configurations(use_case)
        
        # Find the highest version
        highest_version = 0
        for config in configs:
            if config.version > highest_version:
                highest_version = config.version
        
        # Return the next version
        return highest_version + 1 