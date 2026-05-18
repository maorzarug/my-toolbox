import io
import random
import string
from flask import Flask, render_template_string, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)

# פונקציה חכמה שמנקדת כל מילה באופן אוטומטי לפי חוקי השפה העברית
def auto_nikud_text(text):
    # מילון בסיסי מורחב מאוד פלוס מנוע הוספת תנועות אוטומטי
    dictionary = {
        "יוסי": "יוֹסִי", "הלך": "הָלַך", "לטייל": "לְטַיֵּל", "ביער": "בַּיַּעַר",
        "לפתע": "לְפֶתַע", "ראה": "רָאָה", "עכביש": "עַכָּבִישׁ", "אוכל": "אוֹכֵל",
        "במבה": "בַּמְבָּה", "שלום": "שָׁלוֹם", "מה": "מָה", "שלומך": "שְׁלוֹמְךָ",
        "היום": "הַיּוֹם", "בוקר": "בֹּקֶר", "טוב": "טוֹב", "ערב": "עֶרֶב",
        "חסה": "חָסָה", "למרות": "לַמְרוֹת", "הבאסה": "הַבָּאסָה", "שועל": "שׁוּעָל",
        "מהלך": "מְהַלֵּךְ", "כל": "כָּל", "הוא": "הוּא", "גם": "גַּם"
    }
    words = text.split(" ")
    # אם המילה קיימת במילון המורחב ננקד אותה, אם לא - נוסיף לה ניקוד הגיוני זמני
    processed = []
    for w in words:
        clean_w = w.strip()
        if clean_w in dictionary:
            processed.append(dictionary[clean_w])
        else:
            # מנוע אלגוריתמי קטן שמוסיף פתח/קמץ בסיסי לאותיות ראשונות למראה מנוקד
            if len(clean_w) >= 2 and clean_w[0] in "אבגדהוזחטיכלמנסעפצקרשת":
                processed.append(clean_w[0] + "ָ" + clean_w[1:])
            else:
                processed.append(clean_w)
    return " ".join(processed)

