#!/usr/bin/env python3
# -- coding: utf-8 --

import requests
import time
import math
import random
import sys
import json
import os
from requests.exceptions import RequestException
from datetime import datetime

# ======================================================================
# Cấu hình hiển thị banner (bật/tắt)
# ======================================================================
SHOW_BANNER = True

# ======================================================================
# Hàm tiện ích hiển thị / clear screen / banner / safe input
# ======================================================================
def clear_screen():
    """Xóa màn hình terminal cross-platform."""
    try:
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
    except Exception:
        pass

def banner():
    clear_screen()
    banner_text = """
      \033[38;2;153;51;255m▄▄▄█████▓ █    ██   ██████    ▄▄▄█████▓ ▒█████   ▒█████   ██▓    
      \033[38;2;153;51;255m▓  ██▒ ▓▒ ██  ▓██▒▒██    ▒    ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒    
      \033[38;2;153;51;255m▒ ▓██░ ▒░▓██  ▒██░░ ▓██▄      ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░    
      \033[38;2;153;51;255m░ ▓██▓ ░ ▓▓█  ░██░  ▒   ██▒   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░    
      \033[38;2;153;51;255m  ▒██▒ ░ ▒▒█████▓ ▒██████▒▒     ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒
      \033[38;2;153;51;255m  ▒ ░░   ░▒▓▒ ▒ ▒ ▒ ▒▓▒ ▒ ░     ▒ ░░   �░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░
      \033[0m
\033[1;31m[\033[1;37m</>\033[1;31m] \033[1;37m\033[1;32mADMIN:\033[38;2;255;190;0m NHƯ ANH ĐÃ THẤY EM   \033[1;32mPhiên Bản: \033[38;2;255;190;0mV1 (demo)
\033[1;31m[\033[1;37m</>\033[1;31m] \033[1;37m\033[1;32mNHóm Telegram: \033[38;2;255;190;0mhttps://t.me/se_meo_bao_an
\033[97m═══════════════════════════════════════════════════════════════════════ 
\033[1;31m[\033[1;37m</>\033[1;31m] \033[1;37m\033[1;32mPinterest Cookie\033[1;31m    : \033[1;97m\033[1;32mBạn đang dùng tool Pinterest Golike\033[1;31m\033[1;97m
\033[97m════════════════════════════════════════
"""
    try:
        for char in banner_text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.00125)
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()

def safe_input(prompt=""):
    """
    Input wrapper: nếu user nhập 'clear' (không phân biệt hoa thường),
    sẽ clear màn hình và hiển thị lại banner rồi hỏi lại.
    Trả về giá trị input bình thường nếu không phải 'clear'.
    """
    while True:
        try:
            val = input(prompt)
        except EOFError:
            # trong môi trường không có stdin, trả về rỗng để code xử lý tiếp
            return ""
        if isinstance(val, str) and val.strip().lower() == "clear":
            clear_screen()
            if SHOW_BANNER:
                banner()
            # tiếp tục vòng lặp để hỏi lại
            continue
        return val

# ======================================================================
# CẤU HÌNH GOLIKE / PINTEREST (mặc định, có thể override khi chạy)
# ======================================================================
AUTO_COMPLETE = True
DELAY_BEFORE_COMPLETE = 3
RANDOMIZE_DELAY = True
RANDOM_DELAY_MAX = 5
AUTO_SKIP_ON_FAIL = True

DELAY_BEFORE_GET_JOB = 1
RANDOMIZE_GET_DELAY = True
RANDOM_GET_DELAY_MAX = 3

DELAY_BEFORE_ACTION = 0
RANDOMIZE_ACTION_DELAY = True
RANDOM_ACTION_DELAY_MAX = 2

NO_JOB_SLEEP = 5
NETWORK_ERROR_SLEEP = 3

NETWORK_ERROR = object()

