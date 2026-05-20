import io
import os
import random
import string
import json
import zipfile
from flask import Flask, render_template_string, request, send_file, jsonify, redirect, url_for
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from pdf2image import convert_from_bytes

app = Flask(__name__)
# הגבלת נפח העלאה ל-16MB כדי לשמור על יציבות השרת
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# ==========================================
# הגדרות משתנים גלובליים
# ==========================================
PAYPAL_LINK = "https://www.paypal.me/zarug"
CONTACT_EMAIL = "maor.zarug@gmail.com"

# לוגיקת ניקוד בסיסית פנימית כגיבוי (מיושן, מומלץ להחליף ב-API חיצוני)
def get_internal_nikud(text):
    if not text.strip():
        return ""
    lexicon = {
        "שלום": "👑 שָׁלוֹם", "וברכה": "וּבְרָכָה", "אני": "אֲנִי", "עושה": "עוֹשֶׂה",
        "ניסיון": "נִסָּיוֹן", "ואני": "וַאֲנִי", "רואה": "רוֹאֶה", "שזה": "שֶׁזֶּה",
        "לא": "\u05dc\u05b9\u05d0", "מצליח": "מַצְלִיחַ", "יוסי": "יוֹסִי", "הלך": "הָלַךְ",
        "לטייל": "לְטַיֵּל", "ביער": "בַּיַּעַר", "חסה": "חָסָה", "למרות": "לַמְרוֹת",
        "כל": "כָּל", "הבאסה": "הַבָּאסָה", "שועל": "שׁוּעָל", "מהלך": "מְהַלֵּךְ",
        "בוקר": "בֹּקֶר", "טוב": "טוֹב", "ערב": "עֶרֶב", "אבא": "אַבָּא", "אמא": "אִמָּא"
    }
    words = text.split(" ")
    result = []
    for word in words:
        clean = word.strip()
        punc = ""
        while clean and clean[-1] in ".,?!:;\"'.-":
            punc = clean[-1] + punc
            clean = clean[:-1]
        if clean in lexicon:
            result.append(lexicon[clean] + punc)
        else:
            guessed_word = ""
            for idx, char in enumerate(clean):
                guessed_word += char
                if idx == 0 and char in "אבגדהוזחטיכלמנסעפצקרשת":
                    guessed_word += "ָ"
                elif idx == 1 and len(clean) > 2 and char in "אבגדהוזחטיכלמנסעפצקרשת":
                    guessed_word += "ְ"
            result.append(guessed_word + punc)
    return " ".join(result)

