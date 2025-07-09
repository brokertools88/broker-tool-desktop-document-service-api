"""
Date and time utility functions.

This module provides helper functions for date/time operations, formatting, and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List, Dict, Callable, Any
import pytz
import logging

logger = logging.getLogger(__name__)


def get_utc_now(timezone_config: Optional[str] = None, time_provider: Optional[Callable[[], datetime]] = None) -> datetime:
    """
    Get current UTC datetime with configurable timezone and custom time provider.
    
    Args:
        timezone_config: Optional timezone configuration
        time_provider: Custom time provider for testing (function that returns datetime)
        
    Returns:
        Current UTC datetime
    """
    if time_provider:
        # Use custom time provider (useful for testing)
        return time_provider()
    
    if timezone_config and timezone_config != "UTC":
        # Convert from configured timezone to UTC
        local_tz = pytz.timezone(timezone_config)
        local_time = datetime.now(local_tz)
        return local_time.astimezone(timezone.utc)
    
    return datetime.now(timezone.utc)


def format_datetime(
    dt: datetime, 
    format_string: str = "%Y-%m-%d %H:%M:%S",
    locale: Optional[str] = None,
    relative: bool = False,
    include_timezone: bool = False
) -> str:
    """
    Format datetime to string with locale and relative time support.
    
    Args:
        dt: Datetime to format
        format_string: Format string to use
        locale: Locale for formatting (e.g., 'en_US', 'fr_FR')
        relative: Whether to use relative formatting ("2 hours ago")
        include_timezone: Whether to include timezone in formatted string
        
    Returns:
        Formatted datetime string
    """
    if relative:
        return get_relative_time(dt)
    
    # Include timezone if requested
    if include_timezone and dt.tzinfo:
        if format_string == "%Y-%m-%d %H:%M:%S":
            format_string = "%Y-%m-%d %H:%M:%S %Z"
    
    # TODO: Implement locale-specific formatting
    # For now, use standard formatting
    if locale:
        logger.info(f"Locale-specific formatting not yet implemented for: {locale}")
    
    return dt.strftime(format_string)


def parse_datetime(
    date_string: str, 
    format_string: str = "%Y-%m-%d %H:%M:%S",
    fallback_formats: Optional[List[str]] = None,
    auto_detect: bool = False,
    timezone_aware: bool = False
) -> datetime:
    """
    Parse datetime string with multiple format support and auto-detection.
    
    Args:
        date_string: String to parse
        format_string: Primary format string to try
        fallback_formats: Additional formats to try if primary fails
        auto_detect: Whether to attempt automatic format detection
        timezone_aware: Whether to parse timezone information
        
    Returns:
        Parsed datetime object
    """
    # Common formats to try for auto-detection
    common_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z"
    ]
    
    formats_to_try = [format_string]
    
    if fallback_formats:
        formats_to_try.extend(fallback_formats)
    
    if auto_detect:
        formats_to_try.extend(common_formats)
    
    # Try parsing with each format
    for fmt in formats_to_try:
        try:
            parsed_dt = datetime.strptime(date_string, fmt)
            
            # Handle timezone awareness
            if timezone_aware and parsed_dt.tzinfo is None:
                # Assume UTC if no timezone info
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            
            return parsed_dt
            
        except ValueError:
            continue
    
    # If all formats fail, try ISO format parsing
    try:
        return datetime.fromisoformat(date_string)
    except ValueError:
        pass
    
    logger.error(f"Failed to parse datetime: {date_string}")
    raise ValueError(f"Unable to parse datetime string: {date_string}")


def convert_timezone(
    dt: datetime, 
    target_timezone: str,
    cache_timezones: bool = True,
    handle_dst: bool = True
) -> datetime:
    """
    Convert datetime to target timezone with validation and DST handling.
    
    Args:
        dt: Datetime to convert
        target_timezone: Target timezone name
        cache_timezones: Whether to cache timezone objects
        handle_dst: Whether to handle daylight saving time transitions
        
    Returns:
        Datetime converted to target timezone
    """
    # Validate timezone
    try:
        if cache_timezones:
            # Use timezone manager for caching
            tz_manager = TimeZoneManager()
            target_tz = tz_manager.get_timezone(target_timezone)
        else:
            target_tz = pytz.timezone(target_timezone)
    except pytz.exceptions.UnknownTimeZoneError as e:
        logger.error(f"Unknown timezone: {target_timezone}")
        raise ValueError(f"Invalid timezone: {target_timezone}") from e
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    converted = dt.astimezone(target_tz)
    
    # Handle DST transitions if requested
    if handle_dst and hasattr(target_tz, 'normalize'):
        converted = target_tz.normalize(converted)
    
    return converted


def to_iso_format(
    dt: datetime, 
    microseconds: bool = True,
    timezone_offset: bool = True
) -> str:
    """
    Convert datetime to ISO format string with precision control.
    
    Args:
        dt: Datetime to convert
        microseconds: Whether to include microseconds
        timezone_offset: Whether to include timezone offset
        
    Returns:
        ISO format string
    """
    if not microseconds:
        # Remove microseconds
        dt = dt.replace(microsecond=0)
    
    iso_string = dt.isoformat()
    
    if not timezone_offset and dt.tzinfo:
        # Remove timezone offset
        if '+' in iso_string:
            iso_string = iso_string.split('+')[0]
        elif iso_string.endswith('Z'):
            iso_string = iso_string[:-1]
    
    return iso_string


def from_iso_format(
    iso_string: str,
    validate: bool = True,
    parse_timezone: bool = True
) -> datetime:
    """
    Parse datetime from ISO format string with validation.
    
    Args:
        iso_string: ISO format string to parse
        validate: Whether to validate the format
        parse_timezone: Whether to parse timezone information
        
    Returns:
        Parsed datetime object
    """
    if validate:
        # Basic validation of ISO format
        if not iso_string or len(iso_string) < 10:
            raise ValueError("Invalid ISO format string")
    
    try:
        # Handle timezone parsing
        if parse_timezone:
            return datetime.fromisoformat(iso_string)
        else:
            # Remove timezone info before parsing
            clean_string = iso_string
            if '+' in clean_string:
                clean_string = clean_string.split('+')[0]
            elif clean_string.endswith('Z'):
                clean_string = clean_string[:-1]
            elif clean_string.count('-') > 2:  # Has timezone offset
                parts = clean_string.rsplit('-', 1)
                if ':' in parts[1] or len(parts[1]) == 4:
                    clean_string = parts[0]
            
            return datetime.fromisoformat(clean_string)
            
    except ValueError as e:
        logger.error(f"Failed to parse ISO format: {iso_string}, error: {str(e)}")
        raise


def add_time(
    dt: datetime, 
    business_days_only: bool = False,
    holidays: Optional[List[datetime]] = None,
    timezone_aware: bool = False,
    **kwargs
) -> datetime:
    """
    Add time to datetime with business day and holiday awareness.
    
    Args:
        dt: Base datetime
        business_days_only: Whether to add only business days
        holidays: List of holiday dates to skip
        timezone_aware: Whether to handle timezone calculations
        **kwargs: Time units (days, hours, minutes, seconds, etc.)
        
    Returns:
        Modified datetime
    """
    if not business_days_only:
        delta = timedelta(**kwargs)
        result = dt + delta
        
        if timezone_aware and dt.tzinfo:
            # Handle timezone transitions for pytz timezones
            try:
                # Check if it's a pytz timezone with normalize method
                if hasattr(dt.tzinfo, 'normalize'):
                    result = dt.tzinfo.normalize(result)  # type: ignore
            except Exception:
                # If normalization fails, just use the result as-is
                pass
        
        return result
    
    # Business days calculation
    if 'days' in kwargs:
        days_to_add = kwargs.pop('days')
        current_dt = dt
        
        while days_to_add > 0:
            current_dt += timedelta(days=1)
            
            if is_business_day(current_dt, holidays):
                days_to_add -= 1
        
        # Add remaining time components
        if kwargs:
            delta = timedelta(**kwargs)
            current_dt += delta
        
        return current_dt
    
    # For non-day units, just add normally
    delta = timedelta(**kwargs)
    return dt + delta


def subtract_time(
    dt: datetime, 
    business_days_only: bool = False,
    holidays: Optional[List[datetime]] = None,
    **kwargs
) -> datetime:
    """
    Subtract time from datetime with business day and holiday awareness.
    
    Args:
        dt: Base datetime
        business_days_only: Whether to subtract only business days
        holidays: List of holiday dates to skip
        **kwargs: Time units (days, hours, minutes, seconds, etc.)
        
    Returns:
        Modified datetime
    """
    if not business_days_only:
        delta = timedelta(**kwargs)
        return dt - delta
    
    # Business days calculation
    if 'days' in kwargs:
        days_to_subtract = kwargs.pop('days')
        current_dt = dt
        
        while days_to_subtract > 0:
            current_dt -= timedelta(days=1)
            
            if is_business_day(current_dt, holidays):
                days_to_subtract -= 1
        
        # Subtract remaining time components
        if kwargs:
            delta = timedelta(**kwargs)
            current_dt -= delta
        
        return current_dt
    
    # For non-day units, just subtract normally
    delta = timedelta(**kwargs)
    return dt - delta


def time_difference(
    dt1: datetime, 
    dt2: datetime,
    absolute: bool = False,
    business_days_only: bool = False,
    human_readable: bool = False
) -> Union[timedelta, str]:
    """
    Calculate time difference between two datetimes.
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        absolute: Whether to return absolute difference
        business_days_only: Whether to calculate business days difference
        human_readable: Whether to return human-readable format
        
    Returns:
        Time difference as timedelta or human-readable string
    """
    if business_days_only:
        # Calculate business days difference
        start_date = min(dt1, dt2).date()
        end_date = max(dt1, dt2).date()
        
        business_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if is_business_day(datetime.combine(current_date, datetime.min.time())):
                business_days += 1
            current_date += timedelta(days=1)
        
        if dt1 > dt2:
            business_days = -business_days
            
        if absolute:
            business_days = abs(business_days)
            
        if human_readable:
            return f"{business_days} business days"
        
        return timedelta(days=business_days)
    
    difference = dt1 - dt2
    
    if absolute:
        difference = abs(difference)
    
    if human_readable:
        return format_duration(difference)
    
    return difference


def is_past(dt: datetime, tolerance_seconds: int = 0, timezone_aware: bool = True) -> bool:
    """
    Check if datetime is in the past with configurable tolerance.
    
    Args:
        dt: Datetime to check
        tolerance_seconds: Tolerance in seconds (0 for exact)
        timezone_aware: Whether to handle timezone comparison
        
    Returns:
        True if datetime is in the past
    """
    now = get_utc_now()
    
    if timezone_aware and dt.tzinfo and now.tzinfo:
        # Both have timezone info, compare directly
        comparison_time = now
    elif timezone_aware:
        # Normalize timezones for comparison
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        comparison_time = now
    else:
        # Naive comparison
        comparison_time = now.replace(tzinfo=None)
        dt = dt.replace(tzinfo=None)
    
    if tolerance_seconds > 0:
        comparison_time += timedelta(seconds=tolerance_seconds)
    
    return dt < comparison_time


def is_future(dt: datetime, tolerance_seconds: int = 0, timezone_aware: bool = True) -> bool:
    """
    Check if datetime is in the future with configurable tolerance.
    
    Args:
        dt: Datetime to check
        tolerance_seconds: Tolerance in seconds (0 for exact)
        timezone_aware: Whether to handle timezone comparison
        
    Returns:
        True if datetime is in the future
    """
    now = get_utc_now()
    
    if timezone_aware and dt.tzinfo and now.tzinfo:
        comparison_time = now
    elif timezone_aware:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        comparison_time = now
    else:
        comparison_time = now.replace(tzinfo=None)
        dt = dt.replace(tzinfo=None)
    
    if tolerance_seconds > 0:
        comparison_time -= timedelta(seconds=tolerance_seconds)
    
    return dt > comparison_time


def is_within_range(
    dt: datetime, 
    start: datetime, 
    end: datetime,
    inclusive_start: bool = True,
    inclusive_end: bool = True,
    timezone_aware: bool = True
) -> bool:
    """
    Check if datetime is within a range with inclusive/exclusive options.
    
    Args:
        dt: Datetime to check
        start: Range start datetime
        end: Range end datetime
        inclusive_start: Whether start is inclusive
        inclusive_end: Whether end is inclusive
        timezone_aware: Whether to handle timezone normalization
        
    Returns:
        True if datetime is within range
    """
    if timezone_aware:
        # Normalize all datetimes to same timezone
        if dt.tzinfo != start.tzinfo or dt.tzinfo != end.tzinfo:
            target_tz = dt.tzinfo or timezone.utc
            
            if start.tzinfo != target_tz:
                start = start.astimezone(target_tz) if start.tzinfo else start.replace(tzinfo=target_tz)
            if end.tzinfo != target_tz:
                end = end.astimezone(target_tz) if end.tzinfo else end.replace(tzinfo=target_tz)
    
    if inclusive_start and inclusive_end:
        return start <= dt <= end
    elif inclusive_start and not inclusive_end:
        return start <= dt < end
    elif not inclusive_start and inclusive_end:
        return start < dt <= end
    else:
        return start < dt < end


def get_start_of_day(dt: datetime, preserve_timezone: bool = True, custom_start_hour: int = 0) -> datetime:
    """
    Get start of day with timezone preservation and custom start time.
    
    Args:
        dt: Input datetime
        preserve_timezone: Whether to preserve original timezone
        custom_start_hour: Custom hour for day start (default 0 = midnight)
        
    Returns:
        Start of day datetime
    """
    start_of_day = dt.replace(hour=custom_start_hour, minute=0, second=0, microsecond=0)
    
    if preserve_timezone and dt.tzinfo:
        # Preserve timezone
        return start_of_day
    elif not preserve_timezone:
        # Remove timezone info
        return start_of_day.replace(tzinfo=None)
    
    return start_of_day


def get_end_of_day(dt: datetime, preserve_timezone: bool = True, custom_end_hour: int = 23) -> datetime:
    """
    Get end of day with timezone preservation and custom end time.
    
    Args:
        dt: Input datetime
        preserve_timezone: Whether to preserve original timezone
        custom_end_hour: Custom hour for day end (default 23 = 11 PM)
        
    Returns:
        End of day datetime
    """
    end_of_day = dt.replace(hour=custom_end_hour, minute=59, second=59, microsecond=999999)
    
    if preserve_timezone and dt.tzinfo:
        return end_of_day
    elif not preserve_timezone:
        return end_of_day.replace(tzinfo=None)
    
    return end_of_day


def get_start_of_month(dt: datetime, preserve_timezone: bool = True, business_month: bool = False) -> datetime:
    """
    Get first day of month with timezone preservation and business month logic.
    
    Args:
        dt: Input datetime
        preserve_timezone: Whether to preserve original timezone
        business_month: Whether to use business month logic (skip weekends)
        
    Returns:
        Start of month datetime
    """
    start_of_month = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if business_month:
        # Find first business day of month
        while is_weekend(start_of_month):
            start_of_month += timedelta(days=1)
    
    if not preserve_timezone:
        start_of_month = start_of_month.replace(tzinfo=None)
    
    return start_of_month


def get_end_of_month(dt: datetime, preserve_timezone: bool = True, business_month: bool = False) -> datetime:
    """
    Get last day of month with timezone preservation and business month logic.
    
    Args:
        dt: Input datetime
        preserve_timezone: Whether to preserve original timezone
        business_month: Whether to use business month logic (skip weekends)
        
    Returns:
        End of month datetime
    """
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    
    last_day = next_month - timedelta(days=1)
    end_of_month = get_end_of_day(last_day, preserve_timezone)
    
    if business_month:
        # Find last business day of month
        while is_weekend(end_of_month):
            end_of_month -= timedelta(days=1)
        end_of_month = get_end_of_day(end_of_month, preserve_timezone)
    
    return end_of_month


def get_weekday_name(dt: datetime, locale: Optional[str] = None, abbreviated: bool = False) -> str:
    """
    Get weekday name with locale support and abbreviation option.
    
    Args:
        dt: Input datetime
        locale: Locale for day names (e.g., 'en_US', 'fr_FR')
        abbreviated: Whether to return abbreviated name
        
    Returns:
        Weekday name string
    """
    if abbreviated:
        format_code = "%a"  # Abbreviated weekday name
    else:
        format_code = "%A"  # Full weekday name
    
    # TODO: Implement locale-specific day names
    if locale and locale != "en_US":
        logger.info(f"Locale-specific weekday names not yet implemented for: {locale}")
    
    return dt.strftime(format_code)


def get_month_name(dt: datetime, locale: Optional[str] = None, abbreviated: bool = False) -> str:
    """
    Get month name with locale support and abbreviation option.
    
    Args:
        dt: Input datetime
        locale: Locale for month names (e.g., 'en_US', 'fr_FR')
        abbreviated: Whether to return abbreviated name
        
    Returns:
        Month name string
    """
    if abbreviated:
        format_code = "%b"  # Abbreviated month name
    else:
        format_code = "%B"  # Full month name
    
    # TODO: Implement locale-specific month names
    if locale and locale != "en_US":
        logger.info(f"Locale-specific month names not yet implemented for: {locale}")
    
    return dt.strftime(format_code)


def is_weekend(dt: datetime, weekend_days: Optional[List[int]] = None, culture: Optional[str] = None) -> bool:
    """
    Check if datetime falls on weekend with configurable weekend days.
    
    Args:
        dt: Datetime to check
        weekend_days: List of weekend day numbers (0=Monday, 6=Sunday)
        culture: Culture-specific weekend configuration
        
    Returns:
        True if datetime is on weekend
    """
    if culture:
        # Culture-specific weekend configurations
        culture_weekends = {
            'islamic': [4, 5],  # Friday, Saturday
            'israeli': [5, 6],  # Saturday, Sunday
            'western': [5, 6],  # Saturday, Sunday (default)
        }
        weekend_days = culture_weekends.get(culture, [5, 6])
    
    if weekend_days is None:
        weekend_days = [5, 6]  # Default: Saturday = 5, Sunday = 6
    
    return dt.weekday() in weekend_days


def is_business_day(
    dt: datetime, 
    holidays: Optional[List[datetime]] = None,
    country: Optional[str] = None,
    custom_rules: Optional[Dict[str, Callable[[datetime], bool]]] = None
) -> bool:
    """
    Check if datetime is a business day with holiday calendar integration.
    
    Args:
        dt: Datetime to check
        holidays: List of holiday dates
        country: Country code for holiday calendar (e.g., 'US', 'UK', 'FR')
        custom_rules: Custom business day rules
        
    Returns:
        True if datetime is a business day
    """
    # Check if it's a weekend
    if is_weekend(dt):
        return False
    
    # Apply custom rules if provided
    if custom_rules:
        for rule_name, rule_func in custom_rules.items():
            if not rule_func(dt):
                logger.debug(f"Business day rule '{rule_name}' failed for {dt}")
                return False
    
    # Check holidays
    if holidays:
        date_only = dt.date()
        holiday_dates = [h.date() if isinstance(h, datetime) else h for h in holidays]
        if date_only in holiday_dates:
            return False
    
    # TODO: Implement country-specific holiday calendars
    if country:
        logger.info(f"Country-specific holiday calendar not yet implemented for: {country}")
    
    return True


def get_age(
    birth_date: datetime, 
    reference_date: Optional[datetime] = None,
    precision: str = "years",
    timezone_aware: bool = True,
    handle_leap_years: bool = True
) -> Union[int, float, Dict[str, Any]]:
    """
    Calculate age with multiple precision options and leap year handling.
    
    Args:
        birth_date: Birth date
        reference_date: Reference date for age calculation (default: now)
        precision: Precision level ('years', 'months', 'days', 'detailed')
        timezone_aware: Whether to handle timezone differences
        handle_leap_years: Whether to handle leap year edge cases
        
    Returns:
        Age as int, float, or detailed dict based on precision
    """
    if reference_date is None:
        reference_date = get_utc_now()
    
    # Handle timezone normalization
    if timezone_aware:
        if birth_date.tzinfo != reference_date.tzinfo:
            if birth_date.tzinfo is None:
                birth_date = birth_date.replace(tzinfo=timezone.utc)
            if reference_date.tzinfo is None:
                reference_date = reference_date.replace(tzinfo=timezone.utc)
            # Convert to same timezone
            birth_date = birth_date.astimezone(reference_date.tzinfo)
    
    if precision == "years":
        age = reference_date.year - birth_date.year
        
        # Check if birthday has occurred this year
        if handle_leap_years:
            # Handle leap year edge case (Feb 29)
            try:
                birthday_this_year = birth_date.replace(year=reference_date.year)
            except ValueError:
                # Feb 29 on non-leap year, use Feb 28
                birthday_this_year = birth_date.replace(year=reference_date.year, day=28)
        else:
            if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
                age -= 1
            return age
        
        if reference_date < birthday_this_year:
            age -= 1
            
        return age
    
    elif precision == "months":
        months = (reference_date.year - birth_date.year) * 12
        months += reference_date.month - birth_date.month
        if reference_date.day < birth_date.day:
            months -= 1
        return months
    
    elif precision == "days":
        delta = reference_date - birth_date
        return delta.days
    
    elif precision == "detailed":
        # Return detailed breakdown
        years_only = get_age(birth_date, reference_date, "years", timezone_aware, handle_leap_years)
        
        # Ensure we have an integer for year calculation
        if not isinstance(years_only, int):
            raise ValueError("Invalid age calculation result")
        
        # Calculate remaining months after years
        year_anniversary = birth_date.replace(year=birth_date.year + years_only)
        if reference_date >= year_anniversary:
            remaining_months = (reference_date.year - year_anniversary.year) * 12
            remaining_months += reference_date.month - year_anniversary.month
            if reference_date.day < year_anniversary.day:
                remaining_months -= 1
        else:
            remaining_months = 0
        
        # Calculate remaining days
        try:
            month_anniversary = year_anniversary.replace(month=year_anniversary.month + remaining_months)
        except ValueError:
            # Handle month overflow
            month_anniversary = year_anniversary.replace(
                year=year_anniversary.year + (year_anniversary.month + remaining_months - 1) // 12,
                month=(year_anniversary.month + remaining_months - 1) % 12 + 1
            )
        
        remaining_days = (reference_date - month_anniversary).days
        
        return {
            "years": years_only,
            "months": remaining_months,
            "days": remaining_days,
            "total_days": (reference_date - birth_date).days
        }
    
    else:
        raise ValueError(f"Unsupported precision: {precision}")


def format_duration(
    delta: timedelta, 
    locale: Optional[str] = None,
    precision: str = "auto",
    short_format: bool = False
) -> str:
    """
    Format timedelta as human-readable duration with localization and precision control.
    
    Args:
        delta: Timedelta to format
        locale: Locale for formatting
        precision: Precision level ('auto', 'seconds', 'minutes', 'hours', 'days')
        short_format: Whether to use short format (1d vs 1 day)
        
    Returns:
        Formatted duration string
    """
    total_seconds = int(delta.total_seconds())
    
    if total_seconds == 0:
        return "0 seconds" if not short_format else "0s"
    
    # Calculate components
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    
    if precision == "auto":
        # Auto-select appropriate precision
        if days > 0:
            if short_format:
                parts.append(f"{days}d")
                if hours > 0:
                    parts.append(f"{hours}h")
            else:
                parts.append(f"{days} day{'s' if days != 1 else ''}")
                if hours > 0:
                    parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        elif hours > 0:
            if short_format:
                parts.append(f"{hours}h")
                if minutes > 0:
                    parts.append(f"{minutes}m")
            else:
                parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
                if minutes > 0:
                    parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        elif minutes > 0:
            if short_format:
                parts.append(f"{minutes}m")
            else:
                parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        else:
            if short_format:
                parts.append(f"{seconds}s")
            else:
                parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    elif precision == "days":
        if short_format:
            parts.append(f"{days}d")
        else:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
    
    elif precision == "hours":
        total_hours = total_seconds // 3600
        if short_format:
            parts.append(f"{total_hours}h")
        else:
            parts.append(f"{total_hours} hour{'s' if total_hours != 1 else ''}")
    
    elif precision == "minutes":
        total_minutes = total_seconds // 60
        if short_format:
            parts.append(f"{total_minutes}m")
        else:
            parts.append(f"{total_minutes} minute{'s' if total_minutes != 1 else ''}")
    
    elif precision == "seconds":
        if short_format:
            parts.append(f"{total_seconds}s")
        else:
            parts.append(f"{total_seconds} second{'s' if total_seconds != 1 else ''}")
    
    # TODO: Implement localization
    if locale and locale != "en_US":
        logger.info(f"Duration localization not yet implemented for: {locale}")
    
    return " ".join(parts) if parts else "0 seconds"


def get_relative_time(
    dt: datetime, 
    reference_dt: Optional[datetime] = None,
    locale: Optional[str] = None,
    precision: str = "auto",
    threshold_config: Optional[Dict[str, int]] = None
) -> str:
    """
    Get relative time description with localization and precision control.
    
    Args:
        dt: Target datetime
        reference_dt: Reference datetime (default: now)
        locale: Locale for formatting
        precision: Precision level ('auto', 'exact')
        threshold_config: Custom thresholds for relative descriptions
        
    Returns:
        Relative time string (e.g., "2 hours ago", "in 3 days")
    """
    if reference_dt is None:
        reference_dt = get_utc_now()
    
    delta = reference_dt - dt
    is_past = delta.total_seconds() > 0
    
    if not is_past:
        delta = -delta
    
    # Default thresholds (in seconds)
    default_thresholds = {
        'just_now': 30,
        'minutes': 3600,      # 1 hour
        'hours': 86400,       # 1 day
        'days': 2592000,      # 30 days
        'weeks': 31536000,    # 1 year
    }
    
    thresholds = threshold_config or default_thresholds
    total_seconds = int(delta.total_seconds())
    
    # Handle "just now" case
    if total_seconds < thresholds.get('just_now', 30):
        return "just now"
    
    # Format based on duration
    if total_seconds < thresholds.get('minutes', 3600):
        minutes = total_seconds // 60
        unit = "minute" if minutes == 1 else "minutes"
        amount = f"{minutes} {unit}"
    elif total_seconds < thresholds.get('hours', 86400):
        hours = total_seconds // 3600
        unit = "hour" if hours == 1 else "hours"
        amount = f"{hours} {unit}"
    elif total_seconds < thresholds.get('days', 2592000):
        days = total_seconds // 86400
        unit = "day" if days == 1 else "days"
        amount = f"{days} {unit}"
    elif total_seconds < thresholds.get('weeks', 31536000):
        weeks = total_seconds // 604800
        unit = "week" if weeks == 1 else "weeks"
        amount = f"{weeks} {unit}"
    else:
        # Fall back to absolute date for very old/future dates
        return format_datetime(dt, "%Y-%m-%d")
    
    # TODO: Implement localization
    if locale and locale != "en_US":
        logger.info(f"Relative time localization not yet implemented for: {locale}")
    
    if is_past:
        return f"{amount} ago"
    else:
        return f"in {amount}"


def generate_time_range(
    start: datetime, 
    end: datetime, 
    interval: timedelta,
    business_days_only: bool = False,
    timezone_aware: bool = True,
    as_generator: bool = False
) -> Union[List[datetime], Any]:
    """
    Generate list of datetimes with business day filtering and memory efficiency.
    
    Args:
        start: Start datetime
        end: End datetime
        interval: Time interval between points
        business_days_only: Whether to include only business days
        timezone_aware: Whether to handle timezone transitions
        as_generator: Whether to return generator for memory efficiency
        
    Returns:
        List of datetimes or generator
    """
    def time_generator():
        current = start
        
        while current <= end:
            if business_days_only and not is_business_day(current):
                current += interval
                continue
            
            yield current
            
            # Handle timezone transitions
            if timezone_aware and current.tzinfo:
                try:
                    if hasattr(current.tzinfo, 'normalize'):
                        current = current.tzinfo.normalize(current + interval)  # type: ignore
                    else:
                        current += interval
                except Exception:
                    current += interval
            else:
                current += interval
    
    if as_generator:
        return time_generator()
    
    return list(time_generator())


def validate_datetime_range(
    start: datetime, 
    end: datetime,
    normalize_timezones: bool = True,
    tolerance_seconds: int = 0
) -> bool:
    """
    Validate datetime range with timezone normalization and tolerance.
    
    Args:
        start: Start datetime
        end: End datetime
        normalize_timezones: Whether to normalize timezones for comparison
        tolerance_seconds: Tolerance in seconds for near-equal times
        
    Returns:
        True if start is before end (within tolerance)
    """
    if normalize_timezones:
        # Normalize timezones for fair comparison
        if start.tzinfo != end.tzinfo:
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            
            # Convert to same timezone
            end = end.astimezone(start.tzinfo)
    
    time_diff = (end - start).total_seconds()
    
    if tolerance_seconds > 0:
        return time_diff >= -tolerance_seconds
    
    return start < end


class DateTimeHelper:
    """
    Helper class for advanced datetime operations with caching and configuration.
    """
    
    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = default_timezone
        self.tz = pytz.timezone(default_timezone)
        self._cache = {}
        self._config = {
            'cache_enabled': True,
            'cache_size_limit': 1000,
            'default_format': '%Y-%m-%d %H:%M:%S'
        }
    
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
        if hasattr(self.tz, 'normalize'):
            return self.tz.normalize(dt)  # type: ignore
        return dt
    
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration option."""
        self._config[key] = value
        
        if key == 'cache_enabled' and not value:
            self._cache.clear()
    
    def get_cached_result(self, operation: str, *args) -> Any:
        """Get cached result for expensive operations."""
        if not self._config.get('cache_enabled', True):
            return None
        
        cache_key = f"{operation}:{hash(args)}"
        return self._cache.get(cache_key)
    
    def cache_result(self, operation: str, result: Any, *args) -> None:
        """Cache result of expensive operation."""
        if not self._config.get('cache_enabled', True):
            return
        
        # Implement cache size limit
        if len(self._cache) >= self._config.get('cache_size_limit', 1000):
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        cache_key = f"{operation}:{hash(args)}"
        self._cache[cache_key] = result
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
    
    def format_local(self, dt: datetime, format_string: Optional[str] = None) -> str:
        """Format datetime in local timezone."""
        local_dt = self.localize(dt) if dt.tzinfo is None else dt.astimezone(self.tz)
        fmt = format_string or self._config.get('default_format', '%Y-%m-%d %H:%M:%S')
        return local_dt.strftime(fmt)


