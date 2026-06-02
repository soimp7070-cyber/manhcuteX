import base64
import json
import os
import platform
import random
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from time import sleep

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import requests
except ImportError:
    print('Đang cài đặt thư viện...')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "colorama"])
    print('Cài đặt hoàn tất. Vui lòng chạy lại tool.')
    sys.exit()

# ===================== MÀU SẮC =====================
xnhac = "\033[1;36m"
do = "\033[1;31m"
luc = "\033[1;32m"
vang = "\033[1;33m"
xduong = "\033[1;34m"
hong = "\033[1;35m"
trang = "\033[1;39m"
xanh = "\033[1;36m"
end = '\033[0m'

# ===================== QUẢN LÝ PROXY (mã hóa base64) =====================
PROXY_FILE = "proxies.enc"

def encode_proxy(proxy_str: str) -> str:
    return base64.b64encode(proxy_str.encode()).decode()

def decode_proxy(encoded: str) -> str:
    return base64.b64decode(encoded.encode()).decode()

def load_proxies():
    if not os.path.exists(PROXY_FILE):
        return []
    try:
        with open(PROXY_FILE, 'r') as f:
            lines = f.readlines()
        return [decode_proxy(line.strip()) for line in lines if line.strip()]
    except:
        return []

def save_proxies(proxies):
    with open(PROXY_FILE, 'w') as f:
        f.write('\n'.join([encode_proxy(p) for p in proxies]))

def add_proxy(proxy_str: str):
    pattern = r'^([\d\.]+|\w+):(\d+):(.+):(.+)$'
    if not re.match(pattern, proxy_str):
        print(f"{do}Định dạng sai! Phải là ip:port:taikhoan:matkhau{end}")
        return False
    proxies = load_proxies()
    if proxy_str in proxies:
        print(f"{vang}Proxy đã tồn tại.{end}")
        return False
    proxies.append(proxy_str)
    save_proxies(proxies)
    print(f"{luc}Đã thêm proxy (mã hóa).{end}")
    return True

def list_proxies():
    proxies = load_proxies()
    if not proxies:
        print(f"{vang}Chưa có proxy.{end}")
        return
    print(f"\n{trang}{'='*50}{end}")
    for idx, p in enumerate(proxies, 1):
        parts = p.split(':')
        if len(parts) >= 4:
            print(f"{luc}[{idx}]{end} {xnhac}{parts[0]}:{parts[1]}{end} | {vang}{parts[2]}{end} | {do}{'*'*len(parts[3])}{end}")
        else:
            print(f"{do}[{idx}] {p}{end}")
    print(f"{trang}{'='*50}{end}")

def delete_proxy(index: int):
    proxies = load_proxies()
    if not proxies or not (1 <= index <= len(proxies)):
        print(f"{do}Số thứ tự không hợp lệ.{end}")
        return False
    removed = proxies.pop(index-1)
    save_proxies(proxies)
    print(f"{luc}Đã xóa {removed}{end}")
    return True

def check_single_proxy(proxy_str: str, timeout=15):
    try:
        ip, port, user, pwd = proxy_str.split(':')
        proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
        proxies = {"http": proxy_url, "https": proxy_url}
        test_urls = [("http://httpbin.org/ip","http"), ("https://httpbin.org/ip","https")]
        best = None
        for url, proto in test_urls:
            try:
                start = time.time()
                r = requests.get(url, proxies=proxies, timeout=timeout)
                elapsed = (time.time()-start)*1000
                if r.status_code == 200:
                    ip_pub = r.json().get('origin', 'Unknown')
                    if best is None or elapsed < best[0]:
                        best = (elapsed, ip_pub, proto)
            except:
                continue
        if best:
            return True, round(best[0],2), f"IP: {best[1]}", best[2], best[1]
        return False, 0, "Không kết nối được", None, None
    except:
        return False, 0, "Lỗi định dạng", None, None

def check_all_proxies():
    proxies = load_proxies()
    if not proxies:
        print(f"{vang}Không có proxy nào.{end}")
        return
    print(f"\n{trang}{'='*60}{end}")
    print(f"{hong}🔍 Kiểm tra {len(proxies)} proxy (HTTP/HTTPS)...{end}")
    live = []
    dead = []
    for i, p in enumerate(proxies,1):
        short = p.split(':')[0]+':'+p.split(':')[1]
        print(f"[{i}/{len(proxies)}] {short}...", end=' ')
        ok, lat, info, proto, _ = check_single_proxy(p)
        if ok:
            print(f"{luc}✓ LIVE {lat}ms [{proto.upper()}] - {info}{end}")
            live.append((short, lat, info, proto))
        else:
            print(f"{do}✗ DIE - {info}{end}")
            dead.append(short)
        time.sleep(0.2)
    print(f"{trang}{'='*60}{end}")
    print(f"{luc}✅ Live: {len(live)}{end}")
    for s,lat,ip,proto in live:
        print(f"   {xnhac}{s}{end} - {lat}ms [{proto.upper()}] - {ip}")
    print(f"{do}❌ Die: {len(dead)}{end}")
    for s in dead:
        print(f"   {do}{s}{end}")
    print(f"{trang}{'='*60}{end}")

