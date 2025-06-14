#!/usr/bin/env python3
"""
CapB Monitoring Script

This script monitors CapB's performance and health, providing insights into:
- Success rates
- Error rates
- Processing times
- Action item tagging statistics
"""

import sys
import os
import json
from datetime import datetime, timedelta
from tabulate import tabulate

# Add the backend src path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from api.repositories.impl import get_capb_service

def format_time_range(time_range: str) -> str:
    """Format time range for display."""
    if time_range == "hour":
        return "Last Hour"
    elif time_range == "day":
        return "Last 24 Hours"
    elif time_range == "week":
        return "Last 7 Days"
    else:
        return "All Time"

def format_percentage(value: float) -> str:
    """Format percentage for display."""
    return f"{value * 100:.1f}%"

def monitor_capb():
    """Monitor CapB's performance and health."""
    print("🔍 CapB Monitoring Dashboard")
    print("=" * 50)
    
    try:
        # Get CapB service
        capb_service = get_capb_service()
        
        # Monitor different time ranges
        time_ranges = ["hour", "day", "week", "all"]
        
        for time_range in time_ranges:
            print(f"\n📊 {format_time_range(time_range)}")
            print("-" * 30)
            
            # Get metrics
            metrics = capb_service.get_metrics(time_range)
            
            if not metrics:
                print("No data available for this time range")
                continue
            
            # Success rate
            success_rate = capb_service.get_success_rate(time_range)
            print(f"✅ Success Rate: {format_percentage(success_rate)}")
            
            # Error rates
            error_rates = capb_service.get_error_rates(time_range)
            if error_rates:
                print("\n⚠️  Error Rates:")
                error_table = []
                for error_type, rate in error_rates.items():
                    error_table.append([error_type, format_percentage(rate)])
                print(tabulate(error_table, headers=["Error Type", "Rate"], tablefmt="grid"))
            
            # Processing statistics
            print("\n⚡ Processing Statistics:")
            stats_table = [
                ["Total Runs", metrics.get("runs", 0)],
                ["Successful Runs", metrics.get("successful_runs", 0)],
                ["Failed Runs", metrics.get("failed_runs", 0)],
                ["Items Processed", metrics.get("items_processed", 0)],
                ["Items Tagged", metrics.get("items_tagged", 0)],
                ["Avg Processing Time", f"{metrics.get('average_processing_time', 0):.2f}s"]
            ]
            print(tabulate(stats_table, tablefmt="grid"))
            
            # Tagging efficiency
            items_processed = metrics.get("items_processed", 0)
            items_tagged = metrics.get("items_tagged", 0)
            if items_processed > 0:
                tagging_rate = items_tagged / items_processed
                print(f"\n🏷️  Tagging Efficiency: {format_percentage(tagging_rate)}")
            
            # Error breakdown
            if "errors" in metrics and metrics["errors"]:
                print("\n🔍 Error Breakdown:")
                error_table = []
                for error_type, count in metrics["errors"].items():
                    error_table.append([error_type, count])
                print(tabulate(error_table, headers=["Error Type", "Count"], tablefmt="grid"))
        
        print("\n" + "=" * 50)
        print("🏁 Monitoring Complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Error monitoring CapB: {e}")
        return False

if __name__ == "__main__":
    success = monitor_capb()
    sys.exit(0 if success else 1) 