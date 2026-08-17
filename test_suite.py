import io
import unittest
from PIL import Image, ImageDraw
from app import app
from services.pdf_service import compress_pdf, merge_pdfs
from services.image_service import convert_image, resize_image, apply_effect
from services.nikud_service import get_nikud
from services.ads_service import load_ads_config, save_ads_config

class TestToolHub(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_all_routes_status_200(self):
        routes = [
            '/',
            '/inverter',
            '/whatsapp',
            '/nikud',
            '/pdf-merge',
            '/pdf-to-img',
            '/pdf-compress',
            '/img-convert',
            '/img-resize',
            '/img-effects',
            '/about',
            '/admin',
            '/manifest.json',
            '/ads.txt',
            '/icon.png'
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertIn(response.status_code, [200, 302], f"Route {route} failed with status {response.status_code}")

    def test_nikud_api(self):
        response = self.client.post('/api/nikud', json={'text': 'שלום וברכה יום נעים'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('result', data)
        self.assertIn('שָׁלוֹם', data['result'])
        self.assertIn('וּבְרָכָה', data['result'])

    def test_pdf_compression_heavy_scan(self):
        # Create a large simulated scanned page (2480x3508 A4 300DPI)
        img = Image.new('RGB', (2480, 3508), color=(245, 245, 245))
        draw = ImageDraw.Draw(img)
        for y in range(100, 3400, 40):
            draw.line([(100, y), (2380, y)], fill=(30, 30, 30), width=3)

        pdf_buf = io.BytesIO()
        img.save(pdf_buf, format='PDF', quality=95)
        orig_size = len(pdf_buf.getvalue())
        pdf_buf.seek(0)
        
        # Test file upload mock
        class MockFileStorage:
            filename = 'scanned_doc.pdf'
            def read(self):
                return pdf_buf.getvalue()

        compressed_stream = compress_pdf(MockFileStorage(), level='recommended')
        comp_size = len(compressed_stream.getvalue())
        reduction = (1 - comp_size / orig_size) * 100
        
        print(f"\n[PDF Compression Test] Original: {orig_size:,} bytes -> Compressed: {comp_size:,} bytes ({reduction:.1f}% reduction)")
        self.assertLess(comp_size, orig_size * 0.5, "PDF should be compressed by at least 50%")

    def test_image_service_operations(self):
        # Create test image
        img = Image.new('RGBA', (400, 300), color=(255, 100, 50, 255))
        img_buf = io.BytesIO()
        img.save(img_buf, format='PNG')
        img_buf.seek(0)

        class MockFile:
            filename = 'test.png'
            def __init__(self, buf):
                self.buf = buf
            def read(self):
                return self.buf.getvalue()
            def seek(self, pos):
                self.buf.seek(pos)

        # 1. Convert
        img_buf.seek(0)
        out_conv, ext = convert_image(img_buf, 'JPEG')
        self.assertEqual(ext, 'jpg')
        self.assertGreater(len(out_conv.getvalue()), 0)

        # 2. Resize
        img_buf.seek(0)
        out_resize, _ = resize_image(img_buf, 200, 150)
        res_img = Image.open(out_resize)
        self.assertEqual(res_img.size, (200, 150))

        # 3. Effect
        img_buf.seek(0)
        out_fx = apply_effect(img_buf, 'grayscale')
        self.assertGreater(len(out_fx.getvalue()), 0)

    def test_admin_ad_flow(self):
        # 1. Login with correct password
        res = self.client.post('/admin/login', data={'password': 'admin'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('שמור את כל הגדרות הפרסומות'.encode('utf-8'), res.data)

        # 2. Save ad configuration
        save_res = self.client.post('/admin/save', data={
            'top_enabled': '1',
            'top_type': 'custom',
            'top_image_url': 'https://example.com/top_banner.png',
            'top_link_url': 'https://example.com',
            'top_alt_text': 'באנר ראשי',
            'bottom_enabled': '1',
            'bottom_type': 'custom',
            'bottom_image_url': 'https://example.com/bottom_banner.png',
            'bottom_link_url': 'https://example.com/shop',
            'bottom_alt_text': 'באנר תחתון'
        }, follow_redirects=True)
        self.assertEqual(save_res.status_code, 200)

        # 3. Verify ad appears on home page
        home_res = self.client.get('/')
        self.assertIn('https://example.com/top_banner.png'.encode('utf-8'), home_res.data)
        self.assertIn('https://example.com/bottom_banner.png'.encode('utf-8'), home_res.data)

if __name__ == '__main__':
    unittest.main()
