import sys
import os
import requests
import threading
import time
from pystyle import Colorate, Colors, Write, Center, Box

# --- Configuration ---
BUSINESS_CONTENT_URL = 'https://business.facebook.com/content_management'
GRAPH_SHARE_URL = 'https://graph.facebook.com/me/feed'
# --- End Configuration ---

# A lock to prevent threads from writing to the list at the same time
token_list_lock = threading.Lock()
# A counter for successful shares
share_counter = 0
share_counter_lock = threading.Lock()

def banner():
    """Displays the application banner."""
    clear()
    banner_text = """
╔══════════════════════════════════════════════╗
                   Ad Đẹp Trai
╚══════════════════════════════════════════════╝


██████╗░██╗░░░██╗███████╗███████╗  ░██████╗██╗░░██╗░█████╗░██████╗░███████╗
██╔══██╗██║░░░██║██╔════╝██╔════╝  ██╔════╝██║░░██║██╔══██╗██╔══██╗██╔════╝
██████╦╝██║░░░██║█████╗░░█████╗░░  ╚█████╗░███████║███████║██████╔╝█████╗░░
██╔══██╗██║░░░██║██╔══╝░░██╔══╝░░  ░╚═══██╗██╔══██║██╔══██║██╔══██╗██╔══╝░░
██████╦╝╚██████╔╝██║░░░░░██║░░░░░  ██████╔╝██║░░██║██║░░██║██║░░██║███████╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝░░░░░  ╚═════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝
"""
    print(Colorate.Horizontal(Colors.cyan_to_blue, banner_text))
    separator = Colorate.Horizontal(Colors.white_to_black, "- - - - - - - - - - - - - - - - - - - - - - - - -")
    print(Center.XCenter(separator))

def clear():
    """Clears the terminal screen."""
    os.system('cls' if sys.platform.startswith('win') else 'clear')

def check_single_cookie(cookie, live_tokens_list):
    """Checks a single cookie for validity and extracts its token."""
    if not cookie.strip():
        return
    header_ = {
        'authority': 'business.facebook.com', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'vi-VN,vi;q=0.9', 'cache-control': 'max-age=0', 'cookie': cookie,
        'referer': 'https://www.facebook.com/', 'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
        'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Linux"', 'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin', 'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1',
    }
    try:
        response = requests.get(BUSINESS_CONTENT_URL, headers=header_, timeout=15)
        response.raise_for_status()
        if 'EAAG' in response.text:
            token = response.text.split('EAAG')[1].split('","')[0]
            cookie_token = f'{cookie}|EAAG{token}'
            with token_list_lock:
                live_tokens_list.append(cookie_token)
    except Exception:
        pass # Silently ignore dead cookies or network errors

def get_token(list_cookies):
    """Manages multi-threaded checking of all cookies."""
    live_tokens = []
    threads = []
    print('\033[1;33mĐang check token sống/chết song song...\033[0m')
    for i, cookie in enumerate(list_cookies):
        thread = threading.Thread(target=check_single_cookie, args=(cookie, live_tokens))
        threads.append(thread)
        thread.start()
        print(f'\r\033[1;90m-> Đã gửi cookie {i+1}/{len(list_cookies)} để kiểm tra...\033[0m', end='')
    for thread in threads:
        thread.join()
    print(f'\n\033[1;32m✓ Hoàn tất kiểm tra. Tìm thấy {len(live_tokens)} token LIVE.\033[0m')
    return live_tokens

def share(cookie_token, id_share):
    """Performs the share action."""
    global share_counter
    # --- FIX ERROR HERE ---
    # Sử dụng rsplit('|', 1) để tách từ phải sang trái, tách 1 lần duy nhất.
    # Điều này đảm bảo lấy đúng Token ngay cả khi Cookie có chứa dấu '|'.
    try:
        cookie, token = cookie_token.rsplit('|', 1)
    except ValueError:
        return # Nếu lỗi format thì bỏ qua token đó
    # ---------------------
    
    headers = {'accept': '*/*', 'connection': 'keep-alive', 'content-length': '0', 'cookie': cookie, 'host': 'graph.facebook.com'}
    try:
        requests.post(f'{GRAPH_SHARE_URL}?link=https://m.facebook.com/{id_share}&published=0&access_token={token}', headers=headers, timeout=10)
        with share_counter_lock:
            share_counter += 1
    except Exception:
        pass

