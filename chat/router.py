import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def route_query(user_message: str) -> dict:
    """
    Handles greetings and ALL relative date/time queries, including compound:
      - "1 year 10 days ago"
      - "5 months 40 days ago"
      - "1 year 2 months 50 days ago"
      - "2 hours 30 minutes ago" (coming soon)
    """
    msg = user_message.lower().strip()

    # ============================================================
    # 1. GREETINGS (Exact match)
    # ============================================================
    if msg in ['hi', 'hello', 'hey']:
        return {'handled': True, 'response': "Hello there! How can I assist you today?"}

    now = datetime.now()
    today = now.date()

    # ============================================================
    # 2. YESTERDAY & TOMORROW (quick exact matches)
    # ============================================================
    if msg == 'yesterday':
        date = today - timedelta(days=1)
        return {'handled': True, 'response': f"Yesterday was {date.strftime('%A, %B %d, %Y')}."}
    if msg == 'tomorrow':
        date = today + timedelta(days=1)
        return {'handled': True, 'response': f"Tomorrow will be {date.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 3. COMPOUND DATE/TIME PARSER (Handles any combination)
    # ============================================================
    # Detect direction
    is_ago = any(word in msg for word in ['ago', 'back', 'before'])
    is_future = any(word in msg for word in ['from now', 'later', 'after', 'ahead'])

    # If no direction, but query contains a number + unit, treat as current time/date (handled later)
    direction = None
    if is_ago:
        direction = -1
    elif is_future:
        direction = 1

    # Extract all numeric + unit patterns
    pattern = r'(\d+)\s*(years?|year|months?|month|days?|day|hours?|hour)'
    matches = re.findall(pattern, msg)

    if matches:
        # Aggregate values
        years = 0
        months = 0
        days = 0
        hours = 0

        for num, unit in matches:
            num = int(num)
            unit = unit.lower()
            if unit in ('year', 'years'):
                years += num
            elif unit in ('month', 'months'):
                months += num
            elif unit in ('day', 'days'):
                days += num
            elif unit in ('hour', 'hours'):
                hours += num

        # If no direction is specified, assume "ago" if the message ends with "ago" or "back"
        if direction is None and (msg.endswith('ago') or msg.endswith('back')):
            direction = -1
        elif direction is None and (msg.endswith('from now') or msg.endswith('later') or msg.endswith('after')):
            direction = 1

        # If still no direction, treat as a request for current time/date (skip to later)
        if direction is None:
            # This might be just "5 days" (no ago/future) – we'll let the simple current patterns handle it
            # But we can also assume default "ago" for queries like "5 days ago" which should already have direction
            # We'll simply not handle it here and let the LLM handle it if needed.
            pass

        if direction is not None:
            # Compute target time/date
            delta = relativedelta(
                years=years * direction,
                months=months * direction,
                days=days * direction,
                hours=hours * direction
            )
            target_time = now + delta

            # If hours are involved, reply with time; else reply with date
            if hours > 0 or 'hour' in msg:
                # Time response
                if direction == -1:
                    prefix = f"{years}y {months}m {days}d {hours}h ago" if years or months or days or hours else "Ago"
                    response = f"{years}y {months}m {days}d {hours}h ago was {target_time.strftime('%I:%M %p')}."
                else:
                    response = f"{years}y {months}m {days}d {hours}h from now will be {target_time.strftime('%I:%M %p')}."
                return {'handled': True, 'response': response}
            else:
                # Date response
                if direction == -1:
                    # Build a nice description
                    parts = []
                    if years: parts.append(f"{years} year{'s' if years>1 else ''}")
                    if months: parts.append(f"{months} month{'s' if months>1 else ''}")
                    if days: parts.append(f"{days} day{'s' if days>1 else ''}")
                    desc = ' '.join(parts) + ' ago' if parts else 'Ago'
                    response = f"{desc} was {target_time.strftime('%A, %B %d, %Y')}."
                else:
                    parts = []
                    if years: parts.append(f"{years} year{'s' if years>1 else ''}")
                    if months: parts.append(f"{months} month{'s' if months>1 else ''}")
                    if days: parts.append(f"{days} day{'s' if days>1 else ''}")
                    desc = ' '.join(parts) + ' from now' if parts else 'From now'
                    response = f"{desc} will be {target_time.strftime('%A, %B %d, %Y')}."
                return {'handled': True, 'response': response}

    # ============================================================
    # 4. CURRENT TIME (exact matches, no relative)
    # ============================================================
    time_patterns = ['time', 'what time is it', "what's the time", "what is the time", "current time"]
    if any(p in msg for p in time_patterns):
        return {'handled': True, 'response': f"The current time is {now.strftime('%I:%M %p')}."}

    # ============================================================
    # 5. TODAY'S DATE (exact matches, no relative)
    # ============================================================
    date_patterns = ['date', "today's date", "what is today's date", "what's today's date", "what day is today", "current date"]
    if any(p in msg for p in date_patterns):
        return {'handled': True, 'response': f"Today is {now.strftime('%A, %B %d, %Y')}."}

    # ============================================================
    # 6. EVERYTHING ELSE → LLM
    # ============================================================
    return {'handled': False, 'response': None}