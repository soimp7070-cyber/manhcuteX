import sys
import requests
import platform
import os
import time
import concurrent.futures
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.align import Align
from rich import box
from rich.layout import Layout
from rich.live import Live

console = Console()
redeemed_or_exhausted_codes = set()
last_log_time = {}
user_claimed_history = {}
limit_reached_users = set()
system_logs = []

def clear_screen():
    os.system('cls' if platform.system() == "Windows" else 'clear')

def render_banner():
    banner_text = """
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
    """
    text = Text(banner_text, style="bold cyan", justify="center")
    panel = Panel(
        text,
        title="[bold yellow]✨ CANH CODE XWORLD ✨[/bold yellow]",
        subtitle="[bold green]ADMIN: XD| Zalo: https://zalo.me/g/ddxsyp497[/bold green]",
        border_style="bold magenta",
        box=box.DOUBLE_EDGE,
        padding=(1, 2)
    )
    console.print(panel)

def get_code_info(code):
    headers = {
        'accept': '*/*',
        'accept-language': 'vi,en;q=0.9',
        'content-type': 'application/json',
        'country-code': 'vn',
        'origin': 'https://xworld-app.com',
        'priority': 'u=1, i',
        'referer': 'https://xworld-app.com/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'xb-language': 'vi-VN',
    }
    try:
        json_data = {
            'code': code,
            'os_ver': 'android',
            'platform': 'h5',
            'appname': 'app',
        }
        response = requests.post('https://web3task.3games.io/v1/task/redcode/detail', headers=headers, json=json_data, timeout=5).json()
        if response.get('code') == 0 and response.get('message') == 'ok':
            data = response.get('data', {})
            admin_data = data.get('data', {}).get('admin', {})
            info = {
                'status': True,
                'total': data.get('user_cnt', 0),
                'used': data.get('progress', 0),
                'remaining': data.get('user_cnt', 0) - data.get('progress', 0),
                'currency': data.get('currency', 'UNK'),
                'value': admin_data.get('ad_show_value', 0),
                'name': admin_data.get('nick_name', 'Admin')
            }
            return info
        else:
            return {'status': False, 'message': response.get('message', 'Lỗi không xác định')}
    except Exception as e:
        return {'status': False, 'message': str(e)}

def nhap_code(userId, secretKey, code):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://xworld.info',
        'referer': 'https://xworld.info/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'user-id': userId,
        'user-secret-key': secretKey,
        'xb-language': 'vi-VN',
    }
    try:
        json_data = {
            'code': code,
            'os_ver': 'android',
            'platform': 'h5',
            'appname': 'app',
        }
        response = requests.post('https://web3task.3games.io/v1/task/redcode/exchange', headers=headers, json=json_data, timeout=5).json()
        if response.get('code') == 0 and response.get('message') == 'ok':
            val = response['data'].get('value', 0)
            curr = response['data'].get('currency', '')
            return True, f"SUCCESS|{userId}|{val}|{curr}"
        else:
            msg = response.get('message', 'Unknown')
            if "đạt đến giới hạn" in msg.lower() or "limit" in msg.lower():
                return False, "LIMIT_REACHED"
            if "reward has been received" in msg.lower():
                return False, "CLAIMED"
            if "not exist" in msg.lower() or "finish" in msg.lower():
                return False, "EXHAUSTED"
            return False, msg
    except Exception as e:
        return False, str(e)

