"""Callback query handlers for calendar."""

from datetime import date
from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery
from lunarcalendar import Converter, Solar, Lunar

from src.keyboard import get_calendar_keyboard, get_solar_calendar_keyboard


router = Router()


def get_lunar_date_full(solar_date: date):
    solar = Solar(solar_date.year, solar_date.month, solar_date.day)
    lunar = Converter.Solar2Lunar(solar)
    return lunar


@router.callback_query(F.data.startswith("cal_"))
async def handle_calendar_callback(callback: CallbackQuery) -> None:
    data = callback.data

    if data == "cal_current":
        today = date.today()
        keyboard = get_calendar_keyboard(today.month, today.year)
        await callback.message.edit_text(
            f"<b>Lich Am - Thang {today.month} {today.year}</b>\n\nChon ngay de xem chi tiet:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    parts = data.split("_")

    if parts[1] == "prev" or parts[1] == "next":
        month = int(parts[2])
        year = int(parts[3])
        keyboard = get_calendar_keyboard(month, year)
        await callback.message.edit_text(
            f"<b>Lich Am - Thang {month} {year}</b>\n\nChon ngay de xem chi tiet:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    if parts[1] == "select":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        current_date = date(year, month, day)

        lunar = get_lunar_date_full(current_date)

        info = f"<b>Ngay {day}/{month}/{year}</b>\n\n"
        info += f"Am lich: <b>{lunar.day}/{lunar.month}/{lunar.year}</b>\n"

        if lunar.day == 1 and lunar.month != 1:
            info += "Ngay dau thang\n"
        if lunar.day == 1:
            info += "Mung 1\n"
        if lunar.day == 15:
            info += "Ram\n"

        keyboard = get_calendar_keyboard(month, year)

        await callback.message.edit_text(
            info,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    if parts[1] == "detail":
        year = int(parts[2])
        month = int(parts[3])

        info = f"<b>Chi tiet lich am - Thang {month} {year}</b>\n\n"

        import calendar as cal_module
        cal = cal_module.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        for week in month_days:
            week_info = ""
            for day in week:
                if day == 0:
                    continue
                current_date = date(year, month, day)
                lunar = get_lunar_date_full(current_date)

                if lunar.day == 1 or lunar.day == 15:
                    marker = "🔴" if lunar.day == 15 else "🟢"
                    week_info += f"{marker} {lunar.day}/{day}  "
            if week_info:
                info += week_info + "\n"

        keyboard = get_calendar_keyboard(month, year)

        await callback.message.edit_text(
            info,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.answer()


@router.callback_query(F.data.startswith("solar_"))
async def handle_solar_calendar_callback(callback: CallbackQuery) -> None:
    data = callback.data

    if data == "solar_current":
        today = date.today()
        keyboard = get_solar_calendar_keyboard(today.month, today.year)
        await callback.message.edit_text(
            f"<b>Lich Duong - Thang {today.month} {today.year}</b>\n\nHien thi ngay duong + ngay am:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    parts = data.split("_")

    if parts[1] == "prev" or parts[1] == "next":
        month = int(parts[2])
        year = int(parts[3])
        keyboard = get_solar_calendar_keyboard(month, year)
        await callback.message.edit_text(
            f"<b>Lich Duong - Thang {month} {year}</b>\n\nHien thi ngay duong + ngay am:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    if parts[1] == "select":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        current_date = date(year, month, day)

        lunar = get_lunar_date_full(current_date)

        info = f"<b>Ngay {day}/{month}/{year}</b>\n\n"
        info += f"Am lich: <b>{lunar.day}/{lunar.month}/{lunar.year}</b>\n"

        if lunar.day == 1 and lunar.month != 1:
            info += "Ngay dau thang\n"
        if lunar.day == 1:
            info += "Mung 1\n"
        if lunar.day == 15:
            info += "Ram\n"

        keyboard = get_solar_calendar_keyboard(month, year)

        await callback.message.edit_text(
            info,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    if parts[1] == "to_lunar":
        year = int(parts[3])
        month = int(parts[4])
        keyboard = get_calendar_keyboard(month, year)
        await callback.message.edit_text(
            f"<b>Lich Am - Thang {month} {year}</b>\n\nChon ngay de xem chi tiet:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.answer()
