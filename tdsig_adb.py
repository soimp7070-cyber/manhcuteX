#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""
tds_multi_account_final_fix_v20_aggressive_switch.py
TRAODOISUB AUTO IG TOOL V7 - Hỗ trợ ĐA TÀI KHOẢN & ĐA THIẾT BỊ (Enhanced TUI V20)
- FIX CĂN BẢN: Đã sửa lỗi AttributeError: 'list' object has no attribute 'write' trong hàm save_accounts.
- UPDATE: Thêm chức năng [R]un Check vào menu quản lý cấu hình tài khoản để kiểm tra trạng thái Nick Instagram.
- FIX: Cải tiến hàm check_ig_run_status để nhận diện phản hồi "Cấu hình thành công!" (khi thiếu status ON/OFF).
- FIX MỚI (V20): Thêm lệnh API ÉP NICK CHẠY (add_ig_nick) ngay khi bắt đầu luồng để buộc TDS Server chuyển trạng thái "Nick đang chạy".
- FIX MỚI (BATCH CACHE): Gom 8 job Follow Cache để claim 1 lần.
- FIX (User): Bỏ claim REAL đơn lẻ cho job Follow, chỉ giữ claim REAL cho Like.
"""

import os, time, json, random, traceback, subprocess, threading
from typing import Dict, Any, List, Optional
from collections import deque
import sys 

try:
    import uiautomator2 as u2
except:
    u2 = None
import requests

# ----------------- RICH IMPORTS -----------------
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.live import Live
    from rich.status import Status
    from rich.text import Text
    from rich import box
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.style import Style
    RICH_ENABLED = True
except ImportError:
    # Fallback if rich is not installed
    def Console():
        class MockConsole:
            def print(self, *args, **kwargs):
                print(*args)
            def rule(self, *args, **kwargs):
                print("-" * 60)
            def log(self, *args, **kwargs):
                print(*args)
            def clear(self): # Fallback clear
                os.system('cls' if os.name == 'nt' else 'clear')
        return MockConsole()
    RICH_ENABLED = False

CONSOLE = Console()

# ----------------- BANNER DEFINITION & HELPER -----------------
BANNER = """
┏┓┳┓┳┓  ┳┏┓  ┏┳┓┳┓┏┓
┣┫┃┃┣┫  ┃┃┓   ┃ ┃┃┗┓
┛┗┻┛┻┛  ┻┗┛   ┻ ┻┛┗┛
"""
BANNER_PANEL = Panel(
    Text(BANNER, justify="center", style="bold #00ffc8"),
    title="[bold red]TDS AUTO IG TOOL V7[/bold red]",
    border_style="#00ffc8",
    box=box.DOUBLE_EDGE
)

def display_banner():
    """Hiển thị Banner cố định."""
    CONSOLE.print(BANNER_PANEL)
# ----------------- /BANNER DEFINITION & HELPER -----------------

# ----------------- GLOBAL STATE for Dashboard -----------------
DEVICE_STATS: Dict[str, Dict[str, Any]] = {}
LOG_BUFFER = deque(maxlen=20)
STATS_LOCK = threading.Lock()
LOG_LOCK = threading.Lock()

ACCOUNTS_FILE = "tds_accounts.json"
DEVICE_CONNECT_RETRY = 8
DEVICE_CONNECT_INTERVAL = 2

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "tds-auto-tool/1.0"})

# ----------------- DELAY FUNCTION (MODIFIED) -----------------
def rich_delay(seconds: float, status_msg: str, device_id: str, is_micro_delay: bool = False):
    """
    Thực hiện delay. Khi chạy cùng Live Dashboard, chỉ dùng time.sleep 
    và cập nhật trạng thái vào DEVICE_STATS để Dashboard hiển thị.
    """
    seconds = max(0.1, seconds) # Đảm bảo delay tối thiểu
    
    if is_micro_delay or not RICH_ENABLED:
        time.sleep(seconds)
        return

    update_device_stats(device_id, status=f'Delaying {int(seconds)}s') 
    time.sleep(seconds)
    
# ----------------- END DELAY FUNCTION -----------------

# ---------------- API helpers (Giữ nguyên) ----------------
def api_get(url: str, timeout=12):
    try:
        r = SESSION.get(url, timeout=timeout)
        text = (r.text or "").strip()
        if not text:
            return {"_empty": True}
        try:
            return r.json()
        except ValueError:
            return {"_invalid_json": r.text}
    except Exception as e:
        return {"_error": str(e)}

def check_login(token: str, display: bool = True) -> bool:
    """Kiểm tra token và tùy chọn hiển thị thông tin."""
    url = f"https://traodoisub.com/api/?fields=profile&access_token={token}"
    res = api_get(url)
    if isinstance(res, dict) and "data" in res:
        user = res["data"].get("user")
        xu = res["data"].get("xu")
        if display:
            CONSOLE.print(f"👤 [bold #00ffc8]{user}[/] | 💰 [bold #f8ff38]{xu} xu[/]")
        return True
    if display:
        CONSOLE.print("❌ [bold red]Token không hợp lệ hoặc API lỗi:[/bold red]", res)
    return False

def get_balance(token: str):
    url = f"https://traodoisub.com/api/?fields=profile&access_token={token}"
    res = api_get(url)
    if isinstance(res, dict) and "data" in res:
        try:
            return int(res["data"].get("xu", 0))
        except:
            return None
    return None

def get_jobs(token: str, job_field: str):
    url = f"https://traodoisub.com/api/?fields={job_field}&access_token={token}"
    return api_get(url)

def get_run_info(token: str, nick: str):
    url = f"https://traodoisub.com/api/?fields=instagram_run&id={nick}&access_token={token}"
    return api_get(url)

# FIX V20: Thêm tham số print_output để ẩn thông báo khi dùng cho mục đích ÉP NICK CHẠY
def add_ig_nick(token: str, ig_nick: str, print_output: bool = True):
    url = f"https://traodoisub.com/api/?fields=instagram_add&id={ig_nick}&access_token={token}"
    res = api_get(url)
    if isinstance(res, dict):
        if res.get("success"):
            if print_output:
                CONSOLE.print(f"✅ [bold green]IG nick '{ig_nick}' đã được thêm/kích hoạt thành công.[/bold green]")
        elif res.get("error") and "đã tồn tại" in str(res.get("error")):
            if print_output:
                CONSOLE.print(f"ℹ️ [yellow]IG nick '{ig_nick}' đã tồn tại và được kích hoạt chạy.[/yellow]")
        else:
            if print_output:
                CONSOLE.print("⚠️ [yellow]Thêm IG nick trả về:[/yellow]", res)
    else:
        if print_output:
            CONSOLE.print("⚠️ [bold red]Lỗi khi thêm IG nick:[/bold red]", res)
    return res

def claim_job(token: str, job_type: str, job_id: str, cache: bool=True,
              max_retries: int = 3, base_wait_on_error: int = 5, device_id: str = None):
    # Loại bỏ claim CACHE cho job LIKE theo fix mới
    if job_type.lower() == "like" and cache:
        return {"_skip_cache": "Skipped cache claim for LIKE job"}
    
    # [FIX BATCH CACHE] Loại bỏ claim CACHE đơn lẻ cho job FOLLOW
    if job_type.lower() == "follow" and cache:
        return {"_skip_cache": "Skipped single cache claim for FOLLOW job (using batch)"}
        
    claim_type = f"INS_{job_type.upper()}_CACHE" if cache else f"INS_{job_type.upper()}"
    url = f"https://traodoisub.com/api/coin/?type={claim_type}&id={job_id}&access_token={token}"
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        
        if attempt > 1:
            update_device_stats(device_id, status=f'Claim Retry {attempt}/{max_retries}')
            rich_delay(3, f"Claim attempt {attempt}/{max_retries}...", device_id)

        try:
            r = SESSION.get(url, timeout=12)
            text = (r.text or "").strip()
            if not text:
                app_log("⚠️ [yellow]API trả rỗng, retry sau 2s...[/yellow]", device_id)
                update_device_stats(device_id, status=f'API Empty, Retry 2s') 
                rich_delay(2, "API trả rỗng, retry...", device_id) 
                continue
            try:
                data = r.json()
            except ValueError:
                app_log(f"⚠️ [yellow]API trả JSON không hợp lệ:[/yellow] {text[:100]}", device_id)
                update_device_stats(device_id, status=f'API JSON Error, Retry {2 + attempt}s') 
                rich_delay(2 + attempt, "API trả JSON lỗi, retry...", device_id) 
                continue
            
            # Xử lý trường hợp Countdown của job LIKE
            cd = float(data.get("countdown",0))
            if job_type.lower()=="like" and cd > 0:
                wait = max(2,int(cd)+random.randint(1,3))
                app_log(f"⏱ API yêu cầu countdown {cd:.2f}s — chờ [magenta]{wait}s[/magenta] rồi retry...", device_id)
                update_device_stats(device_id, status=f'API Countdown {wait}s')
                rich_delay(wait, f"Countdown {cd:.2f}s...", device_id)
                continue
            
            if "error" in data:
                err = str(data["error"])
                
                # Lỗi quá nhanh
                if "quá nhanh" in err.lower() or "Thao tác quá nhanh" in err:
                    wait = base_wait_on_error + random.randint(2,5)
                    app_log(f"⏱ [yellow]API báo quá nhanh -> chờ {wait}s rồi retry...[/yellow]", device_id)
                    update_device_stats(device_id, status=f'Too Fast Delay {wait}s')
                    rich_delay(wait, "API báo quá nhanh, retry...", device_id) 
                    continue
                
                # Lỗi cần retry: "Lỗi vui lòng thử lại!!!"
                if not cache and ("vui lòng thử lại" in err.lower() or "vui lòng làm thêm" in err.lower()):
                    wait = random.randint(5, 8) 
                    app_log(f"⏱ [yellow]Claim Error (Cần Retry) -> chờ {wait}s rồi retry...[/yellow]", device_id)
                    update_device_stats(device_id, status=f'Claim Error Retry {wait}s')
                    rich_delay(wait, "Claim Error, retry...", device_id)
                    continue
                
                return data
            return data
        except Exception as e:
            app_log(f"⚠️ [bold red]Exception khi claim:[/bold red] {e}", device_id)
            update_device_stats(device_id, status=f'Exception Retry {2 + attempt}s') 
            rich_delay(2 + attempt, "Exception khi claim, retry...", device_id)
    app_log("❌ [bold red]Không thể claim sau nhiều lần thử. Bỏ job.[/bold red]", device_id)
    return None

# ---------------- NEW FUNCTION: Claim BATCH CACHE ----------------
def claim_batch_cache(token: str, job_ids: str,
              max_retries: int = 3, base_wait_on_error: int = 5, device_id: str = None):
    """
    Claim nhiều job Cache (INS_FOLLOW_CACHE) cùng lúc.
    job_ids là chuỗi ID ngăn cách bởi dấu phẩy (vd: "id1,id2,id3").
    """
    claim_type = "INS_FOLLOW_CACHE" # Chỉ dùng cho Follow Cache
    url = f"https://traodoisub.com/api/coin/?type={claim_type}&id={job_ids}&access_token={token}"
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        
        if attempt > 1:
            update_device_stats(device_id, status=f'Batch Cache Retry {attempt}/{max_retries}')
            rich_delay(3, f"Batch Cache attempt {attempt}/{max_retries}...", device_id)

        try:
            r = SESSION.get(url, timeout=15) # Tăng timeout nhẹ vì claim nhiều
            text = (r.text or "").strip()
            if not text:
                app_log("⚠️ [yellow]API Batch Cache trả rỗng, retry sau 2s...[/yellow]", device_id)
                rich_delay(2, "API Batch Cache Empty, retry...", device_id) 
                continue
            try:
                data = r.json()
            except ValueError:
                app_log(f"⚠️ [yellow]API Batch Cache trả JSON không hợp lệ:[/yellow] {text[:100]}", device_id)
                rich_delay(2 + attempt, "API Batch Cache JSON lỗi, retry...", device_id) 
                continue
            
            if "error" in data:
                err = str(data["error"])
                
                # Lỗi quá nhanh
                if "quá nhanh" in err.lower() or "Thao tác quá nhanh" in err:
                    wait = base_wait_on_error + random.randint(2,5)
                    app_log(f"⏱ [yellow]API Batch Cache báo quá nhanh -> chờ {wait}s rồi retry...[/yellow]", device_id)
                    rich_delay(wait, "API Batch Cache báo quá nhanh, retry...", device_id) 
                    continue
                
                # Các lỗi khác của Cache không nên retry nhiều
                app_log(f"❌ [bold red]Batch Cache Error:[/bold red] {err}", device_id)
                    
                # Lỗi cần retry: "Lỗi vui lòng thử lại!!!"
                if ("vui lòng thử lại" in err.lower() or "vui lòng làm thêm" in err.lower()):
                    wait = random.randint(5, 8) 
                    app_log(f"⏱ [yellow]Batch Cache Error (Cần Retry) -> chờ {wait}s rồi retry...[/yellow]", device_id)
                    update_device_stats(device_id, status=f'Claim Error Retry {wait}s')
                    rich_delay(wait, "Batch Cache Error, retry...", device_id)
                    continue
                
                return data

            return data # Trả về kết quả thành công
        
        except Exception as e:
            app_log(f"⚠️ [bold red]Exception khi claim Batch Cache:[/bold red] {e}", device_id)
            rich_delay(2 + attempt, "Exception khi claim Batch Cache, retry...", device_id)
            
    app_log("❌ [bold red]Không thể claim Batch Cache sau nhiều lần thử. Bỏ qua.[/bold red]")
    return None
# ---------------- /NEW FUNCTION: Claim BATCH CACHE ----------------


# ---------------- Multi Account Management (Nâng cấp TUI) ----------------
def load_accounts() -> List[Dict[str, Any]]:
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_accounts(accounts: List[Dict[str, Any]]):
    """
    Sửa lỗi TypeError: dump() takes 2 positional arguments but 3 positional arguments...
    Bằng cách chỉ truyền accounts (obj) và f (fp) vào json.dump().
    """
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        # Sửa: Xóa đối số accounts thứ hai
        json.dump(accounts, f, indent=2, ensure_ascii=False)

def prompt_account_details(account_id: int, initial: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    CONSOLE.clear() 
    display_banner()
    CONSOLE.rule(f"[bold blue]Tạo/Sửa Cấu hình Tài khoản {account_id}[/bold blue]", style="blue")
    
    # 1. Nhập Token và kiểm tra
    token = initial.get('token', '') if initial else ''
    
    token_panel = Panel(
        Text("BƯỚC 1: NHẬP VÀ KIỂM TRA TOKEN", justify="center", style="bold yellow"),
        border_style="yellow"
    )
    CONSOLE.print(token_panel)
    
    if token:
        CONSOLE.print(f"Token hiện tại: [dim]{token}[/dim]")
        use_old = Prompt.ask("Dùng lại Token đã lưu?", choices=["y", "n"], default="y")
        if use_old == "n":
            token = Prompt.ask("🔑 Nhập token TDS mới").strip()
    else:
        token = Prompt.ask("🔑 Nhập token TDS").strip()
    
    while not check_login(token):
        token = Prompt.ask("🔑 Nhập token TDS (Token không hợp lệ, nhập lại)").strip()
        
    # 2. Nhập Config
    CONSOLE.clear() 
    display_banner()
    CONSOLE.rule(f"[bold blue]Tạo/Sửa Cấu hình Tài khoản {account_id}[/bold blue]", style="blue")
        
    conf = initial.copy() if initial else {}
    conf["token"] = token
    conf["account_id"] = account_id
    
    config_panel = Panel(
        Text("BƯỚC 2: CẤU HÌNH INSTAGRAM & DELAY", justify="center", style="bold cyan"),
        border_style="cyan"
    )
    CONSOLE.print(config_panel)

    default_nick = conf.get("ig_nick", "")
    conf["ig_nick"] = Prompt.ask("📱 Nhập Instagram username", default=default_nick).strip()
    
    # CẤU HÌNH THỜI GIAN VÀ BATCH
    
    # [NEW] Cấu hình Delay PRE-CLAIM cho Follow
    default_fl_min = conf.get("fl_pre_claim_min", 5) 
    conf["fl_pre_claim_min"] = max(1, int(Prompt.ask(f"⏱ Follow - Delay PRE-CLAIM tối thiểu (s) [green](Mặc định: {default_fl_min})[/green]", default=str(default_fl_min)).strip() or default_fl_min))

    default_fl_max = conf.get("fl_pre_claim_max", 8) 
    conf["fl_pre_claim_max"] = max(conf["fl_pre_claim_min"], int(Prompt.ask(f"⏱ Follow - Delay PRE-CLAIM tối đa (s) [green](Mặc định: {default_fl_max})[/green]", default=str(default_fl_max)).strip() or default_fl_max))

    # [NEW] Cấu hình Delay PRE-CLAIM cho Like
    default_like_min = conf.get("like_pre_claim_min", 8) 
    conf["like_pre_claim_min"] = max(1, int(Prompt.ask(f"⏱ Like - Delay PRE-CLAIM tối thiểu (s) [green](Mặc định: {default_like_min})[/green]", default=str(default_like_min)).strip() or default_like_min))

    default_like_max = conf.get("like_pre_claim_max", 12) 
    conf["like_pre_claim_max"] = max(conf["like_pre_claim_min"], int(Prompt.ask(f"⏱ Like - Delay PRE-CLAIM tối đa (s) [green](Mặc định: {default_like_max})[/green]", default=str(default_like_max)).strip() or default_like_max))
    
    # Delay chung giữa các job
    default_delay_min = conf.get("delay_min", 7) 
    conf["delay_min"] = max(1, int(Prompt.ask(f"⏳ Delay tối thiểu giữa các job (s) [green](Mặc định: {default_delay_min})[/green]", default=str(default_delay_min)).strip() or default_delay_min))
    
    default_delay_max = conf.get("delay_max", conf["delay_min"] + 4) 
    conf["delay_max"] = max(conf["delay_min"], int(Prompt.ask(f"⏳ Delay tối đa giữa các job (s) [green](Mặc định: {default_delay_max})[/green]", default=str(default_delay_max)).strip() or default_delay_max))
    
    default_batch = conf.get("batch_jobs", 15)
    conf["batch_jobs"] = max(1, int(Prompt.ask(f"🧮 Batch job (số job tối đa/lần) [green](Mặc định: {default_batch})[/green]", default=str(default_batch)).strip() or default_batch))
    
    default_rest = conf.get("rest_time", 90) 
    conf["rest_time"] = max(1, int(Prompt.ask(f"😴 Rest time (seconds) sau khi hoàn thành batch [green](Mặc định: {default_rest})[/green]", default=str(default_rest)).strip() or default_rest))
    
    # Loại job
    CONSOLE.print("\n🔧 Chọn loại job:\n[1] Follow\n[2] Like\n[3] Both (random)")
    default_job_type = {"follow":"1","like":"2","both":"3"}.get(conf.get("job_type","both"),"3")
    ch = Prompt.ask(f"Chọn (1/2/3)", choices=["1", "2", "3"], default=default_job_type).strip()
    conf["job_type"] = "follow" if ch=="1" else "like" if ch=="2" else "both"
    
    CONSOLE.rule("[bold green]✅ Cấu hình Tài khoản đã hoàn tất[/bold green]")
    return conf
    
# ----------------- NEW FUNCTION: Check IG Run Status -----------------
def check_ig_run_status(accounts: List[Dict[str, Any]]):
    CONSOLE.clear()
    display_banner()
    CONSOLE.rule("[bold cyan]KIỂM TRA TRẠNG THÁI RUN CỦA INSTAGRAM NICK[/bold cyan]", style="cyan")
    
    if not accounts:
        CONSOLE.print("❌ [bold red]Không có tài khoản nào được cấu hình.[/bold red]")
        time.sleep(2)
        return

    table = Table(title="KẾT QUẢ KIỂM TRA TRẠNG THÁI RUN", box=box.ROUNDED, border_style="cyan")
    table.add_column("ID", style="yellow", justify="center")
    table.add_column("IG NICK", style="#00ffc8")
    table.add_column("RUN STATUS (TDS)", style="magenta")
    table.add_column("LƯU Ý", style="blue")
    
    for acc in accounts:
        token = acc['token']
        ig_nick = acc['ig_nick']
        acc_id = acc['account_id']
        
        res = get_run_info(token, ig_nick)
        
        status_text = "[red]Lỗi API[/red]"
        note_text = "Kiểm tra token/Lỗi kết nối"
        
        if isinstance(res, dict):
            if res.get("success"):
                data = res.get("data", {})
                status_val = data.get('status')
                msg_val = data.get('msg')
                
                if status_val == "ON":
                    status_text = "[bold green]ON[/bold green]"
                    note_text = "Sẵn sàng nhận job"
                elif status_val == "OFF":
                    status_text = "[bold yellow]OFF[/bold yellow]"
                    note_text = "Nick tạm tắt trên hệ thống TDS"
                elif status_val is None and msg_val == "Cấu hình thành công!":
                    status_text = "[bold blue]CONFIG OK[/bold blue]"
                    note_text = "Nick mới được cấu hình thành công"
                else:
                    status_text = f"[bold red]UNKNOWN ({status_val})[/bold red]"
                    note_text = "Lỗi không xác định hoặc thiếu STATUS"
                    
            elif res.get("error"):
                err_msg = str(res["error"])
                if "chưa được thêm" in err_msg.lower():
                    status_text = "[bold red]NOT ADDED[/bold red]"
                    note_text = "Nick chưa được thêm/xác nhận"
                elif "không hợp lệ" in err_msg.lower():
                    status_text = "[bold red]INVALID TOKEN[/bold red]"
                    note_text = "Token không hợp lệ"
                else:
                    status_text = f"[bold red]ERROR[/bold red]"
                    note_text = err_msg[:40] + "..."
            else:
                status_text = "[red]API Lỗi[/red]"
                note_text = str(res)
        
        table.add_row(str(acc_id), ig_nick, status_text, note_text)

    CONSOLE.print(table)
    
    Prompt.ask("Nhấn [bold green]Enter[/bold green] để quay lại menu chính")

# ----------------- /NEW FUNCTION: Check IG Run Status -----------------


def manage_accounts_config() -> List[Dict[str, Any]]:
    accounts = load_accounts()
    
    while True:
        CONSOLE.clear() 
        display_banner()
        CONSOLE.rule("[bold magenta]QUẢN LÝ CẤU HÌNH TÀI KHOẢN[/bold magenta]", style="magenta")
        
        table = Table(title="DANH SÁCH TÀI KHOẢN TDS", box=box.ROUNDED, border_style="#00ffc8")
        table.add_column("ID", style="cyan", justify="center")
        table.add_column("IG NICK", style="#00ffc8")
        table.add_column("JOB TYPE", style="yellow")
        table.add_column("DELAY", style="magenta")
        table.add_column("BATCH/REST", style="blue")
        table.add_column("STATUS", style="green")
        
        for i, acc in enumerate(accounts):
            token_valid = check_login(acc['token'], display=False)
            status = "[green]VALID[/green]" if token_valid else "[red]INVALID/Lỗi[/red]"
            table.add_row(
                str(i),
                acc.get('ig_nick', '-'),
                acc.get('job_type', '-').upper(),
                f"{acc.get('delay_min', '?')}-{acc.get('delay_max', '?')}s",
                f"{acc.get('batch_jobs', '?')}/{acc.get('rest_time', '?')}s",
                status
            )
        CONSOLE.print(table)
        
        if not accounts:
            choices_list = ["a", "x"]
            default_choice = "a"
            prompt_msg = "[bold cyan][A]dd Account[/bold cyan] | [bold red][X]it/Thoát[/bold red]"
        else:
            choices_list = ["a", "e", "d", "r", "s"] 
            default_choice = "s"
            prompt_msg = "[bold cyan][A]dd[/bold cyan] | [bold yellow][E]dit ID[/bold yellow] | [bold red][D]elete ID[/bold red] | [bold blue][R]un Check[/bold blue] | [bold green][S]tart[/bold green]"
            
        choice = Prompt.ask(prompt_msg, choices=choices_list, default=default_choice).lower()
        
        if choice == "s":
            if not accounts:
                CONSOLE.print("❌ [bold red]Cần ít nhất 1 tài khoản để chạy.[/bold red]")
                time.sleep(2)
                continue
            save_accounts(accounts) 
            return accounts
        
        elif choice == "a":
            new_id = len(accounts)
            new_account = prompt_account_details(new_id)
            accounts.append(new_account)
            save_accounts(accounts)
            
        elif choice == "e":
            if not accounts: continue
            try:
                edit_id = int(Prompt.ask("Nhập ID tài khoản cần Sửa").strip())
                if 0 <= edit_id < len(accounts):
                    accounts[edit_id] = prompt_account_details(edit_id, accounts[edit_id])
                    save_accounts(accounts)
                else:
                    CONSOLE.print("❌ [bold red]ID không hợp lệ.[/bold red]")
                    time.sleep(2)
            except ValueError:
                CONSOLE.print("❌ [bold red]Vui lòng nhập số.[/bold red]")
                time.sleep(2)
                
        elif choice == "d":
            if not accounts: continue
            try:
                delete_id = int(Prompt.ask("Nhập ID tài khoản cần Xóa").strip())
                if 0 <= delete_id < len(accounts):
                    accounts.pop(delete_id)
                    for i, acc in enumerate(accounts):
                         acc['account_id'] = i
                    save_accounts(accounts)
                    CONSOLE.print(f"✅ [bold green]Đã xóa tài khoản ID {delete_id}.[/bold green]")
                    time.sleep(1)
                else:
                    CONSOLE.print("❌ [bold red]ID không hợp lệ.[/bold red]")
                    time.sleep(2)
            except ValueError:
                CONSOLE.print("❌ [bold red]Vui lòng nhập số.[/bold red]")
                time.sleep(2)
                
        elif choice == "r": 
            if not accounts: 
                CONSOLE.print("❌ [bold red]Chưa có tài khoản để kiểm tra.[/bold red]")
                time.sleep(2)
                continue
            check_ig_run_status(accounts)
            
        elif choice == "x":
            CONSOLE.print("👋 [bold red]Thoát chương trình.[/bold red]")
            exit()
            
# ---------------- Device connection & Mapping (Nâng cấp TUI) ----------------
def list_adb_devices():
    try:
        result = subprocess.run(["adb","devices","-l"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")[1:]
        devices = []
        for line in lines:
            if not line.strip() or "offline" in line:
                continue
            parts = line.split()
            dev_id = parts[0]
            model_info = [p for p in parts if p.startswith("model:")]
            name = model_info[0].split(":")[1] if model_info else "Unknown"
            devices.append({"id": dev_id, "name": name, "last_acc": "No Info"})
        return devices
    except Exception as e:
        CONSOLE.print(f"⚠️ [bold red]Lỗi khi quét ADB devices:[/bold red] {e}")
        return []

def display_adb_devices_table(devices_info: List[Dict[str, Any]]):
    """Hiển thị bảng danh sách thiết bị ADB đã quét với STT bắt đầu từ 1."""
    CONSOLE.rule("[bold cyan]DANH SÁCH THIẾT BỊ ADB ĐÃ KẾT NỐI[/bold cyan]", style="cyan")
    
    table = Table(
        title="THIẾT BỊ ĐƯỢC PHÁT HIỆN", 
        box=box.HEAVY, 
        header_style=Style(color="yellow", bold=True),
        border_style="cyan"
    )
    
    table.add_column("STT", style="cyan", justify="center")
    table.add_column("NAME DEVICES", style="#00ffc8", justify="left")
    table.add_column("ID DEVICES", style="magenta", justify="left")
    table.add_column("LAST ACCOUNT", style="dim", justify="center")
    
    if not devices_info:
        table.add_row("---", "---", "---", "---")
    else:
        for i, dev in enumerate(devices_info):
            table.add_row(
                str(i+1),
                dev['name'],
                dev['id'],
                dev['last_acc']
            )
    CONSOLE.print(table)
    CONSOLE.print("\n")


def map_devices_to_accounts(devices_info: List[Dict[str, Any]], accounts: List[Dict[str, Any]]):
    
    if not devices_info or not accounts:
        return []
        
    CONSOLE.rule("[bold blue]LỰA CHỌN TÀI KHOẢN CHO TỪNG THIẾT BỊ[/bold blue]", style="blue")
    
    account_map = {}
    
    account_choices = [str(acc['account_id']) for acc in accounts]
    
    # Hiển thị danh sách tài khoản
    acc_table = Table(title="DANH SÁCH TÀI KHOẢN CÓ SẴN", box=box.ROUNDED, border_style="yellow")
    acc_table.add_column("ID", style="yellow", justify="center")
    acc_table.add_column("IG NICK", style="#00ffc8")
    
    for acc in accounts:
        acc_table.add_row(str(acc['account_id']), acc['ig_nick'])
    
    CONSOLE.print(acc_table)

    for i, dev in enumerate(devices_info):
        
        CONSOLE.print(f"\n[bold magenta]» Gán Thiết bị {i+1} - {dev['name']} ({dev['id']}):[/bold magenta]")
            
        while True:
            try:
                selected_acc_id = Prompt.ask(f"  -> Nhập ID Account (từ 0 đến {len(accounts)-1})", choices=account_choices)
                selected_acc_id = int(selected_acc_id)
                account_map[dev['id']] = accounts[selected_acc_id]
                break
            except (IndexError, ValueError):
                CONSOLE.print("❌ [bold red]ID Account không hợp lệ, thử lại.[/bold red]")

    final_mapping = []
    CONSOLE.rule("[bold green]✅ ÁNH XẠ HOÀN TẤT[/bold green]", style="green")
    for dev in devices_info:
        acc = account_map.get(dev['id'])
        if acc:
            final_mapping.append({
                'device_info': dev,
                'account_profile': acc
            })
            CONSOLE.print(f"🔗 [cyan]{dev['id']}[/] -> [yellow]({acc['account_id']}) {acc['ig_nick']}[/]")
    
    return final_mapping

def _connect_with_retry(connect_fn, label):
    last_exc = None
    for attempt in range(1, DEVICE_CONNECT_RETRY + 1):
        CONSOLE.print(f"🔗 Thử kết nối ({label}) lần [cyan]{attempt}/{DEVICE_CONNECT_RETRY}[/cyan]...")
        try:
            d = connect_fn()
            _ = d.info
            CONSOLE.log(f"✅ [bold green]Kết nối thành công[/bold green] ({label}).")
            return d
        except Exception as e:
            last_exc = e
            CONSOLE.log(f"✖ [bold red]Kết nối thất bại:[/bold red] {e}")
            rich_delay(DEVICE_CONNECT_INTERVAL, f"Nghỉ giữa lần retry {attempt}", label, is_micro_delay=True) 
    raise RuntimeError(f"Không thể kết nối thiết bị ({label}) sau {DEVICE_CONNECT_RETRY} lần. Lỗi: {last_exc}")

def connect_device(dev_info):
    if u2 is None:
        raise RuntimeError("uiautomator2 chưa cài: pip install uiautomator2")
    device_id = dev_info['id']
    if ":" in device_id:
        return _connect_with_retry(lambda: u2.connect(device_id), device_id)
    else:
        return _connect_with_retry(lambda: u2.connect_usb(device_id), device_id)

def ensure_device_connected(d, device_id):
    if u2 is None:
        raise RuntimeError("uiautomator2 chưa cài.")
    try:
        _ = d.info
        return d
    except:
        last_exc = None
        for attempt in range(1, DEVICE_CONNECT_RETRY + 1):
            try:
                if ":" in device_id:
                     d_new = u2.connect(device_id)
                else:
                     d_new = u2.connect_usb(device_id)
                _ = d_new.info
                return d_new
            except Exception as e:
                last_exc = e
                rich_delay(DEVICE_CONNECT_INTERVAL, f"Nghỉ giữa lần retry {attempt}", device_id, is_micro_delay=True) 
        raise RuntimeError(f"Không thể reconnect {device_id} sau {DEVICE_CONNECT_RETRY} lần. Lỗi: {last_exc}")

def open_link_intent(d, link, device_id):
    try:
        d.shell(['am','start','-a','android.intent.action.VIEW','-d',link,'com.instagram.android'])
    except:
        try:
            d.shell(['am','start','-a','android.intent.action.VIEW','-d',link])
        except Exception as e:
            app_log(f"❌ [bold red]Lỗi mở link:[/bold red] {e}", device_id)
    time.sleep(3) 

def perform_follow(d, device_id):
    selectors = [d(text="Follow"),d(text="Theo dõi"),
                 d(resourceId="com.instagram.android:id/row_profile_header_action_button"),
                 d(resourceId="com.instagram.android:id/button_primary")]
    for sel in selectors:
        try:
            if sel.exists(timeout=2):
                sel.click()
                app_log("✅ [bold green]Click Follow.[/bold green]", device_id)
                return True
        except:
            continue
    app_log("⚠️ [yellow]Không tìm thấy nút Follow.[/yellow]", device_id)
    return False

def perform_like(d, device_id):
    selectors = [d(description="Like"),d(description="Thích"),
                 d(resourceId="com.instagram.android:id/row_feed_button_like"),
                 d(resourceId="com.instagram.android:id/like_button")]
    for sel in selectors:
        try:
            if sel.exists(timeout=2):
                sel.click()
                app_log("💗 [bold magenta]Click Like.[/bold magenta]", device_id)
                return True
        except:
            continue
    app_log("⚠️ [yellow]Không tìm thấy nút Like.[/yellow]", device_id)
    return False


# ---------------- Dashboard Generators ----------------
def app_log(message: str, device_id: str = None):
    """Ghi log vào buffer chung để hiển thị trên dashboard."""
    timestamp = time.strftime("%H:%M:%S")
    device_str = f"[[#00ffc8]{device_id}[/]] " if device_id else ""
    log_msg = f"[dim]{timestamp}[/dim] {device_str}{message}"
    
    with LOG_LOCK:
        LOG_BUFFER.append(Text.from_markup(log_msg))

def generate_live_table() -> Table:
    """Tạo bảng trạng thái với thông tin tài khoản."""
    table = Table(
        box=box.DOUBLE, 
        expand=True,
        header_style=Style(color="#f8ff38", bold=True, frame=True) 
    )
    table.add_column("ID DEVICE", style="#00ffc8", justify="left")
    table.add_column("ACCOUNT (IG/ID)", style="yellow", justify="left") 
    table.add_column("STATUS", style="white", justify="center")
    table.add_column("JOBS", style="green", justify="right")
    table.add_column("BATCH", style="magenta", justify="center")
    table.add_column("XU", style="#f8ff38", justify="right")
    
    with STATS_LOCK:
        for stats in DEVICE_STATS.values():
            status = stats['status']
            
            # Tối ưu hóa logic chọn màu trạng thái
            if 'Error' in status or 'NOT ADDED' in status or 'Invalid' in status:
                status_style = "bold red"
            elif 'Delaying' in status or 'Resting' in status or 'Countdown' in status or 'Retry' in status or 'Too Fast' in status:
                status_style = "bold blue"
            elif 'Claiming' in status or 'CONFIG OK' in status or 'Setting' in status:
                status_style = "bold magenta"
            elif 'Getting' in status or 'Opening' in status or 'Checking' in status:
                status_style = "bold cyan"
            elif 'Connected' in status or 'Running' in status:
                status_style = "bold green"
            else:
                status_style = "yellow"

            table.add_row(
                stats['id'],
                f"{stats.get('ig_nick', '-')}/({stats.get('account_id', '-')})",
                Text(status, style=status_style),
                str(stats['total_done']),
                f"{stats['batch_count']}/{stats.get('batch_jobs', '?')}",
                str(stats['balance'])
            )
            
    return table

def generate_dashboard(total_balance=None, total_jobs=0) -> Layout:
    """Tạo layout dashboard hoàn chỉnh."""
    layout = Layout(name="root")
    
    header = BANNER_PANEL
    
    status_table = generate_live_table()
    status_panel = Panel(
        status_table, 
        title="[bold #f8ff38]» LIVE STATUS DEVICES «[/bold #f8ff38]", 
        border_style="#f8ff38", 
        box=box.HEAVY
    )

    with LOG_LOCK:
        log_content = Text("\n").join(LOG_BUFFER)
    log_panel = Panel(
        log_content, 
        title="[bold magenta]» EVENT LOG «[/bold magenta]", 
        border_style="magenta",
        box=box.HEAVY,
        height=10 
    )
    
    footer_text = Text.assemble(
        ("💰 Tổng Xu:", Style(color="yellow", bold=True)),
        (f" {total_balance if total_balance is not None else 'N/A':,}", Style(color="yellow", bold=True, reverse=True)),
        (" | 📈 Tổng Jobs:", Style(color="green", bold=True)),
        (f" {total_jobs}", Style(color="green", bold=True, reverse=True)),
        (" | CTRL+C để thoát", Style(dim=True)) 
    )
    footer = Panel(
        footer_text, 
        border_style="red",
        box=box.DOUBLE,
        title="[bold red]THÔNG TIN CHUNG[/bold red]",
        padding=(0, 1)
    )
    
    layout.split_column(
        Layout(header, size=8), 
        Layout(status_panel, name="status"),
        Layout(log_panel, name="logs", minimum_size=10),
        Layout(footer, size=3)
    )
    return layout

def update_device_stats(device_id: str, **kwargs):
    with STATS_LOCK:
        if device_id in DEVICE_STATS:
            DEVICE_STATS[device_id].update(**kwargs)

# ---------------- Core auto loop (Fixed) ----------------
def run_auto_for_device(device_info, d, account_profile):
    """Luồng tự động cho mỗi thiết bị, sử dụng cấu hình tài khoản riêng."""
    device_id = device_info['id']
    token = account_profile["token"]
    ig_nick = account_profile["ig_nick"]
    delay_min = account_profile["delay_min"]
    delay_max = account_profile["delay_max"]
    batch_jobs = account_profile["batch_jobs"]
    rest_time = account_profile["rest_time"]
    job_type = account_profile["job_type"]
    account_id = account_profile["account_id"]
    
    fl_min = account_profile.get("fl_pre_claim_min", 5)
    fl_max = account_profile.get("fl_pre_claim_max", 8)
    like_min = account_profile.get("like_pre_claim_min", 8)
    like_max = account_profile.get("like_pre_claim_max", 12)
    
    # [FIX BATCH CACHE] Danh sách lưu trữ các Cache ID của job Follow
    FOLLOW_CACHE_IDS: List[str] = [] 
    
    # ----------------- FIX V20: AGGRESSIVE NICK SWITCH -----------------
    app_log(f"THREAD {device_id} (ACC ID {account_id}) bắt đầu khởi tạo và ép nick chạy...", device_id)
    update_device_stats(device_id, 
        status='Setting Running Nick', 
        ig_nick=ig_nick,
        account_id=account_id,
        batch_jobs=batch_jobs
    )
    
    # Gửi lệnh ADD/SET NICK BẮT BUỘC (print_output=False để ẩn thông báo "đã tồn tại")
    add_res = add_ig_nick(token, ig_nick, print_output=False) 
    
    if add_res.get("error") and "không hợp lệ" in str(add_res.get("error")):
        app_log(f"❌ [bold red]KHỞI TẠO LỖI:[/bold red] Token không hợp lệ. Dừng luồng.", device_id)
        update_device_stats(device_id, status='Token Invalid')
        return
    
    # ----------------- KẾT THÚC FIX V20 -----------------

    # Bắt đầu kiểm tra trạng thái RUN sau khi đã ÉP nick chạy
    update_device_stats(device_id, status='Checking Run Status')
    
    try:
        runinfo = get_run_info(token, ig_nick)
            
        status_val = runinfo.get("data", {}).get("status")
        msg_val = runinfo.get("data", {}).get("msg")
        
        if status_val == "ON" or msg_val == "Cấu hình thành công!": 
            pass # OK để chạy (Bao gồm cả trường hợp ON và CONFIG OK sau khi ép chạy)
        elif status_val == "OFF":
            app_log(f"❌ [bold red]KHỞI TẠO LỖI:[/bold red] Nick {ig_nick} đang bị [yellow]OFF[/yellow] trên hệ thống TDS. Vui lòng bật thủ công.", device_id)
            update_device_stats(device_id, status='NOT ADDED/OFF')
            return
        elif status_val is None and msg_val != "Cấu hình thành công!":
            app_log(f"❌ [bold red]KHỞI TẠO LỖI:[/bold red] Nick {ig_nick} chưa có trạng thái RUN rõ ràng. Vui lòng kiểm tra trên web.", device_id)
            update_device_stats(device_id, status='NOT ADDED/OFF')
            return
        
    except Exception as e:
        app_log(f"❌ [bold red]KHỞI TẠO LỖI:[/bold red] {e}", device_id)
        update_device_stats(device_id, status='Error')
        return

    total_done = 0
    batch_count = 0
    update_device_stats(device_id, status='Running', total_done=0, batch_count=0, last_job='-')
    app_log("🚀 [bold green]Bắt đầu auto farm job[/bold green]", device_id)

    while True:
        try:
            d = ensure_device_connected(d, device_id=device_id)
            chosen = random.choice(["follow","like"]) if job_type=="both" else job_type
            field = "instagram_follow" if chosen=="follow" else "instagram_like"
            
            # DELAY TRƯỚC KHI LẤY JOB
            pre_job_delay = random.uniform(1.0, 3.0) 
            app_log(f"⏱ [yellow]Pre-Job Delay {pre_job_delay:.2f}s trước khi lấy job...[/yellow]", device_id)
            update_device_stats(device_id, status=f'Pre-Job Delay {pre_job_delay:.2f}s')
            rich_delay(pre_job_delay, "Chờ trước khi lấy job...", device_id) 
            
            update_device_stats(device_id, status=f'Getting {chosen.upper()} Jobs')
            jobs_resp = get_jobs(token, field)
            
            if not isinstance(jobs_resp, dict) or "data" not in jobs_resp or not jobs_resp["data"]:
                app_log(f"😴 Không có job [cyan]{chosen}[/cyan], chờ 15s...", device_id)
                update_device_stats(device_id, status=f'Resting (No {chosen} job)')
                rich_delay(15, f"Không có job {chosen}, nghỉ...", device_id) 
                continue

            job = random.choice(jobs_resp["data"])
            job_id = job.get("id")
            link = job.get("link") or job.get("url") or job.get("username")
            if not job_id or not link:
                app_log(f"⚠️ [yellow]Job không hợp lệ:[/bold red] {job}", device_id)
                rich_delay(2, "Job không hợp lệ...", device_id)
                continue

            app_log(f"🔎 Job: [bold magenta]{job_id}[/bold magenta] | Type: [bold green]{chosen.upper()}[/bold green]", device_id)
            update_device_stats(device_id, status=f'Opening Link ({chosen})', last_job=job_id)
            open_link_intent(d, link, device_id)
            update_device_stats(device_id, status=f'Performing {chosen.upper()}')
            acted = perform_follow(d, device_id) if chosen=="follow" else perform_like(d, device_id)

            if acted:
                
                if chosen=="follow":
                    
                    # [FIX BATCH CACHE] 1. Thu thập ID Cache
                    FOLLOW_CACHE_IDS.append(job_id)
                    app_log(f"➡️ [cyan]Đã thêm ID Cache: {job_id}[/] | Buffer: [yellow]{len(FOLLOW_CACHE_IDS)}/8[/yellow]", device_id)

                    # [FIX BATCH CACHE] 2. Claim BATCH CACHE khi đủ 8 job
                    if len(FOLLOW_CACHE_IDS) >= 8:
                        update_device_stats(device_id, status='Claiming BATCH CACHE (8 Follow)')
                        
                        # Chuyển list ID thành chuỗi ngăn cách bằng ','
                        ids_to_claim = ",".join(FOLLOW_CACHE_IDS) 
                        FOLLOW_CACHE_IDS.clear() # Xóa buffer sau khi đã lấy ID
                        
                        cache_res = claim_batch_cache(token, ids_to_claim, device_id=device_id) 
                        
                        if cache_res and cache_res.get("success"):
                            app_log(f"✅ [bold green]BATCH CACHE 8 job thành công![/bold green]", device_id)
                            # [FIX] Cập nhật balance sau khi BATCH CACHE thành công
                            bal = get_balance(token)
                            update_device_stats(device_id, balance=f"{bal:,}" if bal is not None else '-')
                        else:
                            msg_err = cache_res.get("error") if cache_res and cache_res.get("error") else "Lỗi không xác định"
                            app_log(f"❌ [bold red]BATCH CACHE 8 job thất bại:[/bold red] {msg_err}", device_id)

                    # 3. [FIX] Xóa bỏ Delay PRE-CLAIM REAL (dòng 545-550 cũ)
                    # (Đã xóa)
                
                if chosen=="like":
                    # LIKE: Bỏ qua Cache Claim. Chỉ Claim REAL.
                    like_pre_claim_delay = random.randint(like_min, like_max) 
                    app_log(f"⏱ [yellow]Like job: Delay {like_pre_claim_delay}s trước khi claim REAL...[/yellow]", device_id)
                    update_device_stats(device_id, status=f'Pre-Claim Delay {like_pre_claim_delay}s')
                    rich_delay(like_pre_claim_delay, f"Pre-Claim {chosen}...", device_id) 

                # [FIX] Chỉ chạy Claim REAL cho LIKE
                if chosen == "like":
                    update_device_stats(device_id, status='Claiming REAL')
                    # Claim REAL (cache=False)
                    real_res = claim_job(token, chosen, job_id, cache=False, device_id=device_id)
                    
                    if real_res and real_res.get("_skip_cache"):
                        pass 
                    elif real_res:
                        if real_res.get("success") or real_res.get("data"):
                            msg = real_res.get("msg") or real_res.get("data",{}).get("msg") or "✅ Thành công"
                            uid = real_res.get("data",{}).get("id") or job_id
                            app_log(f"💎 [bold yellow]REAL claim:[/bold yellow] ID={uid} | MSG=[green]{msg}[/]", device_id)
                            total_done += 1
                            batch_count += 1
                            bal = get_balance(token)
                            update_device_stats(device_id, 
                                total_done=total_done, 
                                batch_count=batch_count, 
                                balance=f"{bal:,}" if bal is not None else '-',
                                status=f'Running (Delay)'
                            )
                            app_log(f"📊 Total: [green]{total_done}[/] | Batch: [magenta]{batch_count}/{batch_jobs}[/]", device_id)
                        elif "error" in real_res:
                            app_log(f"❌ [bold red]REAL claim error:[/bold red] {real_res['error']}", device_id)
                            update_device_stats(device_id, status='Claim Error')
                
                # [FIX] Tăng counter cho Follow (vì nó không chạy claim REAL)
                elif chosen == "follow":
                    app_log(f"✅ [green]Follow OK (chờ batch claim).[/green]", device_id)
                    total_done += 1
                    batch_count += 1
                    update_device_stats(device_id, 
                        total_done=total_done, 
                        batch_count=batch_count, 
                        status=f'Running (Delay)'
                    )
                    app_log(f"📊 Total: [green]{total_done}[/] | Batch: [magenta]{batch_count}/{batch_jobs}[/]", device_id)
                        
                # [FIX] Giữ nguyên delay sau job
                delay = random.randint(delay_min, delay_max)
                app_log(f"⏳ Delay {delay}s...", device_id)
                update_device_stats(device_id, status=f'Delaying {delay}s')
                rich_delay(delay, "Nghỉ giữa các job...", device_id) 
            else:
                update_device_stats(device_id, status='Action Failed')
                rich_delay(2, "Thao tác lỗi...", device_id)

            if batch_count >= batch_jobs:
                app_log(f"🛌 [bold magenta]Batch {batch_jobs} job xong, nghỉ {rest_time}s...[/bold magenta]", device_id)
                update_device_stats(device_id, status=f'Resting ({rest_time}s)')
                rich_delay(rest_time, "Nghỉ batch...", device_id) 
                batch_count = 0
                update_device_stats(device_id, batch_count=0, status='Running')

        except KeyboardInterrupt:
            app_log("⏹️ [bold red]Dừng auto thủ công[/bold red]", device_id)
            update_device_stats(device_id, status='Stopped')
            break
        except Exception as e:
            exc_str = traceback.format_exc()
            app_log(f"⚠️ [bold red]Exception: {e}[/bold red]", device_id)
            update_device_stats(device_id, status='Error')
            rich_delay(5, "Lỗi hệ thống...", device_id) 

# ---------------- Entrypoint (Nâng cấp TUI) ----------------
def main():
    
    if not RICH_ENABLED:
        CONSOLE.print("[bold red]Lỗi: Thư viện rich chưa được cài đặt. Vui lòng chạy: pip install rich[/bold red]")
        return
        
    # 1. Quản lý và chọn Cấu hình Tài khoản
    accounts = manage_accounts_config()
    
    # 2. Quét thiết bị ban đầu
    devices_info = list_adb_devices()
    
    CONSOLE.clear()
    display_banner()
    CONSOLE.rule("[bold magenta]TDS AUTO IG TOOL V7 - LỰA CHỌN THIẾT BỊ[/bold magenta]", style="magenta")
    
    selected_indices: List[int] = []
    manual_devices_added: List[Dict[str, Any]] = []
    
    while True:
        all_devices = devices_info + manual_devices_added
        
        display_adb_devices_table(all_devices)

        if not all_devices:
            # SCENARIO 1: KHÔNG TÌM THẤY THIẾT BỊ NÀO 
            CONSOLE.print("⚠️ [yellow]Không tìm thấy thiết bị ADB tự động nào.[/yellow]")
            choice = Prompt.ask(
                "[bold cyan][A]dd IP:PORT[/bold cyan] | [bold red][X]it/Thoát[/bold red] | [bold yellow][R]escan[/bold yellow]",
                choices=["a", "x", "r"],
                default="a"
            ).lower()
            
            if choice == 'x':
                CONSOLE.print("❌ [bold red]Không có thiết bị để chạy. Thoát.[/bold red]")
                return
            
            if choice == 'r':
                CONSOLE.print("🔃 [yellow]Đang Rescan thiết bị...[/yellow]")
                with CONSOLE.status("Scanning for ADB devices..."):
                    devices_info = list_adb_devices() 
                time.sleep(1)
                CONSOLE.clear()
                display_banner()
                CONSOLE.rule("[bold magenta]TDS AUTO IG TOOL V7 - LỰA CHỌN THIẾT BỊ[/bold magenta]", style="magenta")
                continue 
                
            if choice == 'a':
                ip_ports_input = Prompt.ask("🔌 Nhập địa chỉ [bold cyan]IP:PORT[/bold cyan] (cách nhau bằng dấu phẩy, ví dụ: 192.168.1.1:5555)").strip()
                
                if not ip_ports_input:
                    CONSOLE.print("⚠️ [yellow]Input trống. Quay lại menu.[/yellow]")
                    time.sleep(1)
                    continue
                
                ip_list = [item.strip() for item in ip_ports_input.split(',') if item.strip()]
                
                for ip_port in ip_list:
                    if ":" not in ip_port:
                        CONSOLE.print(f"❌ [bold red]Sai định dạng cho '{ip_port}'. Bỏ qua thiết bị này.[/bold red]")
                        continue
                    
                    new_device = {"id": ip_port, "name": ip_port, "last_acc": "Manual Add"}
                    manual_devices_added.append(new_device)
                    CONSOLE.print(f"✅ [bold green]Đã thêm thiết bị:[/bold green] {ip_port}")
                
                time.sleep(1)
                CONSOLE.clear()
                display_banner()
                CONSOLE.rule("[bold magenta]TDS AUTO IG TOOL V7 - LỰA CHỌN THIẾT BỊ[/bold magenta]", style="magenta")
                continue
        
        # SCENARIO 2: ĐÃ CÓ THIẾT BỊ
        
        valid_stt = [str(i + 1) for i in range(len(all_devices))]
        CONSOLE.print(f"\n[bold yellow]STT có sẵn:[/bold yellow] {', '.join(valid_stt)}")
        
        selection = Prompt.ask(
            "🔌 Nhập [bold yellow]STT Thiết bị[/bold yellow] (vd: 1,2,3), [bold green]A[/bold green] (Tất cả), hoặc [bold cyan]ADD[/bold cyan] (Thêm IP:PORT)"
        ).strip().upper()

        if selection == 'A':
            selected_indices = [int(stt) - 1 for stt in valid_stt]
            break
            
        if selection == 'ADD':
            ip_ports_input = Prompt.ask("🔌 Nhập địa chỉ [bold cyan]IP:PORT[/bold cyan] (cách nhau bằng dấu phẩy, ví dụ: 192.168.1.1:5555)").strip()
            
            if not ip_ports_input:
                CONSOLE.print("⚠️ [yellow]Input trống. Quay lại chọn STT.[/yellow]")
                continue
                
            ip_list = [s.strip() for s in ip_ports_input.split(',') if s.strip()]
            
            for ip_port in ip_list:
                if ":" not in ip_port:
                    CONSOLE.print(f"❌ [bold red]Sai định dạng cho '{ip_port}'. Bỏ qua thiết bị này.[/bold red]")
                    continue
                
                new_device = {"id": ip_port, "name": ip_port, "last_acc": "Manual Add"}
                manual_devices_added.append(new_device)
                CONSOLE.print(f"✅ [bold green]Đã thêm thiết bị:[/bold green] {ip_port}")
            
            time.sleep(1)
            CONSOLE.clear()
            display_banner()
            CONSOLE.rule("[bold magenta]TDS AUTO IG TOOL V7 - LỰA CHỌN THIẾT BỊ[/bold magenta]", style="magenta")
            continue 
        
        # Xử lý lựa chọn STT
        selected_stt_raw = [s.strip() for s in selection.split(',') if s.strip()]
        
        invalid_stt = [stt for stt in selected_stt_raw if stt not in valid_stt]
        
        if invalid_stt:
            CONSOLE.print(f"❌ [bold red]STT không hợp lệ:[/bold red] {', '.join(invalid_stt)}. Vui lòng nhập lại.")
            continue
        
        if not selected_stt_raw:
            CONSOLE.print("❌ [bold red]Vui lòng chọn ít nhất một STT thiết bị.[/bold red]")
            continue
        
        selected_indices = [int(stt) - 1 for stt in selected_stt_raw]
        break 

    devices_to_map = [all_devices[i] for i in selected_indices]
             
    # 4. Ánh xạ Thiết bị đã chọn với Tài khoản
    mapped_configs = map_devices_to_accounts(devices_to_map, accounts)
    
    if not mapped_configs:
        CONSOLE.print("❌ [bold red]Không có thiết bị nào được ánh xạ với tài khoản. Thoát.[/bold red]")
        return

    threads: List[threading.Thread] = []
    connected_devices = []

    CONSOLE.rule("[bold blue]🔌 Đang kết nối thiết bị...[/bold blue]", style="blue")
    for mapping in mapped_configs:
        dev_info = mapping['device_info']
        acc_profile = mapping['account_profile']
        try:
            d = connect_device(dev_info)
            connected_devices.append({'info': dev_info, 'device': d, 'account': acc_profile})
            CONSOLE.print(f"✅ Đã kết nối [cyan]{dev_info['id']}[/] | Gán cho tài khoản ({acc_profile['account_id']}) [yellow]{acc_profile['ig_nick']}[/]")
            # Khởi tạo stats ban đầu
            DEVICE_STATS[dev_info['id']] = {
                'id': dev_info['id'],
                'name': dev_info['name'],
                'status': 'Connected',
                'total_done': 0,
                'batch_count': 0,
                'last_job': '-',
                # Định dạng xu ban đầu
                'balance': f"{get_balance(acc_profile['token']):,}" if get_balance(acc_profile['token']) is not None else '-',
                'ig_nick': acc_profile['ig_nick'],
                'account_id': acc_profile['account_id'],
                'batch_jobs': acc_profile['batch_jobs']
            }
        except Exception as e:
            CONSOLE.print(f"❌ [bold red]Không thể kết nối {dev_info['id']}: {e}[/bold red]")
    
    if not connected_devices:
        CONSOLE.print("❌ [bold red]Không có thiết bị nào được kết nối thành công. Thoát.[/bold red]")
        return
        
    CONSOLE.print(f"\n[bold green]✅ Kết nối thành công {len(connected_devices)} luồng. Bắt đầu Dashboard...[/bold green]")
    time.sleep(2) 

    # Lấy tổng xu ban đầu của tất cả các tài khoản
    initial_balance = sum(get_balance(acc['token']) or 0 for acc in accounts)
    
    CONSOLE.clear() 
    
    with Live(generate_dashboard(initial_balance, 0), refresh_per_second=4) as live:
        for dev_data in connected_devices:
            t = threading.Thread(target=run_auto_for_device, 
                                 args=(dev_data['info'], dev_data['device'], dev_data['account']), 
                                 daemon=True)
            t.start()
            threads.append(t)
            time.sleep(1) 

        try:
            total_jobs = 0
            while any(t.is_alive() for t in threads):
                current_total_balance = 0
                
                with STATS_LOCK:
                    total_jobs = sum(stats.get('total_done', 0) for stats in DEVICE_STATS.values())
                
                # Cập nhật tổng xu thực tế từ tất cả các token
                for acc in accounts:
                    balance = get_balance(acc['token'])
                    if balance is not None:
                         current_total_balance += balance

                live.update(generate_dashboard(current_total_balance, total_jobs))
                rich_delay(0.5, "Cập nhật Dashboard...", 'Main', is_micro_delay=True) 
        except KeyboardInterrupt:
            app_log("🛑 [bold red]Yêu cầu dừng toàn bộ tool...[/bold red]")
            # Tính lại tổng cuối
            current_total_balance = sum(get_balance(acc['token']) or 0 for acc in accounts)
            with STATS_LOCK:
                total_jobs = sum(stats.get('total_done', 0) for stats in DEVICE_STATS.values())
            live.update(generate_dashboard(current_total_balance, total_jobs))
        
    CONSOLE.rule("[bold red]🛑 Dừng tool hoàn tất.[/bold red]", style="red")
    CONSOLE.print("\n[bold yellow]Log cuối cùng:[/bold yellow]")
    with LOG_LOCK:
        for msg in LOG_BUFFER:
            CONSOLE.print(msg)
    
if __name__ == "__main__":
    main()