def display_account_table(user_ids):
    table = Table(title="[bold green]DANH SÁCH TÀI KHOẢN HIỆN CÓ[/bold green]", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("STT", justify="center", width=5)
    table.add_column("User ID", justify="left", style="yellow")
    table.add_column("Trạng thái", justify="center", style="green")
    for idx, uid in enumerate(user_ids):
        table.add_row(str(idx + 1), uid, "Sẵn sàng")
    console.print(Align.center(table))

def load_data_comfirm_codexw():
    user_ids = []
    user_secretkeys = []
    try:
        if os.path.exists('data_xw_confirm_code.txt'):
            panel = Panel("[yellow]Phát hiện file dữ liệu cũ (data_xw_confirm_code.txt) trên hệ thống.[/yellow]", title="[bold blue]THÔNG TIN HỆ THỐNG[/bold blue]", box=box.ROUNDED)
            console.print(panel)
            choice = Prompt.ask("[bold cyan]Bạn có muốn sử dụng lại dữ liệu cũ không?[/bold cyan]", choices=["y", "n"], default="y")
            if choice.lower() == 'y':
                with open('data_xw_confirm_code.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if '|' in line:
                            parts = line.strip().split('|')
                            if len(parts) >= 2:
                                user_ids.append(parts[0])
                                user_secretkeys.append(parts[1])
                if user_ids:
                    console.print(f"[bold green]✅ Đã load thành công {len(user_ids)} tài khoản từ file.[/bold green]\n")
                    display_account_table(user_ids)
                    return user_ids, user_secretkeys
        
        console.print(Panel("[bold cyan]THIẾT LẬP TÀI KHOẢN MỚI[/bold cyan]", box=box.ROUNDED))
        num_str = Prompt.ask("[bold yellow]Nhập số lượng tài khoản cần chạy[/bold yellow]")
        num = int(num_str)
        for i in range(num):
            link = Prompt.ask(f"[bold white]Nhập link Vua thoát hiểm của tài khoản {i+1}[/bold white]")
            link = link.strip()
            try:
                uid = link.split('?userId=')[1].split('&')[0]
                key = link.split('secretKey=')[1].split('&')[0]
                user_ids.append(uid)
                user_secretkeys.append(key)
                console.print(f"[green]✔ Đã thêm tài khoản: {uid}[/green]")
            except:
                console.print("[bold red]❌ Link không hợp lệ, đã bỏ qua.[/bold red]")
        
        if user_ids:
            with open('data_xw_confirm_code.txt', 'w', encoding='utf-8') as f:
                for i in range(len(user_ids)):
                    f.write(f'{user_ids[i]}|{user_secretkeys[i]}\n')
            console.print("\n[bold green]✅ Đã lưu toàn bộ dữ liệu mới vào file cấu hình.[/bold green]")
            display_account_table(user_ids)
            
        return user_ids, user_secretkeys
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi hệ thống khi nhập liệu: {e}[/bold red]")
        sys.exit()

def display_code_info_table(valid_codes_data):
    table = Table(title="[bold magenta]DANH SÁCH CODE ĐANG THEO DÕI[/bold magenta]", box=box.HEAVY_HEAD, header_style="bold yellow")
    table.add_column("Mã Code", justify="center", style="cyan", width=20)
    table.add_column("Giá trị", justify="center", style="green")
    table.add_column("Đã dùng / Tổng", justify="center", style="white")
    table.add_column("Còn lại", justify="center", style="bold red")
    
    for data in valid_codes_data:
        table.add_row(
            data['code'],
            f"{data['value']} {data['currency']}",
            f"{data['used']} / {data['total']}",
            str(data['remaining'])
        )
    console.print(Align.center(table))

def add_system_log(message, style="white"):
    time_str = time.strftime("%H:%M:%S")
    formatted_msg = f"[{time_str}] {message}"
    system_logs.append((formatted_msg, style))
    if len(system_logs) > 15:
        system_logs.pop(0)

def render_dashboard(valid_codes_data, threshold):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="tables", size=8),
        Layout(name="logs")
    )
    
    header_text = Text(f"🔥 HỆ THỐNG ĐANG AUTO CANH {len(valid_codes_data)} CODE - NGƯỠNG TẤN CÔNG: {threshold} LƯỢT 🔥", style="bold white on red", justify="center")
    layout["header"].update(Panel(header_text, box=box.ROUNDED))
    
    table = Table(box=box.SIMPLE, expand=True, header_style="bold cyan")
    table.add_column("MÃ CODE", justify="center")
    table.add_column("PHẦN THƯỞNG", justify="center")
    table.add_column("LƯỢT CÒN LẠI", justify="center")
    table.add_column("TRẠNG THÁI", justify="center")
    
    for data in valid_codes_data:
        rem = data['remaining']
        status = "[bold green]Đang theo dõi...[/bold green]" if rem > threshold else "[bold red]ĐANG TẤN CÔNG![/bold red]"
        rem_display = f"[bold green]{rem}[/bold green]" if rem > threshold + 10 else f"[bold yellow]{rem}[/bold yellow]"
        if rem <= threshold: rem_display = f"[bold red blink]{rem}[/bold red blink]"
        table.add_row(data['code'], f"{data['value']} {data['currency']}", rem_display, status)
        
    layout["tables"].update(Panel(table, title="[bold yellow]BẢNG THEO DÕI THỜI GIAN THỰC[/bold yellow]", box=box.ROUNDED))
    
    log_text = Text()
    for msg, style in system_logs:
        log_text.append(f"{msg}\n", style=style)
        
    layout["logs"].update(Panel(log_text, title="[bold blue]NHẬT KÝ HỆ THỐNG[/bold blue]", box=box.ROUNDED, border_style="blue"))
    return layout