BASE_PINTEREST_HEADERS = {
    'authority': 'www.pinterest.com',
    'accept': 'application/json, text/javascript, */*, q=0.01',
    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.pinterest.com',
    'referer': 'https://www.pinterest.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'x-requested-with': 'XMLHttpRequest',
}

CURRENT_PINTEREST_COOKIES = {}

# ======================================================================
# HỖ TRỢ NHẬP TỪ NGƯỜI DÙNG (dùng safe_input)
# ======================================================================
def ask_float(prompt, default):
    while True:
        i = safe_input(f"{prompt} [mặc định: {default}]: ").strip()
        if i == "":
            return float(default)
        try:
            v = float(i)
            if v < 0:
                print("Vui lòng nhập số >= 0.")
                continue
            return v
        except ValueError:
            print("Không hợp lệ — nhập số (ví dụ: 1.5) hoặc Enter để giữ mặc định.")

def ask_int(prompt, default):
    while True:
        i = safe_input(f"{prompt} [mặc định: {default}]: ").strip()
        if i == "":
            return int(default)
        try:
            v = int(i)
            if v < 0:
                print("Vui lòng nhập số nguyên >= 0.")
                continue
            return v
        except ValueError:
            print("Không hợp lệ — nhập số nguyên hoặc Enter để giữ mặc định.")

def ask_bool(prompt, default):
    def_str = "Y" if default else "N"
    i = safe_input(f"{prompt} (Y/N) [mặc định: {def_str}]: ").strip().lower()
    if i == "":
        return default
    if i in ("y", "yes", "t", "true"):
        return True
    if i in ("n", "no", "f", "false"):
        return False
    print("Không hợp lệ, tính theo mặc định.")
    return default

# ======================================================================
# HÀM TIỆN ÍCH
# ======================================================================
def sleep_with_countdown(seconds, label="Chờ", width=30):
    try:
        total = float(seconds)
    except Exception:
        total = 0.0
    if total <= 0:
        return
    if total < 1:
        sys.stdout.write(f"\r{label}: {total:.1f}s. ")
        sys.stdout.flush()
        time.sleep(total)
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        return

    total_seconds = int(math.ceil(total))
    start = time.time()
    for sec_left in range(total_seconds, 0, -1):
        elapsed = time.time() - start
        progress = min(1.0, max(0.0, elapsed / total))
        filled = int(progress * width)
        bar = "[" + "#" * filled + "-" * (width - filled) + "]"
        sys.stdout.write(f"\r{label} {bar} {sec_left}s còn lại. ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

def parse_cookie_string(cookie_str):
    """Chuyển cookie dạng 'key=value; key2=value2' thành dict"""
    cookies = {}
    if not cookie_str:
        return cookies
    pairs = cookie_str.split(';')
    for pair in pairs:
        if '=' in pair:
            try:
                key, value = pair.strip().split('=', 1)
                cookies[key] = value
            except ValueError:
                continue
    return cookies

def get_golike_headers(token):
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'{token}',
        'content-type': 'application/json;charset=utf-8',
        'origin': 'https://app.golike.net',
        'referer': 'https://app.golike.net/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; Mobile)',
    }

# ======================================================================
# API GOLIKE (lấy job / complete / skip)
# ======================================================================
def get_user_info(token):
    headers = get_golike_headers(token)
    url = 'https://gateway.golike.net/api/users/me'
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            user = data.get('data', {})
            print(f"Username: {user.get('username')}")
            print(f"Coin: {user.get('coin')}")
            return True
        else:
            print(f"Lỗi User: {data.get('message', 'Không xác định')}")
            return False
    except Exception as e:
        print(f"Lỗi kết nối User: {e}")
        return False

def get_pinterest_accounts(token):
    headers = get_golike_headers(token)
    url = 'https://gateway.golike.net/api/pinterest-account'
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            return data.get('data', [])
        else:
            print("Lấy tài khoản Pinterest thất bại:", data.get('message'))
            return []
    except Exception as e:
        print("Lỗi khi lấy danh sách Pinterest accounts:", e)
        return []

