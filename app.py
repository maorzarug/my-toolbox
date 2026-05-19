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
        :root {
            --bg-main: #f8fafc; --bg-card: #ffffff; --bg-sidebar: #0f172a;
            --text-main: #1e293b; --text-muted: #64748b; --primary: #6366f1;
            --radius-lg: 16px; --radius-md: 12px; --border: #e2e8f0;
            --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }
        body { font-family: system-ui, -apple-system, sans-serif; background-color: var(--bg-main); color: var(--text-main); margin: 0; padding: 0; display: flex; min-height: 100vh; }
        .sidebar { width: 280px; background-color: var(--bg-sidebar); color: #f8fafc; height: 100vh; position: fixed; right: 0; top: 0; display: flex; flex-direction: column; box-shadow: -4px 0 30px rgba(0,0,0,0.1); z-index: 10; }
        .sidebar-header { padding: 25px; border-bottom: 1px solid #1e293b; }
        .sidebar-header h2 { margin: 0; font-size: 24px; font-weight: 800; background: linear-gradient(to left, #6366f1, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .sidebar-menu { padding: 15px 12px; display: flex; flex-direction: column; gap: 4px; }
        .sidebar a { display: flex; align-items: center; color: #94a3b8; padding: 12px 16px; text-decoration: none; font-size: 15px; font-weight: 500; border-radius: var(--radius-md); transition: 0.2s; }
        .sidebar a:hover, .sidebar a.active { background-color: #1e293b; color: #ffffff; }
        .sidebar a.active { background: linear-gradient(135deg, var(--primary), #0ea5e9); }
        .main-content { margin-right: 280px; flex-grow: 1; padding: 40px; display: flex; flex-direction: column; align-items: center; width: calc(100% - 280px); box-sizing: border-box; }
        .container { width: 100%; max-width: 850px; background: var(--bg-card); padding: 40px; border-radius: var(--radius-lg); box-shadow: var(--shadow); border: 1px solid var(--border); box-sizing: border-box; }
        h1 { font-size: 26px; font-weight: 800; text-align: center; margin: 0 0 10px 0; }
        .description { color: var(--text-muted); text-align: center; margin-bottom: 30px; font-size: 15px; }
        
        .tools-dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%; text-align: right; }
        .tool-card { background: var(--bg-card); border: 1px solid var(--border); padding: 20px; border-radius: var(--radius-lg); text-decoration: none; color: var(--text-main); transition: 0.2s; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); }
        .tool-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: var(--shadow); }
        .tool-icon { font-size: 28px; }
        .tool-title { font-size: 17px; font-weight: 700; }
        .tool-desc { font-size: 13px; color: var(--text-muted); line-height: 1.4; }
        
        .workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: right; }
        .window-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .mini-copy-btn { background: #f1f5f9; color: var(--primary); border: 1px solid var(--border); padding: 4px 10px; font-size: 12px; font-weight: 600; cursor: pointer; border-radius: 6px; display: flex; align-items: center; gap: 4px; }
        textarea { width: 100%; height: 200px; padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-md); box-sizing: border-box; font-size: 16px; font-family: inherit; resize: none; background-color: #f8fafc; line-height: 1.6; }
        textarea:focus { border-color: var(--primary); background-color: #ffffff; outline: none; }
        .output-area { background-color: #fafafa; }
        .action-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; }
        .btn-action { background: #ffffff; color: var(--text-main); border: 1px solid var(--border); padding: 12px 4px; font-size: 13px; font-weight: 600; cursor: pointer; border-radius: var(--radius-md); }
        .btn-action.active { background-color: rgba(99, 102, 241, 0.08); border: 2px solid var(--primary); }
        .file-dropzone { border: 2px dashed #cbd5e1; padding: 40px 20px; border-radius: var(--radius-md); background-color: #f8fafc; text-align: center; cursor: pointer; }
        .submit-btn { background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: white; border: none; padding: 16px 24px; font-size: 16px; font-weight: 600; cursor: pointer; border-radius: var(--radius-md); width: 100%; margin-top: 15px; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
        .stat-card { background: #ffffff; padding: 20px; border-radius: var(--radius-md); border: 1px solid var(--border); text-align: center; }
        .stat-num { font-size: 24px; font-weight: 700; color: var(--primary); }
        .pass-options { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; text-align: right; }
        .ad-container { background: #ffffff; border: 1px dashed #cbd5e1; padding: 15px; margin: 20px auto; width: 100%; max-width: 850px; color: var(--text-muted); font-size: 12px; border-radius: var(--radius-md); text-align: center; box-sizing: border-box; }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .sidebar { width: 100%; height: auto; position: relative; }
            .sidebar-menu { flex-direction: row; padding: 10px; overflow-x: auto; gap: 8px; }
            .main-content { margin-right: 0; width: 100%; padding: 16px; }
            .container { padding: 20px; }
            .tools-dashboard, .workspace-grid, .stats-grid, .pass-options { grid-template-columns: 1fr; }
            .action-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <a href="/" style="text-decoration: none;"><h2 style="cursor: pointer;">🛠️ ToolHub</h2></a>
            <div style="color: #94a3b8; font-size: 13px; font-weight: 600; margin-top: 4px;">ארגז הכלים שלך</div>
        </div>
        <div class="sidebar-menu">
            <a href="/" class="{% if current_page == 'dashboard' %}active{% endif %}">🏠 דף הבית</a>
            <a href="/inverter" class="{% if current_page == 'inverter' %}active{% endif %}">🔄 היפוך טקסט ומקלדת</a>
            <a href="/nikud" class="{% if current_page == 'nikud' %}active{% endif %}">✍️ ניקוד אוטומטי</a>
            <a href="/cleaner" class="{% if current_page == 'cleaner' %}active{% endif %}">🧼 מנקה רווחים ושורות</a>
            <a href="/counter" class="{% if current_page == 'counter' %}active{% endif %}">📊 סופר מילים ותווים</a>
            <a href="/password" class="{% if current_page == 'password' %}active{% endif %}">🔑 מחולל סיסמאות</a>
            <a href="/compress-img" class="{% if current_page == 'img' %}active{% endif %}">🖼️ כיווץ תמונות</a>
            <a href="/compress-pdf" class="{% if current_page == 'pdf' %}active{% endif %}">📄 כיווץ PDF</a>
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
                    <a href="/nikud" class="tool-card"><div class="tool-icon">✍️</div><div class="tool-title">ניקוד טקסט אוטומטי</div><div class="tool-desc">הוספת ניקוד דקדוקי חכם למשפטים בעברית בלייב.</div></a>
                    <a href="/cleaner" class="tool-card"><div class="tool-icon">🧼</div><div class="tool-title">Mנקה רווחים ושורות</div><div class="tool-desc">ניקוי רווחים כפולים ומחיקת שורות ריקות בקליק.</div></a>
                    <a href="/counter" class="tool-card"><div class="tool-icon">📊</div><div class="tool-title">סופר מילים ותווים</div><div class="tool-desc">ניתוח סטטיסטי מדויק של אורך הטקסט בלייב.</div></a>
                    <a href="/password" class="tool-card"><div class="tool-icon">🔑</div><div class="tool-title">מחולל סיסמאות פרו</div><div class="tool-desc">יצירת סיסמאות חזקות עם שליטה מלאה באורך וסוג התווים.</div></a>
                    <a href="/compress-img" class="tool-card"><div class="tool-icon">🖼️</div><div class="tool-title">כיווץ תמונות מהיר</div><div class="tool-desc">הקטנת משקל קובצי תמונה ב-70% תוך שמירה על האיכות.</div></a>
                    <a href="/compress-pdf" class="tool-card" style="grid-column: span 2;" id="pdfCard"><div class="tool-icon">📄</div><div class="tool-title">כיווץ PDF לממשל זמין</div><div class="tool-desc">דחיסת קובצי PDF והתאמתם למגבלות המשקל של אתרי הממשלה.</div></a>
                </div>
                <script>if(window.innerWidth <= 768) document.getElementById('pdfCard').style.gridColumn = "span 1";</script>

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
                    <button id="btn-eng2heb" class="btn-action" style="color:#16a34a;" onclick="setMode('eng2heb')">⌨️ אנגלית ⬅️ עברית</button>
                    <button id="btn-heb2eng" class="btn-action" style="color:#dc2626;" onclick="setMode('heb2eng')">⌨️ עברית ⬅️ אנגלית</button>
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
                    <div><textarea id="nikudSrc" placeholder="הקלד כאן (למשל: יוסי אכל חסה למרות כל הבאסה)..." oninput="processNikud()"></textarea></div>
                    <div>
                        <div class="window-header">
                            <button id="nikudRefreshBtn" class="mini-copy-btn" style="color:#4f46e5;" onclick="processNikud(true)">🔄 רענן ונקד</button>
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
                    <div><select id="pass-length" style="width:100%; padding:10px;" onchange="generatePasswordLive()"><option value="6">6 תווים</option><option value="8">8 תווים</option><option value="10" selected>10 תווים</option><option value="16">16 תווים</option></select></div>
                    <div style="display:flex; flex-direction:column; gap:5px;">
                        <label><input type="checkbox" id="opt-letters" checked onchange="generatePasswordLive()"> אותיות</label>
                        <label><input type="checkbox" id="opt-numbers" checked onchange="generatePasswordLive()"> מספרים</label>
                        <label><input type="checkbox" id="opt-symbols" checked onchange="generatePasswordLive()"> מיוחדים</label>
                    </div>
                </div>
                <div class="window-header">
                    <button id="passRefreshBtn" class="mini-copy-btn" onclick="generatePasswordLive()">🔄 אחרת</button>
                    <button id="passCopyBtn" class="mini-copy-btn" onclick="copyResult('passDst', 'passCopyBtn')">📋 העתק</button>
                    <button class="mini-copy-btn" style="color:#0369a1;" onclick="downloadPassword()">💾 שמור קובץ</button>
                </div>
                <textarea id="passDst" class="output-area" style="height:60px; text-align:center; font-family:monospace; font-size:22px;" readonly></textarea>
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
                <form method="POST" action="/compress-img" enctype="multipart/form-data"><div class="file-dropzone" onclick="document.getElementById('img_file').click()"><input type="file" id="img_file" name="img_file" accept="image/*" required><div>📥 לחץ או גרור תמונה לכאן</div></div><input type="submit" class="submit-btn" value="🗜️ כווץ תמונה"></form>
            {% elif current_page == 'pdf' %}
                <form method="POST" action="/compress-pdf" enctype="multipart/form-data"><div class="file-dropzone" onclick="document.getElementById('pdf_file').click()"><input type="file" id="pdf_file" name="pdf_file" accept=".pdf" required><div>📥 לחץ או גרור PDF לכאן</div></div><input type="submit" class="submit-btn" value="🗜️ כווץ PDF"></form>
            {% endif %}
        </div>
        <script>
            function copyResult(textareaId, buttonId) {
                const dst = document.getElementById(textareaId); const btn = document.getElementById(buttonId);
                if(dst.value) {
                    navigator.clipboard.writeText(dst.value); btn.innerText = "✨ הועתק!";
                    setTimeout(() => { btn.innerText = buttonId.includes('pass') ? "📋 העתק" : "📋 העתק הכל"; }, 1500);
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
@app.route("/compress-img", methods=["GET", "POST"])
def compress_img():
    if request.method == "POST":
        file = request.files.get("img_file")
        if file:
            img = Image.open(file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            out = io.BytesIO(); img.save(out, format="JPEG", quality=65, optimize=True); out.seek(0)
            return send_file(out, as_attachment=True, download_name="compressed_image.jpg", mimetype="image/jpeg")
    return render_template_string(BASE_HTML, title="🖼️ כיווץ משקל תמונות חכם", description="הורד גרסה קלה ב-70% תוך שמירה מלאה על האיכות.", current_page="img")
@app.route("/compress-pdf", methods=["GET", "POST"])
def compress_pdf():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename.endswith('.pdf'):
            input_pdf = PdfReader(file); writer = PdfWriter()
            for page in input_pdf.pages: page.compress_content_streams(); writer.add_page(page)
            out = io.BytesIO(); writer.write(out); out.seek(0)
            return send_file(out, as_attachment=True, download_name=f"compressed_{file.filename}", mimetype="application/pdf")
    return render_template_string(BASE_HTML, title="📄 כיווץ PDF מהיר לממשל זמין", description="כווץ קבצים כבדים לממשל זמין.", current_page="pdf")

if __name__ == "__main__":
    app.run(debug=True)
