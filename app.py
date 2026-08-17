import io
import os
import json
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session

# Import business logic services
from services.ads_service import load_ads_config, save_ads_config
from services.pdf_service import merge_pdfs, convert_pdf_to_images, compress_pdf
from services.image_service import convert_image, resize_image, apply_effect
from services.nikud_service import get_nikud

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'toolhub-secure-session-key-2026')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB upload limit

# Global links
PAYPAL_LINK = "https://www.paypal.me/zarug"
CONTACT_EMAIL = "maor.zarug@gmail.com"

# Context processor to inject ads and globals into all templates
@app.context_processor
def inject_globals():
    ads_cfg = load_ads_config()
    return {
        'top_ad': ads_cfg.get('top_ad', {}),
        'bottom_ad': ads_cfg.get('bottom_ad', {}),
        'PAYPAL_LINK': PAYPAL_LINK,
        'CONTACT_EMAIL': CONTACT_EMAIL
    }

# ==========================================
# עמודי האתר (Navigation Routes)
# ==========================================

@app.route('/')
def home():
    return render_template('dashboard.html', current_page='dashboard', title='דף הבית', description='ברוכים הבאים ל-ToolHub! בחרו כלי דיגיטלי מתקדם מתפריט הצד כדי להתחיל.')

@app.route('/inverter')
def inverter():
    return render_template('inverter.html', current_page='inverter', title='🔄 היפוך טקסט ומקלדת', description='הפוך טקסטים, תקן בעיות כיווניות של עברית/אנגלית או תקן שורות הפוכות בלייב.')

@app.route('/whatsapp')
def whatsapp():
    return render_template('whatsapp.html', current_page='whatsapp', title='🟢 מחולל קישורי וואטסאפ', description='צור קישור ישיר לשיחת וואטסאפ מותאם אישית הכולל הודעה מובנית מראש.')

@app.route('/nikud')
def nikud_page():
    return render_template('nikud.html', current_page='nikud', title='✍️ ניקוד טקסט אוטומטי', description='הזן משפט בעברית לקבלת ניקוד אוטומטי, עם אפשרות לשינוי ידני בתפריט צף.')

@app.route('/pdf-merge')
def pdf_merge_page():
    return render_template('pdf_merge.html', current_page='pdf-merge', title='📄 מיזוג קבצי PDF', description='מזג והערם מספר קבצי PDF נפרדים לכדי מסמך אחד שלם מאוחד.')

@app.route('/pdf-to-img')
def pdf_to_img_page():
    return render_template('pdf_to_img.html', current_page='pdf-to-img', title='🖼️ המרת PDF לתמונות', description='פירוק מסמך PDF לתמונות JPEG נפרדות בתוך קובץ ZIP אחד להורדה.')

@app.route('/pdf-compress')
def pdf_compress_page():
    return render_template('pdf_compress.html', current_page='pdf-compress', title='🗜️ דחיסת קבצי PDF', description='צמצם את נפח מסמכי ה-PDF והסריקות ב-70%-90% עבור אתרים ממשלתיים ושליחה במייל.')

@app.route('/img-convert')
def img_convert_page():
    return render_template('img_convert.html', current_page='img-convert', title='🔄 המרת פורמט תמונה', description='שנה את סוג קובץ התמונה שלך לפורמט נפוץ אחר (PNG, JPEG, WEBP, BMP) מיידית.')

@app.route('/img-resize')
def img_resize_page():
    return render_template('img_resize.html', current_page='img-resize', title='📐 שינוי גודל תמונה', description='התאם את ממדי הגובה והרוחב של התמונה בפיקסלים מדויקים.')

@app.route('/img-effects')
def img_effects_page():
    return render_template('img_effects.html', current_page='img-effects', title='🎨 פילטרים ואפקטים לתמונות', description='עצב את התמונה עם פילטרים: טשטוש, שחור-לבן, רישום וחדות. כולל תצוגה מקדימה והורדה.')

@app.route('/about')
def about():
    return render_template('about.html', current_page='about', title='ℹ️ אודות הפרויקט', description='הכירו את הסיפור מאחורי ToolHub ומדוע הקמנו אותו.')

# ==========================================
# מערכת ניהול פרסומות (Admin / Ad Management)
# ==========================================

@app.route('/admin')
def admin_page():
    is_auth = session.get('admin_authenticated', False)
    cfg = load_ads_config()
    return render_template('admin.html', current_page='admin', title='⚙️ ניהול פרסומות והגדרות', description='הגדרת קישורים, באנרים וקודי פרסום בשני אזורי הפרסום של האתר.', authenticated=is_auth, config=cfg)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    cfg = load_ads_config()
    if password == cfg.get('admin_password', 'admin'):
        session['admin_authenticated'] = True
        return redirect(url_for('admin_page'))
    return render_template('admin.html', current_page='admin', title='⚙️ ניהול פרסומות', description='כניסה למערכת ניהול', authenticated=False, error='סיסמה שגויה, נסה שוב.')

