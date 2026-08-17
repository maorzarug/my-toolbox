import io
from PIL import Image, ImageEnhance, ImageFilter

def _validate_file(file_input):
    if not file_input:
        raise ValueError("לא נבחר קובץ")
    if hasattr(file_input, 'filename') and file_input.filename == '':
        raise ValueError("לא נבחר קובץ")

def convert_image(file_storage, target_format="JPEG"):
    """
    Converts image to target format (JPEG, PNG, WEBP, BMP).
    """
    _validate_file(file_storage)
        
    target_format = target_format.upper()
    img = Image.open(file_storage)
    
    if img.mode in ('RGBA', 'P', 'LA') and target_format == 'JPEG':
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[3])
        img = bg
        
    out = io.BytesIO()
    img.save(out, format=target_format, quality=90)
    out.seek(0)
    
    ext = target_format.lower()
    if ext == 'jpeg':
        ext = 'jpg'
    return out, ext

def resize_image(file_storage, width, height):
    """
    Resizes image to specific width and height with high-quality Lanczos resampling.
    """
    _validate_file(file_storage)
        
    img = Image.open(file_storage)
    resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    out = io.BytesIO()
    orig_format = img.format if img.format else 'JPEG'
    resized_img.save(out, format=orig_format)
    out.seek(0)
    
    ext = orig_format.lower()
    if ext == 'jpeg':
        ext = 'jpg'
    return out, ext

def apply_effect(file_storage, effect="grayscale"):
    """
    Applies image effects (grayscale, blur, contour, brighten, sharpen)
    and returns a clean JPEG BytesIO buffer.
    """
    _validate_file(file_storage)
        
    img = Image.open(file_storage)
    
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

    # Handle transparency for clean JPEG output
    final_img = processed
    if final_img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', final_img.size, (255, 255, 255))
        if final_img.mode == 'RGBA':
            background.paste(final_img, mask=final_img.split()[3])
        else:
            background.paste(final_img.convert('RGBA'), mask=final_img.convert('RGBA').split()[3])
        final_img = background
    elif final_img.mode != 'RGB':
        final_img = final_img.convert('RGB')
        
    out = io.BytesIO()
    final_img.save(out, format='JPEG', quality=85, optimize=True)
    out.seek(0)
    return out