def proxy_menu():
    while True:
        print(f"\n{trang}{'═'*50}{end}")
        print(f"{hong}📡 QUẢN LÝ PROXY{end}")
        print(f"{trang}1. Thêm proxy (ip:port:user:pass){end}")
        print(f"{trang}2. Xem danh sách{end}")
        print(f"{trang}3. Xóa proxy{end}")
        print(f"{trang}4. Kiểm tra một proxy{end}")
        print(f"{trang}5. Kiểm tra tất cả{end}")
        print(f"{trang}6. Bắt đầu tool chính{end}")
        choice = input(f"{luc}Chọn: {trang}")
        if choice == '1':
            p = input(f"{vang}Nhập proxy: {trang}")
            add_proxy(p)
        elif choice == '2':
            list_proxies()
        elif choice == '3':
            list_proxies()
            try:
                idx = int(input(f"{vang}Số thứ tự cần xóa: {trang}"))
                delete_proxy(idx)
            except:
                print(f"{do}Số không hợp lệ.{end}")
        elif choice == '4':
            p = input(f"{vang}Nhập proxy: {trang}")
            ok, lat, info, proto, _ = check_single_proxy(p)
            if ok:
                print(f"{luc}✓ LIVE - {lat}ms [{proto.upper()}] - {info}{end}")
            else:
                print(f"{do}✗ DIE - {info}{end}")
        elif choice == '5':
            check_all_proxies()
        elif choice == '6':
            break
        input(f"{xnhac}Nhấn Enter...{end}")

# ===================== BANNER =====================
def authentication_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner_text = f"""
{xanh}██╗  ██╗ {luc}███╗   ███╗ {trang}██╗  ██╗
{xanh}██║  ██║ {luc}████╗ ████║ {trang}██║ ██╔╝
{xanh}███████║ {luc}██╔████╔██║ {trang}█████╔╝
{trang}██╔══██║ {luc}██║╚██╔╝██║ {xanh}██╔═██╗
{trang}██║  ██║ {luc}██║ ╚═╝ ██║ {xanh}██║  ██╗
{trang}╚═╝  ╚═╝ {luc}╚═╝     ╚═╝ {xanh}╚═╝  ╚═╝

{trang}══════════════════════════

{luc}      Tool BUMX FB-HMK
{trang}      (No Key Required)

{trang}══════════════════════════
"""
    for char in banner_text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.0001)

# ===================== HÀM TIỆN ÍCH =====================
def prints(*args, **kwargs):
    r, g, b = 255, 255, 255
    text = "text"
    end = "\n"
    if len(args) == 1:
        text = args[0]
    elif len(args) >= 3:
        r, g, b = args[0], args[1], args[2]
        if len(args) >= 4:
            text = args[3]
    if "text" in kwargs:
        text = kwargs["text"]
    if "end" in kwargs:
        end = kwargs["end"]
    print(f"\033[38;2;{r};{g};{b}m{text}\033[0m", end=end)

def encode_to_base64(_data):
    return base64.b64encode(_data.encode()).decode()

def to_requests_proxies(proxy_str):
    if not proxy_str:
        return None
    p = proxy_str.strip().split(':')
    if len(p) == 4:
        try:
            host, port, user, past = p
            int(port)
        except ValueError:
            user, past, host, port = p
        return {
            'http':  f'http://{user}:{past}@{host}:{port}',
            'https': f'http://{user}:{past}@{host}:{port}',
        }
    if len(p) == 2:
        host, port = p
        return {
            'http':  f'http://{host}:{port}',
            'https': f'http://{host}:{port}',
        }
    return None

