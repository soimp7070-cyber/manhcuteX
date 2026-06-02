import requests, os, time, sys, random, json
from datetime import datetime
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except:
    os.system("pip install colorama")
    from colorama import Fore, Style, init

# --- CẤU HÌNH HỆ THỐNG ---
SESSION_FILE = "golike_v8_session.json"
HARD_UA = "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.163 Mobile Safari/537.36"

class GlobalStats:
    def __init__(self):
        self.total_success = 0
        self.total_coin = 0
        self.global_job_count = 0 # Biến đếm cộng dồn không reset

    def update(self, coin, success=True):
        if success:
            self.total_success += 1
            self.total_coin += coin
            self.global_job_count += 1

def banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{Fore.CYAN}██╗  ██╗███╗   ██╗    ████████╗  ██████╗   ██████╗ ██╗     ")
    print(f"{Fore.CYAN}██║ ██╔╝████╗  ██║    ╚══██╔══╝ ██╔═══██╗ ██╔═══██╗██║     ")
    print(f"{Fore.CYAN}█████╔╝ ██╔██╗ ██║       ██║    ██║   ██║ ██║   ██║██║     ")
    print(f"{Fore.CYAN}██╔═██╗ ██║╚██╗██║       ██║    ██║   ██║ ██║   ██║██║     ")
    print(f"{Fore.CYAN}██║  ██╗██║ ╚████║       ██║    ╚██████╔╝ ╚██████╔╝███████╗")
    print(f"{Fore.CYAN}╚═╝  ╚═╝╚═╝  ╚═══╝       ╚═╝     ╚═════╝   ╚═════╝ ╚══════╝")
    print(f"{Fore.MAGENTA}╔══════════════════════════════════════════════════════════╗")
    print(f"{Fore.MAGENTA}║ {Fore.YELLOW}                    GOLIKE PRO V8                        {Fore.MAGENTA}║")
    print(f"{Fore.MAGENTA}║ {Fore.WHITE}                 BẢN V8 : GOLIKE PRO                     {Fore.MAGENTA}║")
    print(f"{Fore.MAGENTA}╚══════════════════════════════════════════════════════════╝")

def loading_bar(seconds, message=""):
    try:
        for i in range(11):
            bar = f"{Fore.GREEN}▰" * i + f"{Fore.WHITE}▱" * (10 - i)
            sys.stdout.write(f"\r{Fore.YELLOW}[{message}] {bar} {i*10}% ")
            sys.stdout.flush()
            time.sleep(seconds/10)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    sys.stdout.write("\r" + " " * 150 + "\r")
    sys.stdout.flush()

def manage_sessions():
    sessions = {}
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f: sessions = json.load(f)
        except: pass
    banner()
    if sessions:
        print(f"{Fore.WHITE}[1] Dùng Token cũ ({sessions.get('username')})\n[2] Nhập Token mới")
        choice = input(f"{Fore.YELLOW}👉 Chọn (1-2): ").strip()
        if choice == '1': return sessions['auth'], sessions['t']
    
    auth = input(f"{Fore.CYAN}Nhập Authorization (Bearer...): ").strip()
    if "Bearer" not in auth: auth = "Bearer " + auth
    t = input(f"{Fore.CYAN}Nhập Header T: ").strip()
    return auth, t

