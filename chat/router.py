import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def route_query(user_message: str) -> dict:
    """
    Handles: Greetings, Time, Date, Relative Days/Months/Years/Hours.
    Does NOT handle: Simple math (2+2, 10*5) -> goes to LLM.
    """
    msg = user_message.lower().strip()

    # ============================================================
    # 1. GREETINGS
    # ============================================================
    if msg in ['hi', 'hello', 'hey']:
        return {'handled': True, 'response': "Hello there! How can I assist you today?"}

    now = datetime.now()
    today = now.date()

    # ============================================================
    # 2. RELATIVE HOURS (Check BEFORE current time)
    # ============================================================
    hour_ago_match = re.search(r'(\d+)\s*hours?\s*(ago|back|before)', msg)
    if hour_ago_match:
        hours = int(hour_ago_match.group(1))
        time = now - timedelta(hours=hours)
        return {'handled': True, 'response': f"{hours} hours ago was {time.strftime('%I:%M %p')}."}

    hour_later_match = re.search(r'(\d+)\s*hours?\s*(from now|from today|later|ahead|after)', msg)
    if hour_later_match:
        hours = int(hour_later_match.group(1))
        time = now + timedelta(hours=hours)
        return {'handled': True, 'response': f"{hours} hours from now will be {time.strftime('%I:%M %p')}."}

    in_hours_match = re.search(r'in\s*(\d+)\s*hours?', msg)
    if in_hours_match:
        hours = int(in_hours_match.group(1))
        time = now + timedelta(hours=hours)
        return {'handled': True, 'response': f"In {hours} hours it will be {time.strftime('%I:%M %p')}."}

    # ============================================================
    # 3. RELATIVE DAYS (Check BEFORE current date)
    # ============================================================
    days_ago_match = re.search(r'(\d+)\s*days?\s*(ago|back|before)', msg)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        date = today - timedelta(days=days)
        return {'handled': True, 'response': f"{days} days ago was {date.strftime('%A, %B %d, %Y')}."}

    days_later_match = re.search(r'(\d+)\s*days?\s*(from now|from today|later|after|ahead)', msg)
    if days_later_match:
        days = int(days_later_match.group(1))
        date = today + timedelta(days=days)
        return {'handled': True, 'response': f"{days} days from now will be {date.strftime('%A, %B %d, %Y')}."}

    in_days_match = re.search(r'in\s*(\d+)\s*days?', msg)
    if in_days_match:
        days = int(in_days_match.group(1))
        date = today + timedelta(days=days)
        return {'handled': True, 'response': f"In {days} days it will be {date.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 4. RELATIVE MONTHS
    # ============================================================
    months_ago_match = re.search(r'(\d+)\s*months?\s*(ago|back|before)', msg)
    if months_ago_match:
        months = int(months_ago_match.group(1))
        date = today - relativedelta(months=months)
        return {'handled': True, 'response': f"{months} months ago was {date.strftime('%A, %B %d, %Y')}."}

    months_later_match = re.search(r'(\d+)\s*months?\s*(from now|from today|later|after|ahead)', msg)
    if months_later_match:
        months = int(months_later_match.group(1))
        date = today + relativedelta(months=months)
        return {'handled': True, 'response': f"{months} months from now will be {date.strftime('%A, %B %d, %Y')}."}

    in_months_match = re.search(r'in\s*(\d+)\s*months?', msg)
    if in_months_match:
        months = int(in_months_match.group(1))
        date = today + relativedelta(months=months)
        return {'handled': True, 'response': f"In {months} months it will be {date.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 5. RELATIVE YEARS
    # ============================================================
    years_ago_match = re.search(r'(\d+)\s*years?\s*(ago|back|before)', msg)
    if years_ago_match:
        years = int(years_ago_match.group(1))
        date = today - relativedelta(years=years)
        return {'handled': True, 'response': f"{years} years ago was {date.strftime('%A, %B %d, %Y')}."}

    years_later_match = re.search(r'(\d+)\s*years?\s*(from now|from today|later|after|ahead)', msg)
    if years_later_match:
        years = int(years_later_match.group(1))
        date = today + relativedelta(years=years)
        return {'handled': True, 'response': f"{years} years from now will be {date.strftime('%A, %B %d, %Y')}."}

    in_years_match = re.search(r'in\s*(\d+)\s*years?', msg)
    if in_years_match:
        years = int(in_years_match.group(1))
        date = today + relativedelta(years=years)
        return {'handled': True, 'response': f"In {years} years it will be {date.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 6. YESTERDAY & TOMORROW (Check AFTER relative patterns)
    # ============================================================
    if 'yesterday' in msg and not any(x in msg for x in ['ago', 'from', 'later', 'after']):
        date = today - timedelta(days=1)
        return {'handled': True, 'response': f"Yesterday was {date.strftime('%A, %B %d, %Y')}."}
    if 'tomorrow' in msg and not any(x in msg for x in ['ago', 'from', 'later', 'after']):
        date = today + timedelta(days=1)
        return {'handled': True, 'response': f"Tomorrow will be {date.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 7. CURRENT TIME (Only if no relative patterns matched)
    # ============================================================
    time_patterns = ['time', 'what time is it', "what's the time", "what is the time", "current time"]
    if any(p in msg for p in time_patterns):
        return {'handled': True, 'response': f"The current time is {now.strftime('%I:%M %p')}."}

    # ============================================================
    # 8. TODAY'S DATE (Only if no relative patterns matched)
    # ============================================================
    date_patterns = ['date', "today's date", "what is today's date", "what's today's date", "what day is today", "current date"]
    if any(p in msg for p in date_patterns):
        return {'handled': True, 'response': f"Today is {now.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 9. EVERYTHING ELSE → LLM
    # ============================================================
    return {'handled': False, 'response': None}