def main():
    clear_screen()
    render_banner()
    
    user_ids, user_secretkeys = load_data_comfirm_codexw()
    if not user_ids:
        console.print("[bold red]❌ Không có tài khoản nào được nạp. Thoát chương trình.[/bold red]")
        return
    
    for uid in user_ids:
        if uid not in user_claimed_history:
            user_claimed_history[uid] = set()

    console.print("\n", Panel("[bold cyan]CẤU HÌNH THEO DÕI CODE[/bold cyan]", box=box.ROUNDED))
    while True:
        try:
            sl_str = Prompt.ask("[bold yellow]Nhập số lượng code muốn đưa vào hệ thống canh[/bold yellow]")
            sl = int(sl_str)
            break
        except:
            console.print("[red]Vui lòng nhập một số nguyên hợp lệ![/red]")

    console.print("\n[bold magenta]⏳ Đang phân tích và kiểm tra dữ liệu code trên máy chủ...[/bold magenta]")
    
    valid_codes = []
    valid_codes_data_initial = []
    
    for i in range(sl):
        c = Prompt.ask(f"[bold white]Nhập mã code thứ {i+1}[/bold white]").strip()
        if not c: continue
        
        info = get_code_info(c)
        if info['status']:
            valid_codes.append(c)
            last_log_time[c] = 0
            info['code'] = c
            valid_codes_data_initial.append(info)
            console.print(f"[green]✔ Đã xác thực code: {c} | Trị giá: {info['value']} {info['currency']}[/green]")
        else:
            console.print(f"[bold red]❌ Code '{c}' không tồn tại hoặc lỗi: {info['message']}[/bold red]")
            
    if not valid_codes:
        console.print("[bold red]❌ Không có mã code nào hợp lệ để tiến hành canh. Thoát chương trình.[/bold red]")
        return

    console.print("\n")
    display_code_info_table(valid_codes_data_initial)

    console.print(Panel("[white]Hướng dẫn: Nếu code có 300 lượt, bạn muốn tool tự động cướp khi hệ thống báo chỉ còn 10 lượt -> Nhập số 10.[/white]", box=box.MINIMAL))
    try:
        threshold_str = Prompt.ask("[bold yellow]Nhập ngưỡng số lượt còn lại để kích hoạt chế độ cướp[/bold yellow]")
        threshold = int(threshold_str)
    except:
        threshold = 5

    clear_screen()
    add_system_log("Hệ thống bắt đầu chạy ngầm và quét API liên tục.", "bold cyan")
    add_system_log(f"Tổng tài khoản hoạt động: {len(user_ids)}", "cyan")
    
    with Live(render_dashboard(valid_codes_data_initial, threshold), refresh_per_second=2, screen=True) as live:
        while True:
            if len(limit_reached_users) >= len(user_ids):
                add_system_log("TẤT CẢ TÀI KHOẢN ĐỀU ĐÃ ĐẠT GIỚI HẠN NHẬP CODE TRONG NGÀY. HỆ THỐNG TỰ ĐỘNG DỪNG.", "bold red on white")
                live.update(render_dashboard(valid_codes_data_initial, threshold))
                time.sleep(3)
                break

            if not valid_codes:
                add_system_log("Toàn bộ danh sách code đã cạn kiệt hoặc hoàn thành. Dừng hệ thống.", "bold red")
                live.update(render_dashboard([], threshold))
                time.sleep(3)
                break

            current_dashboard_data = []

            for code in list(valid_codes): 
                eligible_users_indices = []
                for idx, uid in enumerate(user_ids):
                    if uid not in limit_reached_users and code not in user_claimed_history[uid]:
                        eligible_users_indices.append(idx)
                
                if not eligible_users_indices:
                    active_users_count = len(user_ids) - len(limit_reached_users)
                    if active_users_count > 0:
                        claimed_count = sum(1 for uid in user_ids if uid not in limit_reached_users and code in user_claimed_history[uid])
                        if claimed_count == active_users_count:
                            add_system_log(f"Tất cả tài khoản khả dụng đã nhận thành công code '{code}'. Bỏ qua code này.", "bold green")
                            valid_codes.remove(code)
                    continue

                info = get_code_info(code)
                
                if not info['status']:
                    continue
                
                info['code'] = code
                current_dashboard_data.append(info)
                
                remaining = info['remaining']
                curr_time = time.time()

                should_print = (curr_time - last_log_time.get(code, 0) > 45)
                
                if should_print:
                    if remaining > threshold + 10:
                        add_system_log(f"Quét định kỳ: {code} an toàn. Còn {remaining}/{info['total']} lượt.", "green")
                    else:
                        add_system_log(f"Quét định kỳ: {code} báo động. Còn {remaining}/{info['total']} lượt.", "yellow")
                    last_log_time[code] = curr_time

                if remaining <= threshold and remaining > 0:
                    add_system_log(f"PHÁT HIỆN CODE '{code}' CHỈ CÒN {remaining} LƯỢT! KÍCH HOẠT TẤN CÔNG ĐỒNG LOẠT!!!", "bold white on red")
                    live.update(render_dashboard(current_dashboard_data, threshold))
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=len(eligible_users_indices)) as executor:
                        futures = {
                            executor.submit(nhap_code, user_ids[i], user_secretkeys[i], code): user_ids[i] 
                            for i in eligible_users_indices
                        }
                        
                        for future in concurrent.futures.as_completed(futures):
                            uid = futures[future]
                            try:
                                success, msg = future.result()
                                if success:
                                    _, u, v, c = msg.split('|')
                                    add_system_log(f"[{u}] Cướp thành công! Cộng {v} {c}", "bold cyan")
                                    user_claimed_history[u].add(code)
                                else:
                                    if msg == "CLAIMED":
                                        add_system_log(f"[{uid}] Tài khoản này đã nhập code từ trước.", "dim white")
                                        user_claimed_history[uid].add(code) 
                                    elif msg == "LIMIT_REACHED":
                                        add_system_log(f"[{uid}] Đã chạm ngưỡng giới hạn ngày! Khoá tài khoản này.", "bold red")
                                        limit_reached_users.add(uid)
                                    elif msg == "EXHAUSTED":
                                        add_system_log(f"[{uid}] Chậm chân, code đã hết sạch lượt.", "bold red")
                                    else:
                                        add_system_log(f"[{uid}] Phát sinh lỗi: {msg}", "bold red")
                            except Exception as e:
                                add_system_log(f"Lỗi đa luồng nội bộ: {e}", "bold red")

                    final_check = get_code_info(code)
                    if final_check['status'] and final_check['remaining'] <= 0:
                        add_system_log(f"Code '{code}' đã chính thức cạn kiệt. Loại bỏ khỏi danh sách theo dõi.", "bold red")
                        valid_codes.remove(code)
                        current_dashboard_data = [d for d in current_dashboard_data if d['code'] != code]
                    else:
                        add_system_log(f"Đợt cướp kết thúc. Code '{code}' vẫn dư {final_check.get('remaining', 0)} lượt. Tiếp tục giám sát...", "bold yellow")

                elif remaining <= 0:
                    add_system_log(f"Code '{code}' đã sập (0 lượt). Loại bỏ khỏi hệ thống.", "bold red")
                    if code in valid_codes: valid_codes.remove(code)

            live.update(render_dashboard(current_dashboard_data, threshold))
            time.sleep(1.5) 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        console.print(Panel("[bold red]HỆ THỐNG ĐÃ ĐƯỢC DỪNG BỞI NGƯỜI DÙNG.[/bold red]", box=box.DOUBLE))
