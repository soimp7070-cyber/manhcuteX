# coding: utf-8
import json
import time
import cloudscraper
import itertools
import json
import os
import random
import re
import sys
import time
import traceback
from urllib.parse import urlparse
import requests
import requests.exceptions
from rich.box import DOUBLE, HEAVY, HEAVY_EDGE, ROUNDED
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.style import Style
from rich.table import Table
from rich.text import Text
import pyotp  # Thư viện hỗ trợ 2FA
import cloudscraper  # Thêm thư viện cloudscraper

# --- Configuration & Setup ---

# BẬT MÀU SẮC TRỞ LẠI VÀ THIẾT LẬP MÀU CHỦ ĐẠO
console = Console(force_terminal=True, color_system="truecolor") 
# Tắt cảnh báo requests
requests.packages.urllib3.disable_warnings() 

# Hằng số
LOCK_TIME_SECONDS = 600 # 10 phút tạm ngưng khi tài khoản IG bị block/login required

# File paths
AUTHORIZATION_FILE = "Authorization.txt"
LOGIN_INFO_FILE = "login_IG.json" 
USER_AGENT_FILE = "user_agent.txt" 
CONFIG_FILE = "config.json" # <--- FILE CẤU HÌNH MỚI
TWO_FA_KEYS_FILE = "2fa_keys.json" # File lưu key 2FA cho các tài khoản

# =========================================================================
# 📢 CẤU HÌNH: THÔNG BÁO TELEGRAM MỚI (CHỈ CẦN CHAT ID CỦA NGƯỜI DÙNG, KHÔNG LƯU FILE)
# =========================================================================
# ⚠️ CỐ ĐỊNH TOKEN CỦA BOT CHỦ TOOL TẠI ĐÂY!
# (Người dùng không cần biết token này, chỉ cần biết Chat ID)
GLOBAL_TELEGRAM_TOKEN = "8230870404:AAGri9A07HH-6nOA91j-kCnuFUW-SEEU64U" 

# GLOBAL_TELEGRAM_CHAT_ID sẽ được lưu trong bộ nhớ (không lưu ra file)
GLOBAL_TELEGRAM_CHAT_ID = None
# =========================================================================

# GoLike API Endpoints
API_BASE = "https://gateway.golike.net/api"
INSTAGRAM_ACCOUNT_URL = f"{API_BASE}/instagram-account"
GET_JOBS_URL = f"{API_BASE}/advertising/publishers/instagram/jobs"
COMPLETE_JOBS_URL = f"{API_BASE}/advertising/publishers/instagram/complete-jobs"
REPORT_URL = f"{API_BASE}/report/send"
SKIP_JOBS_URL = f"{API_BASE}/advertising/publishers/instagram/skip-jobs"
VERIFY_ACCOUNT_URL = f"{API_BASE}/instagram-account/verify-account"  # API thêm tài khoản vào Golike

# User-Agent mặc định và toàn cục
DEFAULT_USER_AGENT = 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
# Biến này sẽ được cập nhật sau khi người dùng nhập
GLOBAL_USER_AGENT = DEFAULT_USER_AGENT 

# ==================== PROXY CONFIGURATION ====================

# File paths cho proxy
PROXY_MAPPING_FILE = "proxy_mapping.json"
PROXY_LIST_FILE = "proxy_list.txt"

# Timeout cho việc check proxy (giây)
PROXY_CHECK_TIMEOUT = 10
PROXY_CHECK_RETRIES = 2

# Cấu trúc dữ liệu cho mỗi tài khoản Instagram
# [{"id": 1234, "username": "user_a", "cookies": "ig_cookies", "fail_count": 0, "success_count": 0, "is_locked": False, "lock_until": 0, "user_agent": "..."}, ...]
ACCOUNTS_LIST = [] 

# ==================== THÊM HÀM XỬ LÝ 2FA ====================

