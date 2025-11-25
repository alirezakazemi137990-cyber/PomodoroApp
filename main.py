import os
import csv
import configparser
from datetime import datetime, timedelta
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import FadeTransition 
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget
from plyer import notification
from kivymd.uix.label import MDLabel  
from kivymd.uix.card import MDCard     
from kivymd.uix.textfield import MDTextField 

# ==========================================
# 1. طراحی رابط کاربری (KV Layout)
# ==========================================
KV = '''
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

<DrawerClickableItem@MDNavigationDrawerItem>
    focus_color: "#e7e4c0"
    text_color: "#4a4939"
    icon_color: "#4a4939"
    ripple_color: "#c5bdd2"
    selected_color: "#0c6c4d"

<HomeScreen>:
    name: "home"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)

        # --- Header ---
        MDBoxLayout:
            adaptive_height: True
            orientation: 'vertical'
            MDLabel:
                text: root.greeting_text
                font_style: "H5"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                halign: "center"
            MDLabel:
                text: root.user_title_text
                font_style: "Caption"
                theme_text_color: "Secondary"
                halign: "center"

        # --- Task Input ---
        MDTextField:
            id: task_input
            hint_text: "Task Name"
            mode: "rectangle"
            # فونت‌های فارسی حذف شدند تا از فونت پیش‌فرض استفاده شود

        # --- Timer Display ---
        MDLabel:
            text: root.timer_text
            font_style: "H2"
            halign: "center"
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color if root.is_work_time else (0, 0.8, 0, 1)

        # --- Progress ---
        MDProgressBar:
            id: progress
            value: root.progress_value
            color: app.theme_cls.primary_color if root.is_work_time else (0, 0.8, 0, 1)

        MDLabel:
            text: root.status_text
            halign: "center"
            theme_text_color: "Secondary"
            font_style: "Subtitle1"

        MDLabel:
            text: root.cycle_text
            halign: "center"
            theme_text_color: "Hint"
            font_style: "Caption"

        # --- Controls ---
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(20)
            pos_hint: {"center_x": .5}
            
            MDIconButton:
                icon: "refresh"
                on_release: root.reset_timer()
                
            MDFillRoundFlatButton:
                id: btn_start
                text: "START" if not root.timer_running else "PAUSE"
                font_size: "18sp"
                size_hint_x: 0.5
                on_release: root.toggle_timer()
                md_bg_color: app.theme_cls.primary_color if not root.timer_running else (1, 0.6, 0, 1)

            MDIconButton:
                icon: "skip-next"
                disabled: not root.timer_running
                on_release: root.finish_early()

        # --- Bottom Navigation (Manual Buttons) ---
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(10)
            padding: [0, dp(20), 0, 0]
            
            MDIconButton:
                icon: "cog"
                disabled: root.timer_running
                text_color: app.theme_cls.disabled_hint_text_color if root.timer_running else app.theme_cls.primary_color
                on_release: app.switch_screen("settings")

            MDLabel:
                text: "" # Spacer

            MDIconButton:
                icon: "chart-bar"
                disabled: root.timer_running
                text_color: app.theme_cls.disabled_hint_text_color if root.timer_running else app.theme_cls.primary_color
                on_release: app.switch_screen("stats")

            MDLabel:
                text: "" # Spacer

            MDIconButton:
                icon: "account"
                disabled: root.timer_running
                text_color: app.theme_cls.disabled_hint_text_color if root.timer_running else app.theme_cls.primary_color
                on_release: app.switch_screen("profile")

<SettingsScreen>:
    name: "settings"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        
        MDLabel:
            text: "Settings"
            font_style: "H5"
            halign: "center"
            
        MDTextField:
            id: work_min
            hint_text: "Work Duration (min)"
            input_filter: "int"
            text: str(app.config_engine.work_min)
            
        MDTextField:
            id: short_break
            hint_text: "Short Break (min)"
            input_filter: "int"
            text: str(app.config_engine.short_break_min)
            
        MDTextField:
            id: long_break
            hint_text: "Long Break (min)"
            input_filter: "int"
            text: str(app.config_engine.long_break_min)

        MDLabel:
            text: "Theme Color"
            theme_text_color: "Secondary"
        
        ScrollView:
            MDList:
                id: theme_list

        MDRaisedButton:
            text: "SAVE & RETURN"
            pos_hint: {"center_x": .5}
            on_release: root.save_settings()

<StatsScreen>:
    name: "stats"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        
        MDLabel:
            text: "Analytics"
            font_style: "H5"
            halign: "center"
            size_hint_y: None
            height: dp(50)

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(10)
            padding: dp(10)
            
            MDRectangleFlatButton:
                text: "Daily"
                on_release: root.load_stats("Daily")
            MDRectangleFlatButton:
                text: "Weekly"
                on_release: root.load_stats("Weekly")
            MDRectangleFlatButton:
                text: "Monthly"
                on_release: root.load_stats("Monthly")

        # Summary Cards
        MDBoxLayout:
            adaptive_height: True
            padding: dp(5)
            spacing: dp(5)
            
            # کارت 1: زمان کل
            MDCard:
                orientation: "vertical"
                padding: dp(5)
                size_hint: 0.33, None
                height: dp(80)
                radius: [15]
                MDLabel:
                    id: lbl_total_time
                    text: "0h 0m"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                MDLabel:
                    text: "Total Focus"
                    halign: "center"
                    font_style: "Overline"
            
            # کارت 2: سشن‌های کامل
            MDCard:
                orientation: "vertical"
                padding: dp(5)
                size_hint: 0.33, None
                height: dp(80)
                radius: [15]
                MDLabel:
                    id: lbl_sessions
                    text: "0"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 0, 0.7, 0, 1
                MDLabel:
                    text: "Completed"
                    halign: "center"
                    font_style: "Overline"

            # کارت 3: سشن‌های اسکیپ شده
            MDCard:
                orientation: "vertical"
                padding: dp(5)
                size_hint: 0.33, None
                height: dp(80)
                radius: [15]
                MDLabel:
                    id: lbl_skipped
                    text: "0"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 0.6, 0, 1
                MDLabel:
                    text: "Skipped"
                    halign: "center"
                    font_style: "Overline"

        ScrollView:
            MDBoxLayout:
                id: stats_list
                orientation: 'vertical'
                adaptive_height: True
                padding: [dp(10), dp(10)]
                spacing: dp(15)

        MDRaisedButton:
            text: "BACK"
            pos_hint: {"center_x": .5}
            on_release: app.switch_screen("home")

<ProfileScreen>:
    name: "profile"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)

        Widget: 
        
        MDCard:
            orientation: "vertical"
            size_hint: None, None
            size: dp(320), dp(400)
            pos_hint: {"center_x": .5, "center_y": .5}
            elevation: 4
            padding: dp(25)
            spacing: dp(20)
            radius: [20, 20, 20, 20]

            MDLabel:
                text: "User Profile"
                font_style: "H5"
                halign: "center"
                theme_text_color: "Primary"
                size_hint_y: None
                height: dp(40)

            MDIcon:
                icon: "account-circle"
                halign: "center"
                font_size: "80sp"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                size_hint_y: None
                height: dp(100)

            MDTextField:
                id: user_name
                hint_text: "Display Name"
                text: app.config_engine.user_name
                icon_right: "account-edit"
                mode: "fill"
            
            MDTextField:
                id: user_title
                hint_text: "Job Title / Tagline"
                text: app.config_engine.user_title
                icon_right: "briefcase-edit"
                mode: "fill"

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(20)
            pos_hint: {"center_x": .5}
            padding: [0, dp(20), 0, 0]

            MDFlatButton:
                text: "CANCEL"
                text_color: 1, 0, 0, 1
                on_release: app.switch_screen("home")
            
            MDRaisedButton:
                text: "SAVE PROFILE"
                elevation: 2
                on_release: root.save_profile()

        Widget: 

<SettingsScreen>:
    name: "settings"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        
        MDLabel:
            text: "Settings"
            font_style: "H5"
            halign: "center"
            
        MDTextField:
            id: work_min
            hint_text: "Work Duration (min)"
            input_filter: "int"
            text: str(app.config_engine.work_min)
            
        MDTextField:
            id: short_break
            hint_text: "Short Break (min)"
            input_filter: "int"
            text: str(app.config_engine.short_break_min)
            
        MDTextField:
            id: long_break
            hint_text: "Long Break (min)"
            input_filter: "int"
            text: str(app.config_engine.long_break_min)

        MDLabel:
            text: "Theme Color"
            theme_text_color: "Secondary"
        
        ScrollView:
            MDList:
                id: theme_list

        MDRaisedButton:
            text: "SAVE & RETURN"
            pos_hint: {"center_x": .5}
            on_release: root.save_settings()

<StatsScreen>:
    name: "stats"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        
        MDLabel:
            text: "Analytics"
            font_style: "H5"
            halign: "center"
            size_hint_y: None
            height: dp(50)

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(10)
            padding: dp(10)
            
            MDRectangleFlatButton:
                text: "Daily"
                on_release: root.load_stats("Daily")
            MDRectangleFlatButton:
                text: "Weekly"
                on_release: root.load_stats("Weekly")
            MDRectangleFlatButton:
                text: "Monthly"
                on_release: root.load_stats("Monthly")

        # Summary Cards
        MDBoxLayout:
            adaptive_height: True
            padding: dp(5)
            spacing: dp(5)
            
            # کارت 1: زمان کل
            MDCard:
                orientation: "vertical"
                padding: dp(5)
                size_hint: 0.33, None
                height: dp(80)
                radius: [15]
                MDLabel:
                    id: lbl_total_time
                    text: "0h 0m"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                MDLabel:
                    text: "Total Focus"
                    halign: "center"
                    font_style: "Overline"
            
            # کارت 2: سشن‌های کامل
            MDCard:
                orientation: "vertical"
                padding: dp(5)
                size_hint: 0.33, None
                height: dp(80)
                radius: [15]
                MDLabel:
                    id: lbl_sessions
                    text: "0"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 0, 0.7, 0, 1
                MDLabel:
                    text: "Completed"
                    halign: "center"
                    font_style: "Overline"

            # کارت 3: سشن‌های اسکیپ شده (جدید)
            MDCard:
                orientation: "vertical"
                padding: dp(5)
                size_hint: 0.33, None
                height: dp(80)
                radius: [15]
                MDLabel:
                    id: lbl_skipped
                    text: "0"
                    halign: "center"
                    bold: True
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 0.6, 0, 1
                MDLabel:
                    text: "Skipped"
                    halign: "center"
                    font_style: "Overline"

        ScrollView:
            MDBoxLayout:
                id: stats_list
                orientation: 'vertical'
                adaptive_height: True
                padding: [dp(10), dp(10)]
                spacing: dp(15)

        MDRaisedButton:
            text: "BACK"
            pos_hint: {"center_x": .5}
            on_release: app.switch_screen("home")

<ProfileScreen>:
    name: "profile"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)

        # فضای خالی بالا برای هل دادن کارت به وسط
        Widget: 
        
        MDCard:
            orientation: "vertical"
            size_hint: None, None
            size: dp(320), dp(400)
            pos_hint: {"center_x": .5, "center_y": .5}
            elevation: 4
            padding: dp(25)
            spacing: dp(20)
            radius: [20, 20, 20, 20]

            MDLabel:
                text: "User Profile"
                font_style: "H5"
                halign: "center"
                theme_text_color: "Primary"
                size_hint_y: None
                height: dp(40)

            # آواتار بزرگ
            MDIcon:
                icon: "account-circle"
                halign: "center"
                font_size: "80sp"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                size_hint_y: None
                height: dp(100)

            MDTextField:
                id: user_name
                hint_text: "Display Name"
                text: app.config_engine.user_name
                icon_right: "account-edit"
                mode: "fill"
            
            MDTextField:
                id: user_title
                hint_text: "Job Title / Tagline"
                text: app.config_engine.user_title
                icon_right: "briefcase-edit"
                mode: "fill"

        # دکمه‌ها پایین صفحه
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(20)
            pos_hint: {"center_x": .5}
            padding: [0, dp(20), 0, 0]

            MDFlatButton:
                text: "CANCEL"
                text_color: 1, 0, 0, 1
                on_release: app.switch_screen("home")
            
            MDRaisedButton:
                text: "SAVE PROFILE"
                elevation: 2
                on_release: root.save_profile()

        Widget: # فضای خالی پایین


'''

