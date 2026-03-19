from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import requests
import json
import os
import time
import threading
from datetime import datetime
import psutil
import random
import webview
import pystray
import socket

load_dotenv()

app = Flask(__name__)

HISTORY_FILE = 'posts/history.json'
SCHEDULES_FILE = 'posts/schedules.json'
CONFIG_FILE = 'posts/config.json'
SHEET_URL = os.getenv('SHEET_URL')
FONT_PATH = os.getenv('FONT_PATH', 'C:/Windows/Fonts/arialbd.ttf')

def generate_image_with_pil(template_name, website, da, dr, traffic, filename):
    """Generate image using PIL by injecting text into PNG template"""
    try:
        # values
        website_url = website
        
        # Extract website name and split into parts
        website_name = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('.')[0]
        
        # split website name
        if len(website_name) > 6:
            mid = len(website_name) // 2
            part1 = website_name[:mid]
            part2 = website_name[mid:]
        else:
            part1 = website_name
            part2 = " "
        
        # open template
        img = Image.open("template.png").convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # fonts
        title_font = ImageFont.truetype(FONT_PATH, 110)
        value_font = ImageFont.truetype(FONT_PATH, 43)
        url_font = ImageFont.truetype(FONT_PATH, 32)
        
        # base position
        x = 110
        y = 194
        
        # draw first part
        draw.text((x, y), part1, fill=(0,0,0), font=title_font)
        
        # measure width of first part
        bbox = draw.textbbox((0,0), part1, font=title_font)
        width = bbox[2]
        
        # draw second part right after it
        draw.text((x + width + 10, y), part2, fill=(29, 154, 247), font=title_font)
        
        # url
        draw.text((110,310), website_url, fill=(0,0,0), font=url_font)
        
        # values
        draw.text((333,504), str(da), fill=(0,0,0), font=value_font)
        draw.text((333,585), str(dr), fill=(0,0,0), font=value_font)
        draw.text((380,672), str(traffic), fill=(0,0,0), font=value_font)
        
        # save
        output_path = f"posts/images/{filename}"
        img.save(output_path)
        return True
        
    except Exception as e:
        print(f"Error generating PIL image: {e}")
        return False

SAMESITE_MAP = {'no_restriction': 'None', 'unspecified': 'None', 'lax': 'Lax', 'strict': 'Strict', 'none': 'None'}

def show_notification(title, message, color='#3b82f6'):
    """Tkinter bottom-right popup — ignores Windows DND."""
    def _show():
        import tkinter as tk
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.configure(bg='#161b27')
        W, H = 300, 70
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{sw - W - 16}+{sh - H - 50}")
        frame = tk.Frame(root, bg=color, padx=1, pady=1)
        frame.pack(fill='both', expand=True)
        inner = tk.Frame(frame, bg='#161b27', padx=12, pady=10)
        inner.pack(fill='both', expand=True)
        tk.Frame(inner, bg=color, width=3).pack(side='left', fill='y', padx=(0, 10))
        text_frame = tk.Frame(inner, bg='#161b27')
        text_frame.pack(side='left', fill='both', expand=True)
        tk.Label(text_frame, text=title, bg='#161b27', fg='#ffffff',
                 font=('Segoe UI', 9, 'bold'), anchor='w').pack(fill='x')
        tk.Label(text_frame, text=message, bg='#161b27', fg='#9ca3af',
                 font=('Segoe UI', 8), anchor='w', wraplength=220).pack(fill='x')
        tk.Button(inner, text='✕', bg='#161b27', fg='#4b5563', bd=0,
                  font=('Segoe UI', 8), cursor='hand2',
                  activebackground='#161b27', activeforeground='#fff',
                  command=root.destroy).pack(side='right', anchor='n')
        # slide in
        final_y = sh - H - 50
        for y in range(sh, final_y, -4):
            root.geometry(f"{W}x{H}+{sw - W - 16}+{y}")
            root.update()
            root.after(1)
        root.after(4000, root.destroy)
        root.mainloop()
    threading.Thread(target=_show, daemon=True).start()



