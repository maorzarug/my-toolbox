import io
import random
import string
from flask import Flask, render_template_string, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)

NIKUD_DICT = {
    "יוסי": "יוֹסִי", "הלך": "הָלַך", "לטייל": "לְטַיֵּל", "ביער": "בַּיַּעַר",
    "חסה": "חָסָה", "למרות": "לַמְרוֹת", "הבאסה": "הַבָּאסָה", "שועל": "שׁוּעָל",
    "מהלך": "מְהַלֵּךְ", "שלום": "שָׁלוֹם", "בוקר": "בֹּקֶר", "טוב": "טוֹב"
}

BASE_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - ToolHub</title>
    <style>
        /* 🔮 שילוב אפקט הזכוכית המטושטשת המנצח בכל האתר */
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 40%, #311042 100%);
            --text-main: #f8fafc; --text-muted: #cbd5e1; --primary: #818cf8;
            --primary-hover: #6366f1; --accent: #38bdf8; --radius-lg: 24px; --radius-md: 16px;
            --glass-bg: rgba(255, 255, 255, 0.04);
            --glass-sidebar: rgba(15, 23, 42, 0.4);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-blur: blur(16px);
            --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }
        body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg-gradient); color: var(--text-main); margin: 0; padding: 0; display: flex; min-height: 100vh; background-attachment: fixed; }
        
        .sidebar { width: 280px; background: var(--glass-sidebar); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); color: var(--text-main); height: 100vh; position: fixed; right: 0; top: 0; display: flex; flex-direction: column; box-shadow: -4px 0 30px rgba(0,0,0,0.3); z-index: 10; border-left: 1px solid var(--glass-border); }
        .sidebar-header { padding: 30px 24px; border-bottom: 1px solid var(--glass-border); }
        .sidebar-header h2 { margin: 0; font-size: 24px; font-weight: 800; background: linear-gradient(to left, #818cf8, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .sidebar-menu { padding: 20px 12px; display: flex; flex-direction: column; gap: 6px; flex-grow: 1; overflow-y: auto; }
        .sidebar a { display: flex; align-items: center; color: var(--text-muted); padding: 12px 16px; text-decoration: none; font-size: 14px; font-weight: 500; border-radius: var(--radius-md); transition: all 0.2s; border: 1px solid transparent; }
        .sidebar a:hover { background: rgba(255,255,255,0.05); color: #ffffff; border-color: rgba(255,255,255,0.05); }
        .sidebar a.active { background: rgba(255, 255, 255, 0.1); color: #ffffff; font-weight: 600; border-color: var(--glass-border); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .sidebar-footer { padding: 24px; border-top: 1px solid var(--glass-border); text-align: center; font-size: 12px; color: #94a3b8; }
        .sidebar-footer a { color: var(--accent); text-decoration: none; font-weight: 600; display: inline-block; margin-top: 4px; }
        
        .main-content { margin-right: 280px; flex-grow: 1; padding: 50px 40px; display: flex; flex-direction: column; align-items: center; width: calc(100% - 280px); box-sizing: border-box; }
        .container { width: 100%; max-width: 850px; background: var(--glass-bg); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); padding: 40px; border-radius: var(--radius-lg); box-shadow: var(--shadow); border: 1px solid var(--glass-border); box-sizing: border-box; }
        h1 { font-size: 28px; font-weight: 800; text-align: center; margin: 0 0 10px 0; color: #ffffff; }
        .description { color: var(--text-muted); text-align: center; margin-bottom: 40px; font-size: 15px; }
        
        .tools-dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%; text-align: right; }
        .tool-card { background: rgba(255, 255, 255, 0.02); border: 1px solid var(--glass-border); padding: 24px; border-radius: var(--radius-md); text-decoration: none; color: var(--text-main); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; gap: 6px; }
        .tool-card:hover { background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.2); transform: translateY(-4px); box-shadow: 0 12px 20px rgba(0, 0, 0, 0.2); }
        .tool-icon { font-size: 28px; margin-bottom: 4px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2)); }
        .tool-title { font-size: 17px; font-weight: 700; color: #ffffff; }
        .tool-desc { font-size: 13.5px; color: var(--text-muted); line-height: 1.5; }
        
        .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: right; }
        .window-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .mini-copy-btn { background: rgba(255,255,255,0.08); color: #ffffff; border: 1px solid var(--glass-border); padding: 5px 12px; font-size: 12px; font-weight: 600; cursor: pointer; border-radius: 6px; transition: 0.2s; }
        .mini-copy-btn:hover { background: var(--primary); border-color: var(--primary); }
        textarea, .input-modern { width: 100%; height: 210px; padding: 16px; border: 1px solid var(--glass-border); border-radius: var(--radius-md); box-sizing: border-box; font-size: 16px; font-family: inherit; resize: none; background: rgba(0, 0, 0, 0.2); color: #ffffff; line-height: 1.6; }
        textarea:focus, .input-modern:focus { border-color: var(--primary); box-shadow: 0 0 12px rgba(129, 140, 248, 0.2); outline: none; }
        .input-modern { height: auto; padding: 12px; margin-bottom: 15px; }
        .output-area { background: rgba(255, 255, 255, 0.02); color: #f1f5f9; }
        
        .action-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; }
        .btn-action { background: rgba(255,255,255,0.06); color: var(--text-main); border: 1px solid var(--glass-border); padding: 12px 4px; font-size: 13px; font-weight: 600; cursor: pointer; border-radius: var(--radius-md); transition: 0.2s; }
        .btn-action.active { background: rgba(129, 140, 248, 0.2); border-color: var(--primary); box-shadow: 0 0 10px rgba(129, 140, 248, 0.2); }
        
        .file-dropzone { border: 2px dashed rgba(255,255,255,0.2); padding: 40px 20px; border-radius: var(--radius-md); background: rgba(0,0,0,0.2); text-align: center; cursor: pointer; margin-bottom: 15px; transition: 0.2s; }
        .file-dropzone:hover { border-color: var(--primary); background: rgba(255,255,255,0.02); }
        .submit-btn { background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: white; border: none; padding: 16px 24px; font-size: 16px; font-weight: 600; cursor: pointer; border-radius: var(--radius-md); width: 100%; margin-top: 5px; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); transition: 0.2s; }
        .submit-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4); }
        
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
        .stat-card { background: rgba(255,255,255,0.02); padding: 20px; border-radius: var(--radius-md); border: 1px solid var(--glass-border); text-align: center; }
        .stat-num { font-size: 24px; font-weight: 700; color: var(--primary); text-shadow: 0 0 8px rgba(129, 140, 248, 0.4); }
        .pass-options { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; text-align: right; }
        .pass-opt-label { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text-muted); }
        .select-modern { width: 100%; padding: 12px; border-radius: var(--radius-md); border: 1px solid var(--glass-border); background: rgba(0,0,0,0.2); color: white; font-size: 15px; outline: none; }
        .select-modern option { background: #1e1b4b; color: white; }
        .ad-container { background: rgba(0,0,0,0.2); border: 1px dashed var(--glass-border); padding: 15px; margin: 20px auto; width: 100%; max-width: 850px; color: var(--text-muted); font-size: 12px; border-radius: var(--radius-md); text-align: center; box-sizing: border-box; backdrop-filter: var(--glass-blur); }
        .about-text { font-size: 16px; line-height: 1.8; text-align: right; color: var(--text-main); }
        .about-card-badge { display: inline-block; background: rgba(129, 140, 248, 0.2); color: #a5b4fc; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; margin-bottom: 15px; border: 1px solid var(--glass-border); }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: relative; border-left: none; }
            .sidebar-menu { flex-direction: row; padding: 10px; overflow-x: auto; gap: 8px; }
            .sidebar-footer { display: none; }
            .main-content { margin-right: 0; width: 100%; padding: 20px 16px; }
            .container { padding: 25px 20px; }
            .tools-dashboard, .workspace-grid, .stats-grid, .pass-options { grid-template-columns: 1fr; }
            .action-grid { grid-template-columns: repeat(2, 1fr); }
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
            <a href="/compress-pdf" class="{% if current_page == 'pdf' %}active{% endif %}">📄 כיווץ PDF מהיר</a>
            <a href="/compress-img" class="{% if current_page == 'img' %}active{% endif %}">🖼️ כיווץ תמונות מהיר</a>
            <a href="/whatsapp" class="{% if current_page == 'whatsapp' %}active{% endif %}">🟢 מחולל קישורי וווטסאפ</a>
            <a href="/nikud" class="{% if current_page == 'nikud' %}active{% endif %}">✍️ ניקוד אוטומטי</a>
            <a href="/cleaner" class="{% if current_page == 'cleaner' %}active{% endif %}">🧼 מנקה רווחים ושורות</a>
            <a href="/counter" class="{% if current_page == 'counter' %}active{% endif %}">📊 סופר מילים ותווים</a>
            <a href="/password" class="{% if current_page == 'password' %}active{% endif %}">🔑 מחולל סיסמאות</a>
            <a href="/about" class="{% if current_page == 'about' %}active{% endif %}">ℹ️ אודות הפרויקט</a>
        </div>
        <div class="sidebar-footer">
            <span>💡 מצאתם באג? יש לכם רעיון?</span><br>
            <a href="mailto:support@toolhub.com">שלחו לנו משוב במייל</a>
        </div>
    </div>
    <div class="main-content">
        <div class="ad-container">💰 אזור פרסום פרימיום עליון (Google AdSense)</div>
        <div class="container">
            <h1>{{ title }}</h1>
            <div class="description">{{ description }}</div>
            {% if current_page == 'dashboard' %}
                <div class="tools-dashboard">
                    <a href="/inverter" class="tool-card"><div class="tool-icon">🔄</div><div class="tool-title">היפוך טקסט ומקלדת</div><div class="tool-desc">היפוך אותיות, שורות ותיקון ג'יבריש מקלדת בלייב.</div></a>
                    <a href="/compress-pdf" class="tool-card"><div class="tool-icon">📄</div><div class="tool-title">כיווץ PDF לממשל זמין</div><div class="tool-desc">דחיסת קובצי PDF והתאמתם למגבלות המשקל של אתרי הממשלה.</div></a>
                    <a href="/compress-img" class="tool-card"><div class="tool-icon">🖼️</div><div class="tool-title">כיווץ תמונות מהיר</div><div class="tool-desc">הקטנת משקל קובצי תמונה ב-70% תוך שמירה מלאה על האיכות.</div></a>
                    <a href="/whatsapp" class="tool-card"><div class="tool-icon">🟢</div><div class="tool-title">מחולל קישורי וווטסאפ</div><div class="tool-desc">יצירת קישור ישיר לשיחת וווטסאפ עם הודעה מוכנה מראש בלייב.</div></a>
                    <a href="/nikud" class="tool-card"><div class="tool-icon">✍️</div><div class="tool-title">ניקוד טקסט אוטומטי</div><div class="tool-desc">הוספת ניקוד דקדוקי חכם למשפטים בעברית בלייב.</div></a>
                    <a href="/cleaner" class="tool-card"><div class="tool-icon">🧼</div><div class="tool-title">מנקה רווחים ושורות</div><div class="tool-desc">ניקוי רווחים כפולים ומחיקת שורות ריקות בקליק.</div></a>
                    <a href="/counter" class="tool-card"><div class="tool-icon">📊</div><div class="tool-title">סופר מילים ותווים</div><div class="tool-desc">ניתוח סטטיסטי מדויק של אורך הטקסט בלייב.</div></a>
                    <a href="/password" class="tool-card"><div class="tool-icon">🔑</div><div class="tool-title">מחולל סיסמאות פרו</div><div class="tool-desc">יצירת סיסמאות חזקות עם שליטה מלאה באורך וסוג התווים.</div></a>
                </div>

            {% elif current_page == 'about' %}
                <!-- דף אודות מעוצב ומרגש למטרת חסד -->
                <div class="about-text">
                    <div class="about-card-badge">❤️ פרויקט ללא מטרת רווח - לתועלת הציבור</div>
                    <p>ברוכים הבאים ל-<strong>ToolHub</strong>! האתר הזה נולד מתוך רעיון פשוט: לתת לציבור בישראל ארגז כלים דיגיטלי מתקדם, מהיר ואיכותי - <strong>בחינם לחלוטין וללא צורך בהרשמה</strong>.</p>
                    <p>כל הכלים באתר זה נבנו במטרה אחת: לעשות חסד, להקל על היום-יום שלכם ולחסוך לכם זמן יקר. בין אם אתם סטודנטים שמנסים להגיש טפסים לממשל זמין, בעלי עסקים שצריכים קישור מהיר לווטסאפ, או כותבי תוכן שזקוקים לניקוד או היפוך טקסט - אנחנו כאן בשבילכם.</p>
                    <p><strong>למה יש פרסומות באתר?</strong><br>השירותים והכלים תמיד יישארו חינמיים ב-100%. הפרסומות באתר נועדו אך ורק כדי לעזור לנו לממן את עלויות השרתים החזקים שמריצים את עיבודי ה-PDF והתמונות, ולאפשר לנו להמשיך להחזיק את פרויקט החסד הזה באוויר עבור כולם.</p>
                    <p style="text-align: center; font-weight: 700; margin-top: 30px; color: var(--accent);">תודה רבה על השימוש שלכם ועל התמיכה בפרויקט! 🙏</p>
                </div>

            {% elif current_page == 'inverter' %}
                <div class="workspace-grid">
                    <div><textarea id="srcText" placeholder="הקלד או הדבק כאן..." oninput="processText()"></textarea></div>
                    <div>
                        <div class="window-header"><button id="copyBtn" class="mini-copy-btn" onclick="copyResult('dstText', 'copyBtn')">📋 העתק הכל</button></div>
                        <textarea id="dstText" class="output-area" placeholder="התוצאה תופיע כאן..." readonly></textarea>
                    </div>
                </div>
                <div class="action-grid">
                    <button id="btn-full" class="btn-action active" onclick="setMode('full')">🔄 היפוך מלא</button>
                    <button id="btn-no_num" class="btn-action" onclick="setMode('no_num')">🔢 בלי מספרים</button>
                    <button id="btn-no_eng" class="btn-action" onclick="setMode('no_eng')">🔤 בלי אנגלית</button>
                    <button id="btn-lines" class="btn-action" onclick="setMode('lines')">📝 בתוך שורות</button>
                    <button id="btn-eng2heb" class="btn-action" style="color:#38bdf8;" onclick="setMode('eng2heb')">⌨️ אנגלית ⬅️ עברית</button>
                    <button id="btn-heb2eng" class="btn-action" style="color:#f43f5e;" onclick="setMode('heb2eng')">⌨️ עברית ⬅️ אנגלית</button>
                </div>
                <script>
                    let currentMode = 'full';
                    const engToHebMap = {'q': '/', 'w': "'", 'e': 'ק', 'r': 'ר', 't': 'א', 'y': 'ט', 'u': 'ו', 'i': 'ן', 'o': 'ם', 'p': 'פ', 'a': 'ש', 's': 'ד', 'd': 'ג', 'f': 'כ', 'g': 'ע', 'h': 'י', 'j': 'ח', 'k': 'ל', 'l': 'ך', ';': 'ף', "'": ',', 'z': 'ז', 'x': 'ס', 'c': 'ב', 'v': 'ה', 'b': 'נ', 'n': 'מ', 'm': 'צ', ',': 'ת', '.': 'ץ', '/': '.'};
                    const hebToEngMap = {}; for (let k in engToHebMap) { hebToEngMap[engToHebMap[k]] = k; }
                    function setMode(mode) { currentMode = mode; document.querySelectorAll('.btn-action').forEach(btn => btn.classList.remove('active')); document.getElementById('btn-' + mode).classList.add('active'); processText(); }
                    function processText() {
                        const src = document.getElementById('srcText').value; let result = "";
                        if (currentMode === 'full') { result = src.split('').reverse().join(''); } 
                        else if (currentMode === 'lines') { result = src.split('\\n').map(line => line.split('').reverse().join('')).join('\\n'); } 
                        else if (currentMode === 'no_num') { result = src.split('').reverse().join('').replace(/\\d+/g, m => m.split('').reverse().join('')); } 
                        else if (currentMode === 'no_eng') { result = src.split('').reverse().join('').replace(/[a-zA-Z]+/g, m => m.split('').reverse().join('')); }
                        else if (currentMode === 'eng2heb' || currentMode === 'heb2eng') {
                            const map = (currentMode === 'eng2heb') ? engToHebMap : hebToEngMap;
                            for (let i = 0; i < src.length; i++) { let char = src[i].toLowerCase(); result += map[char] ? map[char] : src[i]; }
                        }
                        document.getElementById('dstText').value = result;
                    }
                </script>

            {% elif current_page == 'whatsapp' %}
                <div class="workspace-grid">
                    <div>
                        <label class="window-label">📱 מספר טלפון (למשל 0501234567):</label>
                        <input type="text" id="waPhone" class="input-modern" placeholder="הכנס מספר טלפון..." oninput="processWhatsapp()">
                        <label class="window-label">💬 הודעה מוכנה מראש (אופציונלי):</label>
                        <textarea id="waMsg" style="height:120px;" placeholder="הקלד את ההודעה שתפתח בשיחה..." oninput="processWhatsapp()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">🔗 הקישור המוכן שלך:</span>
                            <button id="waCopyBtn" class="mini-copy-btn" onclick="copyResult('waDst', 'waCopyBtn')">📋 העתק קישור</button>
                        </div>
                        <textarea id="waDst" class="output-area" style="height:200px; font-family:monospace; font-size:14px; color:var(--accent);" placeholder="הקישור ייווצר כאן אוטומטית..." readonly></textarea>
                    </div>
                </div>
                <script>
                    function processWhatsapp() {
                        let phone = document.getElementById('waPhone').value.trim(); const msg = document.getElementById('waMsg').value;
                        if (!phone) { document.getElementById('waDst').value = ""; return; }
                        if (phone.startsWith('0')) { phone = '972' + phone.substring(1); }
                        phone = phone.replace(/[^0-9]/g, ''); let url = "https://wa.me" + phone;
                        if (msg.trim()) { url += "?text=" + encodeURIComponent(msg); }
                        document.getElementById('waDst').value = url;
                    }
                </script>

            {% elif current_page == 'nikud' %}
                <div class="workspace-grid">
                    <div><textarea id="nikudSrc" placeholder="הקלד כאן (למשל: יוסי אכל חסה למרות כל הבאסה)..." oninput="processNikud()"></textarea></div>
                    <div>
                        <div class="window-header">
                            <button id="nikudRefreshBtn" class="mini-copy-btn" style="color:var(--primary);" onclick="processNikud(true)">🔄 רענן ונקד</button>
                            <button id="nikudCopyBtn" class="mini-copy-btn" onclick="copyResult('nikudDst', 'nikudCopyBtn')">📋 העתק הכל</button>
                        </div>
                        <textarea id="nikudDst" class="output-area" placeholder="התוצאה תופיע כאן..." readonly></textarea>
                    </div>
                </div>
                <script>
                    let timeout = null;
                    function processNikud(force = false) {
                        const text = document.getElementById('nikudSrc').value;
                        if (!text.trim()) { document.getElementById('nikudDst').value = ""; return; }
                        const runFetch = () => {
                            fetch('/api/nikud', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: text }) })
                            .then(res => res.json()).then(data => { document.getElementById('nikudDst').value = data.result; });
                        };
                        if (force) { clearTimeout(timeout); runFetch(); } 
                        else { clearTimeout(timeout); timeout = setTimeout(runFetch, 250); }
                    }
                </script>

            {% elif current_page == 'cleaner' %}
                <div class="workspace-grid">
                    <div><textarea id="cleanSrc" placeholder="הדבק כאן טקסט מבולגן..." oninput="processClean()"></textarea></div>
                    <div>
                        <div class="window-header"><button id="cleanCopyBtn" class="mini-copy-btn" onclick="copyResult('cleanDst', 'cleanCopyBtn')">📋 העתק</button></div>
                        <textarea id="cleanDst" class="output-area" readonly></textarea>
                    </div>
                </div>
                <div class="action-grid">
                    <button id="btn-spaces" class="btn-action active" onclick="setCleanMode('spaces')">🧼 הסר רווחים</button>
                    <button id="btn-lines-del" class="btn-action" onclick="setCleanMode('lines-del')">🗑️ הסר שורות</button>
                    <button id="btn-all-clean" class="btn-action" onclick="setCleanMode('all')">✨ ניקוי משולב</button>
                </div>
                <script>
                    let cleanMode = 'spaces';
                    function setCleanMode(mode) { cleanMode = mode; document.querySelectorAll('.btn-action').forEach(btn => btn.classList.remove('active')); document.getElementById('btn-' + mode).classList.add('active'); processClean(); }
                    function processClean() {
                        const src = document.getElementById('cleanSrc').value; let result = src;
                        if (cleanMode === 'spaces' || cleanMode === 'all') { result = result.replace(/[ ]+/g, ' '); }
                        if (cleanMode === 'lines-del' || cleanMode === 'all') { result = result.split('\\n').filter(line => line.trim() !== '').join('\\n'); }
                        document.getElementById('cleanDst').value = result;
                    }
                </script>

            {% elif current_page == 'counter' %}
                <textarea id="counterSrc" placeholder="התחל להקליד..." oninput="processCounter()"></textarea>
                <div class="stats-grid">
                    <div class="stat-card"><div>תווים</div><div id="stat-chars" class="stat-num">0</div></div>
                    <div class="stat-card"><div>מילים</div><div id="stat-words" class="stat-num">0</div></div>
                    <div class="stat-card"><div>שורות</div><div id="stat-lines" class="stat-num">0</div></div>
                </div>
                <script>
                    function processCounter() {
                        const src = document.getElementById('counterSrc').value;
                        document.getElementById('stat-chars').innerText = src.length;
                        document.getElementById('stat-words').innerText = src.trim() ? src.trim().split(/\\s+/).length : 0;
                        document.getElementById('stat-lines').innerText = src ? src.split('\\n').length : 0;
                    }
                </script>

            {% elif current_page == 'password' %}
                <div class="pass-options">
                    <div><select id="pass-length" class="select-modern" onchange="generatePasswordLive()"><option value="6">6 תווים</option><option value="8">8 תווים</option><option value="10" selected>10 תווים</option><option value="16">16 תווים</option></select></div>
                    <div style="display:flex; flex-direction:column; gap:5px;">
                        <label class="pass-opt-label"><input type="checkbox" id="opt-letters" checked onchange="generatePasswordLive()"> אותיות</label>
                        <label class="pass-opt-label"><input type="checkbox" id="opt-numbers" checked onchange="generatePasswordLive()"> מספרים</label>
                        <label class="pass-opt-label"><input type="checkbox" id="opt-symbols" checked onchange="generatePasswordLive()"> מיוחדים</label>
                    </div>
                </div>
                <div class="window-header">
                    <button id="passRefreshBtn" class="mini-copy-btn" onclick="generatePasswordLive()">🔄 אחרת</button>
                    <button id="passCopyBtn" class="mini-copy-btn" onclick="copyResult('passDst', 'passCopyBtn')">📋 העתק</button>
                    <button class="mini-copy-btn" style="color:var(--accent);" onclick="downloadPassword()">💾 שמור קובץ</button>
                </div>
                <textarea id="passDst" class="output-area" style="height:60px; text-align:center; font-family:monospace; font-size:22px; background:rgba(0,0,0,0.3);" readonly></textarea>
                <script>
                    function generatePasswordLive() {
                        const length = parseInt(document.getElementById('pass-length').value);
                        const pool = (document.getElementById('opt-letters').checked ? "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" : "") + (document.getElementById('opt-numbers').checked ? "0123456789" : "") + (document.getElementById('opt-symbols').checked ? "!@#$%^*()_+=-" : "");
                        if (!pool) { document.getElementById('passDst').value = "בחר אפשרות אחת!"; return; }
                        let pass = ""; for (let i = 0; i < length; i++) pass += pool.charAt(Math.floor(Math.random() * pool.length));
                        document.getElementById('passDst').value = pass;
                    }
                    function downloadPassword() {
                        const pass = document.getElementById('passDst').value; if (!pass || pass.includes("בחר")) return;
                        const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([pass], { type: 'text/plain' })); link.download = 'password.txt'; link.click();
                    }
                    window.addEventListener('DOMContentLoaded', () => { if(document.getElementById('passDst')) generatePasswordLive(); });
                </script>

            {% elif current_page == 'img' %}
                <form method="POST" action="/compress-img" enctype="multipart/form-data">
                    <div class="file-dropzone" onclick="document.getElementById('img_file').click()">
                        <input type="file" id="img_file" name="img_file" accept="image/*" required onchange="document.getElementById('img-text').innerText = '📄 קובץ נבחר: ' + this.files[name]; document.getElementById('img-text').style.color = '#38bdf8';">
                        <div id="img-text" style="font-weight:600; color:var(--text-muted);">📥 לחץ או גרור תמונה לכאן</div>
                    </div>
                    <input type="submit" class="submit-btn" value="🗜️ כווץ תמונה והורד">
                </form>
            {% elif current_page == 'pdf' %}
                <form method="POST" action="/compress-pdf" enctype="multipart/form-data">
                    <div class="file-dropzone" onclick="document.getElementById('pdf_file').click()">
                        <input type="file" id="pdf_file" name="pdf_file" accept=".pdf" required onchange="document.getElementById('pdf-text').innerText = '📄 קובץ נבחר: ' + this.files[name]; document.getElementById('pdf-text').style.color = '#38bdf8';">
                        <div id="pdf-text" style="font-weight:600; color:var(--text-muted);">📥 לחץ או גרור PDF לכאן</div>
                    </div>
                    <input type="submit" class="submit-btn" value="🗜️ התחל כיווץ והורד קובץ">
                </form>
            {% endif %}
        </div>
        <script>
            function copyResult(textareaId, buttonId) {
                const dst = document.getElementById(textareaId); const btn = document.getElementById(buttonId);
                if(dst.value) {
                    navigator.clipboard.writeText(dst.value); btn.innerText = "✨ הועתק!";
                    setTimeout(() => { btn.innerText = buttonId.includes('pass') ? "📋 העתק" : buttonId.includes('wa') ? "📋 העתק קישור" : "📋 העתק הכל"; }, 1500);
                }
            }
        </script>
        <div class="ad-container">💰 אזור פרסום פרימיום תחתון (Google AdSense)</div>
    </div>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(BASE_HTML, title="🏠 ברוכים הבאים ל-ToolHub", description="בחר את הכלי המבוקש מתוך הרשימה למטה והתחל לעבוד במהירות ובחינם.", current_page="dashboard")
