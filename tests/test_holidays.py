"""Tests for holidays module."""

from datetime import date
from zoneinfo import ZoneInfo

import pytest

from src.holidays import (
    convert_lunar_to_solar,
    convert_solar_to_lunar,
    get_upcoming_holidays,
    get_holiday_name,
    format_date_vietnamese,
    get_vietnam_now,
    get_vietnam_date,
    VIETNAM_TZ,
)


class TestVietnamTimezone:
    """Tests for Vietnam timezone."""

    def test_vietnam_tz_is_correct(self):
        """Test that Vietnam timezone is correctly set to UTC+7."""
        assert VIETNAM_TZ.key == "Asia/Ho_Chi_Minh"

    def test_get_vietnam_now_returns_vietnam_time(self):
        """Test that get_vietnam_now returns time in Vietnam timezone."""
        now = get_vietnam_now()
        assert now.tzinfo is not None
        assert now.tzinfo.key == "Asia/Ho_Chi_Minh"

    def test_get_vietnam_date_returns_vietnam_date(self):
        """Test that get_vietnam_date returns date in Vietnam timezone."""
        today = get_vietnam_date()
        assert isinstance(today, date)


class TestLunarSolarConversion:
    """Tests for lunar/solar calendar conversion."""

    def test_lunar_to_solar_basic(self):
        """Test basic lunar to solar conversion."""
        solar_date = convert_lunar_to_solar(1, 1, 2026)
        assert isinstance(solar_date, date)
        assert solar_date.year == 2026
        assert 1 <= solar_date.month <= 12
        assert 1 <= solar_date.day <= 31

    def test_solar_to_lunar_basic(self):
        """Test basic solar to lunar conversion."""
        lunar_month, lunar_day = convert_solar_to_lunar(1, 1, 2026)
        assert isinstance(lunar_month, int)
        assert isinstance(lunar_day, int)
        assert 1 <= lunar_month <= 12
        assert 1 <= lunar_day <= 30

    def test_lunar_to_solar_tet(self):
        """Test Tết Nguyên đán conversion (1/1 lunar)."""
        solar_date = convert_lunar_to_solar(1, 1, 2026)
        assert solar_date.month in [1, 2]
        assert 1 <= solar_date.day <= 31

    def test_solar_to_lunar_tet(self):
        """Test solar to lunar for Tết."""
        lunar_month, lunar_day = convert_solar_to_lunar(1, 29, 2026)
        assert 1 <= lunar_month <= 12

    def test_round_trip_conversion(self):
        """Test that converting solar to lunar and back gives similar results."""
        original_solar = date(2026, 8, 15)
        lunar_month, lunar_day = convert_solar_to_lunar(
            original_solar.month, original_solar.day, original_solar.year
        )
        converted_back = convert_lunar_to_solar(lunar_month, lunar_day, original_solar.year)
        assert converted_back.month == original_solar.month


class TestUpcomingHolidays:
    """Tests for getting upcoming holidays."""

    def test_get_upcoming_holidays_returns_list(self):
        """Test that get_upcoming_holidays returns a list."""
        holidays = get_upcoming_holidays(30)
        assert isinstance(holidays, list)

    def test_get_upcoming_holidays_contains_solar_holidays(self):
        """Test that upcoming holidays includes solar holidays."""
        holidays = get_upcoming_holidays(365)
        holiday_names = [h["name"] for h in holidays]
        assert "Tết Dương lịch" in holiday_names
        assert "Quốc khánh" in holiday_names

    def test_get_upcoming_holidays_contains_lunar_holidays(self):
        """Test that upcoming holidays includes lunar holidays."""
        holidays = get_upcoming_holidays(365)
        holiday_names = [h["name"] for h in holidays]
        assert "Tết Trung thu" in holiday_names
        assert "Tết Nguyên đán" in holiday_names

    def test_upcoming_holidays_has_days_until(self):
        """Test that each holiday has days_until field."""
        holidays = get_upcoming_holidays(365)
        for holiday in holidays:
            assert "days_until" in holiday
            assert isinstance(holiday["days_until"], int)
            assert holiday["days_until"] >= 0

    def test_upcoming_holidays_is_sorted(self):
        """Test that holidays are sorted by days_until."""
        holidays = get_upcoming_holidays(365)
        days_list = [h["days_until"] for h in holidays]
        assert days_list == sorted(days_list)


class TestHolidayName:
    """Tests for getting holiday name."""

    def test_new_year_is_holiday(self):
        """Test that January 1st is recognized as Tết Dương lịch."""
        holiday_name = get_holiday_name(date(2026, 1, 1))
        assert holiday_name == "Tết Dương lịch"

    def test_labor_day_is_holiday(self):
        """Test that May 1st is recognized as Quốc tế Lao động."""
        holiday_name = get_holiday_name(date(2026, 5, 1))
        assert holiday_name == "Quốc tế Lao động"

    def test_independence_day_is_holiday(self):
        """Test that September 2nd is recognized as Quốc khánh."""
        holiday_name = get_holiday_name(date(2026, 9, 2))
        assert holiday_name == "Quốc khánh"


class TestFormatDateVietnamese:
    """Tests for formatting dates in Vietnamese format."""

    def test_format_solar_date(self):
        """Test formatting solar date."""
        d = date(2026, 8, 15)
        formatted = format_date_vietnamese(d, "solar")
        assert "15/08/2026" in formatted

    def test_format_lunar_date(self):
        """Test formatting lunar date includes lunar info."""
        d = date(2026, 8, 15)
        formatted = format_date_vietnamese(d, "lunar")
        assert "15/08/2026" in formatted
        assert "Âm" in formatted
