import sys
import json
import uuid
import time
import requests
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QComboBox, QSpinBox, QGroupBox, 
                             QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

# --- CẤU HÌNH GIAO DIỆN ---
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 14px;
}
QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 5px;
    margin-top: 20px;
    font-weight: bold;
    color: #00ffcc;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
}
QLabel {
    color: #cccccc;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #2d2d2d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    color: white;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #00ffcc;
}
QPushButton {
    background-color: #0078d7;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #005a9e;
}
QPushButton:pressed {
    background-color: #004080;
}
QPushButton#btnStop {
    background-color: #d32f2f;
}
QPushButton#btnStop:hover {
    background-color: #b71c1c;
}
QTextEdit {
    background-color: #121212;
    border: 1px solid #333;
    color: #00ff00;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}
QStatusBar {
    background-color: #0078d7;
    color: white;
}
"""

# --- CORE LOGIC (API) ---

class ApiPro5:
    def __init__(self, cookies, fb_dtsg, jazoet, id_page):
        self.headers = {
            'authority': 'www.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'accept-language': 'vi',
            'cookie': cookies,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        }
        self.fb_dtsg = fb_dtsg
        self.jazoet = jazoet
        self.user_id = id_page

    def join(self, group_id):
        data = {
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoet,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'GroupCometJoinForumMutation',
            'variables': '{"feedType":"DISCUSSION","groupID":"'+group_id+'","imageMediaType":"image/x-auto","input":{"action_source":"GROUPS_ENGAGE_TAB","attribution_id_v2":"GroupsCometCrossGroupFeedRoot.react,comet.groups.feed,tap_tabbar,1667116100089,433821,2361831622,","group_id":"'+group_id+'","group_share_tracking_params":null,"actor_id":"'+self.user_id+'","client_mutation_id":"2"},"inviteShortLinkKey":null,"isChainingRecommendationUnit":false,"isEntityMenu":false,"scale":1,"source":"GROUPS_ENGAGE_TAB","renderLocation":"group_mall","__relay_internal__pv__GlobalPanelEnabledrelayprovider":false,"__relay_internal__pv__GroupsCometEntityMenuEmbeddedrelayprovider":true}',
            'server_timestamps': 'true',
            'doc_id': '5915153095183264',
        }
        try:
            response = requests.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data, timeout=10).text
            return response
        except Exception as e:
            return str(e)

    def reaction(self, id_post, reaction):
        try:
            url = requests.get('https://www.facebook.com/'+id_post, headers=self.headers).url
            home = requests.get(url, headers=self.headers).text
            feedback_id = home.split('{"__typename":"CommentComposerLiveTypingBroadcastPlugin","feedback_id":"')[1].split('","')[0]
            data = {
                'fb_dtsg': self.fb_dtsg,
                'jazoest': self.jazoet,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
                'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1667106623951,429237,190055527696468,","feedback_id":"'+feedback_id+'","feedback_reaction_id":"'+reaction+'","feedback_source":"PROFILE","is_tracking_encrypted":true,"tracking":["AZXg8_yM_zhwrTY7oSTw1K93G-sycXrSreRnRk66aBJ9mWkbSuyIgNqL0zHEY_XgxepV1XWYkuv2C5PuM14WXUB9NGsSO8pPe8qDZbqCw5FLQlsGTnh5w9IyC_JmDiRKOVh4gWEJKaTdTOYlGT7k5vUcSrvUk7lJ-DXs3YZsw994NV2tRrv_zq1SuYfVKqDboaAFSD0a9FKPiFbJLSfhJbi6ti2CaCYLBWc_UgRsK1iRcLTZQhV3QLYfYOLxcKw4s2b1GeSr-JWpxu1acVX_G8d_lGbvkYimd3_kdh1waZzVW333356_JAEiUMU_nmg7gd7RxDv72EkiAxPM6BA-ClqDcJ_krJ_Cg-qdhGiPa_oFTkGMzSh8VnMaeMPmLh6lULnJwvpJL_4E3PBTHk3tIcMXbSPo05m4q_Xn9ijOuB5-KB5_9ftPLc3RS3C24_7Z2bg4DfhaM4fHYC1sg3oFFsRfPVf-0k27EDJM0HZ5tszMHQ"],"session_id":"'+str(uuid.uuid4())+'","actor_id":"'+self.user_id+'","client_mutation_id":"1"},"useDefaultActor":false,"scale":1}',
                'server_timestamps': 'true',
                'doc_id': '5703418209680126',
            }
            reaction = requests.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data, timeout=10).text
            return {'status': True, 'url': url}
        except:
            return {'status': False, 'url': ''}

    def subscribe(self, uid):
        data = {
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoet,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'CometUserFollowMutation',
            'variables': '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1667114418950,431532,190055527696468,","subscribe_location":"PROFILE","subscribee_id":"'+uid+'","actor_id":"'+self.user_id+'","client_mutation_id":"1"},"scale":1}',
            'server_timestamps': 'true',
            'doc_id': '5032256523527306',
        }
        try:
            subscribe = requests.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data, timeout=10).text
            return subscribe
        except:
            return "Error"

class WorkerThread(QThread):
    log_signal = pyqtSignal(str, str)  # message, color
    status_signal = pyqtSignal(str)   # status bar text
    finished_signal = pyqtSignal()
    page_loaded = pyqtSignal(list)    # danh sách page

    def __init__(self):
        super().__init__()
        self.running = False
        self.token = ""
        self.cookie_fb = ""
        self.id_page = ""
        self.fb_dtsg = ""
        self.jazoet = ""
        self.job_type = 1
        self.delay = 5
        self.cookie_ttc = ""
        self.api = None

    def set_credentials(self, token, cookie_fb):
        self.token = token
        self.cookie_fb = cookie_fb
        # Login TTC
        try:
            data = {'access_token': token}
            text_1 = requests.post("https://tuongtaccheo.com/logintoken.php", data=data)
            log = text_1.json().get("status")
            if log == "success":
                self.cookie_ttc = text_1.headers.get("Set-Cookie")
                self.log_signal.emit(f"Đăng nhập TTC thành công! User: {text_1.json()['data']['user']}", "#00ff00")
                return True
            else:
                self.log_signal.emit("Đăng nhập TTC thất bại!", "#ff3333")
                return False
        except Exception as e:
            self.log_signal.emit(f"Lỗi đăng nhập TTC: {e}", "#ff3333")
            return False

    def load_pages(self):
        try:
            headers = {
                'authority': 'mbasic.facebook.com',
                'cookie': self.cookie_fb,
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            }
            response = requests.get('https://mbasic.facebook.com/', headers=headers).text
            self.fb_dtsg = response.split('<input type="hidden" name="fb_dtsg" value="')[1].split('"')[0]
            self.jazoet = response.split('<input type="hidden" name="jazoest" value="')[1].split('"')[0]
            
            idpef = requests.post('https://www.facebook.com/api/graphql/', 
                                  headers=headers, 
                                  data={'fb_dtsg': self.fb_dtsg,
                                        'jazoest': self.jazoet,
                                        'variables': '{"showUpdatedLaunchpointRedesign":true,"useAdminedPagesForActingAccount":false,"useNewPagesYouManage":true}',
                                        'doc_id': '5300338636681652'}).json()
            
            nodes = idpef['data']['viewer']['actor']['profile_switcher_eligible_profiles']['nodes']
            self.page_loaded.emit(nodes)
        except Exception as e:
            self.log_signal.emit(f"Lỗi lấy danh sách Page: {e}", "#ff3333")

    def get_balance(self):
        try:
            head = {
                'Host': 'tuongtaccheo.com',
                'cookie': self.cookie_ttc
            }
            response = requests.get('https://tuongtaccheo.com/home.php', headers=head).text
            xu = response.split('<li><a>Số dư: <strong style="color: red;" id="soduchinh">')[1].split('<')[0]
            return xu
        except:
            return "Error"

    def stop(self):
        self.running = False
        self.wait()

    def run(self):
        self.running = True
        
        # Setup API Facebook
        try:
            # Tạo cookie chuyên dụng cho page
            ck_pro5 = 'sb={}; datr={}; c_user={}; wd={}; xs={}; fr={}; i_user={};'.format(
                self.cookie_fb.split('sb=')[1].split(';')[0] if 'sb=' in self.cookie_fb else '',
                self.cookie_fb.split('datr=')[1].split(';')[0] if 'datr=' in self.cookie_fb else '',
                self.cookie_fb.split('c_user=')[1].split(';')[0] if 'c_user=' in self.cookie_fb else '',
                self.cookie_fb.split('wd=')[1].split(';')[0] if 'wd=' in self.cookie_fb else '',
                self.cookie_fb.split('xs=')[1].split(';')[0] if 'xs=' in self.cookie_fb else '',
                self.cookie_fb.split('fr=')[1].split(';')[0] if 'fr=' in self.cookie_fb else '',
                self.id_page
            )
            self.api = ApiPro5(cookies=ck_pro5, fb_dtsg=self.fb_dtsg, jazoet=self.jazoet, id_page=self.id_page)
        except Exception as e:
            self.log_signal.emit(f"Lỗi khởi tạo API FB: {e}", "#ff3333")
            self.running = False
            self.finished_signal.emit()
            return

        # Cấu hình Page trên TTC
        try:
            url = 'https://tuongtaccheo.com/cauhinh/datnick.php'
            data = f'iddat%5B%5D={self.id_page}&loai=fb'
            head = {'Host': 'tuongtaccheo.com', 'cookie': self.cookie_ttc, 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            ve = requests.post(url=url, headers=head, data=data).text
            if ve != '1':
                self.log_signal.emit(f"Bạn chưa thêm Page {self.id_page} vào cấu hình trên TTC!", "#ff3333")
                self.running = False
                self.finished_signal.emit()
                return
        except:
            pass

        ttt = 0
        total_jobs = 0
        last_bal = self.get_balance()
        self.status_signal.emit(f"Số dư: {last_bal} Xu | Đang chạy...")

        while self.running:
            try:
                # Xác định loại job
                type_5 = ['/subcheo/', '/camxuccheo/', '/thamgianhomcheo/']
                
                # Chỉnh sửa logic loop job
                current_loai_index = (self.job_type - 1) % 3 
                if self.job_type == 4: # Mix
                    current_loai_index = ttt % 3
                    ttt += 1
                else:
                    current_loai_index = self.job_type - 1
                
                loai = type_5[current_loai_index]

                head = {
                    'Host': 'tuongtaccheo.com',
                    'cookie': self.cookie_ttc,
                    'x-requested-with': 'XMLHttpRequest'
                }
                
                get_nv = requests.get(f'https://tuongtaccheo.com/kiemtien{loai}getpost.php', headers=head)
                list_job_json = get_nv.json()

                if not list_job_json:
                    self.log_signal.emit(f"Hết Job [{loai}]", "#ffff00")
                    time.sleep(2) # Chơi tí rồi retry
                    continue

                for job in list_job_json:
                    if not self.running: break
                    id_job = job["idpost"]
                    
                    success = False
                    msg = ""
                    
                    if loai == "/subcheo/": # FOLLOW
                        self.api.subscribe(id_job)
                        data_nhan = f'id={id_job}'
                        success = True # Giả định thành công để nhận xu, tool cũ check lỗi sau
                        msg = "Follow"
                        
                    elif loai == "/camxuccheo/": # REACT
                        type_1 = job["loaicx"]
                        type_2_map = {
                            "LOVE": "1678524932434102", "CARE": "613557422527858",
                            "WOW": "478547315650144", "HAHA": "115940658764963",
                            "SAD": "908563459236466", "ANGRY": "444813342392137"
                        }
                        type_2 = type_2_map.get(type_1, "1678524932434102")
                        self.api.reaction(id_job, type_2)
                        data_nhan = f"id={id_job}&loaicx={type_1}"
                        success = True
                        msg = f"{type_1}"

                    elif loai == "/thamgianhomcheo/": # GROUP
                        self.api.join(id_job)
                        data_nhan = f"id={id_job}"
                        success = True
                        msg = "Group"

                    # Nhận xu
                    nhan = requests.post(f'https://tuongtaccheo.com/kiemtien{loai}nhantien.php', 
                                         headers={'Host':'tuongtaccheo.com','cookie':self.cookie_ttc}, 
                                         data=data_nhan).json()
                    
                    if "error" in nhan:
                        self.log_signal.emit(f"Lỗi: {id_job} | {msg}", "#ff3333")
                    else:
                        total_jobs += 1
                        current_bal = self.get_balance()
                        self.log_signal.emit(f"Thành công: {msg} | {id_job} | Balance: {current_bal}", "#00ff00")
                        self.status_signal.emit(f"Jobs: {total_jobs} | Xu: {current_bal} | Delay: {self.delay}s")

                    # Delay xử lý nhỏ để không spam quá nhanh
                    if self.running:
                        time.sleep(2) 

                # Delay giữa các lượt get job
                for i in range(self.delay):
                    if not self.running: break
                    time.sleep(1)

            except Exception as e:
                self.log_signal.emit(f"Lỗi hệ thống: {e}", "#ff3333")
                time.sleep(5)

        self.finished_signal.emit()

# --- GIAO DIỆN CHÍNH ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool TuongTacCheo  - By KhangDevxCoder")
        self.resize(800, 600)
        self.setStyleSheet(STYLESHEET)
        
        self.worker = WorkerThread()
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_job_finished)
        self.worker.page_loaded.connect(self.populate_pages)

        self.init_ui()
        self.apply_fonts()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # --- Phần Nhập Thông Tin ---
        group_info = QGroupBox("THÔNG TIN TÀI KHOẢN")
        layout_info = QVBoxLayout()
        
        # Token
        h_token = QHBoxLayout()
        h_token.addWidget(QLabel("Access Token TTC:"))
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Nhập token tuongtaccheo.com...")
        h_token.addWidget(self.input_token)
        layout_info.addLayout(h_token)

        # Cookie
        h_cookie = QHBoxLayout()
        h_cookie.addWidget(QLabel("Cookie Facebook:"))
        self.input_cookie = QLineEdit()
        self.input_cookie.setPlaceholderText("Nhập cookie full quyền...")
        self.btn_get_pages = QPushButton("Lấy Page")
        self.btn_get_pages.clicked.connect(self.fetch_pages)
        h_cookie.addWidget(self.input_cookie)
        h_cookie.addWidget(self.btn_get_pages)
        layout_info.addLayout(h_cookie)

        group_info.setLayout(layout_info)
        main_layout.addWidget(group_info)

        # --- Cấu Hình Chạy ---
        group_config = QGroupBox("CẤU HÌNH CHẠY")
        layout_config = QHBoxLayout()

        # Chọn Page
        layout_config.addWidget(QLabel("Chọn Page:"))
        self.combo_pages = QComboBox()
        self.combo_pages.setEnabled(False)
        layout_config.addWidget(self.combo_pages)

        # Loại Job
        layout_config.addWidget(QLabel("|   Loại Job:"))
        self.combo_job = QComboBox()
        self.combo_job.addItems(["Follow", "Cảm Xúc", "Tham Gia Nhóm", "Tất cả (Mix)"])
        self.combo_job.setCurrentIndex(3) # Default Mix
        layout_config.addWidget(self.combo_job)

        # Delay
        layout_config.addWidget(QLabel("|   Delay (s):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 60)
        self.spin_delay.setValue(5)
        layout_config.addWidget(self.spin_delay)

        group_config.setLayout(layout_config)
        main_layout.addWidget(group_config)

        # --- Nút Điều Khiển ---
        layout_btn = QHBoxLayout()
        self.btn_start = QPushButton("▶ BẮT ĐẦU CHẠY")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.clicked.connect(self.start_job)
        
        self.btn_stop = QPushButton("⏹ DỪNG LẠI")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.clicked.connect(self.stop_job)

        layout_btn.addWidget(self.btn_start)
        layout_btn.addWidget(self.btn_stop)
        main_layout.addLayout(layout_btn)

        # --- Log ---
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        main_widget.setLayout(main_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sẵn sàng hoạt động.")

    def apply_fonts(self):
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        log_font = QFont("Consolas", 9)
        self.log_area.setFont(log_font)

    def append_log(self, text, color="#ffffff"):
        time_str = datetime.now().strftime("%H:%M:%S")
        formatted_text = f'<span style="color:gray">[{time_str}]</span> <span style="color:{color}">{text}</span>'
        self.log_area.append(formatted_text)
        # Auto scroll
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_status(self, text):
        self.status_bar.showMessage(text)

    def fetch_pages(self):
        token = self.input_token.text().strip()
        cookie = self.input_cookie.text().strip()
        
        if not token or not cookie:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Token và Cookie!")
            return
        
        self.append_log("Đang lấy danh sách Page...", "#ffff00")
        # Set data to worker to just fetch pages
        self.worker.set_credentials(token, cookie)
        self.worker.load_pages()

    def populate_pages(self, nodes):
        self.combo_pages.clear()
        for page in nodes:
            uid = page['profile']['id']
            name = page['profile']['name']
            self.combo_pages.addItem(f"{name} (ID: {uid})", uid)
        
        self.combo_pages.setEnabled(True)
        self.append_log(f"Đã tải {len(nodes)} Page.", "#00ff00")

    def start_job(self):
        if self.combo_pages.count() == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có Page nào được chọn!")
            return

        self.worker.token = self.input_token.text().strip()
        self.worker.cookie_fb = self.input_cookie.text().strip()
        self.worker.id_page = self.combo_pages.currentData()
        self.worker.job_type = self.combo_job.currentIndex() + 1 # 1, 2, 3, 4
        self.worker.delay = self.spin_delay.value()

        if not self.worker.set_credentials(self.worker.token, self.worker.cookie_fb):
            return

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.input_token.setEnabled(False)
        self.input_cookie.setEnabled(False)
        self.btn_get_pages.setEnabled(False)
        self.combo_pages.setEnabled(False)
        
        self.append_log("------------------------------------------------", "#ffffff")
        self.append_log("BẮT ĐẦU QUÁ TRÌNH CHẠY...", "#00ffcc")
        self.worker.start()

    def stop_job(self):
        self.append_log("Đang dừng...", "#ffff00")
        self.worker.stop()

    def on_job_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.input_token.setEnabled(True)
        self.input_cookie.setEnabled(True)
        self.btn_get_pages.setEnabled(True)
        self.combo_pages.setEnabled(True)
        self.append_log("ĐÃ DỪNG HOÀN TẤT.", "#ff3333")
        self.update_status("Đã dừng.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Cài đặt hỗ trợ màn hình nét cao (High DPI)
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())