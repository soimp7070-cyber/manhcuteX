# Kramer/Specter Deobf by Thesmartcat2303
# file name: [encrypted_TikTok_Studio.py] (py - 3.12)
# dump -> code 0

# a132c42ea9acf4947c4ebd13239d58e5
import os
import sys
import time
import random
import requests
import subprocess
import re
from curl_cffi import requests as cffi_requests
from colorama import Fore, init
from tabulate import tabulate
from termcolor import colored
import uiautomator2 as u2
from uiautomator2.exceptions import UiObjectNotFoundError

# Initialize colorama
init()

# Display banner
def banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner_text = f"""
{Fore.LIGHTRED_EX}╔══════════════════════════════════════════════════════════════════╗
{Fore.RED}║ ██╗  ██╗███╗   ███╗██╗  ██╗████████╗ ██████╗  ██████╗ ██╗       ║
{Fore.LIGHTRED_EX}║ ██║  ██║████╗ ████║██║ ██╔╝╚══██╔══╝██╔═══██╗██╔═══██╗██║       ║
{Fore.RED}║ ███████║██╔████╔██║█████╔╝    ██║   ██║   ██║██║   ██║██║       ║
{Fore.LIGHTRED_EX}║ ██╔══██║██║╚██╔╝██║██╔═██╗    ██║   ██║   ██║██║   ██║██║       ║
{Fore.RED}║ ██║  ██║██║ ╚═╝ ██║██║  ██╗   ██║   ╚██████╔╝╚██████╔╝███████╗  ║
{Fore.LIGHTRED_EX}║ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝  ║
{Fore.LIGHTRED_EX}╠══════════════════════════════════════════════════════════════════╣
{Fore.LIGHTYELLOW_EX}║                    🔥 TOOL BY : HMKTOOL 🔥                      ║
{Fore.LIGHTYELLOW_EX}║                    🎬 YOUTUBE : HMKTOOL                         ║
{Fore.LIGHTYELLOW_EX}║                    🎵 TIKTOK  : HMKTOOL                         ║
{Fore.LIGHTYELLOW_EX}║                    💬 ZALO    : HMKTOOL                         ║
{Fore.LIGHTYELLOW_EX}║                    📞 CONTACT : HMKTOOL                         ║
{Fore.LIGHTRED_EX}╚══════════════════════════════════════════════════════════════════╝
{Fore.RESET}
"""
    print(banner_text)

