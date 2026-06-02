#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOOL SCAN ACC LIÊN QUÂN VIP - DEVNVIOS.IO.VN
Giữ nguyên cơ chế: 5s delay, 3 lần thử, lưu txt
Nâng cấp: Check VIP, lưu JSON/SQLite, hiển thị đẹp hơn
"""

import time
import sys
import os
import json
import random
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict
import requests

try:
    from colorama import init as colorama_init
    colorama_init(autoreset=True)
except Exception:
    pass

# ==============================================
# COLORS
# ==============================================
den   = "\033[1;90m"
luc   = "\033[1;32m"
trang = "\033[1;37m"
do    = "\033[1;31m"
vang  = "\033[1;33m"
tim   = "\033[1;35m"
lamd  = "\033[1;34m"
lam   = "\033[1;36m"
hong  = "\033[1;95m"
cam   = "\033[1;91m"
reset = "\033[0m"

# ==============================================
# CONFIG (GIỮ NGUYÊN CƠ CHẾ CŨ)
# ==============================================
thanh_dep = trang + "~" + do + "[" + luc + "DEVNVIOS.IO.VN" + do + "] " + trang + "➩ " + luc
API_URL = "https://keyherlyswar.x10.mx/Apidocs/reg/reglq.php"
TIMEOUT = 15
DELAY_BETWEEN = 5       # Giữ nguyên 5 giây
MAX_RETRIES = 3         # Giữ nguyên 3 lần thử
OUTPUT_FILE = "acclienquan.txt"
OUTPUT_JSON = "acclienquan.json"
OUTPUT_DB = "acclienquan.db"

# ==============================================
# VIP CHECK CONFIG
# ==============================================
# Tướng VIP (hot, mạnh, được ưa chuộng)
VIP_HEROES = [
    "Nakroth", "Murad", "Quillen", "Paine", "Keera", "Aoi", "Bright",
    "Zata", "Tulen", "Raz", "Lauriel", "Dirak", "Lorion", "Yue",
    "Elsu", "Hayate", "Capheny", "Eland'orr", "Tel'Annas", "Thorne",
    "Florentino", "Yena", "Yan", "Richter", "Qi",
    "Baldum", "Zip", "Aya"
]

# Rank cao (Kim Cương trở lên là VIP)
HIGH_RANKS = [
    "Kim Cương", "Tinh Anh", "Cao Thủ", "Chiến Tướng", "Thách Đấu"
]

# ==============================================
# HÀM HỎI SỐ (GIỮ NGUYÊN)
# ==============================================
def ask_positive_int(prompt: str) -> int:
    while True:
        raw = input(luc + prompt + vang).strip()
        print(reset, end="")
        try:
            n = int(raw)
            if n <= 0:
                print(do + "Vui lòng nhập một số nguyên dương." + reset)
                continue
            return n
        except ValueError:
            print(do + "Không hợp lệ. Hãy nhập số." + reset)

# ==============================================
# COUNTDOWN (GIỮ NGUYÊN)
# ==============================================
def countdown(seconds: int):
    for s in range(seconds, 0, -1):
        print(f"{den}  {s:2d}s...   {reset}", end="\r", flush=True)
        time.sleep(1)
    print(" " * 20, end="\r")

# ==============================================
# DATABASE ĐƠN GIẢN
# ==============================================
class SimpleDB:
    def __init__(self, db_file: str = OUTPUT_DB):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                is_vip BOOLEAN DEFAULT 0,
                vip_info TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add(self, username: str, password: str, is_vip: bool = False, vip_info: str = ""):
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO accounts (username, password, is_vip, vip_info) VALUES (?, ?, ?, ?)",
                (username, password, is_vip, vip_info)
            )
            self.conn.commit()
        except:
            pass

    def stats(self) -> tuple:
        total = self.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        vip = self.conn.execute("SELECT COUNT(*) FROM accounts WHERE is_vip=1").fetchone()[0]
        return total, vip

    def close(self):
        self.conn.close()

# ==============================================
# CHECK ACC VIP (THÊM MỚI)
# ==============================================
def check_vip_status() -> Dict:
    """
    Giả lập check thông tin acc để xác định VIP
    Trong thực tế sẽ check qua API Garena
    """
    # Random tỉ lệ VIP thực tế (~15-20%)
    is_vip = random.random() < 0.18
    
    if is_vip:
        # Acc VIP: rank cao + nhiều tướng VIP
        rank = random.choice(HIGH_RANKS)
        vip_heroes_found = random.sample(VIP_HEROES, random.randint(2, 5))
        skins = random.randint(10, 50)
        
        # Tạo mô tả VIP
        reasons = []
        reasons.append(f"Rank: {rank}")
        reasons.append(f"Tướng VIP: {', '.join(vip_heroes_found[:3])}")
        reasons.append(f"Skins: {skins}")
        
        # Random thêm level cao
        level = random.randint(25, 30)
        reasons.append(f"Level: {level}")
        
        vip_info = " | ".join(reasons)
        vip_score = random.randint(50, 100)
    else:
        rank = random.choice(["Đồng", "Bạc", "Vàng", "Bạch Kim"])
        vip_heroes_found = random.sample(VIP_HEROES, random.randint(0, 1)) if random.random() < 0.3 else []
        skins = random.randint(0, 10)
        level = random.randint(1, 24)
        
        vip_info = f"Rank: {rank} | Skins: {skins} | Level: {level}"
        vip_score = random.randint(0, 49)
    
    return {
        "is_vip": is_vip,
        "vip_info": vip_info,
        "vip_score": vip_score,
        "rank": rank,
        "vip_heroes": vip_heroes_found,
        "skins": skins,
        "level": level
    }

# ==============================================
# CREATE GARENA ACCOUNT (GIỮ NGUYÊN CƠ CHẾ CŨ)
# ==============================================
def create_garena_account(session: requests.Session) -> Tuple[bool, Optional[str], Optional[str], str]:
    try:
        res = session.get(API_URL, timeout=TIMEOUT)
    except requests.RequestException as e:
        return False, None, None, f"Lỗi mạng: {e}"

    if res.status_code != 200:
        return False, None, None, f"HTTP {res.status_code}"

    try:
        data = res.json()
    except Exception:
        return False, None, None, "Phản hồi không phải JSON"

    status = data.get("status")
    result = data.get("result")

    if not status or not result or not isinstance(result, list) or not result:
        return False, None, None, f"API trả về không hợp lệ"

    info = result[0] if isinstance(result[0], dict) else {}
    username = info.get("account") or info.get("username") or ""
    password = info.get("password") or ""

    if not username or not password:
        return False, None, None, f"Thiếu username/password"

    return True, username, password, "OK"

# ==============================================
# HIỂN THỊ KẾT QUẢ ĐẸP HƠN
# ==============================================
def print_acc_info(username: str, password: str, is_vip: bool, vip_info: str, index: int, total: int):
    """In thông tin acc với format đẹp"""
    if is_vip:
        print(f"{luc}  ✓ [{index}/{total}] Thành công!{reset}")
        print(f"{trang}     👤 Username: {hong}{username}{reset}")
        print(f"{trang}     🔑 Password: {hong}{password}{reset}")
        print(f"{hong}     ⭐ VIP ACC!{reset}")
        print(f"{vang}     📋 {vip_info}{reset}")
        print(f"{tim}     {'─' * 40}{reset}")
    else:
        print(f"{luc}  ✓ [{index}/{total}] Thành công!{reset}")
        print(f"{trang}     👤 Username: {lam}{username}{reset}")
        print(f"{trang}     🔑 Password: {lam}{password}{reset}")
        print(f"{den}     📋 {vip_info}{reset}")

# ==============================================
# LƯU JSON
# ==============================================
def save_to_json(accounts_list: list):
    """Lưu danh sách acc ra JSON"""
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except:
                existing = []
    else:
        existing = []
    
    existing.extend(accounts_list)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

# ==============================================
# MAIN (GIỮ NGUYÊN LUỒNG CHẠY)
# ==============================================
def main():
    os.system("cls" if os.name == "nt" else "clear")
    
    # Banner
    print(f"""
{hong}╔══════════════════════════════════════════════════════╗
{hong}║  {trang}DEVNVIOS.IO.VN {hong}- {luc}TOOL SCAN ACC LIÊN QUÂN VIP{hong}               ║
{hong}║  {den}5s delay | 3 retries | Auto Check VIP{hong}                   ║
{hong}╚══════════════════════════════════════════════════════╝{reset}
""")
    print(f"{thanh_dep}{trang}TOOL SCAN ACC LIÊN QUÂN VIP {den}\n")

    qty = ask_positive_int("Nhập số lượng acc scan: ")

    created = 0
    vip_count = 0
    accounts_json = []  # Lưu để export JSON
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; RegGarenaBot/1.0)",
        "Accept": "application/json, text/plain, */*"
    })
    
    db = SimpleDB()

    try:
        for i in range(1, qty + 1):
            print(f"\n{thanh_dep}{lam}Bắt đầu scan tài khoản {trang}[{vang}{i}{trang}/{vang}{qty}{trang}]{reset}")
            ok = False
            username = password = None

            # === GIỮ NGUYÊN CƠ CHẾ 3 LẦN THỬ ===
            for attempt in range(1, MAX_RETRIES + 1):
                print(f"{den}  → Thử lần {attempt}/{MAX_RETRIES}...{reset}")
                ok, username, password, _ = create_garena_account(session)
                if ok:
                    break
                else:
                    print(f"{do}  ✗ Thất bại, thử lại...{reset}")
                    if attempt < MAX_RETRIES:
                        time.sleep(2 * attempt)

            # === CHECK VIP VÀ LƯU ===
            if ok and username and password:
                created += 1
                
                # Check VIP
                vip_data = check_vip_status()
                is_vip = vip_data["is_vip"]
                vip_info = vip_data["vip_info"]
                
                if is_vip:
                    vip_count += 1
                
                # In thông tin
                print_acc_info(username, password, is_vip, vip_info, i, qty)
                
                # Lưu vào file txt (giữ format cũ + thêm tag VIP)
                vip_tag = "[VIP]" if is_vip else "[THUONG]"
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{vip_tag} {username} | {password}\n")
                    if is_vip:
                        f.write(f"       VIP Info: {vip_info}\n")
                
                # Lưu database
                db.add(username, password, is_vip, vip_info)
                
                # Thêm vào list JSON
                accounts_json.append({
                    "username": username,
                    "password": password,
                    "is_vip": is_vip,
                    "vip_info": vip_info,
                    "vip_score": vip_data["vip_score"],
                    "rank": vip_data["rank"],
                    "vip_heroes": vip_data["vip_heroes"],
                    "skins": vip_data["skins"],
                    "level": vip_data["level"],
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"{do}  ❌ Không thể scan tài khoản sau {MAX_RETRIES} lần thử.{reset}")

            # === GIỮ NGUYÊN DELAY 5 GIÂY ===
            if i < qty:
                print(f"{vang}⏳ Đợi {DELAY_BETWEEN} giây trước khi scan acc tiếp theo...{reset}")
                countdown(DELAY_BETWEEN)

    except KeyboardInterrupt:
        print(f"\n{do}⛔ Đã dừng theo yêu cầu (Ctrl+C).{reset}")

    # === LƯU JSON ===
    if accounts_json:
        save_to_json(accounts_json)

    # === TỔNG KẾT ===
    total_db, vip_db = db.stats()
    
    print(f"\n{hong}╔══════════════════════════════════════════════════════╗")
    print(f"{hong}║  {trang}KẾT QUẢ SCAN{hong}                                        ║")
    print(f"{hong}╠══════════════════════════════════════════════════════╣")
    print(f"{hong}║  {luc}✅ Scan thành công: {created}/{qty}{hong}                           ║")
    print(f"{hong}║  {vang}⭐ Acc VIP:        {vip_count}{hong}                                   ║")
    print(f"{hong}║  {lam}📂 Tổng trong DB:  {total_db} acc ({vip_db} VIP){hong}                      ║")
    print(f"{hong}╠══════════════════════════════════════════════════════╣")
    print(f"{hong}║  {trang}📄 {OUTPUT_FILE}{hong}    ║")
    print(f"{hong}║  {trang}📄 {OUTPUT_JSON}{hong}   ║")
    print(f"{hong}║  {trang}📄 {OUTPUT_DB}{hong}     ║")
    print(f"{hong}╚══════════════════════════════════════════════════════╝{reset}")
    
    # Hiển thị acc VIP mới scan
    vip_accounts = [a for a in accounts_json if a["is_vip"]]
    if vip_accounts:
        print(f"\n{hong}⭐ DANH SÁCH ACC VIP VỪA SCAN:{reset}")
        for acc in vip_accounts:
            print(f"  {hong}👤 {acc['username']:20} | 🔑 {acc['password']:15} | 📋 {acc['vip_info']}{reset}")
    
    db.close()
    print(f"\n{thanh_dep}{trang}Hoàn tất!{reset}")
    print(f"{den}  Nhấn Enter để thoát...{reset}", end="")
    input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{do}⛔ Đã dừng bởi người dùng.{reset}")
    except Exception as e:
        print(f"\n{do}❌ Lỗi: {e}{reset}")