def to_bold(text):
    normal = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    bold   = '𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵'
    table  = str.maketrans(normal, bold)
    return text.translate(table)

def build_caption(website, da, dr, traffic):
    return (
        f"{to_bold('Premium SaaS Guest Posting on')} {website}\n"
        f"Boost Your SEO & Organic Traffic\n\n"
        f"🌐 {to_bold('Website:')} {website}\n"
        f"📊 {to_bold('DA:')} {da} | {to_bold('DR:')} {dr}\n"
        f"📈 {to_bold('Monthly Traffic:')} {traffic}\n\n"
        f"🔥 {to_bold('What We Offer')}\n"
        f"✔ Do-Follow, SEO-Optimized Backlinks\n"
        f"✔ Direct Admin-Level Publishing\n"
        f"✔ Permanent Live Posts\n"
        f"✔ Fast Google Indexing\n"
        f"✔ Affordable & Customizable Packages\n"
        f"✔ Guaranteed Performance\n"
        f"✔ On-Time Delivery — Every Time\n\n"
        f"📋 {to_bold('View List:')}\n"
        f"https://docs.google.com/spreadsheets/d/1Y9kRDPV1wRBQRGZ69Xn2Bn4i_J3Bt94ZyCm8YTz__DM/edit?usp=sharing\n\n"
        f"📩 {to_bold('Get Started Today!')}\n"
        f"💬 DM for a FREE Strategy Consultation\n"
        f"📱 {to_bold('WhatsApp:')} +92 344 4255916"
    )

def check_internet(retries=10, delay=15):
    """Block until internet is available. Notifies user on first failure."""
    for attempt in range(retries):
        try:
            requests.get('https://www.google.com', timeout=5)
            return True
        except Exception:
            if attempt == 0:
                show_notification('📡 No Internet', 'Waiting for connection...', '#f59e0b')
            print(f"No internet. Retry {attempt+1}/{retries} in {delay}s...")
            time.sleep(delay)
    show_notification('📡 Internet Failed', 'Could not connect after retries.', '#ef4444')
    return False

def normalize_cookies(cookies):
    for c in cookies:
        ss = c.get('sameSite', '')
        c['sameSite'] = SAMESITE_MAP.get(str(ss).lower(), 'None')
    return cookies

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return [] if file in [HISTORY_FILE, SCHEDULES_FILE] else {}

def save_json(file, data):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/templates/<path:filename>')
def serve_template(filename):
    return send_from_directory('templates', filename)