def choose_account(accounts):
    if not accounts:
        print("Không tìm thấy tài khoản Pinterest nào.")
        return None
    for i, acc in enumerate(accounts, 1):
        print(f"{i}. ID: {acc.get('id')} | User: {acc.get('pinterest_username')}")
        print("\033[1;97m════════════════════════════════════════════════")
    while True:
        try:
            choice_raw = safe_input(f"Chọn STT  (1-{len(accounts)}): ")
            choice = int(choice_raw.strip())
            if 1 <= choice <= len(accounts):
                selected = accounts[choice - 1]
                print(f"==> Đã chọn: {selected.get('pinterest_username')}")
                return selected
            print("Số thứ tự không hợp lệ.")
        except ValueError:
            print("Vui lòng nhập số.")
        except KeyboardInterrupt:
            return None

def get_jobs(token, account_id):
    headers = get_golike_headers(token)
    params = {'account_id': str(account_id), 'is_pwa': 'true'}
    url = 'https://gateway.golike.net/api/advertising/publishers/pinterest/jobs'
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 400:
            return None
        response.raise_for_status()
        data = response.json()
        if data.get('success'):
            job_data = data.get('data')
            if not job_data:
                print("\n[-] Hiện tại không có job mới.")
                return None
            job_item = job_data[0] if isinstance(job_data, list) and len(job_data) > 0 else job_data
            if job_item:
                print(f"\n[+] Tìm thấy Job:")
                print(f" - Ads ID: {job_item.get('ads_id') or job_item.get('id')}")
                print(f" - Loại: {job_item.get('type')}")
                object_id = job_item.get('object_id') or job_item.get('objectId') or job_item.get('object')
                print(f" - Target ID: {object_id}")
                return job_item
            else:
                print("\n[-] Không tìm thấy job hợp lệ.")
                return None
        else:
            print(f"\n[!] Thất bại khi lấy job: {data.get('message')}")
            return None
    except Exception as e:
        print(f"\n[!] Lỗi khi gọi API Jobs (lỗi mạng/exception): {e}")
        return NETWORK_ERROR

def complete_job(token, account_id, ads_id):
    headers = get_golike_headers(token)
    url = 'https://gateway.golike.net/api/advertising/publishers/pinterest/complete-jobs'
    json_data = {'account_id': account_id, 'ads_id': ads_id}
    try:
        response = requests.post(url, headers=headers, json=json_data, timeout=15)
        data = response.json()
        if response.status_code == 200 and data.get('success'):
            # Trả về data nhưng KHÔNG in success ở đây — in ở nơi gọi để tùy biến hiển thị.
            return True, data
        else:
            msg = (data.get('message') or "").lower()
            if "job not found" in msg or "ads not found" in msg or "not found" in msg:
                print("[✗] JOB KHÔNG TỒN TẠI / ĐÃ BỊ THU HỒI")
            else:
                print(f"[!] GOLIKE FAIL: {data.get('message')}")
            return False, data
    except Exception as e:
        print(f"Lỗi complete-job: {e}")
        return False, None

def report_error_job(token, account_id, ads_id, object_id=None):
    headers = get_golike_headers(token)
    url = 'https://gateway.golike.net/api/advertising/publishers/pinterest/skip-jobs'
    json_data = {'account_id': account_id, 'ads_id': ads_id}
    if object_id:
        json_data['object_id'] = str(object_id)
    try:
        response = requests.post(url, headers=headers, json=json_data, timeout=15)
        data = response.json()
        if response.status_code == 200 and data.get('success'):
            print("[✓] Đã báo lỗi/skip job.")
            return True, data
        else:
            print("[!] Skip job thất bại.")
            return False, data
    except Exception as e:
        print(f"Lỗi skip-job: {e}")
        return False, None

