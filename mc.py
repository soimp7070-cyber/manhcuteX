import os
import sys
import subprocess
import time
import random
import threading
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# Cài đặt thư viện nếu thiếu
def install_libraries():
    required = ['requests', 'rich']
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
            except Exception:
                pass

install_libraries()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align
from rich.text import Text
from rich.layout import Layout
from rich.live import Live


class Colors:
    RESET = '\x1b[0m'
    BOLD = '\x1b[1m'
    PRIMARY = '\x1b[38;5;141m'
    SECONDARY = '\x1b[38;5;117m'
    SUCCESS = '\x1b[38;5;120m'
    WARNING = '\x1b[38;5;221m'
    ERROR = '\x1b[38;5;210m'
    INFO = '\x1b[38;5;159m'
    ACCENT = '\x1b[38;5;183m'
    MUTED = '\x1b[38;5;250m'
    WHITE = '\x1b[97m'
    GRAY = '\x1b[38;5;242m'
    GOLD_1 = '\x1b[38;5;220m'
    GRAD1 = '\x1b[38;5;147m'
    GRAD2 = '\x1b[38;5;153m'
    GRAD3 = '\x1b[38;5;159m'
    ORANGE = '\x1b[38;5;208m'
    YELLOW = '\x1b[38;5;220m'
    TT8_GREEN_PRIMARY = '\x1b[38;5;114m'
    TT8_GREEN_SECONDARY = '\x1b[38;5;150m'
    TT8_GREEN_INFO = '\x1b[38;5;156m'
    TT8_GREEN_ACCENT = '\x1b[38;5;157m'
    TT9_BLUE_PRIMARY = '\x1b[38;5;39m'
    TT9_BLUE_SECONDARY = '\x1b[38;5;81m'
    TT9_BLUE_INFO = '\x1b[38;5;87m'
    TT9_BLUE_ACCENT = '\x1b[38;5;123m'
    CASTORICE_PRIMARY = '\x1b[38;5;141m'
    CASTORICE_SECONDARY = '\x1b[38;5;177m'
    CASTORICE_ACCENT = '\x1b[38;5;183m'
    CASTORICE_LIGHT = '\x1b[38;5;189m'
    CASTORICE_DARK = '\x1b[38;5;135m'
    SOFT_RED = '\x1b[38;5;211m'
    SOFT_RED_SECONDARY = '\x1b[38;5;217m'
    SOFT_RED_ACCENT = '\x1b[38;5;224m'
    AMETHYST_DARK = '\x1b[38;5;54m'
    AMETHYST_MID = '\x1b[38;5;99m'
    AMETHYST_LIGHT = '\x1b[38;5;189m'
    SAKURA_DEEP = '\x1b[38;5;204m'
    SAKURA_MID = '\x1b[38;5;218m'
    SAKURA_LIGHT = '\x1b[38;5;225m'
C = Colors()


# Khởi tạo Console
console = Console()

# Biến toàn cục
total_harvested = defaultdict(float)
wallet_balances = {'build': 0.0, 'world': 0.0, 'usdt': 0.0}
history_records = []
ACC_FILE = 'accounts.txt'
stop_spam_event = threading.Event()

def load_accounts():
    if not os.path.exists(ACC_FILE):
        with open(ACC_FILE, 'w', encoding='utf-8') as f:
            pass
    
    accounts = []
    with open(ACC_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    u_id, u_key, name = parts[0], parts[1], parts[2]
                    accounts.append({'id': u_id, 'key': u_key, 'name': name})
    return accounts

def save_accounts(accounts):
    with open(ACC_FILE, 'w', encoding='utf-8') as f:
        for acc in accounts:
            f.write(f"{acc['id']}|{acc['key']}|{acc['name']}\n")

def get_user_info(u_id, u_key):
    try:
        url = f"https://user.3games.io/user/regist?is_cwallet=1&is_mission_setting=true&time={int(time.time()*1000)}"
        headers = {'User-Id': str(u_id), 'User-Secret-Key': str(u_key)}
        r = requests.get(url, headers=headers, timeout=5)
        js = r.json()
        if js.get('code') == 200:
            return js['data']['username']
    except:
        pass
    return 'Unknown'

def update_all_wallets(accounts):
    temp_balances = {'build': 0.0, 'world': 0.0, 'usdt': 0.0}
    
    def fetch_wallet(acc):
        try:
            url = 'https://wallet.3games.io/api/wallet/user_asset'
            headers = {
                'User-Id': str(acc['id']),
                'User-Secret-Key': str(acc['key']),
                'Content-Type': 'application/json'
            }
            payload = {'user_id': int(acc['id']), 'source': 'home'}
            r = requests.post(url, headers=headers, json=payload, timeout=5)
            js = r.json()
            if js.get('code') == 0:
                assets = js.get('data', {}).get('user_asset', {})
                return {
                    'build': float(assets.get('BUILD', 0)),
                    'world': float(assets.get('WORLD', 0)),
                    'usdt': float(assets.get('USDT', 0))
                }
        except:
            pass
        return {'build': 0, 'world': 0, 'usdt': 0}

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_wallet, accounts)
        for res in results:
            temp_balances['build'] += res['build']
            temp_balances['world'] += res['world']
            temp_balances['usdt'] += res['usdt']
            
    wallet_balances.update(temp_balances)