# ===================== KIỂM TRA COOKIE FACEBOOK =====================
def facebook_info(cookie: str, proxy: str = None, timeout: int = 15):
    result = {'success': False, 'user_id': None, 'message': '', 'session': None, 'lsd': '', 'fb_dtsg': '', 'jazoest': '', 'name': ''}
    cookie = cookie.strip()
    if not cookie:
        result['message'] = "Cookie rỗng"
        return result
    match_c_user = re.search(r'c_user\s*=\s*(\d+)', cookie)
    if not match_c_user:
        result['message'] = "Cookie thiếu 'c_user' (ID tài khoản)"
        return result
    user_id = match_c_user.group(1)
    if not re.search(r'xs\s*=', cookie):
        result['message'] = "Cookie thiếu 'xs' (token xác thực)"
        return result
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Cookie': cookie
    })
    if proxy:
        session.proxies = to_requests_proxies(proxy)
    try:
        resp = session.get('https://www.facebook.com/me', timeout=timeout, allow_redirects=True)
        final_url = resp.url
        if 'checkpoint' in final_url or 'login' in final_url or 'mbasic' in final_url or 'recover' in final_url:
            result['message'] = "Cookie hết hạn hoặc tài khoản bị checkpoint"
            return result
        user_match = re.search(r'/profile\.php\?id=(\d+)', final_url)
        if user_match:
            user_id = user_match.group(1)
        else:
            user_match2 = re.search(r'\"userID\":\"(\d+)\"', resp.text)
            if user_match2:
                user_id = user_match2.group(1)
        name_match = re.search(r'\"name\":\"(.*?)\"', resp.text)
        name = name_match.group(1) if name_match else user_id
        fb_dtsg = re.search(r'\["DTSGInitialData",\[\],\{"token":"(.*?)"\}', resp.text)
        lsd = re.search(r'"LSD",\[\],\{"token":"(.*?)"\}', resp.text)
        jazo = re.search(r'jazoest=(.*?)\"', resp.text)
        result['success'] = True
        result['user_id'] = user_id
        result['name'] = name
        result['session'] = session
        result['cookie'] = cookie
        result['fb_dtsg'] = fb_dtsg.group(1) if fb_dtsg else ''
        result['lsd'] = lsd.group(1) if lsd else ''
        result['jazoest'] = jazo.group(1) if jazo else ''
        result['message'] = "Cookie hợp lệ"
        return result
    except Exception as e:
        result['message'] = f"Lỗi kết nối: {str(e)[:50]}"
        return result

def check_cookie_valid(cookie, proxy=None):
    info = facebook_info(cookie, proxy)
    if info['success']:
        print(f"{luc}✓ Cookie hợp lệ - ID: {info['user_id']}{end}")
        return True
    else:
        print(f"{do}✗ Cookie không hợp lệ: {info['message']}{end}")
        return False

# ===================== API BUMX =====================
def wallet(authorization):
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    try:
        response = requests.get('https://api-v2.bumx.vn/api/business/wallet', headers=headers, timeout=10).json()
        return response.get('data', {}).get('balance', 'N/A')
    except:
        return "Error"

def load(session, authorization, job):
    prints(255,255,0,f'Đang mở nhiệm vụ...',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'buff_id': job['buff_id']}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/load-mission', headers=headers, json=json_data, timeout=10).json()
        return response
    except:
        prints(255,0,0,f'Lỗi khi tải thông tin NV')
        return None

def get_job(session, authorization, type_job=None):
    if type_job:
        prints(255,255,0,f'Đang lấy nhiệm vụ loại {type_job}...',end='\r')
    else:
        prints(255,255,0,f'Đang lấy tất cả nhiệm vụ...',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    params = {'is_from_mobile': 'true'}
    if type_job:
        params['type'] = type_job
    try:
        response = session.get('https://api-v2.bumx.vn/api/buff/mission', params=params, headers=headers, timeout=10)
        response.raise_for_status()
        response_json = response.json()
    except:
        prints(255,0,0,f'Lỗi khi lấy NV')
        return []
    job_count = response_json.get('count', 0)
    prints(Fore.LIGHTWHITE_EX+f"Đã tìm thấy {job_count} NV",end='\r')
    JOB=[]
    for i in response_json.get('data', []):
        json_job={
            "_id":i['_id'], "buff_id":i['buff_id'], "type":i['type'], "name":i['name'],
            "status":i['status'], "object_id":i['object_id'], "business_id":i['business_id'],
            "mission_id":i['mission_id'], "create_date":i['create_date'], "note":i['note'],
            "require":i['require'],
        }
        JOB.insert(0,json_job)
    return JOB

def reload(session, authorization, type_job, retries=3):
    prints(255, 255, 0, f'Đang tải danh sách nhiệm vụ {type_job}...', end='\r')
    if retries == 0:
        prints(255, 0, 0, f'Tải danh sách NV {type_job} thất bại.')
        return
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'type': type_job}
    try:
        session.post('https://api-v2.bumx.vn/api/buff/get-new-mission', headers=headers, json=json_data, timeout=10).json()
    except Exception:
        prints(255, 0, 0, f'Lỗi khi tải lại NV. Thử lại...')
        time.sleep(2)
        return reload(session, authorization, type_job, retries - 1)