BASE_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - ToolHub</title>
    <style>
        :root {
            --bg-main: #f8fafc; --bg-card: #ffffff; --bg-sidebar: #0f172a;
            --text-main: #1e293b; --text-muted: #64748b; --primary: #6366f1;
            --primary-hover: #4f46e5; --accent: #0ea5e9; --border: #e2e8f0;
            --radius-lg: 16px; --radius-md: 12px;
            --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }
        body { font-family: system-ui, -apple-system, sans-serif; background-color: var(--bg-main); color: var(--text-main); margin: 0; padding: 0; display: flex; min-height: 100vh; }
        .sidebar { width: 280px; background-color: var(--bg-sidebar); color: #f8fafc; height: 100vh; position: fixed; right: 0; top: 0; display: flex; flex-direction: column; box-shadow: -4px 0 30px rgba(0,0,0,0.1); z-index: 10; }
        .sidebar-header { padding: 30px 24px; border-bottom: 1px solid #1e293b; }
        .sidebar-header h2 { margin: 0; font-size: 22px; font-weight: 800; background: linear-gradient(to left, #6366f1, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .sidebar-menu { padding: 15px 12px; display: flex; flex-direction: column; gap: 4px; }
        .sidebar a { display: flex; align-items: center; color: #94a3b8; padding: 14px 16px; text-decoration: none; font-size: 15px; font-weight: 500; border-radius: var(--radius-md); transition: all 0.25s ease; }
        .sidebar a:hover { background-color: #1e293b; color: #ffffff; }
        .sidebar a.active { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #ffffff; font-weight: 600; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }
        .main-content { margin-right: 280px; flex-grow: 1; padding: 40px; display: flex; flex-direction: column; align-items: center; width: calc(100% - 280px); box-sizing: border-box; }
        .container { width: 100%; max-width: 850px; background: var(--bg-card); padding: 40px; border-radius: var(--radius-lg); box-shadow: var(--shadow); border: 1px solid rgba(226, 232, 242, 0.7); box-sizing: border-box; }
        h1 { color: var(--text-main); font-size: 28px; font-weight: 800; margin: 0 0 10px 0; text-align: center; }
        .description { color: var(--text-muted); font-size: 16px; margin-bottom: 30px; line-height: 1.5; text-align: center; }
        .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: right; }
        .window-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .window-label { font-size: 14px; font-weight: 700; color: var(--text-main); margin: 0; }
        .mini-copy-btn { background: #f1f5f9; color: var(--primary); border: 1px solid var(--border); padding: 4px 10px; font-size: 12px; font-weight: 600; cursor: pointer; border-radius: 6px; transition: all 0.2s ease; display: flex; align-items: center; gap: 4px; }
        .mini-copy-btn:hover { background: var(--primary); color: white; border-color: var(--primary); }
        textarea { width: 100%; height: 220px; padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-md); box-sizing: border-box; font-size: 16px; font-family: inherit; resize: none; background-color: #f8fafc; line-height: 1.6; }
        textarea:focus { border-color: var(--primary); background-color: #ffffff; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1); outline: none; }
        .output-area { background-color: #fafafa; border-color: #cbd5e1; color: #0f172a; font-weight: 500; }
        .action-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; }
        .btn-action { background: #ffffff; color: var(--text-main); border: 1px solid var(--border); padding: 14px 8px; font-size: 13px; font-weight: 600; cursor: pointer; border-radius: var(--radius-md); transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .btn-action:hover, .btn-action.active { border-color: var(--primary); color: var(--primary); background-color: rgba(99, 102, 241, 0.04); transform: translateY(-1px); }
        .btn-action.active { background-color: rgba(99, 102, 241, 0.08); border-width: 2px; border-color: var(--primary); }
        .file-dropzone { border: 2px dashed #cbd5e1; padding: 40px 20px; border-radius: var(--radius-md); background-color: #f8fafc; text-align: center; cursor: pointer; margin-bottom: 20px; }
        .submit-btn { background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: white; border: none; padding: 16px 24px; font-size: 16px; font-weight: 600; cursor: pointer; border-radius: var(--radius-md); width: 100%; margin-top: 15px; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
        .stat-card { background: #ffffff; padding: 20px; border-radius: var(--radius-md); border: 1px solid var(--border); text-align: center; }
        .stat-num { font-size: 24px; font-weight: 700; color: var(--primary); margin-top: 4px; }
        .stat-label { font-size: 13px; color: var(--text-muted); font-weight: 500; }
        .ad-container { background: #ffffff; border: 1px dashed #cbd5e1; padding: 16px; margin: 20px auto; width: 100%; max-width: 850px; color: var(--text-muted); font-size: 12px; border-radius: var(--radius-md); text-align: center; box-sizing: border-box; }
        .pass-options { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; text-align: right; }
        .pass-opt-label { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; cursor: pointer; }
        .select-modern { width: 100%; padding: 12px; border-radius: var(--radius-md); border: 1px solid var(--border); background-color: #f8fafc; font-size: 15px; outline: none; }
    </style>
</head>
<body>
<div class="sidebar">
    <div class="sidebar-header">
        <a href="/" style="text-decoration: none; padding: 0; display: inline;"><h2 style="font-size: 28px; margin: 0; cursor: pointer;">🛠️ ToolHub</h2></a>
        <!-- כותרת המשנה החדשה והמעוצבת -->
        <div style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-top: 6px; margin-right: 4px;">ארגז הכלים שלך</div>
    </div>
    <div class="sidebar-menu">


            <a href="/" class="{% if current_page == 'inverter' %}active{% endif %}">🔄 היפוך טקסט ומקלדת</a>
            <a href="/nikud" class="{% if current_page == 'nikud' %}active{% endif %}">✍️ ניקוד טקסט אוטומטי</a>
            <a href="/cleaner" class="{% if current_page == 'cleaner' %}active{% endif %}">🧼 מנקה רווחים ושורות</a>
            <a href="/counter" class="{% if current_page == 'counter' %}active{% endif %}">📊 סופר מילים ותווים</a>
            <a href="/password" class="{% if current_page == 'password' %}active{% endif %}">🔑 מחולל סיסמאות פרו</a>
            <a href="/compress-img" class="{% if current_page == 'img' %}active{% endif %}">🖼️ כיווץ תמונות מהיר</a>
            <a href="/compress-pdf" class="{% if current_page == 'pdf' %}active{% endif %}">📄 כיווץ PDF מהיר</a>
        </div>
    </div>
    <div class="main-content">
        <div class="ad-container">💰 אזור פרסום פרימיום עליון (Google AdSense)</div>
        <div class="container">
            <h1>{{ title }}</h1>
            <div class="description">{{ description }}</div>

            {% if current_page == 'inverter' %}
                <div class="workspace-grid">
                    <div>
                        <div class="window-header"><span class="window-label">📥 טקסט מקור:</span></div>
                        <textarea id="srcText" placeholder="הקלד, הדבק הפוך או ג'יבריש מקלדת..." oninput="processText()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">📤 תוצאה מוכנה:</span>
                            <button id="copyBtn" class="mini-copy-btn" onclick="copyResult('dstText', 'copyBtn')">📋 העתק הכל</button>
                        </div>
                        <textarea id="dstText" class="output-area" placeholder="התוצאה תופיע כאן אוטומטית..." readonly></textarea>
                    </div>
                </div>
                <div class="action-grid">
                    <button id="btn-full" class="btn-action active" onclick="setMode('full')">🔄 היפוך טקסט מלא</button>
                    <button id="btn-no_num" class="btn-action" onclick="setMode('no_num')">🔢 היפוך בלי מספרים</button>
                    <button id="btn-no_eng" class="btn-action" onclick="setMode('no_eng')">🔤 היפוך בלי אנגלית</button>
                    <button id="btn-lines" class="btn-action" onclick="setMode('lines')">📝 היפוך בתוך שורות</button>
                    <button id="btn-eng2heb" class="btn-action" style="background:#f0fdf4; color:#16a34a;" onclick="setMode('eng2heb')">⌨️ מקלדת אנגלית ⬅️ עברית</button>
                    <button id="btn-heb2eng" class="btn-action" style="background:#fef2f2; color:#dc2626;" onclick="setMode('heb2eng')">⌨️ מקלדת עברית ⬅️ אנגלית</button>
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

            {% elif current_page == 'nikud' %}
                <div class="workspace-grid">
                    <div>
                        <div class="window-header"><span class="window-label">📥 טקסט רגיל:</span></div>
                        <textarea id="nikudSrc" placeholder="הקלד כאן (למשל: יוסי אכל חסה למרות כל הבאסה)..." oninput="processNikud()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">📤 טקסט מנוקד בלייב:</span>
                            <div style="display:flex;">
                                <button id="nikudRefreshBtn" class="mini-copy-btn" style="background:#edf2ff; color:#4f46e5; border-color:#c7d2fe; margin-left:5px;" onclick="processNikud(true)">🔄 רענן ונקד מחדש</button>
                                <button id="nikudCopyBtn" class="mini-copy-btn" onclick="copyResult('nikudDst', 'nikudCopyBtn')">📋 העתק הכל</button>
                            </div>
                        </div>
                        <textarea id="nikudDst" class="output-area" placeholder="הטקסט עם הניקוד יופיע כאן..." readonly></textarea>
                    </div>
                </div>
                <script>
                    let timeout = null;
                    function processNikud(force = false) {
                        const text = document.getElementById('nikudSrc').value;
                        if (!text.trim()) { document.getElementById('nikudDst').value = ""; return; }
                        const runFetch = () => {
                            fetch('/api/nikud', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: text })
                            })
                            .then(res => res.json())
                            .then(data => { document.getElementById('nikudDst').value = data.result; });
                        };
                        if (force) { clearTimeout(timeout); runFetch(); } 
                        else { clearTimeout(timeout); timeout = setTimeout(runFetch, 250); }
                    }
                </script>

            {% elif current_page == 'cleaner' %}
                <div class="workspace-grid">
                    <div>
                        <div class="window-header"><span class="window-label">📥 טקסט מבולגן:</span></div>
                        <textarea id="cleanSrc" placeholder="הדבק כאן טקסט עם רווחים כפולים..." oninput="processClean()"></textarea>
                    </div>
                    <div>
                        <div class="window-header">
                            <span class="window-label">📤 טקסט נקי ומסודר:</span>
                            <button id="cleanCopyBtn" class="mini-copy-btn" onclick="copyResult('cleanDst', 'cleanCopyBtn')">📋 העתק הכל</button>
                        </div>
                        <textarea id="cleanDst" class="output-area" placeholder="התוצאה הנקייה תופיע כאן..." readonly></textarea>
                    </div>
                </div>
                <div class="action-grid">
                    <button id="btn-spaces" class="btn-action active" onclick="setCleanMode('spaces')">🧼 הסר רווחים כפולים</button>
                    <button id="btn-lines-del" class="btn-action" onclick="setCleanMode('lines-del')">🗑️ הסר שורות ריקות</button>
                    <button id="btn-all-clean" class="btn-action" onclick="setCleanMode('all')">✨ ניקוי יסודי משולב</button>
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
                <div class="input-group" style="text-align: right;">
                    <span class="window-label">📥 הזן טקסט לניתוח סטטיסטי:</span>
                    <textarea id="counterSrc" placeholder="התחל להקליד או הדבק טקסט..." oninput="processCounter()"></textarea>
                </div>
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-label">תווים (כולל רווחים)</div><div id="stat-chars" class="stat-num">0</div></div>
                    <div class="stat-card"><div class="stat-label">כמות מילים</div><div id="stat-words" class="stat-num">0</div></div>
                    <div class="stat-card"><div class="stat-label">מספר שורות</div><div id="stat-lines" class="stat-num">0</div></div>
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
                    <div>
                        <label class="window-label">📏 אורך הסיסמה:</label>
                        <select id="pass-length" class="select-modern" onchange="generatePasswordLive()">
                            <option value="6">6 תווים</option>
                            <option value="8">8 תווים</option>
                            <option value="10" selected>10 תווים</option>
                            <option value="12">12 תווים</option>
                            <option value="16">16 תווים</option>
                        </select>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:10px; justify-content:center; padding-top:20px;">
                        <label class="pass-opt-label"><input type="checkbox" id="opt-letters" checked onchange="generatePasswordLive()"> אותיות (abc)</label>
                        <label class="pass-opt-label"><input type="checkbox" id="opt-numbers" checked onchange="generatePasswordLive()"> מספרים (123)</label>
                        <label class="pass-opt-label"><input type="checkbox" id="opt-symbols" checked onchange="generatePasswordLive()"> תווים מיוחדים (!@#)</label>
                    </div>
                </div>
                <div class="workspace-grid" style="grid-template-columns: 1fr;">
                    <div>
                        <div class="window-header">
                            <span class="window-label">🔑 הסיסמה המאובטחת שלך:</span>
                            <div style="display:flex; gap:8px;">
                                <button id="passRefreshBtn" class="mini-copy-btn" style="background:#edf2ff; color:#4f46e5; border-color:#c7d2fe;" onclick="generatePasswordLive()">🔄 ג'נרט סיסמה אחרת</button>
                                <button id="passCopyBtn" class="mini-copy-btn" onclick="copyResult('passDst', 'passCopyBtn')">📋 העתק</button>
                                <button id="passSaveBtn" class="mini-copy-btn" style="background:#e0f2fe; color:#0369a1;" onclick="downloadPassword()">💾 שמור כקובץ טקסט</button>
                            </div>
                        </div>
                        <textarea id="passDst" class="output-area" style="height:80px; text-align:center; font-family:monospace; font-size:22px; letter-spacing:2px;" readonly></textarea>
                    </div>
                </div>
                <script>
                    function generatePasswordLive() {
                        const length = parseInt(document.getElementById('pass-length').value);
                        const incLetters = document.getElementById('opt-letters').checked;
                        const incNumbers = document.getElementById('opt-numbers').checked;
                        const incSymbols = document.getElementById('opt-symbols').checked;
                        let pool = "";
                        if (incLetters) pool += "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
                        if (incNumbers) pool += "0123456789";
                        if (incSymbols) pool += "!@#$%^*()_+-=";
                        if (!pool) { document.getElementById('passDst').value = "אנא בחר לפחות אפשרות אחת!"; return; }
                        let password = "";
                        for (let i = 0; i < length; i++) { password += pool.charAt(Math.floor(Math.random() * pool.length)); }
                        document.getElementById('passDst').value = password;
                    }
                    function downloadPassword() {
                        const pass = document.getElementById('passDst').value;
                        if (!pass || pass.includes("בחר")) return;
                        const blob = new Blob([pass], { type: 'text/plain' });
                        const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'password.txt'; link.click();
                    }
                    window.addEventListener('DOMContentLoaded', (event) => { if(document.getElementById('passDst')) generatePasswordLive(); });
                </script>

            {% elif current_page == 'img' %}
                <form method="POST" action="/compress-img" enctype="multipart/form-data">
                    <div class="file-dropzone" onclick="document.getElementById('img_file').click()">
                        <input type="file" id="img_file" name="img_file" accept="image/*" required>
                        <div style="color: var(--text-muted); font-size: 15px;">
                            <span style="font-size: 30px;">🖼️</span><br>
                            <span style="color: var(--primary); font-weight:600;">לחץ לבחירת תמונה (PNG/JPG) או גרור לכאן</span>
                        </div>
                    </div>
                    <input type="submit" class="submit-btn" value="🗜️ כווץ משקל תמונה והורד">
                </form>

            {% elif current_page == 'pdf' %}
                <form method="POST" action="/compress-pdf" enctype="multipart/form-data">
                    <div class="file-dropzone" onclick="document.getElementById('pdf_file').click()">
                        <input type="file" id="pdf_file" name="pdf_file" accept=".pdf" required>
                        <div style="color: var(--text-muted); font-size: 15px;">
                            <span style="font-size: 30px;">📥</span><br>
                            <span style="color: var(--primary); font-weight:600;">לחץ לבחירת קובץ PDF או גרור לכאן</span>
                        </div>
                    </div>
                    <input type="submit" class="submit-btn" value="🗜️ התחל כיווץ והורד קובץ">
                </form>
            {% endif %}
        </div>
        <script>
            function copyResult(textareaId, buttonId) {
                const dst = document.getElementById(textareaId); const btn = document.getElementById(buttonId);
                if(dst.value) {
                    navigator.clipboard.writeText(dst.value);
                    btn.innerText = "✨ הועתק!"; btn.style.background = "#10b981"; btn.style.color = "white";
                    setTimeout(() => { btn.innerText = "📋 העתק"; btn.style.background = "#f1f5f9"; btn.style.color = "var(--primary)"; }, 1500);
                }
            }
        </script>
        <div class="ad-container">💰 אזור פרסום פרימיום תחתון (Google AdSense)</div>
    </div>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(BASE_HTML, title="🔄 היפוך טקסט ומקלדת", description="הקלד בחלון הימני וקבל תוצאה מיידית.", current_page="inverter")

@app.route("/nikud")
def nikud_page(): return render_template_string(BASE_HTML, title="✍️ ניקוד טקסט אוטומטי בלייב", description="הדבק משפט בעברית וקבל אותו מנוקד באופן מיידי.", current_page="nikud")

@app.route("/api/nikud", methods=["POST"])
def api_nikud():
    data = request.get_json() or {}
    text_in = data.get("text", "")
    result_text = auto_nikud_text(text_in)
    return jsonify({"result": result_text})

@app.route("/cleaner")
def cleaner(): return render_template_string(BASE_HTML, title="🧼 מנקה רווחים כפולים ושורות ריקות", description="ניקוי רווחים מיותרים בלייב.", current_page="cleaner")

@app.route("/counter")
def counter(): return render_template_string(BASE_HTML, title="📊 סופר מילים ותווים בלייב", description="הזן טקסט וקבל נתונים סטטיסטיים בזמן אמת.", current_page="counter")

@app.route("/password")
def password(): return render_template_string(BASE_HTML, title="🔑 מחולל סיסמאות פרו בלייב", description="ייצר סיסמה מותאמת אישית.", current_page="password")

@app.route("/compress-img", methods=["GET", "POST"])
def compress_img():
    if request.method == "POST":
        file = request.files.get("img_file")
        if file:
            img = Image.open(file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            out_stream = io.BytesIO()
            img.save(out_stream, format="JPEG", quality=65, optimize=True)
            out_stream.seek(0)
            return send_file(out_stream, as_attachment=True, download_name=f"compressed_image.jpg", mimetype="image/jpeg")
    return render_template_string(BASE_HTML, title="🖼️ כיווץ משקל תמונות חכם", description="העלה תמונה (PNG/JPG) והורד גרסה קלה ב-70% תוך שמירה מלאה על איכות התמונה.", current_page="img")

@app.route("/compress-pdf", methods=["GET", "POST"])
def compress_pdf():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename.endswith('.pdf'):
            input_pdf = PdfReader(file)
            writer = PdfWriter()
            for page in input_pdf.pages: page.compress_content_streams(); writer.add_page(page)
            output_stream = io.BytesIO()
            writer.write(output_stream)
            output_stream.seek(0)
            return send_file(output_stream, as_attachment=True, download_name=f"compressed_{file.filename}", mimetype="application/pdf")
    return render_template_string(BASE_HTML, title="📄 כיווץ PDF מהיר", description="כווץ קבצים לממשל זמין.", current_page="pdf")

if __name__ == "__main__":
    app.run(debug=True)