# ==========================================
# תבנית ה-HTML המרכזית (BASE_HTML) - עיצוב זכוכית יוקרתי ומלא
# ==========================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - ToolHub</title>
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9821768397488065"
     crossorigin="anonymous"></script>
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 40%, #311042 100%);
            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --primary: #818cf8;
            --primary-hover: #6366f1;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --success: #34d399;
            --danger: #f87171;
            --radius-lg: 24px;
            --radius-md: 16px;
            --radius-sm: 8px;
            --glass-bg: rgba(255, 255, 255, 0.04);
            --glass-sidebar: rgba(15, 23, 42, 0.4);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-blur: blur(16px);
            --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }

        body {
            font-family: 'Assistant', system-ui, -apple-system, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            display: flex;
            min-height: 100vh;
            background-attachment: fixed;
            overflow-x: hidden;
        }

        /* סרגל צד - Sidebar */
        .sidebar {
            width: 280px;
            background: var(--glass-sidebar);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            color: var(--text-main);
            height: 100vh;
            position: fixed;
            right: 0;
            top: 0;
            display: flex;
            flex-direction: column;
            box-shadow: -4px 0 30px rgba(0,0,0,0.3);
            z-index: 10;
            border-left: 1px solid var(--glass-border);
        }

        .sidebar-header {
            padding: 30px 24px;
            border-bottom: 1px solid var(--glass-border);
        }

        .sidebar-header h2 {
            margin: 0;
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(to left, #818cf8, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }

        .sidebar-menu {
            padding: 20px 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex-grow: 1;
            overflow-y: auto;
        }

        .sidebar a {
            display: flex;
            align-items: center;
            color: var(--text-muted);
            padding: 12px 16px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            border-radius: var(--radius-md);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid transparent;
        }

        .sidebar a:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.03);
            transform: translateX(-2px);
        }

        .sidebar a.active {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            font-weight: 600;
            border-color: var(--glass-border);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .sidebar-footer {
            padding: 24px;
            border-top: 1px solid var(--glass-border);
            font-size: 12px;
            color: #94a3b8;
            text-align: center;
            line-height: 1.5;
        }

        .sidebar-footer a {
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            margin-top: 4px;
        }

        /* תוכן מרכזי */
        /* תוכן מרכזי - תיקון שמונע בריחה של העיצוב הצידה */
.main-content {
    margin-right: 280px; /* השטח שהתפריט תופס */
    flex-grow: 1;
    padding: 40px;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: calc(100% - 280px); /* מוודא שהרוחב לא עובר את קצה המסך */
    box-sizing: border-box;    /* הכי חשוב: זה מונע מה-padding להוסיף רוחב */
    min-height: 100vh;
}

        .container {
            width: 100%;
            max-width: 900px;
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            padding: 40px;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            border: 1px solid var(--glass-border);
            box-sizing: border-box;
        }

        h1 {
            font-size: 28px;
            font-weight: 800;
            text-align: center;
            margin: 0 0 10px 0;
            color: #ffffff;
        }

        .description {
            color: var(--text-muted);
            text-align: center;
            margin-bottom: 40px;
            font-size: 15px;
        }

        /* גריד דאשבורד ראשי */
        .tools-dashboard {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            width: 100%;
            text-align: right;
        }

        .tool-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--glass-border);
            padding: 24px;
            border-radius: var(--radius-md);
            text-decoration: none;
            color: var(--text-main);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .tool-card:hover {
            border-color: var(--primary);
            transform: translateY(-4px);
            background: rgba(255, 255, 255, 0.05);
            box-shadow: 0 12px 20px rgba(0, 0, 0, 0.25);
        }

        .tool-icon {
            font-size: 28px;
            margin-bottom: 4px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
        }

        .tool-title {
            font-size: 17px;
            font-weight: 700;
            color: #ffffff;
        }

        .tool-desc {
            font-size: 13.5px;
            color: var(--text-muted);
            line-height: 1.4;
        }

        /* סביבות עבודה וכלי עריכה */
        .workspace-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            text-align: right;
            width: 100%;
        }

        .window-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            height: 32px;
        }

        .window-label {
            font-size: 14px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .mini-copy-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--glass-border);
            color: #ffffff;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .mini-copy-btn:hover {
            background: var(--primary);
            border-color: var(--primary);
        }

        textarea, .input-modern {
            width: 100%;
            height: 250px;
            padding: 16px;
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-md);
            box-sizing: border-box;
            font-size: 16px;
            font-family: inherit;
            resize: none;
            background: rgba(0, 0, 0, 0.2);
            color: #ffffff;
            line-height: 1.6;
            transition: all 0.2s;
        }

        textarea:focus, .input-modern:focus {
            border-color: var(--primary);
            box-shadow: 0 0 12px rgba(129, 140, 248, 0.2);
            outline: none;
        }

        .input-modern {
            height: auto;
            padding: 12px;
            margin-bottom: 15px;
        }

        .output-area {
            background: rgba(255, 255, 255, 0.02);
            color: #f1f5f9;
        }

        /* גריד כפתורי פעולה */
        .action-grid {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            width: 100%;
            flex-wrap: wrap;
        }

        .btn-action {
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-main);
            border: 1px solid var(--glass-border);
            padding: 10px 16px;
            font-size: 13.5px;
            font-weight: 600;
            cursor: pointer;
            border-radius: var(--radius-md);
            transition: all 0.2s;
        }

        .btn-action:hover {
            background: rgba(255, 255, 255, 0.12);
        }

        .btn-action.active {
            background: rgba(129, 140, 248, 0.2);
            border-color: var(--primary);
            box-shadow: 0 0 10px rgba(129, 140, 248, 0.2);
        }

        /* אזורי העלאת קבצים */
        .file-dropzone {
            border: 2px dashed rgba(255, 255, 255, 0.2);
            padding: 40px 20px;
            border-radius: var(--radius-md);
            background: rgba(0, 0, 0, 0.2);
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 15px;
        }

        .file-dropzone:hover {
            border-color: var(--primary);
            background: rgba(255, 255, 255, 0.02);
        }

        .submit-btn {
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: white;
            border: none;
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            border-radius: var(--radius-md);
            width: 100%;
            margin-top: 5px;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            transition: all 0.2s;
        }

        .submit-btn:hover {
            filter: brightness(1.1);
            transform: translateY(-1px);
        }

        /* הגדרות כלי הניקוד האינטראקטיבי */
        .interactive-output {
            white-space: pre-wrap;
            word-wrap: break-word;
            text-align: right;
            overflow-y: auto;
            direction: rtl;
        }

        .nikud-word {
            display: inline-block;
            white-space: nowrap;
            margin-left: 6px;
        }

        .nikud-char {
            display: inline-block;
            cursor: pointer;
            padding: 0 1px;
            border-radius: 4px;
            transition: all 0.15s;
        }

        .nikud-char:hover {
            background: rgba(129, 140, 248, 0.3);
            color: var(--accent);
        }

        .nikud-char.selected {
            background: var(--primary);
            color: white;
        }

        .nikud-menu {
            display: none;
            position: absolute;
            background: #1e1b4b;
            border: 1px solid var(--primary);
            border-radius: 8px;
            padding: 8px;
            display: none;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            z-index: 1000;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }

        .nikud-menu button {
            background: rgba(255, 255, 255, 0.06);
            color: white;
            border: 1px solid var(--glass-border);
            padding: 6px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 4px;
            min-width: 35px;
        }

        .nikud-menu button:hover {
            background: var(--primary);
        }

        /* מחולל קישורים ווטסאפ */
        .wa-link-anchor {
            display: block;
            color: var(--accent);
            word-break: break-all;
            text-decoration: none;
            font-family: monospace;
            font-size: 15px;
            padding: 14px;
            background: rgba(56, 189, 248, 0.05);
            border: 1px dashed rgba(56, 189, 248, 0.3);
            border-radius: var(--radius-md);
            margin-top: 15px;
            transition: all 0.2s ease;
            text-align: center;
        }

        .wa-link-anchor:hover {
            background: rgba(56, 189, 248, 0.12);
            border-color: var(--accent);
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.15);
        }

        /* כפתור פייפאל מעוצב */
        .paypal-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: linear-gradient(135deg, #ffc439 0%, #ff9600 100%);
            color: #003087;
            font-family: inherit;
            font-size: 16px;
            font-weight: 700;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 30px;
            box-shadow: 0 4px 15px rgba(255, 196, 57, 0.3);
            transition: all 0.2s ease;
            margin-top: 20px;
            border: 1px solid rgba(255, 196, 57, 0.5);
        }

        .paypal-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 196, 57, 0.4);
            filter: brightness(1.05);
        }
        
        /* אזור תצוגה מקדימה לתמונות */
        #previewContainer {
            margin-top: 20px;
            text-align: center;
            display: none; /* מוסתר כברירת מחדל */
            width: 100%;
        }
        
        #imagePreview {
            max-width: 100%;
            max-height: 400px;
            border-radius: var(--radius-md);
            border: 2px solid var(--glass-border);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        /* רספונסיביות למובייל */
        @media (max-width: 768px) {
            body {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                height: auto;
                position: relative;
                border-left: none;
                border-bottom: 1px solid var(--glass-border);
            }

            .sidebar-header {
                padding: 20px;
                text-align: center;
            }

            .sidebar-menu {
                flex-direction: row;
                padding: 10px;
                overflow-x: auto;
                gap: 8px;
                white-space: nowrap;
            }

            .sidebar-footer {
                display: none;
            }

            .main-content {
                margin-right: 0;
                width: 100%;
                padding: 20px 16px;
            }

            .container {
                padding: 25px 20px;
            }

            .tools-dashboard {
                grid-template-columns: 1fr;
            }

            .workspace-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <a href="/" style="text-decoration: none;"><h2>🛠️ ToolHub</h2></a>
            <div style="color: var(--text-muted); font-size: 13px; font-weight: 600; margin-top: 4px;">ארגז הכלים שלך</div>
        </div>
        <div class="sidebar-menu">
            <a href="/" class="{% if current_page == 'dashboard' %}active{% endif %}">🏠 דף הבית</a>
            <a href="/inverter" class="{% if current_page == 'inverter' %}active{% endif %}">🔄 היפוך טקסט ומקלדת</a>
            <a href="/whatsapp" class="{% if current_page == 'whatsapp' %}active{% endif %}">🟢 מחולל קישורי וווטסאפ</a>
            <a href="/nikud" class="{% if current_page == 'nikud' %}active{% endif %}">✍️ ניקוד אוטומטי</a>
            <a href="/pdf-merge" class="{% if current_page == 'pdf-merge' %}active{% endif %}">📄 מיזוג קבצי PDF</a>
            <a href="/pdf-to-img" class="{% if current_page == 'pdf-to-img' %}active{% endif %}">🖼️ PDF לתמונות</a>
            <a href="/pdf-compress" class="{% if current_page == 'pdf-compress' %}active{% endif %}">🗜️ דחיסת קבצי PDF</a>
            <a href="/img-convert" class="{% if current_page == 'img-convert' %}active{% endif %}">🔄 המרת פורמט תמונה</a>
            <a href="/img-resize" class="{% if current_page == 'img-resize' %}active{% endif %}">📐 שינוי גודל תמונה</a>
            <a href="/img-effects" class="{% if current_page == 'img-effects' %}active{% endif %}">🎨 פילטרים ואפקטים</a>
            <a href="/about" class="{% if current_page == 'about' %}active{% endif %}">ℹ️ אודות הפרויקט</a>
        </div>
        <div class="sidebar-footer">
            <span>💡 מצאתם באג? יש לכם רעיון?</span><br>
            <a href="mailto:maor.zarug@gmail.com" style="cursor: pointer; pointer-events: auto;">שלחו לנו משוב במייל</a>
        </div>
    </div>

    <div class="main-content">
        <div class="ad-container" style="background: rgba(0,0,0,0.2); border: 1px dashed var(--glass-border); padding: 15px; margin: 0 auto 20px auto; width:100%; max-width:900px; color:var(--text-muted); font-size:12px; text-align:center; border-radius:var(--radius-md); box-sizing:border-box;">    
            💰 אזור פרסום פרימיום עליון (Google AdSense)
        </div>

        <div class="container">
            <h1>{{ title }}</h1>
            <div class="description">{{ description }}</div>

            {% if current_page == 'dashboard' %}
                <div class="tools-dashboard">
                    <a href="/inverter" class="tool-card">
                        <div class="tool-icon">🔄</div>
                        <div class="tool-title">היפוך טקסט ומקלדת</div>
                        <div class="tool-desc">היפוך אותיות, שורות ותיקון ג'יבריש מקלדת בלייב ללא טעינת עמוד.</div>
                    </a>
                    <a href="/whatsapp" class="tool-card">
                        <div class="tool-icon">🟢</div>
                        <div class="tool-title">מחולל קישורי וווטסאפ</div>
                        <div class="tool-desc">יצירת קישור ישיר לשיחת וווטסאפ עם הודעה מוכנה מראש בלייב לחלוטין.</div>
                    </a>
                    <a href="/nikud" class="tool-card">
                        <div class="tool-icon">✍️</div>
                        <div class="tool-title">ניקוד טקסט אוטומטי</div>
                        <div class="tool-desc">הוספת ניקוד דקדוקי חכם למשפטים בעברית בלייב עם ממשק עריכה ידני.</div>
                    </a>
                    <a href="/pdf-merge" class="tool-card">
                        <div class="tool-icon">📄</div>
                        <div class="tool-title">מיזוג קבצי PDF</div>
                        <div class="tool-desc">העלאת מספר קבצי PDF ואיחודם המלא לקובץ אחד מהיר ויציב להורדה.</div>
                    </a>
                    <a href="/pdf-to-img" class="tool-card">
                        <div class="tool-icon">🖼️</div>
                        <div class="tool-title">PDF לתמונות</div>
                        <div class="tool-desc">העלאת קובץ PDF ופירוק כל הדפים שלו לתמונות JPEG נפרדות בתוך קובץ ZIP.</div>
                    </a>
                    <a href="/pdf-compress" class="tool-card">
                        <div class="tool-icon">🗜️</div>
                        <div class="tool-title">דחיסת קבצי PDF</div>
                        <div class="tool-desc">הקטנת נפח קובץ PDF באמצעות אופטימיזציה פנימית מבלי לפגוע באיכות.</div>
                    </a>
                    <a href="/img-convert" class="tool-card">
                        <div class="tool-icon">🔄</div>
                        <div class="tool-title">המרת פורמט תמונה</div>
                        <div class="tool-desc">שינוי פורמט מהיר בין קבצי PNG, JPEG, WEBP, ו-BMP בצורה חלקה.</div>
                    </a>
                    <a href="/img-resize" class="tool-card">
                        <div class="tool-icon">📐</div>
                        <div class="tool-title">שינוי גודל תמונה</div>
                        <div class="tool-desc">שינוי רזולוציה ומימדים (רוחב וגובה) של תמונות בהתאמה אישית מדויקת.</div>
                    </a>
                    <a href="/img-effects" class="tool-card">
                        <div class="tool-icon">🎨</div>
                        <div class="tool-title">פילטרים ואפקטים</div>
                        <div class="tool-desc">הוספת פילטרים של שחור-לבן, טשטוש, ניגודיות וחדות לתמונה שלך בשני קליקים.</div>
                    </a>
                </div>

            {% elif current_page == 'about' %}
                <div class="about-text" style="text-align: center;">
                    <div class="about-card-badge" style="display: inline-block; background: rgba(129, 140, 241, 0.2); color: #a5b4fc; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; margin-bottom: 15px; border: 1px solid var(--glass-border);">❤️ פרויקט ללא מטרת רווח - לתועלת הציבור</div>
                    <p style="text-align: right; margin-bottom: 15px;">ברוכים הבאים ל-<strong>ToolHub</strong>! האתר הזה נולד מתוך רעיון פשוט: לתת לציבור בישראל ארגז כלים דיגיטלי מתקדם, מהיר ואיכותי - <strong>בחינם לחלוטין וללא צורך בהרשמה</strong>.</p>
                    <p style="text-align: right; margin-bottom: 15px;">כל הכלים באתר זה נבנו במטרה אחת: לעשות חסד, להקל על היום-יום שלכם ולחסוך לכם זמן יקר. בין אם אתם סטודנטים, בעלי עסקים שצריכים קישור מהיר לווטסאפ, או כותבי תוכן שזקוקים לניקוד או היפוך טקסט - אנחנו כאן בשבילכם.</p>
                    <p style="text-align: right; margin-bottom: 25px;"><strong>למה יש פרסומות באתר?</strong><br>השירותים והכלים תמיד יישארו חינמיים ב-100%. הפרסומות באתר נועדו אך ורק כדי לעזור לנו לממן את עלויות השרתים, ולאפשר לנו להמשיך להחזיק את פרויקט החסד הזה באוויר עבור כולם.</p>
                    
                    <div style="margin: 30px 0; padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); border-radius: var(--radius-md);">
                        <p style="font-weight: 700; font-size: 17px; margin-bottom: 10px; color: #ffffff;">☕ אהבתם את האתר? נשמח לתמיכה שלכם!</p>
                        <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 15px;">אם הכלים שלנו עזרו לכם וחסכו לכם זמן, אתם מוזמנים להביע הערכה ולתרום למימון המשך פיתוח השרתים:</p>
                        <a href="{{ PAYPAL_LINK }}" target="_blank" class="paypal-button">
                            <span>💙 תמיכה ותרומה מאובטחת באמצעות PayPal</span>
                        </a>
                    </div>
                </div>

            {% elif current_page == 'inverter' %}
                <div class="workspace-grid">
                    <div>
                        <div class="window-header"><span class="window-label">✍️ הטקסט המקורי שלך:</span></div>
                        <textarea id="srcText" placeholder="הקלד או הדבק כאן את הטקסט..." oninput="processText()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">📋 התוצאה המעובדת:</span>
                            <button id="copyBtn" class="mini-copy-btn" onclick="copyResult('dstText', 'copyBtn')">📋 העתק הכל</button>
                        </div>
                        <textarea id="dstText" class="output-area" placeholder="התוצאה המעובדת תופיע כאן אוטומטית..." readonly></textarea>
                    </div>
                </div>
                <div class="action-grid">
                    <button id="btn-full" class="btn-action active" onclick="setMode('full')">🔄 היפוך מלא</button>
                    <button id="btn-lines" class="btn-action" onclick="setMode('lines')">📝 בתוך שורות</button>
                    <button id="btn-no_num" class="btn-action" onclick="setMode('no_num')">🔢 בלי מספרים</button>
                    <button id="btn-no_eng" class="btn-action" onclick="setMode('no_eng')">🔤 בלי אנגלית</button>
                    <button id="btn-eng2heb" class="btn-action" style="color: var(--accent);" onclick="setMode('eng2heb')">⌨️ אנגלית ⬅️ עברית</button>
                    <button id="btn-heb2eng" class="btn-action" style="color: var(--danger);" onclick="setMode('heb2eng')">⌨️ עברית ⬅️ אנגלית</button>
                </div>
                <script>
                    let currentMode = 'full';
                    const engToHebMap = {'q': '/', 'w': "'", 'e': 'ק', 'r': 'ר', 't': 'א', 'y': 'ט', 'u': 'ו', 'i': 'ן', 'o': 'ם', 'p': 'פ', 'a': 'ש', 's': 'ד', 'd': 'ג', 'f': 'כ', 'g': 'ע', 'h': 'י', 'j': 'ח', 'k': 'ל', 'l': 'ך', ';': 'ף', "'": ',', 'z': 'ז', 'x': 'ס', 'c': 'ב', 'v': 'ה', 'b': 'נ', 'n': 'מ', 'm': 'צ', ',': 'ת', '.': 'ץ', '/': '.'};
                    const hebToEngMap = {}; for (let k in engToHebMap) { hebToEngMap[engToHebMap[k]] = k; }

                    function setMode(mode) {
                        currentMode = mode;
                        document.querySelectorAll('.btn-action').forEach(btn => btn.classList.remove('active'));
                        document.getElementById('btn-' + mode).classList.add('active');
                        processText();
                    }

                    function processText() {
                        const src = document.getElementById('srcText').value;
                        let result = "";
                        if (currentMode === 'full') {
                            result = src.split('').reverse().join('');
                        } else if (currentMode === 'lines') {
                            result = src.split('\\n').map(line => line.split('').reverse().join('')).join('\\n');
                        } else if (currentMode === 'no_num') {
                            result = src.split('').reverse().join('').replace(/\\d+/g, m => m.split('').reverse().join(''));
                        } else if (currentMode === 'no_eng') {
                            result = src.split('').reverse().join('').replace(/[a-zA-Z]+/g, m => m.split('').reverse().join(''));
                        } else if (currentMode === 'eng2heb' || currentMode === 'heb2eng') {
                            const map = (currentMode === 'eng2heb') ? engToHebMap : hebToEngMap;
                            for (let i = 0; i < src.length; i++) {
                                let char = src[i].toLowerCase();
                                result += map[char] ? map[char] : src[i];
                            }
                        }
                        document.getElementById('dstText').value = result;
                    }

                    function copyResult(targetId, btnId) {
                        const target = document.getElementById(targetId);
                        if (!target.value.trim()) return;
                        navigator.clipboard.writeText(target.value).then(() => {
                            const btn = document.getElementById(btnId);
                            const oldText = btn.innerText;
                            btn.innerText = "✅ הועתק!";
                            btn.style.background = "var(--success)";
                            setTimeout(() => { btn.innerText = oldText; btn.style.background = ""; }, 2000);
                        });
                    }
                </script>

            {% elif current_page == 'whatsapp' %}
                <div class="workspace-grid">
                    <div>
                        <label class="window-label">📱 מספר טלפון (למשל 0501234567):</label>
                        <input type="text" id="waPhone" class="input-modern" placeholder="הכנס מספר טלפון..." oninput="processWhatsapp()">
                        <label class="window-label">💬 הודעה מוכנה מראש (אופציונלי):</label>
                        <textarea id="waMsg" style="height: 120px;" placeholder="הקלד את ההודעה שתפתח אוטומטית בשיחה..." oninput="processWhatsapp()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">🔗 הקישור המוכן שלך:</span>
                            <button id="waCopyBtn" class="mini-copy-btn" onclick="copyResult('waDst', 'waCopyBtn')">📋 העתק קישור</button>
                        </div>
                        <textarea id="waDst" class="output-area" style="height: 110px; font-family: monospace; font-size: 14px; color: var(--accent);" placeholder="הקישור הגולמי ייווצר כאן..." readonly></textarea>
                        
                        <div style="margin-top: 15px;">
                            <span class="window-label" style="display: block; margin-bottom: 6px;">🚀 קישור ישיר ללחיצה מיידית:</span>
                            <a id="waDirectLink" href="#" target="_blank" class="wa-link-anchor" style="display: none;">לחץ כאן כדי לפתוח את הווטסאפ</a>
                            <div id="waPlaceholder" style="text-align: center; padding: 20px; color: rgba(255,255,255,0.15); border: 1px dashed rgba(255,255,255,0.05); border-radius: var(--radius-md); font-size: 14px;">הזן מספר טלפון כדי להפעיל את הקישור המהיר...</div>
                        </div>
                    </div>
                </div>
                <script>
                    function processWhatsapp() {
                        let phone = document.getElementById('waPhone').value.trim();
                        const msg = document.getElementById('waMsg').value;
                        const linkTxt = document.getElementById('waDst');
                        const directBtn = document.getElementById('waDirectLink');
                        const placeholder = document.getElementById('waPlaceholder');

                        if (!phone) {
                            linkTxt.value = "";
                            directBtn.style.display = "none";
                            placeholder.style.display = "block";
                            return;
                        }
                        if (phone.startsWith('0')) { phone = '972' + phone.substring(1); }
                        phone = phone.replace(/[^0-9]/g, '');
                        let url = "https://wa.me/" + phone;
                        if (msg.trim()) { url += "?text=" + encodeURIComponent(msg); }

                        linkTxt.value = url;
                        directBtn.href = url;
                        directBtn.style.display = "block";
                        placeholder.style.display = "none";
                    }
                    function copyResult(targetId, btnId) {
                        const target = document.getElementById(targetId);
                        if (!target.value.trim()) return;
                        navigator.clipboard.writeText(target.value).then(() => {
                            const btn = document.getElementById(btnId);
                            const oldText = btn.innerText;
                            btn.innerText = "✅ הועתק!";
                            btn.style.background = "var(--success)";
                            setTimeout(() => { btn.innerText = oldText; btn.style.background = ""; }, 2000);
                        });
                    }
                </script>

            {% elif current_page == 'nikud' %}
                <div class="workspace-grid">
                    <div>
                        <div class="window-header"><span class="window-label">✍️ הקלד משפט חופשי בעברית:</span></div>
                        <textarea id="nikudSrc" placeholder="הקלד כאן כל משפט חופשי בעברית..." oninput="processNikud()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">💡 לחץ על אות לתיקון הניקוד הידני:</span>
                            <button id="nikudCopyBtn" class="mini-copy-btn" onclick="copyInteractiveText()">📋 העתק הכל</button>
                        </div>
                        <div id="nikudDst" class="output-area interactive-output" style="height: 250px; border: 1px solid var(--glass-border); border-radius: var(--radius-md); padding: 16px; background: rgba(0, 0, 0, 0.2);"></div>
                    </div>
                </div>

                <div id="nikudPopupMenu" class="nikud-menu">
                    <button onclick="applyNikud('')">❌</button>
                    <button onclick="applyNikud('\\u05B8')">ָ</button>
                    <button onclick="applyNikud('\\u05B7')">ַ</button>
                    <button onclick="applyNikud('\\u05B5')">ֵ</button>
                    <button onclick="applyNikud('\\u05B6')">ֶ</button>
                    <button onclick="applyNikud('\\u05B4')">ִ</button>
                    <button onclick="applyNikud('\\u05B9')">ֹ</button>
                    <button onclick="applyNikud('\\u05BB')">ֻ</button>
                    <button onclick="applyNikud('\\u05B0')">ְ</button>
                    <button onclick="applyNikud('\\u05BC')">ּ</button>
                    <button onclick="applyNikud('\\u05C1')">ׁ</button>
                    <button onclick="applyNikud('\\u05C2')">ׂ</button>
                </div>

                <script>
                    let timeout = null;
                    let selectedCharSpan = null;

                    function processNikud() {
                        const text = document.getElementById('nikudSrc').value;
                        if (!text.trim()) { document.getElementById('nikudDst').innerHTML = ""; return; }
                        
                        clearTimeout(timeout);
                        timeout = setTimeout(() => {
                            fetch('/api/nikud', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: text })
                            })
                            .then(res => res.json())
                            .then(data => {
                                renderInteractiveNikud(data.result);
                            });
                        }, 500);
                    }

                    function renderInteractiveNikud(processedText) {
                        const container = document.getElementById('nikudDst');
                        container.innerHTML = "";
                        
                        const words = processedText.split(" ");
                        words.forEach(word => {
                            const wordSpan = document.createElement('span');
                            wordSpan.className = 'nikud-word';
                            
                            let i = 0;
                            while(i < word.length) {
                                let char = word[i];
                                let nikud = "";
                                i++;
                                while(i < word.length && word[i].charCodeAt(0) >= 0x05B0 && word[i].charCodeAt(0) <= 0x05C4) {
                                    nikud += word[i];
                                    i++;
                                }
                                
                                const charSpan = document.createElement('span');
                                charSpan.className = 'nikud-char';
                                charSpan.innerText = char + nikud;
                                charSpan.dataset.baseChar = char;
                                charSpan.dataset.currentNikud = nikud;
                                
                                charSpan.onclick = function(e) {
                                    e.stopPropagation();
                                    if(selectedCharSpan) selectedCharSpan.classList.remove('selected');
                                    selectedCharSpan = charSpan;
                                    charSpan.classList.add('selected');
                                    showNikudMenu(e.pageX, e.pageY);
                                };
                                wordSpan.appendChild(charSpan);
                            }
                            container.appendChild(wordSpan);
                        });
                    }

                    function showNikudMenu(x, y) {
                        const menu = document.getElementById('nikudPopupMenu');
                        menu.style.display = 'grid';
                        menu.style.left = x + 'px';
                        menu.style.top = y + 'px';
                    }

                    function applyNikud(nikudChar) {
                        if(selectedCharSpan) {
                            const base = selectedCharSpan.dataset.baseChar;
                            selectedCharSpan.innerText = base + nikudChar;
                            selectedCharSpan.dataset.currentNikud = nikudChar;
                            selectedCharSpan.classList.remove('selected');
                        }
                        document.getElementById('nikudPopupMenu').style.display = 'none';
                    }

                    function copyInteractiveText() {
                        let resultText = "";
                        const words = document.querySelectorAll('.nikud-word');
                        words.forEach((w, idx) => {
                            w.querySelectorAll('.nikud-char').forEach(c => {
                                resultText += c.innerText;
                            });
                            if(idx < words.length - 1) resultText += " ";
                        });
                        
                        if(!resultText.trim()) return;
                        
                        navigator.clipboard.writeText(resultText).then(() => {
                            const btn = document.getElementById('nikudCopyBtn');
                            const old = btn.innerText;
                            btn.innerText = "✅ הועתק!";
                            btn.style.background = "var(--success)";
                            setTimeout(() => { btn.innerText = old; btn.style.background = ""; }, 2000);
                        });
                    }

                    document.onclick = function() {
                        document.getElementById('nikudPopupMenu').style.display = 'none';
                        if(selectedCharSpan) selectedCharSpan.classList.remove('selected');
                    };
                </script>

            {% elif current_page == 'pdf-merge' %}
                <form action="/action/pdf-merge" method="POST" enctype="multipart/form-data" style="text-align: right;">
                    <label class="window-label">📁 בחר קבצי PDF למיזוג (ניתן לבחור כמה קבצים יחד):</label>
                    <div class="file-dropzone" onclick="document.getElementById('pdfFiles').click()">
                        <div style="font-size: 32px; margin-bottom: 10px;">📥</div>
                        <div style="font-weight: 600; font-size: 15px;">לחץ כאן לבחירת קבצים ממחשבך</div>
                        <div style="color: var(--text-muted); font-size: 13px; margin-top: 5px;">ניתן להעלות קבצים מרובים במקביל</div>
                        <input type="file" id="pdfFiles" name="files" multiple accept=".pdf" style="display: none;" onchange="updateFileCount(this, 'fileCountPdf')">
                        <div id="fileCountPdf" style="margin-top: 12px; font-weight: 700; color: var(--accent);"></div>
                    </div>
                    <button type="submit" class="submit-btn">⚡ מיזוג קבצים והורדת התוצאה</button>
                </form>

            {% elif current_page == 'pdf-to-img' %}
                <form action="/action/pdf-to-img" method="POST" enctype="multipart/form-data" style="text-align: right;">
                    <label class="window-label">📁 בחר קובץ PDF לפירוק לתמונות:</label>
                    <div class="file-dropzone" onclick="document.getElementById('pdfToImgFile').click()">
                        <div style="font-size: 32px; margin-bottom: 10px;">🖼️</div>
                        <div style="font-weight: 600; font-size: 15px;">לחץ כאן לבחירת קובץ PDF מסוים</div>
                        <input type="file" id="pdfToImgFile" name="file" accept=".pdf" style="display: none;" onchange="updateFileCount(this, 'fileCountImg')">
                        <div id="fileCountImg" style="margin-top: 12px; font-weight: 700; color: var(--accent);"></div>
                    </div>
                    <button type="submit" class="submit-btn">⚡ חלץ דפים לתמונות (ZIP)</button>
                </form>

            {% elif current_page == 'pdf-compress' %}
                <form action="/action/pdf-compress" method="POST" enctype="multipart/form-data" style="text-align: right;">
                    <label class="window-label">🗜️ העלה קובץ PDF לדחיסה אופטימלית:</label>
                    <div class="file-dropzone" onclick="document.getElementById('pdfCompFile').click()">
                        <div style="font-size: 32px; margin-bottom: 10px;">🗜️</div>
                        <div style="font-weight: 600; font-size: 15px;">לחץ להעלאת הקובץ לדחיסה</div>
                        <input type="file" id="pdfCompFile" name="file" accept=".pdf" style="display: none;" onchange="updateFileCount(this, 'fileCountComp')">
                        <div id="fileCountComp" style="margin-top: 12px; font-weight: 700; color: var(--accent);"></div>
                    </div>
                    <button type="submit" class="submit-btn">⚡ בצע דחיסה והורד מסמך רזה</button>
                </form>

            {% elif current_page == 'img-convert' %}
                <form action="/action/img-convert" method="POST" enctype="multipart/form-data" style="text-align: right;">
                    <label class="window-label">🖼️ בחר תמונה מקורית להמרה:</label>
                    <div class="file-dropzone" onclick="document.getElementById('imgConvFile').click()">
                        <div style="font-size: 32px; margin-bottom: 10px;">🔄</div>
                        <div style="font-weight: 600; font-size: 15px;">לחץ לבחירת קובץ תמונה</div>
                        <input type="file" id="imgConvFile" name="file" accept="image/*" style="display: none;" onchange="updateFileCount(this, 'fileCountConv')">
                        <div id="fileCountConv" style="margin-top: 12px; font-weight: 700; color: var(--accent);"></div>
                    </div>
                    <label class="window-label">🎯 בחר את פורמט היעד המבוקש:</label>
                    <select name="format" class="input-modern" style="background-color: #1e1b4b; border-radius: var(--radius-sm); color:#fff; height: 45px;">
                        <option value="JPEG">JPEG (.jpg)</option>
                        <option value="PNG">PNG (.png)</option>
                        <option value="WEBP">WEBP (.webp)</option>
                        <option value="BMP">BMP (.bmp)</option>
                    </select>
                    <button type="submit" class="submit-btn">⚡ המר פורמט והורד תמונה</button>
                </form>

            {% elif current_page == 'img-resize' %}
                <form action="/action/img-resize" method="POST" enctype="multipart/form-data" style="text-align: right;">
                    <label class="window-label">🖼️ בחר תמונה לשינוי מימדים:</label>
                    <div class="file-dropzone" onclick="document.getElementById('imgResFile').click()">
                        <div style="font-size: 32px; margin-bottom: 10px;">📐</div>
                        <div style="font-weight: 600; font-size: 15px;">לחץ לבחירת קובץ תמונה מהמחשב</div>
                        <input type="file" id="imgResFile" name="file" accept="image/*" style="display: none;" onchange="updateFileCount(this, 'fileCountRes')">
                        <div id="fileCountRes" style="margin-top: 12px; font-weight: 700; color: var(--accent);"></div>
                    </div>
                    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                        <div style="flex: 1;">
                            <label class="window-label">📐 רוחב פיקסלים רצוי (Width):</label>
                            <input type="number" name="width" class="input-modern" placeholder="למשל: 800" required>
                        </div>
                        <div style="flex: 1;">
                            <label class="window-label">📐 גובה פיקסלים רצוי (Height):</label>
                            <input type="number" name="height" class="input-modern" placeholder="למשל: 600" required>
                        </div>
                    </div>
                    <button type="submit" class="submit-btn">⚡ שנה מימדי תמונה והורד קובץ</button>
                </form>

            {% elif current_page == 'img-effects' %}
                <form id="effectForm" style="text-align: right;">
                    <label class="window-label">🎨 בחר תמונה להחלת פילטרים מתקדמים:</label>
                    <div class="file-dropzone" onclick="document.getElementById('imgEffFile').click()">
                        <div style="font-size: 32px; margin-bottom: 10px;">🎨</div>
                        <div style="font-weight: 600; font-size: 15px;">לחץ לבחירת תמונה לעיבוד</div>
                        <input type="file" id="imgEffFile" name="file" accept="image/*" style="display: none;" onchange="handleFileSelect(this)">
                        <div id="fileCountEff" style="margin-top: 12px; font-weight: 700; color: var(--accent);"></div>
                    </div>
                    
                    <label class="window-label">🎯 בחר אפקט או פילטר אמנותי:</label>
                    <select id="effectSelect" name="effect" class="input-modern" style="background-color: #1e1b4b; border-radius: var(--radius-sm); color:#fff; height: 45px;">
                        <option value="grayscale">📷 שחור לבן קלאסי (Grayscale)</option>
                        <option value="blur">🌫️ אפקט טשטוש עדין (Blur)</option>
                        <option value="contour">✏️ רישום קווי מתאר (Contour Sketch)</option>
                        <option value="brighten">☀️ הגברת בהירות וצבע (Brighten)</option>
                        <option value="sharpen">🔍 הגברת חדות פרטים (Sharpen)</option>
                    </select>
                    
                    <button type="button" class="submit-btn" onclick="applyEffectAndPreview()">⚡ החל אפקט והצג תצוגה מקדימה</button>
                    
                    <div id="previewContainer">
                        <label class="window-label" style="display: block; margin-top: 20px;">👀 תצוגה מקדימה (JPEG):</label>
                        <img id="imagePreview" src="" alt="תצוגה מקדימה של האפקט">
                        <br>
                        <button type="button" class="btn-action" style="background: var(--success); margin-top: 15px; width: auto;" onclick="downloadProcessedImage()">💾 הורד תמונה סופית (JPEG)</button>
                    </div>
                </form>

                <script>
                    let currentProcessedBlob = null; // משתנה גלובלי לשמירת התמונה המעובדת
                    
                    // עדכון טקסט הקובץ הנבחר
                    function handleFileSelect(input) {
                        const count = input.files.length;
                        const target = document.getElementById('fileCountEff');
                        if (count > 0) {
                            target.innerText = " 🖼️ תמונה נבחרה מוכנה לעיבוד!";
                            // הסתרת תצוגה מקדימה קודמת אם קיימת
                            document.getElementById('previewContainer').style.display = 'none';
                        } else {
                            target.innerText = "";
                        }
                    }

                    // שליחת הטופס ב-AJAX והצגת התוצאה
                    function applyEffectAndPreview() {
                        const fileInput = document.getElementById('imgEffFile');
                        const effectSelect = document.getElementById('effectSelect');
                        
                        if (fileInput.files.length === 0) {
                            alert("אנא בחר תמונה תחילה.");
                            return;
                        }
                        
                        // יצירת FormData לשליחת הקובץ והאפקט
                        const formData = new FormData();
                        formData.append('file', fileInput.files[0]);
                        formData.append('effect', effectSelect.value);
                        
                        const btn = event.target;
                        const oldText = btn.innerText;
                        btn.innerText = "⏳ מעבד תמונה...";
                        btn.disabled = true;

                        // שליחת הבקשה לשרת
                        fetch('/action/img-effects-preview', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => {
                            if (!response.ok) throw new Error('שגיאה בעיבוד התמונה.');
                            return response.blob(); // קבלת התמונה כ-Blob
                        })
                        .then(blob => {
                            currentProcessedBlob = blob; // שמירה להורדה מאוחרת
                            const url = URL.createObjectURL(blob); // יצירת URL מקומי לתצוגה
                            const previewImg = document.getElementById('imagePreview');
                            const previewContainer = document.getElementById('previewContainer');
                            
                            // טעינת התמונה לאלמנט ה-img והצגת המיכל
                            previewImg.src = url;
                            previewContainer.style.display = 'block';
                            
                            btn.innerText = oldText;
                            btn.disabled = false;
                        })
                        .catch(error => {
                            console.error(error);
                            alert("אירעה שגיאה בעיבוד התמונה.");
                            btn.innerText = oldText;
                            btn.disabled = false;
                        });
                    }
                    
                    // פונקציה להורדת התמונה שנמצאת בתצוגה המקדימה
                    function downloadProcessedImage() {
                        if (!currentProcessedBlob) return;
                        
                        // יצירת קישור פיקטיבי והפעלת לחיצה עליו
                        const url = URL.createObjectURL(currentProcessedBlob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'toolhub_processed_image.jpg'; // סיומת JPEG
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url); // ניקוי ה-URL מהזיכרון
                    }
                </script>
            {% endif %}

        </div>
    </div>
    
    <script>
        // פונקציה כללית לעדכון תצוגת כמות קבצים שנבחרו
        function updateFileCount(input, targetId) {
            const count = input.files.length;
            const target = document.getElementById(targetId);
            if (count > 1) {
                target.innerText = " 📂 " + count + " קבצים נבחרו ומוכנים!";
            } else if (count === 1) {
                target.innerText = " 📄 קובץ אחד נבחר ומוכן!";
            } else {
                target.innerText = "";
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# נתבי ניווט השרת (Flask Route Handlers)
# ==========================================

@app.route('/')
def home():
    return render_template_string(BASE_HTML, current_page='dashboard', title='דף הבית', description='ברוכים הבאים ל-ToolHub! בחרו כלי דיגיטלי מתקדם מתפריט הצד כדי להתחיל.')

@app.route('/inverter')
def inverter():
    return render_template_string(BASE_HTML, current_page='inverter', title='🔄 היפוך טקסט ומקלדת', description='הפוך טקסטים, תקן בעיות כיווניות של עברית/אנגלית או תקן שורות הפוכות בלייב.')
@app.route('/ads.txt')
def ads_txt():
    return "google.com, pub-9821768397488065, DIRECT, f08c47fec0942fa0", 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/whatsapp')
def whatsapp():
    return render_template_string(BASE_HTML, current_page='whatsapp', title='🟢 מחולל קישורי וווטסאפ', description='צור קישור ישיר לשיחת וווטסאפ מותאם אישית הכולל הודעה מובנית מראש.')

@app.route('/nikud')
def nikud_page():
    return render_template_string(BASE_HTML, current_page='nikud', title='✍️ ניקוד טקסט אוטומטי', description='הזן משפט בעברית לקבלת ניקוד אוטומטי, עם אפשרות לשינוי ידני בתפריט צף.')

@app.route('/pdf-merge')
def pdf_merge_page():
    return render_template_string(BASE_HTML, current_page='pdf-merge', title='📄 מיזוג קבצי PDF', description='מזג והערם מספר קבצי PDF נפרדים לכדי מסמך אחד שלם מאוחד.')

@app.route('/pdf-to-img')
def pdf_to_img_page():
    return render_template_string(BASE_HTML, current_page='pdf-to-img', title='🖼️ המרת PDF לתמונות', description='פירוק מסמך PDF לתמונות JPEG נפרדות בתוך קובץ ZIP אחד להורדה.')

@app.route('/pdf-compress')
def pdf_compress_page():
    return render_template_string(BASE_HTML, current_page='pdf-compress', title='🗜️ דחיסת קבצי PDF', description='צמצם את המשקל הפיזי של קבצי PDF לטובת שליחה קלה במייל ובאתרים ממשלתיים.')

@app.route('/img-convert')
def img_convert_page():
    return render_template_string(BASE_HTML, current_page='img-convert', title='🔄 המרת פורמט תמונה', description='שנה את סוג קובץ התמונה שלך לפורמט נפוץ אחר (PNG, JPEG, WEBP, BMP) מיידית.')

@app.route('/img-resize')
def img_resize_page():
    return render_template_string(BASE_HTML, current_page='img-resize', title='📐 שינוי גודל תמונה', description='התאם את ממדי הגובה והרוחב של התמונה בפיקסלים מדויקים.')

@app.route('/img-effects')
def img_effects_page():
    return render_template_string(BASE_HTML, current_page='img-effects', title='🎨 פילטרים ואפקטים לתמונות', description='עצב את התמונה WITH פילטרים: טשטוש, שחור-לבן, רישום וחדות. כולל תצוגה מקדימה והורדת JPEG.')

@app.route('/about')
def about():
    return render_template_string(BASE_HTML, current_page='about', title='ℹ️ אודות הפרויקט', description='הכירו את הסיפור מאחורי ToolHub ומדוע הקמנו אותו.', PAYPAL_LINK=PAYPAL_LINK)

# ==========================================
# פעולות ועיבודי קצה (API Backends & Logic)
# ==========================================

@app.route('/api/nikud', methods=['POST'])
def api_nikud():
    data = request.get_json() or {}
    text = data.get('text', '')
    result_text = get_internal_nikud(text)
    return jsonify({'result': result_text})

@app.route('/action/pdf-merge', methods=['POST'])
def action_pdf_merge():
    files = request.files.getlist('files')
    if not files or files[0].filename == '': return "לא נבחרו קבצים", 400
    writer = PdfWriter()
    for f in files:
        if f.filename.lower().endswith('.pdf'):
            try:
                reader = PdfReader(f)
                for page in reader.pages: writer.add_page(page)
            except Exception as e: return f"שגיאה בעיבוד {f.filename}: {str(e)}", 500
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return send_file(out, mimetype='application/pdf', as_attachment=True, download_name='merged_output.pdf')

@app.route('/action/pdf-to-img', methods=['POST'])
def action_pdf_to_img():
    f = request.files.get('file')
    if not f or f.filename == '': return "לא נבחר קובץ", 400
    try:
        pdf_bytes = f.read()
        images = convert_from_bytes(pdf_bytes)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, img in enumerate(images):
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=85)
                img_buffer.seek(0)
                zip_file.writestr(f'page_{i+1}.jpg', img_buffer.read())
        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='pdf_extracted_images.zip')
    except Exception as e: return f"שגיאה בהמרה: {str(e)}", 500