# Check ADB installation
def check_adb():
    try:
        result = subprocess.run(["adb", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            display_temp_message("❌ Lỗi: ADB không được cài đặt hoặc không phản hồi. Vui lòng cài đặt ADB và thêm vào PATH.")
            sys.exit(1)
    except FileNotFoundError:
        display_temp_message("❌ Lỗi: ADB không được cài đặt. Vui lòng cài đặt ADB và thêm vào PATH.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        display_temp_message("❌ Lỗi: ADB không phản hồi. Kiểm tra cài đặt ADB.")
        sys.exit(1)

# Get list of connected ADB devices
def get_connected_devices():
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().splitlines()
        devices = [line.split()[0] for line in lines[1:] if "device" in line and "unauthorized" not in line]
        if not devices:
            print(Fore.RED + f"❌ Lỗi: Không tìm thấy thiết bị nào được kết nối qua ADB.")
            time.sleep(3)
            print(Fore.RED + f"❌ Vui lòng kết nối với với adb để auto: ")
            sys.exit(1)
        return devices
    except subprocess.TimeoutExpired:
        display_temp_message("❌ Lỗi: ADB không phản hồi. Kiểm tra kết nối ADB.")
        sys.exit(1)
    except Exception as e:
        display_temp_message(f"❌ Lỗi khi lấy danh sách thiết bị: ")
        sys.exit(1)

# Display temporary message
def display_temp_message(message, color=Fore.RED, duration=2):
    print(f"{color}{message}", end="\r")
    time.sleep(duration)
    print("\r" + " " * len(message), end="\r")

# Fetch TikTok account list
def chonacc():
    json_data = {}
    try:
        response = cffi_requests.get('https://gateway.golike.net/api/tiktok-account', impersonate="chrome", headers=headers, json=json_data).json()
        return response
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi lấy danh sách tài khoản: ")
        return None

# Fetch task
def nhannv(account_id):
    params = {
        'account_id': account_id,
        'data': 'null',
    }
    json_data = {}
    try:
        response = cffi_requests.get('https://gateway.golike.net/api/advertising/publishers/tiktok/jobs', impersonate="chrome", params=params, headers=headers, json=json_data).json()
        return response
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi nhận nhiệm vụ: ")
        return None

# Complete task
def hoanthanh(ads_id, account_id):
    json_data = {
        'ads_id': ads_id,
        'account_id': account_id,
        'async': True,
        'data': None,
    }
    try:
        response = cffi_requests.post(
            'https://gateway.golike.net/api/advertising/publishers/tiktok/complete-jobs', impersonate="chrome",
            headers=headers, json=json_data
        ).json()
        return response
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi hoàn thành nhiệm vụ: ")
        return None

# Report error
def baoloi(ads_id, object_id, account_id, loai):
    json_data1 = {
        'description': 'Báo cáo hoàn thành thất bại',
        'users_advertising_id': ads_id,
        'type': 'ads',
        'provider': 'tiktok',
        'fb_id': account_id,
        'error_type': 6,
    }
    try:
        cffi_requests.post('https://gateway.golike.net/api/report/send', impersonate="chrome", headers=headers, json=json_data1).json()
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi báo lỗi (bước 1): ")

    json_data = {
        'ads_id': ads_id,
        'object_id': object_id,
        'account_id': account_id,
        'type': loai,
    }
    try:
        cffi_requests.post(
            'https://gateway.golike.net/api/advertising/publishers/tiktok/skip-jobs', impersonate="chrome",
            headers=headers, json=json_data
        ).json()
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi báo lỗi (bước 2): ")

# Display TikTok account list
def dsacc(chontk_TikTok):
    while True:
        try:
            if chontk_TikTok["status"] != 200:
                print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mAuthorization hoặc T sai, hãy nhập lại!!!")
                sys.exit()
            banner()
            table_data = []
            for i in range(len(chontk_TikTok["data"])):
                table_data.append([
                    f"\033[1;36m[{i + 1}]",
                    f"\033[1;93m{chontk_TikTok['data'][i]['unique_username']}",
                    f"\033[1;32mHoạt Động"
                ])
            headers = [
                colored("STT", "blue", attrs=["bold"]),
                colored("ID Tài Khoản", "yellow", attrs=["bold"]),
                colored("Trạng Thái", "green", attrs=["bold"]),
            ]
            print(colored("\n📋 DANH SÁCH TÀI KHOẢN TIKTOK 📋", "blue", attrs=["bold"]))
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
            break
        except Exception as e:
            print(Fore.RED + f"[✖] Lỗi khi hiển thị danh sách tài khoản: ")
            time.sleep(10)

# Hàm lấy user_id từ username
def get_user_id(link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36",
    }
    response = requests.get(link, headers=headers)

    if response.status_code != 200:
        print(f"Không thể mở trang. Bỏ qua job nhé.")
        return None

    # Tìm uid bằng regex
    match = re.search(r'"id":"(\d{10,30})"', response.text)
    if match:
        return match.group(1)
    else:
        print("Lỗi không thể mở link. Bỏ qua job nhé.")
        return None

# Display UI
def hien_thi_ui():
    os.system("cls" if os.name == "nt" else "clear")
    banner()
    print(f"\033[1;35m════════════════════════════════════════════════════════════════════")
    if bang_nhan_tien:
        print(tabulate(bang_nhan_tien, headers=headers_table, tablefmt="fancy_grid"))
    print(f"""{Fore.YELLOW}┌──────────────────────────────────────────────────────────────────┐
│     {Fore.WHITE}Code Tool By: {Fore.CYAN}HuongDev           {Fore.MAGENTA}Youtube: {Fore.WHITE}Hướng Dev - MMO    {Fore.YELLOW}│
└──────────────────────────────────────────────────────────────────┘{Fore.RESET}
""")

# Initialize script
banner()
check_adb()
devices = get_connected_devices()
if not devices:
    display_temp_message("❌ Không có thiết bị nào được kết nối.")
    sys.exit(1)
headers_table = [
    "\033[1;97mSTT",
    "\033[1;33mThời gian",
    "\033[1;32mTrạng thái",
    "\033[1;31mType Job",
    "\033[1;91m+Xu \033[1;33m(Tổng)"
]
device_list = [[colored(str(i+1), "cyan"), colored(serial, "red"), colored("Hoạt động", "green")]
               for i, serial in enumerate(devices)]

print(colored("📱 DANH SÁCH THIẾT BỊ KẾT NỐI 📱", "blue", attrs=["bold"]))
print(tabulate(device_list, headers=headers_table[:3], tablefmt="fancy_grid"))

# Select device
while True:
    try:
        choice = int(input(colored("👉 Nhập số thứ tự thiết bị muốn kết nối: ", "magenta")))
        if 1 <= choice <= len(devices):
            break
        display_temp_message("❌ Lựa chọn không hợp lệ, vui lòng chọn lại.")
    except ValueError:
        display_temp_message("❌ Vui lòng nhập một số hợp lệ.")

serial_chosen = devices[choice - 1]
print(colored(f"\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mĐang kết nối với thiết bị: {serial_chosen}", "green", attrs=["bold"]))

# Connect to Android device
try:
    device_serial = devices[choice - 1]  # Use selected device
    d = u2.connect(device_serial)
    print(Fore.GREEN + f"[✔] Đã kết nối với thiết bị: {device_serial}")
except Exception as e:
    print(Fore.RED + f"[✖] Lỗi khi kết nối với thiết bị: ")
    sys.exit(1)

print(f"\033[1;35m═══════════════════════════════════════════════════════════════════")
print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập \033[1;31m1 \033[1;33mđể vào \033[1;34mTool TikTok\033[1;33m")
print(Fore.RED + '\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mNhập 2 Để Xóa Authorization Hiện Tại')

# Select option
while True:
    try:
        choose = int(input(Fore.WHITE + '\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập Lựa Chọn (1 hoặc 2): '))
        if choose not in [1, 2]:
            print(Fore.RED + "\n❌ Lựa chọn không hợp lệ! Hãy nhập lại.")
            continue
        break
    except ValueError:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mSai định dạng! Vui lòng nhập số.")

# Delete Authorization if option 2 is selected
if choose == 2:
    for file in ["Authorization.txt"]:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(Fore.GREEN + f"[✔] Đã xóa {file}!")
            except Exception as e:
                print(Fore.RED + f"[✖] Không thể xóa {file}! Lý do: ")
    print(Fore.YELLOW + "👉 Vui lòng nhập lại thông tin!")

# Create Authorization file if it doesn't exist
for file in ["Authorization.txt"]:
    try:
        if not os.path.exists(file):
            open(file, "x").close()
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi tạo file {file}: ")

# Read Authorization
author = ""
if os.path.exists("Authorization.txt"):
    try:
        with open("Authorization.txt", "r") as f:
            author = f.read().strip()
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi đọc file Authorization.txt: ")

while not author:
    print(f"\033[1;35m═══════════════════════════════════════════════════════════════════")
    author = input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập Authorization : ").strip()
    try:
        with open("Authorization.txt", "w") as f:
            f.write(author)
    except Exception as e:
        print(Fore.RED + f"[✖] Lỗi khi ghi file Authorization.txt: ")
        sys.exit()

# Set headers
headers = {
    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
    'Referer': 'https://app.golike.net/',
    'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'T': 'VFZSak1FNUVTVEZOYWtGM1RrRTlQUT09',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    "Authorization": author,
    'Content-Type': 'application/json;charset=utf-8'
}

print(f"\033[1;35m═══════════════════════════════════════════════════════════════════")
print(Fore.GREEN + "🚀 Đăng nhập thành công! Đang vào Tool TikTok...")
time.sleep(1)

# Fetch TikTok account list
chontk_TikTok = chonacc()
if not chontk_TikTok:
    print(Fore.RED + "[✖] Không thể lấy danh sách tài khoản TikTok!")
    sys.exit()

# Display TikTok account list
dsacc(chontk_TikTok)

# Select TikTok account
account_found = 0
while True:
    idacc = input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập \033[1;31mID Acc TikTok \033[1;35mlàm việc: ").strip()
    for i in range(len(chontk_TikTok["data"])):
        if chontk_TikTok["data"][i]["unique_username"] == idacc:
            account_found = 1
            account_id = chontk_TikTok["data"][i]["id"]
            break
    if account_found == 0:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mAcc này chưa được thêm vào Golike hoặc ID sai")
        continue
    break

# Input job delay
while True:
    try:
        delay = int(input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập thời gian làm job: "))
        break
    except ValueError:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mSai định dạng!!!")

# Retry payment if first attempt fails
while True:
    lannhan = input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhận tiền lần 2 nếu lần 1 fail? (y/n): ").strip().lower()
    if lannhan not in ["y", "n"]:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mNhập sai, hãy nhập lại (y/n)!!!")
        continue
    break

# Input number of successful jobs to switch account
while True:
    try:
        doiacc_success = int(input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mSố job thành công để đổi acc TikTok (nhập 1 nếu không muốn đổi): "))
        if doiacc_success < 1:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mSố job phải lớn hơn 0!!!")
            continue
        break
    except ValueError:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mNhập vào một số!!!")

# Input number of failed jobs to switch account
while True:
    try:
        doiacc = int(input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mSố job fail để đổi acc TikTok (nhập 1 nếu không muốn đổi): "))
        if doiacc < 1:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mSố job phải lớn hơn 0!!!")
            continue
        break
    except ValueError:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mNhập vào một số!!!")

# Select link opening method
while True:
    try:
        print(f"\033[1;35m════════════════════════════════════════════════════════════════════")
        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập 1 : \033[1;33mMở link Tiktok thường")
        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập 2 : \033[1;33mMở link Tiktok Studio")
        print(f"\033[1;35m════════════════════════════════════════════════════════════════════")
        check_molink = int(input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;34mChọn lựa chọn: "))
        if check_molink not in [1, 2]:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mChỉ được nhập 1 hoặc 2!")
            continue
        break
    except ValueError:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mNhập vào một số!!!")

# Select task mode
while True:
    try:
        print(f"\033[1;35m════════════════════════════════════════════════════════════════════")
        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập 1 : \033[1;33mChỉ nhận nhiệm vụ Follow")
        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập 2 : \033[1;33mChỉ nhận nhiệm vụ Like")
        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mNhập 12 : \033[1;33mKết hợp cả Like và Follow")
        print(f"\033[1;35m════════════════════════════════════════════════════════════════════")
        chedo = int(input("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;34mChọn lựa chọn: "))
        if chedo not in [1, 2, 12]:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mChỉ được nhập 1, 2 hoặc 12!")
            continue
        break
    except ValueError:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mNhập vào một số!!!")

# Determine task types
lam = []
if chedo == 1:
    lam = ["follow"]
elif chedo == 2:
    lam = ["like"]
elif chedo == 12:
    lam = ["follow", "like"]

# Initialize variables
dem = 0
tong = 0
success_count = 0
checkdoiacc = 0
previous_job = None
bang_nhan_tien = []

# Main loop
while True:
    check_adb()
    # Check if failed jobs limit reached
    if checkdoiacc >= doiacc:
        dsacc(chontk_TikTok)
        idacc = input(f"\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mJob fail đã đạt giới hạn ({checkdoiacc}/{doiacc}), nhập ID acc khác để đổi: ").strip()
        account_found = 0
        for i in range(len(chontk_TikTok["data"])):
            if chontk_TikTok["data"][i]["unique_username"] == idacc:
                account_found = 1
                account_id = chontk_TikTok["data"][i]["id"]
                break
        if account_found == 0:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;31mAcc chưa thêm vào Golike hoặc ID không đúng!")
            continue
        checkdoiacc = 0
        success_count = 0
        hien_thi_ui()

    # Check if successful jobs limit reached
    if doiacc_success != 1 and success_count >= doiacc_success:
        dsacc(chontk_TikTok)
        idacc = input(f"\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mĐã đạt {success_count}/{doiacc_success} job thành công, nhập ID acc khác để đổi: ").strip()
        account_found = 0
        for i in range(len(chontk_TikTok["data"])):
            if chontk_TikTok["data"][i]["unique_username"] == idacc:
                account_found = 1
                account_id = chontk_TikTok["data"][i]["id"]
                break
        if account_found == 0:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;31mAcc chưa thêm vào Golike hoặc ID không đúng!")
            continue
        checkdoiacc = 0
        success_count = 0
        hien_thi_ui()

    print("                                     ", end="\r")
    print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mĐang làm nhiệm vụ :))", end="\r")
    nhanjob = nhannv(account_id)
    if not nhanjob:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mKhông nhận được nhiệm vụ, thử lại sau 10s...")
        time.sleep(10)
        continue

    if "data" not in nhanjob or "link" not in nhanjob["data"] or not nhanjob["data"]["link"]:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mHết nhiệm vụ - Không có link!        \r", end="")
        time.sleep(10)
        try:
            baoloi(nhanjob["data"]["id"], nhanjob["data"]["object_id"], account_id, nhanjob["data"]["type"])
        except:
            pass
        continue

    if nhanjob.get("status") == 200:
        ads_id = nhanjob["data"]["id"]
        link = nhanjob["data"]["link"]
        object_id = nhanjob["data"]["object_id"]
        loai = nhanjob["data"]["type"]

        # Check for duplicate job
        if previous_job and previous_job["data"]["link"] == link and previous_job["data"]["type"] == loai:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mJob trùng với job trước đó - Bỏ qua!        \r", end="")
            time.sleep(2)
            try:
                baoloi(ads_id, object_id, account_id, loai)
            except:
                pass
            continue

        previous_job = nhanjob

        if loai not in lam:
            try:
                baoloi(ads_id, object_id, account_id, loai)
                print(f"\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mĐang bỏ qua job {loai}", end="\r")
                time.sleep(1)
                continue
            except:
                pass

        if loai == "follow":
            try:
                if check_molink == 1:
                    d.shell(f"am start -a android.intent.action.VIEW -d {link}")
                    time.sleep(5)
                    if d.xpath('//*[contains(@text, "Đây là tài khoản riêng tư")]').exists:
                        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mTài khoản riêng tư, bỏ qua job:>        ", end="\r")
                        baoloi(ads_id, object_id, account_id, loai)
                        d.press("back")
                        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mTrở về:>        ", end="\r")
                        time.sleep(2)
                        continue
                    # Follow
                    if d(text="Follow").exists:
                        d(text="Follow").click()
                        time.sleep(random.uniform(2, 4))
                        w, h = d.window_size()
                        d.swipe(w//2, int(h*0.2), w//2, int(h*0.8))
                        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mCheck Follow:>        ", end="\r")
                        time.sleep(3)

                    try:
                        d.press("Back")   # Chỉ cần gọi là được
                        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mTrở về:>        ", end="\r")
                        time.sleep(2)
                    except Exception as e:
                        print(Fore.RED + f"[✖] Lỗi khi thực hiện follow ")
                else:
                    user_id = get_user_id(link)
                    if user_id:
                        # Mở profile bằng deep link
                        d.shell(f'am start -n com.ss.android.tt.creator/com.ss.android.ugc.aweme.deeplink.DeepLinkActivityV2 '
                                f'-a android.intent.action.VIEW -d "aweme://user/profile/{user_id}"')
                        time.sleep(5)
                        if d.xpath('//*[contains(@text, "Đây là tài khoản riêng tư")]').exists:
                            print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mTài khoản riêng tư, bỏ qua job:>        ", end="\r")
                            baoloi(ads_id, object_id, account_id, loai)
                            d.press("back")
                            print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mTrở về:>        ", end="\r")
                            time.sleep(2)
                            continue
                        # Follow
                        if d(text="Follow").exists:
                            d(text="Follow").click()
                            time.sleep(random.uniform(2, 4))
                            w, h = d.window_size()
                            d.swipe(w//2, int(h*0.2), w//2, int(h*0.8))
                            print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mCheck Follow:>        ", end="\r")
                            time.sleep(3)

                        try:
                            d.press("back")   # Chỉ cần gọi là được
                            print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mTrở về:>        ", end="\r")
                            time.sleep(2)
                        except Exception as e:
                            print(Fore.RED + f"[✖] Lỗi khi thực hiện follow ")

                    else:
                        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mKhông thể mở profile của {link}        ", end="\r")
                        baoloi(ads_id, object_id, account_id, loai)
                        checkdoiacc += 1
                        continue
            except UiObjectNotFoundError as e:
                print(Fore.RED + f"[✖] Lỗi khi thực hiện follow, bỏ qua job! ")
                baoloi(ads_id, object_id, account_id, loai)
                checkdoiacc += 1
                continue
            except Exception as e:
                print(Fore.RED + f"[✖] Lỗi không xác định khi thực hiện follow, bỏ qua job! ")
                baoloi(ads_id, object_id, account_id, loai)
                checkdoiacc += 1
                continue

        elif loai == "like":
            try:
                d.shell(f"am start -a android.intent.action.VIEW -d {link}")
                time.sleep(random.uniform(2, 4))
                like_button = d(resourceId="com.zhiliaoapp.musically:id/cnv")
                if like_button.wait(timeout=5):
                    like_button.click()
                    time.sleep(random.uniform(1, 2))
                else:
                    raise UiObjectNotFoundError("Không tìm thấy nút like")
            except UiObjectNotFoundError as e:
                print(Fore.RED + f"[✖] Lỗi khi thực hiện like: ")
                baoloi(ads_id, object_id, account_id, loai)
                checkdoiacc += 1
                continue
            except Exception as e:
                print(Fore.RED + f"[✖] Lỗi không xác định khi thực hiện like: ")
                baoloi(ads_id, object_id, account_id, loai)
                checkdoiacc += 1
                continue

        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mĐang fake ip chống block:>        ", end="\r")
        time.sleep(3)

        for remaining_time in range(delay, -1, -1):
            colors = [
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;37mH\033[1;36mu\033[1;35mo\033[1;32mn\033[1;31mg \033[1;34mD\033[1;33me\033[1;36mv\033[1;36m🍉 - Tool\033[1;36m Vip \033[1;31m\033[1;32m",
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;34mH\033[1;31mu\033[1;37mo\033[1;36mn\033[1;32mg \033[1;35mD\033[1;37me\033[1;33mv\033[1;32m🍉 - Tool\033[1;34m Vip \033[1;31m\033[1;32m",
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mH\033[1;37mu\033[1;36mo\033[1;33mn\033[1;35mg \033[1;32mD\033[1;34me\033[1;35mv\033[1;37m🍉 - Tool\033[1;33m Vip \033[1;31m\033[1;32m",
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;32mH\033[1;33mu\033[1;34mo\033[1;35mn\033[1;36mg \033[1;37mD\033[1;36me\033[1;31mv\033[1;34m🍉 - Tool\033[1;31m Vip \033[1;31m\033[1;32m",
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;37mH\033[1;34mu\033[1;35mo\033[1;36mn\033[1;32mg \033[1;33mD\033[1;31me\033[1;37mv\033[1;34m🍉 - Tool\033[1;37m Vip \033[1;31m\033[1;32m",
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;34mH\033[1;33mu\033[1;37mo\033[1;35mn\033[1;31mg \033[1;36mD\033[1;36me\033[1;32mv\033[1;37m🍉 - Tool\033[1;36m Vip \033[1;31m\033[1;32m",
                "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;36mH\033[1;35mu\033[1;31mo\033[1;34mn\033[1;37mg \033[1;35mD\033[1;32me\033[1;36mv\033[1;33m🍉 - Tool\033[1;33m Vip \033[1;31m\033[1;32m",
            ]
            for color in colors:
                print(f"\r{color}|{remaining_time}|", end="")
                time.sleep(0.12)

        print("\r                          \r", end="")
        print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mĐang Nhận Tiền Lần 1:>        ", end="\r")
        nhantien = hoanthanh(ads_id, account_id)
        if not nhantien:
            print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mLỗi khi nhận tiền lần 1!")
            try:
                baoloi(ads_id, object_id, account_id, loai)
            except:
                pass
            checkdoiacc += 1
            continue

        checklan = 1 if lannhan == "y" else 2
        while checklan <= 2:
            if nhantien and nhantien.get("status") == 200:
                dem += 1
                success_count += 1
                tien = nhantien["data"].get("prices", 0)
                tong += tien
                local_time = time.strftime("%H:%M:%S")

                # Update table
                if bang_nhan_tien:
                    bang_nhan_tien.pop()
                bang_nhan_tien.append([
                    f"\033[1;36m{dem}",
                    f"\033[1;33m{local_time}",
                    f"\033[1;32msuccess",
                    f"\033[1;35m{loai}",
                    f"\033[1;91m+{tien} \033[1;93m({tong})"
                ])

                hien_thi_ui()
                checkdoiacc = 0
                break
            else:
                checklan += 1
                if checklan > 2:
                    baoloi(ads_id, object_id, account_id, loai)
                    checkdoiacc += 1
                    display_temp_message("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mBỏ qua job!")
                    time.sleep(1)
                    break
                print("\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;35mĐang Nhận Tiền Lần 2:>        ", end="\r")
                nhantien = hoanthanh(ads_id, account_id)
    else:
        print(Fore.RED + "\033[1;97m[\033[1;91m❣\033[1;97m] \033[1;36m✈ \033[1;31mLỗi khi nhận nhiệm vụ, bỏ qua job...")
        continue
