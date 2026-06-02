import aiohttp
import asyncio
import random
import requests
import re
import time
import secrets
import os
import signal
import sys
from hashlib import md5
from time import time as T
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import logging
import json
from concurrent.futures import ThreadPoolExecutor
import socket
import ssl

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    model: str
    version: str
    api_level: int
    brand: str
    hardware: str
    manufacturer: str

class DeviceGenerator:
    DEVICES = [
        DeviceInfo("Pixel 6", "13", 33, "Google", "oriole", "Google"),
        DeviceInfo("Pixel 7", "14", 34, "Google", "panther", "Google"),
        DeviceInfo("SM-S901B", "13", 33, "Samsung", "dm3q", "samsung"),
        DeviceInfo("SM-S911B", "14", 34, "Samsung", "e1s", "samsung"),
        DeviceInfo("2201123C", "13", 33, "Xiaomi", "zeus", "Xiaomi"),
        DeviceInfo("2210132C", "14", 34, "Xiaomi", "nuwa", "Xiaomi"),
        DeviceInfo("CPH2447", "13", 33, "OPPO", "OPPO", "OPPO"),
        DeviceInfo("CPH2499", "14", 34, "OPPO", "OPPO", "OPPO"),
        DeviceInfo("V2217", "13", 33, "vivo", "V2217", "vivo"),
        DeviceInfo("V2309", "14", 34, "vivo", "V2309", "vivo"),
        DeviceInfo("RMX3371", "13", 33, "realme", "RE5B6A", "realme"),
        DeviceInfo("RMX3843", "14", 34, "realme", "RE58B6", "realme"),
        DeviceInfo("LE2123", "13", 33, "OnePlus", "OnePlus9Pro", "OnePlus"),
        DeviceInfo("CPH2451", "14", 34, "OnePlus", "OnePlus11", "OnePlus"),
    ]
    
    @classmethod
    def random_device(cls) -> DeviceInfo:
        return random.choice(cls.DEVICES)
    
    @classmethod
    def generate_device_id(cls) -> str:
        """Generate realistic device ID"""
        return str(random.randint(6800000000000000000, 6999999999999999999))
    
    @classmethod
    def generate_openudid(cls) -> str:
        """Generate OpenUDID"""
        return ''.join(random.choices('abcdef0123456789', k=16))
    
    @classmethod
    def generate_cdids(cls) -> str:
        """Generate CDIDs"""
        return ''.join(random.choices('abcdef0123456789', k=16))

class ProxyManager:
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxies = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.load_proxies(proxy_file)
    
    def load_proxies(self, proxy_file: str):
        """Load proxies from file"""
        try:
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(self.proxies)} proxies")
            else:
                logger.warning("No proxy file found, running without proxies")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
    
    async def get_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        async with self.lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy

class SignatureGenerator:
    """Improved X-Gorgon generator (simplified version)"""
    
    @staticmethod
    def generate_x_gorgon(params: str, data: str = "", cookies: str = "") -> Dict[str, str]:
        """Generate X-Gorgon and X-Khronos headers"""
        timestamp = int(T())
        
        # Create signature string
        to_sign = f"{params}{data}{cookies}{timestamp}"
        signature = md5(to_sign.encode()).hexdigest()[:16]
        
        # Format X-Gorgon (this is simplified, real algorithm is more complex)
        x_gorgon = f"8402{signature}"
        
        return {
            "X-Gorgon": x_gorgon,
            "X-Khronos": str(timestamp)
        }

class RateLimiter:
    def __init__(self, max_requests_per_second: int = 100):
        self.max_requests_per_second = max_requests_per_second
        self.tokens = max_requests_per_second
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.max_requests_per_second,
                self.tokens + time_passed * self.max_requests_per_second
            )
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.max_requests_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

