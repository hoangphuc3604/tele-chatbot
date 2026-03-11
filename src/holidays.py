"""Vietnam holidays and calendar conversion service."""

from datetime import datetime, date, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from lunarcalendar import Converter, Solar, Lunar

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

VIETNAM_HOLIDAYS_SOLAR = [
    {"name": "Tết Dương lịch", "month": 1, "day": 1},
    {"name": "Ngày Giải phóng miền Nam", "month": 4, "day": 30},
    {"name": "Quốc tế Lao động", "month": 5, "day": 1},
    {"name": "Quốc khánh", "month": 9, "day": 2},
    {"name": "Giáng Sinh", "month": 12, "day": 25},
]

VIETNAM_HOLIDAYS_LUNAR = [
    {"name": "Tết Nguyên đán", "lunar_month": 1, "lunar_day": 1, "description": "Mùng 1 Tết"},
    {"name": "Tết Nguyên đán", "lunar_month": 1, "lunar_day": 2, "description": "Mùng 2 Tết"},
    {"name": "Tết Nguyên đán", "lunar_month": 1, "lunar_day": 3, "description": "Mùng 3 Tết"},
    {"name": "Hội Lim (miền Bắc)", "lunar_month": 1, "lunar_day": 15, "description": "Hội Lim - đánh du kè"},
    {"name": "Lễ Thanh Minh", "lunar_month": 3, "lunar_day": 3, "description": "Tuần trăng rằm - đi chơi pháo hoa"},
    {"name": "Giỗ Tổ Hùng Vương", "lunar_month": 3, "lunar_day": 10, "description": "Giỗ Tổ Hùng Vương"},
    {"name": "Lễ Phật Đản", "lunar_month": 4, "lunar_day": 8, "description": "Sinh nhật Đức Phật"},
    {"name": "Lễ Vu Lan", "lunar_month": 7, "lunar_day": 15, "description": "Rằm tháng 7 - báo hiếu"},
    {"name": "Tết Trung thu", "lunar_month": 8, "lunar_day": 15, "description": "Rằm tháng 8 - trẻ em"},
    {"name": "Ngày Nhà giáo Việt Nam", "lunar_month": 11, "lunar_day": 20, "description": "Ngày Nhà giáo Việt Nam"},
    {"name": "Tết Tây", "lunar_month": 12, "lunar_day": 23, "description": "Ông Táo về trời"},
]


def get_vietnam_now() -> datetime:
    """Get current time in Vietnam timezone."""
    return datetime.now(VIETNAM_TZ)


def get_vietnam_date() -> date:
    """Get current date in Vietnam timezone."""
    return get_vietnam_now().date()


def to_vietnam_tz(dt: datetime) -> datetime:
    """Convert datetime to Vietnam timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VIETNAM_TZ)


def convert_lunar_to_solar(
    lunar_month: int, lunar_day: int, year: int
) -> date:
    """Convert lunar date to solar date."""
    lunar_date = Lunar(year, lunar_month, lunar_day)
    solar = Converter.Lunar2Solar(lunar_date)
    return date(solar.year, solar.month, solar.day)


def convert_solar_to_lunar(
    solar_month: int, solar_day: int, year: int
) -> tuple[int, int]:
    """Convert solar date to lunar date (month, day)."""
    solar_date = Solar(year, solar_month, solar_day)
    lunar = Converter.Solar2Lunar(solar_date)
    return lunar.month, lunar.day


def get_upcoming_holidays(days_ahead: int = 30) -> list[dict]:
    """Get upcoming Vietnam holidays within specified days."""
    today = get_vietnam_date()
    end_date = today + timedelta(days=days_ahead)
    upcoming = []

    for holiday in VIETNAM_HOLIDAYS_SOLAR:
        month = holiday["month"]
        day = holiday["day"]
        holiday_date = date(today.year, month, day)

        if holiday_date < today:
            holiday_date = date(today.year + 1, month, day)

        if today <= holiday_date <= end_date:
            days_until = (holiday_date - today).days
            upcoming.append({
                "name": holiday["name"],
                "date": holiday_date,
                "date_type": "solar",
                "days_until": days_until,
            })

    for holiday in VIETNAM_HOLIDAYS_LUNAR:
        lunar_month = holiday["lunar_month"]
        lunar_day = holiday["lunar_day"]

        try:
            solar_date = convert_lunar_to_solar(lunar_month, lunar_day, today.year)
        except Exception:
            continue

        if solar_date < today:
            try:
                solar_date = convert_lunar_to_solar(lunar_month, lunar_day, today.year + 1)
            except Exception:
                continue

        if today <= solar_date <= end_date:
            days_until = (solar_date - today).days
            upcoming.append({
                "name": holiday["name"],
                "date": solar_date,
                "date_type": "lunar",
                "lunar_month": lunar_month,
                "lunar_day": lunar_day,
                "days_until": days_until,
            })

    upcoming.sort(key=lambda x: x["days_until"])
    return upcoming


def get_holiday_name(solar_date: date) -> Optional[str]:
    """Get holiday name for a specific solar date."""
    month = solar_date.month
    day = solar_date.day

    for holiday in VIETNAM_HOLIDAYS_SOLAR:
        if holiday["month"] == month and holiday["day"] == day:
            return holiday["name"]

    lunar_month, lunar_day = convert_solar_to_lunar(month, day, solar_date.year)
    for holiday in VIETNAM_HOLIDAYS_LUNAR:
        if holiday["lunar_month"] == lunar_month and holiday["lunar_day"] == lunar_day:
            return holiday["name"]

    return None


def format_date_vietnamese(d: date, date_type: str = "solar") -> str:
    """Format date in Vietnamese format."""
    day = d.day
    month = d.month
    year = d.year
    result = f"{day:02d}/{month:02d}/{year}"

    if date_type == "lunar":
        lunar_month, lunar_day = convert_solar_to_lunar(month, day, year)
        result += f" (Âm: {lunar_day:02d}/{lunar_month:02d})"

    return result