@app.route('/template-preview/<template_name>')
def template_preview(template_name):
    try:
        # Just return the raw template image path
        template_path = f'template.png'
        if os.path.exists(template_path):
            return jsonify({'image_url': f'/template.png'})
        else:
            return jsonify({'error': 'Template not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/posts/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('posts/images', filename)

@app.route('/icon.png')
def serve_icon():
    return send_from_directory('.', 'icon.png')

@app.route('/ali.png')
def serve_ali_image():
    return send_from_directory('.', 'ali.png')

@app.route('/template.png')
def serve_template_image():
    return send_from_directory('.', 'template.png')

@app.route('/history')
def get_history():
    return jsonify(load_json(HISTORY_FILE))

@app.route('/config', methods=['GET', 'POST'])
def save_config():
    if request.method == 'GET':
        return jsonify(load_json(CONFIG_FILE))
    save_json(CONFIG_FILE, request.json)
    return jsonify({'status': 'saved'})

@app.route('/schedules', methods=['GET', 'POST'])
def schedules():
    if request.method == 'POST':
        data = request.json
        schedules = load_json(SCHEDULES_FILE)
        
        # Check if time already exists
        if any(s['time'] == data['time'] for s in schedules):
            return jsonify({'error': 'Time slot already taken'})
        
        schedules.append(data)
        save_json(SCHEDULES_FILE, schedules)
        return jsonify({'status': 'created'})
    
    return jsonify(load_json(SCHEDULES_FILE))

@app.route('/schedules/<time>', methods=['DELETE'])
def delete_schedule(time):
    schedules = load_json(SCHEDULES_FILE)
    schedules = [s for s in schedules if s['time'] != time]
    save_json(SCHEDULES_FILE, schedules)
    return jsonify({'status': 'deleted'})

@app.route('/accounts')
def get_accounts():
    platforms = ['linkedin', 'facebook', 'twitter', 'instagram']
    accounts = []
    
    for platform in platforms:
        cookie_file = f'cookies/{platform}.json'
        status = 'logged_in' if os.path.exists(cookie_file) else 'not_logged_in'
        accounts.append({
            'platform': platform,
            'status': status,
            'cookie_file': cookie_file
        })
    
    return jsonify(accounts)

@app.route('/cookies/<platform>', methods=['GET', 'POST'])
def manage_cookies(platform):
    if platform not in ['linkedin', 'facebook', 'twitter', 'instagram']:
        return jsonify({'error': 'Invalid platform'}), 400
    cookie_file = f'cookies/{platform}.json'
    if request.method == 'GET':
        if os.path.exists(cookie_file):
            return jsonify(load_json(cookie_file))
        return jsonify([])
    cookies = request.json
    if not isinstance(cookies, list):
        return jsonify({'error': 'Cookies must be a JSON array'}), 400
    os.makedirs('cookies', exist_ok=True)
    save_json(cookie_file, cookies)
    return jsonify({'status': 'saved', 'count': len(cookies)})

@app.route('/test-browser')
def test_browser():
    try:
        config = load_json(CONFIG_FILE)
        headless = config.get('headless', False)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto('https://www.google.com')
            page.wait_for_timeout(3000)
            browser.close()
        return jsonify({'status': 'Browser test successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-login/<platform>')
def test_login_platform(platform):
    if platform not in ['linkedin', 'facebook', 'twitter', 'instagram']:
        return jsonify({'error': 'Invalid platform'}), 400
    
    cookie_file = f'cookies/{platform}.json'
    if not os.path.exists(cookie_file):
        return jsonify({'error': 'No cookies found for this platform'}), 400
    
    try:
        threading.Thread(target=test_platform_cookies, args=(platform,), daemon=True).start()
        return jsonify({'status': 'opening test browser'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def test_platform_cookies(platform):
    try:
        cookie_file = f'cookies/{platform}.json'
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
        cookies = normalize_cookies(cookies)
        print(f"Testing {platform} with {len(cookies)} cookies...")
        
        config = load_json(CONFIG_FILE)
        headless = config.get('headless', False)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            
            # Add cookies
            context.add_cookies(cookies)
            page = context.new_page()
            
            # Navigate to platform
            urls = {
                'linkedin': 'https://www.linkedin.com/feed/',
                'facebook': 'https://www.facebook.com/',
                'twitter': 'https://twitter.com/home',
                'instagram': 'https://www.instagram.com/'
            }
            
            page.goto(urls[platform])
            page.wait_for_timeout(3000)
            
            print(f"Test browser opened for {platform} - check login status")
            
            # Wait for user to close browser
            try:
                while True:
                    page.wait_for_timeout(1000)
                    page.title()  # This will throw error when browser closes
            except Exception:
                pass  # Browser closed by user
                
    except Exception as e:
        print(f"Error testing {platform} cookies: {e}")

@app.route('/login/<platform>')
def login_platform(platform):
    if platform not in ['linkedin', 'facebook', 'twitter', 'instagram']:
        return jsonify({'error': 'Invalid platform'}), 400
    
    try:
        print(f"Starting login thread for {platform}")
        thread = threading.Thread(target=open_login_browser, args=(platform,), daemon=True)
        thread.start()
        print(f"Login thread started for {platform}")
        return jsonify({'status': 'opening browser'})
    except Exception as e:
        print(f"Error starting login thread: {e}")
        return jsonify({'error': str(e)}), 500

def open_login_browser(platform):
    try:
        print(f"Starting login process for {platform}...")
        os.makedirs('cookies', exist_ok=True)
        
        config = load_json(CONFIG_FILE)
        headless = config.get('headless', False)
        with sync_playwright() as p:
            print(f"Launching browser for {platform}...")
            browser = p.chromium.launch(headless=headless)
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768}
            )
            
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            urls = {
                'linkedin': 'https://www.linkedin.com/login',
                'facebook': 'https://www.facebook.com/login',
                'twitter': 'https://twitter.com/login',
                'instagram': 'https://www.instagram.com/accounts/login/'
            }
            
            print(f"Navigating to {urls[platform]}...")
            page.goto(urls[platform])
            page.wait_for_timeout(3000)
            
            print(f"Browser opened for {platform}. Please login and close the browser when done...")
            
            # Wait for browser to be closed by user
            try:
                while True:
                    page.wait_for_timeout(1000)  # Check every second
                    # This will throw an error when browser is closed
                    page.title()
            except Exception:
                # Browser was closed by user
                pass
            
            # Save cookies before browser closes completely
            try:
                cookies = context.cookies()
                cookie_path = f'cookies/{platform}.json'
                with open(cookie_path, 'w') as f:
                    json.dump(cookies, f, indent=2)
                print(f"Login completed for {platform}! Cookies saved to {cookie_path}")
                print(f"Saved {len(cookies)} cookies")
            except Exception as e:
                print(f"Could not save cookies: {e}")
            
    except Exception as e:
        print(f"Error in login process for {platform}: {str(e)}")
        import traceback
        traceback.print_exc()
def fetch_and_generate():
    print("=== FETCH AND GENERATE DEBUG START ===")
    if not check_internet():
        print("ERROR: No internet connection. Aborting.")
        return
    config = load_json(CONFIG_FILE)
    template = config.get('template', 'template1')
    platforms = config.get('platforms', [])
    
    print(f"Config loaded - Template: {template}, Platforms: {platforms}")
    
    if not platforms:
        print("ERROR: No platforms selected")
        return
    
    # Fetch sheet data
    print(f"Fetching data from: {SHEET_URL}")
    try:
        response = requests.get(SHEET_URL + '?action=list')
        print(f"Response status: {response.status_code}")
        rows = response.json()
        print(f"Total rows received: {len(rows)}")
        print(f"First 3 rows: {rows[:3] if len(rows) > 0 else 'No rows'}")
    except Exception as e:
        print(f"ERROR fetching sheet data: {e}")
        return
    
    history = load_json(HISTORY_FILE)
    
    # Find first row that is not posted (empty, FALSE, or PENDING)
    target_row = None
    for i, row in enumerate(rows):
        # Check both possible field names for isPosted
        is_posted = row.get('isPosted', row.get('Is Posted', False))
        status = str(is_posted).upper() if is_posted is not None else ''
        website_field = row.get('website', row.get('Website', 'N/A'))
        print(f"Row {i}: Status='{status}', Website='{website_field}'")
        if not is_posted or status not in ['TRUE', 'POSTED']:
            target_row = row
            print(f"SELECTED ROW {i}: {target_row}")
            break
    
    if not target_row:
        print("ERROR: No unposted rows found")
        return
    
    # Use correct field names from Google Sheets
    website = target_row.get('website', target_row.get('Website', ''))
    da = target_row.get('da', target_row.get('DA', ''))
    dr = target_row.get('dr', target_row.get('DR', ''))
    traffic = target_row.get('traffic', target_row.get('Traffic', ''))
    
    print(f"Extracted data - Website: '{website}', DA: '{da}', DR: '{dr}', Traffic: '{traffic}'")
    
    # Extract website name from URL
    website_name = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('.')[0].title()
    
    # Split website name into two parts for styling
    if len(website_name) > 6:
        mid = len(website_name) // 2
        website_name_part1 = website_name[:mid].upper()
        website_name_part2 = website_name[mid:].upper()
    else:
        website_name_part1 = website_name.upper()
        website_name_part2 = "POST"
    
    print(f"Website name processing - Original: '{website_name}', Part1: '{website_name_part1}', Part2: '{website_name_part2}'")
    
    # Generate image using PIL
    filename = f"{website.replace('.', '_').replace('/', '_')}_{int(time.time())}.png"
    print(f"Generating PIL image: {filename}")
    
    success = generate_image_with_pil(template, website, da, dr, traffic, filename)
    if not success:
        print("ERROR: Failed to generate image with PIL")
        return
    
    image_path = f'posts/images/{filename}'
    
    # Post to platforms
    for platform in platforms:
        post_to_platform_with_retry(platform, image_path, website, da, dr, traffic)
    
    # Save history
    history.append({
        'website': website,
        'da': da,
        'dr': dr,
        'traffic': traffic,
        'image': image_path,
        'template': template,
        'status': 'posted',
        'platforms': platforms,
        'posted_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    
    save_json(HISTORY_FILE, history)
    
    # Update sheet status to TRUE
    update_url = SHEET_URL + f'?action=update&website={website}&status=TRUE'
    requests.get(update_url)

  

def post_to_platform_with_retry(platform, image_path, website, da, dr, traffic, max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"[{platform}] Attempt {attempt}/{max_retries}")
        if not check_internet():
            show_notification(f'{platform.title()} ❌ Failed', 'No internet connection.', '#ef4444')
            return
        success = post_to_platform(platform, image_path, website, da, dr, traffic)
        if success:
            return
        if attempt < max_retries:
            show_notification(f'{platform.title()} 🔄 Retrying', f'Attempt {attempt} failed. Retrying in 10s...', '#f59e0b')
            print(f"[{platform}] Attempt {attempt} failed. Waiting 10s before retry...")
            time.sleep(10)
    show_notification(f'{platform.title()} ❌ Failed', f'All {max_retries} attempts failed.', '#ef4444')

def post_to_platform(platform, image_path, website, da, dr, traffic):
    caption = build_caption(website, da, dr, traffic)

    cookie_file = f'cookies/{platform}.json'
    if not os.path.exists(cookie_file):
        show_notification(f'{platform.title()} ❌', 'No cookies found. Please login first.', '#ef4444')
        print(f"No cookies found for {platform}. Please login first.")
        return False

    has_media = os.path.exists(image_path) if image_path else False
    config = load_json(CONFIG_FILE)
    headless = config.get('headless', False)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768}
            )
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            context.add_cookies(normalize_cookies(cookies))
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            if platform == 'linkedin':
                page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(6000)

                page.click('div.share-box-feed-entry__top-bar button')
                page.wait_for_timeout(3000)

                if has_media:
                    with page.expect_file_chooser() as fc_info:
                        page.click('button.share-promoted-detour-button[aria-label="Add media"]')
                    fc_info.value.set_files(image_path)
                    page.wait_for_timeout(6000)

                    next_btn = page.locator('button.share-box-footer__primary-btn[aria-label="Next"]')
                    next_btn.wait_for(state='visible', timeout=15000)
                    next_btn.click()
                    page.wait_for_timeout(3000)

                editor = page.locator('div.ql-editor[contenteditable="true"]').first
                editor.wait_for(state='visible', timeout=15000)
                editor.click()
                page.wait_for_timeout(500)
                page.keyboard.type(caption, delay=30)
                page.wait_for_timeout(1000)

                post_btn = page.locator('button.share-actions__primary-action')
                post_btn.wait_for(state='visible', timeout=15000)
                for _ in range(20):
                    if not post_btn.is_disabled():
                        break
                    page.wait_for_timeout(500)
                post_btn.click()
                page.wait_for_timeout(5000)
                
            elif platform == 'facebook':
                page.goto('https://www.facebook.com/', wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(7000)

                try:
                    if has_media:
                        page.set_input_files('input[type="file"][accept*="image"]', image_path)
                        page.wait_for_timeout(6000)
                        print(f"Uploaded image: {image_path}")

                    text_box = page.locator('div[contenteditable="true"][role="textbox"]').first
                    text_box.click()
                    page.wait_for_timeout(500)
                    page.keyboard.type(caption, delay=30)
                    page.wait_for_timeout(2000)

                    page.click('div[aria-label="Next"][role="button"]', timeout=15000)
                    page.wait_for_timeout(3000)

                    page.click('div[aria-label="Post"][role="button"]', timeout=15000)
                    page.wait_for_timeout(6000)

                except Exception as fb_error:
                    print(f"Facebook posting error: {fb_error}")
                    show_notification('Facebook ⚠️ Error', str(fb_error)[:80], '#f59e0b')
                    return False
                
            elif platform == 'twitter':
                page.goto('https://x.com/home', wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(6000)

                editor = page.locator('div[data-testid="tweetTextarea_0"]').first
                editor.wait_for(state='visible', timeout=15000)
                editor.click()
                page.wait_for_timeout(500)
                page.keyboard.type(caption, delay=30)
                page.wait_for_timeout(1000)

                if has_media:
                    page.locator('input[data-testid="fileInput"]').set_input_files(image_path)
                    page.wait_for_timeout(6000)

                page.wait_for_selector('button[data-testid="tweetButtonInline"]:not([disabled])', timeout=20000)
                page.wait_for_timeout(500)
                page.evaluate("document.querySelector('button[data-testid=\"tweetButtonInline\"]').click()")
                page.wait_for_timeout(5000)
                
            elif platform == 'instagram':
                page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(6000)

                if not has_media:
                    print(f"No media found for Instagram - media is required")
                    return False

                not_now = page.locator('button._a9--._ap36._a9_1')
                if not_now.is_visible():
                    not_now.click()
                    page.wait_for_timeout(1000)

                page.click('a[role="link"] svg[aria-label="New post"]')
                page.wait_for_timeout(3000)

                page.click('a[role="link"]:has(svg[aria-label="Post"])', timeout=15000)
                page.wait_for_timeout(3000)

                file_input = page.locator('form[role="presentation"] input[type="file"]').first
                file_input.wait_for(state='attached', timeout=15000)
                file_input.set_input_files(image_path)
                page.wait_for_timeout(5000)

                page.locator('div._ac7b._ac7d div[role="button"]').filter(has_text='Next').click()
                page.wait_for_timeout(3000)

                page.locator('div._ac7b._ac7d div[role="button"]').filter(has_text='Next').click()
                page.wait_for_timeout(3000)

                caption_box = page.locator('div[aria-label="Write a caption..."][contenteditable="true"]').first
                caption_box.wait_for(state='visible', timeout=15000)
                caption_box.click()
                page.wait_for_timeout(500)
                page.keyboard.type(caption, delay=30)
                page.wait_for_timeout(1000)

                page.locator('div._ac7b._ac7d div[role="button"]').filter(has_text='Share').click()
                page.wait_for_selector('div[aria-label="Post shared"][role="dialog"]', state='visible', timeout=60000)
            
            print(f"Posted to {platform} successfully!")
            show_notification(f'{platform.title()} ✅ Posted', f'Successfully posted on {platform.title()}', '#22c55e')
            page.wait_for_timeout(5000)
            return True

        except Exception as e:
            print(f"Error posting to {platform}: {e}")
            return False
        finally:
            try:
                browser.close()
            except:
                pass

def check_missed_schedules():
    schedules = load_json(SCHEDULES_FILE)
    if not schedules:
        return
    today = datetime.now().strftime('%Y-%m-%d')
    now_minutes = datetime.now().hour * 60 + datetime.now().minute
    last_run = load_json('posts/last_run.json')

    for schedule in schedules:
        t = schedule['time']
        h, m = map(int, t.split(':'))
        if (h * 60 + m) < now_minutes and last_run.get(t) != today:
            print(f"Running missed schedule: {schedule['name']} at {t}")
            last_run[t] = today
            save_json('posts/last_run.json', last_run)
            fetch_and_generate()
            time.sleep(5)


def scheduler_loop():
    check_missed_schedules()
    fired_this_minute = None
    last_missed_check = datetime.now()

    while True:
        schedules = load_json(SCHEDULES_FILE)
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        today = now.strftime('%Y-%m-%d')
        last_run = load_json('posts/last_run.json')

        # Re-check missed schedules every 5 minutes
        if (now - last_missed_check).total_seconds() >= 300:
            check_missed_schedules()
            last_missed_check = now

        for schedule in schedules:
            t = schedule['time']
            if t == current_time and last_run.get(t) != today and fired_this_minute != f"{today}_{t}":
                print(f"Firing schedule: {schedule['name']} at {t}")
                fired_this_minute = f"{today}_{t}"
                last_run[t] = today
                save_json('posts/last_run.json', last_run)
                fetch_and_generate()
                break

        time.sleep(30)


# ── Single instance ──────────────────────────────────────────────────────────
_LOCK_PORT = 19847  # arbitrary port used as a mutex

def _acquire_instance_lock():
    """Try to bind a socket. Returns the socket if we are the first instance, None otherwise."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        sock.bind(('127.0.0.1', _LOCK_PORT))
        sock.listen(1)
        return sock
    except OSError:
        return None

def _focus_existing_instance():
    """Send a wake signal to the already-running instance."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', _LOCK_PORT))
        s.sendall(b'show')
        s.close()
    except Exception:
        pass

def _listen_for_focus(lock_sock):
    """Background thread: when a second instance connects, restore the window."""
    while True:
        try:
            conn, _ = lock_sock.accept()
            conn.recv(16)
            conn.close()
            if _window:
                _window.show()
                _window.restore()
        except Exception:
            break




FLASK_URL = 'http://localhost:5110'
_window   = None
_tray     = None


def _create_tray_icon():
    return Image.open('icon.png').convert('RGBA').resize((64, 64))


def _show_window(icon, item):
    _window.show()
    _window.restore()


def _on_closing():
    _window.hide()
    return False


def _quit_app(icon, item):
    icon.stop()
    _window.destroy()
    os._exit(0)


def _start_tray():
    global _tray
    menu  = pystray.Menu(
        pystray.MenuItem('Open PostPilot', _show_window, default=True),
        pystray.MenuItem('Quit', _quit_app)
    )
    _tray = pystray.Icon('PostPilot', _create_tray_icon(), 'PostPilot', menu)
    _tray.run()


def _wait_for_flask(timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(FLASK_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def _bootstrap():
    os.makedirs('posts/images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('cookies', exist_ok=True)
    threading.Thread(target=scheduler_loop, daemon=True).start()
    _register_startup()


def _register_startup():
    """Add this app to Windows startup via registry (no admin needed)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run',
            0, winreg.KEY_SET_VALUE
        )
        # Use pythonw.exe so no console window appears on startup
        pythonw = os.path.join(os.path.dirname(os.sys.executable), 'pythonw.exe')
        script  = os.path.abspath(__file__)
        winreg.SetValueEx(key, 'PostPilot', 0, winreg.REG_SZ, f'"{pythonw}" "{script}"')
        winreg.CloseKey(key)
    except Exception as e:
        print(f'Startup registration failed: {e}')


_bootstrap()

if __name__ == '__main__':
    # Single-instance check
    lock_sock = _acquire_instance_lock()
    if lock_sock is None:
        _focus_existing_instance()
        os._exit(0)

    # Listen for focus requests from future instances
    threading.Thread(target=_listen_for_focus, args=(lock_sock,), daemon=True).start()

    # Start Flask in background thread
    threading.Thread(
        target=lambda: app.run(debug=False, port=5110, use_reloader=False),
        daemon=True
    ).start()

    if not _wait_for_flask():
        print('ERROR: Flask did not start in time.')
    else:
        threading.Thread(target=_start_tray, daemon=True).start()

        _window = webview.create_window(
            'PostPilot', FLASK_URL,
            width=510,
        height=630,
            resizable=False, on_top=False
        )
        _window.events.closing += _on_closing
        webview.start(icon='icon.png')
