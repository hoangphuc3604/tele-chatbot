"""Inline keyboards for INKLIU Bot."""

from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from lunarcalendar import Converter, Solar, Lunar


def get_lunar_date(solar_date: date) -> tuple[int, int]:
    solar = Solar(solar_date.year, solar_date.month, solar_date.day)
    lunar = Converter.Solar2Lunar(solar)
    return lunar.month, lunar.day


def get_calendar_keyboard(month: int, year: int) -> InlineKeyboardMarkup:
    """Generate inline keyboard calendar with lunar dates only."""
    month_names = [
        "Thang 1", "Thang 2", "Thang 3", "Thang 4", "Thang 5", "Thang 6",
        "Thang 7", "Thang 8", "Thang 9", "Thang 10", "Thang 11", "Thang 12"
    ]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text="◀",
            callback_data=f"cal_prev_{prev_month}_{prev_year}"
        ),
        InlineKeyboardButton(
            text=f"{month_names[month - 1]} {year}",
            callback_data="cal_current"
        ),
        InlineKeyboardButton(
            text="▶",
            callback_data=f"cal_next_{next_month}_{next_year}"
        ),
    ])

    keyboard.append([
        InlineKeyboardButton(text="T2", callback_data="cal_day"),
        InlineKeyboardButton(text="T3", callback_data="cal_day"),
        InlineKeyboardButton(text="T4", callback_data="cal_day"),
        InlineKeyboardButton(text="T5", callback_data="cal_day"),
        InlineKeyboardButton(text="T6", callback_data="cal_day"),
        InlineKeyboardButton(text="T7", callback_data="cal_day"),
        InlineKeyboardButton(text="CN", callback_data="cal_day"),
    ])

    import calendar as cal_module
    cal = cal_module.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    today = date.today()

    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal_day"))
            else:
                current_date = date(year, month, day)
                lunar_month, lunar_day = get_lunar_date(current_date)

                is_today = current_date == today

                if lunar_day == 1 and lunar_month != 1:
                    day_text = f"1/{lunar_month}"
                elif lunar_day == 15:
                    day_text = "15"
                elif lunar_day == 1:
                    day_text = "M1"
                else:
                    day_text = str(lunar_day)

                if is_today:
                    day_text = f"*{day_text}"

                row.append(InlineKeyboardButton(
                    text=day_text,
                    callback_data=f"cal_select_{year}_{month}_{day}"
                ))

        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            text="Xem chi tiet",
            callback_data=f"cal_detail_{year}_{month}"
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_solar_calendar_keyboard(month: int, year: int) -> InlineKeyboardMarkup:
    """Generate inline keyboard calendar for solar dates."""
    month_names = [
        "Thang 1", "Thang 2", "Thang 3", "Thang 4", "Thang 5", "Thang 6",
        "Thang 7", "Thang 8", "Thang 9", "Thang 10", "Thang 11", "Thang 12"
    ]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text="◀",
            callback_data=f"solar_prev_{prev_month}_{prev_year}"
        ),
        InlineKeyboardButton(
            text=f"{month_names[month - 1]} {year}",
            callback_data="solar_current"
        ),
        InlineKeyboardButton(
            text="▶",
            callback_data=f"solar_next_{next_month}_{next_year}"
        ),
    ])

    keyboard.append([
        InlineKeyboardButton(text="T2", callback_data="solar_day"),
        InlineKeyboardButton(text="T3", callback_data="solar_day"),
        InlineKeyboardButton(text="T4", callback_data="solar_day"),
        InlineKeyboardButton(text="T5", callback_data="solar_day"),
        InlineKeyboardButton(text="T6", callback_data="solar_day"),
        InlineKeyboardButton(text="T7", callback_data="solar_day"),
        InlineKeyboardButton(text="CN", callback_data="solar_day"),
    ])

    import calendar as cal_module
    cal = cal_module.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    today = date.today()

    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="solar_day"))
            else:
                is_today = date(year, month, day) == today

                day_text = str(day)
                if is_today:
                    day_text = f"*{day_text}"

                row.append(InlineKeyboardButton(
                    text=day_text,
                    callback_data=f"solar_select_{year}_{month}_{day}"
                ))

        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            text="Xem lich am",
            callback_data=f"solar_to_lunar_{year}_{month}"
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main keyboard with action buttons."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="[+] Them Task",
                    callback_data="add_task",
                ),
                InlineKeyboardButton(
                    text="[*] Danh sach Task",
                    callback_data="list_tasks",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="[!] Nhac nho",
                    callback_data="reminders",
                ),
                InlineKeyboardButton(
                    text="[?] Tro giup",
                    callback_data="help",
                ),
            ],
        ]
    )
    return keyboard


def get_task_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for task actions."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="[X] Hoan thanh",
                    callback_data="task_done",
                ),
                InlineKeyboardButton(
                    text="[S] Sua",
                    callback_data="task_edit",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="[-] Xoa",
                    callback_data="task_delete",
                ),
                InlineKeyboardButton(
                    text="[<] Quay lai",
                    callback_data="back_to_main",
                ),
            ],
        ]
    )
    return keyboard


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="[OK] Xac nhan",
                    callback_data=f"confirm_{action}",
                ),
                InlineKeyboardButton(
                    text="[X] Huy",
                    callback_data=f"cancel_{action}",
                ),
            ],
        ]
    )
    return keyboard