def main():
    stats = GlobalStats()
    auth, t = manage_sessions()
    headers = {"Authorization": auth, "T": t, "User-Agent": HARD_UA, "Content-Type": "application/json"}
    ss = requests.Session()
    ss.headers.update(headers)

    try:
        u_res = ss.get("https://gateway.golike.net/api/users/me").json()
        if u_res.get("status") != 200:
            print(f"{Fore.RED}❌ Token không hợp lệ!"); return
        username = u_res['data']['username']
        with open(SESSION_FILE, "w") as f: json.dump({"auth": auth, "t": t, "username": username}, f)
    except: return

    while True: # MENU CHÍNH
        banner()
        print(f"{Fore.GREEN}👤 tên: {username} | Số dư: {u_res['data']['coin']}₫")
        print(f"{Fore.MAGENTA}📊 Tổng JOB: Thành công {stats.total_success} | +{stats.total_coin}₫")
        print(f"{Fore.CYAN}" + "─"*55)
        print(f"{Fore.WHITE}[1] TikTok      [2] Instagram")
        print(f"{Fore.WHITE}[3] YouTube     [4] Snapchat")
        print(f"{Fore.WHITE}[5] Pinterest   [6] VIP : TIKTOK + SNAPCHAT")
        print(f"{Fore.WHITE}[7] VIP : YOUTUBE + SNAPCHAT + Pinterest")
        print(f"{Fore.YELLOW}[8] VIP : YOUTUBE + SNAPCHAT + Pinterest + INSTAGRAM")
        print(f"{Fore.RED}[0] THOÁT TOOL")
        
        choice = input(f"{Fore.YELLOW}👉 Chọn (0-8): ").strip()
        if choice == '0': break
        
        p_map = {
            "1":["tiktok"], "2":["instagram"], "3":["youtube"], "4":["snapchat"], "5":["pinterest"], 
            "6":["tiktok", "snapchat"], 
            "7":["youtube", "snapchat", "pinterest"],
            "8":["youtube", "snapchat", "pinterest", "instagram"]
        }
        selected_codes = p_map.get(choice)
        if not selected_codes: continue

        acc_configs = {} # Lưu danh sách account theo từng nền tảng
        for code in selected_codes:
            url = f"https://gateway.golike.net/api/{code}-account?limit=100"
            acc_res = ss.get(url).json()

            if acc_res.get("status") != 200:
                print(f"\n{Fore.RED}❌ Không lấy được danh sách tài khoản {code.upper()}")
                continue

            if not acc_res.get('data'):
                print(f"\n{Fore.RED}❌ Không có tài khoản {code.upper()} hoặc API trả về rỗng")
                continue

            if acc_res.get("status") == 200:
                print(f"\n{Fore.YELLOW}--- Danh sách tài khoản {code.upper()} ---")
                
                # Hiển thị số thứ tự và Tên tài khoản
                for i, a in enumerate(acc_res['data']): 
                    name = a.get('nickname') or a.get('username') or a.get('name') or "No Name"
                    print(f"{Fore.WHITE}[{i+1}] {Fore.GREEN}ID: {a['id']}{Fore.WHITE} | Tên: {name}")
                
                if code == "instagram":
                    print(f"{Fore.CYAN}[*] Mẹo: Nhấn ENTER để tool tự động chạy xoay vòng TẤT CẢ account Instagram.")
                    target_id = input(f"{Fore.YELLOW}👉 Nhập ID INSTAGRAM: ").strip()
                    if not target_id:
                        # Lưu toàn bộ account IG để chạy xoay vòng
                        acc_configs[code] = acc_res['data']
                    else:
                        acc_configs[code] = [a for a in acc_res['data'] if str(a['id']) == target_id]
                else:
                    target_id = input(f"{Fore.YELLOW}👉 Nhập ID {code.upper()} (Enter lấy acc đầu tiên): ").strip()
                    if not target_id: 
                        acc_configs[code] = [acc_res['data'][0]]
                    else:
                        acc_configs[code] = [a for a in acc_res['data'] if str(a['id']) == target_id]

        if not acc_configs: continue
        delay = int(input(f"\n{Fore.YELLOW}👉 Giây chờ làm nhiệm vụ: ") or 15)
        max_j = int(input(f"{Fore.YELLOW}👉 Số lượng nhiệm vụ muốn chạy ở phiên này: ") or 100)

        banner()
        print(f"{Fore.CYAN}🚀 Đang chạy... {Fore.RED}(Nhấn Ctrl+C để trở về Menu)")
        
        session_run_count = 0 
        ig_pointer = 0 # Con trỏ dùng để xoay vòng Instagram

        try:
            while session_run_count < max_j:
                # Random chọn 1 nền tảng trong các nền tảng đã chọn
                p_code = random.choice(list(acc_configs.keys()))
                
                # Logic Xoay vòng Instagram
                if p_code == "instagram":
                    current_acc = acc_configs[p_code][ig_pointer]
                else:
                    current_acc = random.choice(acc_configs[p_code])
                
                acc_id = current_acc['id']
                acc_name = current_acc.get('nickname') or current_acc.get('username') or "No Name"
                
                # --- FETCH JOB ---
                if p_code == "instagram":
                    job_url = f"https://gateway.golike.net/api/advertising/publishers/instagram/jobs?instagram_account_id={acc_id}&data=null"
                else:
                    job_url = f"https://gateway.golike.net/api/advertising/publishers/{p_code}/jobs?account_id={acc_id}"
                
                try:
                    job_res = ss.get(job_url).json()
                except: continue

                if job_res.get("status") != 200:
                    sys.stdout.write(f"\r{Fore.RED}[!] {p_code.upper()} đang lọc job mới...         ")
                    time.sleep(3)
                    # Nếu IG hết job, chuyển sang Acc IG tiếp theo
                    if p_code == "instagram" and len(acc_configs['instagram']) > 1:
                        ig_pointer = (ig_pointer + 1) % len(acc_configs['instagram'])
                        next_acc_name = acc_configs['instagram'][ig_pointer].get('username')
                        print(f"\n{Fore.YELLOW}🔄 [IG] Acc {acc_name} hết job. Tự động chuyển sang -> {next_acc_name}")
                    continue

                job = job_res['data']
                job_id = job['id']
                job_type = job.get('type', 'job')
                price = job.get('prices') or job.get('coin') or 35
                now = datetime.now().strftime("%H:%M:%S")

                # --- BỘ LỌC TIKTOK THÔNG MINH ---
                if p_code == "tiktok":
                    skip_payload = {"users_advertising_id": job_id, "account_id": acc_id, "ads_id": job_id, "async": True}
                    if job_type.lower() == "comment":
                        print(f"{Fore.RED}[Bỏ Qua] {Fore.WHITE}TikTok Comment (Không làm rác acc) | ID: {job_id}")
                        ss.post(f"https://gateway.golike.net/api/advertising/publishers/tiktok/skip-jobs", json=skip_payload)
                        time.sleep(1); continue
                    if job_type.lower() == "follow" and int(price) < 20:
                        print(f"{Fore.RED}[Bỏ Qua] {Fore.WHITE}TikTok Follow giá bèo ({price}đ) | ID: {job_id}")
                        ss.post(f"https://gateway.golike.net/api/advertising/publishers/tiktok/skip-jobs", json=skip_payload)
                        time.sleep(1); continue

                # Hiển thị Tên tài khoản trên thanh Loading
                comment = job.get('message', '') or job.get('comment', '')
                if comment:
                    os.system(f"termux-clipboard-set '{comment}' > /dev/null 2>&1")
                    loading_msg = f"Làm {p_code.upper()} | {job_type.upper()} | tài khoản: {acc_name}"
                else:
                    loading_msg = f"Làm {p_code.upper()} | {job_type.upper()} | tài khoản: {acc_name}"

                os.system(f"termux-open-url '{job['link']}' > /dev/null 2>&1")
                loading_bar(delay, loading_msg)

                # --- BÁO CÁO HOÀN THÀNH ---
                if p_code == "instagram":
                    complete_url = "https://gateway.golike.net/api/advertising/publishers/instagram/complete-jobs"
                    payload = {"instagram_account_id": int(acc_id), "instagram_users_advertising_id": job_id, "type": job_type}
                else:
                    complete_url = f"https://gateway.golike.net/api/advertising/publishers/{p_code}/complete-jobs"
                    payload = {"users_advertising_id": job_id, "account_id": acc_id, "ads_id": job_id, "async": True}

                success_coin, status_log = 0, f"{Fore.RED}[Thất bại]"
                time.sleep(2)

                try:
                    done = ss.post(complete_url, json=payload).json()
                    if done.get("status") == 200:
                        success_coin = done.get("data", {}).get("prices") or price
                        status_log = f"{Fore.GREEN}[Nhận: {success_coin}₫]"
                        stats.update(success_coin, True)
                    else:
                        skip_url = complete_url.replace("complete-jobs", "skip-jobs")
                        ss.post(skip_url, json=payload)
                except: pass

                session_run_count += 1
                
                # In Log chuẩn V6 (Đếm Job tổng cộng dồn)
                current_job_display = stats.global_job_count if success_coin > 0 else stats.global_job_count + 1
                
                print(f"{Fore.WHITE}[{session_run_count}/{max_j}] "
                      f"{Fore.BLUE}[{now}] "
                      f"{Fore.CYAN}[{p_code}] "
                      f"{Fore.YELLOW}[{job_type.lower()}] "
                      f"{Fore.MAGENTA}[Job: {current_job_display}] "
                      f"{status_log} "
                      f"{Fore.GREEN}[Tổng: {stats.total_coin}đ]")

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Đã dừng! Quay lại Menu...")
            time.sleep(1.5)
            continue 

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit()