class OptimizedTikTokViewBot:
    def __init__(self):
        self.count = 0
        self.start_time = 0
        self.is_running = False
        self.session = None
        self.successful_requests = 0
        self.failed_requests = 0
        self.peak_speed = 0
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter(max_requests_per_second=50)  # Conservative limit
        self.stats_lock = asyncio.Lock()
        
    async def init_session(self):
        """Initialize aiohttp session with optimized settings"""
        timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
        
        # Custom SSL context to avoid SSL issues
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            limit=100,  # Limit total connections
            limit_per_host=10,  # Limit per host
            ttl_dns_cache=300,
            ssl=ssl_context,
            force_close=False,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            cookie_jar=aiohttp.DummyCookieJar()
        )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    def get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL with multiple patterns"""
        try:
            # Clean URL
            url = url.split('?')[0]
            
            # Pattern 1: Direct video ID in URL
            patterns = [
                r'/video/(\d+)',
                r'/v/(\d+)',
                r'tiktok\.com/@[\w.]+/video/(\d+)',
                r'tiktok\.com/@[\w.]+/(\d+)',
                r'(\d{19})'  # TikTok video IDs are 19 digits
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    if len(video_id) >= 18:  # Validate length
                        logger.info(f"Found Video ID: {video_id}")
                        return video_id
            
            # Pattern 2: Fetch from page if not found in URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Look for video ID in page content
            page_patterns = [
                r'"id":"(\d{19})"',
                r'video_id["\']:\s*["\'](\d{19})',
                r'video/(\d{19})',
                r'aweme_id["\']:\s*["\'](\d{19})'
            ]
            
            for pattern in page_patterns:
                match = re.search(pattern, response.text)
                if match:
                    video_id = match.group(1)
                    logger.info(f"Found Video ID from page: {video_id}")
                    return video_id
            
            logger.error("No video ID found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting video ID: {e}")
            return None
    
    def generate_request_data(self, video_id: str) -> Tuple[str, Dict, Dict, Dict]:
        """Generate realistic request data with device fingerprints"""
        device = DeviceGenerator.random_device()
        device_id = DeviceGenerator.generate_device_id()
        openudid = DeviceGenerator.generate_openudid()
        
        # Base parameters
        params = {
            "channel": "googleplay",
            "aid": "1233",
            "app_name": "musical_ly",
            "version_code": "400304",
            "version_name": "40.3.4",
            "device_platform": "android",
            "device_type": device.model,
            "device_brand": device.brand,
            "device_manufacturer": device.manufacturer,
            "os_version": device.version,
            "os_api": str(device.api_level),
            "device_id": device_id,
            "openudid": openudid,
            "app_language": random.choice(["vi", "en", "id", "th", "ms"]),
            "tz_name": "Asia/Ho_Chi_Minh",
            "tz_offset": "25200",
            "carrier_region": random.choice(["VN", "US", "ID", "TH", "MY"]),
            "sys_region": random.choice(["vn", "us", "id", "th", "my"]),
            "ac": random.choice(["wifi", "4g", "5g"]),
            "mcc_mnc": random.choice(["45201", "310260", "51010"]),
            "pass-route": "1"
        }
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"https://api16-core-c-alisg.tiktokv.com/aweme/v1/aweme/stats/?{query_string}"
        
        # Request body
        data = {
            "item_id": video_id,
            "play_delta": 1,
            "action_time": int(time.time()),
            "source": random.choice([1, 2, 3, 4]),
            "media_type": 4,
            "content_type": "video"
        }
        
        # Cookies with realistic session
        cookies = {
            "sessionid": secrets.token_hex(20),
            "uid": str(random.randint(1000000000, 9999999999)),
            "cdids": DeviceGenerator.generate_cdids()
        }
        
        # Base headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": f"com.ss.android.ugc.trill/{params['version_code']} (Linux; U; Android {device.version}; {device.model}; Build/PI; tt-ok/3.12.13)",
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive",
            "Host": "api16-core-c-alisg.tiktokv.com",
            "sdk-version": "2",
            "x-tt-dm-status": "login=1; launch=0"
        }
        
        return url, data, cookies, headers
    
    async def send_view_request(self, video_id: str, semaphore: asyncio.Semaphore) -> bool:
        """Send view request with retry logic"""
        async with semaphore:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Get proxy
            proxy = await self.proxy_manager.get_proxy()
            proxy_url = f"http://{proxy}" if proxy else None
            
            for attempt in range(3):  # Max 3 retries
                try:
                    url, data, cookies, base_headers = self.generate_request_data(video_id)
                    
                    # Generate signatures
                    sig = SignatureGenerator.generate_x_gorgon(
                        url.split('?')[1] if '?' in url else "",
                        str(data),
                        str(cookies)
                    )
                    headers = {**base_headers, **sig}
                    
                    async with self.session.post(
                        url, 
                        data=data, 
                        headers=headers, 
                        cookies=cookies,
                        proxy=proxy_url,
                        ssl=False
                    ) as response:
                        
                        if response.status == 200:
                            async with self.stats_lock:
                                self.count += 1
                                self.successful_requests += 1
                            return True
                        elif response.status == 429:  # Rate limited
                            wait_time = 2 ** attempt  # Exponential backoff
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Other HTTP errors
                            if attempt < 2:  # Retry on first 2 attempts
                                await asyncio.sleep(0.1 * (attempt + 1))
                                continue
                            async with self.stats_lock:
                                self.failed_requests += 1
                            return False
                            
                except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror) as e:
                    if attempt == 2:  # Last attempt failed
                        async with self.stats_lock:
                            self.failed_requests += 1
                        logger.debug(f"Request failed after 3 attempts: {e}")
                        return False
                    await asyncio.sleep(0.1 * (attempt + 1))
                    
                except Exception as e:
                    async with self.stats_lock:
                        self.failed_requests += 1
                    logger.error(f"Unexpected error: {e}")
                    return False
            
            return False
    
    async def view_sender(self, video_id: str, task_id: int, semaphore: asyncio.Semaphore):
        """Continuous view sender with adaptive delay"""
        consecutive_success = 0
        
        while self.is_running:
            success = await self.send_view_request(video_id, semaphore)
            
            # Adaptive delay based on success rate
            if success:
                consecutive_success += 1
                if consecutive_success > 50:
                    delay = random.uniform(0.001, 0.003)
                elif consecutive_success > 20:
                    delay = random.uniform(0.003, 0.005)
                else:
                    delay = random.uniform(0.005, 0.01)
            else:
                consecutive_success = 0
                delay = random.uniform(0.02, 0.05)  # Longer delay after failure
            
            # Adjust based on current speed
            stats = self.calculate_stats()
            if stats["views_per_second"] > 200:
                delay *= 1.5
            elif stats["views_per_second"] > 300:
                delay *= 2
            
            await asyncio.sleep(delay)
    
    def calculate_stats(self) -> Dict[str, float]:
        """Calculate current statistics"""
        elapsed = time.time() - self.start_time
        views_per_second = self.count / elapsed if elapsed > 0 else 0
        
        if views_per_second > self.peak_speed:
            self.peak_speed = views_per_second
        
        views_per_minute = views_per_second * 60
        views_per_hour = views_per_minute * 60
        
        total_requests = self.successful_requests + self.failed_requests
        success_rate = (self.successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_views": self.count,
            "elapsed_time": elapsed,
            "views_per_second": views_per_second,
            "views_per_minute": views_per_minute,
            "views_per_hour": views_per_hour,
            "success_rate": success_rate,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "peak_speed": self.peak_speed
        }
    
    def display_stats(self):
        """Display detailed statistics"""
        stats = self.calculate_stats()
        print(f"\n{'='*60}")
        print(f"📊 TOTAL VIEWS     : {stats['total_views']:,}")
        print(f"⏱️  ELAPSED TIME    : {stats['elapsed_time']:.1f}s")
        print(f"⚡ CURRENT SPEED    : {stats['views_per_second']:.1f} views/s")
        print(f"🚀 PEAK SPEED       : {stats['peak_speed']:.1f} views/s")
        print(f"📈 VIEWS PER MINUTE : {stats['views_per_minute']:,.0f}")
        print(f"📊 VIEWS PER HOUR   : {stats['views_per_hour']:,.0f}")
        print(f"✅ SUCCESSFUL       : {stats['successful_requests']:,}")
        print(f"❌ FAILED           : {stats['failed_requests']:,}")
        print(f"📊 SUCCESS RATE     : {stats['success_rate']:.1f}%")
        print(f"{'='*60}")
    
    async def run_optimized(self, video_url: str):
        """Main run method with optimized settings"""
        print("🔍 Extracting video ID...")
        video_id = self.get_video_id(video_url)
        
        if not video_id:
            print("❌ Cannot extract video ID!")
            return
        
        # Determine optimal workers based on system
        cpu_count = os.cpu_count() or 1
        available_memory = self.get_available_memory()
        
        if available_memory < 1024:  # Less than 1GB free
            optimal_workers = 500
        elif available_memory < 2048:  # Less than 2GB free
            optimal_workers = 1000
        elif cpu_count <= 2:
            optimal_workers = 1500
        elif cpu_count <= 4:
            optimal_workers = 2500
        else:
            optimal_workers = 3500
        
        print(f"✅ Video ID: {video_id}")
        print(f"💻 CPU Cores: {cpu_count}")
        print(f"💾 Available Memory: {available_memory}MB")
        print(f"⚙️  Optimal workers: {optimal_workers:,}")
        
        await asyncio.sleep(2)
        
        await self.init_session()
        self.is_running = True
        self.start_time = time.time()
        
        # Limit concurrent requests
        semaphore = asyncio.Semaphore(min(500, optimal_workers // 5))
        
        tasks = []
        try:
            # Create tasks
            for i in range(optimal_workers):
                task = asyncio.create_task(self.view_sender(video_id, i, semaphore))
                tasks.append(task)
            
            logger.info(f"🚀 Started {len(tasks):,} tasks")
            
            # Display stats periodically
            last_display = 0
            while self.is_running:
                await asyncio.sleep(1)
                current_time = time.time()
                
                if current_time - last_display >= 5:  # Update every 5 seconds
                    stats = self.calculate_stats()
                    print(
                        f"\r📊 Views: {stats['total_views']:,} | "
                        f"⚡ Speed: {stats['views_per_second']:.1f}/s | "
                        f"🚀 Peak: {stats['peak_speed']:.1f}/s | "
                        f"✅ Success: {stats['success_rate']:.1f}% | "
                        f"⏱️ Time: {stats['elapsed_time']:.1f}s",
                        end="", flush=True
                    )
                    last_display = current_time
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping bot...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.is_running = False
            logger.info("Stopping all tasks...")
            
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            
            # Wait for tasks to cancel
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.close_session()
            
            print("\n" + "="*60)
            print("📊 FINAL STATISTICS")
            self.display_stats()
    
    def get_available_memory(self) -> int:
        """Get available system memory in MB"""
        try:
            import psutil
            return psutil.virtual_memory().available // (1024 * 1024)
        except ImportError:
            return 4096  # Assume 4GB if psutil not available

def signal_handler(sig, frame):
    print("\n\n🛑 Received interrupt signal. Stopping...")
    sys.exit(0)

def display_banner():
    """Display beautiful banner"""
    os.system("cls" if os.name == "nt" else "clear")
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    TIKTOK VIEW BOT v4.0                      ║
║                    ⚡ OPTIMIZED EDITION ⚡                     ║
╠══════════════════════════════════════════════════════════════╣
║  ████████╗██╗██╗  ██╗████████╗ ██████╗ ██╗  ██╗             ║
║  ╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔═══██╗██║ ██╔╝             ║
║     ██║   ██║█████╔╝    ██║   ██║   ██║█████╔╝              ║
║     ██║   ██║██╔═██╗    ██║   ██║   ██║██╔═██╗              ║
║     ██║   ██║██║  ██╗   ██║   ╚██████╔╝██║  ██╗             ║
║     ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝             ║
╠══════════════════════════════════════════════════════════════╣
║  ⚡ FEATURES:                                                 ║
║  ✓ Device fingerprint rotation                               ║
║  ✓ Adaptive rate limiting                                    ║
║  ✓ Proxy support                                            ║
║  ✓ Real-time statistics                                     ║
║  ✓ Memory-optimized                                          ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def get_user_input():
    """Get user input with validation"""
    print("\n" + "═" * 60)
    print("📝 INPUT REQUIRED")
    print("═" * 60)
    
    video_url = input("\n📎 Enter TikTok video URL: ").strip()
    
    if not video_url:
        print("❌ URL cannot be empty!")
        return None
    
    if not video_url.startswith(('http://', 'https://')):
        print("❌ Invalid URL format! Please include http:// or https://")
        return None
    
    # Basic URL validation
    if 'tiktok.com' not in video_url:
        print("⚠️  Warning: URL does not contain 'tiktok.com'")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return None
    
    print("\n🔍 Checking internet connection...", end="")
    try:
        requests.get("https://www.google.com", timeout=5)
        print(" ✅ Connected")
    except:
        print(" ❌ No internet connection!")
        return None
    
    return video_url

async def main_optimized():
    """Main async function"""
    display_banner()
    signal.signal(signal.SIGINT, signal_handler)
    
    video_url = get_user_input()
    if not video_url:
        return
    
    print("\n🚀 Initializing bot...")
    bot = OptimizedTikTokViewBot()
    
    try:
        await bot.run_optimized(video_url)
    except Exception as e:
        logger.error(f"Bot execution error: {e}")
        print(f"\n❌ Error occurred: {e}")
    finally:
        await bot.close_session()
    
    print("\n" + "═" * 60)
    print("🎉 BOT SESSION COMPLETED")
    print("═" * 60)
    print("Thank you for using TikTok View Bot!")

if __name__ == "__main__":
    # Set up event loop for different platforms
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main_optimized())
    except KeyboardInterrupt:
        print("\n\n👋 Program terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        loop.close()