def load_2fa_keys():
    """Tải danh sách key 2FA từ file."""
    try:
        if os.path.exists(TWO_FA_KEYS_FILE):
            with open(TWO_FA_KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
    return {}

def save_2fa_keys(keys_dict):
    """Lưu danh sách key 2FA vào file."""
    try:
        with open(TWO_FA_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys_dict, f, indent=4, ensure_ascii=False)
        return True
    except IOError:
        return False

def get_2fa_code(key):
    """Tạo mã 2FA từ key (TOTP)."""
    try:
        # Kiểm tra xem key có phải là base32 không
        if not re.match(r'^[A-Z2-7]+=*$', key.upper()):
            # Nếu không phải base32, thử xem có phải là secret key không
            totp = pyotp.TOTP(key)
        else:
            totp = pyotp.TOTP(key)
        return totp.now()
    except Exception as e:
        console.print(f"[bold red]Lỗi tạo mã 2FA: {e}[/bold red]")
        return None

def save_2fa_key_for_account(username, key):
    """Lưu key 2FA cho tài khoản."""
    keys = load_2fa_keys()
    keys[username] = key
    save_2fa_keys(keys)
    return True

def get_2fa_key_for_account(username):
    """Lấy key 2FA cho tài khoản."""
    keys = load_2fa_keys()
    return keys.get(username)

# ==================== THÊM HÀM LẤY THÔNG TIN TỪ COOKIES (TỪ addiggo.py) ====================

def get_account_info_from_cookies(cookies, user_agent=None):
    """
    Lấy thông tin tài khoản từ cookies (giống hàm get_infock trong addiggo.py).
    Trả về: (username, user_id, csrftoken) hoặc (None, None, None) nếu thất bại
    """
    if not user_agent:
        user_agent = GLOBAL_USER_AGENT
    
    headers_ig = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'cache-control': 'max-age=0',
        'dpr': '1.25',
        'priority': 'u=0, i',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-full-version-list': '"Chromium";v="136.0.7103.114", "Google Chrome";v="136.0.7103.114", "Not.A/Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-model': '"Nexus 5"',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua-platform-version': '"6.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'viewport-width': '400',
        'cookie': cookies,
    }
    
    try:
        response = requests.get('https://www.instagram.com/', headers=headers_ig, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
        # Lấy username
        match_username = re.search(r'"username":"(.*?)"', html_content)
        username = match_username.group(1) if match_username else None
        
        if not username:
            console.print("[bold red]❌ Không thể lấy username từ cookie![/bold red]")
            return None, None, None
        
        # Lấy user_id
        match_user = re.search(r'__user=(\d+)', html_content)
        user_id = match_user.group(1) if match_user else None
        
        # Lấy csrftoken từ cookies
        csrf_match = re.search(r'csrftoken=([^;]+)', cookies)
        csrftoken = csrf_match.group(1) if csrf_match else None
        
        console.print(f"[bold green]✅ Lấy thông tin thành công: {username}[/bold green]")
        return username, user_id, csrftoken
        
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Lỗi kết nối khi lấy thông tin: {e}[/bold red]")
        return None, None, None
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi không xác định khi lấy thông tin: {e}[/bold red]")
        return None, None, None

# ==================== THÊM HÀM THÊM TÀI KHOẢN VÀO GOLIKE ====================

def add_account_to_golike(username, authorization, cookies=None, proxy_dict=None):
    """
    Thêm tài khoản Instagram vào Golike (giống addiggo.py).
    Trả về True nếu thành công, False nếu thất bại.
    """
    console.print(f"[bold cyan]📤 Đang thêm {username} vào Golike...[/bold cyan]")
    
    # Tạo scraper để bypass cloudflare
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'android',
        'mobile': True
    })
    
    # THÊM: Hàm follow kênh evansnguyen.0104 - GIỐNG HOÀN TOÀN addiggo.py
    def follow_target_channel(cookies, proxy_dict=None):
        """Follow kênh evansnguyen.0104 trước khi thêm vào Golike - GIỐNG HOÀN TOÀN addiggo.py"""
        try:
            console.print(f"[bold yellow]🔗 Đang follow kênh @evansnguyen.0104...[/bold yellow]")
            
            # Tạo session
            session = requests.Session()
            if proxy_dict:
                proxies = format_proxy_for_requests(proxy_dict)
                session.proxies.update(proxies)
            
            # Thêm cookies vào session
            for cookie in cookies.split('; '):
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    session.cookies.set(name.strip(), value.strip())
            
            # Extract csrftoken từ cookies (giống addiggo.py)
            csrf_match = re.search(r'csrftoken=([^;]+)', cookies)
            csrftoken = csrf_match.group(1) if csrf_match else ''
            
            if not csrftoken:
                console.print("[bold red]❌ Không tìm thấy csrftoken trong cookie![/bold red]")
                return False
            
            # User agent GIỐNG addiggo.py
            ua = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36"
            
            # 1. Lấy thông tin từ Instagram homepage (giống hàm get_infock trong addiggo.py)
            def get_infock():
                headers_ig = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'cache-control': 'max-age=0',
                    'dpr': '1.25',
                    'priority': 'u=0, i',
                    'sec-ch-prefers-color-scheme': 'dark',
                    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                    'sec-ch-ua-full-version-list': '"Chromium";v="136.0.7103.114", "Google Chrome";v="136.0.7103.114", "Not.A/Brand";v="99.0.0.0"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-model': '"Nexus 5"',
                    'sec-ch-ua-platform': '"Android"',
                    'sec-ch-ua-platform-version': '"6.0"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': ua,
                    'viewport-width': '400',
                    'cookie': cookies,
                }
                
                try:
                    response = session.get('https://www.instagram.com/', headers=headers_ig, timeout=30)
                    html = response.text
                    
                    # Lấy các thông tin cần thiết GIỐNG addiggo.py
                    match_actor_id = re.search(r'"actorID":"(\d+)"', html)
                    actor_id = match_actor_id.group(1) if match_actor_id else None
                    
                    match_d = re.search(r'__d=([a-zA-Z0-9_]+)', html)
                    d_value = match_d.group(1) if match_d else None
                    
                    match_user = re.search(r'__user=(\d+)', html)
                    user_id = match_user.group(1) if match_user else None
                    
                    match_a = re.search(r'__a=(\d+)', html)
                    a_value = match_a.group(1) if match_a else None
                    
                    match_rev = re.search(r'data-btmanifest="([^"]+)"', html)
                    value = match_rev.group(1) if match_rev else None
                    
                    match_r = re.search(r'"__spin_r":(\d+)', html)
                    spin_r = match_r.group(1) if match_r else None
                    
                    match_b = re.search(r'"__spin_b":"([^"]+)"', html)
                    spin_b = match_b.group(1) if match_b else None
                    
                    match_t = re.search(r'"__spin_t":(\d+)', html)
                    spin_t = match_t.group(1) if match_t else None
                    
                    match_token1 = re.search(r'"token"\s*:\s*"([^"]+)"', html)
                    token1 = match_token1.group(1) if match_token1 else None
                    
                    if not all([actor_id, d_value, user_id, a_value, value, token1]):
                        console.print("[bold red]❌ Thiếu thông tin cần thiết từ Instagram![/bold red]")
                        return None, None, None, None, None, None, None, None, None
                    
                    return actor_id, d_value, user_id, a_value, value, spin_r, spin_b, spin_t, token1
                    
                except Exception as e:
                    console.print(f"[bold red]❌ Lỗi khi lấy thông tin Instagram: {str(e)}[/bold red]")
                    return None, None, None, None, None, None, None, None, None
            
            # 2. Lấy thông tin cần thiết
            result = get_infock()
            if result[0] is None:  # actor_id là None
                return False
            
            actor_id, d_value, user_id, a_value, value, spin_r, spin_b, spin_t, token1 = result
            clean_value = value.split('_')[0] if value else ""
            
            # 3. Lấy profile_id của target (giống hàm get_uidfl trong addiggo.py)
            target_url = "https://www.instagram.com/evansnguyen.0104/"
            
            def get_uidfl(url):
                headers_ig = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'cache-control': 'max-age=0',
                    'dpr': '1.25',
                    'priority': 'u=0, i',
                    'sec-ch-prefers-color-scheme': 'dark',
                    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                    'sec-ch-ua-full-version-list': '"Chromium";v="136.0.7103.114", "Google Chrome";v="136.0.7103.114", "Not.A/Brand";v="99.0.0.0"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-model': '"Nexus 5"',
                    'sec-ch-ua-platform': '"Android"',
                    'sec-ch-ua-platform-version': '"6.0"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': ua,
                    'viewport-width': '400',
                    'cookie': cookies,
                }
                
                try:
                    response = session.get(url, headers=headers_ig, timeout=30)
                    html = response.text
                    match_profile = re.search(r'"profile_id":"(\d+)"', html)
                    profile_id = match_profile.group(1) if match_profile else None
                    return profile_id
                except:
                    return None
            
            target_uid = get_uidfl(target_url)
            if not target_uid:
                console.print("[bold red]❌ Không thể lấy profile_id của target![/bold red]")
                return False
            
            console.print(f"[yellow]Đã tìm thấy target_uid: {target_uid}[/yellow]")
            
            # 4. Thực hiện follow (giống hàm follow_uid trong addiggo.py)
            def follow_uid(url, uid_fl):
                headers_follow = {
                    'accept': '*/*',
                    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://www.instagram.com',
                    'priority': 'u=1, i',
                    'referer': url,
                    'sec-ch-prefers-color-scheme': 'dark',
                    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                    'sec-ch-ua-full-version-list': '"Chromium";v="136.0.7103.114", "Google Chrome";v="136.0.7103.114", "Not.A/Brand";v="99.0.0.0"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-model': '"Nexus 5"',
                    'sec-ch-ua-platform': '"Android"',
                    'sec-ch-ua-platform-version': '"6.0"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': ua,
                    'x-asbd-id': '359341',
                    'x-bloks-version-id': '446750d9733aca29094b1f0c8494a768d5742385af7ba20c3e67c9afb91391d8',
                    'x-csrftoken': csrftoken,
                    'x-fb-friendly-name': 'usePolarisFollowMutation',
                    'x-fb-lsd': 'jbkYL7qHmocJngjmnvJA0L',
                    'x-ig-app-id': '936619743392459',
                    'x-root-field-name': 'xdt_create_friendship',
                    'cookie': cookies,
                }
                
                data = {
                    'av': actor_id,
                    '__d': d_value,
                    '__user': user_id,
                    '__a': a_value,
                    '__req': '15',
                    '__hs': '20226.HYP:instagram_web_pkg.2.1...1',
                    'dpr': '3',
                    '__ccg': 'EXCELLENT',
                    '__rev': clean_value,
                    '__comet_req': '7',
                    'fb_dtsg': token1,
                    'jazoest': '26429',
                    '__spin_r': spin_r,
                    '__spin_b': spin_b,
                    '__spin_t': spin_t,
                    '__crn': 'comet.igweb.PolarisProfilePostsTabRoute',
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'usePolarisFollowMutation',
                    'variables': f'{{"target_user_id":"{uid_fl}","container_module":"profile","nav_chain":"PolarisProfilePostsTabRoot:profilePage:1:via_cold_start"}}',
                    'server_timestamps': 'true',
                    'doc_id': '9663809173698092',
                }
                
                try:
                    response = session.post('https://www.instagram.com/graphql/query', headers=headers_follow, data=data, timeout=30)
                    response_json = response.json()
                    friendship_status = response_json['data']['xdt_create_friendship']['friendship_status']
                    
                    following = friendship_status['following']
                    outgoing_request = friendship_status['outgoing_request']
                    
                    if following and not outgoing_request:
                        return 1, "Thành Công"
                    elif not following and outgoing_request:
                        return 2, "Yêu Cầu"
                    else:
                        return 3, "Không Xác Định"
                except Exception as e:
                    return 3, f"Lỗi: {str(e)}"
            
            # 5. Thực hiện follow
            console.print("[yellow]⏳ Đang thực hiện follow...[/yellow]")
            follow_result, status = follow_uid(target_url, target_uid)
            
            if follow_result in [1, 2]:
                console.print(f"[bold green]✅ Follow @evansnguyen.0104: {status}[/bold green]")
                return True
            else:
                console.print(f"[bold red]❌ Follow thất bại: {status}[/bold red]")
                return False
            
        except Exception as e:
            console.print(f"[bold red]❌ Lỗi trong quá trình follow: {str(e)}[/bold red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False
    
    # BƯỚC 1: Follow kênh evansnguyen.0104 trước
    if cookies:
        console.print(f"[yellow]⏳ Đang chuẩn bị follow kênh...[/yellow]")
        time.sleep(2)  # Delay trước khi follow
        
        follow_success = follow_target_channel(cookies, proxy_dict)
        
        if follow_success:
            console.print(f"[green]✅ Đã follow kênh thành công![/green]")
        else:
            console.print(f"[yellow]⚠️ Không thể follow kênh, nhưng vẫn thử thêm vào Golike...[/yellow]")
        
        # Delay sau khi follow trước khi thêm vào Golike
        console.print(f"[yellow]⏳ Chờ 5 giây trước khi thêm vào Golike...[/yellow]")
        time.sleep(5)
    else:
        console.print(f"[yellow]⚠️ Không có cookies để follow kênh[/yellow]")
    
    # Headers cho Golike API
    headers = {
        'accept-language': 'vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6',
        'authorization': authorization,
        'content-type': 'application/json;charset=utf-8',
        'origin': 'https://app.golike.net',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        't': 'VFZSak1FNTZWVFJOUkdkNFRrRTlQUT09',
    }
    
    # Dữ liệu gửi lên
    json_data = {
        'object_id': username,
    }
    
    try:
        # Cấu hình proxy nếu có
        if proxy_dict:
            proxies = {
                'http': f"{proxy_dict['protocol']}://{proxy_dict['host']}:{proxy_dict['port']}",
                'https': f"{proxy_dict['protocol']}://{proxy_dict['host']}:{proxy_dict['port']}"
            }
            if proxy_dict.get('username') and proxy_dict.get('password'):
                auth_str = f"{proxy_dict['username']}:{proxy_dict['password']}@"
                proxies = {
                    'http': f"{proxy_dict['protocol']}://{auth_str}{proxy_dict['host']}:{proxy_dict['port']}",
                    'https': f"{proxy_dict['protocol']}://{auth_str}{proxy_dict['host']}:{proxy_dict['port']}"
                }
            scraper.proxies = proxies
        
        console.print(f"[yellow]⏳ Đang gửi request thêm tài khoản vào Golike...[/yellow]")
        
        response = scraper.post(VERIFY_ACCOUNT_URL, headers=headers, json=json_data, timeout=30)
        
        if response.status_code == 200:
            console.print(f"[bold green]✅ {username} đã được thêm thành công vào Golike![/bold green]")
            return True
        elif response.status_code == 429:
            # Xử lý rate limiting
            console.print(f"[bold yellow]⚠️ Bị rate limit (429), chờ 15 giây rồi thử lại...[/bold yellow]")
            time.sleep(15)
            
            # Thử lại lần 2
            console.print(f"[yellow]⏳ Thử lại lần 2...[/yellow]")
            response = scraper.post(VERIFY_ACCOUNT_URL, headers=headers, json=json_data, timeout=30)
            
            if response.status_code == 200:
                console.print(f"[bold green]✅ {username} đã được thêm thành công vào Golike! (lần 2)[/bold green]")
                return True
            else:
                console.print(f"[bold red]❌ Lỗi khi thêm {username} vào Golike - Status: {response.status_code} (lần 2)[/bold red]")
                try:
                    error_data = response.json()
                    console.print(f"[bold red]Chi tiết lỗi: {error_data}[/bold red]")
                except:
                    console.print(f"[bold red]Response: {response.text[:100]}...[/bold red]")
                return False
        else:
            console.print(f"[bold red]❌ Lỗi khi thêm {username} vào Golike - Status: {response.status_code}[/bold red]")
            try:
                error_data = response.json()
                console.print(f"[bold red]Chi tiết lỗi: {error_data}[/bold red]")
            except:
                console.print(f"[bold red]Response: {response.text[:100]}...[/bold red]")
            return False
            
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi kết nối Golike: {e}[/bold red]")
        return False

# ==================== PROXY VALIDATION ====================

def parse_proxy_string(proxy_str):
    """
    Parse chuỗi proxy thành dictionary.
    Hỗ trợ format:
    - ip:port
    - ip:port:user:pass
    - protocol://ip:port
    - protocol://user:pass@ip:port
    
    Returns:
        dict: {
            'protocol': 'http/https/socks4/socks5',
            'host': 'ip',
            'port': 'port',
            'username': 'user' (optional),
            'password': 'pass' (optional),
            'raw': 'original string'
        }
        None nếu invalid
    """
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None
    
    result = {
        'protocol': 'http',  # Default
        'host': None,
        'port': None,
        'username': None,
        'password': None,
        'raw': proxy_str
    }
    
    # Pattern 1: protocol://user:pass@ip:port
    pattern1 = r'^(https?|socks4|socks5)://([^:]+):([^@]+)@([^:]+):(\d+)$'
    match = re.match(pattern1, proxy_str, re.IGNORECASE)
    if match:
        result['protocol'] = match.group(1).lower()
        result['username'] = match.group(2)
        result['password'] = match.group(3)
        result['host'] = match.group(4)
        result['port'] = match.group(5)
        return result
    
    # Pattern 2: protocol://ip:port
    pattern2 = r'^(https?|socks4|socks5)://([^:]+):(\d+)$'
    match = re.match(pattern2, proxy_str, re.IGNORECASE)
    if match:
        result['protocol'] = match.group(1).lower()
        result['host'] = match.group(2)
        result['port'] = match.group(3)
        return result
    
    # Pattern 3: ip:port:user:pass
    parts = proxy_str.split(':')
    if len(parts) == 4:
        result['host'] = parts[0]
        result['port'] = parts[1]
        result['username'] = parts[2]
        result['password'] = parts[3]
        return result
    
    # Pattern 4: ip:port
    elif len(parts) == 2:
        result['host'] = parts[0]
        result['port'] = parts[1]
        return result
    
    # Pattern 5: user:pass@ip:port
    elif len(parts) == 3 and '@' in parts[1]:
        auth_host = parts[1].split('@')
        if len(auth_host) == 2:
            result['username'] = parts[0]
            result['password'] = auth_host[0]
            result['host'] = auth_host[1]
            result['port'] = parts[2]
            return result
    
    return None

def validate_ip(ip):
    """Validate IPv4 hoặc IPv6"""
    # IPv4
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    # IPv6 (simplified check)
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
    if re.match(ipv6_pattern, ip):
        return True
    
    # Domain name
    domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?(\.[a-zA-Z]{2,})+$'
    if re.match(domain_pattern, ip):
        return True
    
    return False

def validate_proxy(proxy_dict):
    """
    Validate proxy dictionary
    Returns: (bool, error_message)
    """
    if not proxy_dict:
        return False, "Proxy dictionary is None"
    
    # Check host
    if not proxy_dict.get('host'):
        return False, "Missing host"
    
    if not validate_ip(proxy_dict['host']):
        return False, f"Invalid IP/domain: {proxy_dict['host']}"
    
    # Check port
    try:
        port = int(proxy_dict['port'])
        if not (1 <= port <= 65535):
            return False, f"Port out of range: {port}"
    except (ValueError, TypeError):
        return False, f"Invalid port: {proxy_dict.get('port')}"
    
    # Check protocol
    valid_protocols = ['http', 'https', 'socks4', 'socks5']
    if proxy_dict['protocol'].lower() not in valid_protocols:
        return False, f"Invalid protocol: {proxy_dict['protocol']}"
    
    return True, "Valid"

# ==================== PROXY CHECKING ====================

def format_proxy_for_requests(proxy_dict):
    """
    Format proxy dictionary thành format cho requests library
    Returns: dict cho requests.Session().proxies
    """
    protocol = proxy_dict['protocol']
    host = proxy_dict['host']
    port = proxy_dict['port']
    username = proxy_dict.get('username')
    password = proxy_dict.get('password')
    
    # Build proxy URL
    if username and password:
        proxy_url = f"{protocol}://{username}:{password}@{host}:{port}"
    else:
        proxy_url = f"{protocol}://{host}:{port}"
    
    # Requests expects http and https keys
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    return proxies

def check_proxy_live(proxy_dict, test_url="http://httpbin.org/ip", timeout=PROXY_CHECK_TIMEOUT):
    """
    Kiểm tra proxy có hoạt động không
    Returns: (bool, response_time_ms, error_message)
    """
    import time
    
    try:
        proxies = format_proxy_for_requests(proxy_dict)
        
        start_time = time.time()
        response = requests.get(
            test_url,
            proxies=proxies,
            timeout=timeout,
            verify=False  # Bỏ qua SSL verification
        )
        end_time = time.time()
        
        response_time_ms = int((end_time - start_time) * 1000)
        
        if response.status_code == 200:
            return True, response_time_ms, "OK"
        else:
            return False, response_time_ms, f"HTTP {response.status_code}"
            
    except requests.exceptions.ProxyError as e:
        return False, 0, f"Proxy Error: {str(e)[:50]}"
    except requests.exceptions.Timeout:
        return False, 0, "Timeout"
    except requests.exceptions.ConnectionError as e:
        return False, 0, f"Connection Error: {str(e)[:50]}"
    except Exception as e:
        return False, 0, f"Unknown Error: {str(e)[:50]}"

def check_proxy_with_retry(proxy_dict, retries=PROXY_CHECK_RETRIES):
    """
    Check proxy với retry logic
    Returns: (bool, best_response_time_ms, error_message)
    """
    best_time = float('inf')
    last_error = ""
    
    for attempt in range(retries):
        is_live, response_time, error_msg = check_proxy_live(proxy_dict)
        
        if is_live:
            best_time = min(best_time, response_time)
            return True, best_time, "OK"
        
        last_error = error_msg
    
    return False, 0, last_error

# ==================== PROXY STORAGE ====================

def load_proxy_mapping():
    """Tải mapping proxy từ file JSON"""
    try:
        with open(PROXY_MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_proxy_mapping(mapping):
    """Lưu mapping proxy vào file JSON"""
    try:
        with open(PROXY_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi lưu proxy mapping: {e}[/bold red]")
        return False

def get_account_proxy(username):
    """Lấy proxy đã được gán cho tài khoản"""
    mapping = load_proxy_mapping()
    return mapping.get(username, None)

def assign_proxy_to_account(username, proxy_dict):
    """Gán proxy cho tài khoản và lưu vào file"""
    mapping = load_proxy_mapping()
    mapping[username] = proxy_dict
    save_proxy_mapping(mapping)
    return True

def remove_proxy_from_account(username):
    """Xóa proxy của tài khoản"""
    mapping = load_proxy_mapping()
    if username in mapping:
        del mapping[username]
        save_proxy_mapping(mapping)
        return True
    return False

def get_proxy_for_session(username):
    """
    Lấy proxy dict format cho requests.Session
    Returns: proxies dict hoặc None
    """
    proxy_info = get_account_proxy(username)
    if not proxy_info:
        return None
    
    return format_proxy_for_requests(proxy_info)

# ==================== PROXY MANAGEMENT UI ====================

def display_proxy_list(proxy_list):
    """Hiển thị danh sách proxy dạng table"""
    if not proxy_list:
        console.print("[bold yellow]⚠️  Danh sách proxy trống[/bold yellow]")
        return
    
    table = Table(title="[bold cyan]📋 DANH SÁCH PROXY[/bold cyan]", border_style="cyan", show_lines=True)
    table.add_column("STT", justify="center", style="yellow")
    table.add_column("Protocol", justify="center", style="magenta")
    table.add_column("Host", style="white")
    table.add_column("Port", justify="center", style="green")
    table.add_column("Auth", justify="center", style="cyan")
    table.add_column("Status", justify="center")
    
    for idx, proxy_info in enumerate(proxy_list, 1):
        proxy = proxy_info['proxy']
        status = proxy_info.get('status', 'Unknown')
        response_time = proxy_info.get('response_time', 0)
        
        auth = "✓" if proxy.get('username') else "✗"
        
        if status == "OK":
            status_text = f"[bold green]✓ Live ({response_time}ms)[/bold green]"
        elif status == "Unknown":
            status_text = "[yellow]? Chưa test[/yellow]"
        else:
            status_text = f"[bold red]✗ {status}[/bold red]"
        
        table.add_row(
            str(idx),
            proxy['protocol'].upper(),
            proxy['host'],
            str(proxy['port']),
            auth,
            status_text
        )
    
    console.print(table)

def input_proxy_manually():
    """Nhập proxy thủ công từng dòng"""
    console.print("\n[bold yellow]╔══════════════════════════════════════════════════╗[/bold yellow]")
    console.print("[bold cyan]📝 NHẬP PROXY THỦ CÔNG[/bold cyan]")
    console.print("[bold white]Hỗ trợ các format:[/bold white]")
    console.print("  • ip:port")
    console.print("  • ip:port:user:pass")
    console.print("  • protocol://ip:port")
    console.print("  • protocol://user:pass@ip:port")
    console.print("\n[bold white]Nhập từng proxy, Enter để thêm tiếp, Enter trống để kết thúc.[/bold white]")
    console.print("[bold yellow]╚══════════════════════════════════════════════════╝[/bold yellow]")
    
    proxy_list = []
    
    while True:
        proxy_str = Prompt.ask(f"\n ✈ [bold cyan]Nhập proxy #{len(proxy_list)+1} (Enter trống để kết thúc)[/bold cyan]").strip()
        
        if not proxy_str:
            break
        
        # Parse proxy
        proxy_dict = parse_proxy_string(proxy_str)
        
        if not proxy_dict:
            console.print("[bold red]❌ Format proxy không hợp lệ! Thử lại.[/bold red]")
            continue
        
        # Validate
        is_valid, error_msg = validate_proxy(proxy_dict)
        if not is_valid:
            console.print(f"[bold red]❌ Proxy không hợp lệ: {error_msg}[/bold red]")
            continue
        
        proxy_list.append({'proxy': proxy_dict, 'status': 'Unknown'})
        console.print(f"[bold green]✓ Đã thêm: {proxy_dict['host']}:{proxy_dict['port']}[/bold green]")
    
    return proxy_list

def input_proxy_from_file():
    """Nhập proxy từ file txt"""
    console.print("\n[bold yellow]╔══════════════════════════════════════════════════╗[/bold yellow]")
    console.print("[bold white]📁 File cần chứa mỗi proxy trên một dòng.[/bold white]")
    console.print("[bold yellow]╚══════════════════════════════════════════════════╝[/bold yellow]")
    
    file_path = Prompt.ask(f" ✈ [bold cyan]Nhập đường dẫn file proxy[/bold cyan]", default=PROXY_LIST_FILE).strip()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            console.print("[bold red]❌ File trống![/bold red]")
            return []
        
        proxy_list = []
        invalid_count = 0
        
        console.print(f"\n[bold yellow]⏳ Đang parse {len(lines)} proxy từ file...[/bold yellow]")
        
        for line in lines:
            proxy_dict = parse_proxy_string(line)
            
            if not proxy_dict:
                invalid_count += 1
                continue
            
            is_valid, error_msg = validate_proxy(proxy_dict)
            if not is_valid:
                invalid_count += 1
                continue
            
            proxy_list.append({'proxy': proxy_dict, 'status': 'Unknown'})
        
        console.print(f"[bold green]✓ Đã parse thành công {len(proxy_list)} proxy[/bold green]")
        if invalid_count > 0:
            console.print(f"[bold yellow]⚠️  Bỏ qua {invalid_count} proxy không hợp lệ[/bold yellow]")
        
        return proxy_list
        
    except FileNotFoundError:
        console.print(f"[bold red]❌ Không tìm thấy file: {file_path}[/bold red]")
        return []
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi đọc file: {e}[/bold red]")
        return []

def batch_check_proxies(proxy_list):
    """
    Check hàng loạt proxy với progress bar
    Returns: updated proxy_list với status
    """
    if not proxy_list:
        return proxy_list
    
    console.print(f"\n[bold yellow]🔍 Bắt đầu kiểm tra {len(proxy_list)} proxy...[/bold yellow]")
    console.print(f"[bold white]⏱️  Timeout: {PROXY_CHECK_TIMEOUT}s, Retries: {PROXY_CHECK_RETRIES}[/bold white]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Checking proxies...", total=len(proxy_list))
        
        live_count = 0
        dead_count = 0
        
        for idx, proxy_info in enumerate(proxy_list):
            proxy = proxy_info['proxy']
            
            progress.update(task, description=f"[cyan]Checking {proxy['host']}:{proxy['port']}...")
            
            is_live, response_time, error_msg = check_proxy_with_retry(proxy)
            
            if is_live:
                proxy_info['status'] = "OK"
                proxy_info['response_time'] = response_time
                live_count += 1
            else:
                proxy_info['status'] = error_msg
                proxy_info['response_time'] = 0
                dead_count += 1
            
            progress.update(task, advance=1)
    
    # Summary
    summary = Text("\n")
    summary.append("╔════════════════════════════════════╗\n", style="bold yellow")
    summary.append("       📊 KẾT QUẢ KIỂM TRA           \n", style="bold cyan")
    summary.append("╠════════════════════════════════════╣\n", style="bold yellow")
    summary.append(f"  ✓ Live:  {live_count}/{len(proxy_list)}\n", style="bold green")
    summary.append(f"  ✗ Dead:  {dead_count}/{len(proxy_list)}\n", style="bold red")
    summary.append("╚════════════════════════════════════╝", style="bold yellow")
    
    console.print(summary)
    
    return proxy_list

def filter_live_proxies(proxy_list):
    """Lọc chỉ lấy proxy live"""
    return [p for p in proxy_list if p.get('status') == 'OK']

def proxy_management_menu(accounts_list):
    """
    Menu quản lý proxy cho các tài khoản
    accounts_list: danh sách tài khoản Instagram từ ACCOUNTS_LIST
    """
    
    while True:
        console.clear()
        
        # Banner
        banner = Panel(
            Text("🌐 QUẢN LÝ PROXY CHO INSTAGRAM ACCOUNTS 🌐", justify="center", style="bold cyan"),
            border_style="cyan"
        )
        console.print(banner)
        
        # Hiển thị trạng thái proxy của các acc
        mapping = load_proxy_mapping()
        
        status_table = Table(title="[bold yellow]📱 TRẠNG THÁI PROXY CÁC TÀI KHOẢN[/bold yellow]", border_style="yellow")
        status_table.add_column("Username", style="cyan")
        status_table.add_column("Proxy", style="white")
        status_table.add_column("Status", justify="center")
        
        for acc in accounts_list:
            username = acc.get('username')
            proxy_info = mapping.get(username)
            
            if proxy_info:
                proxy_str = f"{proxy_info['protocol']}://{proxy_info['host']}:{proxy_info['port']}"
                if proxy_info.get('username'):
                    proxy_str += " (Auth)"
                status = "[bold green]✓ Đã gán[/bold green]"
            else:
                proxy_str = "Không có"
                status = "[bold red]✗ Chưa gán[/bold red]"
            
            status_table.add_row(username, proxy_str, status)
        
        console.print(status_table)
        
        # Menu
        menu = Text("\n")
        menu.append(" ✈ 1: Thêm proxy từ danh sách (thủ công/file)\n", style="bold green")
        menu.append(" ✈ 2: Gán proxy cho từng tài khoản\n", style="bold cyan")
        menu.append(" ✈ 3: Gán proxy tự động (random)\n", style="bold magenta")
        menu.append(" ✈ 4: Xem chi tiết proxy các tài khoản\n", style="bold yellow")
        menu.append(" ✈ 5: Xóa proxy tất cả tài khoản\n", style="bold red")
        menu.append(" ✈ 0: Quay lại\n", style="bold white")
        
        console.print(Panel(menu, title="[bold yellow]MENU PROXY[/bold yellow]", border_style="yellow"))
        
        choice = Prompt.ask(" ✈ [bold cyan]Chọn chức năng[/bold cyan]", choices=['0','1','2','3','4','5']).strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            # Thêm proxy vào danh sách
            input_method = Prompt.ask(
                " ✈ [bold cyan]Nhập proxy từ (1: Thủ công, 2: File)[/bold cyan]",
                choices=['1', '2']
            )
            
            if input_method == '1':
                proxy_list = input_proxy_manually()
            else:
                proxy_list = input_proxy_from_file()
            
            if not proxy_list:
                console.print("[bold red]❌ Không có proxy nào được thêm![/bold red]")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            # Hỏi có check live không
            check_live = Confirm.ask(" ✈ [bold yellow]Kiểm tra proxy live trước khi sử dụng?[/bold yellow]", default=True)
            
            if check_live:
                proxy_list = batch_check_proxies(proxy_list)
                
                # Chỉ giữ lại live proxies
                filter_option = Confirm.ask(" ✈ [bold yellow]Chỉ giữ lại proxy live?[/bold yellow]", default=True)
                if filter_option:
                    original_count = len(proxy_list)
                    proxy_list = filter_live_proxies(proxy_list)
                    console.print(f"[bold green]✓ Lọc còn {len(proxy_list)}/{original_count} proxy live[/bold green]")
            
            # Hiển thị danh sách
            display_proxy_list(proxy_list)
            
            # Lưu vào file tạm để dùng cho các option khác
            try:
                with open('temp_proxy_list.json', 'w', encoding='utf-8') as f:
                    json.dump(proxy_list, f, indent=4)
                console.print("[bold green]✓ Đã lưu danh sách proxy tạm thời[/bold green]")
            except:
                pass
            
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '2':
            # Gán proxy thủ công cho từng acc
            # Load proxy list
            try:
                with open('temp_proxy_list.json', 'r', encoding='utf-8') as f:
                    proxy_list = json.load(f)
            except:
                console.print("[bold red]❌ Chưa có danh sách proxy! Vui lòng chọn option 1 trước.[/bold red]")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            if not proxy_list:
                console.print("[bold red]❌ Danh sách proxy trống![/bold red]")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            # Hiển thị proxy list
            display_proxy_list(proxy_list)
            
            for acc in accounts_list:
                username = acc.get('username')
                
                console.print(f"\n[bold cyan]📱 Tài khoản: {username}[/bold cyan]")
                
                # Check xem đã có proxy chưa
                current_proxy = get_account_proxy(username)
                if current_proxy:
                    console.print(f"[bold yellow]⚠️  Proxy hiện tại: {current_proxy['host']}:{current_proxy['port']}[/bold yellow]")
                
                assign = Confirm.ask(f" ✈ [bold yellow]Gán proxy cho {username}?[/bold yellow]", default=True)
                
                if not assign:
                    continue
                
                # Chọn proxy từ list
                while True:
                    proxy_idx = Prompt.ask(
                        f" ✈ [bold cyan]Nhập STT proxy (1-{len(proxy_list)}) hoặc 0 để bỏ qua[/bold cyan]"
                    ).strip()
                    
                    try:
                        idx = int(proxy_idx)
                        if idx == 0:
                            break
                        if 1 <= idx <= len(proxy_list):
                            selected_proxy = proxy_list[idx-1]['proxy']
                            assign_proxy_to_account(username, selected_proxy)
                            console.print(f"[bold green]✓ Đã gán proxy {selected_proxy['host']}:{selected_proxy['port']} cho {username}[/bold green]")
                            break
                        else:
                            console.print("[bold red]❌ STT không hợp lệ![/bold red]")
                    except ValueError:
                        console.print("[bold red]❌ Vui lòng nhập số![/bold red]")
            
            console.print("\n[bold green]✓ Hoàn tất gán proxy thủ công![/bold green]")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '3':
            # Gán proxy tự động (random)
            import random
            
            try:
                with open('temp_proxy_list.json', 'r', encoding='utf-8') as f:
                    proxy_list = json.load(f)
            except:
                console.print("[bold red]❌ Chưa có danh sách proxy! Vui lòng chọn option 1 trước.[/bold red]")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            # Lọc live proxies
            live_proxies = filter_live_proxies(proxy_list)
            
            if not live_proxies:
                console.print("[bold red]❌ Không có proxy live nào![/bold red]")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            console.print(f"\n[bold yellow]🎲 Gán ngẫu nhiên {len(live_proxies)} proxy cho {len(accounts_list)} tài khoản...[/bold yellow]")
            
            for acc in accounts_list:
                username = acc.get('username')
                random_proxy = random.choice(live_proxies)['proxy']
                assign_proxy_to_account(username, random_proxy)
                console.print(f"[bold green]✓ {username}: {random_proxy['host']}:{random_proxy['port']}[/bold green]")
            
            console.print("\n[bold green]✓ Hoàn tất gán proxy tự động![/bold green]")
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '4':
            # Xem chi tiết proxy
            mapping = load_proxy_mapping()
            
            if not mapping:
                console.print("[bold yellow]⚠️  Chưa có tài khoản nào được gán proxy[/bold yellow]")
                input("\nNhấn Enter để tiếp tục...")
                continue
            
            detail_table = Table(
                title="[bold cyan]🔍 CHI TIẾT PROXY CÁC TÀI KHOẢN[/bold cyan]",
                border_style="cyan",
                show_lines=True
            )
            detail_table.add_column("Username", style="bold cyan")
            detail_table.add_column("Protocol", justify="center", style="magenta")
            detail_table.add_column("Host", style="white")
            detail_table.add_column("Port", justify="center", style="green")
            detail_table.add_column("Username (Proxy)", style="yellow")
            detail_table.add_column("Password", style="yellow")
            
            for username, proxy in mapping.items():
                detail_table.add_row(
                    username,
                    proxy['protocol'].upper(),
                    proxy['host'],
                    str(proxy['port']),
                    proxy.get('username', '-'),
                    proxy.get('password', '-')
                )
            
            console.print(detail_table)
            input("\nNhấn Enter để tiếp tục...")
        
        elif choice == '5':
            # Xóa tất cả proxy
            confirm = Confirm.ask(" ✈ [bold red]⚠️  XÓA TẤT CẢ PROXY? Hành động không thể hoàn tác![/bold red]", default=False)
            
            if confirm:
                try:
                    with open(PROXY_MAPPING_FILE, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
                    console.print("[bold green]✓ Đã xóa tất cả proxy mapping![/bold green]")
                except:
                    console.print("[bold red]❌ Lỗi khi xóa![/bold red]")
            
            input("\nNhấn Enter để tiếp tục...")

# --- USER AGENT MANAGER (Tích hợp trực tiếp) ---

# File lưu mapping user-agent cho từng tài khoản
USER_AGENT_MAPPING_FILE = "user_agent_mapping.json"

def load_user_agent_mapping():
    """Tải mapping user-agent từ file JSON."""
    if os.path.exists(USER_AGENT_MAPPING_FILE):
        try:
            with open(USER_AGENT_MAPPING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_user_agent_mapping(mapping: dict):
    """Lưu mapping user-agent vào file JSON."""
    try:
        with open(USER_AGENT_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=4, ensure_ascii=False)
        return True
    except IOError:
        return False

def assign_user_agent(username: str, user_agents: list):
    """
    Gán ngẫu nhiên một User-Agent từ danh sách cho tài khoản.
    Lưu vào file mapping.
    """
    if not user_agents:
        return DEFAULT_USER_AGENT
    
    mapping = load_user_agent_mapping()
    
    # Nếu tài khoản đã có User-Agent, trả về luôn
    if username in mapping:
        return mapping[username]
    
    # Gán ngẫu nhiên User-Agent mới
    selected_ua = random.choice(user_agents)
    mapping[username] = selected_ua
    save_user_agent_mapping(mapping)
    
    return selected_ua

def get_account_user_agent(username: str):
    """
    Lấy User-Agent đã được gán cho tài khoản.
    Trả về None nếu chưa có.
    """
    mapping = load_user_agent_mapping()
    return mapping.get(username, None)

# --- KẾT THÚC USER AGENT MANAGER ---
# IG Headers cơ bản cho đăng nhập
IG_LOGIN_HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.instagram.com',
    'Referer': 'https://www.instagram.com/accounts/login/',
    'User-Agent': GLOBAL_USER_AGENT, 
    'X-Csrftoken': 'missing',
    'X-Instagram-Ajax': '1007802778',
    'X-Ig-App-Id': '936619743392459',
}
IG_LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'

# --- Utility Functions ---

def trim_title_for_panel(title: str, max_width: int = 60) -> str:
    """Cắt bớt tiêu đề nếu nó quá dài để tránh lỗi tràn Panel trên một số terminal."""
    if len(title) > max_width:
        return title[:max_width-3] + "..."
    return title

def safe_dict_check(data, context="API"):
    """
    Kiểm tra an toàn. Đảm bảo dữ liệu là dictionary. 
    Nếu không phải, trả về một dictionary lỗi để ngăn chặn crash FATAL ERROR: 'str' object has no attribute 'get'.
    """
    if not data:
         error_message = f"Critical Error: {context} returned empty data. Returning 500."
         return {"status": 500, "message": error_message, "critical_safe_check_fail": True}
         
    if not isinstance(data, dict):
        error_message = f"Critical Error: {context} returned type {type(data)} instead of dict. Raw data: {str(data)[:50]}"
        return {"status": 500, "message": error_message, "critical_safe_check_fail": True}
    return data

def get_cookie_file_path(username: str):
    """Trả về đường dẫn file cookies theo username."""
    return f"cookies_{username}.txt"

def clear_screen():
    """Xóa màn hình Termux/CMD/PowerShell. Tương thích đa nền tảng."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_base_headers(authorization: str = None):
    """Trả về headers chuẩn cho API GoLike. Đã cập nhật User-Agent."""
    headers = {
        'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://app.golike.net/',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': "Windows",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'T': 'VFZSak1FMTZZM3BOZWtFd1RtYzlQUT09',
        'User-Agent': GLOBAL_USER_AGENT, 
        'Content-Type': 'application/json;charset=utf-8'
    }
    if authorization:
        headers['Authorization'] = authorization
    return headers

def safe_file_rw(file_path: str, mode: str, content: any = None): # Cập nhật type hint cho content
    """Đọc/ghi/xóa/ghi JSON/đọc JSON file an toàn."""
    try:
        if mode == 'r':
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        elif mode == 'w' and content is not None:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        elif mode == 'd':
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        elif mode == 'wj' and content is not None:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
            return True
        elif mode == 'rj':
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    except IOError as e:
        console.print(f"❌ [bold red]Lỗi thao tác file {file_path}: {e}[/bold red]")
        # Không thoát chương trình, chỉ dừng thao tác file
        return None
    except json.JSONDecodeError:
        console.print(f"❌ [bold red]Lỗi đọc file JSON {file_path}.[/bold red]")
        return None
    return False

# --- CÁC HÀM CẤU HÌNH MỚI ---

DEFAULT_CONFIG = {
    "delay": 5,
    "lannhan_lan2": True,
    "doiacc_fail_limit": 5,
    "job_success_limit": 10,
    "job_ratio": "1,1", # Like,Follow
    "chedo_job": 12, # 1: Follow, 2: Like, 12: All
    "ai_autobot": True, # Thêm cấu hình AI AutoBot
    "scroll_duration": 10 # Thời gian lướt cuộn sau mỗi job
}

def load_config():
    """Tải cấu hình từ file config.json."""
    config = safe_file_rw(CONFIG_FILE, 'rj')
    if config:
        # Hợp nhất với cấu hình mặc định để đảm bảo không bị thiếu key mới
        return {**DEFAULT_CONFIG, **config}
    return None

def save_config(settings: dict):
    """Lưu cấu hình hiện tại vào file config.json."""
    return safe_file_rw(CONFIG_FILE, 'wj', settings)

# --------------------------

# --- HÀM get_real_ip_info ĐÃ CẬP NHẬT THEO YÊU CẦU ---
def get_real_ip_info():
    """
    Lấy IP công cộng và thông tin địa lý chi tiết (Quốc gia, Tỉnh/Thành phố) 
    với cơ chế dự phòng và gọi API ngẫu nhiên.
    """
    
    # Danh sách các API dịch vụ IP, với các hàm xử lý dữ liệu tương ứng
    # Hàm xử lý: lambda data -> dict {"ip": str, "location": str}
    api_services = [
        # API 1: ip-api.com
        {
            "url": 'http://ip-api.com/json', 
            "handler": lambda data: {
                "ip": data.get('query', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('regionName', 'N/A')}, {data.get('country', 'N/A')}"
            },
            "success_key": 'status',
            "success_value": 'success'
        },
        # API 2: ipwhois.app/json
        {
            "url": 'https://ipwhois.app/json',
            "handler": lambda data: {
                "ip": data.get('ip', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('region', 'N/A')}, {data.get('country', 'N/A')}"
            },
            "success_key": 'success',
            "success_value": True
        },
        # API 3: ipinfo.io/json
        {
            "url": 'https://ipinfo.io/json', 
            "handler": lambda data: {
                "ip": data.get('ip', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('region', 'N/A')}, {data.get('country', 'N/A')}"
            },
            "success_key": 'ip', # Kiểm tra sự tồn tại của key 'ip'
            "success_value": lambda v: v is not None # Logic kiểm tra giá trị
        },
        # API 4: freegeoip.app/json/
        {
            "url": 'https://freegeoip.app/json/', 
            "handler": lambda data: {
                "ip": data.get('ip', 'N/A'),
                "location": f"{data.get('city', 'N/A')}, {data.get('region_name', 'N/A')}, {data.get('country_name', 'N/A')}"
            },
            "success_key": 'ip',
            "success_value": lambda v: v is not None
        }
    ]
    
    # Xáo trộn danh sách API để gọi ngẫu nhiên
    random.shuffle(api_services)
    
    for api in api_services:
        try:
            response = requests.get(api['url'], timeout=5)
            response.raise_for_status() # Lỗi HTTP sẽ ném exception
            data = response.json()
            
            is_success = False
            
            # Kiểm tra trạng thái thành công
            if api['success_key'] in data:
                expected_value = api['success_value']
                actual_value = data[api['success_key']]
                
                if callable(expected_value):
                    is_success = expected_value(actual_value)
                else:
                    is_success = (actual_value == expected_value)
            
            if is_success:
                return api['handler'](data)
                
        except requests.exceptions.RequestException:
            # Bỏ qua, thử API tiếp theo
            continue
        except json.JSONDecodeError:
            # Bỏ qua, thử API tiếp theo
            continue 

    # Trả về mặc định nếu tất cả API đều thất bại
    return {"ip": "N/A", "location": "Không thể lấy vị trí"}
# --- KẾT THÚC HÀM get_real_ip_info ĐÃ CẬP NHẬT ---

def create_job_cycler(ratio_str: str, lam: list):
    """
    Tạo một iterator chu kỳ các loại job dựa trên tỉ lệ và lựa chọn.
    ratio_str: "1,2" (Like,Follow)
    lam: ["like", "follow"]
    """
    if not lam:
        return itertools.cycle([])
        
    try:
        parts = [int(p.strip()) for p in ratio_str.split(',') if p.strip().isdigit()]
        if len(parts) != 2:
            raise ValueError("Invalid ratio format")
            
        # parts[0] là tỉ lệ Like, parts[1] là tỉ lệ Follow
        ratio_like, ratio_follow = parts
        
    except ValueError:
        # Mặc định 1:1 nếu nhập sai
        ratio_like, ratio_follow = 1, 1

    jobs = []
    if "like" in lam and ratio_like > 0:
        jobs.extend(["like"] * ratio_like)
    if "follow" in lam and ratio_follow > 0:
        jobs.extend(["follow"] * ratio_follow)
        
    if not jobs:
        return itertools.cycle([])

    return itertools.cycle(jobs)

# --- AI AUTOBOT FUNCTIONS ---

def ai_autobot_scroll_and_browse(username: str, cookies: str, scroll_duration: int = 10):
    """
    AI AutoBot: Mô phỏng hành vi người dùng thực tế bằng cách lướt và cuộn trang
    để tránh bị Instagram phát hiện là bot.
    """
    console.print(f"🤖 [bold cyan]AI AutoBot đang hoạt động cho {username}...[/bold cyan]")
    
    # Lấy proxy cho tài khoản
    proxy_dict = get_account_proxy(username)
    proxies = format_proxy_for_requests(proxy_dict) if proxy_dict else None
    
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)
    
    # Thêm cookies vào session
    for cookie in cookies.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            session.cookies.set(name.strip(), value.strip())
    
    try:
        # 1. Truy cập trang chủ Instagram
        console.print("   📱 Đang truy cập trang chủ Instagram...")
        headers = {
            'User-Agent': GLOBAL_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        response = session.get('https://www.instagram.com/', headers=headers, timeout=10)
        if response.status_code != 200:
            console.print(f"   ⚠️ [bold yellow]Không thể truy cập trang chủ (HTTP {response.status_code})[/bold yellow]")
            return False
        
        # 2. Lấy thông tin feed
        console.print("   🔄 Đang tải feed...")
        feed_headers = headers.copy()
        feed_headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'X-CSRFToken': session.cookies.get('csrftoken', ''),
            'Referer': 'https://www.instagram.com/'
        })
        
        # Mô phỏng việc lấy feed
        feed_response = session.get(
            'https://www.instagram.com/api/v1/feed/timeline/',
            headers=feed_headers,
            timeout=10
        )
        
        # 3. Mô phỏng hành vi cuộn và lướt
        console.print(f"   🖱️ Đang mô phỏng lướt và cuộn trang trong {scroll_duration}s...")
        
        start_time = time.time()
        scroll_actions = 0
        like_simulations = 0
        view_simulations = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("AI AutoBot đang hoạt động...", total=scroll_duration)
            
            while time.time() - start_time < scroll_duration:
                # Mô phỏng các hành động ngẫu nhiên
                action = random.choice(['scroll', 'pause', 'view', 'like_simulation'])
                
                if action == 'scroll':
                    scroll_actions += 1
                    progress.update(task, description=f"📜 Cuộn trang ({scroll_actions})...")
                    time.sleep(random.uniform(0.5, 2.0))
                    
                elif action == 'pause':
                    pause_time = random.uniform(1.0, 3.0)
                    progress.update(task, description=f"⏸️ Dừng {pause_time:.1f}s...")
                    time.sleep(pause_time)
                    
                elif action == 'view':
                    view_simulations += 1
                    progress.update(task, description=f"👀 Xem bài viết ({view_simulations})...")
                    time.sleep(random.uniform(2.0, 5.0))
                    
                elif action == 'like_simulation':
                    like_simulations += 1
                    progress.update(task, description=f"❤️ Thích bài viết ({like_simulations})...")
                    time.sleep(random.uniform(1.0, 2.0))
                
                # Cập nhật tiến trình
                elapsed = time.time() - start_time
                progress.update(task, advance=min(elapsed, scroll_duration) - progress.tasks[task].completed)
        
        console.print(f"   ✅ [bold green]AI AutoBot hoàn thành: {scroll_actions} lần cuộn, {view_simulations} lần xem, {like_simulations} lần thích[/bold green]")
        return True
        
    except Exception as e:
        console.print(f"   ⚠️ [bold yellow]AI AutoBot có lỗi nhỏ: {str(e)}[/bold yellow]")
        return False

def human_like_delay(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """
    Tạo độ trễ giống con người với thời gian ngẫu nhiên
    """
    delay_time = random.uniform(min_seconds, max_seconds)
    time.sleep(delay_time)

# --- Display Functions ---

def display_banner():
    """Hiển thị banner."""
    clear_screen()
    
    banner_art = Text(justify="center")
    art_lines = """
███╗   ███╗ █████╗ ██████╗  ██╗███████╗ ██████╗ ███████╗
████╗ ████║██╔══██╗██╔══██╗███║╚════██║██╔═████╗██╔════╝
██╔████╔██║███████║██████╔╝╚██║    ██╔╝██║██╔██║███████╗
██║╚██╔╝██║██╔══██║██╔═══╝  ██║   ██╔╝ ████╔╝██║╚════██║
██║ ╚═╝ ██║██║  ██║██║      ██║   ██║  ╚██████╔╝███████║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝      ╚═╝   ╚═╝   ╚═════╝ ╚══════╝                                                                                                                                                                                                                                                                                                                                                                                                                                                               
    """
    
    for line in art_lines.split('\n'):
        if line.strip():
            banner_art.append(Text(line.strip(), style="bold yellow") + "\n")
            
    console.print(Panel(
        banner_art, 
        title=trim_title_for_panel("[bold cyan]✨ INSTAGRAM TOOL VIP (MULTI-ACCOUNT) ✨"), 
        border_style=Style(color="cyan", bold=True), 
        padding=(1, 1),
        title_align="center",
        box=HEAVY_EDGE
    ))

def display_current_info(authorization: str):
    """Hiển thị trạng thái Authorization và IP thật cùng vị trí địa lý."""
    
    ip_info = get_real_ip_info()
    
    auth_status = Text()
    auth_status.append(f"Authorization: ")
    auth_status.append(f"{'ĐÃ KẾT NỐI' if authorization else 'CHƯA CÓ'}", style=f"bold {'green' if authorization else 'red'}")
    
    # Đã thêm màu cho các thông tin trạng thái
    ip_display = Text(f" Địa Chỉ IP  : {ip_info['ip']}", style="bold magenta")
    location_display = Text(f" Vị trí  : {ip_info['location']}", style="bold green")
    ua_display = Text(f" User-Agent  : {GLOBAL_USER_AGENT[:50]}...", style="bold cyan")
    
    info_table = Table(title="[bold yellow]🌍 TRẠNG THÁI HIỆN TẠI 🌍[/bold yellow]", border_style="bold yellow", show_header=False, show_lines=False)
    info_table.add_column("Key", style="bold green")
    info_table.add_column("Value")
    
    info_table.add_row(" Authorization:", auth_status)
    info_table.add_row("", ip_display)
    info_table.add_row("", location_display)
    info_table.add_row("", ua_display) 
    info_table.add_row(" Tài khoản IG:", f"[bold magenta]{len(ACCOUNTS_LIST)}[/bold magenta] đã chọn") 
    
    console.print(Panel(
        info_table, 
        border_style="deep_sky_blue1", 
        title_align="center",
        box=HEAVY_EDGE
    ))

# --- User-Agent Function ---

def get_user_agent():
    """Xử lý việc nhập và lưu danh sách User-Agent."""
    global GLOBAL_USER_AGENT
    
    display_banner()
    
    # Đọc danh sách User-Agent hiện có
    try:
        with open(USER_AGENT_FILE, 'r', encoding='utf-8') as f:
            user_agents = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        user_agents = []
    
    if user_agents:
        GLOBAL_USER_AGENT = random.choice(user_agents)
    
    IG_LOGIN_HEADERS['User-Agent'] = GLOBAL_USER_AGENT

    ua_menu_text = Text(justify="left")
    
    # Hiển thị số lượng User-Agent hiện có
    ua_count = len(user_agents)
    ua_menu_text.append(f" ✈ Số lượng User-Agent đã lưu: {ua_count}", style="bold white")
    if ua_count > 0:
        ua_menu_text.append(f"\n ✈ User-Agent đang sử dụng: {GLOBAL_USER_AGENT[:50]}...", style="bold white")
    
    ua_menu_text.append("\n ✈ ", style="bold white").append("1", style="bold cyan").append(" : Sử dụng danh sách User-Agent hiện tại", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("2", style="bold cyan").append(" : Thêm User-Agent mới vào danh sách", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("3", style="bold cyan").append(" : Nhập danh sách User-Agent từ file", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("4", style="bold cyan").append(" : Xem tất cả User-Agent trong danh sách", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("5", style="bold cyan").append(" : Xem User-Agent của từng tài khoản", style="bold white")
    ua_menu_text.append("\n ✈ ", style="bold white").append("6", style="bold cyan").append(" : Xóa tất cả và dùng User-Agent mặc định", style="bold white")
    
    console.print(Panel(
        ua_menu_text,
        title=trim_title_for_panel("[bold yellow]👤 QUẢN LÝ USER-AGENT 👤[/bold yellow]"),
        border_style="yellow",
        box=HEAVY_EDGE, 
        title_align="center"
    ))
    
    prompt_default = "1"
    
    while True:
        choice = Prompt.ask(f" ✈ [bold yellow]Nhập Lựa Chọn (1/2/3/4/5/6)[/bold yellow]", default=prompt_default).strip()
        
        if choice == '1':
            if not user_agents:
                GLOBAL_USER_AGENT = DEFAULT_USER_AGENT
                console.print(f"✔ [bold yellow]Chưa có User-Agent, sử dụng mặc định.[/bold yellow]")
            break
            
        elif choice == '2':
            console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
            console.print("✏️ [bold white]Nhập từng User-Agent mới vào danh sách.[/bold white]")
            console.print("✏️ [bold white]Mỗi lần nhập một User-Agent, nhấn Enter để nhập tiếp.[/bold white]")
            console.print("✏️ [bold white]Nhấn Enter (để trống) khi muốn kết thúc nhập.[/bold white]")
            
            new_uas = []
            while True:
                new_ua = Prompt.ask(f" ✈ [bold cyan]Nhập User-Agent mới (Enter trống để kết thúc)[/bold cyan]").strip()
                if not new_ua:
                    break
                new_uas.append(new_ua)
            
            if new_uas:
                # Thêm vào danh sách hiện có
                user_agents.extend(new_uas)
                # Ghi toàn bộ danh sách vào file
                with open(USER_AGENT_FILE, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(user_agents))
                GLOBAL_USER_AGENT = random.choice(user_agents)
                console.print(f"✔ [bold green]Đã thêm thành công {len(new_uas)} User-Agent mới vào danh sách![/bold green]")
                break
                
        elif choice == '3':
            console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
            console.print("✏️ [bold white]File text cần chứa mỗi User-Agent trên một dòng.[/bold white]")
            file_path = Prompt.ask(f" ✈ [bold cyan]Nhập đường dẫn đến file chứa danh sách User-Agent[/bold cyan]").strip()
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_uas = [line.strip() for line in f if line.strip()]
                if new_uas:
                    # Thêm vào danh sách hiện có
                    user_agents.extend(new_uas)
                    # Ghi toàn bộ danh sách vào file
                    with open(USER_AGENT_FILE, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(user_agents))
                    GLOBAL_USER_AGENT = random.choice(user_agents)
                    console.print(f"✔ [bold green]Đã nhập thành công {len(new_uas)} User-Agent từ file![/bold green]")
                    break
                else:
                    console.print("[bold red]File trống hoặc không chứa User-Agent hợp lệ![/bold red]")
            except FileNotFoundError:
                console.print("[bold red]Không tìm thấy file![/bold red]")
            except Exception as e:
                console.print(f"[bold red]Lỗi đọc file: {str(e)}[/bold red]")
                
        elif choice == '4':
            if user_agents:
                console.print("[bold yellow]═══════════ DANH SÁCH TẤT CẢ USER-AGENT ═══════════[/bold yellow]")
                for i, ua in enumerate(user_agents, 1):
                    console.print(f"  {i}. {ua[:100]}...")
                console.print(f"\n[bold green]Tổng số User-Agent trong danh sách: {len(user_agents)}[/bold green]")
                console.print("[bold yellow]═══════════════════════════════════════════════════[/bold yellow]")
                Prompt.ask(" [bold cyan]Nhấn Enter để quay lại menu[/bold cyan]")
            else:
                console.print("[bold yellow]Danh sách trống! Chưa có User-Agent nào được thêm vào.[/bold yellow]")
                
        elif choice == '5':
            # Xem User-Agent của từng tài khoản
            if not ACCOUNTS_LIST:
                console.print("[bold yellow]Chưa có tài khoản nào được thêm vào.[/bold yellow]")
            else:
                console.print("[bold yellow]═══════════ USER-AGENT CỦA CÁC TÀI KHOẢN ═══════════[/bold yellow]")
                for acc in ACCOUNTS_LIST:
                    username = acc.get('username')
                    account_ua = get_account_user_agent(username)
                    if account_ua:
                        console.print(f"\n[bold cyan]👤 Tài khoản: {username}[/bold cyan]")
                        console.print(f"[bold white]🔹 User-Agent: {account_ua[:100]}...[/bold white]")
                    else:
                        console.print(f"\n[bold cyan]👤 Tài khoản: {username}[/bold cyan]")
                        console.print("[bold yellow]🔸 Đang sử dụng User-Agent mặc định[/bold yellow]")
                
                console.print("\n[bold yellow]═══════════════════════════════════════════════════[/bold yellow]")
                Prompt.ask("[bold cyan]Nhấn Enter để quay lại menu[/bold cyan]")
            
        elif choice == '6':
            if safe_file_rw(USER_AGENT_FILE, 'd'):
                console.print(f"✔ [bold green]Đã xóa {USER_AGENT_FILE}![/bold green]")
            GLOBAL_USER_AGENT = DEFAULT_USER_AGENT
            user_agents = []
            console.print(f"✔ [bold green]Đã chuyển về User-Agent mặc định.[/bold green]")
            break
            
        else:
            console.print("❌ [bold red]Lựa chọn không hợp lệ! Hãy nhập lại.[/bold red]")

    IG_LOGIN_HEADERS['User-Agent'] = GLOBAL_USER_AGENT
    console.print(f"✔ [bold green]Sử dụng User-Agent: {GLOBAL_USER_AGENT[:50]}...[/bold green]")
    time.sleep(1) 

# --- Authorization Function ---

def get_authorization():
    """Xử lý file Authorization."""
    display_banner()
    
    console.print("✅ [bold green]ĐANG CHẠY CODE PYTHON ĐÃ NÂNG CẤP HỖ TRỢ ĐA TÀI KHOẢN INSTAGRAM![/bold green]") 
    
    current_auth = safe_file_rw(AUTHORIZATION_FILE, 'r')
    display_current_info(current_auth) 
    
    auth_menu_text = Text(justify="left")
    # FIX: Tối ưu hóa cách nối Text để đảm bảo màu sắc
    auth_menu_text.append(" ✈ Nhập ", style="bold white").append("1", style="bold cyan").append(" để vào Tool Instagram", style="bold white")
    auth_menu_text.append("\n ✈ Nhập ", style="bold white").append("2", style="bold cyan").append(" Để Xóa Authorization Hiện Tại", style="bold white")
    
    console.print(Panel(
        auth_menu_text,
        title=trim_title_for_panel("[bold cyan]✈️ LỰA CHỌN TÁC VỤ ✈️[/bold cyan]"),
        border_style="cyan",
        box=HEAVY_EDGE, 
        title_align="center"
    ))
    
    while True:
        choice = Prompt.ask(f" ✈ [bold yellow]Nhập Lựa Chọn (1 hoặc 2)[/bold yellow]").strip()
        if choice in ['1', '2']:
            choice = int(choice)
            break
        console.print("❌ [bold red]Lựa chọn không hợp lệ! Hãy nhập lại.[/bold red]")

    if choice == 2:
        if safe_file_rw(AUTHORIZATION_FILE, 'd'):
            console.print(f"✔ [bold green]Đã xóa {AUTHORIZATION_FILE}![/bold green]")
        else:
            console.print(f"! [bold yellow]File {AUTHORIZATION_FILE} không tồn tại![/bold yellow]")
        console.print("👉 [bold white]Vui lòng nhập lại thông tin![/bold white]")

    auth_content = safe_file_rw(AUTHORIZATION_FILE, 'r')
    
    while not auth_content:
        console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
        auth_content = Prompt.ask(f" ✈ [bold cyan]Nhập Authorization[/bold cyan]").strip()
        if auth_content:
            safe_file_rw(AUTHORIZATION_FILE, 'w', auth_content)
        else:
            console.print("[bold red]Authorization không được để trống![/bold red]")

    return auth_content

# --- Instagram Login/Cookies Functions ---

def ig_login_with_2fa(username: str, password: str, proxy_dict=None, two_fa_key=None):
    """
    Đăng nhập Instagram bằng tài khoản/mật khẩu với hỗ trợ 2FA.
    Trả về chuỗi cookies nếu thành công.
    """
    IG_LOGIN_HEADERS['User-Agent'] = GLOBAL_USER_AGENT
    
    with requests.Session() as s:
        # Cấu hình proxy nếu có
        if proxy_dict:
            proxies = format_proxy_for_requests(proxy_dict)
            s.proxies.update(proxies)
            
        try:
            # 1. Get CSRF Token
            console.print(f"[bold yellow]⏳ Đang lấy CSRF token cho {username}...[/bold yellow]")
            r = s.get('https://www.instagram.com/accounts/login/', headers=IG_LOGIN_HEADERS, timeout=10)
            csrf_token = s.cookies.get('csrftoken')
            
            if not csrf_token:
                console.print("❌ [bold red]Không lấy được CSRF token ban đầu. Đăng nhập thất bại.[/bold red]")
                return None
            
            IG_LOGIN_HEADERS['X-Csrftoken'] = csrf_token
            
            # 2. Login POST
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'queryParams': {},
                'optIntoOneTap': 'false'
            }
            
            console.print("⏳ [bold yellow]Đang gửi yêu cầu đăng nhập...[/bold yellow]")
            
            r_login = s.post(IG_LOGIN_URL, headers=IG_LOGIN_HEADERS, data=login_data, timeout=10)
            login_json = r_login.json()
            
            # Nếu đã xác thực ngay lập tức
            if login_json.get('authenticated'):
                console.print("✅ [bold green]Đăng nhập thành công![/bold green]")
                cookie_str = "; ".join([f"{k}={v}" for k, v in s.cookies.items()])
                return cookie_str

            # Nếu cần 2FA
            if login_json.get('two_factor_required'):
                console.print("🔐 [bold yellow]Tài khoản có bảo mật 2FA. Đang xử lý xác thực...[/bold yellow]")

                two_factor_info = login_json.get('two_factor_info', {}) or {}
                two_factor_identifier = two_factor_info.get('two_factor_identifier') or two_factor_info.get('two_factor_id')

                if not two_factor_identifier:
                    console.print("❌ [bold red]Không lấy được thông tin 2FA từ Instagram.[/bold red]")
                    return None

                # Kiểm tra phương thức xác thực có thể dùng (sms/totp)
                sms_on = two_factor_info.get('sms_two_factor_on', False)
                totp_on = two_factor_info.get('totp_two_factor_on', False)

                method = None
                # Nếu cả 2 đều bật, cho người dùng chọn
                if sms_on and totp_on:
                    console.print("📱 Phương thức 2FA: Có thể dùng SMS hoặc Authenticator (App).")
                    method = Prompt.ask(" ✈ [bold cyan]Chọn phương thức (sms/totp)[/bold cyan]", choices=['sms','totp'], default='sms')
                elif sms_on:
                    method = 'sms'
                    console.print("📩 Phương thức 2FA: SMS được phát hiện. Hệ thống sẽ gửi mã SMS.")
                elif totp_on:
                    method = 'totp'
                    console.print("🔐 Phương thức 2FA: Authenticator (App) được phát hiện. Nhập mã từ ứng dụng của bạn.")
                else:
                    # Fallback: không biết phương thức, chỉ yêu cầu nhập mã
                    console.print("🔐 Không phát hiện rõ phương thức 2FA. Vui lòng nhập mã nhận được.")
                    method = Prompt.ask(" ✈ [bold cyan]Phương thức (sms/totp) hoặc để trống nếu không biết[/bold cyan]", default="").strip() or None

                # Tạo mã 2FA tự động nếu có key
                verification_code = None
                if two_fa_key and method == 'totp':
                    verification_code = get_2fa_code(two_fa_key)
                    if verification_code:
                        console.print(f"🔐 [bold green]Mã 2FA tự động: {verification_code}[/bold green]")
                    else:
                        console.print("[bold yellow]⚠️ Không thể tạo mã 2FA tự động. Vui lòng nhập thủ công.[/bold yellow]")
                
                if not verification_code:
                    # Thử nhiều lần (tối đa 3 lần) cho trường hợp nhập sai mã
                    max_attempts = 3
                    for attempt in range(1, max_attempts + 1):
                        console.print(f"⏳ [bold yellow]Lần {attempt}/{max_attempts} - Vui lòng nhập mã 2FA (6 chữ số)[/bold yellow]")
                        verification_code = Prompt.ask(" ✈ [bold cyan]Nhập mã xác thực 2FA (6 chữ số)[/bold cyan]").strip()

                        if not verification_code or not verification_code.isdigit() or len(verification_code) < 4:
                            console.print("❌ [bold red]Mã 2FA không hợp lệ! Vui lòng nhập mã hợp lệ.[/bold red]")
                            if attempt == max_attempts:
                                return None
                            continue
                        break

                two_factor_url = 'https://www.instagram.com/accounts/login/ajax/two_factor/'

                # Cập nhật CSRF token (nếu có)
                csrf_token = s.cookies.get('csrftoken')
                if csrf_token:
                    IG_LOGIN_HEADERS['X-Csrftoken'] = csrf_token

                two_factor_data = {
                    'username': username,
                    'verificationCode': verification_code,
                    'identifier': two_factor_identifier,  # Instagram expects 'identifier'
                    'queryParams': '{}',
                    'optIntoOneTap': 'false'
                }
                # Gửi thông tin phương thức xác thực nếu có
                if method:
                    two_factor_data['verification_method'] = method
                    if method == 'sms':
                        two_factor_data['phone_number'] = ''  # Instagram yêu cầu field này khi dùng SMS

                try:
                    # Cập nhật headers với Content-Type phù hợp
                    headers_2fa = IG_LOGIN_HEADERS.copy()
                    headers_2fa['Content-Type'] = 'application/x-www-form-urlencoded'
                    
                    r_2fa = s.post(
                        two_factor_url,
                        headers=headers_2fa,
                        data=two_factor_data,
                        timeout=10
                    )

                    try:
                        two_fa_json = r_2fa.json()
                        # Debug response nếu có lỗi
                        if not two_fa_json.get('authenticated'):
                            console.print(f"🔍 [bold yellow]Debug - Response: {str(two_fa_json)}[/bold yellow]")
                    except json.JSONDecodeError:
                        console.print(f"❌ [bold red]Lỗi phản hồi từ Instagram khi xác thực 2FA.[/bold red]")
                        console.print(f"🔍 [bold yellow]Debug - Raw Response: {r_2fa.text[:200]}...[/bold yellow]")
                        return None
                except requests.exceptions.RequestException as e:
                    console.print(f"❌ [bold red]Lỗi kết nối khi xác thực 2FA: {str(e)}[/bold red]")
                    return None

                if two_fa_json.get('authenticated'):
                    console.print("✅ [bold green]Xác thực 2FA thành công! Đăng nhập thành công![/bold green]")
                    cookie_str = "; ".join([f"{k}={v}" for k, v in s.cookies.items()])
                    return cookie_str
                else:
                    # Có thể có thông tin lỗi chi tiết
                    error_msg = two_fa_json.get('message') or two_fa_json.get('errors') or str(two_fa_json)
                    console.print(f"❌ [bold red]Xác thực 2FA thất bại: {error_msg}[/bold red]")
                    return None

            # Nếu không authenticated và không cần 2FA
            console.print(f"❌ [bold red]Đăng nhập thất bại. Message: {login_json.get('message', 'Lỗi không rõ')}[/bold red]")
            return None
            
        except requests.exceptions.RequestException as e:
            console.print(f"❌ [bold red]Lỗi kết nối khi đăng nhập IG: {e}[/bold red]")
            return None
        except Exception as e:
            console.print(f"❌ [bold red]Lỗi không xác định khi đăng nhập IG: {e}[/bold red]")
            return None

# --- HÀM MỚI: XỬ LÝ ĐĂNG NHẬP BẰNG ACCOUNT ---

def login_with_account(username: str, authorization: str):
    """
    Đăng nhập Instagram bằng tài khoản/mật khẩu và tự động thêm vào Golike.
    Trả về cookies nếu thành công, None nếu thất bại.
    """
    console.print(f"\n[bold cyan]🔐 ĐĂNG NHẬP BẰNG TÀI KHOẢN CHO: {username}[/bold cyan]")
    
    # Nhập mật khẩu
    password = Prompt.ask(f" ✈ [bold cyan]Nhập mật khẩu Instagram cho {username}[/bold cyan]", password=True).strip()
    if not password:
        console.print("[bold red]❌ Mật khẩu không được để trống![/bold red]")
        return None
    
    # Kiểm tra xem có key 2FA đã lưu không
    two_fa_key = get_2fa_key_for_account(username)
    if two_fa_key:
        use_saved_key = Confirm.ask(f" ✈ [bold yellow]Phát hiện key 2FA đã lưu cho {username}. Sử dụng key này?[/bold yellow]", default=True)
        if not use_saved_key:
            two_fa_key = None
    
    # Hỏi nếu muốn lưu key 2FA mới
    if not two_fa_key:
        save_2fa = Confirm.ask(f" ✈ [bold yellow]Bạn có muốn lưu key 2FA cho {username}? (Nếu có)[/bold yellow]", default=False)
        if save_2fa:
            two_fa_key_input = Prompt.ask(f" ✈ [bold cyan]Nhập key 2FA (base32 secret) cho {username}[/bold cyan]").strip()
            if two_fa_key_input:
                save_2fa_key_for_account(username, two_fa_key_input)
                two_fa_key = two_fa_key_input
    
    # Lấy proxy nếu có
    proxy_dict = get_account_proxy(username)
    
    # Thực hiện đăng nhập
    console.print(f"[bold yellow]⏳ Đang đăng nhập Instagram cho {username}...[/bold yellow]")
    cookies = ig_login_with_2fa(username, password, proxy_dict, two_fa_key)
    
    if cookies:
        console.print(f"✅ [bold green]Đăng nhập thành công cho {username}![/bold green]")
        
        # Lấy thông tin tài khoản từ cookies
        console.print(f"[bold yellow]⏳ Đang lấy thông tin tài khoản...[/bold yellow]")
        actual_username, user_id, csrftoken = get_account_info_from_cookies(cookies)
        
        if actual_username:
            console.print(f"✅ [bold green]Lấy thông tin thành công: {actual_username}[/bold green]")
            
            # Tự động thêm vào Golike
            console.print(f"[bold yellow]⏳ Đang thêm tài khoản vào Golike...[/bold yellow]")
            if add_account_to_golike(actual_username, authorization, cookies, proxy_dict):
                console.print(f"✅ [bold green]Tài khoản {actual_username} đã được thêm vào Golike thành công![/bold green]")
            else:
                console.print(f"⚠️ [bold yellow]Không thể thêm tài khoản vào Golike, nhưng vẫn có thể sử dụng cookies.[/bold yellow]")
            
            # Lưu cookies vào file
            cookie_file = get_cookie_file_path(actual_username)
            safe_file_rw(cookie_file, 'w', cookies)
            console.print(f"✅ [bold green]Đã lưu cookies vào file: {cookie_file}[/bold green]")
            
            return cookies
        else:
            console.print("[bold red]❌ Không thể lấy thông tin tài khoản từ cookies![/bold red]")
            return None
    else:
        console.print("[bold red]❌ Đăng nhập thất bại![/bold red]")
        return None

# --- HÀM CẬP NHẬT: XỬ LÝ COOKIES CHO TÀI KHOẢN (THÊM CHẾ ĐỘ ACCOUNT) ---

def get_cookies_for_account(username: str):
    """Cho phép người dùng nhập hoặc đăng nhập để lấy cookies cho một tài khoản cụ thể. 
    Đã thêm chế độ đăng nhập bằng Account."""
    
    cookies_file = get_cookie_file_path(username)
    cookies = safe_file_rw(cookies_file, 'r')
    
    # Xử lý User-Agent cho tài khoản
    account_ua = get_account_user_agent(username)
    
    # Nếu tài khoản chưa có User-Agent, gán ngẫu nhiên một cái từ danh sách
    if not account_ua:
        try:
            with open(USER_AGENT_FILE, 'r', encoding='utf-8') as f:
                user_agents = [line.strip() for line in f if line.strip()]
            if user_agents:
                account_ua = assign_user_agent(username, user_agents)
                console.print(f"✔ [bold green]Đã gán ngẫu nhiên User-Agent cho tài khoản {username}[/bold green]")
                console.print(f"👉 [bold cyan]User-Agent: {account_ua[:50]}...[/bold cyan]")
            else:
                account_ua = DEFAULT_USER_AGENT
                console.print(f"⚠️ [bold yellow]Sử dụng User-Agent mặc định cho tài khoản {username}[/bold yellow]")
        except FileNotFoundError:
            account_ua = DEFAULT_USER_AGENT
            console.print(f"⚠️ [bold yellow]Không tìm thấy danh sách User-Agent, sử dụng mặc định[/bold yellow]")
    
    while True:
        display_banner()
        display_current_info(safe_file_rw(AUTHORIZATION_FILE, 'r'))
        
        cookies_menu_text = Text(justify="left")
        
        cookies_menu_text.append(f" 🍪 Quản lý Cookies cho tài khoản: {username} 🍪 ", style="bold yellow")
        
        if cookies:
            cookies_menu_text.append("\n ✈ Cookies hiện tại: ", style="bold white").append("ĐÃ TÌM THẤY", style="bold green")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("ENTER", style="bold cyan").append(" : Dùng Cookies hiện tại và TIẾP TỤC sang nick tiếp theo", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("1", style="bold cyan").append(" : Nhập Cookies Thủ công mới (sẽ ghi đè)", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("2", style="bold cyan").append(" : Đăng nhập bằng tài khoản/mật khẩu IG (Tạo cookies mới)", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("3", style="bold cyan").append(" : Cấu hình Proxy cho tài khoản này", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("4", style="bold cyan").append(" : Xóa Cookies hiện tại", style="bold white")
            
            prompt_default = "" 
        else:
            cookies_menu_text.append("\n ✈ ", style="bold white").append("Chưa có Cookies IG", style="bold red")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("ENTER", style="bold cyan").append(" : Bỏ qua tài khoản này (Không chạy)", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("1", style="bold cyan").append(" : Nhập Cookies Thủ công", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("2", style="bold cyan").append(" : Đăng nhập bằng tài khoản/mật khẩu IG (Tạo cookies)", style="bold white")
            cookies_menu_text.append("\n ✈ Nhập ", style="bold white").append("3", style="bold cyan").append(" : Cấu hình Proxy cho tài khoản này", style="bold white")
            
            prompt_default = ""

        console.print(Panel(
            cookies_menu_text,
            title=trim_title_for_panel(f"[bold magenta]QUẢN LÝ COOKIES: {username}[/bold magenta]"),
            border_style="magenta",
            box=HEAVY_EDGE, 
            title_align="center"
        ))
        
        choice = Prompt.ask(f" ✈ [bold yellow]Nhập Lựa Chọn (Enter/1/2/3/4)[/bold yellow]", default=prompt_default).strip()
        
        if choice == '': # Người dùng nhấn ENTER
            if cookies:
                console.print(f"✔ [bold green]Sử dụng Cookies cũ cho {username}.[/bold green]")
                return cookies # Cookies đã có, dùng luôn
            else:
                console.print(f"❌ [bold red]Bỏ qua tài khoản {username} (Không có Cookies).[/bold red]")
                return None # Cookies chưa có, bỏ qua
        
        elif choice == '1': # Nhập Cookies Thủ công mới
            if cookies and safe_file_rw(get_cookie_file_path(username), 'd'):
                console.print(f"✔ [bold green]Đã xóa cookies cũ![/bold green]")
            
            cookies_content = Prompt.ask(f" ✈ [bold cyan]Nhập Cookies cho {username}[/bold cyan]").strip()
            
            if cookies_content:
                safe_file_rw(get_cookie_file_path(username), 'w', cookies_content)
                console.print(f"✔ [bold green]Đã lưu Cookies mới cho {username}.[/bold green]")
                return cookies_content
            else:
                console.print("[bold red]Cookies không được để trống! Thử lại.[/bold red]")
                time.sleep(1)
                
        elif choice == '2': # Đăng nhập bằng tài khoản/mật khẩu
            # Lấy Authorization từ file
            auth = safe_file_rw(AUTHORIZATION_FILE, 'r')
            if not auth:
                console.print("[bold red]❌ Chưa có Authorization! Vui lòng cấu hình Authorization trước.[/bold red]")
                time.sleep(2)
                continue
                
            new_cookies = login_with_account(username, auth)
            if new_cookies:
                console.print(f"✔ [bold green]Đã đăng nhập thành công cho {username}.[/bold green]")
                return new_cookies
            else:
                console.print("[bold red]Đăng nhập thất bại. Vui lòng thử lại.[/bold red]")
                time.sleep(2)
        
        elif choice == '3': # Cấu hình Proxy
            configure_account_proxy(username)
            time.sleep(1)
        
        elif choice == '4': # Xóa Cookies hiện tại
            if cookies:
                confirm = Confirm.ask(f" ✈ [bold red]Xác nhận xóa cookies của {username}?[/bold red]", default=False)
                if confirm:
                    if safe_file_rw(get_cookie_file_path(username), 'd'):
                        console.print(f"✅ [bold green]Đã xóa cookies của {username}[/bold green]")
                        cookies = None
                    else:
                        console.print(f"❌ [bold red]Không thể xóa cookies của {username}[/bold red]")
            else:
                console.print(f"⚠️ [bold yellow]{username} chưa có cookies để xóa[/bold yellow]")
            time.sleep(1)
        
        else:
            console.print("❌ [bold red]Lựa chọn không hợp lệ! Hãy nhập Enter, 1, 2, 3 hoặc 4.[/bold red]")
            time.sleep(1)

def configure_account_proxy(username: str):
    """Cấu hình proxy cho tài khoản cụ thể."""
    console.print(f"\n[bold cyan]🔧 Cấu hình Proxy cho tài khoản: {username}[/bold cyan]")
    
    # Hiển thị proxy hiện tại
    current_proxy = get_account_proxy(username)
    if current_proxy:
        console.print(f"[bold yellow]Proxy hiện tại: {current_proxy['protocol']}://{current_proxy['host']}:{current_proxy['port']}[/bold yellow]")
    else:
        console.print("[bold yellow]Chưa có proxy được cấu hình cho tài khoản này.[/bold yellow]")
    
    proxy_menu = Text()
    proxy_menu.append("1. Nhập proxy thủ công\n", style="bold green")
    proxy_menu.append("2. Chọn từ danh sách proxy đã có\n", style="bold cyan")
    proxy_menu.append("3. Xóa proxy hiện tại\n", style="bold red")
    proxy_menu.append("4. Kiểm tra proxy hiện tại\n", style="bold yellow")
    proxy_menu.append("0. Quay lại\n", style="bold white")
    
    console.print(Panel(proxy_menu, title="[bold magenta]MENU PROXY[/bold magenta]", border_style="magenta"))
    
    choice = Prompt.ask(" ✈ [bold cyan]Chọn chức năng[/bold cyan]", choices=['0','1','2','3','4']).strip()
    
    if choice == '1':
        # Nhập proxy thủ công
        proxy_str = Prompt.ask(f" ✈ [bold cyan]Nhập proxy cho {username}[/bold cyan]").strip()
        
        if proxy_str:
            proxy_dict = parse_proxy_string(proxy_str)
            
            if not proxy_dict:
                console.print("[bold red]❌ Format proxy không hợp lệ![/bold red]")
                return
            
            is_valid, error_msg = validate_proxy(proxy_dict)
            if not is_valid:
                console.print(f"[bold red]❌ Proxy không hợp lệ: {error_msg}[/bold red]")
                return
            
            # Kiểm tra proxy live
            console.print("⏳ [bold yellow]Đang kiểm tra proxy...[/bold yellow]")
            is_live, response_time, error_msg = check_proxy_with_retry(proxy_dict)
            
            if is_live:
                assign_proxy_to_account(username, proxy_dict)
                console.print(f"✅ [bold green]Đã gán proxy {proxy_dict['host']}:{proxy_dict['port']} cho {username} (Response: {response_time}ms)[/bold green]")
            else:
                console.print(f"❌ [bold red]Proxy không hoạt động: {error_msg}[/bold red]")
                assign_anyway = Confirm.ask(" ✈ [bold yellow]Vẫn muốn gán proxy này?[/bold yellow]", default=False)
                if assign_anyway:
                    assign_proxy_to_account(username, proxy_dict)
                    console.print(f"✅ [bold yellow]Đã gán proxy không hoạt động cho {username}[/bold yellow]")
    
    elif choice == '2':
        # Chọn từ danh sách proxy đã có
        try:
            with open('temp_proxy_list.json', 'r', encoding='utf-8') as f:
                proxy_list = json.load(f)
        except:
            console.print("[bold red]❌ Chưa có danh sách proxy! Vui lòng thêm proxy trước.[/bold red]")
            return
        
        if not proxy_list:
            console.print("[bold red]❌ Danh sách proxy trống![/bold red]")
            return
        
        display_proxy_list(proxy_list)
        
        while True:
            proxy_idx = Prompt.ask(
                f" ✈ [bold cyan]Nhập STT proxy (1-{len(proxy_list)}) hoặc 0 để hủy[/bold cyan]"
            ).strip()
            
            try:
                idx = int(proxy_idx)
                if idx == 0:
                    return
                if 1 <= idx <= len(proxy_list):
                    selected_proxy = proxy_list[idx-1]['proxy']
                    assign_proxy_to_account(username, selected_proxy)
                    console.print(f"✅ [bold green]Đã gán proxy {selected_proxy['host']}:{selected_proxy['port']} cho {username}[/bold green]")
                    break
                else:
                    console.print("[bold red]❌ STT không hợp lệ![/bold red]")
            except ValueError:
                console.print("[bold red]❌ Vui lòng nhập số![/bold red]")
    
    elif choice == '3':
        # Xóa proxy hiện tại
        if current_proxy:
            confirm = Confirm.ask(" ✈ [bold red]Xác nhận xóa proxy hiện tại?[/bold red]", default=False)
            if confirm:
                remove_proxy_from_account(username)
                console.print("✅ [bold green]Đã xóa proxy khỏi tài khoản[/bold green]")
        else:
            console.print("[bold yellow]⚠️  Tài khoản không có proxy để xóa[/bold yellow]")
    
    elif choice == '4':
        # Kiểm tra proxy hiện tại
        if current_proxy:
            console.print("⏳ [bold yellow]Đang kiểm tra proxy...[/bold yellow]")
            is_live, response_time, error_msg = check_proxy_with_retry(current_proxy)
            
            if is_live:
                console.print(f"✅ [bold green]Proxy hoạt động tốt! Response time: {response_time}ms[/bold green]")
            else:
                console.print(f"❌ [bold red]Proxy không hoạt động: {error_msg}[/bold red]")
        else:
            console.print("[bold yellow]⚠️  Tài khoản không có proxy để kiểm tra[/bold yellow]")

# --- GoLike API Functions ---

def chonacc(authorization: str):
    headers = get_base_headers(authorization)
    try:
        response = requests.get(INSTAGRAM_ACCOUNT_URL, headers=headers, timeout=5)
        response.raise_for_status()
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": 500, "message": "API Error", "detail": f"Dữ liệu trả về không phải JSON: {response.text[:50]}..."}
            
    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Network Error: {e}"}
    except Exception as e:
        return {"status": 500, "message": f"Unexpected Error in chonacc: {e}"}

def nhannv(account_id: int, authorization: str):
    headers = get_base_headers(authorization)
    params = {
        'instagram_account_id': account_id,
        'data': 'null'
    }
    try:
        response = requests.get(GET_JOBS_URL, headers=headers, params=params, timeout=5)
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": 500, "message": "API Error: Invalid JSON (200 OK)", "raw_response": response.text}
        elif response.status_code == 400:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": 400, "message": "Account error: Non-JSON 400 response", "detail": response.text[:50]}
        else:
            return {"status": response.status_code, "message": f"HTTP Error: {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Network Error: {e}"}
    except Exception as e:
        return {"status": 500, "message": f"Unexpected Error in nhannv: {e}"}

def hoanthanh(ads_id: str, account_id: int, authorization: str):
    headers = get_base_headers(authorization)
    data = {
        'instagram_users_advertising_id': ads_id,
        'instagram_account_id': account_id,
        'async': True,
        'data': None
    }
    
    try:
        response = requests.post(COMPLETE_JOBS_URL, headers=headers, json=data, timeout=10, verify=True) 
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": 500, "error": "Lỗi giải mã JSON (200 OK)"}
        else:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": response.status_code, "error": f"Lỗi HTTP {response.status_code} - Dữ liệu không phải JSON."}

    except requests.exceptions.RequestException as e:
        return {'error': f'Không thể kết nối đến server hoặc timeout: {e}', 'status': 500} 
    except Exception as e:
        return {'error': f'Lỗi không mong muốn trong hoanthanh: {e}', 'status': 500}


def baoloi(ads_id: str, object_id: str, account_id: int, job_type: str, authorization: str):
    headers = get_base_headers(authorization)
    
    data1 = {
        'description': 'Tôi đã làm Job này rồi',
        'users_advertising_id': ads_id,
        'type': 'ads',
        'provider': 'instagram',
        'fb_id': account_id,
        'error_type': 6
    }
    try:
        requests.post(REPORT_URL, headers=headers, json=data1, timeout=5)
    except requests.exceptions.RequestException:
        pass

    data2 = {
        'ads_id': ads_id,
        'object_id': object_id,
        'account_id': account_id,
        'type': job_type
    }
    try:
        response = requests.post(SKIP_JOBS_URL, headers=headers, json=data2, timeout=5)
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": 500, "message": f"Lỗi giải mã JSON (Skip Job): {response.text[:50]}..."}
            
    except requests.exceptions.RequestException as e:
        return {"status": 500, "message": f"Network Error on skip: {e}"}

# --- Telegram Functions MỚI (ĐÃ CẬP NHẬT) ---

def send_telegram_message(message: str):
    """Gửi tin nhắn thông báo qua Telegram."""
    # Chỉ cần kiểm tra Chat ID vì Token đã được Hardcode
    if not (GLOBAL_TELEGRAM_TOKEN and GLOBAL_TELEGRAM_TOKEN != "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE" and GLOBAL_TELEGRAM_CHAT_ID):
        return False
        
    try:
        token = GLOBAL_TELEGRAM_TOKEN
        chat_id = GLOBAL_TELEGRAM_CHAT_ID

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'parse_mode': 'HTML', 
            'text': message
        }
        # Tăng timeout cho việc gửi Telegram
        response = requests.post(url, data=payload, timeout=15) 
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False
    except Exception:
        return False

def tool_get_chat_id():
    """Công cụ giúp người dùng lấy Chat ID từ Bot Token của họ (HOẶC BOT CHỦ)."""
    console.print("\n[bold yellow]═════════════ CÔNG CỤ TÌM KIẾM CHAT ID TELEGRAM ═════════════[/bold yellow]")
    
    # Sử dụng token cố định nếu có
    if GLOBAL_TELEGRAM_TOKEN and GLOBAL_TELEGRAM_TOKEN != "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE":
        token_to_use = GLOBAL_TELEGRAM_TOKEN
        console.print(f"ℹ️ [bold white]Sử dụng Token Bot Chủ để tìm Chat ID. Hãy chat bất kỳ với Bot của bạn.[/bold white]")
    else:
        # Nếu chưa cố định token, yêu cầu người dùng nhập để tìm Chat ID
        console.print(f"⚠️ [bold red]Chủ Tool chưa cấu hình Token cố định![/bold red] [bold white]Bạn sẽ cần nhập Token của riêng bạn để tìm Chat ID.[/bold white]")
        token_to_use = Prompt.ask(f" ✈ [bold cyan]Nhập Telegram Bot Token để tìm Chat ID (tạm thời)[/bold cyan]").strip()
        if not token_to_use:
            console.print("[bold red]❌ Token không được để trống. Hủy bỏ.[/bold red]")
            time.sleep(2)
            return

    console.print("1. [bold yellow]CHAT VỚI BOT:[/bold yellow] link bot telegram @thongbaoigbot Gửi bất kỳ tin nhắn nào (ví dụ: '/start') đến Bot.")
    
    try:
        # Dùng offset=-1 để chỉ lấy tin nhắn mới nhất
        url = f"https://api.telegram.org/bot{token_to_use}/getUpdates?offset=-1" 
        
        # Thử lấy tin nhắn trong 5 lần, mỗi lần cách nhau 5 giây
        for attempt in range(1, 6):
            console.print(f"⏳ [bold yellow]Đang thử tìm Chat ID (Lần {attempt}/5)... Đảm bảo bạn đã gửi tin nhắn đến bot.[/bold yellow]")
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                console.print(f"[bold red]❌ Lỗi API. Status Code: {response.status_code}. Thử lại sau 5s.[/bold red]")
                time.sleep(5)
                continue
                
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                # Lấy tin nhắn mới nhất
                latest_update = data['result'][-1] 
                
                # Kiểm tra message (tin nhắn từ người dùng) hoặc channel_post
                if 'message' in latest_update:
                    chat_id = latest_update['message']['chat']['id']
                elif 'channel_post' in latest_update:
                     chat_id = latest_update['channel_post']['chat']['id']
                else:
                    console.print("[bold red]❌ Không tìm thấy tin nhắn mới trong phản hồi. Hãy gửi lại tin nhắn cho bot và thử lại.[/bold red]")
                    time.sleep(5)
                    continue
                
                console.print(f"\n🎉 [bold green]TÌM THẤY CHAT ID THÀNH CÔNG![/bold green]")
                console.print(f"   [bold magenta]Chat ID của bạn là:[/bold magenta] [bold yellow]{chat_id}[/bold yellow]")
                console.print("\n[bold white]⚠️ Hãy nhập Chat ID này vào phần cấu hình Telegram khi chạy BOT.[/bold white]")
                time.sleep(5)
                return
            
            time.sleep(5) # Đợi 5 giây trước khi thử lại

        console.print("\n[bold red]❌ KHÔNG THỂ TÌM THẤY CHAT ID sau 5 lần thử. Vui lòng kiểm tra lại:[/bold red]")
        console.print("   - Bạn đã chat với Bot chưa?")
        if 'token_to_use' not in locals():
            console.print("   - Token Bot bạn nhập có đúng không?")

    except requests.exceptions.RequestException as e:
        console.print(f"\n[bold red]❌ Lỗi kết nối hoặc timeout khi gọi API: {e}[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Lỗi không xác định: {e}[/bold red]")
    
    time.sleep(5)
    return

def get_telegram_config():
    """
    Xử lý việc nhập Telegram Chat ID, KHÔNG LƯU vào file.
    Chat ID chỉ có hiệu lực trong phiên chạy hiện tại.
    """
    global GLOBAL_TELEGRAM_CHAT_ID
    
    # 1. Kiểm tra Token đã được cấu hình chưa
    if GLOBAL_TELEGRAM_TOKEN == "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE":
        console.print("\n⚠️ [bold red]Chủ Tool: Token Telegram chưa được cấu hình. Bỏ qua thông báo Telegram.[/bold red]")
        return False
        
    # Loại bỏ phần đọc/ghi từ file theo yêu cầu người dùng
    
    console.print("\n[bold yellow]════════════════════════════════════════════════[/bold yellow]")
    try:
        confirm = Confirm.ask(f" ✈ [bold yellow]Bạn có muốn nhận thông báo qua Telegram trong phiên này không? (y/n)[/bold yellow]", default=True)
    except Exception:
        confirm = input("Bạn có muốn nhận thông báo qua Telegram trong phiên này không? (y/n, mặc định: y): ").lower() != 'n'
    
    if not confirm:
        console.print(f"✔ [bold blue]Bỏ qua cấu hình Telegram cho phiên này.[/bold blue]")
        return False

    console.print("\n[bold cyan]CẤU HÌNH THÔNG BÁO TELEGRAM (KHÔNG LƯU LẠI)[/bold cyan]")
    console.print(f"ℹ️ [bold white]Bot đã được cấu hình sẵn. Bạn chỉ cần nhập [bold yellow]Chat ID[/bold yellow] của mình.[/bold white]")
    console.print(f"   [bold yellow]Chat ID:[/bold yellow] Là mã số bạn lấy được sau khi chạy chức năng [bold magenta]2. Công cụ tìm Chat ID Telegram[/bold magenta] ở Menu Chính.")
    
    while True:
        new_chat_id = Prompt.ask(f" ✈ [bold cyan]Nhập Telegram Chat ID của bạn[/bold cyan]").strip()
        if new_chat_id:
            # KHÔNG LƯU VÀO FILE THEO YÊU CẦU
            GLOBAL_TELEGRAM_CHAT_ID = new_chat_id
            break
        console.print("[bold red]Chat ID không được để trống![/bold red]")
        
    console.print(f"✔ [bold green]Đã nhập Chat ID. Thông báo sẽ được gửi trong phiên này.[/bold green]")
    time.sleep(1)
    return True

# --- Instagram Interaction Functions (Thêm logic tạm ngưng & Notification) ---

def extract_csrftoken(cookies_str):
    """Trích xuất csrftoken từ chuỗi cookies."""
    for cookie in cookies_str.split(';'):
        if 'csrftoken=' in cookie.strip():
            return cookie.split('=')[1].strip()
    return None

def get_ig_headers(cookies: str, referer: str = "https://www.instagram.com/"):
    """Tạo headers cho API Instagram. Đã cập nhật User-Agent."""
    token = extract_csrftoken(cookies)
    
    IG_HEADERS = {
        'authority': 'i.instagram.com',
        'accept': '*/*',
        'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookies,
        'origin': 'https://www.instagram.com',
        'referer': referer,
        'user-agent': GLOBAL_USER_AGENT, 
        'x-csrftoken': token if token else '',
        'x-ig-app-id': '936619743392459',
        'x-instagram-ajax': '1006309104',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
    }
    return IG_HEADERS

def get_cookie_string(s: requests.Session):
    """Chuyển đối tượng CookieJar thành chuỗi cookies."""
    return "; ".join([f"{k}={v}" for k, v in s.cookies.items()])

def handle_follow_job(account_info: dict, object_id: str):
    """Thực hiện nhiệm vụ Follow và trả về (thành công/thất bại, cookies mới)."""
    cookies = account_info['cookies']
    username = account_info['username']
    
    # Lấy proxy cho tài khoản
    proxy_dict = get_account_proxy(username)
    proxies = format_proxy_for_requests(proxy_dict) if proxy_dict else None
    
    headers = get_ig_headers(cookies)
    url = f"https://i.instagram.com/api/v1/web/friendships/{object_id}/follow/"
    
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)
        
    try:
        for c in cookies.split('; '):
            if '=' in c:
                name, value = c.split('=', 1)
                session.cookies.set(name, value)
                
        response = session.post(url, headers=headers, data=None, timeout=10) 
        
        # Thêm logic tạm ngưng nếu bị block/yêu cầu đăng nhập lại
        if 'login_required' in response.text or response.status_code == 403:
             console.print(f"❌ [bold red]Follow thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị block hoặc cần đăng nhập lại. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
             account_info['is_locked'] = True
             account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
             
             # 📢 THÔNG BÁO TELEGRAM: CHECKPOINT/LOGIN REQUIRED
             telegram_message = f"""
🚨 <b>CẢNH BÁO: NICK CHECKPOINT/LOGIN REQUIRED</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: FOLLOW
- Trạng thái: Cần xác minh/đăng nhập lại.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
             send_telegram_message(telegram_message)
             return False, cookies

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            console.print(f"❌ [bold red]Follow thất bại: Lỗi phản hồi không phải JSON ({response.status_code}).[/bold red]")
            return False, cookies
        
        if response_json.get('status') == 'ok':
            console.print("✅ [bold green]Follow thành công[/bold green]")
            new_cookies = get_cookie_string(session)
            return True, new_cookies
        else:
            console.print(f"❌ [bold red]Follow thất bại:[/bold red] [bold yellow]{response.text[:50]}...[/bold yellow]")
            return False, cookies

    except requests.exceptions.TooManyRedirects as e:
        # ❗ LỖI SỬA CHỮA ĐỂ KHẮC PHỤC SỰ CỐ "EXCEEDED 30 REDIRECTS"
        console.print(f"❌ [bold red]Follow thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị lỗi Redirects (>30). Cần cập nhật Cookies. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
        account_info['is_locked'] = True
        account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
        
        # 📢 THÔNG BÁO TELEGRAM: REDIRECTS LOCK
        telegram_message = f"""
🚨 <b>CẢNH BÁO: LỖI REDIRECT/CẦN CẬP NHẬT COOKIES</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: FOLLOW
- Trạng thái: Lỗi Redirect (>30). Cần cập nhật Cookies.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
        send_telegram_message(telegram_message)
        return False, cookies
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        console.print(f"[bold red]Lỗi nghiêm trọng khi Follow (Network/Unknown):[/bold red] [bold yellow]{e}[/bold yellow]")
        return False, cookies

def handle_like_job(account_info: dict, media_id: str, link: str):
    """Thực hiện nhiệm vụ Like và trả về (thành công/thất bại, cookies mới)."""
    cookies = account_info['cookies']
    username = account_info['username']
    
    # Lấy proxy cho tài khoản
    proxy_dict = get_account_proxy(username)
    proxies = format_proxy_for_requests(proxy_dict) if proxy_dict else None
    
    headers = get_ig_headers(cookies, referer=link)
    headers['authority'] = 'www.instagram.com'
    headers['x-ig-app-id'] = '936619743392459'
    
    url = f"https://www.instagram.com/web/likes/{media_id}/like/"
    
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)
        
    try:
        for c in cookies.split('; '):
            if '=' in c:
                name, value = c.split('=', 1)
                session.cookies.set(name, value)
                
        response = session.post(url, headers=headers, data=None, timeout=10) 

        # Thêm logic tạm ngưng nếu bị block/yêu cầu đăng nhập lại
        if 'login_required' in response.text or response.status_code == 403:
             console.print(f"❌ [bold red]Like thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị block hoặc cần đăng nhập lại. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
             account_info['is_locked'] = True
             account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
             
             # 📢 THÔNG BÁO TELEGRAM: CHECKPOINT/LOGIN REQUIRED
             telegram_message = f"""
🚨 <b>CẢNH BÁO: NICK CHECKPOINT/LOGIN REQUIRED</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: LIKE
- Trạng thái: Cần xác minh/đăng nhập lại.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
             send_telegram_message(telegram_message)
             return False, cookies
        
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {}
            
        if response.status_code == 200 and response_json.get('status') == 'ok':
            console.print("✅ [bold green]Like thành công[/bold green]")
            new_cookies = get_cookie_string(session)
            return True, new_cookies
        elif response.status_code == 400 and 'Sorry, this photo has been deleted' in response.text:
            console.print("❌ [bold red]PHOTO HAS BEEN DELETED[/bold red]")
            return False, cookies
        else:
            console.print(f"❌ [bold red]ERROR (Like):[/bold red] [bold yellow]Status {response.status_code}, Response: {response.text[:50]}...[/bold yellow]")
            return False, cookies

    except requests.exceptions.TooManyRedirects as e:
        # ❗ LỖI SỬA CHỮA ĐỂ KHẮC PHỤC SỰ CỐ "EXCEEDED 30 REDIRECTS"
        console.print(f"❌ [bold red]Like thất bại: Tài khoản [bold cyan]{username}[/bold cyan] bị lỗi Redirects (>30). Cần cập nhật Cookies. Tạm ngưng {LOCK_TIME_SECONDS/60} phút.[/bold red]")
        account_info['is_locked'] = True
        account_info['lock_until'] = time.time() + LOCK_TIME_SECONDS
        
        # 📢 THÔNG BÁO TELEGRAM: REDIRECTS LOCK
        telegram_message = f"""
🚨 <b>CẢNH BÁO: LỖI REDIRECT/CẦN CẬP NHẬT COOKIES</b> 🚨
- Tài khoản: <b><code>{username}</code></b>
- Loại Job: LIKE
- Trạng thái: Lỗi Redirect (>30). Cần cập nhật Cookies.
- Hành động: Đã tạm dừng tài khoản này ({LOCK_TIME_SECONDS // 60} phút).
"""
        send_telegram_message(telegram_message)
        return False, cookies
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # Lỗi Exceeded 30 redirects sẽ nằm ở đây nếu không có khối except TooManyRedirects riêng.
        console.print(f"[bold red]CÓ LỖI XẢY RA!!! (Network/Unknown):[/bold red] [bold yellow]{e}[/bold yellow]")
        return False, cookies

# --- Main Logic ---

def dsacc(chontk_Instagram, authorization: str):
    """Hiển thị danh sách và cho phép chọn nhiều tài khoản Instagram."""
    global ACCOUNTS_LIST
    
    if chontk_Instagram.get("status") != 200:
        console.print(f"❌ [bold red]Authorization hoặc T sai, hoặc GoLike API lỗi. Vui lòng kiểm tra lại![/bold red]")
        error_detail = chontk_Instagram.get('message', 'Lỗi không xác định')
        console.print(f"[bold red]Chi tiết lỗi: {error_detail}[/bold red]")
        raw_response = chontk_Instagram.get('raw_response', None)
        if raw_response:
             console.print(f"[bold red]Raw Response API: {raw_response[:100]}...[/bold red]")
        console.print("[bold yellow]════════════════════════════════════════════════[/bold red]")
        sys.exit(1)
            
    list_all_acc = chontk_Instagram["data"]
    
    while True:
        display_banner()
        display_current_info(authorization)
        
        acc_table = Table(title="[bold green]DANH SÁCH ACC INSTAGRAM[/bold green]", border_style="bold green", show_lines=True)
        acc_table.add_column("STT", justify="center", style="bold yellow")
        acc_table.add_column("Username", style="bold white")
        acc_table.add_column("Trạng Thái", justify="center", style="bold white")

        for i, acc in enumerate(list_all_acc):
            status_text = "[bold green]Hoạt Động[/bold green]"
            if acc.get('status') != 1:
                status_text = "[bold red]Chưa Duyệt[/bold red]"
            
            acc_table.add_row(
                str(i + 1),
                acc['instagram_username'],
                status_text
            )
        
        console.print(Panel(
            acc_table, 
            border_style="green",
            title_align="center",
            box=HEAVY_EDGE
        ))
        
        selection = Prompt.ask(f" ✈ [bold cyan]Nhập STT các tài khoản muốn chạy (VD: 1,3,4) hoặc 'all'[/bold cyan]").strip().lower()
        
        selected_indices = []
        if selection == 'all':
            selected_indices = range(len(list_all_acc))
        else:
            try:
                indices = [int(i.strip()) - 1 for i in selection.split(',') if i.strip().isdigit()]
                for index in indices:
                    if 0 <= index < len(list_all_acc):
                        selected_indices.append(index)
            except:
                console.print("❌ [bold red]Lựa chọn không hợp lệ. Vui lòng nhập đúng định dạng (VD: 1,3,4 hoặc all).[/bold red]")
                time.sleep(1)
                continue
        
        if not selected_indices:
            console.print("❌ [bold red]Vui lòng chọn ít nhất một tài khoản hợp lệ.[/bold red]")
            time.sleep(1)
            continue
            
        ACCOUNTS_LIST.clear()
        
        # 2. Xử lý Cookies cho từng tài khoản đã chọn
        console.print("\n[bold yellow]════════════════════════════════════════════════[/bold yellow]")
        console.print("[bold cyan]BẮT ĐẦU CẤU HÌNH COOKIES CHO TỪNG TÀI KHOẢN...[/bold cyan]")
        
        for index in selected_indices:
            acc_info = list_all_acc[index]
            username = acc_info['instagram_username']
            golike_id = acc_info['id']
            
            cookies = get_cookies_for_account(username)
            
            if cookies:
                ACCOUNTS_LIST.append({
                    "id": golike_id,
                    "username": username,
                    "cookies": cookies,
                    "fail_count": 0,
                    "success_count": 0,
                    "is_locked": False, 
                    "lock_until": 0 
                })
                console.print(f"✔ [bold green]Đã thêm tài khoản {username} vào danh sách chạy.[/bold green]")
            else:
                console.print(f"❌ [bold red]Bỏ qua tài khoản {username} (Không có Cookies/Bị Bỏ qua).[/bold red]")
            
            time.sleep(1)
            
        if ACCOUNTS_LIST:
            console.print(f"\n[bold green]✅ Đã chọn [bold yellow]{len(ACCOUNTS_LIST)}[/bold yellow] tài khoản để chạy luân phiên.[/bold green]")
            time.sleep(2)
            break
        else:
            console.print("\n[bold red]Danh sách tài khoản chạy trống. Vui lòng chọn lại![/bold red]")
            time.sleep(2)
            
    return ACCOUNTS_LIST

def get_user_settings():
    """Nhận cài đặt từ người dùng, ưu tiên sử dụng cấu hình tự động."""
    
    current_config = load_config()
    
    if current_config:
        # FIX CĂN CHỈNH: BỎ justify="left" để rich tự căn chỉnh, dùng \n để ngắt dòng
        config_status = Text() 
        config_status.append("✅ Đã tìm thấy file config.json.\n")
        config_status.append(f" ✈ Delay (giây): {current_config['delay']}\n")
        config_status.append(f" ✈ Nhận tiền lần 2: {'Có' if current_config['lannhan_lan2'] else 'Không'}\n")
        config_status.append(f" ✈ Job Fail Limit: {current_config['doiacc_fail_limit']}\n")
        config_status.append(f" ✈ Job Success Limit: {current_config['job_success_limit']}\n")
        config_status.append(f" ✈ Tỉ lệ Job (Like/Follow): {current_config['job_ratio']}\n")
        config_status.append(f" ✈ Chế độ Job: {'Follow' if current_config['chedo_job'] == 1 else 'Like' if current_config['chedo_job'] == 2 else 'Cả Hai'} (Code: {current_config['chedo_job']})\n")
        config_status.append(f" ✈ AI AutoBot: {'Bật' if current_config['ai_autobot'] else 'Tắt'}\n")
        config_status.append(f" ✈ Thời gian lướt: {current_config['scroll_duration']}s")
        
        console.print(Panel(
            config_status,
            title=trim_title_for_panel("[bold cyan]⚙️ CẤU HÌNH TỰ ĐỘNG ĐÃ LƯU ⚙️[/bold cyan]"), # SỬ DỤNG HÀM CẮT TIÊU ĐỀ
            border_style="cyan",
            box=HEAVY_EDGE,
            title_align="center"
        ))
        
        use_config = Confirm.ask(f" ✈ [bold yellow]Bạn có muốn sử dụng cấu hình này? (y/n)[/bold yellow]", default=True)
        
        if use_config:
            
            # Chuyển đổi chedo_job sang định dạng lam
            lam = []
            if current_config['chedo_job'] == 1:
                lam = ["follow"]
            elif current_config['chedo_job'] == 2:
                lam = ["like"]
            elif current_config['chedo_job'] == 12:
                lam = ["follow", "like"]
            
            # Trả về các giá trị đã load
            console.print("✔ [bold green]Sử dụng cấu hình tự động.[/bold green]")
            return (
                current_config['delay'], 
                "y" if current_config['lannhan_lan2'] else "n", 
                current_config['doiacc_fail_limit'], 
                lam, 
                current_config['job_success_limit'], 
                current_config['job_ratio'],
                current_config['ai_autobot'],
                current_config['scroll_duration']
            )
            
    # Nếu không có config, hoặc người dùng chọn không dùng config
    console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
    
    while True:
        try:
            delay = int(Prompt.ask(f" ✈ [bold cyan]Nhập thời gian làm job (giây) (tối thiểu 3s)[/bold cyan]", default="5").strip())
            if delay >= 3:
                break
            console.print("[bold red]Thời gian phải lớn hơn hoặc bằng 3 giây![/bold red]")
        except ValueError:
            console.print("[bold red]Sai định dạng!!! Vui lòng nhập số.[/bold red]")

    lannhan_confirm = Confirm.ask(f" ✈ [bold yellow]Nhận tiền lần 2 nếu lần 1 fail? (y/n)[/bold yellow]", default=True)
    lannhan = "y" if lannhan_confirm else "n"

    while True:
        try:
            doiacc = int(Prompt.ask(f" ✈ [bold cyan]Số job fail để chuyển sang tài khoản Instagram khác (>= 1)[/bold cyan]", default="5").strip())
            if doiacc >= 1:
                break
            console.print("[bold red]Số job fail phải là số nguyên dương (>= 1)![/bold red]")
        except ValueError:
            console.print("[bold red]Nhập vào 1 số!!![/bold red]")
            
    # --- Cài đặt Giới hạn Job Thành công ---
    while True:
        try:
            job_limit = int(Prompt.ask(f" ✈ [bold cyan]Số job thành công tối đa trước khi đổi tài khoản (>= 1)[/bold cyan]", default="10").strip())
            if job_limit >= 1:
                break
            console.print("[bold red]Giới hạn job phải là số nguyên dương (>= 1)![/bold red]")
        except ValueError:
            console.print("[bold red]Nhập vào 1 số!!![/bold red]")
    # ----------------------------------------
    
    # --- Nhập Tỉ lệ Like/Follow ---
    while True:
        job_ratio = Prompt.ask(f" ✈ [bold cyan]Nhập tỉ lệ Like,Follow (VD: 1,2 = 1 like rồi 2 follow)[/bold cyan]", default="1,1").strip()
        try:
            parts = [int(p.strip()) for p in job_ratio.split(',') if p.strip().isdigit()]
            # Kiểm tra phải có 2 phần, và tổng phải lớn hơn 0
            if len(parts) == 2 and parts[0] >= 0 and parts[1] >= 0 and (parts[0] + parts[1] > 0):
                break
            console.print("[bold red]Tỉ lệ không hợp lệ! Vui lòng nhập 2 số nguyên không âm, tổng lớn hơn 0 (VD: 1,1).[/bold red]")
        except ValueError:
            console.print("[bold red]Sai định dạng! Vui lòng nhập 2 số cách nhau bằng dấu phẩy (VD: 1,1).[/bold red]")
    
    # --- Cấu hình AI AutoBot ---
    ai_autobot = Confirm.ask(f" ✈ [bold yellow]Bật AI AutoBot (lướt và cuộn trang sau mỗi job)?[/bold yellow]", default=True)
    
    scroll_duration = 10  # Mặc định
    if ai_autobot:
        while True:
            try:
                scroll_duration = int(Prompt.ask(f" ✈ [bold cyan]Thời gian lướt cuộn sau mỗi job (giây)[/bold cyan]", default="10").strip())
                if scroll_duration >= 5:
                    break
                console.print("[bold red]Thời gian lướt phải lớn hơn hoặc bằng 5 giây![/bold red]")
            except ValueError:
                console.print("[bold red]Sai định dạng!!! Vui lòng nhập số.[/bold red]")
    
    # --- Cấu hình Nhiệm vụ (Chọn loại job) ---
    config_options = Text(justify="left")
    config_options.append(f" ✈ Nhập 1 : Chỉ nhận nhiệm vụ Follow\n")
    config_options.append(f" ✈ Nhập 2 : Chỉ nhận nhiệm vụ Like\n")
    config_options.append(f" ✈ Nhập 12 : Kết hợp cả Like và Follow theo tỉ lệ {job_ratio}\n")
    
    console.print(Panel(
        config_options,
        title=trim_title_for_panel("[bold yellow]⚙️ CẤU HÌNH NHIỆM VỤ ⚙️[/bold yellow]"),
        border_style="yellow",
        box=HEAVY_EDGE,
        title_align="center"
    ))

    while True:
        try:
            chedo = int(Prompt.ask(f" ✈ [bold cyan]Chọn lựa chọn[/bold cyan]").strip())
            if chedo in [1, 2, 12]:
                break
            else:
                console.print("[bold red]Chỉ được nhập 1, 2 hoặc 12![/bold red]")
        except ValueError:
            console.print("[bold red]Nhập vào 1 số!!![/bold red]")

    lam = []
    if chedo == 1:
        lam = ["follow"]
    elif chedo == 2:
        lam = ["like"]
    elif chedo == 12:
        lam = ["follow", "like"]
        
    # --- LƯU CẤU HÌNH MỚI ---
    new_config = {
        "delay": delay,
        "lannhan_lan2": lannhan_confirm,
        "doiacc_fail_limit": doiacc,
        "job_success_limit": job_limit,
        "job_ratio": job_ratio,
        "chedo_job": chedo,
        "ai_autobot": ai_autobot,
        "scroll_duration": scroll_duration
    }
    save_config(new_config)
    console.print("✔ [bold green]Đã lưu cấu hình mới vào config.json.[/bold green]")
    time.sleep(1)
    # -------------------------
        
    return delay, lannhan, doiacc, lam, job_limit, job_ratio, ai_autobot, scroll_duration

# --- HÀM MAIN_LOOP ĐÃ SỬA LỖI LOGIC BỎ QUA JOB KHÔNG CẦN THIẾT VÀ THÊM NOTIFICATION ---
def main_loop(accounts: list, delay: int, lannhan: str, doiacc_limit: int, lam: list, authorization: str, job_success_limit: int, job_ratio: str, ai_autobot: bool, scroll_duration: int): 
    """Vòng lặp xử lý nhiệm vụ chính, chạy luân phiên giữa các tài khoản và loại job."""
    
    dem = 0
    tong = 0
    
    account_cycler = itertools.cycle(accounts)
    job_cycler = create_job_cycler(job_ratio, lam) 
    
    log_table = Table(
        title="[bold magenta]📜 BẢNG LOG NHIỆM VỤ 📜[/bold magenta]", 
        border_style="bold magenta",
        show_lines=True 
    )
    log_table.add_column("STT", justify="center", style="bold yellow")
    log_table.add_column("Thời gian", justify="center", style="bold white")
    log_table.add_column("Tài khoản", justify="center", style="bold cyan")
    log_table.add_column("Status", justify="center", style="bold green")
    log_table.add_column("Xu", justify="center", style="bold magenta")
    log_table.add_column("Tổng", justify="center", style="bold yellow")
    
    spinner = itertools.cycle([
        "⚡", "🚀", "💻", "🔥", "⏳",
        "🛠️", "🛰️", "🔒", "🔓", "📡",
        "🧩", "🔧", "✨", "⚙️", "🧨",
        "🪄", "👾", "🕶️", "🎯", "💣",
        "🖥️"
    ])
    colors = [
        "red", "magenta", "cyan", "green", "yellow", "blue", "white"
    ]
    
    def display_ui_and_log():
        """Hàm dùng để in lại toàn bộ UI và Log"""
        clear_screen()
        display_banner()
        display_current_info(authorization)
        
        console.print("[bold yellow]════════════════════════════════════════════════[/bold yellow]")
        
        console.print(Panel(
            log_table, 
            border_style="magenta",
            title_align="center",
            box=HEAVY_EDGE
        ))

    display_ui_and_log()
    
    while True:
        current_acc = next(account_cycler)
        account_id = current_acc['id']
        username = current_acc['username']
        current_cookies = current_acc['cookies']
        
        # 1. Check LOCK status 
        if current_acc['is_locked']:
            if time.time() < current_acc['lock_until']:
                remaining_time = int(current_acc['lock_until'] - time.time())
                console.print(f"⚠️ [bold red]Tài khoản [bold cyan]{username}[/bold cyan] đang bị tạm ngưng. Mở lại sau {remaining_time}s. Chuyển acc...[/bold red]")
                time.sleep(1)
                continue
            else:
                # Mở khóa tài khoản
                current_acc['is_locked'] = False
                current_acc['lock_until'] = 0
                console.print(f"✅ [bold green]Tài khoản [bold cyan]{username}[/bold cyan] đã hết thời gian tạm ngưng. Bắt đầu lại...[/bold green]")
                time.sleep(1)
                
        # 2. Check fail_count và chuyển tài khoản (nếu cần)
        if current_acc['fail_count'] >= doiacc_limit:
            fail_message = Text("\nJob fail của ", style="bold red")
            fail_message.append(username, style="bold cyan")
            fail_message.append(f" đã đạt giới hạn (", style="bold red")
            fail_message.append(f"{doiacc_limit}", style="bold yellow")
            fail_message.append(")!", style="bold red")
            fail_message.append(" Bỏ qua tài khoản này trong 1 lượt.", style="bold red")
            console.print(fail_message)

            current_acc['fail_count'] = 0 
            time.sleep(1)
            continue 
            
        # --- Check Job Thành công Limit ---
        if current_acc['success_count'] >= job_success_limit:
            success_message = Text("\n✔ Tài khoản ", style="bold yellow")
            success_message.append(username, style="bold cyan")
            success_message.append(" đã hoàn thành ", style="bold yellow")
            success_message.append(str(job_success_limit), style="bold green")
            success_message.append(" jobs. Đổi sang tài khoản tiếp theo.", style="bold yellow")
            console.print(success_message)
            
            # 📢 THÔNG BÁO TELEGRAM: ĐẠT GIỚI HẠN JOB THÀNH CÔNG
            telegram_limit_message = f"""
📈 <b>ĐẠT GIỚI HẠN JOB THÀNH CÔNG</b>
- Tài khoản: <code>{username}</code>
- Trạng thái: Đã hoàn thành {job_success_limit} jobs.
- Hành động: Tự động chuyển sang tài khoản tiếp theo.
"""
            send_telegram_message(telegram_limit_message)

            current_acc['success_count'] = 0 # Reset count
            time.sleep(1)
            continue
        # ----------------------------------

        # Lấy loại job mong muốn theo chu kỳ (Vẫn lấy để duy trì thứ tự luân phiên)
        desired_job_type = next(job_cycler)
        
        # 3. Get Job - Sử dụng console.status
        with console.status(f"[bold white]Đang Tìm NV [bold green]{desired_job_type}[/bold green] cho [bold cyan]{username}[/bold cyan]:>[/bold white] [bold yellow]Tổng xu: {tong}[/bold yellow]") as status:
            try:
                # Gọi API nhận job, API sẽ trả về job đầu tiên nó tìm thấy (Like hoặc Follow)
                nhanjob = safe_dict_check(nhannv(account_id, authorization), context="Get Job")
            except Exception as e:
                nhanjob = {"status": 500, "message": f"Failed to get job (exception outside of nhannv): {e}"}
            
            if nhanjob.get("critical_safe_check_fail"):
                 status.update(f"❌ [bold red]Lỗi dữ liệu nghiêm trọng cho [bold cyan]{username}[/bold cyan]. Bỏ qua.[/bold red]")
                 time.sleep(1)
                 continue
            
            job_data = nhanjob.get("data")
            if nhanjob.get("status") != 200 or not job_data:
                # 📢 THÔNG BÁO TELEGRAM: HẾT JOB
                if nhanjob.get("status") == 400:
                    status.update(f"❌ [bold red]Hết Job cho [bold cyan]{username}[/bold cyan]: [bold yellow]{nhanjob.get('detail', nhanjob.get('message', 'Lỗi không rõ'))}. Chuyển acc...[/bold yellow]")
                else:
                    status.update(f"[bold yellow]Không tìm thấy nhiệm vụ cho [bold cyan]{username}[/bold cyan]. Chuyển acc...[/bold yellow]")
                time.sleep(1)
                continue
                
            ads_id = job_data.get("id")
            link = job_data.get("link")
            object_id = job_data.get("object_id")
            loai = job_data.get("type") # Loại job mà GoLike thực sự trả về
            
            # ❗ PHẦN SỬA LỖI QUAN TRỌNG: BỎ QUA JOB KHÔNG ĐƯỢC CHỌN
            if loai not in lam:
                try:
                    baoloi(ads_id, object_id, account_id, loai, authorization)
                    status.update(f"[bold red]Đã bỏ qua job {loai} (Không nằm trong chế độ đã chọn {', '.join(lam)})! Tiếp tục tìm {desired_job_type}...[/bold red]")
                    time.sleep(1)
                    continue
                except Exception:
                    pass
            # -------------------------------------------------------------
                
            # 4. Execute Job (Follow/Like)
            status.update(f"[bold white]Đã nhận job [bold magenta]{loai}[/bold magenta] ({object_id}). Đang thực hiện bằng [bold cyan]{username}[/bold cyan]...[/bold white]")
            success = False
            new_cookies_from_job = current_cookies 
            
            if loai == "follow":
                success, new_cookies_from_job = handle_follow_job(current_acc, object_id)
            elif loai == "like":
                # ---- XỬ LÝ DỮ LIỆU JOB LIKE (ĐÃ SỬA LỖI TRÍCH XUẤT media_id) ----
                obj_data = job_data.get("object_data", {})
                
                if isinstance(obj_data, str):
                    try:
                        obj_data = json.loads(obj_data)
                    except json.JSONDecodeError:
                        console.print(f"⚠️ [bold red]Bỏ qua job like: object_data là chuỗi nhưng không phải JSON hợp lệ. object_data: {obj_data[:50]}...[/bold red]")
                        current_acc['fail_count'] += 1
                        time.sleep(1)
                        continue
                
                if not isinstance(obj_data, dict):
                    obj_data = {}

                media_id = None
                try:
                    media_id = obj_data.get("pk") or object_id
                except Exception:
                    media_id = object_id

                if media_id:
                    success, new_cookies_from_job = handle_like_job(current_acc, media_id, link)
                else:
                    console.print("❌ [bold red]Lỗi: Không tìm thấy media_id cho job like.[/bold red]")
                    success = False
            
            # CẬP NHẬT COOKIES VÀO CẤU TRÚC ACCOUNTS_LIST VÀ FILE
            if new_cookies_from_job != current_cookies:
                current_acc['cookies'] = new_cookies_from_job
                safe_file_rw(get_cookie_file_path(username), 'w', new_cookies_from_job)
                
            # If IG job failed (và không bị khóa), skip GoLike job
            if not success and not current_acc['is_locked']: 
                try:
                    baoloi(ads_id, object_id, account_id, loai, authorization)
                    status.update(f"❌ [bold red]Đã báo lỗi (Fail IG) và bỏ qua job {loai}! Tài khoản [bold cyan]{username}[/bold cyan] fail +1.[/bold red]")
                    
                    # 📢 THÔNG BÁO TELEGRAM: LỖI THỰC THI JOB
                    telegram_job_fail_message = f"""
❌ <b>LỖI THỰC THI JOB IG</b>
- Tài khoản: <code>{username}</code>
- Loại Job: {loai.upper()}
- ID Job: <code>{object_id}</code>
- Lý do: Thực hiện trên IG thất bại/Job đã bị xóa.
"""
                    send_telegram_message(telegram_job_fail_message)

                    current_acc['fail_count'] += 1
                    time.sleep(1)
                    continue
                except Exception:
                    status.update(f"❌ [bold red]Lỗi khi báo lỗi job![/bold red]")
                    current_acc['fail_count'] += 1
                    time.sleep(1)
                    continue
            
            # Nếu job thất bại do bị khóa tài khoản (checkpoint), chỉ cần continue
            if current_acc['is_locked']:
                 continue
                 
            # 5. AI AutoBot: Lướt và cuộn trang sau khi hoàn thành job
            if ai_autobot and success:
                status.update(f"🤖 [bold cyan]AI AutoBot đang hoạt động cho {username}...[/bold cyan]")
                ai_autobot_scroll_and_browse(username, current_acc['cookies'], scroll_duration)
            
            # 6. Delay nhận tiền
            for i in range(delay, 0, -1):
                icon = next(spinner)
                color = colors[i % len(colors)]
                status.update(f"[bold {color}]{icon} Như Anh Đã Thấy Em {i:02d}s còn lại...[/bold {color}]")
                time.sleep(1)
            
            # 7. Complete Job (Nhận tiền)
            ok = False
            nhantien = {}
            for lan in range(1, 3):
                if lan == 2 and lannhan == "n":
                    break
                
                status.update(f"[bold white]Đang Nhận Tiền Lần {lan}:>[/bold white]")
                try:
                    nhantien = safe_dict_check(hoanthanh(ads_id, account_id, authorization), context="Complete Job")
                except Exception as e:
                    nhantien = {"status": 500, "message": f"Lỗi khi hoàn thành job (exception): {e}"} 
                
                if nhantien.get("critical_safe_check_fail"):
                    status.update(f"❌ [bold red]Lỗi dữ liệu nghiêm trọng khi nhận tiền. Bỏ qua.[/bold red]")
                    break

                if nhantien.get("status") == 200 and nhantien.get("data"):
                    ok = True
                    dem += 1
                    tien = nhantien["data"]["prices"]
                    tong += tien
                    local_time = time.strftime("%H:%M:%S")
                    
                    log_table.add_row(
                        str(dem),
                        local_time,
                        f"[bold cyan]{username}[/bold cyan]",
                        "[bold green]SUCCESS[/bold green]", 
                        f"[bold magenta]+{tien}[/bold magenta]", 
                        f"[bold yellow]{tong}[/bold yellow]"
                    )
                    
                    # 📢 THÔNG BÁO TELEGRAM: HOÀN THÀNH JOB
                    telegram_success_message = f"""
✅ <b>HOÀN THÀNH JOB THÀNH CÔNG!</b>
- Tài khoản: <code>{username}</code>
- Loại Job: {loai.upper()}
- Tiền Nhận: <b>+{tien} Xu</b>
- Tổng Xu: <b>{tong} Xu</b>
"""
                    send_telegram_message(telegram_success_message)

                    display_ui_and_log()
                    current_acc['fail_count'] = 0 
                    current_acc['success_count'] += 1
                    break
                else:
                    if lan == 1 and lannhan == "y":
                        time.sleep(2)
                        continue
                    break 

            if not ok:
                try:
                    baoloi(ads_id, object_id, account_id, loai, authorization)
                    status.update(f"❌ [bold red]Đã bỏ qua job (Lỗi nhận tiền)! Tài khoản [bold cyan]{username}[/bold cyan] fail +1.[/bold red]")
                    
                    # 📢 THÔNG BÁO TELEGRAM: LỖI NHẬN TIỀN
                    error_detail = nhantien.get('error', nhantien.get('message', 'Lỗi không rõ'))
                    telegram_complete_fail_message = f"""
❌ <b>LỖI NHẬN TIỀN</b>
- Tài khoản: <code>{username}</code>
- Loại Job: {loai.upper()}
- ID Job: <code>{object_id}</code>
- Lý do: {error_detail}
- Hành động: Đã báo lỗi và bỏ qua job.
"""
                    send_telegram_message(telegram_complete_fail_message)

                    current_acc['fail_count'] += 1
                    time.sleep(1)
                except Exception:
                    status.update("[bold red]❌ Lỗi khi báo lỗi job![/bold red]")
                    current_acc['fail_count'] += 1
                    time.sleep(1)

# --- MENU CHÍNH ĐÃ SỬA LỖI PANEL ---

def display_main_menu_and_get_choice():
    """Hiển thị menu chính và lấy lựa chọn của người dùng."""
    console.clear()
    display_banner()
    
    # Sửa lỗi: Gộp các dòng menu vào một đối tượng Text duy nhất
    menu_text = Text()
    menu_text.append("1. Khởi động BOT GoLike IG\n", style="bold green")
    menu_text.append("2. Công cụ tìm Chat ID Telegram\n", style="bold magenta")
    menu_text.append("3. Quản lý Proxy\n", style="bold cyan")   # Thêm dòng này
    menu_text.append("4. Thêm tài khoản Instagram mới\n", style="bold yellow")  # Thêm dòng mới
    menu_text.append("5. Thoát", style="bold red")

    console.print(Panel(
        menu_text, # Chỉ truyền một đối tượng nội dung
        title="[bold yellow]MENU CHÍNH[/bold yellow]", # Sử dụng tham số title cho tiêu đề
        border_style="cyan"
    ))
    return Prompt.ask("Chọn chức năng bạn muốn chạy", choices=['1', '2', '3', '4', '5'])  # Thêm lựa chọn '4'

# --- HÀM THÊM TÀI KHOẢN MỚI (GỘP TỪ addiggo.py) ---

def add_new_instagram_account():
    """Chức năng thêm tài khoản Instagram mới (giống addiggo.py)."""
    display_banner()
    
    console.print("[bold cyan]🔐 THÊM TÀI KHOẢN INSTAGRAM MỚI[/bold cyan]")
    
    # Nhập Authorization
    auth = safe_file_rw(AUTHORIZATION_FILE, 'r')
    if not auth:
        console.print("[bold red]❌ Chưa có Authorization! Vui lòng cấu hình Authorization trước.[/bold red]")
        time.sleep(2)
        return
    
    console.print("\n[bold yellow]Chọn phương thức thêm tài khoản:[/bold yellow]")
    console.print("1. Đăng nhập bằng Cookie (đã có sẵn)")
    console.print("2. Đăng nhập bằng Tài khoản/Mật khẩu")
    
    choice = Prompt.ask(" ✈ [bold cyan]Chọn phương thức (1/2)[/bold cyan]", choices=['1', '2']).strip()
    
    if choice == '1':
        # Phương thức Cookie
        cookies = Prompt.ask(" ✈ [bold cyan]Nhập Cookies Instagram[/bold cyan]").strip()
        if not cookies:
            console.print("[bold red]❌ Cookies không được để trống![/bold red]")
            time.sleep(2)
            return
        
        # Lấy thông tin từ cookies
        username, user_id, csrftoken = get_account_info_from_cookies(cookies)
        if not username:
            console.print("[bold red]❌ Không thể lấy thông tin từ cookies![/bold red]")
            time.sleep(2)
            return
        
        # Thêm vào Golike
        proxy_dict = get_account_proxy(username)
        if add_account_to_golike(username, auth, cookies, proxy_dict):
            console.print(f"✅ [bold green]Tài khoản {username} đã được thêm vào Golike thành công![/bold green]")
            # Lưu cookies
            safe_file_rw(get_cookie_file_path(username), 'w', cookies)
            console.print(f"✅ [bold green]Đã lưu cookies vào file: cookies_{username}.txt[/bold green]")
        else:
            console.print(f"❌ [bold red]Không thể thêm tài khoản {username} vào Golike![/bold red]")
    
    elif choice == '2':
        # Phương thức Tài khoản/Mật khẩu
        username = Prompt.ask(" ✈ [bold cyan]Nhập Username Instagram[/bold cyan]").strip()
        if not username:
            console.print("[bold red]❌ Username không được để trống![/bold red]")
            time.sleep(2)
            return
        
        # Đăng nhập và thêm vào Golike
        login_with_account(username, auth)
    
    time.sleep(3)

if __name__ == "__main__":
    
    # KHI CHẠY, SẼ KIỂM TRA LỖI HARDCODE TOKEN TRƯỚC
    if GLOBAL_TELEGRAM_TOKEN == "YOUR_HARDCODED_TELEGRAM_BOT_TOKEN_HERE":
        console.print("\n\n⚠️ [bold red]LỖI CẤU HÌNH NGHIÊM TRỌNG (CHỦ TOOL):[/bold red]")
        console.print("[bold yellow]Bạn chưa thay Token Bot chủ trong biến GLOBAL_TELEGRAM_TOKEN. [/bold yellow]")
        console.print("[bold yellow]Thông báo Telegram sẽ không hoạt động cho đến khi bạn sửa lỗi này.[/bold yellow]")
        time.sleep(5)
    
    while True:
        choice = display_main_menu_and_get_choice()

        if choice == '5':
            console.print("[bold red]👋 Tạm biệt. Chương trình dừng lại.[/bold red]")
            sys.exit(0)
        
        elif choice == '4':
            add_new_instagram_account()
            # Quay lại menu sau khi hoàn thành
            continue
        
        elif choice == '3':
            proxy_management_menu(ACCOUNTS_LIST)
            # Quay lại menu sau khi hoàn thành
            continue

        elif choice == '2':
            tool_get_chat_id()
            # Quay lại menu sau khi hoàn thành
            continue

        elif choice == '1':
            break # Thoát vòng lặp menu để bắt đầu chạy bot
    
    # BẮT ĐẦU CHẠY BOT
    try:
        clear_screen()
        
        # 1. Get User-Agent
        get_user_agent()
        
        # 2. Get Authorization
        AUTH = get_authorization()
        
        # 3. Get Telegram Config (chỉ cần Chat ID trong bộ nhớ)
        get_telegram_config()
        
        # 4. Run initial account check
        console.print("🚀 [bold green]Đăng nhập thành công! Đang vào Tool Instagram...[/bold green]")
        time.sleep(1)
        chontk_Instagram = safe_dict_check(chonacc(AUTH), context="chonacc API") 
        
        # 5. Select Account(s) and get Cookies
        ACCOUNTS = dsacc(chontk_Instagram, AUTH)
        
        if not ACCOUNTS:
            console.print("\n[bold red]Chưa có tài khoản Instagram nào được chọn hoặc có Cookies hợp lệ. Chương trình dừng lại.[/bold red]")
            sys.exit(1)

        # 6. Get User Settings (Đã tích hợp Load/Save Config)
        display_banner()
        display_current_info(AUTH)
        DELAY, LANNHAN, DOIACC_LIMIT, LAM, JOB_SUCCESS_LIMIT, JOB_RATIO, AI_AUTOBOT, SCROLL_DURATION = get_user_settings()

        # 7. Start Main Loop 
        main_loop(ACCOUNTS, DELAY, LANNHAN, DOIACC_LIMIT, LAM, AUTH, JOB_SUCCESS_LIMIT, JOB_RATIO, AI_AUTOBOT, SCROLL_DURATION)

    except KeyboardInterrupt:
        console.print("\n[bold red]👋 Chương trình đã dừng bởi người dùng.[/bold red]")
    except Exception as e:
        # --- KHỐI CODE GỬI LỖI HỆ THỐNG VÀO TELEGRAM ---
        error_text = Text("\n❌ CÓ LỖI NGHIÊM TRỌNG XẢY RA! ❌\n", style="bold red")
        escaped_error_message = str(e)
        
        error_text.append(f"Lỗi: {escaped_error_message}\n", style="red") 
        error_text.append("\nChi tiết lỗi (Traceback):", style="bold yellow")
        
        console.print(error_text)
        
        # Gửi thông báo lỗi hệ thống qua Telegram
        telegram_message = f"""
🔥 <b>LỖI HỆ THỐNG BOT NGHIÊM TRỌNG!</b> 🔥
- Bot đã dừng chạy.
- Lỗi chi tiết: <b>{escaped_error_message[:100]}...</b>
- Hành động: Vui lòng kiểm tra console để xem chi tiết lỗi.
"""
        send_telegram_message(telegram_message)

        # In Traceback ra console
        traceback_string = traceback.format_exc()
        console.print(Text(traceback_string, style="dim")) 
        
        sys.exit(1)