from io import BytesIO
import requests, re, json, random
from time import sleep
import os

# ====== DEBUG MODE ======
DEBUG = True  # Bật/tắt debug

# ====== MÀU SẮC TERMINAL ======
luc    = "\033[1;32m"
trang  = "\033[1;37m"
do     = "\033[1;31m"
vang   = "\033[0;93m"
hong   = "\033[1;35m"
xnhac  = "\033[1;36m"
xduong = "\033[1;34m"
xam = "\033[90m"
reset = "\033[0m"
hdang  = f"{trang} [{do}+_+{trang}] {hong}➤ {luc}"

# ====== HÀM LẤY IP MÁY ======
def get_ip_from_url(url):
    try:
        data = requests.get(url).json()
        return data['ip'], data['country']
    except:
        return "Unknown", "Unknown"

ip, country = get_ip_from_url("https://api.myip.com/")

def debug_print(message, data=None):
    if DEBUG:
        print(f"\n\033[90m[DEBUG]\033[0m {message}")
        if data:
            print(f"\033[90m[DATA]\033[0m {data}\033[0m")

# ====== LOGO TOOL ======
def logo():
    os.system("cls" if os.name == "nt" else "clear")

    mau = random.choice([
        "\033[1;31m",  # đỏ
        "\033[1;32m",  # xanh lá
        "\033[1;33m",  # vàng
        "\033[1;34m",  # xanh dương
        "\033[1;35m",  # tím
        "\033[1;36m",  # xanh ngọc
        "\033[1;91m",  # đỏ sáng
        "\033[1;92m",  # xanh sáng
        "\033[1;93m",  # vàng sáng
        "\033[1;94m",  # xanh dương sáng
        "\033[1;95m",  # hồng
        "\033[1;96m",  # cyan sáng
    ])

    print(f"""
{mau}
██╗  ██╗███╗   ███╗██╗  ██╗      ████████╗ ██████╗  ██████╗ ██╗
██║  ██║████╗ ████║██║ ██╔╝      ╚══██╔══╝██╔═══██╗██╔═══██╗██║
███████║██╔████╔██║█████╔╝          ██║   ██║   ██║██║   ██║██║
██╔══██║██║╚██╔╝██║██╔═██╗          ██║   ██║   ██║██║   ██║██║
██║  ██║██║ ╚═╝ ██║██║  ██╗         ██║   ╚██████╔╝╚██████╔╝███████╗
╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝         ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝

╔═══════════════════════════════════════════════════════╗
{hdang}Website: \033[1;97manhcute.neocities.org{mau}
║───────────────────────────────────────────────────────║
{hdang}Tool Upload Avatar & Cover
{hdang}Copyright: HMK-TOOL
{hdang}Zalo: https://zalo.me/g/rcryht808
{hdang}Facebook: HMK-TOOL
{hdang}IP: {ip} ({country})
╚═══════════════════════════════════════════════════════╝
\033[0m
""")
def DelayTime(seconds, message):
    for remaining in range(seconds, 0, -1):
        for _ in range(5):
            effect = "".join(random.choice(["𝐗", " "]) for _ in range(5))
            print(f"\r{do}[{vang}LTHĐ{do}] [{trang}{message}{do}] [{luc}{effect}{do}] [{xnhac}{remaining}{do}]                         \r", end='')
            sleep(0.2)
    print("\r\r\033[1;95m     ⚡Lê Trọng Hải Đăng⚡\033[1;37m                 \r", end='')

def thanh_ngang():
    print('\033[1;31m─\033[1;37m' * 57) 