@app.route('/admin/save', methods=['POST'])
def admin_save():
    if not session.get('admin_authenticated', False):
        return redirect(url_for('admin_page'))
        
    cfg = load_ads_config()
    
    # Top ad update
    cfg['top_ad']['enabled'] = bool(request.form.get('top_enabled'))
    cfg['top_ad']['type'] = request.form.get('top_type', 'custom')
    cfg['top_ad']['image_url'] = request.form.get('top_image_url', '').strip()
    cfg['top_ad']['link_url'] = request.form.get('top_link_url', '').strip()
    cfg['top_ad']['alt_text'] = request.form.get('top_alt_text', 'פרסומת').strip()
    cfg['top_ad']['html_code'] = request.form.get('top_html_code', '').strip()

    # Bottom ad update
    cfg['bottom_ad']['enabled'] = bool(request.form.get('bottom_enabled'))
    cfg['bottom_ad']['type'] = request.form.get('bottom_type', 'custom')
    cfg['bottom_ad']['image_url'] = request.form.get('bottom_image_url', '').strip()
    cfg['bottom_ad']['link_url'] = request.form.get('bottom_link_url', '').strip()
    cfg['bottom_ad']['alt_text'] = request.form.get('bottom_alt_text', 'פרסומת').strip()
    cfg['bottom_ad']['html_code'] = request.form.get('bottom_html_code', '').strip()

    # Password update (optional)
    new_pass = request.form.get('new_password', '').strip()
    if new_pass:
        cfg['admin_password'] = new_pass

    save_ads_config(cfg)
    return render_template('admin.html', current_page='admin', title='⚙️ ניהול פרסומות', description='ההגדרות נשמרו בהצלחה', authenticated=True, config=cfg, message='✅ כל השינויים נשמרו והפרסומות עודכנו באתר!')

# ==========================================
# פעולות ועיבודי קצה (Backend Actions & APIs)
# ==========================================

@app.route('/api/nikud', methods=['POST'])
def api_nikud():
    data = request.get_json() or {}
    text = data.get('text', '')
    return jsonify({'result': get_nikud(text)})

@app.route('/action/pdf-merge', methods=['POST'])
def action_pdf_merge():
    files = request.files.getlist('files')
    try:
        out = merge_pdfs(files)
        return send_file(out, mimetype='application/pdf', as_attachment=True, download_name='merged_output.pdf')
    except Exception as e:
        return f"שגיאה במיזוג: {str(e)}", 500

@app.route('/action/pdf-to-img', methods=['POST'])
def action_pdf_to_img():
    f = request.files.get('file')
    try:
        zip_buffer = convert_pdf_to_images(f)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='pdf_extracted_images.zip')
    except Exception as e:
        return f"שגיאה בהמרת PDF לתמונות: {str(e)}", 500

@app.route('/action/pdf-compress', methods=['POST'])
def action_pdf_compress():
    f = request.files.get('file')
    level = request.form.get('level', 'recommended')
    try:
        out = compress_pdf(f, level=level)
        return send_file(out, mimetype='application/pdf', as_attachment=True, download_name='compressed_document.pdf')
    except Exception as e:
        return f"שגיאה בדחיסת PDF: {str(e)}", 500

@app.route('/action/img-convert', methods=['POST'])
def action_img_convert():
    f = request.files.get('file')
    target_format = request.form.get('format', 'JPEG')
    try:
        out, ext = convert_image(f, target_format)
        return send_file(out, mimetype=f'image/{ext}', as_attachment=True, download_name=f'converted_image.{ext}')
    except Exception as e:
        return f"שגיאה בהמרת תמונה: {str(e)}", 500

@app.route('/action/img-resize', methods=['POST'])
def action_img_resize():
    f = request.files.get('file')
    try:
        width = int(request.form.get('width', 800))
        height = int(request.form.get('height', 600))
        out, ext = resize_image(f, width, height)
        return send_file(out, mimetype=f'image/{ext}', as_attachment=True, download_name=f'resized_image.{ext}')
    except Exception as e:
        return f"שגיאה בשינוי גודל תמונה: {str(e)}", 500

@app.route('/action/img-effects-preview', methods=['POST'])
def action_img_effects_preview():
    f = request.files.get('file')
    effect = request.form.get('effect', 'grayscale')
    try:
        out = apply_effect(f, effect)
        return send_file(out, mimetype='image/jpeg')
    except Exception as e:
        return f"שגיאה בעיבוד אפקט: {str(e)}", 500

# ==========================================
# קבצים סטטיים ו-PWA
# ==========================================

@app.route('/ads.txt')
def ads_txt():
    return "google.com, pub-9821768397488065, DIRECT, f08c47fec0942fa0", 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/manifest.json')
def manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), 'static', 'manifest.json')
    if os.path.exists(manifest_path):
        return send_file(manifest_path, mimetype='application/manifest+json')
    return jsonify({"name": "ToolHub", "short_name": "ToolHub"})

@app.route('/icon.png')
def app_icon():
    static_icon = os.path.join(os.path.dirname(__file__), 'static', 'icon.png')
    root_icon = os.path.join(os.path.dirname(__file__), 'icon.png')
    
    if os.path.exists(static_icon):
        return send_file(static_icon, mimetype='image/png')
    elif os.path.exists(root_icon):
        return send_file(root_icon, mimetype='image/png')
        
    return "Icon not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