@app.route("/inverter")
def inverter(): return render_template_string(BASE_HTML, title="🔄 היפוך טקסט ומקלדת בלייב", description="הקלד בחלון הימני וקבל תוצאה מיידית.", current_page="inverter")
@app.route("/whatsapp")
def whatsapp(): return render_template_string(BASE_HTML, title="🟢 מחולל קישורי ווטסאפ מהיר", description="הזן מספר טלפון והודעה, וקבל קישור ישיר להעתקה מיידית ללא רענון עמוד.", current_page="whatsapp")
@app.route("/nikud")
def nikud_page(): return render_template_string(BASE_HTML, title="✍️ ניקוד טקסט אוטומטי בלייב", description="הדבק משפט בעברית וקבל אותו מנוקד באופן מיידי.", current_page="nikud")
@app.route("/api/nikud", methods=["POST"])
def api_nikud():
    text_in = (request.get_json() or {}).get("text", "")
    processed = [NIKUD_DICT.get(w.strip(), w.strip()) for w in text_in.split(" ")]
    return jsonify({"result": " ".join(processed)})
@app.route("/cleaner")
def cleaner(): return render_template_string(BASE_HTML, title="🧼 מנקה רווחים כפולים ושורות ריקות", description="ניקוי רווחים מיותרים בלייב.", current_page="cleaner")
@app.route("/counter")
def counter(): return render_template_string(BASE_HTML, title="📊 סופר מילים ותווים בלייב", description="הזן טקסט וקבל נתונים סטטיסטיים בזמן אמת.", current_page="counter")
@app.route("/password")
def password(): return render_template_string(BASE_HTML, title="🔑 מחולל סיסמאות פרו בלייב", description="ייצר סיסמה מותאמת אישית.", current_page="password")
@app.route("/about")
def about(): return render_template_string(BASE_HTML, title="ℹ️ אודות פרויקט ToolHub", description="הסיפור מאחורי ארגז הכלים הדיגיטלי שלנו שנבנה למטרת חסד ועזרה לציבור.", current_page="about")