def submit(session, authorization, job, reslamjob, res_load):
    prints(255,255,0,f'Đang hoàn thành nhiệm vụ',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {
        'buff_id': job['buff_id'], 'comment': None, 'comment_id': None, 'code_submit': None,
        'attachments': [], 'link_share': '', 'code': '', 'is_from_mobile': True,
        'type': job['type'], 'sub_id': None, 'data': None,
    }
    if job['type']=='like_facebook':
        json_data['comment'] = 'tt nha'
    elif job['type']=='like_poster':
        json_data['comment'] = res_load.get('data')
        json_data['comment_id'] = res_load.get('comment_id')
    elif job['type']=='review_facebook':
        json_data['comment'] = 'Helo Bạn chúc Bạn sức khỏe '
        json_data['link_share'] = reslamjob
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/submit-mission', headers=headers, json=json_data, timeout=10).json()
        if response.get('success') == True:
            message = response.get('message', '')
            _xu = '0'
            sonvdalam = '0'
            try:
                _xu = message.split('cộng ')[1].split(',')[0]
                sonvdalam = message.split('làm: ')[1]
            except IndexError:
                pass
            return [True, _xu, sonvdalam]
        return [False, '0', '0']
    except Exception:
        prints(255,0,0,f'Lỗi khi submit')
        return [False, '0', '0']

def report(session, authorization, job, retries=3):
    prints(255, 255, 0, f'Đang báo lỗi...', end='\r')
    if retries == 0:
        prints(255, 0, 0, f'Báo lỗi thất bại.')
        return
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)',
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'buff_id': job['buff_id']}
    try:
        session.post('https://api-v2.bumx.vn/api/buff/report-buff', headers=headers, json=json_data, timeout=10)
        prints(255, 165, 0, 'Đã báo lỗi thành công và bỏ qua NV.')
    except Exception:
        time.sleep(2)
        return report(session, authorization, job, retries - 1)

def add_account_fb(session, authorization, user_id):
    headers = {
        'Content-Type': 'application/json',
        'lang': 'en',
        'version': '37',
        'origin': 'app',
        'authorization': authorization,
    }
    json_data = {'link': f'https://www.facebook.com/profile.php?id={str(user_id)}'}
    try:
        response = session.post('https://api-v2.bumx.vn/api/account-facebook/connect-link', headers=headers, json=json_data, timeout=10).json()
        prints(255,255,0,f"Khai báo tài khoản FB: {response.get('message', 'No message')}")
    except Exception as e:
        prints(255,0,0,f"Lỗi khai báo tài khoản FB: {e}")

# ===================== CÁC HÀM TƯƠNG TÁC FACEBOOK =====================
def get_post_id(session,cookie,link):
    prints(255,255,0,f'Đang lấy post id',end='\r')
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'cookie': cookie,
    }
    try:
        response = session.get(link, headers=headers, timeout=15).text
        response= re.sub(r"\\", "", response)
        page_id=''
        post_id=''
        stories_id=''
        permalink_id=''
        try:
            if '"post_id":"' in str(response):
                permalink_id=re.findall('"post_id":".*?"',response)[0].split(':"')[1].split('"')[0]
        except:
            pass
        try:
            if 'posts' in str(response):
                post_id=response.split('posts')[1].split('"')[0]
                post_id=post_id.replace("/", "")
                post_id = re.sub(r"\\", "", post_id)
        except:
            pass
        try:
            if 'storiesTrayType' in response and not '"profile_type_name_for_content":"PAGE"' in response:
                stories_id=re.findall('"card_id":".*?"',response)[0].split('":"')[1].split('"')[0]
        except:
            pass
        try:
            if '"page_id"' in response:
                page_id=re.findall('"page_id":".*?"',response)[0].split('id":"')[1].split('"')[0]
        except:
            pass
        return {'success':True,'post_id':post_id,'permalink_id':permalink_id,'stories_id':stories_id,'page_id':page_id}
    except Exception as e:
        print(Fore.RED+f'Lỗi khi lấy ID post: {e}')
        return {'success':False}

