import datetime
import urllib.request
import json
import os

# Cache in memory
_shabbat_cache = {
    'last_fetch': None,
    'data': None
}

def get_israel_now():
    """Returns current datetime in Israel (UTC+2 or UTC+3 depending on DST)"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    # Israel is UTC+2 (winter) or UTC+3 (summer)
    # A simple reliable heuristic for Israel DST:
    # DST in Israel is roughly from last Friday before April 2 to last Sunday before Nov 1
    # We can estimate Israel offset:
    month = utc_now.month
    is_dst = 4 <= month <= 10  # April through October is summer time (UTC+3)
    offset_hours = 3 if is_dst else 2
    israel_tz = datetime.timezone(datetime.timedelta(hours=offset_hours))
    return utc_now.astimezone(israel_tz)

def check_shabbat_offline():
    """
    Offline fallback based on Israel weekday and hour:
    Friday: from 17:30 (winter) / 19:15 (summer)
    Saturday: until 18:30 (winter) / 20:30 (summer)
    """
    now = get_israel_now()
    weekday = now.weekday()  # Monday is 0, Friday is 4, Saturday is 5, Sunday is 6
    hour = now.hour + now.minute / 60.0
    is_summer = 4 <= now.month <= 10

    # Friday (4)
    friday_start = 19.0 if is_summer else 16.75  # ~19:00 in summer, ~16:45 in winter
    if weekday == 4 and hour >= friday_start:
        return True, "שבת קודש", "צאת השבת במוצאי שבת"

    # Saturday (5)
    saturday_end = 20.5 if is_summer else 18.0   # ~20:30 in summer, ~18:00 in winter
    if weekday == 5 and hour <= saturday_end:
        return True, "שבת קודש", "צאת השבת במוצאי שבת"

    return False, "", ""

def get_shabbat_status():
    """
    Checks Hebcal API for exact Shabbat / Yom Tov times in Israel.
    Falls back to offline calculation if offline.
    """
    global _shabbat_cache
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Check cache (1 hour valid)
    if _shabbat_cache['last_fetch'] and (now_utc - _shabbat_cache['last_fetch']).total_seconds() < 3600:
        cached = _shabbat_cache['data']
        if cached:
            return cached

    # Try Hebcal API for Israel (Geoname ID 281184 = Jerusalem)
    try:
        url = "https://www.hebcal.com/shabbat?cfg=json&geonameid=281184&M=on"
        req = urllib.request.Request(url, headers={'User-Agent': 'ToolHub-Shabbat-Service/1.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))

            candle_lighting = None
            havdalah = None
            event_name = "שבת קודש"

            for item in data.get('items', []):
                cat = item.get('category')
                date_str = item.get('date') # ISO string e.g. 2026-09-04T18:42:00+03:00

                if date_str:
                    try:
                        # Parse ISO date with tz
                        dt = datetime.datetime.fromisoformat(date_str)
                        if cat == 'candles':
                            candle_lighting = (dt, item.get('title', 'הדלקת נרות'))
                        elif cat == 'havdalah':
                            havdalah = (dt, item.get('title', 'הבדלה'))
                        elif cat == 'holiday' and 'subcat' in item and item['subcat'] == 'major':
                            event_name = item.get('hebrew', event_name)
                    except Exception:
                        pass

            is_active = False
            havdalah_display = ""

            if candle_lighting and havdalah:
                c_dt, c_title = candle_lighting
                h_dt, h_title = havdalah

                if c_dt <= now_utc <= h_dt:
                    is_active = True
                    havdalah_display = h_title

            result = {
                'is_shabbat': is_active,
                'event_title': event_name,
                'havdalah_info': havdalah_display
            }

            _shabbat_cache['last_fetch'] = now_utc
            _shabbat_cache['data'] = result
            return result

    except Exception:
        # Fallback offline
        is_shab, ev_name, hav_info = check_shabbat_offline()
        return {
            'is_shabbat': is_shab,
            'event_title': ev_name,
            'havdalah_info': hav_info
        }