def get_user_input():
    """Handles all user input with validation."""
    # --- ENHANCED COOKIE INPUT ---
    print(f'\033[1;34m  👑 \033[1;37m Nhập Tất Cả Cookies (Cách nhau bởi dấu phẩy hoặc xuống dòng).')
    print(f'\033[1;90m     -> Nhấn Enter 1 lần để hoàn tất.\033[0m')
    
    # Read the entire block of cookies at once
    all_cookies_input = input()
    
    # Split by comma or newline and filter out empty strings
    input_cookies_list = [c.strip() for c in all_cookies_input.replace(',', '\n').split('\n') if c.strip()]

    if not input_cookies_list:
        print('\033[1;31m[!] Chưa nhập cookies nào!')
        input('Nhấn Enter để thử lại...')
        return None, None, None, None

    id_share = input("\033[1;34m  🌝 \033[1;37m Nhập ID Bài Cần Share:\033[1;31m ")
    while True:
        try:
            delay = int(input("\033[1;34m  🎑 \033[1;37m Nhập Delay Share (giây):\033[1;31m "))
            break
        except ValueError:
            print('\033[1;31m[!] Vui lòng nhập một số nguyên cho Delay!')
    while True:
        try:
            total_share = int(input("\033[1;34m  🌚 \033[1;37m Bao Nhiêu Share Thì Dừng Tool:\033[1;31m "))
            break
        except ValueError:
            print('\033[1;31m[!] Vui lòng nhập một số nguyên cho Tổng share!')
            
    return input_cookies_list, id_share, delay, total_share

def main_share():
    """Main function to run the sharing process."""
    global share_counter
    share_counter = 0
    banner()
    
    cookies, id_share, delay, total_share = get_user_input()
    
    if not all([cookies, id_share, delay, total_share]):
        return

    print(f'\033[1;31m────────────────────────────────────────')
    all_tokens = get_token(cookies)
    
    if not all_tokens:
        print('\033[1;31mKhông có token live nào. Kiểm tra lại cookies nhé.\033[0m')
        input('Nhấn Enter để thoát...')
        sys.exit()

    print(f'\033[1;32mBắt đầu chia sẻ bài viết ID: {id_share}\033[0m')
    
    for i in range(total_share):
        token_to_use = all_tokens[i % len(all_tokens)]
        
        thread = threading.Thread(target=share, args=(token_to_use, id_share))
        thread.start()
        
        # Clear previous lines and print current status
        sys.stdout.write('\r' + ' ' * 100 + '\r') # Clear line
        print(f'\033[1;91m[\033[1;33m{i + 1}\033[1;91m]\033[1;34m 🤣🤣🤣 \033[1;32mSHARE\033[1;34m 🍋‍🟩\033[1;35m ĐANG CHẠY\033[1;34m 👀👀 ID ➤\033[1;31m\033[1;93m {id_share} \033[1;34m💯💯💯💯 \033[1;31m')
        
        # --- ENHANCED VISUAL COUNTDOWN ---
        if i < total_share - 1:
            for remaining in range(delay, -1, -1):
                # Use sys.stdout.write for a clean, updating countdown
                sys.stdout.write(f'\r\033[1;90m-> Vui lòng chờ \033[1;33m{remaining}\033[1;90m giây để tiếp tục...\033[0m')
                sys.stdout.flush()
                time.sleep(1)
            print() # Move to the next line after countdown finishes

    print('\n' + ' ' * 100, end='\r') # Clear the last countdown line
    print(f'\n\033[1;32m✓ Hoàn thành! Đã thực hiện {share_counter} lượt share.\033[0m')
    input('\033[38;5;245m[Nhấn Enter để chạy lại]\033[0m')

if __name__ == '__main__':
    while True:
        try:
            main_share()
        except KeyboardInterrupt:
            print('\n\033[38;5;245m[\033[38;5;9m!\033[38;5;245m] \033[38;5;9mĐã dừng tool. Thắc mắc ibox zalo nhé!\033[0m')
            sys.exit()
        except Exception as e:
            print(f'\n\033[1;31m[!] Đã xảy ra lỗi không mong muốn: {e}\033[0m')
            input('Nhấn Enter để chạy lại...')
