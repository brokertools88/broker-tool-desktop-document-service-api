"""
Date and time utility functions.

This module provides helper functions for date/time operations, formatting, and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import pytz
import logging

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    TODO:
    - Add timezone configuration support
    - Implement custom time providers for testing
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    TODO:
    - Add locale-specific formatting
    - Implement relative time formatting (e.g., "2 hours ago")
    - Add timezone-aware formatting
    """
    return dt.strftime(format_string)


def parse_datetime(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse datetime string.
    
    TODO:
    - Add multiple format support with fallbacks
    - Implement automatic format detection
    - Add timezone parsing support
    """
    try:
        return datetime.strptime(date_string, format_string)
    except ValueError as e:
        logger.error(f"Failed to parse datetime: {date_string}, error: {str(e)}")
        raise


def convert_timezone(dt: datetime, target_timezone: str) -> datetime:
    """
    Convert datetime to target timezone.
    
    TODO:
    - Add timezone validation
    - Implement timezone caching
    - Add daylight saving time handling
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    target_tz = pytz.timezone(target_timezone)
    return dt.astimezone(target_tz)


def to_iso_format(dt: datetime) -> str:
    """
    Convert datetime to ISO format string.
    
    TODO:
    - Add microsecond precision control
    - Implement timezone offset formatting
    """
    return dt.isoformat()


def from_iso_format(iso_string: str) -> datetime:
    """
    Parse datetime from ISO format string.
    
    TODO:
    - Add error handling for malformed strings
    - Implement timezone parsing
    """
    return datetime.fromisoformat(iso_string)


def add_time(dt: datetime, **kwargs) -> datetime:
    """
    Add time to datetime using keyword arguments.
    
    Args:
        dt: Base datetime
        **kwargs: Time units (days, hours, minutes, seconds, etc.)
    
    TODO:
    - Add business day calculations
    - Implement holiday awareness
    - Add timezone-aware calculations
    """
    delta = timedelta(**kwargs)
    return dt + delta


def subtract_time(dt: datetime, **kwargs) -> datetime:
    """
    Subtract time from datetime using keyword arguments.
    
    TODO:
    - Add business day calculations
    - Implement holiday awareness
    """
    delta = timedelta(**kwargs)
    return dt - delta


def time_difference(dt1: datetime, dt2: datetime) -> timedelta:
    """
    Calculate time difference between two datetimes.
    
    TODO:
    - Add absolute difference option
    - Implement business day difference
    - Add human-readable difference formatting
    """
    return dt1 - dt2


def is_past(dt: datetime) -> bool:
    """
    Check if datetime is in the past.
    
    TODO:
    - Add timezone-aware comparison
    - Implement configurable time tolerance
    """
    return dt < get_utc_now()


def is_future(dt: datetime) -> bool:
    """
    Check if datetime is in the future.
    
    TODO:
    - Add timezone-aware comparison
    - Implement configurable time tolerance
    """
    return dt > get_utc_now()


def is_within_range(dt: datetime, start: datetime, end: datetime) -> bool:
    """
    Check if datetime is within a range.
    
    TODO:
    - Add inclusive/exclusive range options
    - Implement timezone handling
    """
    return start <= dt <= end


def get_start_of_day(dt: datetime) -> datetime:
    """
    Get start of day (00:00:00) for given datetime.
    
    TODO:
    - Add timezone preservation
    - Implement custom day start time
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(dt: datetime) -> datetime:
    """
    Get end of day (23:59:59) for given datetime.
    
    TODO:
    - Add timezone preservation
    - Implement custom day end time
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_start_of_month(dt: datetime) -> datetime:
    """
    Get first day of month for given datetime.
    
    TODO:
    - Add timezone preservation
    - Implement business month logic
    """
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_end_of_month(dt: datetime) -> datetime:
    """
    Get last day of month for given datetime.
    
    TODO:
    - Add timezone preservation
    - Implement business month logic
    """
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    
    last_day = next_month - timedelta(days=1)
    return get_end_of_day(last_day)


def get_weekday_name(dt: datetime) -> str:
    """
    Get weekday name for datetime.
    
    TODO:
    - Add locale-specific day names
    - Implement abbreviated names option
    """
    return dt.strftime("%A")


def get_month_name(dt: datetime) -> str:
    """
    Get month name for datetime.
    
    TODO:
    - Add locale-specific month names
    - Implement abbreviated names option
    """
    return dt.strftime("%B")


def is_weekend(dt: datetime) -> bool:
    """
    Check if datetime falls on weekend.
    
    TODO:
    - Add configurable weekend days
    - Implement culture-specific weekends
    """
    return dt.weekday() >= 5  # Saturday = 5, Sunday = 6


def is_business_day(dt: datetime, holidays: Optional[list] = None) -> bool:
    """
    Check if datetime is a business day.
    
    TODO:
    - Implement holiday calendar integration
    - Add country-specific business days
    - Implement custom business day rules
    """
    if is_weekend(dt):
        return False
    
    if holidays:
        date_only = dt.date()
        return date_only not in holidays
    
    return True


def get_age(birth_date: datetime, reference_date: Optional[datetime] = None) -> int:
    """
    Calculate age in years.
    
    TODO:
    - Add precision options (months, days)
    - Implement timezone handling
    - Add leap year handling
    """
    if reference_date is None:
        reference_date = get_utc_now()
    
    age = reference_date.year - birth_date.year
    
    # Check if birthday has occurred this year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age


def format_duration(delta: timedelta) -> str:
    """
    Format timedelta as human-readable duration.
    
    TODO:
    - Add localization support
    - Implement precision control
    - Add short/long format options
    """
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minutes"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hours"
    else:
        days = total_seconds // 86400
        return f"{days} days"


def get_relative_time(dt: datetime, reference_dt: Optional[datetime] = None) -> str:
    """
    Get relative time description (e.g., "2 hours ago", "in 3 days").
    
    TODO:
    - Add localization support
    - Implement precision control
    - Add threshold customization
    """
    if reference_dt is None:
        reference_dt = get_utc_now()
    
    delta = reference_dt - dt
    
    if delta.total_seconds() > 0:
        # Past
        return f"{format_duration(delta)} ago"
    else:
        # Future
        return f"in {format_duration(-delta)}"


def generate_time_range(
    start: datetime, 
    end: datetime, 
    interval: timedelta
) -> list[datetime]:
    """
    Generate list of datetimes between start and end with given interval.
    
    TODO:
    - Add business day filtering
    - Implement timezone handling
    - Add generator version for memory efficiency
    """
    times = []
    current = start
    
    while current <= end:
        times.append(current)
        current += interval
    
    return times


def validate_datetime_range(start: datetime, end: datetime) -> bool:
    """
    Validate that start datetime is before end datetime.
    
    TODO:
    - Add timezone normalization
    - Implement configurable tolerance
    """
    return start < end


class DateTimeHelper:
    """
    Helper class for advanced datetime operations.
    
    TODO:
    - Implement caching for expensive operations
    - Add configuration management
    - Implement timezone management
    """
    
    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = default_timezone
        self.tz = pytz.timezone(default_timezone)
    
    def now(self) -> datetime:
        """Get current time in configured timezone."""
        return datetime.now(self.tz)
    
    def localize(self, dt: datetime) -> datetime:
        """Localize naive datetime to configured timezone."""
        if dt.tzinfo is None:
            return self.tz.localize(dt)
        return dt.astimezone(self.tz)
    
    def normalize(self, dt: datetime) -> datetime:
        """Normalize datetime to handle DST transitions."""
        return self.tz.normalize(dt)


class TimeZoneManager:
    """
    Manager for timezone operations and conversions.
    
    TODO:
    - Implement timezone caching
    - Add timezone validation
    - Implement DST handling
    """
    
    def __init__(self):
        self.timezones = {}
    
    def get_timezone(self, tz_name: str) -> pytz.BaseTzInfo:
        """Get timezone object with caching."""
        if tz_name not in self.timezones:
            self.timezones[tz_name] = pytz.timezone(tz_name)
        return self.timezones[tz_name]
    
    def convert_between_timezones(
        self, 
        dt: datetime, 
        from_tz: str, 
        to_tz: str
    ) -> datetime:
        """Convert datetime between timezones."""
        source_tz = self.get_timezone(from_tz)
        target_tz = self.get_timezone(to_tz)
        
        if dt.tzinfo is None:
            dt = source_tz.localize(dt)
        
        return dt.astimezone(target_tz)