@app.route('/action/pdf-compress', methods=['POST'])
def action_pdf_compress():
    f = request.files.get('file')
    if not f or f.filename == '': return "לא נבחר קובץ", 400
    try:
        reader = PdfReader(f)
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return send_file(out, mimetype='application/pdf', as_attachment=True, download_name='compressed_output.pdf')
    except Exception as e: return f"שגיאה בדחיסה: {str(e)}", 500

@app.route('/action/img-convert', methods=['POST'])
def action_img_convert():
    f = request.files.get('file')
    target_format = request.form.get('format', 'JPEG').upper()
    if not f or f.filename == '': return "לא נבחרה תמונה", 400
    try:
        img = Image.open(f)
        if img.mode in ('RGBA', 'P') and target_format == 'JPEG': img = img.convert('RGB')
        out = io.BytesIO()
        img.save(out, format=target_format, quality=90)
        out.seek(0)
        ext = target_format.lower()
        if ext == 'jpeg': ext = 'jpg'
        return send_file(out, mimetype=f'image/{ext}', as_attachment=True, download_name=f'converted_image.{ext}')
    except Exception as e: return f"שגיאה בהמרה: {str(e)}", 500

@app.route('/action/img-resize', methods=['POST'])
def action_img_resize():
    f = request.files.get('file')
    try:
        width, height = int(request.form.get('width', 800)), int(request.form.get('height', 600))
    except ValueError: return "מימדים לא תקינים", 400
    if not f or f.filename == '': return "לא נבחרה תמונה", 400
    try:
        img = Image.open(f)
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        orig_format = img.format if img.format else 'JPEG'
        resized_img.save(out, format=orig_format)
        out.seek(0)
        ext = orig_format.lower()
        return send_file(out, mimetype=f'image/{ext}', as_attachment=True, download_name=f'resized_image.{ext}')
    except Exception as e: return f"שגיאה בשינוי גודל: {str(e)}", 500