def _parse_graphql_response(response):
    try:
        response_json = response.json()
        if 'errors' in response_json:
            error = response_json['errors'][0]
            error_msg = error.get('message', '').lower()
            if 'login required' in error_msg or 'session has expired' in error_msg:
                return {'status': 'cookie_dead', 'message': 'Cookie đã hết hạn hoặc không hợp lệ.'}
            if 'temporarily blocked' in error_msg or 'spam' in error_msg:
                 return {'status': 'action_failed', 'message': 'Hành động bị chặn vì spam.'}
            if 'permission' in error_msg:
                return {'status': 'action_failed', 'message': 'Không có quyền thực hiện hành động này.'}
            return {'status': 'action_failed', 'message': f"Lỗi từ Facebook: {error.get('message', 'Không rõ')}"}
        if 'data' in response_json and response_json.get('data'):
            if any(v is None for v in response_json['data'].values()):
                 return {'status': 'action_failed', 'message': 'Phản hồi thành công nhưng dữ liệu trả về không hợp lệ.'}
            return {'status': 'success', 'data': response_json['data']}
        return {'status': 'action_failed', 'message': 'Phản hồi không chứa dữ liệu hợp lệ.'}
    except json.JSONDecodeError:
        return {'status': 'action_failed', 'message': 'Lỗi giải mã phản hồi từ Facebook.'}
    except Exception as e:
        return {'status': 'action_failed', 'message': f'Lỗi không xác định khi phân tích phản hồi: {e}'}

