from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import requests
import json
import os
import time
import threading
from datetime import datetime
import psutil
import random

app = Flask(__name__)

HISTORY_FILE = 'posts/history.json'
SCHEDULES_FILE = 'posts/schedules.json'
CONFIG_FILE = 'posts/config.json'
SHEET_URL = 'https://script.google.com/macros/s/AKfycbxYnXuF5hMMZNE9QgWz-uwxMGYkhSsvN9rOh-c-OzuToqI9em9_CgqGS81UqxQEwHJ5mw/exec'  # Replace with your Apps Script URL

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
            part2 = "Insider"
        
        # open template
        img = Image.open("template.png").convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # fonts
        title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 110)
        value_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 43)
        url_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
        
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

@app.route('/ali.png')
def serve_ali_image():
    return send_from_directory('.', 'ali.png')

@app.route('/template.png')
def serve_template_image():
    return send_from_directory('.', 'template.png')

@app.route('/history')
def get_history():
    return jsonify(load_json(HISTORY_FILE))

@app.route('/config', methods=['POST'])
def save_config():
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
        cookie_file = f'cookies/{platform}.pkl'
        status = 'logged_in' if os.path.exists(cookie_file) else 'not_logged_in'
        accounts.append({
            'platform': platform,
            'status': status,
            'cookie_file': cookie_file
        })
    
    return jsonify(accounts)