# ==========================================
# 2. منطق برنامه (Logic Engine)
# ==========================================
class PomodoroConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        
        # --- تشخیص مسیر ذخیره‌سازی (سازگار با اندروید و ویندوز) ---
        from kivy.utils import platform
        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            self.data_dir = activity.getFilesDir().getAbsolutePath() + '/'
        else:
            # در ویندوز کنار فایل برنامه ذخیره شود
            self.data_dir = os.path.dirname(os.path.abspath(__file__))

        # تنظیم مسیر فایل‌های کانفیگ و تاریخچه
        self.filename = os.path.join(self.data_dir, 'config.ini')
        self.history_file = os.path.join(self.data_dir, 'pomodoro_history.csv')
        # -------------------------------------------------------
        
        self._load_config()

    def _load_config(self):
        # اگر فایل نبود، تنظیمات پیش‌فرض را بساز
        if not os.path.exists(self.filename):
            self.config['SETTINGS'] = {
                'work_minutes': '25',
                'short_break': '5',
                'long_break': '15',
                'cycles': '4',
                'theme_accent': 'Blue',
                'theme_bg': 'Dark'
            }
            self.config['USER'] = {
                'name': 'Dr. Kazemi',
                'title': 'Physician & Inventor'
            }
            with open(self.filename, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(self.filename)
            if 'USER' not in self.config:
                self.config['USER'] = {'name': 'User', 'title': 'Dreamer'}

        self.work_min = int(self.config['SETTINGS'].get('work_minutes', 25))
        self.short_break_min = int(self.config['SETTINGS'].get('short_break', 5))
        self.long_break_min = int(self.config['SETTINGS'].get('long_break', 15))
        self.cycles_limit = int(self.config['SETTINGS'].get('cycles', 4))
        self.current_accent = self.config['SETTINGS'].get('theme_accent', 'Blue')
        self.user_name = self.config['USER'].get('name', 'User')
        self.user_title = self.config['USER'].get('title', 'Dreamer')

    def log_session(self, session_type, duration_minutes, task_name="General"):
        # استفاده از self.history_file به جای نام ثابت
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_exists = os.path.isfile(self.history_file)
        try:
            with open(self.history_file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists: writer.writerow(["Date", "Type", "Duration (min)", "Task"])
                writer.writerow([now, session_type, duration_minutes, task_name])
        except Exception as e:
            print(f"Log Error: {e}")

    def get_chart_data(self, timeframe="Daily"):
        if not os.path.exists(self.history_file): 
            return {"bar_data": [], "pie_data": {}, "total_count": 0, "skipped_count": 0, "total_mins": 0}

        grand_total_mins = 0
        grand_total_count = 0 # فقط سشن‌های کامل
        skipped_count = 0      # سشن‌های اسکیپ شده
        
        # ساختار داده برای نمودار میله‌ای و دایره‌ای
        timeline_data = {} 
        task_distribution = {}

        now = datetime.now()
        labels = []
        
        # تنظیم بازه زمانی
        if timeframe == "Daily":
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                key = day.strftime("%Y-%m-%d")
                label = day.strftime("%a") 
                timeline_data[key] = {} 
                labels.append((key, label))
        
        elif timeframe == "Weekly":
            for i in range(3, -1, -1):
                week_start = now - timedelta(weeks=i)
                key = week_start.strftime("%U")
                label = f"W{key}"
                timeline_data[key] = {}
                labels.append((key, label))

        elif timeframe == "Monthly":
            for i in range(5, -1, -1):
                current_month = now.month - i
                current_year = now.year
                if current_month <= 0:
                    current_month += 12
                    current_year -= 1
                month_date = now.replace(year=current_year, month=current_month, day=1)
                key = month_date.strftime("%Y-%m")
                label = month_date.strftime("%b")
                timeline_data[key] = {}
                labels.append((key, label))

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 4: continue
                    session_type = row[1]
                    
                    # فقط کارهایی که با Work شروع می‌شوند (شامل Work و Work (Early))
                    if not session_type.startswith("Work"): continue
                    
                    try:
                        date_str = row[0].split(" ")[0]
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        duration = int(row[2])
                        task_name = row[3] if row[3] else "General"
                    except: continue
                    
                    # جداسازی منطق شمارش
                    if session_type == "Work":
                        grand_total_count += 1 # فقط کامل‌ها
                    else:
                        skipped_count += 1     # اسکیپ شده‌ها (Work (Early))

                    grand_total_mins += duration
                    
                    # داده‌های نمودار دایره‌ای
                    task_distribution[task_name] = task_distribution.get(task_name, 0) + duration

                    # کلید زمانی
                    key = ""
                    if timeframe == "Daily": key = date_str
                    elif timeframe == "Weekly": key = dt.strftime("%U")
                    elif timeframe == "Monthly": key = dt.strftime("%Y-%m")

                    # داده‌های نمودار میله‌ای
                    if key in timeline_data:
                        timeline_data[key][task_name] = timeline_data[key].get(task_name, 0) + duration

        except Exception as e:
            print(f"Error reading stats: {e}")

        # تبدیل به لیست نهایی برای رسم
        bar_chart_data = []
        for key, display_label in labels:
            day_tasks = timeline_data.get(key, {})
            total_day_time = sum(day_tasks.values())
            bar_chart_data.append({
                "label": display_label,
                "total": total_day_time,
                "details": day_tasks
            })

        return {
            "bar_data": bar_chart_data,
            "pie_data": task_distribution,
            "total_count": grand_total_count,
            "skipped_count": skipped_count,
            "total_mins": grand_total_mins
        }


    def save_config(self):
        self.config['SETTINGS']['work_minutes'] = str(self.work_min)
        self.config['SETTINGS']['short_break'] = str(self.short_break_min)
        self.config['SETTINGS']['long_break'] = str(self.long_break_min)
        self.config['SETTINGS']['theme_accent'] = self.current_accent
        self.config['USER']['name'] = self.user_name
        self.config['USER']['title'] = self.user_title
        
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)


# ==========================================
# 3. کلاس‌های صفحات (Screens)
# ==========================================
class HomeScreen(MDScreen):
    timer_text = StringProperty("00:00")
    status_text = StringProperty("Ready to Focus?")
    greeting_text = StringProperty("")
    user_title_text = StringProperty("")
    cycle_text = StringProperty("Cycle: 0/4")
    progress_value = NumericProperty(0)
    timer_running = BooleanProperty(False)
    is_work_time = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clock_event = None
        self.app = MDApp.get_running_app()
        self.cfg = self.app.config_engine
        self.reset_state()

    def on_enter(self):
        # حذف f()
        self.greeting_text = f"Hi, {self.cfg.user_name}"
        self.user_title_text = self.cfg.user_title
        current = self.cycles_completed + 1 if self.cycles_completed < self.cfg.cycles_limit else self.cfg.cycles_limit
        self.cycle_text = f"Cycle: {current}/{self.cfg.cycles_limit}"

    def reset_state(self):
        self.timer_running = False
        self.is_work_time = True
        self.cycles_completed = 0
        self.time_left = self.cfg.work_min * 60
        self.total_time_session = self.time_left
        self.update_display_time()
        self.progress_value = 0
        self.status_text = "Ready to Focus?"
        self.cycle_text = f"Cycle: 1/{self.cfg.cycles_limit}"
        if self.clock_event: self.clock_event.cancel()
        self.ids.task_input.text = ""
        self.ids.task_input.error = False

    def update_display_time(self):
        mins, secs = divmod(self.time_left, 60)
        self.timer_text = f"{mins:02d}:{secs:02d}"

    def toggle_timer(self):
        raw_task = self.ids.task_input.text.strip()
        
        if not raw_task:
            self.ids.task_input.error = True
            return
        self.ids.task_input.error = False

        if not self.timer_running:
            self.timer_running = True
            self.clock_event = Clock.schedule_interval(self.update_clock, 1)
            self.status_text = "Focusing..."
        else:
            self.timer_running = False
            if self.clock_event: self.clock_event.cancel()
            self.status_text = "Paused"

    def update_clock(self, dt):
        if self.time_left > 0:
            self.time_left -= 1
            self.update_display_time()
            elapsed = self.total_time_session - self.time_left
            self.progress_value = (elapsed / self.total_time_session) * 100
        else:
            self.finish_session()

    def finish_early(self):
        if not self.timer_running: return
        elapsed_seconds = self.total_time_session - self.time_left
        elapsed_minutes = int(elapsed_seconds / 60) 
        if elapsed_minutes < 1: elapsed_minutes = 1
        self.finish_session(manual_duration=elapsed_minutes, is_early=True)

    def finish_session(self, manual_duration=None, is_early=False):
        self.timer_running = False
        if self.clock_event: self.clock_event.cancel()
        self.progress_value = 100 if not is_early else self.progress_value
        
        try:
            notification.notify(title="PomoPulse", message="Session Ended", timeout=5)
        except: pass

        task_name = self.ids.task_input.text.strip() or "General"
        duration_to_log = manual_duration if manual_duration is not None else self.cfg.work_min

        if self.is_work_time:
            session_type = "Work (Early)" if is_early else "Work"
            self.cfg.log_session(session_type, duration_to_log, task_name)
            
            self.cycles_completed += 1
            
            if self.cycles_completed >= self.cfg.cycles_limit:
                self.status_text = "Long Break! 🎉"
                self.time_left = self.cfg.long_break_min * 60
                self.cycles_completed = 0 
            else:
                self.status_text = "Short Break ☕"
                self.time_left = self.cfg.short_break_min * 60
            self.is_work_time = False
        else:
            self.status_text = "Back to Work! 🚀"
            self.time_left = self.cfg.work_min * 60
            self.is_work_time = True
            current_cycle = self.cycles_completed + 1
            self.cycle_text = f"Cycle: {current_cycle}/{self.cfg.cycles_limit}"

        self.total_time_session = self.time_left
        self.update_display_time()
        if not is_early: self.progress_value = 0



class SettingsScreen(MDScreen):
    def on_enter(self):
        app = MDApp.get_running_app()
        # پر کردن لیست رنگ‌ها
        colors = ["Blue", "Red", "Green", "Orange", "Purple", "Teal"]
        self.ids.theme_list.clear_widgets()
        for color in colors:
            item = OneLineAvatarIconListItem(text=color, on_release=lambda x, c=color: self.set_theme(c))
            icon = IconLeftWidget(icon="circle", theme_text_color="Custom", text_color=app.theme_cls.colors[color]["500"])
            item.add_widget(icon)
            self.ids.theme_list.add_widget(item)

    def set_theme(self, color_name):
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = color_name
        app.config_engine.current_accent = color_name

    def save_settings(self):
        app = MDApp.get_running_app()
        try:
            app.config_engine.work_min = int(self.ids.work_min.text)
            app.config_engine.short_break_min = int(self.ids.short_break.text)
            app.config_engine.long_break_min = int(self.ids.long_break.text)
            app.config_engine.save_config()
            
            # ریست کردن تایمر با مقادیر جدید
            home_screen = app.root.get_screen("home")
            home_screen.reset_state()
            app.switch_screen("home")
        except ValueError:
            pass


class StatsScreen(MDScreen):
    colors = [
        (0.29, 0.66, 0.95, 1), (0.96, 0.66, 0.26, 1), (0.37, 0.73, 0.54, 1), 
        (0.91, 0.34, 0.34, 1), (0.62, 0.45, 0.81, 1), (0.4, 0.4, 0.4, 1)
    ]

    def get_color(self, index):
        return self.colors[index % len(self.colors)]

    def format_time(self, minutes):
        if minutes == 0: return ""
        h, m = divmod(int(minutes), 60)
        if h > 0 and m > 0: return f"{h}h {m}m"
        if h > 0: return f"{h}h"
        return f"{m}m"

    def on_enter(self):
        self.load_stats("Daily")

    def load_stats(self, timeframe):
        app = MDApp.get_running_app()
        data = app.config_engine.get_chart_data(timeframe)
        
        self.ids.stats_list.clear_widgets()

        # --- بخش 1: کارت‌های خلاصه ---
        total_mins = data["total_mins"]
        h, m = divmod(total_mins, 60)
        self.ids.lbl_total_time.text = f"{h}h {m}m"
        self.ids.lbl_sessions.text = str(data["total_count"])
        self.ids.lbl_skipped.text = str(data["skipped_count"]) 
        
        if not data["bar_data"] or total_mins == 0:
            self.ids.stats_list.add_widget(MDLabel(
                text="No data available for this period.", 
                halign="center", 
                theme_text_color="Secondary"
            ))
            return

        # --- بخش 2: نمودار میله‌ای ---
        chart_card = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(10), padding=[0, 0, 0, dp(20)])
        chart_card.add_widget(MDLabel(text="Activity Over Time", font_style="Subtitle2", theme_text_color="Secondary"))

        max_val = max((d['total'] for d in data["bar_data"]), default=60)
        if max_val == 0: max_val = 60

        chart_body = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(220), spacing=dp(5))

        # محور Y
        y_axis = MDBoxLayout(orientation="vertical", size_hint_x=None, width=dp(35), spacing=0)
        y_axis.add_widget(MDLabel(text=self.format_time(max_val), font_style="Caption", theme_text_color="Hint", halign="right", valign="top"))
        y_axis.add_widget(MDBoxLayout())
        y_axis.add_widget(MDLabel(text=self.format_time(max_val/2), font_style="Caption", theme_text_color="Hint", halign="right", valign="center"))
        y_axis.add_widget(MDBoxLayout())
        y_axis.add_widget(MDLabel(text="0m", font_style="Caption", theme_text_color="Hint", halign="right", valign="bottom"))
        y_axis.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20))) 
        chart_body.add_widget(y_axis)

        # ترسیم میله‌ها
        bars_layout = MDBoxLayout(orientation="horizontal", spacing=dp(10), padding=[dp(10), 0, 0, 0])
        unique_tasks = list(data["pie_data"].keys())
        task_color_map = {task: self.get_color(i) for i, task in enumerate(unique_tasks)}

        for day_data in data["bar_data"]:
            col = MDBoxLayout(orientation="vertical", size_hint_x=1)
            total_day_time = day_data['total']
            fill_percent = (total_day_time / max_val) if max_val > 0 else 0

            col.add_widget(MDBoxLayout(size_hint_y=1.0 - fill_percent)) 
            bar_container = MDBoxLayout(orientation="vertical", size_hint_y=fill_percent) 
            
            if total_day_time > 0:
                bar_container.add_widget(MDLabel(text=self.format_time(total_day_time), halign="center", theme_text_color="Primary", font_style="Overline", size_hint_y=None, height=dp(15)))
                segments_wrapper = MDBoxLayout(orientation="vertical")
                for task, duration in day_data["details"].items():
                    segment_percent = duration / total_day_time
                    color = task_color_map.get(task, self.get_color(len(unique_tasks)))
                    segment = MDBoxLayout(size_hint_y=segment_percent, md_bg_color=color)
                    segments_wrapper.add_widget(segment)
                bar_container.add_widget(segments_wrapper)

            col.add_widget(bar_container)
            col.add_widget(MDLabel(text=day_data['label'], halign="center", theme_text_color="Secondary", font_style="Caption", size_hint_y=None, height=dp(20))) 
            bars_layout.add_widget(col)

        chart_body.add_widget(bars_layout)
        chart_card.add_widget(chart_body)
        self.ids.stats_list.add_widget(chart_card)

        # --- بخش 3: راهنمای رنگ‌ها ---
        pie_container = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(15), padding=[0, dp(20), 0, 0])
        pie_container.add_widget(MDLabel(text="Color Guide & Details", font_style="Subtitle2", theme_text_color="Secondary"))
        
        sorted_tasks = sorted(data["pie_data"].items(), key=lambda x: x[1], reverse=True)
        grand_total = sum(data["pie_data"].values()) or 1

        for task, duration in sorted_tasks:
            percent = (duration / grand_total) * 100
            color = task_color_map.get(task, self.get_color(len(unique_tasks)))
            
            row = MDBoxLayout(adaptive_height=True, spacing=dp(15), padding=[0, dp(5), 0, dp(5)])
            icon = MDIconButton(icon="checkbox-blank-circle", theme_text_color="Custom", text_color=color, size_hint=(None, None), size=(dp(30), dp(30)), ripple_scale=0)
            row.add_widget(icon)
            
            info_box = MDBoxLayout(orientation="vertical", adaptive_height=True, pos_hint={"center_y": .5}, spacing=dp(6))
            top_line = MDBoxLayout(adaptive_height=True)
            
            # حذف f() و شرط فونت
            top_line.add_widget(MDLabel(text=task, font_style="Body2", bold=True))
            
            top_line.add_widget(MDLabel(text=f"{int(percent)}% ({self.format_time(duration)})", halign="right", theme_text_color="Secondary", font_style="Caption"))
            info_box.add_widget(top_line)
            
            pb = MDProgressBar(value=percent, color=color, size_hint_y=None, height=dp(6))
            info_box.add_widget(pb)
            row.add_widget(info_box)
            pie_container.add_widget(row)

        self.ids.stats_list.add_widget(pie_container)


class ProfileScreen(MDScreen):
    def save_profile(self):
        app = MDApp.get_running_app()
        app.config_engine.user_name = self.ids.user_name.text
        app.config_engine.user_title = self.ids.user_title.text
        app.config_engine.save_config()
        app.switch_screen("home")

# ==========================================
# 4. کلاس اصلی اپلیکیشن
# ==========================================
class PomoPulseApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.config_engine = PomodoroConfig()
        
        try:
            self.theme_cls.primary_palette = self.config_engine.current_accent
        except:
            self.theme_cls.primary_palette = "Blue"

        self.sm = MDScreenManager(transition=FadeTransition())
        Builder.load_string(KV)
        
        self.sm.add_widget(HomeScreen())
        self.sm.add_widget(SettingsScreen())
        self.sm.add_widget(StatsScreen())
        self.sm.add_widget(ProfileScreen())
        
        return self.sm


    def switch_screen(self, screen_name):
        self.sm.current = screen_name

if __name__ == '__main__':
    PomoPulseApp().run()
