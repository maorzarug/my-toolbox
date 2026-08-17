import io
import zipfile
from pypdf import PdfReader, PdfWriter
from PIL import Image
from pdf2image import convert_from_bytes

def _validate_file(file_input):
    if not file_input:
        raise ValueError("לא נבחר קובץ PDF")
    if hasattr(file_input, 'filename') and file_input.filename == '':
        raise ValueError("לא נבחר קובץ PDF")

def merge_pdfs(files):
    """
    Merges a list of uploaded PDF files into a single BytesIO buffer.
    """
    if not files:
        raise ValueError("לא נבחרו קבצים למיזוג")
    
    writer = PdfWriter()
    added_count = 0
    for f in files:
        fname = getattr(f, 'filename', '')
        if not fname or fname.lower().endswith('.pdf'):
            try:
                reader = PdfReader(f)
                for page in reader.pages:
                    writer.add_page(page)
                added_count += 1
            except Exception:
                pass
                
    if added_count == 0:
        raise ValueError("לא נמצאו דפי PDF תקינים למיזוג")
        
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def convert_pdf_to_images(file_storage):
    """
    Extracts all pages from a PDF as JPEG images bundled into a ZIP file BytesIO buffer.
    """
    _validate_file(file_storage)
        
    pdf_bytes = file_storage.read()
    images = convert_from_bytes(pdf_bytes)
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, img in enumerate(images):
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            zip_file.writestr(f'page_{i+1}.jpg', img_buffer.read())
            
    zip_buffer.seek(0)
    return zip_buffer

def compress_pdf(file_storage, level="recommended"):
    """
    Smart PDF compressor specifically optimized for scanned documents, gov forms, and email.
    Compresses both PDF content streams and downsamples/re-encodes embedded high-res images.
    """
    _validate_file(file_storage)

    pdf_bytes = file_storage.read() if hasattr(file_storage, 'read') else file_storage
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Clone reader pages into writer
    for page in reader.pages:
        writer.add_page(page)

    quality = 65
    max_dim = 1600
    if level == 'high':
        quality = 40
        max_dim = 1200
    elif level == 'light':
        quality = 80
        max_dim = 2000

    for page in writer.pages:
        # Compress vector streams
        try:
            page.compress_content_streams()
        except Exception:
            pass

        # Compress embedded scan images
        try:
            for img in page.images:
                try:
                    pil_img = Image.open(io.BytesIO(img.data))
                    orig_w, orig_h = pil_img.size
                    if max(orig_w, orig_h) > max_dim:
                        scale = max_dim / max(orig_w, orig_h)
                        new_size = (int(orig_w * scale), int(orig_h * scale))
                        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    if pil_img.mode in ('RGBA', 'LA', 'P'):
                        bg = Image.new('RGB', pil_img.size, (255, 255, 255))
                        if pil_img.mode == 'RGBA':
                            bg.paste(pil_img, mask=pil_img.split()[3])
                        else:
                            bg.paste(pil_img.convert('RGBA'), mask=pil_img.convert('RGBA').split()[3])
                        pil_img = bg
                    elif pil_img.mode != 'RGB' and pil_img.mode != 'L':
                        pil_img = pil_img.convert('RGB')
                    
                    img_out = io.BytesIO()
                    pil_img.save(img_out, format='JPEG', quality=quality, optimize=True)
                    img_out.seek(0)

                    img.replace(Image.open(img_out), quality=quality)
                except Exception:
                    pass
        except Exception:
            pass

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out