def react_post_perm(data,object_id,type_react, proxy=None):
    prints(255,255,0,f'Đang thả {type_react} vào {object_id[:20]}',end='\r')
    react_list = {"LIKE": "1635855486666999","LOVE": "1678524932434102","CARE": "613557422527858","HAHA": "115940658764963","WOW": "478547315650144","SAD": "908563459236466","ANGRY": "444813342392137"}
    headers = {
        'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
        'x-fb-lsd': data['lsd'], 'cookie': data['cookie'],
    }
    payload = {
        'av': data['user_id'], '__user': data['user_id'], 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'],
        'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
        'variables': '{"input":{"feedback_id":"'+encode_to_base64('feedback:'+object_id)+'","feedback_reaction_id":"'+react_list.get(type_react.upper())+'","actor_id":"'+data['user_id']+'","client_mutation_id":"1"}}',
        'doc_id': '24034997962776771',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        return _parse_graphql_response(response)
    except Exception as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def react_post_defaul(data,object_id,type_react, proxy=None):
    return react_post_perm(data,object_id,type_react, proxy)

def react_stories(data,object_id, proxy=None):
    prints(255,255,0,f'Đang tim story {object_id[:20]}',end='\r')
    headers = {'x-fb-lsd': data['lsd'], 'cookie': data['cookie']}
    payload = {
        'av': data['user_id'], '__user': data['user_id'], 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'],
        'fb_api_req_friendly_name': 'useStoriesSendReplyMutation',
        'variables': '{"input":{"story_id":"'+object_id+'","message":"❤️","actor_id":"'+data['user_id']+'","client_mutation_id":"2"}}',
        'doc_id': '9697491553691692',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        return _parse_graphql_response(response)
    except Exception as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def react_post(data,link,type_react, proxy=None):
    res_object_id=get_post_id(data['session'],data['cookie'],link)
    if not res_object_id.get('success'):
        return {'status': 'action_failed', 'message': 'Không thể lấy ID bài viết.'}
    if res_object_id.get('stories_id'):
        return react_stories(data,res_object_id['stories_id'], proxy)
    elif res_object_id.get('permalink_id'):
        return react_post_perm(data,res_object_id['permalink_id'],type_react, proxy)
    elif res_object_id.get('post_id'):
        return react_post_defaul(data,res_object_id['post_id'],type_react, proxy)
    return {'status': 'action_failed', 'message': 'Không tìm thấy đối tượng hợp lệ để tương tác.'}

def comment_fb(data, object_id, msg, proxy=None):
    prints(255,255,0,f'Đang comment vào {object_id[:20]}',end='\r')
    headers = {'x-fb-lsd': data['lsd'], 'cookie': data['cookie']}
    payload = {
        'av': data['user_id'], '__user': data['user_id'], 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'],
        'fb_api_req_friendly_name': 'useCometUFICreateCommentMutation',
        'variables': '{"input":{"feedback_id":"'+encode_to_base64('feedback:'+object_id)+'","message":{"text":"'+msg+'"},"actor_id":"'+data['user_id']+'","client_mutation_id":"4"}}',
        'doc_id': '9379407235517228',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        parsed = _parse_graphql_response(response)
        if parsed['status'] == 'success':
            try:
                comment_text = parsed['data']['comment_create']['feedback_comment_edge']['node']['preferred_body']['text']
                prints(5,255,0,f'Đã comment "{comment_text[:30]}"',end='\r')
                parsed['payload'] = comment_text
            except:
                pass
        return parsed
    except Exception as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def dexuat_fb(data,object_id,msg, proxy=None):
    prints(255,255,0,f'Đang đề xuất Fanpage {object_id[:20]}',end='\r')
    if len(msg)<=25:
        msg+=' '*(26-len(msg))
    headers = {'x-fb-lsd': data['lsd'], 'cookie': data['cookie']}
    payload = {
        'av': data['user_id'], '__user': data['user_id'], 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'],
        'fb_api_req_friendly_name': 'ComposerStoryCreateMutation',
        'variables': '{"input":{"message":{"text":"'+msg+'"},"page_recommendation":{"page_id":"'+object_id+'","rec_type":"POSITIVE"},"actor_id":"'+data['user_id']+'","client_mutation_id":"1"}}',
        'doc_id': '24952395477729516',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        parsed = _parse_graphql_response(response)
        if parsed['status'] == 'success':
            try:
                post_id = parsed['data']['story_create']['profile_review_edge']['node']['post_id']
                my_id = parsed['data']['story_create']['profile_review_edge']['node']['feedback']['owning_profile']['id']
                link_post = f'https://www.facebook.com/{my_id}/posts/{post_id}'
                link_p = get_lin_share(data, link_post, proxy)
                parsed['payload'] = link_p
            except:
                pass
        return parsed
    except Exception as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def get_lin_share(data,link, proxy=None):
    headers = {'x-fb-lsd': data['lsd'], 'cookie': data['cookie']}
    payload = {
        'av': data['user_id'], '__user': data['user_id'], 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'],
        'fb_api_req_friendly_name': 'useLinkSharingCreateWrappedUrlMutation',
        'variables': '{"input":{"original_content_url":"'+link+'","actor_id":"'+data['user_id']+'","client_mutation_id":"3"}}',
        'doc_id': '30568280579452205',
    }
    try:
        proxies = to_requests_proxies(proxy) if proxy else None
        response = requests.post('https://www.facebook.com/api/graphql/', headers=headers, data=payload, proxies=proxies, timeout=15).json()
        return response['data']['xfb_create_share_url_wrapper']['share_url_wrapper']['wrapped_url']
    except Exception as e:
        prints(255,0,0,f'Lỗi khi lấy link share: {e}')
        return ''

def lam_job(data, jobs, type_job_doing, current_proxy=None):
    prints(255,255,0,f'Đang làm NV...',end='\r')
    link = 'https://www.facebook.com/' + jobs['object_id']
    if type_job_doing == 'review_facebook':
        res_get_post_id = get_post_id(data['session'], data['cookie'], link)
        if res_get_post_id.get('page_id'):
            return dexuat_fb(data, res_get_post_id['page_id'], jobs['data'], current_proxy)
        else:
            return {'status': 'action_failed', 'message': 'Không lấy được Page ID để đánh giá.'}
    elif type_job_doing == 'like_facebook':
        react_type = 'LIKE'
        icon = jobs.get('icon', '').lower()
        if 'love' in icon or 'thuongthuong' in icon: react_type = 'LOVE'
        elif 'care' in icon: react_type = 'CARE'
        elif 'wow' in icon: react_type = 'WOW'
        elif 'sad' in icon: react_type = 'SAD'
        elif 'angry' in icon: react_type = 'ANGRY'
        elif 'haha' in icon: react_type = 'HAHA'
        return react_post(data, link, react_type.upper(), current_proxy)
    elif type_job_doing == 'like_poster':
        res_get_post_id = get_post_id(data['session'], data['cookie'], link)
        post_id_to_comment = res_get_post_id.get('post_id') or res_get_post_id.get('permalink_id')
        if post_id_to_comment:
            return comment_fb(data, post_id_to_comment, jobs['data'], current_proxy)
        else:
            return {'status': 'action_failed', 'message': 'Không lấy được Post ID để bình luận.'}
    return {'status': 'action_failed', 'message': 'Loại nhiệm vụ không hợp lệ.'}

def countdown(seconds):
    seconds = int(seconds)
    if seconds < 1: return
    for i in range(seconds, 0, -1):
        prints(147,112,219,'[', end='')
        prints(0,255,127,'TDK', end='')
        prints(147,112,219,']', end='')
        prints(255,255,255,'[', end='')
        prints(255,215,0,'WAIT', end='')
        prints(255,255,255,']', end='')
        prints(255,20,147,' ➤ ', end='')
        prints(0,191,255,f'⏳ {i}s...', end='\r')
        time.sleep(1)
    print(' '*50, end='\r')

def print_state(status_job,_xu,jobdalam,dahoanthanh,tongcanhoanthanh,type_job, name_acc):
    hanoi_tz = timezone(timedelta(hours=7))
    now = datetime.now(hanoi_tz).strftime("%H:%M:%S")
    type_NV = {'like_facebook':'CAMXUC', 'like_poster':'COMMENT', 'review_facebook':'FANPAGE'}
    status_color = '\033[38;2;0;255;0m' + status_job.upper() + '\033[0m' if status_job.lower()=='complete' else '\033[38;2;255;255;0m' + status_job.upper() + '\033[0m'
    print(f"[{name_acc}][{now}][{dahoanthanh}/{tongcanhoanthanh}][BUMX][{type_NV.get(type_job,'UNKNOWN')}][{status_color}][+{_xu}][Đã làm:{jobdalam}]")

def switch_facebook_account(cookie, authorization, bumx_session, current_proxy=None):
    prints(0, 255, 255, "\n--- Chuyển đổi tài khoản Facebook ---")
    data = facebook_info(cookie, current_proxy)
    if not data or not data.get('success'):
        prints(255, 0, 0, 'Cookie không hợp lệ. Bỏ qua tài khoản này.')
        return None
    prints(5, 255, 0, f"Đang sử dụng tài khoản: {data['name']} ({data['user_id']})")
    add_account_fb(bumx_session, authorization, data['user_id'])
    return data

# ===================== MAIN BUMX =====================
def main_bumx_free():
    authentication_banner()
    # Chọn proxy
    use_proxy = input('Bạn có muốn sử dụng proxy không? (y/n): ').lower()
    current_proxy = None
    if use_proxy == 'y':
        proxies_list = load_proxies()
        if proxies_list:
            print(f"{trang}{'='*40}{end}")
            for idx, p in enumerate(proxies_list, 1):
                parts = p.split(':')
                if len(parts) >= 4:
                    print(f"{luc}[{idx}]{end} {xnhac}{parts[0]}:{parts[1]}{end}")
            print(f"{trang}{'='*40}{end}")
            try:
                idx = int(input(f"{luc}Chọn proxy: {end}")) - 1
                if 0 <= idx < len(proxies_list):
                    current_proxy = proxies_list[idx]
                    print(f"{luc}Đã chọn proxy: {current_proxy}{end}")
            except:
                pass
        else:
            print(f"{vang}Chưa có proxy, bỏ qua.{end}")

    # Nhập authorization BUMX
    auth_file = 'tdk-auth-bumx.txt'
    if os.path.exists(auth_file):
        choice = input('Dùng lại authorization đã lưu? (y/n): ').lower()
        if choice == 'y':
            with open(auth_file,'r') as f:
                authorization = f.read().strip()
            prints(5,255,0,'Đã dùng lại authorization')
        else:
            authorization = input('Nhập authorization bumx: ').strip()
            with open(auth_file,'w') as f:
                f.write(authorization)
    else:
        authorization = input('Nhập authorization bumx: ').strip()
        with open(auth_file,'w') as f:
            f.write(authorization)
    prints(5,255,0,f'Số dư: {wallet(authorization)}')

    # Nhập cookie Facebook
    num = int(input('Số lượng cookie FB muốn chạy: '))
    cookies_list = []
    for i in range(num):
        fname = f'tdk-cookie-fb-bumx-{i+1}.txt'
        cookie = ''
        if os.path.exists(fname):
            reuse = input(f'Dùng lại cookie trong {fname}? (y/n): ').lower()
            if reuse == 'y':
                with open(fname,'r') as f:
                    cookie = f.read().strip()
                if not re.search(r'c_user\s*=\s*\d+', cookie):
                    print(f"{do}⚠️ File {fname} không chứa cookie hợp lệ, nhập lại.{end}")
                    cookie = input(f'Nhập cookie FB thứ {i+1}: ').strip()
                    with open(fname,'w') as f:
                        f.write(cookie)
            else:
                cookie = input(f'Nhập cookie FB thứ {i+1}: ').strip()
                with open(fname,'w') as f:
                    f.write(cookie)
        else:
            cookie = input(f'Nhập cookie FB thứ {i+1}: ').strip()
            with open(fname,'w') as f:
                f.write(cookie)
        if cookie:
            cookies_list.append(cookie)
    if not cookies_list:
        prints(255,0,0,'Không có cookie')
        sys.exit(1)

    # Lọc cookie hợp lệ
    valid_cookies = []
    for ck in cookies_list:
        if check_cookie_valid(ck, current_proxy):
            valid_cookies.append(ck)
        else:
            prints(255,165,0,'Cookie không hợp lệ, bỏ qua')
    if not valid_cookies:
        prints(255,0,0,'Không có cookie hợp lệ')
        sys.exit(1)

    # ================== CHỌN CHẾ ĐỘ NHIỆM VỤ (theo yêu cầu) ==================
    prints(66, 245, 245, '''
╔════════════════════════════════════════╗
║  CHỌN CHẾ ĐỘ LÀM NHIỆM VỤ             ║
╠════════════════════════════════════════╣
║  1. Chỉ Thả cảm xúc                    ║
║  2. Chỉ Comment                        ║
║  3. ƯU TIÊN COMMENT → CẢM XÚC → REVIEW ║
║  (Có thể nhập tổ hợp: 12, 23, 123)    ║
╚════════════════════════════════════════╝
''', end='')
    choice_str = input(f"{luc}Nhập lựa chọn: {trang}").strip()

    list_type_job = []
    job_map = {'1': 'like_facebook', '2': 'like_poster', '3': 'review_facebook'}

    if choice_str == '3':
        # Chế độ ưu tiên: Comment → Cảm xúc → Review
        list_type_job = ['like_poster', 'like_facebook', 'review_facebook']
        prints(0, 255, 255, '✅ Chế độ ƯU TIÊN: Comment trước → Cảm xúc → Review')
    else:
        for ch in choice_str:
            if ch in job_map:
                job_type = job_map[ch]
                if job_type not in list_type_job:
                    list_type_job.append(job_type)
        if not list_type_job:
            prints(255, 0, 0, '❌ Không có lựa chọn hợp lệ. Mặc định chạy tất cả (ưu tiên Comment).')
            list_type_job = ['like_poster', 'like_facebook', 'review_facebook']

    prints(0, 255, 0, f'📋 Thứ tự làm nhiệm vụ: {" → ".join(list_type_job)}')
    # =========================================================

    SO_NV = int(input('Làm bao nhiêu job: '))
    delay1 = int(input('Delay min (s): '))
    delay2 = int(input('Delay max (s): '))

    # Khởi tạo session BUMX
    bumx_session = requests.Session()

    # Đăng nhập cookie đầu tiên
    data = switch_facebook_account(valid_cookies[0], authorization, bumx_session, current_proxy)
    if not data:
        prints(255,0,0,'Cookie đầu lỗi')
        sys.exit(1)

    os.system('cls' if os.name=='nt' else 'clear')
    authentication_banner()

    demht = 0
    demsk = 0
    current_idx = 0
    tasks_on_current = 0
    consecutive_failures = 0
    failed_jobs = set()

    while demht < SO_NV:
        try:
            # Xoay cookie nếu cần
            if tasks_on_current >= 50 and len(valid_cookies) > 1:
                current_idx = (current_idx + 1) % len(valid_cookies)
                new_data = switch_facebook_account(valid_cookies[current_idx], authorization, bumx_session, current_proxy)
                if new_data:
                    data = new_data
                    tasks_on_current = 0
                    consecutive_failures = 0
                else:
                    valid_cookies.pop(current_idx)
                    if not valid_cookies: break
                    current_idx %= len(valid_cookies)
                    data = switch_facebook_account(valid_cookies[current_idx], authorization, bumx_session, current_proxy)
                    tasks_on_current = 0

            # Tải job theo thứ tự ưu tiên
            all_jobs = []
            for t in list_type_job:
                reload(bumx_session, authorization, t)
                time.sleep(2)
                jobs = get_job(bumx_session, authorization, t)
                if jobs:
                    all_jobs.extend(jobs)
            if not all_jobs:
                prints(255,255,0,'Không có NV, chờ 10s', end='\r')
                time.sleep(10)
                continue

            for job in all_jobs:
                if demht >= SO_NV: break
                if job['buff_id'] in failed_jobs: continue
                try:
                    res_load = load(bumx_session, authorization, job)
                    time.sleep(random.randint(2,4))
                    if res_load and res_load.get('success') and job['type'] in list_type_job:
                        delay = random.randint(delay1, delay2)
                        start = time.time()
                        status = lam_job(data, res_load, job['type'], current_proxy)
                        if status and status.get('status') == 'success':
                            submit_res = submit(bumx_session, authorization, job, status.get('payload'), res_load)
                            if submit_res[0]:
                                demht += 1
                                tasks_on_current += 1
                                consecutive_failures = 0
                                print_state('complete', submit_res[1], submit_res[2], demht, SO_NV, job['type'], data['name'])
                                countdown(delay - (time.time() - start))
                            else:
                                raise Exception('Submit fail')
                        else:
                            raise Exception('Action fail')
                    else:
                        raise Exception('Load fail')
                except Exception as e:
                    prints(255,165,0,f'Job lỗi: {e}, báo cáo...')
                    report(bumx_session, authorization, job)
                    failed_jobs.add(job['buff_id'])
                    demsk += 1
                    consecutive_failures += 1
                    time.sleep(4)
        except KeyboardInterrupt:
            prints(255,255,0,'\nDừng bởi người dùng')
            break
    prints(5,255,0,f'\nHoàn thành: {demht}, Lỗi: {demsk}')

# ===================== KHỞI CHẠY =====================
if __name__ == "__main__":
    authentication_banner()
    proxy_menu()
    main_bumx_free()
