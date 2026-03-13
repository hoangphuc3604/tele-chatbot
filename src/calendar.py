import calendar as cal_module
from datetime import date

from lunarcalendar import Converter, Solar, Lunar


def get_lunar_date(solar_date: date) -> tuple[int, int]:
    solar = Solar(solar_date.year, solar_date.month, solar_date.day)
    lunar = Converter.Solar2Lunar(solar)
    return lunar.month, lunar.day


def generate_calendar_html(month: int, year: int) -> str:
    month_names = [
        "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
        "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
    ]

    cal = cal_module.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    today = date.today()

    lines = []
    lines.append(f"<b>{month_names[month - 1]} {year}</b>")
    lines.append("<b>Lịch Âm Dương</b>")
    lines.append("")
    lines.append("<pre>")

    header = "   T2    T3    T4    T5    T6    T7    CN  "
    lines.append(header)

    for week in month_days:
        line = ""
        for i, day in enumerate(week):
            if day == 0:
                line += "     "
            else:
                current_date = date(year, month, day)
                lunar_month, lunar_day = get_lunar_date(current_date)

                is_today = current_date == today
                is_special = lunar_day in [1, 15]

                day_str = f"{day:2d}"
                if is_today:
                    day_str = f"*{day}"

                lunar_str = ""
                if lunar_day == 1 and lunar_month != 1:
                    lunar_str = f"{lunar_month}/1"
                elif lunar_day == 15:
                    lunar_str = "*15*"
                elif lunar_day == 1:
                    lunar_str = "*M1*"
                else:
                    lunar_str = f"{lunar_day}"

                if is_special:
                    lunar_str = f"*{lunar_str}*"

                line += f"{day_str}{lunar_str:>3} "

        lines.append(line.rstrip())

    lines.append("</pre>")
    lines.append("* = Hom nay | M1 = Mung 1, 15 = Ram")

    return "\n".join(lines)