def check_code(acc, code):
    try:
        headers = {
            'User-Id': str(acc['id']),
            'User-Secret-Key': str(acc['key']),
            'Content-Type': 'application/json'
        }
        url = 'https://web3task.3games.io/v1/task/redcode/detail'
        r = requests.post(url, headers=headers, json={'code': code}, timeout=5)
        return r.json()
    except:
        return {'code': -1}

def exchange_code(acc, code):
    try:
        headers = {
            'User-Id': str(acc['id']),
            'User-Secret-Key': str(acc['key']),
            'Content-Type': 'application/json'
        }
        payload = {
            'code': code,
            'os_ver': 'pc',
            'platform': 'h5',
            'appname': 'app'
        }
        url = 'https://web3task.3games.io/v1/task/redcode/exchange'
        r = requests.post(url, headers=headers, json=payload, timeout=5)
        return r.json()
    except:
        return {}

def spam_worker(acc, code, idx):
    global total_harvested
    for i in range(10):
        try:
            res = exchange_code(acc, code)
            code_res = res.get('code')
            if code_res == 0:
                v = float(res['data']['value'])
                cur = res['data']['currency'].lower()
                total_harvested[cur] += v
                now_str = datetime.now().strftime('%H:%M:%S')
                history_entry = [now_str, f"[{idx}] {acc['name']}", f"+{v:,.2f}", cur.upper()]
                history_records.append(history_entry)
                console.print(f"[bold green] [✓] {acc['name']} (Lần {i+1}): +{v} {cur.upper()}[/]")
                return
            elif code_res == 100306:
                console.print(f"[yellow] [!] {acc['name']}: Đã nhập trước đó[/]")
                return
            elif code_res == 100305 or code_res == 100301:
                if i == 9:
                    console.print(f"[red] [X] {acc['name']}: Hết lượt (Thử 10 lần thất bại)[/]")
            else:
                pass
            time.sleep(0.5)
        except:
            time.sleep(0.5)




def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    cons = Console()

    banner_lines = [
        f'{C.CASTORICE_DARK}  ███▄ ▄███▓       ▄▄▄█████▓ ▒█████   ▒█████   ██▓    ',
        f'{C.CASTORICE_PRIMARY} ▓██▒▀█▀ ██▒       ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒    ',
        f'{C.CASTORICE_SECONDARY} ▓██    ▓██░ ▄▄▄▄▄ ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░    ',
        f'{C.CASTORICE_LIGHT} ▒██    ▒██░ █▀▀▀█ ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░    ',
        f'{C.CASTORICE_ACCENT} ▒██▒   ░██▒ ▀▀▀▀▀   ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒',
    ]

    print()
    for line in banner_lines:
        cons.print(Align.center(Text.from_ansi(line + C.RESET)))
        time.sleep(0.02)
    print()

