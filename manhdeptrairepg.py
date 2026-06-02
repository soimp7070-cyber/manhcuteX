#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ===================== KIỂM TRA THƯ VIỆN =====================
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"[LỖI] Thiếu thư viện: {e}")
    print("Vui lòng chạy: pip install requests beautifulsoup4")
    exit(1)

import os
import re
import json
import random
import time
from typing import Dict, Any, Optional, Tuple, Union

# ===================== 1. CookieHandler =====================
class CookieHandler:
    @staticmethod
    def to_dict(cookie_str: str) -> Dict[str, str]:
        cookie_dict = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookie_dict[key] = value
        return cookie_dict

    @staticmethod
    def get_user_id_from_cookie(cookie_str: str) -> Optional[str]:
        match = re.search(r'c_user=(\d+)', cookie_str)
        return match.group(1) if match else None

# ===================== 2. NumberEncoder =====================
class NumberEncoder:
    @staticmethod
    def to_base36(num: int) -> str:
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        if num == 0:
            return "0"
        result = ""
        while num:
            num, remainder = divmod(num, 36)
            result = chars[remainder] + result
        return result

# ===================== 3. HTMLExtractor =====================
class HTMLExtractor:
    @staticmethod
    def find_pattern(html: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, html, re.DOTALL)
        return match.group(1) if match else None

    @staticmethod
    def extract_token(html: str) -> Optional[str]:
        soup = BeautifulSoup(html, 'html.parser')
        inp = soup.find('input', {'name': 'fb_dtsg'})
        if inp and inp.get('value'):
            return inp['value']
        patterns = [
            r'"fb_dtsg":"([^"]+)"',
            r'DTSGInitialData.*?token":"([^"]+)"',
            r'window\.__DTSG__\s*=\s*{.*?token:\s*"([^"]+)"',
        ]
        for pattern in patterns:
            token = HTMLExtractor.find_pattern(html, pattern)
            if token:
                return token
        return None

    @staticmethod
    def extract_lsd(html: str) -> Optional[str]:
        soup = BeautifulSoup(html, 'html.parser')
        inp = soup.find('input', {'name': 'lsd'})
        if inp and inp.get('value'):
            return inp['value']
        for script in soup.find_all('script'):
            if not script.string:
                continue
            text = script.string
            match = re.search(r'\[\s*"LSD"\s*,\s*\[\]\s*,\s*\{\s*"token"\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1)
            match = re.search(r'LSD\s*:\s*\{\s*token\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1)
            match = re.search(r'"LSD",\s*"token"\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1)
        elem = soup.find(attrs={'data-lsd': True})
        if elem:
            return elem['data-lsd']
        patterns = [
            r'name="lsd"\s+value="([^"]+)"',
            r'"lsd":"([^"]+)"',
            r'lsd=([^&;"\']+)',
            r'"LSD","([^"]+)"',
        ]
        for pattern in patterns:
            lsd = HTMLExtractor.find_pattern(html, pattern)
            if lsd:
                return lsd
        with open("facebook_debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[DEBUG] Không tìm thấy lsd. Đã lưu HTML vào facebook_debug.html")
        return None

    @staticmethod
    def extract_user_id(html: str, cookie_str: str) -> Optional[str]:
        uid = CookieHandler.get_user_id_from_cookie(cookie_str)
        if uid:
            return uid
        patterns = [r'"userID":"(\d+)"', r'"actorID":"(\d+)"', r'"USER_ID":"(\d+)"']
        for pattern in patterns:
            uid = HTMLExtractor.find_pattern(html, pattern)
            if uid:
                return uid
        return None

    @staticmethod
    def extract_revision(html: str) -> str:
        pattern = r'"client_revision":"(\d+)"'
        rev = HTMLExtractor.find_pattern(html, pattern)
        return rev or "1000000"

    @staticmethod
    def extract_jazoest(html: str) -> Optional[str]:
        pattern = r'jazoest=(\d+)'
        return HTMLExtractor.find_pattern(html, pattern)

# ===================== 4. FacebookSession =====================
class FacebookSession:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.token = None
        self.user_id = None
        self.revision = None
        self.jazoest = None
        self.lsd = None
        self.session = requests.Session()
        self.session.cookies.update(CookieHandler.to_dict(cookie))

    def authenticate(self, retries=3) -> Union[Dict[str, str], bool]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        urls_to_try = [
            "https://www.facebook.com/",
            "https://www.facebook.com/login/",
            "https://mbasic.facebook.com/"
        ]

        for attempt in range(retries):
            for url in urls_to_try:
                try:
                    print(f"[*] GET {url} (lần {attempt+1})")
                    response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
                    print(f"[DEBUG] Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        html = response.text
                        self.token = HTMLExtractor.extract_token(html)
                        self.lsd = HTMLExtractor.extract_lsd(html)
                        self.user_id = HTMLExtractor.extract_user_id(html, self.cookie)
                        self.revision = HTMLExtractor.extract_revision(html)
                        self.jazoest = HTMLExtractor.extract_jazoest(html)

                        if not self.lsd:
                            cookie_dict = CookieHandler.to_dict(self.cookie)
                            self.lsd = cookie_dict.get('lsd')
                            if self.lsd:
                                print("[*] Lấy lsd từ cookie thành công (fallback).")

                        if not self.lsd:
                            print("[!] Không thể tự động lấy lsd. Vui lòng xem file facebook_debug.html")
                            manual = input("Nhập giá trị lsd (hoặc Enter để bỏ qua): ").strip()
                            if manual:
                                self.lsd = manual
                                print("[*] Đã sử dụng lsd thủ công.")

                        if self.token and self.lsd and self.user_id:
                            return {
                                "token": self.token,
                                "user_id": self.user_id,
                                "revision": self.revision,
                                "jazoest": self.jazoest,
                                "lsd": self.lsd,
                            }
                        else:
                            print(f"[!] Lần thử {attempt+1} - {url} - Thiếu: token={self.token is not None}, lsd={self.lsd is not None}, user_id={self.user_id is not None}")
                    elif response.status_code == 400:
                        print(f"[!] HTTP 400 - Bad Request. Response đầu: {response.text[:200]}")
                    else:
                        print(f"[!] HTTP {response.status_code}")
                except Exception as e:
                    print(f"[!] Lỗi {url}: {e}")
                time.sleep(2)
        print("[✗] Xác thực thất bại sau các lần thử.")
        return False

# ===================== 5. GenData =====================
class GenData:
    POSSIBLE_DOC_IDS = [
        "23863457623296585",
        "507601867234850",
        "100522224212670",
    ]

    def __init__(self, session: FacebookSession):
        self.session = session
        self.request_counter = 0
        self.doc_id = os.getenv("FB_ADD_PROFILE_DOC_ID", self.POSSIBLE_DOC_IDS[0])

    def set_doc_id(self, doc_id: str):
        self.doc_id = doc_id

    def build(self, bio: str, name: str) -> Dict[str, Any]:
        self.request_counter += 1
        category_list = [169421023103905, 2347428775505624, 192614304101075,
                         145118935550090, 1350536325044173, 471120789926333,
                         180410821995109, 357645644269220, 2705]
        category = random.choice(category_list)

        variables = {
            "input": {
                "bio": bio,
                "categories": [str(category)],
                "creation_source": "comet",
                "name": name,
                "off_platform_creator_reachout_id": None,
                "page_referrer": "launch_point",
                "actor_id": self.session.user_id,
                "client_mutation_id": str(self.request_counter)
            }
        }

        payload = {
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AdditionalProfilePlusCreationMutation",
            "server_timestamps": "true",
            "fb_dtsg": self.session.token,
            "__a": "1",
            "__user": self.session.user_id,
            "__req": NumberEncoder.to_base36(self.request_counter),
            "__rev": self.session.revision,
            "av": self.session.user_id,
            "lsd": self.session.lsd,
            "variables": json.dumps(variables, separators=(',', ':')),
            "doc_id": self.doc_id
        }
        if self.session.jazoest:
            payload["jazoest"] = self.session.jazoest
        return payload

# ===================== 6. REGPRO5 =====================
class REGPRO5:
    REQUIRED_COOKIE_KEYS = ['c_user', 'xs']

    def __init__(self, cookie: str):
        self.cookie = cookie
        self.session = FacebookSession(cookie)
        self.payload_builder = None
        self.ready = False

    def _validate_cookie(self) -> Tuple[bool, str]:
        if not self.cookie or self.cookie.strip() == "":
            return False, "Cookie rỗng. Vui lòng cung cấp cookie thật."
        cookie_dict = CookieHandler.to_dict(self.cookie)
        missing = [k for k in self.REQUIRED_COOKIE_KEYS if k not in cookie_dict]
        if missing:
            return False, f"Cookie thiếu trường bắt buộc: {missing}. Cookie hiện tại: {list(cookie_dict.keys())}"
        c_user = cookie_dict.get('c_user', '')
        if not c_user.isdigit():
            return False, f"c_user phải là số, nhận được: {c_user}"
        return True, "OK"

    def login(self) -> bool:
        valid, msg = self._validate_cookie()
        if not valid:
            print(f"[✗] {msg}")
            return False

        print("[*] Đang đăng nhập... Có thể mất vài giây.")
        info = self.session.authenticate()
        if info:
            self.payload_builder = GenData(self.session)
            self.ready = True
            print(f"[✓] Đăng nhập thành công. User ID: {info['user_id']}")
            return True
        print("[✗] Đăng nhập thất bại.")
        return False

    def reg(self, bio: str, name: str, auto_retry_doc_id=True) -> Tuple[bool, str]:
        if not self.ready:
            return False, "Chưa đăng nhập"

        success, result = self._try_reg(bio, name)
        if success:
            return True, result

        if auto_retry_doc_id:
            lower_result = result.lower()
            retry_keywords = ['doc_id', 'invalid', 'not found', 'unsupported', 'malformed', 'query', '1357054']
            if any(kw in lower_result for kw in retry_keywords):
                print("[!] Có thể doc_id lỗi hoặc token hết hạn, thử doc_id dự phòng...")
                for doc_id in GenData.POSSIBLE_DOC_IDS[1:]:
                    self.payload_builder.set_doc_id(doc_id)
                    print(f"[*] Thử doc_id: {doc_id}")
                    success, result = self._try_reg(bio, name)
                    if success:
                        return True, result
                return False, "Đã thử hết doc_id nhưng vẫn thất bại."
        return False, result

    def _try_reg(self, bio: str, name: str) -> Tuple[bool, str]:
        payload = self.payload_builder.build(bio, name)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/",
            "X-FB-LSD": self.session.lsd,
            "X-FB-Friendly-Name": "AdditionalProfilePlusCreationMutation",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        try:
            response = self.session.session.post(
                "https://www.facebook.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"

            text = response.text
            if text.startswith("for (;;);"):
                text = text[len("for (;;);"):]
            if not text.strip():
                return False, "Response rỗng sau khi loại bỏ prefix"

            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                return False, f"JSON parse error: {e}\nText: {text[:500]}"

            if "error" in data:
                error_code = data.get("error")
                error_summary = data.get("errorSummary", "")
                error_desc = data.get("errorDescription", "")
                return False, f"Facebook error {error_code}: {error_summary} - {error_desc}"

            if "data" in data and data["data"]:
                result = data["data"].get("additional_profile_plus_create")
                if result:
                    if result.get("additional_profile") and result["additional_profile"].get("id"):
                        return True, result["additional_profile"]["id"]
                    if result.get("error_message"):
                        return False, result["error_message"]
                return False, f"Response data: {json.dumps(data['data'], ensure_ascii=False)[:500]}"
            return False, f"Response không có data: {json.dumps(data)[:500]}"
        except Exception as e:
            return False, f"Lỗi: {e}"

# ===================== 7. Chạy chính (hỗ trợ tạo nhiều page với delay) =====================
if __name__ == "__main__":
    print("=== Mạnh Cute Đẹp Trai ===")
    print("LƯU Ý: Đừng Quên Tên Anh .")
    print("https://zalo.me/g/rcryht808.\n")

    cookie_input = input("Nhập cookie Facebook (bao gồm c_user, xs, ...): ").strip()
    if not cookie_input:
        print("[LỖI] Cookie không được để trống.")
        exit(1)

    bot = REGPRO5(cookie_input)
    if not bot.login():
        print("\n[KẾT LUẬN] Không thể đăng nhập. Hãy kiểm tra lại cookie hoặc thử cách thủ công.")
        exit(1)

    print("\n--- Chế độ tạo hồ sơ phụ ---")
    mode = input("Bạn muốn tạo bao nhiêu hồ sơ? (nhập số, hoặc 'n' để tạo từng lần): ").strip().lower()
    
    if mode == 'n':
        count = 0
        while True:
            print(f"\n--- Lần tạo thứ {count+1} ---")
            bio = input("Nhập bio (giới thiệu): ").strip()
            name = input("Nhập tên hồ sơ: ").strip()
            if not name:
                print("Tên không được để trống, bỏ qua lần này.")
                continue
            success, result = bot.reg(bio, name)
            if success:
                print(f"✅ THÀNH CÔNG! ID hồ sơ mới: {result}")
            else:
                print(f"❌ THẤT BẠI: {result}")
            count += 1
            again = input("\nBạn có muốn tạo thêm hồ sơ khác không? (y/n): ").strip().lower()
            if again != 'y':
                break
            delay = input("Nhập thời gian delay (giây) trước lần tạo tiếp theo (mặc định 5): ").strip()
            delay = int(delay) if delay.isdigit() else 5
            print(f"Chờ {delay} giây...")
            time.sleep(delay)
    else:
        try:
            num = int(mode)
            if num <= 0:
                print("Số lượng không hợp lệ, thoát.")
                exit(1)
        except ValueError:
            print("Số lượng không hợp lệ, thoát.")
            exit(1)
        
        delay_between = input("Nhập delay giữa các lần tạo (giây, mặc định 5): ").strip()
        delay_between = int(delay_between) if delay_between.isdigit() else 5
        
        use_same = input("Dùng chung bio và name cho tất cả? (y/n): ").strip().lower()
        if use_same == 'y':
            common_bio = input("Nhập bio chung: ").strip()
            common_name = input("Nhập tên chung (sẽ thêm số thứ tự): ").strip()
            for i in range(1, num+1):
                print(f"\n--- Lần {i}/{num} ---")
                bio = common_bio
                name = f"{common_name} {i}" if common_name else f"Profile {i}"
                success, result = bot.reg(bio, name)
                if success:
                    print(f"✅ THÀNH CÔNG! ID: {result}")
                else:
                    print(f"❌ THẤT BẠI: {result}")
                if i < num:
                    print(f"Chờ {delay_between} giây...")
                    time.sleep(delay_between)
        else:
            for i in range(1, num+1):
                print(f"\n--- Lần {i}/{num} ---")
                bio = input(f"Nhập bio cho lần {i}: ").strip()
                name = input(f"Nhập tên cho lần {i}: ").strip()
                if not name:
                    print("Tên không được để trống, bỏ qua lần này.")
                    continue
                success, result = bot.reg(bio, name)
                if success:
                    print(f"✅ THÀNH CÔNG! ID: {result}")
                else:
                    print(f"❌ THẤT BẠI: {result}")
                if i < num:
                    print(f"Chờ {delay_between} giây...")
                    time.sleep(delay_between)
    
    print("\n=== KẾT THÚC ===")