# API FACEBOOK
class ApiClient:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.headers = {
            'authority': 'www.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '"Chromium";v="120", "Google Chrome";v="120", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'viewport-width': '1366',
            'Cookie': self.cookie
        }
        self.idfb, self.name, self.username, self.jazoest, self.fb_dtsg = self.profile()
    def profile(self):
        url = 'https://www.facebook.com/profile.php'
        try:
            debug_print("Đang lấy profile...", f"Cookie: {self.cookie[:30]}...")
            
            res = self.session.get(url, headers=self.headers).text
            debug_print("Response nhận được", f"Length: {len(res)}")
            
            # Lấy User ID từ cookie
            idfb = self.cookie.split('c_user=')[1].split(';')[0]
            debug_print("User ID:", idfb)
            
            # Lấy tên từ URL redirect (cách đáng tin cậy nhất)
            link_redirect = self.session.get(url, headers=self.headers).url
            debug_print("Redirect URL:", link_redirect)
            
            name = None
            username = None
            jazoest = None
            fb_dtsg = None
            
            # Lấy tên từ URL: /people/Dang-Thinh-Khoa/pfbid...
            if '/people/' in link_redirect:
                parts = link_redirect.split('/people/')[1].split('/')
                if len(parts) > 0:
                    url_name = parts[0].split('?')[0]
                    # Chuyển dash thành khoảng trắng rồi title case
                    name = url_name.replace('-', ' ').title()
                    debug_print("Tên user (từ URL):", name)
            
            # Lấy username từ URL nếu có
            if '/people/' not in link_redirect:
                match = re.search(r'facebook\.com/([^/?]+)/?', link_redirect)
                if match:
                    username = match.group(1)
                    debug_print("Username (từ URL):", username)
            
            # Lấy jazoest từ HTML (nhiều pattern khác nhau)
            jazoest = None
            jazoest_patterns = [
                r'jazoest[="]+(\d{3,10})',  # jazoest=123 hoặc jazoest="123" (3-10 số)
                r'"jazoest":"(\d{3,10})"',  # "jazoest":"123"
                r'jazoest%22%3A%22(\d{3,10})',  # URL encoded jazoest%22%3A%22123%22
                r'&jazoest=(\d{3,10})',  # &jazoest=123 trong URL
                r'jazoest%3D(\d{3,10})',  # URL encoded jazoest%3D123
            ]
            for pattern in jazoest_patterns:
                match_jazoest = re.search(pattern, res)
                if match_jazoest:
                    jazoest = match_jazoest.group(1)
                    debug_print(f"Jazoest (pattern {pattern}):", jazoest)
                    break
            
            # Nếu vẫn không tìm thấy, thử từ cookie
            if not jazoest or jazoest == '0' or len(jazoest) < 3:
                if 'jazoest=' in self.cookie:
                    jazoest = self.cookie.split('jazoest=')[1].split(';')[0]
                    debug_print("Jazoest (từ cookie):", jazoest)
                else:
                    # Tạo jazoest giả (fb thường dùng số ngẫu nhiên 6-8 chữ số)
                    import random
                    jazoest = str(random.randint(100000, 9999999))
                    debug_print("Jazoest (random fallback):", jazoest)
            
            # Nếu không tìm thấy trong HTML, thử từ cookie
            if not jazoest or jazoest == '0':
                if 'jazoest=' in self.cookie:
                    jazoest = self.cookie.split('jazoest=')[1].split(';')[0]
                else:
                    jazoest = '0'
                debug_print("Jazoest (từ cookie):", jazoest)
            
            # Lấy fb_dtsg từ HTML - kiểm tra nhiều vị trí
            fb_dtsg = None
            
            # Cách 1: envFlush có thể chứa "f" hoặc "fb_dtsg"
            # Tìm toàn bộ envFlush và parse thủ công
            env_flush_match = re.search(r'function envFlush\(e\)\{[^}]*\}envFlush\(\{([^}]+)\}', res, re.DOTALL)
            if env_flush_match:
                env_content = env_flush_match.group(1)
                debug_print("EnvFlush content:", env_content[:200] + "..." if len(env_content) > 200 else env_content)
                
                # Tìm "f":"xxx" hoặc "fb_dtsg":"xxx"
                f_match = re.search(r'"f":"([A-Za-z0-9_=-]+)"', env_content)
                if f_match:
                    fb_dtsg = f_match.group(1)
                    debug_print("FB DTSG (f):", fb_dtsg[:30] + "...")
                
                if not fb_dtsg:
                    fb_dtsg_match = re.search(r'"fb_dtsg":"([A-Za-z0-9_=-]+)"', env_content)
                    if fb_dtsg_match:
                        fb_dtsg = fb_dtsg_match.group(1)
                        debug_print("FB DTSG (fb_dtsg):", fb_dtsg[:30] + "...")
            
            # Cách 2: Tìm trong script tag bất kỳ
            if not fb_dtsg:
                script_matches = re.findall(r'<script[^>]*>(.*?)</script>', res, re.DOTALL)
                for script in script_matches:
                    if 'envFlush' in script:
                        f_match = re.search(r'"f":"([A-Za-z0-9_=-]{10,50})"', script)
                        if f_match:
                            fb_dtsg = f_match.group(1)
                            debug_print("FB DTSG (script envFlush):", fb_dtsg[:30] + "...")
                            break
            
            # Cách 3: Tìm data-fb-dtsg
            if not fb_dtsg:
                data_dtsg = re.search(r'data-fb-dtsg="([A-Za-z0-9_=-]+)"', res)
                if data_dtsg:
                    fb_dtsg = data_dtsg.group(1)
                    debug_print("FB DTSG (data-fb-dtsg):", fb_dtsg[:30] + "...")
            
            # Cách 4: Tìm trong __webpack_modules__ hoặc các chunk khác
            if not fb_dtsg:
                # fb_dtsg thường có dạng like: AgAA... (base64 encoded)
                # Chỉ lấy từ các vị trí cụ thể: envFlush, data-fb-dtsg, hoặc những pattern chuẩn
                
                # Thử tìm trong tất cả script với pattern chuẩn hơn
                script_matches = re.findall(r'<script[^>]*>(.*?)</script>', res, re.DOTALL)
                for i, script in enumerate(script_matches):
                    if 'dtsg' in script.lower() or '"f"' in script:
                        # Tìm pattern chuẩn: "f":"XXX" hoặc fb_dtsg":"XXX"
                        matches = re.findall(r'["\'](f|fb_dtsg)["\']\s*:\s*["\']([A-Za-z0-9_=-]{20,80})["\']', script)
                        for key, value in matches:
                            # Validate: phải có cả chữ hoa, chữ thường và số
                            if any(c.isupper() for c in value) and any(c.islower() for c in value) and any(c.isdigit() for c in value):
                                fb_dtsg = value
                                debug_print(f"FB DTSG (script#{i} {key}):", fb_dtsg[:30] + "...")
                                break
                    if fb_dtsg:
                        break
            
            # Kiểm tra cuối cùng: fb_dtsg phải hợp lệ
            # fb_dtsg thực thường bắt đầu bằng A, Q, hoặc các ký tự base64 khác
            # và KHÔNG chứa các từ như Config, Data, Summary, v.v.
            invalid_patterns = ['Config', 'Data', 'Summary', 'Blacklist', 'ClickID', 'AdsPE', 'Insights', 'Domain']
            if fb_dtsg:
                for pattern in invalid_patterns:
                    if pattern in fb_dtsg:
                        debug_print(f"❌ FB DTSG invalid (contains {pattern}), discarding...")
                        fb_dtsg = None
                        break
            
            # Lấy username từ HTML nếu chưa có
            if not username:
                match = re.search(r'"userVanity":"(.*?)"', res)
                if match and match.group(1):
                    username = match.group(1)
                    debug_print("Username (từ HTML):", username)
            
            # Kiểm tra nếu vẫn thiếu thông tin quan trọng
            if not fb_dtsg:
                debug_print("❌ Không lấy được fb_dtsg từ HTML, thử cách khác...")
                # Thử request đến API để lấy fb_dtsg
                try:
                    api_response = self.session.get(
                        'https://www.facebook.com/api/graphql/',
                        headers=self.headers,
                        params={'__a': '1'}
                    ).text
                    debug_print("API Response:", api_response[:200] if api_response else "Empty")
                    
                    # Thử tìm trong API response
                    if api_response:
                        f_match = re.search(r'"f":"([A-Za-z0-9_=-]+)"', api_response)
                        if f_match:
                            fb_dtsg = f_match.group(1)
                            debug_print("FB DTSG (từ API):", fb_dtsg[:30] + "...")
                except Exception as e:
                    debug_print("Lỗi khi gọi API:", str(e))
            
            if not fb_dtsg:
                debug_print("❌ Vẫn không lấy được fb_dtsg!")
            elif not jazoest or jazoest == '0' or len(jazoest) < 3:
                debug_print("⚠️ Jazoest không hợp lệ:", jazoest)
            else:
                debug_print("✅ Profile lấy thành công!")
                
            return idfb, name, username, jazoest, fb_dtsg
        except Exception as e:
            debug_print("❌ Lỗi profile:", str(e))
            import traceback
            debug_print("Traceback:", traceback.format_exc())
            return None, None, None, None , None
        
    def upload(self, linkanh):
        try:
            debug_print(f"Đang upload ảnh: {linkanh}")
            
            img_data = requests.get(linkanh).content
            debug_print("Đã tải ảnh", f"Size: {len(img_data)} bytes")
            
            params = {'profile_id': self.idfb,'__a': '1','fb_dtsg': self.fb_dtsg,'jazoest': self.jazoest}
            ext = linkanh.split('.')[-1].lower()
            mime = f'image/{ext if ext != "jpg" else "jpeg"}'
            files = {'file': ('random_image.' + ext, BytesIO(img_data), mime)}
            
            res = self.session.post('https://www.facebook.com/profile/picture/upload/',params=params,headers=self.headers,files=files).text
            debug_print("Response upload:", res[:200] if len(res) > 200 else res)
            
            if '{"fbid":"' in res:
                fbid = res.split('{"fbid":"')[1].split('"')[0]
                debug_print("✅ Upload thành công", f"FBID: {fbid}")
                return fbid
            else:
                debug_print("❌ Upload thất bại - không tìm thấy fbid")
                return False
        except Exception as e:
            debug_print("❌ Lỗi upload:", str(e))
            return False

    def UpAvt(self, idavt:int):
        debug_print(f"Đang set avatar: {idavt}")
        
        data = {
            'av': self.idfb,
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'ProfileCometProfilePictureSetMutation',
            'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1721296676721,110519,190055527696468,,","caption":"UPDATE AVATA AUTO BY HAIDANG","existing_photo_id":"'+idavt+'","expiration_time":null,"profile_id":"'+self.idfb+'","profile_pic_method":"EXISTING","profile_pic_source":"TIMELINE","scaled_crop_rect":{"height":0.99999,"width":0.99999,"x":0,"y":0},"skip_cropping":true,"actor_id":"'+self.idfb+'","client_mutation_id":"1"},"isPage":false,"isProfile":true,"sectionToken":"UNKNOWN","collectionToken":"UNKNOWN","scale":1,"__relay_internal__pv__ProfileGeminiIsCoinFlipEnabledrelayprovider":false}',
            'server_timestamps': 'true',
            'doc_id': '8252641828081928',
        }
        rq = self.session.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data).text
        debug_print("Response UpAvt:", rq[:200] if len(rq) > 200 else rq)
        
        if '{"data":{"profile_picture_set":{"profile":{"__typename":"User","id":"' in rq:
            debug_print("✅ Set avatar thành công!")
            return True
        else:
            debug_print("❌ Set avatar thất bại!")
            return False
            
    def UpCover(self, idavt:int):
        debug_print(f"Đang set cover: {idavt}")
        
        data = {
            'av': self.idfb,
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'ProfileCometCoverPhotoUpdateMutation',
            'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1753753183176,88451,190055527696468,,","cover_photo_id":"'+idavt+'","focus":{"x":0.5,"y":0.49999998393811673},"target_user_id":"'+self.idfb+'","actor_id":"'+self.idfb+'","client_mutation_id":"1"},"scale":1,"contextualProfileContext":null}',
            'server_timestamps': 'true',
            'doc_id': '31388044007461211',
        }

        rq = self.session.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data).text
        debug_print("Response UpCover:", rq[:200] if len(rq) > 200 else rq)
        
        if '{"data":{"user_update_cover_photo":{"user":{"name":"' in rq:
            debug_print("✅ Set cover thành công!")
            return True
        else:
            debug_print("❌ Set cover thất bại!")
            return False