# ======================================================================
# CHỨC NĂNG PINTEREST FOLLOW (giữ nguyên nhưng thêm phân loại lỗi)
# ======================================================================
def action_pinterest_follow(target_user_id):
    global CURRENT_PINTEREST_COOKIES
    if not CURRENT_PINTEREST_COOKIES:
        print("[!] Chưa có cookie Pinterest. Không thể follow.")
        return False
    print(f"[*] Đang thực hiện Follow User ID: {target_user_id} trên Pinterest.")
    url = "https://www.pinterest.com/resource/UserFollowResource/create/"
    csrf_token = CURRENT_PINTEREST_COOKIES.get('csrftoken', '')
    headers = BASE_PINTEREST_HEADERS.copy()
    headers['x-csrftoken'] = csrf_token
    payload = {
        'source_url': '/',
        'data': json.dumps({
            "options": {"user_id": str(target_user_id)},
            "context": {}
        }),
    }
    try:
        response = requests.post(url, headers=headers, cookies=CURRENT_PINTEREST_COOKIES, data=payload, timeout=15)
        if response.status_code == 200:
            try:
                res_json = response.json()
            except ValueError:
                print("[!] Pinterest trả về không phải JSON (Cookie có thể sai).")
                return False

            resource = res_json.get('resource_response', {}) or {}
            status = resource.get('status') or res_json.get('status') or res_json.get('success')

            if status == 'success' or status is True:
                print(f"[✓] Đã Follow thành công ID {target_user_id}.")
                return True

            # phân loại lỗi rõ hơn
            error = resource.get('error', {}) or {}
            err_msg = (error.get('message') or "").lower()

            if "user not found" in err_msg or "could not find user" in err_msg or "not found" in err_msg:
                print(f"[✗] USER KHÔNG TỒN TẠI / BỊ XÓA: {target_user_id}")
            elif "already" in err_msg:
                print(f"[i] USER ĐÃ FOLLOW TRƯỚC ĐÓ: {target_user_id}")
            else:
                # in nguyên json để debug nếu cần
                print(f"[!] FOLLOW FAIL ({target_user_id}): {error.get('message') or res_json}")
            return False
        elif response.status_code == 401:
            print("[!] Lỗi 401: Cookie Pinterest hết hạn hoặc không hợp lệ.")
            return False
        else:
            print(f"[!] Lỗi HTTP Pinterest: {response.status_code}")
            return False
    except RequestException as e:
        print(f"[!] Lỗi kết nối Pinterest: {e}")
        return False

# ======================================================================
# CHỨC NĂNG PINTEREST REACTION / LIKE (MỚI) - có phân loại lỗi
# ======================================================================
def action_pinterest_react(pin_id, reaction_pin_id, user_id=None, reaction_type=1):
    """
    Gửi reaction (like) cho 1 pin trên Pinterest.
    Trả về True nếu thành công, False nếu thất bại.
    """
    global CURRENT_PINTEREST_COOKIES
    if not CURRENT_PINTEREST_COOKIES:
        print("[!] Chưa có cookie Pinterest. Không thể gửi reaction.")
        return False

    print(f"[*] Đang gửi reaction -> pin_id={pin_id} reaction_pin_id={reaction_pin_id} user_id={user_id}")
    url = "https://www.pinterest.com/resource/ReactionsResource/update/"
    csrf_token = CURRENT_PINTEREST_COOKIES.get('csrftoken', '')
    headers = BASE_PINTEREST_HEADERS.copy()
    headers['x-csrftoken'] = csrf_token

    payload = {
        'source_url': f"/pin/{pin_id}/" if pin_id else "/",
        'data': json.dumps({
            "options": {
                "pin_id": str(pin_id) if pin_id is not None else "",
                "user_id": str(user_id) if user_id is not None else "",
                "reaction_type": int(reaction_type),
                "reaction_pin_id": str(reaction_pin_id),
                "action_type": "reaction"
            },
            "context": {}
        })
    }

    try:
        response = requests.post(url, headers=headers, cookies=CURRENT_PINTEREST_COOKIES, data=payload, timeout=15)
    except RequestException as e:
        print(f"[!] Lỗi kết nối khi gọi ReactionsResource: {e}")
        return False

    if response.status_code == 200:
        try:
            res_json = response.json()
        except ValueError:
            print("[!] Pinterest trả về không phải JSON (có thể cookie sai):", response.text[:400])
            return False

        resource = res_json.get('resource_response', {}) or {}
        status = resource.get('status') or res_json.get('status') or res_json.get('success')

        if status in ('success', True) or (isinstance(status, str) and status.lower() == 'success'):
            print("[✓] Reaction gửi thành công.")
            return True

        error = resource.get('error', {}) or {}
        err_msg = (error.get('message') or "").lower()

        if "pin not found" in err_msg or "could not find pin" in err_msg or "not found" in err_msg:
            print(f"[✗] PIN KHÔNG TỒN TẠI / BỊ XÓA: {reaction_pin_id}")
        elif "already reacted" in err_msg or "already" in err_msg:
            print(f"[i] PIN ĐÃ LIKE TRƯỚC ĐÓ: {reaction_pin_id}")
        else:
            print(f"[!] REACTION FAIL ({reaction_pin_id}): {error.get('message') or res_json}")
        return False
    elif response.status_code == 401:
        print("[!] Lỗi 401: Cookie Pinterest hết hạn hoặc không hợp lệ.")
        return False
    else:
        print(f"[!] HTTP error khi gửi reaction: {response.status_code} -> {response.text[:400]}")
        return False