def build_dashboard():
    # 1. Bảng Tổng Tài Sản
    status_table = Table(title="[bold blue]TỔNG TÀI SẢN[/]", expand=True, box=box.ROUNDED, border_style="blue")
    status_table.add_column("Loại Tiền-", justify="left", style="white")
    status_table.add_column("Số Dư", justify="right", style="green")
    status_table.add_column("Lúa Về 🌾", justify="right", style="yellow")
    
    status_table.add_row("BUILD", f"{wallet_balances['build']:,.2f}", f"+{total_harvested['build']:,.2f}")
    status_table.add_row("WORLD", f"{wallet_balances['world']:,.4f}", f"+{total_harvested['world']:,.4f}")
    status_table.add_row("USDT", f"{wallet_balances['usdt']:,.6f}", f"+{total_harvested['usdt']:,.6f}")

    # 2. Bảng Lịch Sử
    history_table = Table(title="[bold yellow]LỊCH SỬ NHẬP CODE[/]", expand=True, box=box.ROUNDED, border_style="yellow")
    history_table.add_column("Thời Gian", justify="center", style="dim white")
    history_table.add_column("Tài Khoản", justify="left", style="cyan")
    history_table.add_column("Giá Trị", justify="right", style="green")
    history_table.add_column("Loại", justify="center", style="white")

    if not history_records:
        history_table.add_row("-", "Chưa có dữ liệu", "-", "-")
    else:
        for rec in history_records[-8:]: # Show 8 record gần nhất
            history_table.add_row(rec[0], rec[1], rec[2], rec[3])

    # Layout
    layout = Table.grid(expand=True, padding=(0, 1))
    layout.add_column(ratio=1)
    layout.add_row(status_table)
    layout.add_row("") 
    layout.add_row(history_table)
    
    return Panel(layout, title="[bold cyan]DASHBOARD[/]", border_style="cyan", box=box.ROUNDED)

def manage_accounts():
    while True:
        banner()
        accounts = load_accounts()
        
        table = Table(title=f"DANH SÁCH TÀI KHOẢN ({len(accounts)}/10)", expand=True, box=box.ROUNDED)
        table.add_column("STT", justify="center", style="dim")
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Tên", justify="left", style="green")
        
        for i, acc in enumerate(accounts, 1):
            table.add_row(str(i), acc['id'], acc['name'])
            
        console.print(table)
        console.print(f"\n[bold yellow](t)[/] Thêm | [bold red](x)[/] Xóa | [bold green](n)[/] Vào Auto Speed: ", end="")
        cmd = input().lower().strip()
        
        if cmd == 't':
            if len(accounts) >= 10:
                console.print("[bold red][!] Tối đa 10 tài khoản![/]")
                time.sleep(1)
                continue
            
            console.print("[cyan]Nhập URL hoặc ID|Key: [/]")
            inp = input().strip()
            u_id, u_key = None, None
            
            if 'http' in inp:
                try:
                    params = parse_qs(urlparse(inp).query)
                    u_id = params.get('userId', [None])[0]
                    u_key = params.get('secretKey', [None])[0]
                except:
                    pass
            elif '|' in inp:
                parts = inp.split('|')
                if len(parts) >= 2:
                    u_id, u_key = parts[0], parts[1]
            
            if u_id and u_key:
                name = get_user_info(u_id, u_key)
                accounts.append({'id': u_id, 'key': u_key, 'name': name})
                save_accounts(accounts)
                console.print(f"[bold green][+] Đã thêm: {name}[/]")
                time.sleep(1)
            else:
                console.print("[bold red][!] Định dạng sai![/]")
                time.sleep(1)
                
        elif cmd == 'x':
            try:
                idx = int(input("[>] Nhập STT để xóa: ")) - 1
                if 0 <= idx < len(accounts):
                    removed = accounts.pop(idx)
                    save_accounts(accounts)
                    console.print(f"[bold red][-] Đã xóa: {removed['name']}[/]")
                    time.sleep(1)
            except:
                pass
                
        elif cmd == 'n':
            if accounts:
                return accounts
            else:
                console.print("[red]Vui lòng thêm ít nhất 1 tài khoản![/]")
                time.sleep(1)