class TimeZoneManager:
    """
    Manager for timezone operations with caching, validation, and DST handling.
    """
    
    def __init__(self):
        self.timezones = {}
        self._dst_cache = {}
        self._validation_cache = set()
    
    def get_timezone(self, tz_name: str) -> pytz.BaseTzInfo:
        """Get timezone object with caching and validation."""
        # Check validation cache first
        if tz_name not in self._validation_cache:
            try:
                # Validate timezone name
                pytz.timezone(tz_name)
                self._validation_cache.add(tz_name)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f"Unknown timezone: {tz_name}")
        
        # Get from cache or create
        if tz_name not in self.timezones:
            self.timezones[tz_name] = pytz.timezone(tz_name)
        
        return self.timezones[tz_name]
    
    def convert_between_timezones(
        self, 
        dt: datetime, 
        from_tz: str, 
        to_tz: str,
        handle_dst: bool = True
    ) -> datetime:
        """Convert datetime between timezones with DST handling."""
        source_tz = self.get_timezone(from_tz)
        target_tz = self.get_timezone(to_tz)
        
        # Localize if naive
        if dt.tzinfo is None:
            dt = source_tz.localize(dt)
        
        # Convert to target timezone
        converted = dt.astimezone(target_tz)
        
        # Handle DST transitions if requested
        if handle_dst and hasattr(target_tz, 'normalize'):
            converted = target_tz.normalize(converted)  # type: ignore
        
        return converted
    
    def get_dst_info(self, tz_name: str, year: int) -> Dict[str, Any]:
        """Get DST transition information for a timezone and year."""
        cache_key = f"{tz_name}:{year}"
        
        if cache_key in self._dst_cache:
            return self._dst_cache[cache_key]
        
        tz = self.get_timezone(tz_name)
        
        # Find DST transitions for the year
        dst_info = {
            'has_dst': False,
            'transitions': [],
            'standard_offset': None,
            'dst_offset': None
        }
        
        try:
            # Check a few dates throughout the year for DST changes
            test_dates = [
                datetime(year, 1, 1),   # Winter
                datetime(year, 4, 1),   # Spring
                datetime(year, 7, 1),   # Summer
                datetime(year, 10, 1),  # Fall
            ]
            
            offsets = []
            for test_date in test_dates:
                localized = tz.localize(test_date)
                offset = localized.utcoffset()
                if offset:
                    offsets.append(offset.total_seconds())
            
            if len(set(offsets)) > 1:
                dst_info['has_dst'] = True
                dst_info['standard_offset'] = min(offsets)
                dst_info['dst_offset'] = max(offsets)
            
        except Exception as e:
            logger.warning(f"Failed to get DST info for {tz_name}: {str(e)}")
        
        self._dst_cache[cache_key] = dst_info
        return dst_info
    
    def list_common_timezones(self, region: Optional[str] = None) -> List[str]:
        """List common timezones, optionally filtered by region."""
        common_zones = pytz.common_timezones
        
        if region:
            return [tz for tz in common_zones if tz.startswith(region)]
        
        return list(common_zones)
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.timezones.clear()
        self._dst_cache.clear()
        self._validation_cache.clear()
