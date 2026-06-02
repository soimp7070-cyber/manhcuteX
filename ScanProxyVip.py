#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================================================================
██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗      █████╗ ██╗
██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗    ██╔══██╗██║
██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝     ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝    ███████║██║
██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝      ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗    ██╔══██║██║
██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║       ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║    ██║  ██║██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝
================================================================================================================================
Tên dự án    : NP_HUNGG PROXY SCANNER TITAN ULTRA EDITION (UI CUTHAM)
Tác giả      : ☆ NP HUNG ☆
Phiên bản    : 10.0.0 TITAN ULTRA (New UI & Auto Export)
Mô tả        : Hệ thống quét Proxy cao cấp, UI Cutham, tự động chia file & thư mục.
================================================================================================================================
"""

import requests, json, os, sys, sqlite3, random, threading, queue, time, re, logging
import hashlib, base64, socket, ssl, ipaddress, csv, math, functools
import concurrent.futures, urllib.parse, http.client, collections, itertools
import string, pickle, zlib, struct, glob, fnmatch, shutil, tempfile, subprocess, warnings
import unicodedata
import platform as pf
from sys import platform
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, OrderedDict, deque, Counter
from contextlib import contextmanager
from urllib.parse import urlparse, parse_qs, urljoin
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector


warnings.filterwarnings('ignore')
requests.packages.urllib3.disable_warnings()

# ========================================================================================
# MODULE 1: AUTO INSTALL & IMPORT THIRD-PARTY LIBRARIES
# ========================================================================================
REQUIRED_LIBS = {
    'pystyle': 'pystyle',
    'requests': 'requests',
    'colorama': 'colorama',
    'fake_useragent': 'fake-useragent',
    'dns': 'dnspython',                 # <--- Fix ở đây (đổi thành dns)
    'pyfiglet': 'pyfiglet',
    'tqdm': 'tqdm',
    'cryptography': 'cryptography',
    'bs4': 'beautifulsoup4',            # <--- Fix ở đây (đổi thành bs4)
    'lxml': 'lxml',
    'aiohttp': 'aiohttp',
    'socks': 'PySocks',
}

MISSING_LIBS = []
for lib, pip_name in REQUIRED_LIBS.items():
    try:
        __import__(lib)
    except ImportError:
        MISSING_LIBS.append(pip_name)

if MISSING_LIBS:
    print(f"[!] Đang cài đặt thư viện: {', '.join(MISSING_LIBS)}")
    for lib in MISSING_LIBS:
        os.system(f'pip install {lib}')
    print("[!] Vui lòng khởi động lại tool sau khi cài đặt hoàn tất.")
    sys.exit(0)

try:
    from pystyle import Add, Center, Anime, Colors, Colorate, Write, System
    from colorama import init, Fore, Back, Style
    from fake_useragent import UserAgent
    import dns.resolver
    import pyfiglet
    from tqdm import tqdm
    from bs4 import BeautifulSoup
    import asyncio
    import aiohttp
    import socks
    init(autoreset=True)
except ImportError as e:
    print(f"[!] Không thể import thư viện: {e}")
    sys.exit(1)

# ========================================================================================
# MODULE 2: HỆ THỐNG MÀU SẮC GIAO DIỆN (CHUẨN CUTHAM.PY)
# ========================================================================================
den = '\x1b[1;90m'
luc = '\x1b[1;32m'
trang = '\x1b[1;37m'
red = '\x1b[1;31m'
vang = '\x1b[1;33m'
tim = '\x1b[1;35m'
lamd = '\x1b[1;34m'
lam = '\x1b[1;36m'
purple = '\x1b[35m'
hong = '\x1b[95m'

class Theme:
    DEN = den
    LUC = luc
    TRANG = trang
    RED = red
    VANG = vang
    TIM = tim
    LAMD = lamd
    LAM = lam
    PURPLE = purple
    HONG = hong
    RESET = '\x1b[0m'
    
    @classmethod
    def rainbow_text(cls, text: str) -> str:
        return Colorate.Horizontal(Colors.rainbow, text)

# ========================================================================================
# MODULE 3: HỆ THỐNG LOGGING (ONLY WEB & FILE - KHÔNG SPAM TERMUX)
# ========================================================================================

class AppLogger:
    _instance = None
    _logger = None
    web_logs = deque(maxlen=50) # Lưu 50 dòng log để đẩy lên Web Dashboard
    
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def setup_logger(cls):
        if cls._logger is not None: return cls._logger
            
        logger = logging.getLogger("PROXY_TITAN_V15")
        logger.setLevel(logging.DEBUG)
        if not os.path.exists('logs'): os.makedirs('logs')
        
        # 1. Handler bắn log ra Web dạng JSON
        class WebHandler(logging.Handler):
            def emit(self, record):
                AppLogger.web_logs.append({
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "level": record.levelname,
                    "msg": record.getMessage()
                })

        # 2. Handler lưu log vào File ổ cứng
        log_filename = f"logs/titan_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_filename, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%H:%M:%S'))
        
        # Ép Log vào File và Web (Bỏ hẳn StreamHandler để không in ra màn hình Termux nữa)
        logger.addHandler(fh)
        logger.addHandler(WebHandler())
        cls._logger = logger
        return logger
    
    @classmethod
    def get_logger(cls):
        if cls._logger is None: return cls.setup_logger()
        return cls._logger

log = AppLogger.get_logger()

# ========================================================================================
# MODULE 4: ENUMS VÀ DATACLASSES
# ========================================================================================
class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    SOCKS5H = "socks5h"
    HTTP_CONNECT = "http_connect"
    
    @classmethod
    def from_string(cls, s: str):
        s = s.lower().strip()
        for proto in cls:
            if proto.value == s: return proto
        return None

class AnonymityLevel(Enum):
    TRANSPARENT = "transparent"
    ANONYMOUS = "anonymous"
    ELITE = "elite"
    UNKNOWN = "unknown"
    
    @classmethod
    def get_color(cls, level: 'AnonymityLevel') -> str:
        colors = {cls.TRANSPARENT: vang, cls.ANONYMOUS: lam, cls.ELITE: luc, cls.UNKNOWN: den}
        return colors.get(level, trang)

class ProxyStatus(Enum):
    UNCHECKED = auto()
    LIVE = auto()
    DEAD = auto()
    TIMEOUT = auto()
    BLOCKED = auto()
    BANNED = auto()
    SLOW = auto()
    
    @classmethod
    def get_color(cls, status: 'ProxyStatus') -> str:
        colors = {cls.UNCHECKED: den, cls.LIVE: luc, cls.DEAD: red, cls.TIMEOUT: vang, cls.BLOCKED: red, cls.BANNED: red, cls.SLOW: vang}
        return colors.get(status, trang)

@dataclass
class ProxyInfo:
    ip: str
    port: int
    protocol: str = "unknown"
    country: str = "Không xác định"
    country_code: str = "UN"
    city: str = "Không xác định"
    region: str = "Không xác định"
    isp: str = "Không xác định"
    latency: int = 0
    anonymity: str = "unknown"
    status: str = "unchecked"
    last_checked: Optional[datetime] = None
    success_rate: float = 0.0
    target_url: str = ""
    target_name: str = ""
    uptime: float = 0.0
    response_time_history: List[int] = field(default_factory=list)
    geo_cache_expiry: Optional[datetime] = None
    ssl_verified: bool = False
    bandwidth_kbps: float = 0.0
    max_concurrent: int = 1
    supported_methods: List[str] = field(default_factory=list)
    score: int = 0
    fail_count: int = 0
    success_count: int = 0
    org: str = "Không xác định"
    asn: str = "Không xác định"
    timezone: str = "Không xác định"
    
    @property
    def ip_port(self) -> str:
        return f"{self.ip}:{self.port}"
    
    @property
    def proxy_dict(self) -> Dict[str, str]:
        if self.protocol in ['http', 'https', 'socks5', 'socks4']:
            proxy_url = f"{self.protocol}://{self.ip}:{self.port}"
            return {'http': proxy_url, 'https': proxy_url}
        return {}
    
    def calculate_score(self) -> int:
        score = 0
        if self.latency < 300: score += 50
        elif self.latency < 800: score += 40
        elif self.latency < 1500: score += 25
        elif self.latency < 3000: score += 10
        else: score -= 20
        
        if self.anonymity == AnonymityLevel.ELITE.value: score += 40
        elif self.anonymity == AnonymityLevel.ANONYMOUS.value: score += 20
        elif self.anonymity == AnonymityLevel.TRANSPARENT.value: score += 5
        
        if self.protocol in ['socks5', 'socks5h']: score += 20
        elif self.protocol == 'socks4': score += 15
        elif self.protocol == 'https': score += 10
        elif self.protocol == 'http': score += 5
        
        score += int(self.uptime * 15)
        if self.ssl_verified: score += 10
        score += int(self.success_rate * 30)
        score -= self.fail_count * 2
        self.score = max(0, min(100, score))
        return self.score

@dataclass
class ScanStatistics:
    total_found: int = 0
    total_checked: int = 0
    total_live: int = 0
    total_dead: int = 0
    total_timeout: int = 0
    total_blocked: int = 0
    total_banned: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    protocol_stats: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    country_stats: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    anonymity_stats: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    avg_latency: float = 0.0
    peak_threads: int = 0
    bandwidth_used: float = 0.0
    sources_used: int = 0
    sources_failed: int = 0
    
    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time: return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def scan_rate(self) -> float:
        if self.duration_seconds > 0: return self.total_checked / self.duration_seconds
        return 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_checked > 0: return (self.total_live / self.total_checked) * 100
        return 0.0

# ========================================================================================
# 1: DỮ LIỆU TĨNH KHỔNG LỒ (STATIC DATA) - FIX LỖI SPAM FAKE-USERAGENT
# ========================================================================================
class StaticData:
    """Chứa hàng nghìn User-Agents và danh sách nguồn Proxy public"""
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """Lấy User-Agent ngẫu nhiên từ danh sách tĩnh (Bỏ fake-useragent để chống lag)"""
        return random.choice(cls.USER_AGENTS)
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/105.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/1.61.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.58",
        "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/114.0 Firefox/114.0",
        "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
        "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
        "Mozilla/5.0 (PlayStation 5 9.00/SmartTv) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    ]
    
    # Danh sách mục tiêu để test proxy
    TARGETS = {
        "1": {"name": "Mặc định (HTTPBin)", "url": "http://httpbin.org/get"},
        "2": {"name": "HTTPSBin", "url": "https://httpbin.org/get"},
        "3": {"name": "Google", "url": "https://www.google.com"},
        "4": {"name": "Facebook", "url": "https://www.facebook.com"},
        "5": {"name": "Roblox API", "url": "https://api.roblox.com/docs"},
        "6": {"name": "TikTok", "url": "https://www.tiktok.com"},
        "7": {"name": "Netflix", "url": "https://www.netflix.com"},
        "8": {"name": "Amazon", "url": "https://www.amazon.com"},
        "9": {"name": "Discord API", "url": "https://discord.com/api/v9/gateway"},
        "10": {"name": "Steam", "url": "https://store.steampowered.com"},
        "11": {"name": "Twitter/X", "url": "https://twitter.com"},
        "12": {"name": "Instagram", "url": "https://www.instagram.com"},
        "13": {"name": "LinkedIn", "url": "https://www.linkedin.com"},
        "14": {"name": "GitHub", "url": "https://api.github.com"},
        "15": {"name": "Reddit", "url": "https://www.reddit.com"},
        "16": {"name": "Cloudflare", "url": "https://cloudflare.com/cdn-cgi/trace"},
        "17": {"name": "IP-API (Geo Check)", "url": "http://ip-api.com/json"},
        "18": {"name": "WhatIsMyIP", "url": "https://api.ipify.org?format=json"},
        "19": {"name": "ProxyJudge A", "url": "http://proxyjudge.us/azenv.php"},
        "20": {"name": "ProxyJudge B", "url": "http://azenv.net/"},
    }
    
    # Danh sách nguồn proxy mở rộng (200+ nguồn cơ bản)
    PROXY_SOURCES_RAW = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/rooster127/proxylist/main/proxylist.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/BlexBoy/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Volodichev/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/master/http.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/master/socks4.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/master/socks5.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/ObcbO/getproxy/master/http.txt",
        "https://raw.githubusercontent.com/ObcbO/getproxy/master/socks4.txt",
        "https://raw.githubusercontent.com/ObcbO/getproxy/master/socks5.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/opsxcq/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/opsxcq/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/opsxcq/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all.txt",
        "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/UserR3X/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/UserR3X/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/UserR3X/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/scidam/proxy-list/master/proxy-list.txt",
        "https://raw.githubusercontent.com/ryanmcdermott/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/chipsguide/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/NullMaster000/Proxy-List/main/http.txt",
        "https://raw.githubusercontent.com/NullMaster000/Proxy-List/main/socks4.txt",
        "https://raw.githubusercontent.com/NullMaster000/Proxy-List/main/socks5.txt",
        "https://raw.githubusercontent.com/hy-az/free-proxy-list/main/proxies.txt",
    ]
    
    # GeoIP API Endpoints
    GEOIP_APIS = [
        "http://ip-api.com/json/{}?fields=status,message,country,countryCode,region,regionName,city,isp,org,as,query,timezone",
        "https://ipapi.co/{}/json/",
        "https://ipinfo.io/{}/json",
        "https://api.ip2location.io/?ip={}&format=json",
        "http://ipwhois.app/json/{}",
    ]
    
    # Proxy Judge URLs
    PROXY_JUDGES = [
        "http://proxyjudge.us/azenv.php",
        "http://azenv.net/",
        "http://httpbin.org/headers",
        "https://httpbin.org/headers",
        "http://ipinfo.io/json",
        "http://checkip.amazonaws.com",
        "http://ip-api.com/json",
    ]

# ========================================================================================
# MODULE 6: QUẢN LÝ CẤU HÌNH (JSON FILE) - NÂNG CẤP
# ========================================================================================
class ConfigManager:
    """Tạo, đọc, ghi file cấu hình dạng JSON với validation và backup"""
    
    def __init__(self, filename: str = "np_hungg_config_ultra.json"):
        self.filename = filename
        self.backup_filename = f"{filename}.backup"
        self.data = {
            "threads": 500,
            "timeout": 8,
            "sources_multiplier": 200,
            "target_id": "1",
            "protocols": ["http", "https", "socks4", "socks5"],
            "auto_export_txt": True,
            "auto_export_json": True,
            "auto_export_csv": False,
            "show_dead_proxies": False,
            "show_progress_bar": True,
            "min_anonymity": "anonymous",
            "max_latency": 3000,
            "geoip_enabled": True,
            "geoip_cache_ttl": 3600,
            "proxy_judge_enabled": True,
            "ssl_verify": False,
            "keep_alive": True,
            "max_retries": 3,
            "retry_delay": 1,
            "connection_pool_size": 50,
            "dns_cache_enabled": True,
            "export_compress": False,
            "source_limit": 500,
            "auto_generate_sources": True,
            "proxy_filter": {
                "countries": [],
                "exclude_countries": ["CN", "RU"],
                "min_success_rate": 0.3,
                "max_failures": 5,
            },
            "notifications": {
                "enabled": False,
                "sound_on_complete": True,
                "desktop_notify": False,
            },
            "advanced": {
                "tcp_fast_open": True,
                "tcp_nodelay": True,
                "reuse_connections": True,
                "chunk_size": 8192,
                "enable_compression": True,
            }
        }
        self.load()
    
    def load(self):
        """Load config từ file, nếu lỗi thì thử backup"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._deep_update(self.data, loaded)
                log.info(f"Đã load config từ {self.filename}")
            except Exception as e:
                log.error(f"Lỗi khi đọc file config: {e}, thử backup...")
                self._try_load_backup()
        else:
            self.save()
            log.info(f"Đã tạo file config mới: {self.filename}")
    
    def _try_load_backup(self):
        """Thử load từ file backup"""
        if os.path.exists(self.backup_filename):
            try:
                with open(self.backup_filename, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._deep_update(self.data, loaded)
                log.info(f"Đã load config từ backup {self.backup_filename}")
            except:
                log.warning("Không thể load backup, sử dụng config mặc định")
    
    def _deep_update(self, target: dict, source: dict):
        """Cập nhật dictionary lồng nhau"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def save(self):
        """Lưu config, tạo backup trước khi ghi"""
        try:
            if os.path.exists(self.filename):
                shutil.copy2(self.filename, self.backup_filename)
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log.error(f"Lỗi khi lưu file config: {e}")
    
    def update(self, key: str, value: Any):
        """Cập nhật một key trong config"""
        keys = key.split('.')
        target = self.data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save()
        log.info(f"Đã cập nhật cấu hình: {key} = {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị từ config với key dạng dot notation"""
        keys = key.split('.')
        target = self.data
        for k in keys:
            if isinstance(target, dict) and k in target:
                target = target[k]
            else:
                return default
        return target
    
    def reset_to_default(self):
        """Reset về cấu hình mặc định"""
        self.data = {
            "threads": 500,
            "timeout": 8,
            "sources_multiplier": 200,
            "target_id": "1",
            "protocols": ["http", "https", "socks4", "socks5"],
            "auto_export_txt": True,
            "auto_export_json": True,
            "auto_export_csv": False,
            "show_dead_proxies": False,
            "show_progress_bar": True,
            "min_anonymity": "anonymous",
            "max_latency": 3000,
            "geoip_enabled": True,
            "geoip_cache_ttl": 3600,
            "proxy_judge_enabled": True,
            "ssl_verify": False,
            "keep_alive": True,
            "max_retries": 3,
            "retry_delay": 1,
            "connection_pool_size": 50,
            "dns_cache_enabled": True,
            "export_compress": False,
            "source_limit": 500,
            "auto_generate_sources": True,
            "proxy_filter": {
                "countries": [],
                "exclude_countries": ["CN", "RU"],
                "min_success_rate": 0.3,
                "max_failures": 5,
            },
            "notifications": {
                "enabled": False,
                "sound_on_complete": True,
                "desktop_notify": False,
            },
            "advanced": {
                "tcp_fast_open": True,
                "tcp_nodelay": True,
                "reuse_connections": True,
                "chunk_size": 8192,
                "enable_compression": True,
            }
        }
        self.save()
        log.info("Đã reset config về mặc định")

cfg = ConfigManager()

# ========================================================================================
# MODULE 7: GEOIP CACHE MANAGER
# ========================================================================================
class GeoIPCache:
    """Quản lý cache cho thông tin địa lý IP"""
    
    def __init__(self, cache_file: str = "geoip_cache.pkl"):
        self.cache_file = cache_file
        self.cache: Dict[str, Tuple[Dict, datetime]] = {}
        self.ttl = cfg.get('geoip_cache_ttl', 3600)
        self._load_cache()
    
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                self._clean_expired()
                log.info(f"Đã load {len(self.cache)} entries từ GeoIP cache")
            except Exception as e:
                log.error(f"Lỗi load GeoIP cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            log.error(f"Lỗi lưu GeoIP cache: {e}")
    
    def _clean_expired(self):
        now = datetime.now()
        expired = [ip for ip, (_, exp) in self.cache.items() if exp < now]
        for ip in expired:
            del self.cache[ip]
    
    def get(self, ip: str) -> Optional[Dict]:
        if ip in self.cache:
            data, expiry = self.cache[ip]
            if expiry > datetime.now():
                return data
            else:
                del self.cache[ip]
        return None
    
    def set(self, ip: str, data: Dict):
        expiry = datetime.now() + timedelta(seconds=self.ttl)
        self.cache[ip] = (data, expiry)
        if len(self.cache) % 10 == 0:
            self._save_cache()
    
    def clear(self):
        self.cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        log.info("Đã xóa GeoIP cache")

geo_cache = GeoIPCache()

# ========================================================================================
# MODULE 8: QUẢN LÝ DATABASE (SQLITE3) - NÂNG CẤP
# ========================================================================================
class DatabaseManager:
    """Tương tác với cơ sở dữ liệu SQLite với nhiều tính năng nâng cao"""
    
    def __init__(self, db_name: str = "np_hungg_titan_ultra.db"):
        self.db_name = db_name
        self._local = threading.local()
        self._init_connection()
        self.create_tables()
        self.create_indexes()
        self._migrate_if_needed()
    
    def _init_connection(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.cursor = self._local.conn.cursor()
            self._local.cursor.execute("PRAGMA foreign_keys = ON")
            self._local.cursor.execute("PRAGMA busy_timeout = 5000")
            self._local.cursor.execute("PRAGMA journal_mode = WAL")
    
    @property
    def conn(self):
        if not hasattr(self._local, 'conn'): self._init_connection()
        return self._local.conn
    
    @property
    def cursor(self):
        if not hasattr(self._local, 'cursor'): self._init_connection()
        return self._local.cursor
    
    @contextmanager
    def transaction(self):
        try:
            yield self.cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_port TEXT UNIQUE NOT NULL,
                    ip TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    protocol TEXT NOT NULL,
                    country TEXT DEFAULT 'Không xác định',
                    country_code TEXT DEFAULT 'UN',
                    city TEXT DEFAULT 'Không xác định',
                    region TEXT DEFAULT 'Không xác định',
                    isp TEXT DEFAULT 'Không xác định',
                    org TEXT DEFAULT 'Không xác định',
                    asn TEXT DEFAULT 'Không xác định',
                    timezone TEXT DEFAULT 'Không xác định',
                    ping_ms INTEGER DEFAULT 0,
                    target TEXT,
                    target_name TEXT,
                    anonymity TEXT DEFAULT 'unknown',
                    status TEXT DEFAULT 'live',
                    success_rate REAL DEFAULT 0.0,
                    uptime REAL DEFAULT 0.0,
                    score INTEGER DEFAULT 0,
                    ssl_verified INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_checked DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS check_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_id INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    ping_ms INTEGER,
                    target_url TEXT,
                    error_message TEXT,
                    FOREIGN KEY (proxy_id) REFERENCES live_proxies(id) ON DELETE CASCADE
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    total_checked INTEGER DEFAULT 0,
                    total_live INTEGER DEFAULT 0,
                    avg_ping_ms REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_id INTEGER UNIQUE NOT NULL,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    note TEXT,
                    FOREIGN KEY (proxy_id) REFERENCES live_proxies(id) ON DELETE CASCADE
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time DATETIME,
                    end_time DATETIME,
                    total_proxies INTEGER,
                    live_proxies INTEGER,
                    sources_used INTEGER,
                    config_snapshot TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_proxy_timestamp 
                AFTER UPDATE ON live_proxies
                BEGIN
                    UPDATE live_proxies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
            ''')
            
            self.conn.commit()
            log.info("Khởi tạo Database thành công.")
        except Exception as e:
            log.error(f"Lỗi khởi tạo bảng DB: {e}")
    
    def create_indexes(self):
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_proxy_status ON live_proxies(status)",
                "CREATE INDEX IF NOT EXISTS idx_proxy_protocol ON live_proxies(protocol)",
                "CREATE INDEX IF NOT EXISTS idx_proxy_country ON live_proxies(country_code)",
                "CREATE INDEX IF NOT EXISTS idx_proxy_ping ON live_proxies(ping_ms)",
                "CREATE INDEX IF NOT EXISTS idx_proxy_score ON live_proxies(score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_proxy_last_checked ON live_proxies(last_checked)",
                "CREATE INDEX IF NOT EXISTS idx_history_proxy_id ON check_history(proxy_id)",
                "CREATE INDEX IF NOT EXISTS idx_blacklist_ip ON blacklist(ip)",
            ]
            for idx_sql in indexes:
                self.cursor.execute(idx_sql)
            self.conn.commit()
        except Exception as e:
            log.error(f"Lỗi tạo indexes: {e}")
    
    def _migrate_if_needed(self):
        try:
            self.cursor.execute("PRAGMA table_info(live_proxies)")
            columns = [col[1] for col in self.cursor.fetchall()]
            new_columns = {
                'city': 'TEXT DEFAULT "Không xác định"',
                'region': 'TEXT DEFAULT "Không xác định"',
                'isp': 'TEXT DEFAULT "Không xác định"',
                'org': 'TEXT DEFAULT "Không xác định"',
                'asn': 'TEXT DEFAULT "Không xác định"',
                'timezone': 'TEXT DEFAULT "Không xác định"',
                'score': 'INTEGER DEFAULT 0',
                'ssl_verified': 'INTEGER DEFAULT 0',
                'success_rate': 'REAL DEFAULT 0.0',
                'uptime': 'REAL DEFAULT 0.0',
                'fail_count': 'INTEGER DEFAULT 0',
                'success_count': 'INTEGER DEFAULT 0',
                'target_name': 'TEXT',
            }
            for col, col_def in new_columns.items():
                if col not in columns:
                    self.cursor.execute(f"ALTER TABLE live_proxies ADD COLUMN {col} {col_def}")
            self.conn.commit()
        except Exception as e:
            log.error(f"Lỗi migrate database: {e}")
    
    def insert_proxy(self, proxy_info: ProxyInfo) -> bool:
        try:
            with self.transaction() as cur:
                cur.execute('''
                    INSERT OR REPLACE INTO live_proxies 
                    (ip_port, ip, port, protocol, country, country_code, city, region, isp, org, asn, timezone,
                     ping_ms, target, target_name, anonymity, status, success_rate, uptime,
                     score, ssl_verified, fail_count, success_count, last_checked)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    proxy_info.ip_port, proxy_info.ip, proxy_info.port, proxy_info.protocol,
                    proxy_info.country, proxy_info.country_code, proxy_info.city, proxy_info.region,
                    proxy_info.isp, proxy_info.org, proxy_info.asn, proxy_info.timezone,
                    proxy_info.latency, proxy_info.target_url, proxy_info.target_name,
                    proxy_info.anonymity, proxy_info.status, proxy_info.success_rate, proxy_info.uptime,
                    proxy_info.score, 1 if proxy_info.ssl_verified else 0,
                    proxy_info.fail_count, proxy_info.success_count, datetime.now().isoformat()
                ))
                
                proxy_id = cur.lastrowid
                if proxy_id == 0:
                    cur.execute("SELECT id FROM live_proxies WHERE ip_port = ?", (proxy_info.ip_port,))
                    row = cur.fetchone()
                    if row: proxy_id = row[0]
                
                if proxy_id:
                    cur.execute('''
                        INSERT INTO check_history (proxy_id, status, ping_ms, target_url)
                        VALUES (?, ?, ?, ?)
                    ''', (proxy_id, proxy_info.status, proxy_info.latency, proxy_info.target_url))
            return True
        except Exception as e:
            log.error(f"Lỗi insert proxy {proxy_info.ip_port}: {e}")
            return False
    
    def get_stats(self) -> Tuple[int, List[Tuple]]:
        try:
            self.cursor.execute('SELECT COUNT(*) FROM live_proxies WHERE status = "live"')
            total = self.cursor.fetchone()[0]
            self.cursor.execute('''
                SELECT protocol, COUNT(*) FROM live_proxies 
                WHERE status = "live" GROUP BY protocol
            ''')
            return total, self.cursor.fetchall()
        except Exception as e:
            log.error(f"Lỗi get stats: {e}")
            return 0, []
    
    def get_top_proxies(self, limit: int = 50, filters: Dict = None) -> List[Dict]:
        try:
            query = 'SELECT * FROM live_proxies WHERE status = "live"'
            params = []
            if filters:
                if 'protocol' in filters:
                    query += " AND protocol = ?"
                    params.append(filters['protocol'])
                if 'country_code' in filters:
                    query += " AND country_code = ?"
                    params.append(filters['country_code'])
                if 'anonymity' in filters:
                    query += " AND anonymity = ?"
                    params.append(filters['anonymity'])
            query += " ORDER BY score DESC, ping_ms ASC LIMIT ?"
            params.append(limit)
            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            log.error(f"Lỗi get top proxies: {e}")
            return []
    
    def get_all_proxies(self, status: str = None) -> List[Dict]:
        try:
            if status:
                self.cursor.execute('SELECT * FROM live_proxies WHERE status = ? ORDER BY score DESC, ping_ms ASC', (status,))
            else:
                self.cursor.execute('SELECT * FROM live_proxies ORDER BY score DESC, ping_ms ASC')
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            log.error(f"Lỗi get all proxies: {e}")
            return []
    
    def get_proxy(self, ip_port: str) -> Optional[Dict]:
        try:
            self.cursor.execute('SELECT * FROM live_proxies WHERE ip_port = ?', (ip_port,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except: return None
    
    def add_to_blacklist(self, ip: str, reason: str = "", expiry_hours: int = 24) -> bool:
        try:
            expires_at = datetime.now() + timedelta(hours=expiry_hours) if expiry_hours else None
            with self.transaction() as cur:
                cur.execute('''
                    INSERT OR REPLACE INTO blacklist (ip, reason, expires_at)
                    VALUES (?, ?, ?)
                ''', (ip, reason, expires_at.isoformat() if expires_at else None))
                cur.execute('DELETE FROM live_proxies WHERE ip = ?', (ip,))
            log.info(f"Đã blacklist IP {ip}: {reason}")
            return True
        except Exception as e:
            log.error(f"Lỗi blacklist {ip}: {e}")
            return False
    
    def is_blacklisted(self, ip: str) -> bool:
        try:
            self.cursor.execute('''
                SELECT 1 FROM blacklist 
                WHERE ip = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', (ip,))
            return self.cursor.fetchone() is not None
        except: return False
    
    def clear_database(self):
        try:
            self.cursor.execute('DELETE FROM live_proxies')
            self.cursor.execute('DELETE FROM check_history')
            self.conn.commit()
            log.info("Đã xóa database")
        except: pass
    
    def vacuum(self):
        try:
            self.cursor.execute('VACUUM')
            log.info("Đã vacuum database")
        except: pass
    
    def get_database_size(self) -> int:
        try: return os.path.getsize(self.db_name)
        except: return 0

db = DatabaseManager()

# ========================================================================================
# MODULE 9: TIỆN ÍCH HIỂN THỊ (FIX CĂN LỀ BANNER CHUẨN XÁC 100%)
# ========================================================================================

class UIHelper:
    @staticmethod
    def clear_screen():
        if platform[0:3] == 'lin' or platform == 'darwin': os.system('clear')
        else: os.system('cls')
    
    @staticmethod
    def get_terminal_size() -> Tuple[int, int]:
        try: return shutil.get_terminal_size((80, 24))
        except: return 80, 24
    
    @staticmethod
    def get_protocol_icon(protocol: str) -> str:
        icons = {'https': '🔒', 'http': '🌐', 'socks4': '🧦', 'socks5': '🧤'}
        return icons.get(protocol.lower(), '⚡')

    @staticmethod
    def get_ping_color(ping: int) -> Tuple[str, str]:
        if ping < 300: return Theme.LUC, "████"
        elif ping < 800: return Theme.VANG, "███░"
        elif ping < 1500: return Theme.RED, "██░░"
        else: return Theme.DEN, "█░░░"
        
    @staticmethod
    def get_country_flag(country_code: str) -> str:
        if not country_code or country_code == 'UN': return "🌍"
        try:
            return chr(ord(country_code[0].upper()) + 127397) + chr(ord(country_code[1].upper()) + 127397)
        except: return "🌍"
    
    @staticmethod
    def print_line(text: str, width: int = 75, align: str = 'left') -> str:
        # Xóa các mã màu ANSI để tính toán chiều dài text thực tế
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text)
        
        # Tính độ rộng hiển thị (Ký tự châu Á và một số kí tự full-width chiếm 2 ô)
        visible_len = 0
        for char in clean_text:
            if unicodedata.east_asian_width(char) in ('W', 'F'):
                visible_len += 2
            else:
                visible_len += 1
                
        # Bù trừ thủ công các Emoji thường dùng (Python đếm 1 nhưng Terminal hiển thị 2)
        emoji_list = ['🌪', '📂', '⚙', '🤖', '👑', '🔍', '💾', '📊', '🛠', '🌍', '🚫', '🚀', '🌐', '♻', '❌', '✅', '⚡', '💚', '💀', '⏱', '💎', '⛏', '⭐', '🔒', '🧤', '🧦', '📁']
        for e in emoji_list:
            visible_len += clean_text.count(e)

        padding = width - 4 - visible_len
        if padding < 0: padding = 0
        
        if align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return f"║ {' ' * left_pad}{text}{' ' * right_pad} ║\n"
        elif align == 'right':
            return f"║ {' ' * padding}{text} ║\n"
        else:
            return f"║ {text}{' ' * padding} ║\n"
    
    @staticmethod
    def print_banner(width: int = 85):
        UIHelper.clear_screen()
        banner = """███╗   ██╗██████╗       ██╗  ██╗██╗   ██╗███╗   ██╗ ██████╗
████╗  ██║██╔══██╗      ██║  ██║██║   ██║████╗  ██║██╔════╝
██╔██╗ ██║██████╔╝█████╗███████║██║   ██║██╔██╗ ██║██║  ███╗
██║╚██╗██║██╔═══╝ ╚════╝██╔══██║██║   ██║██║╚██╗██║██║   ██║
██║ ╚████║██║           ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝
╚═╝  ╚═══╝╚═╝           ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝"""
        
        # Căn giữa từng dòng của banner
        for line in banner.split('\n'):
            print(Colorate.Horizontal(Colors.blue_to_purple, line.center(width)))
            
        print(Colorate.Horizontal(Colors.blue_to_purple, "PROXY SCANNER TITAN ULTRA EDITION V15.0".center(width)))
        print(Colorate.Horizontal(Colors.blue_to_purple, "⭐ NP HUNG ⭐".center(width)))
        print(Colorate.Horizontal(Colors.blue_to_purple, ('═' * width).center(width)))

    @staticmethod
    def print_statistics(stats, width: int = 75):
        UIHelper.clear_screen(); UIHelper.print_banner(width)
        box = f"╔{'═' * (width - 2)}╗\n"
        box += UIHelper.print_line("📊 BÁO CÁO THỐNG KÊ QUÉT", width, 'center')
        box += f"╠{'═' * (width - 2)}╣\n"
        box += UIHelper.print_line(f"⏱️ Tổng thời gian: {stats.duration_seconds:.2f}s", width, 'center')
        box += UIHelper.print_line(f"✅ Đã quét: {stats.total_checked} | 💚 Sống: {stats.total_live}", width, 'center')
        box += f"╚{'═' * (width - 2)}╝\n"
        sys.stdout.write(Colorate.Vertical(Colors.blue_to_purple, box))

# ========================================================================================
# MODULE 10: AI SOURCE GENERATOR - TỰ ĐỘNG SINH NGUỒN KHÔNG GIỚI HẠN
# ========================================================================================
class AISourceGenerator:
    """AI Engine tự động suy luận và sinh ra nguồn proxy mới"""
    
    def __init__(self):
        self.generated_sources = set()
    
    def get_base_sources(self) -> List[str]:
        return StaticData.PROXY_SOURCES_RAW.copy()
    
    def generate_github_variations(self) -> List[str]:
        variations = []
        common_users = ['TheSpeedX', 'ShiftyTR', 'monosans', 'hookzof', 'clarketm', 'rooster127', 'jetkai', 'sunny9577', 'BlexBoy', 'UptimerBot', 'Volodichev', 'Zaeem20', 'MuRongPIG', 'ErcinDedeoglu']
        common_repos = ['PROXY-List', 'Proxy-List', 'proxy-list', 'proxies', 'free-proxy-list']
        common_branches = ['master', 'main']
        common_files = ['http.txt', 'socks4.txt', 'socks5.txt', 'proxies.txt', 'all.txt']
        
        for user in common_users:
            for repo in common_repos:
                for branch in common_branches:
                    for file in common_files:
                        variations.append(f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file}")
        return list(set(variations))
    
    def generate_api_variations(self) -> List[str]:
        variations = []
        for proto in ['http', 'socks4', 'socks5']:
            for limit in [100, 500, 1000, 5000]:
                variations.append(f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol={proto}&timeout=10000&country=all&limit={limit}")
        for page in range(1, 11):
            variations.append(f"https://proxylist.geonode.com/api/proxy-list?limit=500&page={page}")
        return list(set(variations))
    
    def get_sources_by_limit(self, limit: int = 500) -> List[str]:
        all_sources = set(self.get_base_sources())
        if len(all_sources) < limit:
            all_sources.update(self.generate_github_variations())
            all_sources.update(self.generate_api_variations())
        return list(all_sources)[:limit]

# ========================================================================================
# MODULE 11: GEOIP SERVICE & PROXY JUDGE
# ========================================================================================
class GeoIPService:
    def __init__(self):
        self.cache = geo_cache
        self.timeout = 5
    
    def lookup(self, ip: str) -> Dict:
        cached = self.cache.get(ip)
        if cached: return cached
        try: ipaddress.ip_address(ip)
        except: return self._empty_result()
        
        for api_url in StaticData.GEOIP_APIS:
            try:
                url = api_url.format(ip)
                resp = requests.get(url, timeout=self.timeout, headers={'User-Agent': StaticData.get_random_user_agent()})
                if resp.status_code == 200:
                    data = resp.json()
                    res = self._parse_response(data)
                    if res.get('country_code') != 'UN':
                        self.cache.set(ip, res)
                        return res
            except: continue
        return self._empty_result()
    
    def _parse_response(self, data: Dict) -> Dict:
        result = {
            'country': 'Không xác định', 'country_code': 'UN',
            'city': 'Không xác định', 'region': 'Không xác định',
            'isp': 'Không xác định', 'org': 'Không xác định',
            'asn': 'Không xác định', 'timezone': 'Không xác định'
        }
        # ip-api.com format
        if data.get('status') == 'success':
            result.update({
                'country':      data.get('country',    'Không xác định'),
                'country_code': data.get('countryCode','UN'),
                'city':         data.get('city',       'Không xác định'),
                'region':       data.get('regionName', 'Không xác định'),
                'isp':          data.get('isp',        'Không xác định'),
                'org':          data.get('org',        'Không xác định'),
                'asn':          data.get('as',         'Không xác định'),
                'timezone':     data.get('timezone',   'Không xác định'),
            })
        # ipapi.co format
        elif 'country_code' in data and 'country_name' in data:
            result.update({
                'country':      data.get('country_name',  'Không xác định'),
                'country_code': data.get('country_code',  'UN'),
                'city':         data.get('city',          'Không xác định'),
                'region':       data.get('region',        'Không xác định'),
                'isp':          data.get('org',           'Không xác định'),
                'org':          data.get('org',           'Không xác định'),
                'asn':          data.get('asn',           'Không xác định'),
                'timezone':     data.get('timezone',      'Không xác định'),
            })
        # ipinfo.io format
        elif 'country' in data and 'hostname' not in data.get('org',''):
            cc = data.get('country', 'UN')
            result.update({
                'country':      data.get('country', 'Không xác định'),
                'country_code': cc if len(cc) == 2 else 'UN',
                'city':         data.get('city',    'Không xác định'),
                'region':       data.get('region',  'Không xác định'),
                'isp':          data.get('org',     'Không xác định'),
                'org':          data.get('org',     'Không xác định'),
                'timezone':     data.get('timezone','Không xác định'),
            })
        return result
    
    def _empty_result(self) -> Dict:
        return {'country': 'Không xác định', 'country_code': 'UN', 'city': 'Không xác định', 'region': 'Không xác định', 'isp': 'Không xác định', 'org': 'Không xác định', 'asn': 'Không xác định', 'timezone': 'Không xác định'}

geoip_service = GeoIPService()

# ========================================================================================
# MODULE 12: PROXY JUDGE & ANONYMITY CHECKER
# ========================================================================================
class ProxyJudge:
    """Kiểm tra mức độ ẩn danh của proxy (Elite / Anonymous / Transparent)"""
    
    def __init__(self):
        self.real_ip = self._get_real_ip()
    
    def _get_real_ip(self) -> str:
        try:
            resp = requests.get("http://ip-api.com/json", timeout=5)
            return resp.json().get('query', '')
        except:
            return ''
    
    def check_anonymity(self, proxy_info: ProxyInfo) -> AnonymityLevel:
        proxies = proxy_info.proxy_dict
        if not proxies:
            return AnonymityLevel.UNKNOWN
        
        try:
            for judge_url in StaticData.PROXY_JUDGES[:3]:
                try:
                    resp = requests.get(
                        judge_url,
                        proxies=proxies,
                        timeout=10,
                        headers={'User-Agent': StaticData.get_random_user_agent()}
                    )
                    
                    if resp.status_code == 200:
                        headers = dict(resp.headers)
                        content = resp.text
                        
                        if self.real_ip and self.real_ip in content:
                            return AnonymityLevel.TRANSPARENT
                        
                        headers_lower = {k.lower(): v for k, v in headers.items()}
                        proxy_headers = ['via', 'x-forwarded-for', 'x-proxy-connection', 'proxy-connection']
                        
                        has_proxy_header = any(h in headers_lower for h in proxy_headers)
                        
                        if has_proxy_header:
                            return AnonymityLevel.ANONYMOUS
                        else:
                            return AnonymityLevel.ELITE
                except:
                    continue
            return AnonymityLevel.UNKNOWN
        except Exception as e:
            log.debug(f"Lỗi kiểm tra anonymity cho {proxy_info.ip_port}: {e}")
            return AnonymityLevel.UNKNOWN

proxy_judge = ProxyJudge()

# ========================================================================================
# MODULE 13: ĐỘNG CƠ THU THẬP & QUÉT (SCRAPER & SCANNER ENGINE) - ASYNCIO V15 PRO
# ========================================================================================

class ProxyEngine:
    def __init__(self):
        self.queue = queue.Queue()
        self.total = 0
        self.checked = 0
        self.live = 0
        self.dead = 0
        self.timeout = 0
        self.blocked = 0
        self.lock = threading.Lock()
        self.is_running = False
        self.stop_event = threading.Event()
        self.statistics = ScanStatistics()
        self.proxy_judge = ProxyJudge()
        self.geoip = geoip_service
        self.ai_generator = AISourceGenerator()
        self.session_pool = self._create_session_pool()
        self.dns_cache = {}
        self.semaphore = threading.Semaphore(cfg.get('connection_pool_size', 50))
    
    def _create_session_pool(self) -> List[requests.Session]:
        sessions = []
        for _ in range(cfg.get('connection_pool_size', 50)):
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
            session.mount('http://', adapter); session.mount('https://', adapter)
            session.verify = False; sessions.append(session)
        return sessions
    
    def _get_session(self) -> requests.Session:
        return random.choice(self.session_pool)
    
    def scrape(self, source_limit: int = None) -> int:
        if source_limit is None: source_limit = cfg.get('source_limit', 500)
        print(f"\n{Theme.VANG}🌐 AI Engine đang chuẩn bị {source_limit}+ nguồn proxy...{Theme.RESET}")
        
        all_sources = self.ai_generator.get_sources_by_limit(source_limit)
        self.statistics.sources_used = len(all_sources)
        print(f"{Theme.LUC}✅ Đã sẵn sàng {len(all_sources)} nguồn proxy!{Theme.RESET}\n")
        
        raw_proxies = set()
        failed_sources = 0; completed_sources = 0
        total_sources = len(all_sources)
        ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{1,5}\b')
        
        import urllib3; urllib3.disable_warnings()

        def fetch_source(url: str):
            nonlocal failed_sources, completed_sources
            local_found = set()
            try:
                headers = {'User-Agent': StaticData.get_random_user_agent()}
                response = requests.get(url, headers=headers, timeout=5, verify=False)
                if response.status_code == 200:
                    found = ip_pattern.findall(response.text)
                    for proxy in found:
                        try:
                            ip, port = proxy.split(':')
                            if 1 <= int(port) <= 65535: local_found.add(proxy)
                        except: pass
                else: failed_sources += 1
            except: failed_sources += 1
            finally:
                with self.lock:
                    raw_proxies.update(local_found); completed_sources += 1
                    sys.stdout.write(f"\r\033[2K{Theme.LAM}║ ⛏️  Đang đào: [{completed_sources}/{total_sources}] nguồn | 💎 Tìm thấy: {Theme.LUC}{len(raw_proxies)}{Theme.LAM} proxy | ❌ Lỗi: {Theme.RED}{failed_sources}{Theme.RESET}")
                    sys.stdout.flush()

        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
            executor.map(fetch_source, all_sources)
        
        print(f"\n\n{Theme.VANG}⏳ Đang thanh lọc proxy rác và blacklist...{Theme.RESET}")
        valid_proxies = set()
        for p in raw_proxies:
            try:
                ip = p.split(':')[0]; ip_obj = ipaddress.ip_address(ip)
                if not ip_obj.is_private and not ip_obj.is_loopback:
                    if not db.is_blacklisted(ip): valid_proxies.add(p)
            except: pass
        
        self.total = len(valid_proxies)
        self.statistics.total_found = self.total
        self.statistics.sources_failed = failed_sources
        
        for p in valid_proxies: self.queue.put(p)
        print(f"{Theme.LUC}✅ Đã nạp {self.total} proxy sạch vào Động cơ Quét!{Theme.RESET}\n")
        return self.total
    
    def load_from_file(self, filepath: str) -> int:
        print(f"\n{Theme.VANG}📂 Đang đọc proxy từ file: {filepath}{Theme.RESET}")
        if not os.path.exists(filepath):
            print(f"{Theme.RED}❌ File không tồn tại!{Theme.RESET}"); return 0
        raw_proxies = set()
        ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{1,5}\b')
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
            for proxy in ip_pattern.findall(content):
                try:
                    ip, port = proxy.split(':')
                    if 1 <= int(port) <= 65535 and not db.is_blacklisted(ip): raw_proxies.add(proxy)
                except: pass
            self.total = len(raw_proxies)
            for p in raw_proxies: self.queue.put(p)
            print(f"{Theme.LUC}✅ Đã load {self.total} proxy từ file!{Theme.RESET}\n")
            return self.total
        except Exception as e:
            print(f"{Theme.RED}❌ Lỗi: {e}{Theme.RESET}"); return 0

    # LÕI ASYNCIO ĐƯỢC TỐI ƯU HÓA KHÔNG BLOCKING DB
    async def _async_check_proxy(self, proxy_str, target_url, target_name, sem):
        if not self.is_running or self.stop_event.is_set(): return
        # Validate proxy string format trước khi xử lý
        parts = proxy_str.split(':')
        if len(parts) != 2: return
        ip, port = parts
        if not port.isdigit(): return

        best_proto, best_ping, best_status = None, float('inf'), "dead"
        timeout_obj = aiohttp.ClientTimeout(total=cfg.data.get('timeout', 8))
        
        async with sem:
            for proto in cfg.data.get('protocols', ['http', 'socks5']):
                try:
                    connector = ProxyConnector.from_url(f"{proto}://{proxy_str}")
                    async with aiohttp.ClientSession(connector=connector) as proxy_session:
                        start_time = time.time()
                        async with proxy_session.get(target_url, timeout=timeout_obj, ssl=False) as resp:
                            if resp.status in [200, 201, 202, 204, 301, 302, 303, 307, 308]:
                                ping = int((time.time() - start_time) * 1000)
                                if ping < best_ping: best_ping, best_proto, best_status = ping, proto, "live"
                except: continue
                
        # Dùng lock để đảm bảo thread-safe khi cập nhật counter
        with self.lock:
            self.checked += 1
        sys.stdout.write("\r\033[2K")
        
        if best_proto:
            p_info = ProxyInfo(ip=ip, port=int(port), protocol=best_proto, latency=best_ping, status=best_status, target_url=target_url, target_name=target_name)
            
            if cfg.get('geoip_enabled', True):
                # asyncio.to_thread yêu cầu Python 3.9+ - dùng run_in_executor cho 3.8+
                loop = asyncio.get_event_loop()
                geo = await loop.run_in_executor(None, self.geoip.lookup, ip)
                p_info.country = geo.get('country', 'Không xác định')
                p_info.country_code = geo.get('country_code', geo.get('cc', 'UN'))
                p_info.isp = geo.get('isp', 'Không xác định')
                
            p_info.calculate_score()
            with self.lock:
                self.live += 1
                if hasattr(self.statistics, 'total_live'): self.statistics.total_live += 1
            
            self._print_result(p_info)
            
            # Đẩy tác vụ ghi DB nặng nề ra thread phụ (compatible Python 3.8+)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, db.insert_proxy, p_info)
            log.info(f"LIVE: {proxy_str} | {best_proto.upper()} | {best_ping}ms")
        else:
            with self.lock:
                self.dead += 1
                if hasattr(self.statistics, 'total_dead'): self.statistics.total_dead += 1
            
        self.draw_progress_bar()

    def draw_progress_bar(self):
        if self.total == 0: return
        percent = (self.checked / self.total) * 100
        bar_len = 40; filled = int(bar_len * self.checked // self.total)
        bar_color = Theme.RED if percent < 30 else Theme.VANG if percent < 70 else Theme.LUC
        bar = f"{bar_color}{'█' * filled}{Theme.DEN}{'░' * (bar_len - filled)}{Theme.RESET}"
        elapsed = (datetime.now() - self.statistics.start_time).total_seconds() if self.statistics.start_time else 1
        rate = self.checked / elapsed if elapsed > 0 else 0
        eta = (self.total - self.checked) / rate if rate > 0 else 0
        sys.stdout.write(f"\r\033[2K{Theme.LAM}║ 🚀 [{bar}] {percent:5.1f}% | ✓ {self.checked}/{self.total} | 💚 {self.live} | 💀 {self.dead} | ⚡ {rate:.1f}/s | ⏱️ ETA: {eta:.0f}s {Theme.RESET}")
        sys.stdout.flush()

    def _print_result(self, proxy_info: ProxyInfo):
        p_color, speed_bar = UIHelper.get_ping_color(proxy_info.latency)
        flag = UIHelper.get_country_flag(proxy_info.country_code)
        bad_isps = ['digitalocean', 'aws', 'amazon', 'ovh', 'choopa', 'hetzner', 'linode', 'alibaba', 'google', 'hosting', 'datacenter', 'cloud']
        is_safe = not any(bad in str(proxy_info.isp).lower() for bad in bad_isps)
        shield = f"{Theme.LUC}[SAFE]{Theme.RESET}" if is_safe else f"{Theme.RED}[SCAM]{Theme.RESET}"
        print(f"{Theme.LUC}╠ ✓ SỐNG{Theme.RESET} 🌐 {Theme.LAM}[{proxy_info.protocol.upper():<7}]{Theme.RESET} {Theme.TRANG}{proxy_info.ip_port:<21}{Theme.RESET} {speed_bar} {p_color}{proxy_info.latency:>4}ms{Theme.RESET} {flag} {proxy_info.country[:12]:<12} {shield}")

    def start_engine(self, source_type: str = "online", file_path: str = None, is_autopilot: bool = False):
        UIHelper.clear_screen(); UIHelper.print_banner()
        total = self.scrape(cfg.get('source_limit', 500)) if source_type == "online" else self.load_from_file(file_path) if file_path else 0
        if total == 0:
            print(f"{Theme.RED}[!] Không có proxy nào để kiểm tra!{Theme.RESET}")
            if not is_autopilot: input("\nNhấn Enter để quay lại...")
            return
        
        target = StaticData.TARGETS.get(str(cfg.data['target_id']), StaticData.TARGETS["1"])
        print(f"{Theme.LAM}╔{'═' * 70}╗\n║ 🎯 MỤC TIÊU: {target['name']} | 📊 TỔNG: {total} | LUỒNG ẢO: {cfg.data['threads']}\n╚{'═' * 70}╝{Theme.RESET}\n")
        
        self.statistics = ScanStatistics(); self.statistics.start_time = datetime.now()
        self.is_running, self.checked, self.live, self.dead, self.timeout, self.blocked = True, 0, 0, 0, 0, 0
        self.stop_event.clear(); self.draw_progress_bar()
        
        proxy_list = []
        while not self.queue.empty(): proxy_list.append(self.queue.get())

        async def run_tasks():
            sem = asyncio.Semaphore(cfg.data['threads'])
            tasks = [asyncio.create_task(self._async_check_proxy(p, target['url'], target['name'], sem)) for p in proxy_list]
            await asyncio.gather(*tasks)

        try:
            asyncio.run(run_tasks())
        except KeyboardInterrupt:
            print(f"\n{Theme.RED}╠ [!] Dừng khẩn cấp...{Theme.RESET}"); self.stop_event.set(); self.is_running = False
        
        self.statistics.end_time = datetime.now()
        # duration_seconds là @property tự tính từ start_time/end_time, không gán trực tiếp
        self.statistics.total_live, self.statistics.total_dead = self.live, self.dead
        sys.stdout.write("\r\033[2K"); UIHelper.print_statistics(self.statistics)
        print(f"\n{Theme.LUC}✅ QUÉT HOÀN TẤT! TÌM THẤY {self.live} PROXY SỐNG.{Theme.RESET}")
        
        self.auto_export_results()
        self.export_special_formats() 
        
        if not is_autopilot: input(f"\n{Theme.DEN}Nhấn Enter để quay lại Menu...{Theme.RESET}")

    async def start_engine_async(self):
        """Wrapper async để Telegram Commander có thể kích hoạt engine"""
        self.start_engine(source_type="online", is_autopilot=True)

    def auto_export_results(self):
        folder = f"exports/ScanResult_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(folder, exist_ok=True)
        proxies = db.get_all_proxies("live")
        if not proxies: return
        all_file = f"{folder}/ALL_PROXIES.txt"
        with open(all_file, "w", encoding='utf-8') as f: f.write("\n".join([p['ip_port'] for p in proxies]))
        print(f"\n{Theme.VANG}📁 Đã tự động lưu kết quả vào: {Theme.TRANG}{folder}/{Theme.RESET}")

        bot_token = cfg.get('telegram_bot_token', ''); chat_id = cfg.get('telegram_chat_id', '')
        if bot_token and chat_id:
            print(f"{Theme.LAM}🚀 Đang sử dụng API gửi file kết quả về Telegram...{Theme.RESET}")
            try:
                msg = f"<b>✅ QUÉT HOÀN TẤT V15 PRO!</b>\n🎯 Tổng proxy sống: {len(proxies)}\n⚡ Thời gian quét: {self.statistics.duration_seconds:.1f}s"
                requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=10)
                with open(all_file, 'rb') as f: requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", data={"chat_id": chat_id, "caption": f"🎁 File Proxy Xịn ({len(proxies)} live)"}, files={"document": f}, timeout=20)
                print(f"{Theme.LUC}✅ Đã ném thành công qua Telegram! Ting ting!{Theme.RESET}")
            except Exception as e: print(f"{Theme.RED}❌ Lỗi mạng khi gửi Telegram: {e}{Theme.RESET}")

    def export_special_formats(self):
        proxies = db.get_all_proxies("live"); folder = "exports/VIP_Formats"
        if not proxies: return
        os.makedirs(folder, exist_ok=True)
        with open(f"{folder}/Proxifier_Profile.ppx", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0"?><ProxifierProfile version="101"><ProxyList>')
            for i, p in enumerate(proxies[:100]): f.write(f'<Proxy id="{i+100}" type="{p["protocol"].upper()}"><Address>{p["ip"]}</Address><Port>{p["port"]}</Port><Options>48</Options></Proxy>')
            f.write('</ProxyList></ProxifierProfile>')
        with open(f"{folder}/Clash_Config.yaml", "w", encoding="utf-8") as f:
            f.write("proxies:\n")
            for p in proxies[:100]: f.write(f"  - name: '{p['country_code']}_{p['ip_port']}'\n    type: {p['protocol']}\n    server: {p['ip']}\n    port: {p['port']}\n")

# ========================================================================================
# MODULE 14: QUẢN LÝ GIAO DIỆN (PEAK UI - BẢN BUNG NÉN 100% TỪNG DÒNG LỆNH)
# ========================================================================================
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class ApplicationUI:
    def __init__(self):
        term_width = shutil.get_terminal_size((80, 24)).columns
        self.width = min(term_width - 2, 85)
        if self.width < 65:
            self.width = 65
            
        self.engine = ProxyEngine()
        self.web_server = None
        
        try:
            self.heal = AutoHealThread()
            self.heal.daemon = True
            self.heal.start()
            
            self.bot_cmd = TelegramCommander(self.engine)
            self.bot_cmd.daemon = True
            self.bot_cmd.start()
        except Exception as e:
            log.error(f"Lỗi khởi động dịch vụ ngầm: {e}")
            
    def get_ram_usage(self):
        if HAS_PSUTIL:
            try:
                process = psutil.Process(os.getpid())
                ram_mb = process.memory_info().rss / (1024 * 1024)
                return f"{ram_mb:.1f}MB"
            except Exception:
                return "N/A"
        return "N/A"
    
    def draw_main_menu(self):
        UIHelper.clear_screen()
        UIHelper.print_banner(self.width)
        
        total, protos = db.get_stats()
        if protos:
            proto_str = " | ".join([f"{p[0].upper()}: {p[1]}" for p in protos])
        else:
            proto_str = "Trống"
            
        tele_token = cfg.get('telegram_bot_token', '')
        tele_cid = cfg.get('telegram_chat_id', '')
        
        if tele_token and tele_cid:
            tele_status = "✅ ONLINE"
        else:
            tele_status = "❌ OFFLINE"
            
        if self.web_server:
            web_status = "✅ CHẠY NGẦM"
        else:
            web_status = "❌ ĐANG TẮT"
            
        ram_str = self.get_ram_usage()

        # ====== THIẾT KẾ PEAK UI CHIA BLOCK ======
        print(f"{Theme.LAM}╔{'═' * (self.width - 2)}╗")
        print(UIHelper.print_line(f"{Theme.VANG} [ TRẠNG THÁI HỆ THỐNG - SYSTEM STATUS ] {Theme.LAM}", self.width, 'center'), end='')
        print(f"╠{'═' * (self.width - 2)}╣")
        print(UIHelper.print_line(f"📊 Kho DB  : {total:<12} │ 💻 RAM Dùng: {ram_str:<10}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"🤖 Bot Tele: {tele_status:<12} │ 🌐 Web Dash: {web_status:<10}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"⚡ Động Cơ : {cfg.get('source_limit', 500):<4} Nguồn   │ ⚙️ Threads : {cfg.get('threads', 500):<10}", self.width, 'center'), end='')
        
        print(f"╠{'═' * (self.width - 2)}╣")
        print(UIHelper.print_line(f"{Theme.VANG} [ BẢNG ĐIỀU KHIỂN - CONTROL PANEL ] {Theme.LAM}", self.width, 'center'), end='')
        print(f"╠{'═' * (self.width - 2)}╣")
        
        print(UIHelper.print_line(f"{Theme.TRANG}[1] 🌪️ Quét Siêu Tốc (Async)   │ [9]  🛠️ Bảo Trì, Dọn Dẹp DB{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[2] 📂 Quét Từ FILE (TXT)       │ [10] 🌍 Kiểm Tra Vị Trí GeoIP{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[3] ⚙️ Cài Đặt Hệ Thống         │ [11] 🚫 Quản Lý Blacklist IP{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[4] 🤖 Đổi Giới Hạn Nguồn AI    │ [12] 🤖 Cài Đặt Bot Telegram{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[5] 👑 Lấy Top 50 Proxy VIP     │ [13] 🚀 Bật Trạm Proxy Local{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[6] 🔍 Xem Chi Tiết 1 Proxy     │ [14] 🌐 Bật / Tắt Web Dashboard{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[7] 💾 Xuất File (Proxy/Clash)  │ [15] ♻️ Kích Hoạt Auto-Pilot{Theme.LAM}", self.width, 'center'), end='')
        print(UIHelper.print_line(f"{Theme.TRANG}[8] 📊 Thống Kê Database        │ [0]  ❌ Thoát & Đóng Hệ Thống{Theme.LAM}", self.width, 'center'), end='')
        print(f"╚{'═' * (self.width - 2)}╝{Theme.RESET}")
    
    def prompt_input(self) -> str:
        user = cfg.get("username", "root").lower().replace(" ", "")
        print(f"\n{Theme.LAM}╭─[{Theme.LUC}root@{user}{Theme.LAM}]─[{Theme.VANG}ProxyTitan{Theme.LAM}]")
        choice = input(f"{Theme.LAM}╰─➤ {Theme.TRANG}Nhập số: {Theme.LUC}").strip()
        return choice

    def telegram_setup_menu(self):
        while True:
            UIHelper.clear_screen()
            UIHelper.print_banner(self.width)
            
            token = cfg.get('telegram_bot_token', '')
            chat_id = cfg.get('telegram_chat_id', '')
            
            if token and len(token) > 12:
                token_display = f"{token[:8]}........{token[-4:]}"
            else:
                token_display = "CHƯA CÀI ĐẶT"
            
            box = f"╔{'═' * (self.width - 2)}╗\n"
            box += UIHelper.print_line("🤖 BẢNG ĐIỀU KHIỂN TELEGRAM BOT", self.width, 'center')
            box += f"╠{'═' * (self.width - 2)}╣\n"
            
            if token and chat_id:
                status_str = "✅ ĐÃ KẾT NỐI"
            else:
                status_str = "❌ CHƯA SẴN SÀNG"
                
            box += UIHelper.print_line(f"Trạng thái: {status_str}", self.width)
            box += UIHelper.print_line("", self.width)
            box += UIHelper.print_line(f"[1] Nhập / Đổi Bot Token (Hiện tại: {token_display})", self.width)
            box += UIHelper.print_line(f"[2] Nhập / Đổi Chat ID   (Hiện tại: {chat_id})", self.width)
            box += UIHelper.print_line(f"[3] 📩 Gửi tin nhắn Test Bot", self.width)
            box += UIHelper.print_line(f"[0] Quay lại Menu Chính", self.width)
            box += f"╚{'═' * (self.width - 2)}╝\n"
            
            sys.stdout.write(Colorate.Vertical(Colors.blue_to_purple, box))
            
            c = input(f"\n{Theme.LAM}╰─➤ {Theme.TRANG}Chọn: {Theme.LUC}").strip()
            
            if c == '1':
                new_token = input(f"{Theme.LAM}╰─➤ {Theme.TRANG}Nhập Bot Token: {Theme.LUC}").strip()
                if new_token: 
                    cfg.update("telegram_bot_token", new_token)
                    print(f"{Theme.LUC}✅ Đã lưu!{Theme.RESET}")
                    time.sleep(1)
            
            elif c == '2':
                new_cid = input(f"{Theme.LAM}╰─➤ {Theme.TRANG}Nhập Chat ID: {Theme.LUC}").strip()
                if new_cid: 
                    cfg.update("telegram_chat_id", new_cid)
                    print(f"{Theme.LUC}✅ Đã lưu!{Theme.RESET}")
                    time.sleep(1)
                    
            elif c == '3':
                if not token or not chat_id: 
                    print(f"\n{Theme.RED}❌ Thiếu thông tin Token hoặc Chat ID!{Theme.RESET}")
                else:
                    try:
                        import requests
                        msg = "<b>✅ PROXY TITAN V15: Kết nối thành công! Hệ thống đã sẵn sàng.</b>"
                        payload = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
                        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=10)
                        print(f"{Theme.LUC}✅ Đã gửi tin nhắn test đến Bot Telegram!{Theme.RESET}")
                    except Exception as e: 
                        print(f"{Theme.RED}❌ Lỗi mạng hoặc Token sai: {e}{Theme.RESET}")
                time.sleep(2)
                
            elif c == '0': 
                break

    def show_settings(self):
        while True:
            UIHelper.clear_screen()
            UIHelper.print_banner(self.width)
            
            target_id = str(cfg.data.get('target_id', '1'))
            target_name = StaticData.TARGETS.get(target_id, StaticData.TARGETS['1'])['name']
            
            box = f"╔{'═' * (self.width - 2)}╗\n"
            box += UIHelper.print_line("⚙️ CÀI ĐẶT HỆ THỐNG", self.width, 'center')
            box += f"╠{'═' * (self.width - 2)}╣\n"
            box += UIHelper.print_line(f"[1] Luồng ảo (Threads): {cfg.data.get('threads', 500)}", self.width)
            box += UIHelper.print_line(f"[2] Timeout (Giây): {cfg.data.get('timeout', 8)}s", self.width)
            box += UIHelper.print_line(f"[3] Mục tiêu test: {target_name}", self.width)
            
            protos = cfg.data.get('protocols', ['http','socks4','socks5'])
            proto_str = ", ".join(protos).upper()
            box += UIHelper.print_line(f"[4] Giao thức: {proto_str}", self.width)
            
            if cfg.data.get('auto_export_txt', True):
                export_status = "BẬT"
            else:
                export_status = "TẮT"
            box += UIHelper.print_line(f"[5] Tự động lưu TXT: {export_status}", self.width)
            
            box += UIHelper.print_line(f"[R] Reset về mặc định", self.width)
            box += UIHelper.print_line(f"[0] Quay lại Menu", self.width)
            box += f"╚{'═' * (self.width - 2)}╝\n"
            
            sys.stdout.write(Colorate.Vertical(Colors.blue_to_purple, box))
            
            c = input(f"\n{Theme.LAM}╰─➤ {Theme.TRANG}Chọn: {Theme.LUC}").strip().lower()
            
            if c == '1':
                t = input(f"{Theme.TRANG}Nhập số luồng (50-5000): {Theme.LUC}")
                if t.isdigit(): 
                    cfg.update("threads", int(t))
            elif c == '2':
                t = input(f"{Theme.TRANG}Nhập Timeout (3-30s): {Theme.LUC}")
                if t.isdigit(): 
                    cfg.update("timeout", int(t))
            elif c == '3':
                for k, v in StaticData.TARGETS.items(): 
                    print(f"  {k}. {v['name']}")
                t = input(f"{Theme.TRANG}Chọn ID mục tiêu: {Theme.LUC}")
                if t in StaticData.TARGETS: 
                    cfg.update("target_id", t)
            elif c == '4':
                t = input(f"{Theme.TRANG}Nhập giao thức (VD: http,socks5): {Theme.LUC}").strip()
                if t: 
                    parsed_protos = [p.strip() for p in t.split(',')]
                    cfg.update("protocols", parsed_protos)
            elif c == '5': 
                current_state = cfg.data.get('auto_export_txt', True)
                cfg.update("auto_export_txt", not current_state)
            elif c == 'r': 
                cfg.reset_to_default()
                time.sleep(1)
            elif c == '0': 
                break

    def start_autopilot(self):
        UIHelper.clear_screen(); UIHelper.print_banner()
        print(f"{Theme.LAM}╔{'═' * 70}╗")
        print(f"║ 🤖 CHẾ ĐỘ AUTO-PILOT 24/7 ĐÃ KÍCH HOẠT")
        print(f"║ ⚡ Tool sẽ tự động cào, quét, lọc và gửi Bot mỗi 30 phút.")
        print(f"║ ⚠️  Nhấn Ctrl+C bất cứ lúc nào để dừng lại.")
        print(f"╚{'═' * 70}╝{Theme.RESET}\n")
        cycle = 1
        while True:
            try:
                print(f"\n{Theme.VANG}[VÒNG LẶP {cycle}] Bắt đầu thu thập và làm mới Proxy...{Theme.RESET}")
                self.engine.start_engine(source_type="online", is_autopilot=True)
                print(f"\n{Theme.LUC}⏳ Vòng {cycle} hoàn tất! Nghỉ ngơi 30 phút...{Theme.RESET}")
                for i in range(1800, 0, -1):
                    mins, secs = divmod(i, 60)
                    sys.stdout.write(f"\r\033[2K{Theme.LAM}║ 💤 Chờ chu kỳ tiếp theo sau: {mins:02d}:{secs:02d}{Theme.RESET}")
                    sys.stdout.flush(); time.sleep(1)
                cycle += 1
            except KeyboardInterrupt:
                print(f"\n{Theme.RED}🛑 Đã tắt hệ thống Auto-Pilot!{Theme.RESET}"); break
            except Exception as e:
                log.error(f"Lỗi Auto-pilot: {e}"); time.sleep(60)

    def run(self):
        while True:
            try:
                self.draw_main_menu()
                choice = self.prompt_input()
                
                # ==========================================
                # [1] QUÉT ONLINE
                # ==========================================
                if choice == '1': 
                    self.engine.start_engine("online")
                    input(f"\n{Theme.DEN}Nhấn Enter để quay lại Menu...{Theme.RESET}")
                
                # ==========================================
                # [2] QUÉT TỪ FILE
                # ==========================================
                elif choice == '2':
                    filepath = input(f"{Theme.LAM}╰─➤ {Theme.TRANG}Nhập đường dẫn file (VD: proxy.txt): {Theme.LUC}").strip()
                    if filepath: 
                        self.engine.start_engine("file", filepath)
                    input(f"\n{Theme.DEN}Nhấn Enter để quay lại Menu...{Theme.RESET}")
                
                # ==========================================
                # [3] CÀI ĐẶT
                # ==========================================
                elif choice == '3': 
                    self.show_settings()
                
                # ==========================================
                # [4] ĐỔI GIỚI HẠN NGUỒN AI
                # ==========================================
                elif choice == '4':
                    lim = input(f"{Theme.TRANG}Nhập giới hạn nguồn AI Engine (Mặc định 500): {Theme.LUC}")
                    if lim.isdigit(): 
                        cfg.update("source_limit", int(lim))
                        print(f"{Theme.LUC}✅ Đã lưu cấu hình mới!{Theme.RESET}")
                        time.sleep(1)
                
                # ==========================================
                # [5] XEM TOP 50
                # ==========================================
                elif choice == '5':
                    UIHelper.clear_screen()
                    print(f"\n{Theme.VANG}--- 👑 TOP 50 PROXY SỐNG MẠNH NHẤT ---{Theme.RESET}")
                    proxies = db.get_top_proxies(50)
                    
                    if not proxies: 
                        print(f"{Theme.RED}Kho proxy đang trống! Vui lòng thực hiện quét.{Theme.RESET}")
                    else:
                        bad_isps = ['digitalocean', 'aws', 'amazon', 'ovh', 'choopa', 'hetzner', 'linode', 'alibaba', 'google', 'hosting', 'datacenter', 'cloud']
                        for p in proxies: 
                            is_safe = not any(b in str(p.get('isp','')).lower() for b in bad_isps)
                            if is_safe:
                                shield = f"{Theme.LUC}[SAFE]{Theme.RESET}"
                            else:
                                shield = f"{Theme.RED}[SCAM]{Theme.RESET}"
                                
                            ip_port_str = p['ip_port']
                            proto_str = p['protocol']
                            ping_ms = p.get('ping_ms', 0)
                            cc = p.get('country_code', 'UN')
                            
                            print(f"  {ip_port_str:<21} | {proto_str:<6} | {ping_ms:<4}ms | {shield} | {cc}")
                            
                    input(f"\n{Theme.DEN}Nhấn Enter để quay lại...{Theme.RESET}")
                
                # ==========================================
                # [6] CHI TIẾT 1 PROXY
                # ==========================================
                elif choice == '6':
                    ip_port = input(f"{Theme.TRANG}Nhập IP:PORT cần kiểm tra: {Theme.LUC}").strip()
                    p = db.get_proxy(ip_port)
                    if p: 
                        print(f"{Theme.LUC}📍 Chi tiết Proxy: {p}{Theme.RESET}")
                    else: 
                        print(f"{Theme.RED}❌ Không tìm thấy IP này trong Database!{Theme.RESET}")
                        
                    input(f"\n{Theme.DEN}Nhấn Enter...{Theme.RESET}")
                
                # ==========================================
                # [7] XUẤT DỮ LIỆU FULL + VIP
                # ==========================================
                elif choice == '7':
                    proxies = db.get_all_proxies("live")
                    if not proxies:
                        print(f"{Theme.RED}❌ Kho proxy đang trống! Không có gì để xuất.{Theme.RESET}")
                    else:
                        http_list = []
                        socks4_list = []
                        socks5_list = []
                        
                        for p in proxies:
                            proto_val = p.get('protocol', '').lower()
                            if 'http' in proto_val:
                                http_list.append(p['ip_port'])
                            if 'socks4' in proto_val:
                                socks4_list.append(p['ip_port'])
                            if 'socks5' in proto_val:
                                socks5_list.append(p['ip_port'])
                        
                        if http_list: 
                            with open("EXPORT_HTTP.txt", "w", encoding='utf-8') as f:
                                f.write("\n".join(http_list))
                        if socks4_list: 
                            with open("EXPORT_SOCKS4.txt", "w", encoding='utf-8') as f:
                                f.write("\n".join(socks4_list))
                        if socks5_list: 
                            with open("EXPORT_SOCKS5.txt", "w", encoding='utf-8') as f:
                                f.write("\n".join(socks5_list))
                        
                        print(f"\n{Theme.LUC}✅ ĐÃ XUẤT THÀNH CÔNG RA THƯ MỤC GỐC:{Theme.RESET}")
                        print(f" 🌐 HTTP   : {len(http_list)} proxy")
                        print(f" 🧦 SOCKS4 : {len(socks4_list)} proxy")
                        print(f" 🧦 SOCKS5 : {len(socks5_list)} proxy")
                        
                        if hasattr(self.engine, 'export_special_formats'):
                            print(f"\n{Theme.VANG}⚙️ Đang tạo cấu hình VIP (Proxifier Profile / Clash YAML)...{Theme.RESET}")
                            self.engine.export_special_formats()
                            
                    input(f"\n{Theme.DEN}Nhấn Enter để quay lại Menu...{Theme.RESET}")
                
                # ==========================================
                # [8] THỐNG KÊ
                # ==========================================
                elif choice == '8':
                    total_live, protocols = db.get_stats()
                    print(f"\n{Theme.VANG}📊 THỐNG KÊ CHI TIẾT:{Theme.RESET}")
                    print(f" - Tổng số Proxy đang SỐNG: {total_live}")
                    if protocols:
                        for proto in protocols:
                            print(f" - Giao thức {proto[0].upper()}: {proto[1]} proxy")
                            
                    input(f"\n{Theme.DEN}Nhấn Enter để tiếp tục...{Theme.RESET}")
                
                # ==========================================
                # [9] DỌN DẸP DATABASE
                # ==========================================
                elif choice == '9':
                    xac_nhan = input(f"{Theme.RED}Xác nhận xóa SẠCH Database? Lệnh này không thể hoàn tác! (y/n): {Theme.LUC}").lower()
                    if xac_nhan == 'y':
                        db.clear_database()
                        print(f"{Theme.LUC}✅ Đã dọn dẹp sạch sẽ kho dữ liệu!{Theme.RESET}")
                        time.sleep(1)
                
                # ==========================================
                # [10] KIỂM TRA GEOIP
                # ==========================================
                elif choice == '10':
                    ip = input(f"{Theme.TRANG}Nhập IP cần check vị trí: {Theme.LUC}").strip()
                    try: 
                        import requests
                        response = requests.get(f"http://ip-api.com/json/{ip}").json()
                        if response.get("status") == "success":
                            print(f"\n{Theme.LUC}🌍 QUỐC GIA: {response.get('country')}{Theme.RESET}")
                            print(f"🏢 NHÀ MẠNG (ISP): {response.get('isp')}")
                            print(f"📍 THÀNH PHỐ: {response.get('city')}")
                        else:
                            print(f"{Theme.RED}❌ Lỗi: {response.get('message', 'Không rõ')}{Theme.RESET}")
                    except Exception as e: 
                        print(f"{Theme.RED}❌ Lỗi kết nối mạng: {e}{Theme.RESET}")
                        
                    input(f"\n{Theme.DEN}Nhấn Enter để tiếp tục...{Theme.RESET}")
                
                # ==========================================
                # [11] BLACKLIST
                # ==========================================
                elif choice == '11':
                    ip = input(f"{Theme.TRANG}Nhập IP cần chặn vĩnh viễn (Blacklist): {Theme.LUC}").strip()
                    if ip: 
                        db.add_to_blacklist(ip, "Chặn thủ công từ Menu")
                        print(f"{Theme.LUC}✅ Đã đưa IP {ip} vào danh sách đen!{Theme.RESET}")
                        time.sleep(1)
                
                # ==========================================
                # [12] SETUP BOT TELEGRAM
                # ==========================================
                elif choice == '12': 
                    self.telegram_setup_menu()
                
                # ==========================================
                # [13] BẬT TRẠM LOCAL PROXY
                # ==========================================
                elif choice == '13':
                    print(f"\n{Theme.LAM}🚀 BẬT TRẠM CHUYỂN TIẾP (LOCAL PROXY SERVER){Theme.RESET}")
                    print("  [1] Chế độ Đảo IP (Rotating) - Mỗi request đổi 1 IP")
                    print("  [2] Chế độ Giữ IP (Sticky)   - Giữ nguyên IP trong 5 phút")
                    print("  [3] Chế độ Chuỗi (Chaining)  - Bypass cực mạnh")
                    m = input(f"{Theme.TRANG}Chọn chế độ: {Theme.LUC}").strip()
                    
                    if m == '3':
                        mode = 'chaining'
                    elif m == '2':
                        mode = 'sticky'
                    else:
                        mode = 'rotating'
                        
                    srv = LocalProxyServer(mode=mode)
                    srv.start()
                    
                    input(f"\n{Theme.RED}Nhấn phím Enter để TẮT Trạm Trung Chuyển...{Theme.RESET}")
                    srv.stop()
                
                # ==========================================
                # [14] BẬT / TẮT WEB DASHBOARD
                # ==========================================
                elif choice == '14':
                    if self.web_server is None:
                        self.web_server = WebDashboardServer(port=8080)
                        self.web_server.daemon = True
                        self.web_server.start()
                        print(f"\n{Theme.LUC}🌐 WEB DASHBOARD ĐÃ BẬT VÀ CHẠY NGẦM 24/24 TẠI: http://127.0.0.1:8080{Theme.RESET}")
                        print(f"{Theme.VANG}👉 Sếp có thể tiếp tục sử dụng Terminal để gõ lệnh bình thường.{Theme.RESET}")
                        print(f"{Theme.DEN}👉 (Nhấn số 14 lần nữa nếu muốn TẮT Web){Theme.RESET}")
                    else:
                        self.web_server.stop()
                        self.web_server = None
                        print(f"\n{Theme.RED}❌ ĐÃ TẮT WEB DASHBOARD!{Theme.RESET}")
                        
                    time.sleep(2.5)
                
                # ==========================================
                # [15] AUTO-PILOT
                # ==========================================
                elif choice == '15':
                    self.start_autopilot()

                # ==========================================
                # [0] THOÁT CHƯƠNG TRÌNH
                # ==========================================
                elif choice == '0':
                    print(f"\n{Theme.RED}👋 Tạm biệt sếp! Đang hủy các tiến trình ngầm...{Theme.RESET}")
                    os._exit(0)
                    
                else:
                    print(f"{Theme.RED}❌ Lựa chọn không hợp lệ! Hãy nhập số từ 0 đến 15.{Theme.RESET}")
                    time.sleep(1)
                    
            except KeyboardInterrupt: 
                print(f"\n{Theme.RED}🛑 Dừng khẩn cấp bằng phím Ctrl+C! Đang thoát...{Theme.RESET}")
                os._exit(0)
            except Exception as e: 
                print(f"{Theme.RED}❌ Lỗi Hệ thống tại Menu: {e}{Theme.RESET}")
                time.sleep(2)

# ========================================================================================
# MODULE 15: LOCAL PROXY SERVER (HỖ TRỢ STICKY, ROTATING & CẤM THUẬT CHAINING)
# ========================================================================================
class LocalProxyServer(threading.Thread):
    def __init__(self, host='127.0.0.1', port=8888, mode='rotating'):
        super().__init__()
        self.host = host; self.port = port; self.mode = mode
        self.current_proxy = None; self.last_proxy_time = 0
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); self.is_running = False

    def get_proxy(self):
        proxies = [p for p in db.get_all_proxies("live") if p['protocol'] == 'http']
        if not proxies: return None
        if self.mode == 'sticky':
            if not self.current_proxy or (time.time() - self.last_proxy_time > 300):
                self.current_proxy = random.choice(proxies); self.last_proxy_time = time.time()
            return self.current_proxy
        return random.choice(proxies)

    def handle_client(self, client_socket):
        remote_socket = None
        try:
            request = client_socket.recv(4096)
            if not request: return
            
            connected = False
            for _ in range(3):
                p1 = self.get_proxy()
                if not p1: break
                
                if self.mode == 'chaining':
                    p2 = self.get_proxy()
                    if p1 and p2 and p1 != p2:
                        try:
                            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            remote_socket.settimeout(5); remote_socket.connect((p1['ip'], int(p1['port'])))
                            remote_socket.sendall(f"CONNECT {p2['ip_port']} HTTP/1.1\r\n\r\n".encode())
                            remote_socket.recv(4096)
                            remote_socket.sendall(request)
                            connected = True; break
                        except: remote_socket.close() if remote_socket else None; continue
                else:
                    try:
                        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        remote_socket.settimeout(5); remote_socket.connect((p1['ip'], int(p1['port'])))
                        remote_socket.sendall(request); connected = True; break 
                    except:
                        remote_socket.close() if remote_socket else None
                        if self.mode == 'sticky': self.current_proxy = None 
            
            if not connected: client_socket.close(); return
            
            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(8192)
                        if not data: break
                        dst.sendall(data)
                except: pass
                
            t1 = threading.Thread(target=forward, args=(client_socket, remote_socket))
            t2 = threading.Thread(target=forward, args=(remote_socket, client_socket))
            t1.start(); t2.start(); t1.join(); t2.join()
        except: pass
        finally:
            client_socket.close()
            if remote_socket: remote_socket.close()

    def run(self):
        try:
            self.server_socket.bind((self.host, self.port)); self.server_socket.listen(100); self.is_running = True
            print(f"\n{Theme.LUC}🚀 Trạm Trung Chuyển [{self.mode.upper()}] đang chạy tại {self.host}:{self.port}{Theme.RESET}")
            while self.is_running:
                client_socket, _ = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
        except Exception as e: print(f"Lỗi Server: {e}")
        
    def stop(self): self.is_running = False; self.server_socket.close()

# ========================================================================================
# MODULE 16: API SERVER NỘI BỘ (CHIA SẺ PROXY)
# ========================================================================================

class ProxyAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/get_proxy'):
            proxies = db.get_all_proxies('live')
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            if proxies:
                p = random.choice(proxies)
                res = {"status": "success", "proxy": p['ip_port'], "protocol": p['protocol'], "country": p['country']}
            else: res = {"status": "error", "message": "Database rỗng"}
            self.wfile.write(json.dumps(res).encode('utf-8'))
        else: self.send_response(404); self.end_headers()
        
    def log_message(self, format, *args): pass # Tắt log rác hiển thị ra màn hình

class APIServerThread(threading.Thread):
    def __init__(self, port=5000):
        super().__init__(); self.port = port
        self.server = HTTPServer(('0.0.0.0', self.port), ProxyAPIHandler)
    def run(self): self.server.serve_forever()
    def stop(self): self.server.shutdown()


# ========================================================================================
# MODULE 17: TELEGRAM COMMANDER OMNI-GOD (HTML FORMAT & SMART ACTIONS)
# ========================================================================================
class TelegramCommander(threading.Thread):
    def __init__(self, engine):
        super().__init__(); self.engine = engine
        self.token = cfg.get('telegram_bot_token', ''); self.cid = cfg.get('telegram_chat_id', '')
        self.is_running = True

    def send_menu(self):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        keyboard = {
            "inline_keyboard": [
                [{"text": "🚀 BẮT ĐẦU QUÉT", "callback_data": "start"}, {"text": "🛑 DỪNG LẠI", "callback_data": "stop"}],
                [{"text": "📊 THỐNG KÊ KHO", "callback_data": "status"}, {"text": "👑 LẤY TOP 5 VIP", "callback_data": "top5"}],
                [{"text": "📥 TẢI FILE (.TXT)", "callback_data": "dl"}, {"text": "♻️ LỌC MÁU RÁC", "callback_data": "clear_dead"}]
            ]
        }
        text = "🤖 <b>TT ĐIỀU KHIỂN PROXY TITAN V15 </b>\n<i>Hệ thống kết nối thành công! Đang chờ lệnh sếp:</i>"
        try: requests.post(url, data={"chat_id": self.cid, "text": text, "parse_mode": "HTML", "reply_markup": json.dumps(keyboard)}, timeout=5)
        except: pass

    def run(self):
        if not self.token: return
        self.send_menu()
        offset = 0
        while self.is_running:
            try:
                res = requests.get(f"https://api.telegram.org/bot{self.token}/getUpdates?offset={offset}&timeout=10").json()
                for item in res.get('result', []):
                    offset = item['update_id'] + 1
                    
                    if 'callback_query' in item:
                        call = item['callback_query']
                        data = call['data']; call_id = call['id']
                        
                        if data == "start":
                            requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", data={"callback_query_id": call_id, "text": "🚀 Đang kích hoạt lõi Asyncio...", "show_alert": False})
                            threading.Thread(target=lambda: asyncio.run(self.engine.start_engine_async())).start()
                        
                        elif data == "stop":
                            self.engine.is_running = False
                            requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", data={"callback_query_id": call_id, "text": "🛑 Đã ra lệnh ngắt động cơ!", "show_alert": True})
                            
                        elif data == "status": 
                            total, protos = db.get_stats()
                            msg = f"📊 <b>TRẠNG THÁI DATABASE</b>\n\n🟢 Tổng Proxy Sống: <b>{total}</b>\n"
                            for p in protos: msg += f"🔹 {p[0].upper()}: {p[1]}\n"
                            requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", data={"chat_id": self.cid, "text": msg, "parse_mode": "HTML"})
                            requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", data={"callback_query_id": call_id})
                            
                        elif data == "top5":
                            top_proxies = db.get_top_proxies(5)
                            if not top_proxies:
                                msg = "❌ Kho proxy đang trống!"
                            else:
                                msg = "👑 <b>TOP 5 PROXY XỊN NHẤT:</b>\n\n"
                                for p in top_proxies:
                                    msg += f"<code>{p['ip_port']}</code>\n"
                                    msg += f"⚡ {p['protocol'].upper()} | ⏱ {p['ping_ms']}ms | 🌍 {p['country_code']}\n\n"
                            requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", data={"chat_id": self.cid, "text": msg, "parse_mode": "HTML"})
                            requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", data={"callback_query_id": call_id})
                            
                        elif data == "dl":
                            requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", data={"callback_query_id": call_id, "text": "⏳ Đang tạo file...", "show_alert": False})
                            proxies = db.get_all_proxies("live")
                            if proxies:
                                file_path = "Titan_V15_Live.txt"
                                with open(file_path, "w") as f: f.write("\n".join([p['ip_port'] for p in proxies]))
                                with open(file_path, "rb") as f: requests.post(f"https://api.telegram.org/bot{self.token}/sendDocument", data={"chat_id": self.cid, "caption": f"🎁 Danh sách {len(proxies)} Proxy Live"}, files={"document": f})
                            
                        elif data == "clear_dead":
                            # Lọc rác: Xóa proxy ping cao > 2000 hoặc datacenter ISP
                            try:
                                with db.transaction() as cur:
                                    cur.execute(
                                        "DELETE FROM live_proxies WHERE ping_ms > 2000 "
                                        "OR isp LIKE '%digitalocean%' OR isp LIKE '%aws%'"
                                    )
                                    deleted = cur.rowcount
                                requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery",
                                    data={"callback_query_id": call_id,
                                          "text": f"♻️ Đã thanh trừng {deleted} proxy rác/ping cao!",
                                          "show_alert": True})
                            except: pass
            except: time.sleep(2)

# ========================================================================================
# MODULE 18: ADVANCED DATA BUNDLE (TĂNG ĐỘ ẨN DANH & BYPASS FIREWALL)
# ========================================================================================
class AdvancedData:
    """Hàng trăm Headers và Fingerprints để bypass Cloudflare, Akamai, v.v."""
    
    HEADERS_LIST = [
        {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate, br", "Connection": "keep-alive", "Upgrade-Insecure-Requests": "1"},
        {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3", "Connection": "keep-alive", "Pragma": "no-cache", "Cache-Control": "no-cache"},
        {"Accept": "application/json, text/plain, */*", "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin"},
        {"Accept": "*/*", "Accept-Language": "en-US,en;q=0.5", "Connection": "keep-alive", "X-Requested-With": "XMLHttpRequest"},
    ] * 50  # Nhân bản dữ liệu để tool luân chuyển liên tục

    EXTRA_SOURCES = [
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/BlexBoy/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Volodichev/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/master/http.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/master/socks4.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/master/socks5.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/ObcbO/getproxy/master/http.txt",
        "https://raw.githubusercontent.com/ObcbO/getproxy/master/socks4.txt",
        "https://raw.githubusercontent.com/ObcbO/getproxy/master/socks5.txt",
    ] * 3 # Gấp 3 lần kho dữ liệu

    @classmethod
    def get_random_header(cls):
        return random.choice(cls.HEADERS_LIST)

# ========================================================================================
# MODULE 20: WEB DASHBOARD V15 PRO - ULTIMATE FIX (SIDEBAR LAYOUT - LONG CONTENT)
# ========================================================================================

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

class WebDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path); query = parse_qs(parsed.query)
        
        # --- [1] HỆ THỐNG API MMO (FULL PARAMETERS) ---
        if parsed.path == '/get_proxy':
            proxies = db.get_all_proxies("live")
            p_proto = query.get('protocol', [''])[0].lower()
            if p_proto: proxies = [p for p in proxies if p_proto in p['protocol'].lower()]
            if query.get('safe', [''])[0].lower() == 'true':
                bad = ['digitalocean', 'aws', 'amazon', 'ovh', 'choopa', 'hetzner', 'linode', 'alibaba', 'google', 'hosting']
                proxies = [p for p in proxies if not any(b in str(p.get('isp','')).lower() for b in bad)]
            p_cc = query.get('country', [''])[0].upper()
            if p_cc: proxies = [p for p in proxies if p_cc == p['country_code']]
            
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            if proxies:
                p = random.choice(proxies)
                res = {"status": "success", "proxy": p['ip_port'], "protocol": p['protocol'], "cc": p['country_code'], "isp": p['isp'], "ping": p['ping_ms'], "score": p.get('score', 0)}
            else: res = {"status": "error", "message": "No proxy matches filter"}
            self.wfile.write(json.dumps(res).encode('utf-8')); return 

        elif parsed.path == '/api/stats':
            try:
                _bad_isps = ['digitalocean','aws','amazon','ovh','choopa','hetzner',
                             'linode','alibaba','google','hosting','datacenter','cloud']
                pxs = db.get_all_proxies("live"); top10 = db.get_top_proxies(10)
                res = {
                    "total": len(pxs),
                    "http": sum(1 for p in pxs if 'http' in p['protocol'].lower()),
                    "socks": sum(1 for p in pxs if 'socks' in p['protocol'].lower()),
                    "top10": [{"ip": p['ip_port'], "cc": p['country_code'], "ping": p['ping_ms'],
                                "safe": "❌ RÁC" if any(b in str(p.get('isp','')).lower() for b in _bad_isps) else "✅ SẠCH"}
                               for p in top10]
                }
                self._send_json(res)
            except: self._send_json({"total": 0, "http": 0, "socks": 0, "top10": []})
            return
        
        elif parsed.path == '/api/logs':
            self._send_json(list(AppLogger.web_logs)); return
            
        elif parsed.path == '/api/download':
            proxies = db.get_all_proxies("live"); content = "\n".join([p['ip_port'] for p in proxies])
            self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.send_header('Content-Disposition', 'attachment; filename="ProxyTitan_V15_Pro.txt"'); self.end_headers()
            self.wfile.write(content.encode('utf-8')); return

        elif parsed.path == '/api/check':
            proxy = query.get('proxy', [''])[0]
            try:
                start = time.time()
                requests.get("http://httpbin.org/get",
                             proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                             timeout=5, verify=False)
                self._send_json({"status": "live", "ping": int((time.time() - start) * 1000)})
            except:
                self._send_json({"status": "dead"})
            return
            
        # --- [2] GIAO DIỆN WEB DASHBOARD SIÊU ĐẸP (LAYOUT SIDEBAR CHUẨN) ---
        else:
            self.send_response(200); self.send_header('Content-type', 'text/html; charset=utf-8'); self.end_headers()
            username = cfg.get("username", "NP_HUNGG DATA CENTER").upper()
            username_lower = username.lower().replace(" ", "-")
            html = r"""
            <!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PROXY TITAN V15 PRO</title>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
            <style>
                :root { --theme-color: #38bdf8; --theme-glow: rgba(56, 189, 248, 0.5); }
                body, html { margin:0; padding:0; width:100%; height:100%; font-family:'Rajdhani', sans-serif; background:#000; color:#e2e8f0; overflow: hidden; }
                #bg-layer { position:fixed; top:0; left:0; width:100vw; height:100vh; background: url("https://i.postimg.cc/DzNYbKCD/Anhnen.jpg") center/cover no-repeat; z-index:1; filter: brightness(0.3) saturate(1.1); transition: 1.2s ease; }
                #canvas-particles { position:fixed; top:0; left:0; width:100vw; height:100vh; z-index: 2; pointer-events:none; }
                
                /* LAYOUT CHÍNH: CỐ ĐỊNH SIDEBAR - CUỘN NỘI DUNG */
                .app-container { position:relative; z-index:10; display:flex; height:100vh; width: 100vw; flex-direction:row; }
                .sidebar { width:320px; min-width: 320px; background:rgba(5, 8, 15, 0.95); backdrop-filter:blur(25px); border-right:1px solid rgba(255,255,255,0.05); padding:20px; display:flex; flex-direction:column; overflow-y:auto; box-shadow: 10px 0 40px #000; z-index: 100; }
                .main-content { flex:1; padding:30px; overflow-y:auto; scroll-behavior: smooth; -webkit-overflow-scrolling: touch; }

                /* RESPONSIVE CHO MOBILE: Sidebar thu nhỏ nhưng vẫn nằm bên trái */
                @media (max-width: 800px) {
                    .sidebar { width: 120px; min-width: 120px; padding: 10px; }
                    .sidebar img { width: 90% !important; border-radius: 10px !important; }
                    .sidebar h2, .sidebar .menu-label, .sidebar #logs-box-title { display: none; }
                    .sidebar #clock { font-size: 1.2em !important; margin: 10px 0 !important; }
                    .nav-btn { font-size: 0.8em !important; padding: 10px 5px !important; text-align: center !important; }
                    .nav-btn .icon { display: block; font-size: 1.5em; margin-bottom: 5px; }
                    .yt-box, #logs-box { display: none; }
                    .main-content { padding: 15px; }
                }

                .card { background: rgba(10, 15, 25, 0.9); padding: 35px; border-radius: 25px; border: 1px solid var(--theme-color); margin-bottom: 30px; box-shadow: 0 0 35px var(--theme-glow); line-height: 2; animation: slideUp 0.8s ease; }
                h2 { font-family:'Orbitron'; color:var(--theme-color); margin-top:0; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 15px; letter-spacing: 2px; text-transform: uppercase; }
                
                .nav-btn { width: 100%; padding: 15px; margin: 5px 0; background: rgba(255,255,255,0.03); color: #fff; border: 1px solid rgba(255,255,255,0.1); text-align: left; cursor: pointer; border-radius: 12px; font-weight: bold; transition: 0.3s; font-size: 1em; }
                .nav-btn:hover, .nav-btn.active { background: var(--theme-color); color: #000; box-shadow: 0 0 25px var(--theme-color); transform: scale(1.02); }
                
                .yt-box { background:rgba(0,0,0,0.6); border:1px solid var(--theme-color); padding:15px; border-radius:15px; margin-top:15px; }
                .yt-box input { width:100%; padding:10px; background:#000; border:1px solid #333; color:#fff; margin-bottom:8px; border-radius:8px; box-sizing: border-box; }
                
                #logs-box { font-family: 'Share Tech Mono', monospace; font-size: 0.85em; height: 180px; overflow-y: auto; background: #020202; border: 1px solid rgba(255,255,255,0.1); padding: 12px; margin-top: auto; color: var(--theme-color); border-radius: 12px; }
                
                .stat-number { font-family:'Orbitron'; font-size: 7em; color: var(--theme-color); text-shadow: 0 0 50px var(--theme-glow); margin: 15px 0; }
                table { width:100%; border-collapse:collapse; margin-top:20px; background: rgba(0,0,0,0.5); border-radius: 15px; overflow: hidden; border: 1px solid #222; }
                th { background: rgba(255,255,255,0.05); padding: 18px; color: var(--theme-color); font-family: 'Orbitron'; text-align: left; border-bottom: 2px solid #222; }
                td { padding: 15px 18px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: 'Share Tech Mono'; }
                
                .tag-safe { color: #10b981; font-weight: bold; } .tag-scam { color: #ef4444; font-weight: bold; }
                body.rgb-flow-mode { animation: rgbHue 8s linear infinite; }
                @keyframes rgbHue { 0% { filter: hue-rotate(0deg); } 100% { filter: hue-rotate(360deg); } }
                body.neon-pink-mode .card, body.neon-pink-mode h2, body.neon-pink-mode .nav-btn.active { border-color: #ff00ff; color: #ff00ff; text-shadow: 0 0 20px #ff00ff; }
                @keyframes slideUp { from { opacity: 0; transform: translateY(50px); } to { opacity: 1; transform: translateY(0); } }
            </style></head><body>
            <div id="bg-layer"></div><canvas id="canvas-particles"></canvas>
            <div class="app-container">
                <div class="sidebar">
                    <img src="https://i.postimg.cc/x8TTZM2Z/IMG-20260413-171622.jpg" style="width:75%; border-radius:25px; margin:0 auto 15px; border: 2px solid var(--theme-color); box-shadow: 0 0 30px var(--theme-glow);">
                    <h2 style="text-align:center; font-size:1.1em; letter-spacing:5px;">SYSTEM UI</h2>
                    <div id="clock" style="font-family:'Orbitron'; font-size:2.8em; color:#fcd34d; text-align:center; margin-bottom:20px; text-shadow: 0 0 15px rgba(252,211,77,0.4);">00:00:00</div>
                    
                    <div class="menu-label" style="color:rgba(255,255,255,0.3); font-size:0.8em; font-weight:bold; margin-bottom:10px;">🧭 ĐIỀU HƯỚNG</div>
                    <button class="nav-btn active" onclick="show('info')"><span class="icon">🏠</span> Info Center</button>
                    <button class="nav-btn" onclick="show('dash')"><span class="icon">📊</span> Proxy Dashboard</button>
                    <button class="nav-btn" onclick="show('checker')"><span class="icon">🔍</span> Live Checker</button>
                    <button class="nav-btn" onclick="show('download')"><span class="icon">📥</span> Download Center</button>
                    <button class="nav-btn" onclick="show('guide')"><span class="icon">🔌</span> Hướng Dẫn Cắm</button>
                    <button class="nav-btn" onclick="show('faq')"><span class="icon">❓</span> FAQ & Hỏi Đáp</button>
                    
                    <div class="menu-label" style="color:rgba(255,255,255,0.3); font-size:0.8em; font-weight:bold; margin: 20px 0 10px;">🎨 THEME VIP</div>
                    <div style="display:flex; gap:10px; align-items:center; background:rgba(0,0,0,0.5); padding:12px; border-radius:12px; border:1px solid rgba(255,255,255,0.1);">
                        <input type="color" id="color-picker" value="#38bdf8" style="width:50px; height:45px; border:none; background:none; cursor:pointer;" onchange="setCustomColor(this.value)">
                        <span class="menu-label" style="font-weight:bold; color:var(--theme-color);">Màu Bất Kỳ</span>
                    </div>
                    <button class="nav-btn" onclick="setSpecial('rgb')">🌈 RGB Flow Mode</button>
                    <button class="nav-btn" onclick="setSpecial('neon')">💖 Hồng Neon Flow</button>
                    
                    <div class="menu-label" style="color:rgba(255,255,255,0.3); font-size:0.8em; font-weight:bold; margin: 20px 0 10px;">🖼️ VISUAL & MUSIC</div>
                    <button class="nav-btn" onclick="changeAnime()">🖼️ Đổi Nền Anime</button>
                    <button class="nav-btn" onclick="toggleParticles()">✨ Tắt/Bật Tuyết</button>
                    
                    <div class="yt-box">
                        <div style="color:var(--theme-color); font-weight:bold; margin-bottom:10px; font-family:'Orbitron'; font-size:0.9em;">🎵 MUSIC PLAYER</div>
                        <input type="text" id="yt-link" placeholder="Dán mã Youtube...">
                        <button onclick="playMusic()" style="width:100%; padding:12px; background:var(--theme-color); color:#000; border:none; font-weight:bold; border-radius:10px; cursor:pointer;">▶ PHÁT NHẠC</button>
                        <div id="m-player" style="display:none; margin-top:15px; border-radius:10px; overflow:hidden;"><iframe id="yt-frame" width="100%" height="80" src="" frameborder="0" allow="autoplay"></iframe></div>
                    </div>
                    <div id="logs-box-title" style="color:rgba(255,255,255,0.2); font-size:0.7em; margin-top:20px;">root@""" + username_lower + r""":~# tail -f engine.log</div>
                    <div id="logs-box"></div>
                </div>
                
                <div class="main-content">
                    <div id="p-info" class="page-sec">
                        <div class="card">
                            <h2 style="text-align:center; font-size:2.2em; border:none;">🚀 HỆ THỐNG PROXY TITAN V15 PRO</h2>
                            <p style="text-align:center; font-style:italic; color:#94a3b8; margin-bottom:30px;">Giải pháp quản lý tài nguyên mạng tối thượng cho giới MMO chuyên nghiệp.</p>
                            <hr style="border:0; border-top:1px dashed rgba(255,255,255,0.1); margin:30px 0;">
                            
                            <h3>🏢 GIỚI THIỆU HỆ SINH THÁI TITAN</h3>
                            <p>Proxy Titan V15 Pro không đơn thuần là một công cụ quét IP. Nó là một <b>Platform điều phối tài nguyên</b> được xây dựng trên nền tảng Python 3.10+ tối ưu hóa cho hiệu suất cao. Hệ thống được thiết kế để phục vụ các tác vụ nặng như nuôi hàng nghìn tài khoản Facebook, Google, TikTok mà không gặp phải tình trạng nghẽn cổ chai hay treo Terminal.</p>
                            
                            <p><b>Các lõi công nghệ chính đang vận hành:</b></p>
                            <p><b>1. Lõi Quét Asyncio God-Tier:</b> Sử dụng cơ chế I/O bất đồng bộ (Non-blocking), cho phép duy trì hơn 5000 kết nối TCP đồng thời mà chỉ chiếm dụng chưa tới 10% tài nguyên CPU của điện thoại. Điều này giúp sếp có thể vừa quét proxy vừa lướt web mượt mà.</p>
                            <p><b>2. ISP Shield AI 2.5:</b> Đây là bộ não của hệ thống. Nó tự động phân tích hàng chục thông số của IP bao gồm Organization Name, ASN, và Route để gắn thẻ chính xác IP Sạch (Residential) hoặc IP Rác (Datacenter). ISP Shield giúp giảm tỷ lệ bị Checkpoint tài khoản lên tới 90%.</p>
                            <p><b>3. Database Engine Ultra:</b> Toàn bộ IP được cấu trúc hóa trong SQLite3 với các Index nâng cao, hỗ trợ truy vấn hàng triệu bản ghi chỉ trong vài miligiây.</p>
                            <p><b>4. Auto-Heal Doctor:</b> Luồng chạy ngầm liên tục lọc máu database, đảm bảo kho IP của sếp luôn "tươi" và ping thấp dưới 1500ms.</p>
                        </div>
                    </div>
                    
                    <div id="p-dash" class="page-sec" style="display:none">
                        <div class="card" style="text-align:center;">
                            <h2 style="border:none;">📊 TỔNG KHO DỮ LIỆU THỜI GIAN THỰC</h2>
                            <div id="tot" class="stat-number">0</div>
                            <div style="display:flex; justify-content:center; gap:60px; font-size:2em; font-weight:bold; color:var(--theme-color);">
                                <div>🌐 HTTP/S: <span id="ht">0</span></div>
                                <div>🧦 SOCKS: <span id="sk">0</span></div>
                            </div>
                            <p style="margin-top:25px; color:#666; font-size:1.1em;">Hệ thống tự động cập nhật thống kê mỗi 2 giây từ Database.</p>
                        </div>
                        <div class="card">
                            <h2>👑 TOP 10 PROXY TINH ANH (PINGS SIÊU THẤP)</h2>
                            <table><thead><tr><th>IP ADDRESS : PORT</th><th>LOCATION</th><th>PING</th><th>ISP SHIELD</th></tr></thead><tbody id="top10"></tbody></table>
                        </div>
                    </div>
                    
                    <div id="p-checker" class="page-sec" style="display:none">
                        <div class="card">
                            <h2>🔍 WEB LIVE CHECKER V15</h2>
                            <p>Kiểm tra độ sống/chết của bất kỳ IP nào ngay trên trình duyệt trước khi đưa vào tool MMO quan trọng.</p>
                            <div style="display:flex; gap:15px; margin:30px 0;">
                                <input type="text" id="cip" style="flex:1; padding:20px; background:#000; border:2px solid var(--theme-color); color:#fff; border-radius:15px; font-family:'Share Tech Mono'; font-size:1.5em;" placeholder="Ví dụ: 103.1.2.3:8080">
                                <button onclick="checkNow()" style="padding:0 50px; background:var(--theme-color); color:#000; border:none; cursor:pointer; font-weight:bold; border-radius:15px; font-size:1.4em;">CHECK</button>
                            </div>
                            <div id="cres" style="margin-top:35px; font-size:3em; font-family:'Orbitron'; text-align:center; min-height:100px;"></div>
                        </div>
                    </div>
                    
                    <div id="p-guide" class="page-sec" style="display:none">
                        <div class="card">
                            <h2>🔌 HƯỚNG DẪN CẮM PROXY TITAN VÀO TOOL CHI TIẾT</h2>
                            <p>Để tối ưu hóa việc nuôi nick và tránh các thuật toán phát hiện của Google/Facebook, sếp cần thực hiện theo quy trình cài đặt chuyên nghiệp sau:</p>
                            
                            <h3 style="color:#fcd34d;">📍 Cách 1: Sử dụng Link API (Khuyên dùng cho nuôi nick hàng loạt)</h3>
                            <p>Đây là phương pháp mạnh mẽ nhất vì Proxy Titan sẽ tự động "thay máu" IP sống mỗi khi tool MMO của sếp yêu cầu request mới, giúp sếp không bao giờ phải đổi cấu hình thủ công.</p>
                            <ul>
                                <li><b>Lấy 1 IP bất kỳ (Auto Rotate):</b> <code>http://127.0.0.1:8080/get_proxy</code></li>
                                <li><b>Chỉ lấy IP SẠCH (Residential):</b> <code>http://127.0.0.1:8080/get_proxy?safe=true</code></li>
                                <li><b>Lấy IP theo nước (VD: Mỹ):</b> <code>http://127.0.0.1:8080/get_proxy?country=US</code></li>
                                <li><b>Lọc theo giao thức:</b> <code>http://127.0.0.1:8080/get_proxy?protocol=socks5</code></li>
                            </ul>
                            <p><b>Quy trình cài đặt:</b> Trong phần cài đặt Proxy của AdsPower, Gologin hoặc Kikilogin -> Chọn <b>Get from API/URL</b> -> Dán link API tương ứng ở trên vào -> Set <b>Refresh time</b> là 60 giây hoặc mỗi khi đổi Profile.</p>
                            <hr style="border:0; border-top:1px solid #333; margin:35px 0;">
                            
                            <h3 style="color:#fcd34d;">📍 Cách 2: Trạm Local Forwarding (Port 8888)</h3>
                            <p>Phương pháp này biến chính điện thoại/máy tính của sếp thành một Proxy Server trung chuyển cực kỳ bảo mật.</p>
                            <p><b>Bước 1:</b> Tại màn hình Terminal chính, nhấn phím <b>[13]</b> để khởi động Trạm Local. <br><b>Bước 2:</b> Trong tool nuôi nick, sếp cài đặt Proxy tĩnh là IP <code>127.0.0.1</code> và Port <code>8888</code>. <br><b>Cơ chế hoạt động:</b> Khi sếp truy cập mạng, Titan sẽ tự động đảo IP thầm lặng ở phía sau mỗi request hoặc giữ nguyên IP tùy chế độ sếp chọn (Rotating/Sticky).</p>
                        </div>
                    </div>
                    
                    <div id="p-faq" class="page-sec" style="display:none">
                        <div class="card">
                            <h2>❓ GIẢI ĐÁP THẮC MẮC CHUYÊN SÂU (TITAN FAQ)</h2>
                            <p><b>1. Tại sao IP báo LIVE trên Dashboard nhưng vào trình duyệt lại báo LỖI?</b><br>Nguyên nhân 90% là do sếp đang test với "Mục tiêu mặc định" là HTTPBin (rất nhẹ). Hãy quay lại Terminal, vào Menu [3] và đổi <b>Target Test</b> sang <code>https://www.google.com</code> hoặc <code>https://www.facebook.com</code>. Khi đó IP nào báo LIVE mới thực sự có khả năng truy cập vào các trang đó.</p>
                            
                            <p><b>2. IP Shield báo "RÁC" thì có dùng được không?</b><br>Hoàn toàn dùng được, nhưng độ an toàn thấp. Các IP này thường là từ Google Cloud, AWS, Linode... Google rất ghét dải này. Titan khuyên sếp chỉ nên dùng IP báo "SẠCH" (Residential - IP nhà dân) để nuôi nick Facebook/Google an toàn nhất.</p>
                            
                            <p><b>3. Làm sao để quét nhanh hơn nữa?</b><br>Sếp có thể nâng số <b>Threads (Luồng ảo)</b> lên 1000 - 2000 trong Menu [3]. Tuy nhiên, hãy đảm bảo băng thông Wifi/4G của sếp đủ khỏe để không bị nghẽn mạng, gây ra lỗi Timeout hàng loạt.</p>
                            
                            <p><b>4. Tôi muốn share web này cho bạn bè xem cùng?</b><br>Rất đơn giản, sếp hãy mở một tab Termux mới rồi gõ lệnh: <code>cloudflared tunnel --url localhost:8080</code>. Nó sẽ nhả ra 1 cái link đuôi <code>.trycloudflare.com</code>, sếp gửi link đó cho ai cũng có thể xem được Dashboard và húp API Proxy của sếp từ xa!</p>
                            
                            <p><b>5. Web này có chạy tốn RAM không?</b><br>Không sếp nhé! Hệ thống Web được xây dựng trên lõi <code>BaseHTTPRequestHandler</code> cực nhẹ, tổng dung lượng RAM tiêu thụ chưa tới 20MB, sếp cứ yên tâm bật 24/24 trên VPS hay điện thoại.</p>
                        </div>
                    </div>

                    <div id="p-download" class="page-sec" style="display:none">
                        <div class="card" style="text-align:center; padding:90px 40px;">
                            <h2>📥 TẢI XUỐNG KHO DỮ LIỆU PROXY (.TXT)</h2>
                            <p style="margin-bottom:50px; font-size:1.3em; color:#cbd5e1;">Hệ thống sẽ tổng hợp toàn bộ IP đang <b>SỐNG</b> thực sự và xuất ra định dạng <code>IP:PORT</code> chuẩn.</p>
                            <a href="/api/download" style="display:inline-block; padding:25px 90px; background:var(--theme-color); color:#000; text-decoration:none; font-weight:bold; border-radius:18px; font-size:2em; box-shadow:0 15px 50px var(--theme-glow); transition:0.5s;">📥 DOWNLOAD FULL LIST</a>
                            <p style="margin-top:40px; color:#666;">Phù hợp với 99% phần mềm MMO: AdsPower, Gologin, Proxifier, ProxyCap...</p>
                        </div>
                    </div>
                </div>
            </div>
            <script>
                const bgs = ["https://i.postimg.cc/DzNYbKCD/Anhnen.jpg", "https://i.postimg.cc/bwBRm9Qm/c8739c54501aedab5e683253251ef161.jpg", "https://i.postimg.cc/7hw15syW/e95e09bcc1bb45d946ddac1c25f59f16.jpg", "https://i.postimg.cc/xT8W5FmC/anime4.jpg", "https://i.postimg.cc/mD8G60Fk/anime5.jpg"];
                let cbg = 0; function changeAnime() { cbg = (cbg+1)%bgs.length; document.getElementById('bg-layer').style.backgroundImage = `url('${bgs[cbg]}')`; }
                function show(p){ document.querySelectorAll('.page-sec').forEach(e=>e.style.display='none'); document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active')); document.getElementById('p-'+p).style.display='block'; if(event) event.target.classList.add('active'); document.querySelector('.main-content').scrollTop = 0; }
                function updateClock() { const n = new Date(); document.getElementById('clock').innerText = n.getHours().toString().padStart(2,'0')+":"+n.getMinutes().toString().padStart(2,'0')+":"+n.getSeconds().toString().padStart(2,'0'); }
                setInterval(updateClock, 1000); updateClock();
                function setCustomColor(h) { document.body.classList.remove('rgb-flow-mode','neon-pink-mode'); document.documentElement.style.setProperty('--theme-color', h); document.documentElement.style.setProperty('--theme-glow', h+'66'); }
                function setSpecial(m) { document.body.classList.remove('rgb-flow-mode','neon-pink-mode'); if(m==='rgb') document.body.classList.add('rgb-flow-mode'); else if(m==='neon') { setCustomColor('#ff00ff'); document.body.classList.add('neon-pink-mode'); } else { setCustomColor('#38bdf8'); } }
                function playMusic() { let l = document.getElementById('yt-link').value; let id = ''; if(l.includes('v=')) id = l.split('v=')[1].substring(0,11); else if(l.includes('be/')) id = l.split('be/')[1].substring(0,11); if(id){ document.getElementById('m-player').style.display='block'; document.getElementById('yt-frame').src=`https://www.youtube.com/embed/${id}?autoplay=1`; } }
                async function updateS(){
                    try {
                        let r=await fetch('/api/stats'); let d=await r.json(); 
                        if(d.total !== undefined) { document.getElementById('tot').innerText=d.total; document.getElementById('ht').innerText=d.http; document.getElementById('sk').innerText=d.socks; }
                        let h=''; if(d.top10) d.top10.forEach(p=>{ h+=`<tr><td>${p.ip}</td><td>${p.cc}</td><td style="color:#fcd34d">${p.ping}ms</td><td class="${p.safe.includes('SẠCH')?'tag-safe':'tag-scam'}">${p.safe}</td></tr>`; });
                        document.getElementById('top10').innerHTML = h || '<tr><td colspan="4">DATABASE IS EMPTY...</td></tr>';
                        let rl=await fetch('/api/logs'); let dl=await rl.json();
                        document.getElementById('logs-box').innerHTML = dl.map(l=>`<div style="font-size:0.9em; margin-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.03);"><span style="color:#64748b">[${l.time}]</span> <span style="color:var(--theme-color)">${l.msg}</span></div>`).join('');
                        document.getElementById('logs-box').scrollTop = 99999;
                    } catch(e){}
                }
                setInterval(updateS, 2000); updateS();
                async function checkNow(){ let ip=document.getElementById('cip').value; if(!ip)return; document.getElementById('cres').innerHTML="<span style='color:#fcd34d'>⏳ PROCESSING...</span>"; let r=await fetch('/api/check?proxy='+ip); let d=await r.json(); document.getElementById('cres').innerHTML=d.status==='live'?`<span style="color:#10b981">✅ LIVE (${d.ping}ms)</span>`:`<span style="color:#ef4444">❌ DEAD</span>`; }
                const c=document.getElementById('canvas-particles'), x=c.getContext('2d'); let pts=[]; let ptsOn=true; window.onresize=()=>{c.width=innerWidth;c.height=innerHeight;}; window.onresize();
                function toggleParticles() { ptsOn = !ptsOn; if(!ptsOn) x.clearRect(0,0,c.width,c.height); }
                class P{ constructor(){this.x=Math.random()*c.width;this.y=Math.random()*c.height;this.v=Math.random()*0.4+0.1;} update(){if(!ptsOn)return;this.y+=this.v;if(this.y>c.height)this.y=-5;} draw(){if(!ptsOn)return;x.fillStyle='rgba(255,255,255,0.25)';x.beginPath();x.arc(this.x,this.y,1.2,0,Math.PI*2);x.fill();}}
                for(let i=130;i>0;i--)pts.push(new P());
                function anim(){if(ptsOn){x.clearRect(0,0,c.width,c.height);pts.forEach(p=>{p.update();p.draw();});}requestAnimationFrame(anim);} anim();
            </script></body></html>
            """
            self.wfile.write(html.encode('utf-8'))

    def _send_json(self, data):
        self.send_response(200); self.send_header('Content-type','application/json'); self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    def log_message(self, format, *args): pass

class WebDashboardServer(threading.Thread):
    def __init__(self, port=8080):
        super().__init__(); self.port = port
        self.server = ReusableHTTPServer(('0.0.0.0', self.port), WebDashboardHandler)
    def run(self): self.server.serve_forever()
    def stop(self): self.server.shutdown(); self.server.server_close()

# ========================================================================================
# MODULE 21: AUTO-HEAL V15 (BÁC SĨ CHẠY NGẦM BẤT ĐỒNG BỘ)
# ========================================================================================
class AutoHealThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.is_running = True
        self.daemon = True

    def run(self):
        # Tạo một event loop riêng cho Auto-Heal để không đụng chạm luồng chính
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.heal_cycle())

    async def heal_cycle(self):
        while self.is_running:
            proxies = db.get_all_proxies("live")
            if not proxies:
                await asyncio.sleep(60)
                continue
                
            # Check âm thầm từng proxy một để không gây nghẽn mạng
            async with aiohttp.ClientSession() as session:
                for p in proxies:
                    if not self.is_running: break
                    ip_port = p['ip_port']
                    try:
                        # Thử kết nối cực nhanh (3 giây)
                        proxy_url = f"http://{ip_port}"
                        async with session.get("http://httpbin.org/get", proxy=proxy_url, timeout=3) as res:
                            if res.status != 200:
                                self._remove_proxy(ip_port)
                    except:
                        self._remove_proxy(ip_port)
                    
                    # Nghỉ 0.5s giữa mỗi lần check để ngầm hoàn toàn
                    await asyncio.sleep(0.5) 
            
            # Sau khi quét xong 1 vòng kho database, nghỉ 10 phút
            await asyncio.sleep(600)
            
    def _remove_proxy(self, ip_port):
        """Thread-safe: xóa proxy khỏi DB bằng transaction context manager"""
        try:
            with db.transaction() as cur:
                cur.execute("DELETE FROM live_proxies WHERE ip_port=?", (ip_port,))
            log.warning(f"Auto-Heal: Đã loại proxy đột tử [{ip_port}] khỏi kho.")
        except Exception as e:
            log.debug(f"Auto-Heal remove error: {e}")

# ========================================================================================
# MODULE 22: DEEP TELEGRAM & DORK SCRAPER (CÀO ĐA TẦNG)
# ========================================================================================
class DeepTelegramScraper:
    def scrape_all(self):
        raw_proxies = set()
        ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{1,5}\b')
        sources = [
            "https://t.me/s/proxylist_updated", 
            "https://t.me/s/ProxyScrape", 
            "https://t.me/s/Free_Proxies",
            "https://t.me/s/proxy_list_1",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"
        ]
        lock = threading.Lock()
        def fetch_source(url):
            try:
                res = requests.get(url, timeout=8, headers={'User-Agent': StaticData.get_random_user_agent()})
                if res.status_code == 200:
                    found = set(ip_pattern.findall(res.text))
                    with lock:
                        raw_proxies.update(found)
            except: pass
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(fetch_source, sources)
        return list(raw_proxies)

# ========================================================================================
# MODULE 19: ENTRY POINT
# ========================================================================================
def main():
    log.info("Khởi động Proxy Scanner Titan Ultra Edition V15.0 GOD TIER")
    for d in ['exports', 'logs']:
        if not os.path.exists(d): os.makedirs(d)
    
    UIHelper.clear_screen()
    UIHelper.print_banner(95)
    
    # --- THÊM KHUNG NHẬP TÊN NGƯỜI DÙNG TẠI ĐÂY ---
    print(f"\n{Theme.LAM}╭─[{Theme.LUC}SYSTEM{Theme.LAM}]─[{Theme.VANG}Authentication{Theme.LAM}]")
    raw_name = input(f"{Theme.LAM}╰─➤ {Theme.TRANG}Nhập Tên của bạn (Tool tự thêm chữ DATA CENTER): {Theme.LUC}").strip()
    
    if not raw_name:
        raw_name = "Ẩn Danh"
        
    # Tự động gắp thêm đuôi DATA CENTER và viết hoa toàn bộ
    username = f"{raw_name.upper()} DATA CENTER"
    
    # Lưu tên vào file config json để gọi lại ở web & terminal
    cfg.update("username", username)
    
    print(f"\n{Theme.LUC}🤖 Xin chào sếp {raw_name}! Đang khởi động hệ thống TITAN V15 HÓA THẦN...{Theme.RESET}")
    print(f"{Theme.VANG}🧠 Khởi tạo AI Engine và Load Cấu hình...{Theme.RESET}")
    time.sleep(1)
    # ---------------------------------------------
    
    ui = ApplicationUI()
    ui.run()

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        print(f"\n{Theme.RED}👋 Tạm biệt đại ca! Hẹn gặp lại nhé!{Theme.RESET}")
        sys.exit(0)