def display_code_rich(data):
    val = float(data.get('value', 0))
    f_val = f"{val:,.0f}".replace(',', '.')
    created_ts = datetime.fromtimestamp(data.get('created_ts', 0)).strftime('%H:%M:%S %d/%m')
    expired_ts = datetime.fromtimestamp(data.get('expired_ts', 0)).strftime('%H:%M:%S %d/%m')
    remain = int(data.get('user_cnt', 0)) - int(data.get('progress', 0))
    
    info_table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 1))
    info_table.add_column("Key", style="bold cyan")
    info_table.add_column("Value", style="bold white", justify="right")
    
    info_table.add_row("Người tạo", str(data.get('nickname', 'Unknown')))
    info_table.add_row("UID", str(data.get('uid', '---')))
    info_table.add_row("Phần thưởng", f"{f_val} {data.get('currency', '').upper()}")
    info_table.add_row("Đã nhập", f"{data.get('progress', 0)} / {data.get('user_cnt', 0)}")
    info_table.add_row("Còn lại", str(remain))
    info_table.add_row("Thời gian tạo", created_ts)
    info_table.add_row("Hết hạn", expired_ts)
    
    panel = Panel(
        info_table,
        title=f"[bold yellow]THÔNG TIN CODE: {data.get('title', 'Unknown').upper()}[/]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)

    

def run_tool():
    global stop_spam_event
    accounts = manage_accounts()
    
    console.print("\n[bold yellow][*] Đang đồng bộ số dư tất cả tài khoản...[/]")
    update_all_wallets(accounts)
    
    while True:
        try:
            banner()
            console.print(build_dashboard())
            
            code = console.input(f"\n[bold green][>] NHẬP MÃ CODE: [/]").strip()
            if not code: continue
            
            res = check_code(accounts[0], code)
            
            if res.get('code') != 0:
                console.print(f"[bold red][!] Code lỗi hoặc không tồn tại: {res.get('msg')}[/]")
                time.sleep(2)
                continue
                
            data = res['data']
            display_code_rich(data)
            
            choice = console.input("[bold yellow][?] Bắt đầu canh code này? (y/n): [/]").lower()
            if choice != 'y': continue

            is_wait = console.input("[bold yellow][?] Canh lượt trống để nhập? (y/n): [/]").lower()
            if is_wait == 'y':
                try:
                    thres = int(console.input("[bold cyan][>] Ngưỡng lượt trống để nhập: [/]").strip())
                except:
                    thres = 5
                
                console.print(f"[bold magenta] [*] ĐANG CANH CODE... (Ngưỡng kích hoạt: {thres})[/]")
                
                while True:
                    try:
                        c_res = check_code(accounts[0], code)
                        if c_res.get('code') != 0:
                            console.print(f"\n[bold red][!] Code không khả dụng hoặc đã hết![/]")
                            break
                        
                        inf = c_res['data']
                        rem = int(inf['user_cnt']) - int(inf['progress'])
                        sys.stdout.write(f"\r\033[K[*] Còn lại: {rem} | Tổng: {inf['user_cnt']}")
                        sys.stdout.flush()
                        
                        if rem <= thres:
                            print()
                            console.print(f"[bold yellow][⚡] ĐẠT NGƯỠNG {thres}! KÍCH HOẠT TURBO...[/]")
                            break
                        
                        time.sleep(0.1)
                    except KeyboardInterrupt:
                        console.print(f"\n[bold red][!] Đã hủy canh.[/]")
                        sys.exit()
                    except:
                        time.sleep(0.5)

            console.print(f"[bold magenta] [*] BẮT ĐẦU CHẠY {len(accounts)} TÀI KHOẢN...[/]")

            succeeded_indices = set()
            max_rounds = 20

            def process_acc(idx, acc):
                if idx in succeeded_indices: return
                try:
                    res = exchange_code(acc, code)
                    code_res = res.get('code')
                    if code_res == 0:
                        v = float(res['data']['value'])
                        cur = res['data']['currency'].lower()
                        total_harvested[cur] += v
                        now_str = datetime.now().strftime('%H:%M:%S')
                        history_records.append([now_str, f"{acc['name']}", f"+{v:,.2f}", cur.upper()])
                        console.print(f"[bold green] [✓] {acc['name']}: +{v} {cur.upper()}[/]")
                        succeeded_indices.add(idx)
                    elif code_res == 100306:
                        console.print(f"[yellow] [!] {acc['name']}: Đã nhập trước đó[/]")
                        succeeded_indices.add(idx)
                    else:
                        console.print(f"[red] [X] {acc['name']}: Lỗi {code_res}[/]")
                except:
                    console.print(f"[red] [X] {acc['name']}: Lỗi kết nối[/]")

            for round_num in range(1, max_rounds + 1):
                if len(succeeded_indices) == len(accounts): break
                console.print(f"[bold cyan]--- Vòng {round_num}/{max_rounds} ---[/]")
                with ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(process_acc, idx, acc) for idx, acc in enumerate(accounts)]
                    for f in futures:
                        f.result()

            console.print("[bold green][✓] Kết thúc tiến trình nhập![/]")
            console.print("[bold yellow][*] Cập nhật số dư...[/]")
            update_all_wallets(accounts)

        except KeyboardInterrupt:
            console.print(f"\n[bold yellow][!] Đã dừng canh mã.[/]")
            stop_spam_event.set()
            time.sleep(1)
            sys.exit()


if __name__ == "__main__":
    try:
        run_tool()
    except KeyboardInterrupt:
        console.print(f"\n[bold red][!] ĐÃ TẮT TOOL.[/]")
        sys.exit()