# =========================================================================
# פילטרים ואפקטים - לוגיקה מעודכנת הכוללת תצוגה מקדימה והמרה ל-JPEG
# =========================================================================
@app.route('/action/img-effects-preview', methods=['POST'])
def action_img_effects_preview():
    f = request.files.get('file')
    effect = request.form.get('effect', 'grayscale')
    if not f or f.filename == '':
        return "לא נבחר קובץ לעיבוד", 400
    try:
        img = Image.open(f)
        
        # החלת האפקט
        if effect == 'grayscale':
            processed = img.convert('L')
        elif effect == 'blur':
            processed = img.filter(ImageFilter.GaussianBlur(radius=4))
        elif effect == 'contour':
            processed = img.filter(ImageFilter.CONTOUR)
        elif effect == 'brighten':
            enhancer = ImageEnhance.Brightness(img)
            processed = enhancer.enhance(1.4)
        elif effect == 'sharpen':
            processed = img.filter(ImageFilter.SHARPEN)
        else:
            processed = img

        # המרה סופית ל-JPEG עבור תצוגה והורדה
        # מטפל בשקיפות (RGBA) כדי למנוע רקע שחור ב-JPEG
        final_img = processed
        if final_img.mode in ('RGBA', 'LA', 'P'):
            # יצירת רקע לבן ומיזוג התמונה עליו
            background = Image.new('RGB', final_img.size, (255, 255, 255))
            if final_img.mode == 'RGBA':
                background.paste(final_img, mask=final_img.split()[3]) # שימוש ב-alpha channel כמסיכה
            else:
                background.paste(final_img.convert('RGBA'), mask=final_img.convert('RGBA').split()[3])
            final_img = background
        elif final_img.mode != 'RGB':
            # המרת מצבים אחרים (כמו 'L' - שחור לבן) ל-'RGB'
            final_img = final_img.convert('RGB')
            
        out = io.BytesIO()
        final_img.save(out, format='JPEG', quality=85, optimize=True)
        out.seek(0)
        
        # החזרת התמונה ישירות כ-response עבור התצוגה המקדימה
        return send_file(out, mimetype='image/jpeg')
        
    except Exception as e:
        print(f"Error in img_effects_preview: {e}")
        return f"שגיאה בעיבוד האפקט: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