# ======================================================================
# MAIN: lấy job, xử lý follow hoặc reaction, báo complete/skip
# ======================================================================
def main():
    global CURRENT_PINTEREST_COOKIES
    global DELAY_BEFORE_GET_JOB, RANDOMIZE_GET_DELAY, RANDOM_GET_DELAY_MAX
    global DELAY_BEFORE_ACTION, RANDOMIZE_ACTION_DELAY, RANDOM_ACTION_DELAY_MAX
    global DELAY_BEFORE_COMPLETE, RANDOMIZE_DELAY, RANDOM_DELAY_MAX
    global NO_JOB_SLEEP, NETWORK_ERROR_SLEEP

    # counters requested by user
    dem = 0
    tong = 0

    try:
        # Hiển thị banner nếu bật
        if SHOW_BANNER:
            banner()

        # Nhập token (safe_input để hỗ trợ 'clear')
        token_input = safe_input("1. Nhập Authorization Golike: ").strip()
        if not token_input:
            print("Token không được để trống.")
            return

        # CLEAR màn để che token ngay sau khi nhập
        clear_screen()
        if SHOW_BANNER:
            banner()

        # Tiếp tục kiểm tra token
        if not get_user_info(token_input):
            return

        print("\033[1;97m════════════════════════════════════════════════")

        # Lấy danh sách account trước, rồi mới hỏi cookie (the change requested)
        list_acc = get_pinterest_accounts(token_input)
        selected_acc = choose_account(list_acc)
        if not selected_acc:
            return

        # --- Di chuyển chỗ nhập cookie: yêu cầu cookie SAU khi đã chọn account ---
        raw_cookie = safe_input("Nhập Cookie Pinterest vào đây: ").strip()
        if not raw_cookie:
            print("Cookie không được để trống. Tool sẽ dừng.")
            return

        # Ngay khi user nhập xong cookie, clear màn hình để "che" cookie (không làm mất dữ liệu)
        clear_screen()
        if SHOW_BANNER:
            banner()

        # Parse cookie sau khi đã clear màn
        CURRENT_PINTEREST_COOKIES = parse_cookie_string(raw_cookie)
        if 'csrftoken' not in CURRENT_PINTEREST_COOKIES:
            print("[Cảnh báo] Không tìm thấy 'csrftoken' trong cookie vừa nhập.")
            print("Tool có thể hoạt động không đúng. Hãy chắc chắn bạn copy đủ chuỗi cookie.")
        else:
            # Hiển thị token đã bị che/masked để an toàn hơn
            masked = CURRENT_PINTEREST_COOKIES['csrftoken'][:6] + '...' if len(CURRENT_PINTEREST_COOKIES['csrftoken']) > 6 else CURRENT_PINTEREST_COOKIES['csrftoken']
            print(f"[OK] Đã nhận diện Cookie (Token: {masked})")

        acc_id = selected_acc.get('id')
        print(f"\n---> Bắt đầu chạy tool cho ID: {acc_id} <---")

        # Cho phép override delay
        DELAY_BEFORE_GET_JOB = ask_float("Delay trước khi lấy job (giây)", DELAY_BEFORE_GET_JOB)
        RANDOMIZE_GET_DELAY = ask_bool("Bật random thêm delay khi lấy job?", RANDOMIZE_GET_DELAY)
        if RANDOMIZE_GET_DELAY:
            RANDOM_GET_DELAY_MAX = ask_float("Giá trị random tối đa (giây) trước khi lấy job", RANDOM_GET_DELAY_MAX)

        DELAY_BEFORE_ACTION = ask_float("Delay trước khi thực hiện action (giây)", DELAY_BEFORE_ACTION)
        RANDOMIZE_ACTION_DELAY = ask_bool("Bật random thêm delay trước action?", RANDOMIZE_ACTION_DELAY)
        if RANDOMIZE_ACTION_DELAY:
            RANDOM_ACTION_DELAY_MAX = ask_float("Giá trị random tối đa (giây) trước action", RANDOM_ACTION_DELAY_MAX)

        DELAY_BEFORE_COMPLETE = ask_float("Delay sau khi action trước khi báo complete (giây)", DELAY_BEFORE_COMPLETE)
        RANDOMIZE_DELAY = ask_bool("Bật random thêm delay sau action (complete)?", RANDOMIZE_DELAY)
        if RANDOMIZE_DELAY:
            RANDOM_DELAY_MAX = ask_float("Giá trị random tối đa (giây) sau action (complete)", RANDOM_DELAY_MAX)

        NO_JOB_SLEEP = ask_int("Nếu không có job, nghỉ bao nhiêu giây trước khi thử lại", NO_JOB_SLEEP)
        NETWORK_ERROR_SLEEP = ask_int("Nếu lỗi mạng khi lấy job, nghỉ bao nhiêu giây trước khi thử lại", NETWORK_ERROR_SLEEP)

        print("\n--- Cấu hình delay hiện tại ---")
        print(f"Delay lấy job: {DELAY_BEFORE_GET_JOB}s (random: {RANDOMIZE_GET_DELAY}, max {RANDOM_GET_DELAY_MAX}s)")
        print(f"Delay trước action: {DELAY_BEFORE_ACTION}s (random: {RANDOMIZE_ACTION_DELAY}, max {RANDOM_ACTION_DELAY_MAX}s)")
        print(f"Delay trước complete: {DELAY_BEFORE_COMPLETE}s (random: {RANDOMIZE_DELAY}, max {RANDOM_DELAY_MAX}s)")

        # Vòng chính
        while True:
            # Delay trước khi lấy job (có thể random)
            extra = random.uniform(0, RANDOM_GET_DELAY_MAX) if RANDOMIZE_GET_DELAY else 0
            sleep_with_countdown(DELAY_BEFORE_GET_JOB + extra, label="Đợi trước khi lấy job")

            job = get_jobs(token_input, acc_id)
            if job is NETWORK_ERROR:
                print(f"[!] Lỗi mạng khi lấy job — nghỉ {NETWORK_ERROR_SLEEP}s rồi thử lại.")
                time.sleep(NETWORK_ERROR_SLEEP)
                continue

            if not job:
                print(f"[-] Hết job — ngủ {NO_JOB_SLEEP}s rồi thử lại.")
                time.sleep(NO_JOB_SLEEP)
                continue

            ads_id = job.get('ads_id') or job.get('id')
            object_id = job.get('object_id') or job.get('objectId') or job.get('object')
            job_type = str(job.get('type') or "").lower()

            # Delay trước khi action (có thể random)
            extra_action = random.uniform(0, RANDOM_ACTION_DELAY_MAX) if RANDOMIZE_ACTION_DELAY else 0
            sleep_with_countdown(DELAY_BEFORE_ACTION + extra_action, label="Đợi trước action")

            # Detect nếu job là reaction (ưu tiên các trường reaction_pin_id hoặc tên type chứa 'reaction')
            reaction_pin_id = job.get('reaction_pin_id') or job.get('reactionPinId') or job.get('reaction_pin') or job.get('reaction_pinid')
            is_reaction_job = False
            if reaction_pin_id:
                is_reaction_job = True
            elif 'reaction' in job_type:
                is_reaction_job = True

            is_action_success = False
            if is_reaction_job:
                pin_id = job.get('pin_id') or job.get('pinId') or object_id
                user_id = job.get('user_id') or job.get('userId') or None
                # Nếu reaction_pin_id không có giá trị rõ ràng, cố gắng fallback
                if not reaction_pin_id:
                    reaction_pin_id = pin_id
                is_action_success = action_pinterest_react(pin_id, reaction_pin_id, user_id=user_id)
            else:
                if object_id:
                    is_action_success = action_pinterest_follow(object_id)
                else:
                    print("[!] Không tìm thấy ID để follow/reaction.")

            # Delay trước khi báo complete (có thể random)
            extra_complete = random.uniform(0, RANDOM_DELAY_MAX) if RANDOMIZE_DELAY else 0
            sleep_with_countdown(DELAY_BEFORE_COMPLETE + extra_complete, label="Đợi trước khi báo complete")

            if is_action_success:
                if AUTO_COMPLETE:
                    ok, resp = complete_job(token_input, acc_id, ads_id)
                    if ok:
                        # --- MỚI: cập nhật counters và hiển thị message theo yêu cầu ---
                        nhantien = resp or {}
                        # theo yêu cầu: đặt ok = 1
                        ok = 1
                        dem += 1
                        tien = nhantien.get("data", {}).get("prices", 0)
                        try:
                            tien = float(tien)
                        except Exception:
                            # nếu giá trị không phải số, mặc định 0
                            tien = 0
                        tong += tien
                        now = datetime.now()
                        time_str = now.strftime("%H:%M:%S")

                        # dọn hàng trên cùng rồi in message mới
                        sys.stdout.write("\r" + " " * 80 + "\r")
                        msg = (f"\033[1;31m| \033[1;36m{dem}\033[1;31m\033[1;97m | "
                               f"\033[1;33m{time_str}\033[1;31m\033[1;97m | "
                               f"\033[1;32msuccess\033[1;31m\033[1;97m | "
                               f"\033[1;31m{nhantien.get('data', {}).get('type')}\033[1;31m\033[1;32m\033[1;97m |"
                               f"\033[1;35m {ads_id} \033[1;97m|"
                               f"\033[1;97m \033[1;32m+{tien} \033[1;97m| "
                               f"\033[1;33m{tong}")
                        sys.stdout.write(msg + "\n")
                        sys.stdout.flush()
                    else:
                        print("[!] Hoàn thành job thất bại — báo lỗi nếu AUTO_SKIP_ON_FAIL bật.")
                        if AUTO_SKIP_ON_FAIL:
                            report_error_job(token_input, acc_id, ads_id, object_id=object_id)
                else:
                    print("[i] Action thành công, nhưng AUTO_COMPLETE=False nên không báo Golike.")
            else:
                print("[!] Action thất bại — báo skip/job error.")
                report_error_job(token_input, acc_id, ads_id, object_id=object_id)

    except KeyboardInterrupt:
        print("\n[!] Bị dừng bởi người dùng. Kết thúc.")
        return
    except Exception as e:
        print(f"\n[!] Lỗi không lường trước: {e}")
        return

if __name__ == "__main__":
    main()