def addcookie():
    list_clone, stt = [], 0
    while True:
        stt += 1
        ck = input(f'{hdang}Nhập Cookie Facebook thứ {xnhac}{stt}: {vang}').strip()
        if ck == '': break
        clone = ApiClient(ck)
        if not all([clone.idfb, clone.name, clone.jazoest, clone.fb_dtsg]):
            print(f"{hdang}{do}Cookie không hợp lệ hoặc lỗi lấy thông tin."); stt -= 1
        else:
            print(f"{luc}Login Success:{vang} {clone.name}{do}|{xnhac}{clone.username}{do}|{xduong}{clone.idfb}")
            list_clone.append(ck)
            thanh_ngang()
    debug_print("Tổng cookie hợp lệ:", len(list_clone))
    return list_clone

# Nhập danh sách link ảnh
valid_extensions = ('.jpg', '.jpeg')
list_link = []
stt = 0
# Login
logo()
list_clone = addcookie()
logo()
solink = int(input(f'{hdang}Bạn Muốn Sử Dụng Bao Nhiêu Link Ảnh:{vang} '))
thanh_ngang()
print(f"{hdang}{do}Nếu không có link nào được nhập → dùng API random")
while stt < solink:
    link = input(f"{hdang}Nhập Link Ảnh Thứ{xnhac} {stt + 1} (Enter để dừng): {vang}").strip()
    if not link:
        break
    # Kiểm tra điều kiện hợp lệ
    if link.lower().endswith(valid_extensions) and link.startswith(('http://', 'https://')):
        print(f"{luc} Link ảnh hợp lệ!{reset}")
        list_link.append(link)
        stt += 1
    else:
        print(f"{do} Link không hợp lệ! Phải bắt đầu bằng http(s):// và kết thúc bằng đuôi ảnh hợp lệ.{reset}")
