import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'ads_config.json')
TMP_CONFIG_FILE = os.path.join('/tmp', 'ads_config.json') if os.name != 'nt' else CONFIG_FILE

DEFAULT_CONFIG = {
    "admin_password": "admin",
    "shabbat_mode": True,
    "top_ad": {
        "enabled": True,
        "type": "custom",
        "image_url": "https://s.click.aliexpress.com/e/_c4OPcnwd?bz=725*90",
        "link_url": "https://s.click.aliexpress.com/e/_c4OPcnwd?bz=725*90",
        "alt_text": "מבצעים חמים ובלעדיים ב-AliExpress",
        "html_code": ""
    },
    "bottom_ad": {
        "enabled": True,
        "type": "custom",
        "image_url": "https://s.click.aliexpress.com/e/_c4OPcnwd?bz=725*90",
        "link_url": "https://s.click.aliexpress.com/e/_c4OPcnwd?bz=725*90",
        "alt_text": "הנחות מיוחדות וקופונים ב-AliExpress",
        "html_code": ""
    }
}

def load_ads_config():
    # 1. Try reading from /tmp on Vercel (for changes saved via /admin at runtime)
    if TMP_CONFIG_FILE != CONFIG_FILE and os.path.exists(TMP_CONFIG_FILE):
        try:
            with open(TMP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    # 2. Try reading from repository root config file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return DEFAULT_CONFIG

def save_ads_config(config_data):
    saved = False
    
    # Try writing to root file
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        saved = True
    except Exception:
        pass

    # On Vercel / serverless, write to /tmp
    if TMP_CONFIG_FILE != CONFIG_FILE:
        try:
            with open(TMP_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            saved = True
        except Exception:
            pass

    return saved
