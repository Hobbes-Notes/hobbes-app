"""
Monitoring Service Layer

This module provides service-level functionality for monitoring system metrics,
including CapB performance and error tracking.
"""

import logging
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Service for monitoring system metrics and performance.
    
    This class handles tracking and persistence of various system metrics,
    including CapB performance, error rates, and processing times.
    """
    
    def __init__(self, metrics_dir: str = "metrics"):
        """
        Initialize the MonitoringService.
        
        Args:
            metrics_dir: Directory to store metrics files
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics storage
        self._metrics = {
            "capb": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "total_action_items_processed": 0,
                "total_action_items_tagged": 0,
                "average_processing_time": 0,
                "error_counts": {},
                "hourly_stats": {},
                "daily_stats": {}
            }
        }
        
        # Load existing metrics
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from disk."""
        try:
            metrics_file = self.metrics_dir / "capb_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    self._metrics["capb"] = json.load(f)
                logger.info("Loaded existing CapB metrics")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
    
    def _save_metrics(self):
        """Save current metrics to disk."""
        try:
            metrics_file = self.metrics_dir / "capb_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self._metrics["capb"], f, indent=2)
            logger.debug("Saved CapB metrics")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def update_capb_metrics(self, metrics: Dict[str, any]):
        """
        Update CapB metrics with new data.
        
        Args:
            metrics: Dictionary containing CapB metrics
        """
        try:
            # Update basic metrics
            self._metrics["capb"]["total_runs"] = metrics.get("total_runs", 0)
            self._metrics["capb"]["successful_runs"] = metrics.get("successful_runs", 0)
            self._metrics["capb"]["failed_runs"] = metrics.get("failed_runs", 0)
            self._metrics["capb"]["total_action_items_processed"] = metrics.get("total_action_items_processed", 0)
            self._metrics["capb"]["total_action_items_tagged"] = metrics.get("total_action_items_tagged", 0)
            self._metrics["capb"]["average_processing_time"] = metrics.get("average_processing_time", 0)
            
            # Update error counts
            for error_type, count in metrics.get("error_counts", {}).items():
                self._metrics["capb"]["error_counts"][error_type] = count
            
            # Update hourly stats
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            if current_hour not in self._metrics["capb"]["hourly_stats"]:
                self._metrics["capb"]["hourly_stats"][current_hour] = {
                    "runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "items_processed": 0,
                    "items_tagged": 0,
                    "errors": {}
                }
            
            hourly_stats = self._metrics["capb"]["hourly_stats"][current_hour]
            hourly_stats["runs"] += 1
            if metrics.get("success", False):
                hourly_stats["successful_runs"] += 1
            else:
                hourly_stats["failed_runs"] += 1
            hourly_stats["items_processed"] += metrics.get("total_action_items", 0)
            hourly_stats["items_tagged"] += metrics.get("tagged_action_items", 0)
            
            # Update error counts for this hour
            for error_type, count in metrics.get("error_counts", {}).items():
                hourly_stats["errors"][error_type] = hourly_stats["errors"].get(error_type, 0) + count
            
            # Update daily stats
            current_day = datetime.now().strftime("%Y-%m-%d")
            if current_day not in self._metrics["capb"]["daily_stats"]:
                self._metrics["capb"]["daily_stats"][current_day] = {
                    "runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "items_processed": 0,
                    "items_tagged": 0,
                    "errors": {}
                }
            
            daily_stats = self._metrics["capb"]["daily_stats"][current_day]
            daily_stats["runs"] += 1
            if metrics.get("success", False):
                daily_stats["successful_runs"] += 1
            else:
                daily_stats["failed_runs"] += 1
            daily_stats["items_processed"] += metrics.get("total_action_items", 0)
            daily_stats["items_tagged"] += metrics.get("tagged_action_items", 0)
            
            # Update error counts for this day
            for error_type, count in metrics.get("error_counts", {}).items():
                daily_stats["errors"][error_type] = daily_stats["errors"].get(error_type, 0) + count
            
            # Clean up old stats (keep last 7 days)
            cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            self._metrics["capb"]["daily_stats"] = {
                k: v for k, v in self._metrics["capb"]["daily_stats"].items()
                if k >= cutoff_date
            }
            
            # Save updated metrics
            self._save_metrics()
            
        except Exception as e:
            logger.error(f"Error updating CapB metrics: {e}")
    
    def get_capb_metrics(self, time_range: str = "all") -> Dict[str, any]:
        """
        Get CapB metrics for the specified time range.
        
        Args:
            time_range: Time range to get metrics for ("hour", "day", "week", "all")
            
        Returns:
            Dictionary containing CapB metrics for the specified time range
        """
        try:
            if time_range == "hour":
                current_hour = datetime.now().strftime("%Y-%m-%d-%H")
                return self._metrics["capb"]["hourly_stats"].get(current_hour, {})
            
            elif time_range == "day":
                current_day = datetime.now().strftime("%Y-%m-%d")
                return self._metrics["capb"]["daily_stats"].get(current_day, {})
            
            elif time_range == "week":
                cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                return {
                    k: v for k, v in self._metrics["capb"]["daily_stats"].items()
                    if k >= cutoff_date
                }
            
            else:  # "all"
                return self._metrics["capb"]
                
        except Exception as e:
            logger.error(f"Error getting CapB metrics: {e}")
            return {}
    
    def get_capb_error_rates(self, time_range: str = "day") -> Dict[str, float]:
        """
        Get CapB error rates for the specified time range.
        
        Args:
            time_range: Time range to get error rates for ("hour", "day", "week")
            
        Returns:
            Dictionary containing error rates by type
        """
        try:
            metrics = self.get_capb_metrics(time_range)
            total_runs = metrics.get("runs", 0)
            
            if total_runs == 0:
                return {}
            
            error_rates = {}
            for error_type, count in metrics.get("errors", {}).items():
                error_rates[error_type] = count / total_runs
            
            return error_rates
            
        except Exception as e:
            logger.error(f"Error getting CapB error rates: {e}")
            return {}
    
    def get_capb_success_rate(self, time_range: str = "day") -> float:
        """
        Get CapB success rate for the specified time range.
        
        Args:
            time_range: Time range to get success rate for ("hour", "day", "week")
            
        Returns:
            Success rate as a float between 0 and 1
        """
        try:
            metrics = self.get_capb_metrics(time_range)
            total_runs = metrics.get("runs", 0)
            
            if total_runs == 0:
                return 0.0
            
            return metrics.get("successful_runs", 0) / total_runs
            
        except Exception as e:
            logger.error(f"Error getting CapB success rate: {e}")
            return 0.0 