# Nếu không có link nào được nhập → dùng API random
if not list_link:
    debug_print("Không có link ảnh, đang lấy từ API...")
    while stt < solink:
        try:
            linkanh = requests.get('https://dangvippro.x10.mx/api/random_image.php').json().get('image', '')
            debug_print("API trả về:", linkanh)
        except:
            print(f'{do} Sever random ảnh bị lỗi. Vui lòng nhập link ảnh!')
            exit()

        if linkanh.lower().endswith(valid_extensions) and linkanh.startswith(('http://', 'https://')):
            stt += 1
            print(f'{hdang}Đang lấy ảnh thứ {stt}/{solink}', end='\r')
            list_link.append(linkanh)
        else:
            print(f"{do}Link ảnh random không hợp lệ!{reset}", end='\r')
        sleep(2)
logo()
print(f"{xnhac} Tìm thấy {len(list_clone)} cookie và {len(list_link)} link ảnh")
thanh_ngang()

for cookies in list(list_clone):
    debug_print(f"=== Đang xử lý cookie: {cookies[:20]}... ===")
    
    clone = ApiClient(cookies)
    if not all([clone.idfb, clone.name, clone.jazoest, clone.fb_dtsg]):
        print(f"{hdang}{do}Cookie không hợp lệ hoặc lỗi lấy thông tin.")
        list_clone.remove(cookies)
        continue
    print(f"{luc}Login Success:{vang} {clone.name}{do}|{xnhac}{clone.username}{do}|{xduong}{clone.idfb}")
    list_uid = []
    if list_link:
        for linkanh in list_link:
            idavt = clone.upload(linkanh)
            if idavt and idavt not in list_uid:
                list_uid.append(idavt)
                print(f"{luc}Upload ảnh random thành công!{reset} {idavt}", end='\r')
            else:
                print(f"{do}Upload ảnh thất bại hoặc trùng!{reset}", end='\r')
            sleep(1)
            DelayTime(10, idavt)
                
    if list_uid:
        debug_print(f"Có {len(list_uid)} ảnh hợp lệ để set", list_uid)
        print(f"{luc}Tìm thấy {len(list_uid)} ảnh hợp lệ!                                {reset}", end='\r')
        
        if len(list_uid) == 1:
            avt_id = cover_id = list_uid[0]
        else:
            avt_id, cover_id = random.sample(list_uid, 2)

        debug_print("Chọn avatar:", avt_id)
        debug_print("Chọn cover:", cover_id)
        
        print(f"{vang}Đang cập nhật avatar...       {reset}", end='\r')
        if clone.UpAvt(avt_id):
            print(f"{trang} ╰─> Cập nhật avatar thành công!{reset} {avt_id}")
        else:
            print(f"{do} ╰─> Cập nhật avatar thất bại!{reset}")

        DelayTime(2, "Delay")
        print(f"{vang}Đang cập nhật cover...        {reset}", end='\r')
        if clone.UpCover(cover_id):
            print(f"{trang} ╰─> Cập nhật bìa thành công!{reset} {cover_id}")
        else:
            print(f"{do} ╰─> Cập nhật bìa thất bại!{reset}")
    else:
        print(f"{do}Không có ảnh nào để cập nhật!{reset}")
        
    debug_print("=== Hoàn thành xử lý ===\n")