@app.route('/test-browser')
def test_browser():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
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
    
    cookie_file = f'cookies/{platform}.pkl'
    if not os.path.exists(cookie_file):
        return jsonify({'error': 'No cookies found for this platform'}), 400
    
    try:
        threading.Thread(target=test_platform_cookies, args=(platform,), daemon=True).start()
        return jsonify({'status': 'opening test browser'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def test_platform_cookies(platform):
    try:
        import pickle  # Add missing import
        cookie_file = f'cookies/{platform}.pkl'
        
        # Load cookies
        with open(cookie_file, 'rb') as f:
            cookies = pickle.load(f)
        
        print(f"Testing {platform} with {len(cookies)} cookies...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
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
        
        with sync_playwright() as p:
            print(f"Launching browser for {platform}...")
            browser = p.chromium.launch(headless=False)
            
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
                import pickle
                cookie_path = f'cookies/{platform}.pkl'
                with open(cookie_path, 'wb') as f:
                    pickle.dump(cookies, f)
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
        post_to_platform(platform, image_path, website, da, dr, traffic)
    
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

  

def post_to_platform(platform, image_path, website, da, dr, traffic):
    caption = f"Guest Post Available on {website}\n\nDA: {da} | DR: {dr} | Traffic: {traffic}\n\n#guestpost #seo #backlinks"
    
    # Check if cookies exist
    cookie_file = f'cookies/{platform}.pkl'
    if not os.path.exists(cookie_file):
        print(f"No cookies found for {platform}. Please login first.")
        return
    
    # Check if image exists
    has_media = os.path.exists(image_path) if image_path else False
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=False,
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
            
            # Load cookies
            import pickle
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            context.add_cookies(cookies)
            
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Platform-specific automation using real selectors from JS files
            if platform == 'linkedin':
                page.goto('https://www.linkedin.com/feed/')
                page.wait_for_timeout(3000)
                
                # Click "Start a post" button
                page.click('button[aria-label="Start a post"]')
                page.wait_for_timeout(2000)
                
                # Enter text in editor
                page.fill('div[contenteditable="true"]', caption)
                page.wait_for_timeout(1000)
                
                # Upload media if available
                if has_media:
                    page.set_input_files('input[type="file"][accept^="image"]', image_path)
                    page.wait_for_timeout(2000)
                
                # Click Post button
                page.click('button.share-actions__primary-action')
                page.wait_for_timeout(3000)
                
            elif platform == 'facebook':
                page.goto('https://www.facebook.com/')
                page.wait_for_timeout(5000)
                
                try:
                    # Click create post area
                    page.click('div[aria-label="Create a post"] [role="button"]', timeout=10000)
                    page.wait_for_timeout(3000)
                    
                    # Upload media first if available
                    if has_media:
                        page.set_input_files('input[type="file"][accept*="image"]', image_path)
                        page.wait_for_timeout(4000)  # Wait for image to process
                    
                    # Enter text after media upload (Facebook clears text when uploading)
                    text_selectors = [
                        'div[contenteditable="true"][role="textbox"]',
                        'div[contenteditable="true"]',
                        '[data-testid="status-attachment-mentions-input"]'
                    ]
                    
                    text_entered = False
                    for selector in text_selectors:
                        try:
                            page.fill(selector, caption)
                            text_entered = True
                            print(f"Text entered with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if not text_entered:
                        print("Could not enter text in Facebook post")
                    
                    page.wait_for_timeout(2000)
                    
                    # Try multiple post button selectors
                    post_selectors = [
                        '[aria-label="Post"][role="button"]',
                        'div[aria-label="Post"]',
                        '[data-testid="react-composer-post-button"]',
                        'button:has-text("Post")',
                        '[role="button"]:has-text("Post")'
                    ]
                    
                    posted = False
                    for selector in post_selectors:
                        try:
                            page.click(selector, timeout=5000)
                            posted = True
                            print(f"Posted with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if not posted:
                        print("Could not find Facebook post button")
                        # Try clicking any visible button with 'Post' text
                        try:
                            page.click('text=Post', timeout=3000)
                            posted = True
                            print("Posted using text selector")
                        except:
                            print("All Facebook post attempts failed")
                    
                    page.wait_for_timeout(5000)
                    
                except Exception as fb_error:
                    print(f"Facebook posting error: {fb_error}")
                
            elif platform == 'twitter':
                page.goto('https://twitter.com/home')
                page.wait_for_timeout(3000)
                
                # Enter text in composer
                page.fill('div[data-testid="tweetTextarea_0"]', caption)
                page.wait_for_timeout(1000)
                
                # Upload media if available
                if has_media:
                    page.set_input_files('input[data-testid="fileInput"]', image_path)
                    page.wait_for_timeout(2000)
                
                # Click Tweet button
                page.click('div[data-testid="tweetButton"]')
                page.wait_for_timeout(3000)
                
            elif platform == 'instagram':
                page.goto('https://www.instagram.com/')
                page.wait_for_timeout(3000)
                
                # Click New post
                page.click('svg[aria-label="New post"]')
                page.wait_for_timeout(2000)
                
                # Click Post option
                page.click('svg[aria-label="Post"]')
                page.wait_for_timeout(2000)
                
                # Upload media (required for Instagram)
                if has_media:
                    page.set_input_files('input[type="file"][accept*="image"]', image_path)
                    page.wait_for_timeout(3000)
                    
                    # Click Next buttons
                    page.click('button:has-text("Next")')
                    page.wait_for_timeout(2000)
                    page.click('button:has-text("Next")')
                    page.wait_for_timeout(2000)
                    
                    # Enter caption
                    page.fill('div[aria-label="Write a caption..."]', caption)
                    page.wait_for_timeout(1000)
                    
                    # Click Share
                    page.click('button:has-text("Share")')
                    page.wait_for_timeout(3000)
                else:
                    print(f"No media found for Instagram - media is required")
                    return
            
            print(f"Posted to {platform} successfully!")
            page.wait_for_timeout(5000)
                
        except Exception as e:
            print(f"Error posting to {platform}: {e}")
        finally:
            try:
                browser.close()
            except:
                pass

def check_missed_schedules():
    schedules = load_json(SCHEDULES_FILE)
    current_time = datetime.now()
    today = current_time.strftime('%Y-%m-%d')
    
    # Load last run date
    last_run_file = 'posts/last_run.json'
    last_run_data = load_json(last_run_file)
    last_run_date = last_run_data.get('date', today)
    
    # If app was closed and restarted on same day, check missed schedules
    if last_run_date == today:
        current_minutes = current_time.hour * 60 + current_time.minute
        
        for schedule in schedules:
            schedule_time = schedule['time']
            schedule_hour, schedule_minute = map(int, schedule_time.split(':'))
            schedule_minutes = schedule_hour * 60 + schedule_minute
            
            # If schedule time has passed today, execute it
            if schedule_minutes < current_minutes:
                print(f"Running missed schedule: {schedule['name']} at {schedule_time}")
                fetch_and_generate()
                time.sleep(5)  # Small delay between missed posts
    
    # Update last run date
    save_json(last_run_file, {'date': today})

def scheduler_loop():
    # Check for missed schedules on startup
    check_missed_schedules()
    
    while True:
        schedules = load_json(SCHEDULES_FILE)
        current_time = datetime.now().strftime('%H:%M')
        
        for schedule in schedules:
            if schedule['time'] == current_time:
                fetch_and_generate()
                time.sleep(60)  # Prevent duplicate posts in same minute
                break
        
        time.sleep(30)
        
    browser.close()
    

# Start scheduler in background
threading.Thread(target=scheduler_loop, daemon=True).start()

if __name__ == '__main__':
    os.makedirs('posts/images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('cookies', exist_ok=True)
    
    # Run without auto-reload to prevent browser interruption
    app.run(debug=True, port=5000, use_reloader=False)