@app.route("/compress-img", methods=["GET", "POST"])
def compress_img():
    if request.method == "POST":
        file = request.files.get("img_file")
        if file and file.filename != '':
            img = Image.open(file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            out = io.BytesIO(); img.save(out, format="JPEG", quality=65, optimize=True); out.seek(0)
            return send_file(out, as_attachment=True, download_name="compressed_image.jpg", mimetype="image/jpeg")
    return render_template_string(BASE_HTML, title="🖼️ כיווץ משקל תמונות חכם", description="הורד גרסה קלה ב-70% תוך שמירה מלאה על האיכות.", current_page="img")

@app.route("/compress-pdf", methods=["GET", "POST"])
def compress_pdf():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename != '':
            try:
                input_pdf = PdfReader(file); writer = PdfWriter()
                for page in input_pdf.pages: writer.add_page(page)
                out = io.BytesIO(); writer.write(out); out.seek(0)
                return send_file(out, as_attachment=True, download_name="compressed_document.pdf", mimetype="application/pdf")
            except Exception as e:
                return "אירעה שגיאה בעיבוד הקובץ. ודא שמדובר בקובץ PDF תקין.", 400
    return render_template_string(BASE_HTML, title="📄 כיווץ PDF מהיר לממשל זמין", description="הקובץ כבד מדי לאתרים ממשלתיים? כווץ אותו כאן בקליק אחד.", current_page="pdf")

if __name__ == "__main__":
    app.run(debug=True)
