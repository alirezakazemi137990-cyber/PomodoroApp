import os
import csv
import configparser
import random
import threading
from datetime import datetime, timedelta
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.screenmanager import FadeTransition
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDFlatButton, MDIconButton, MDFillRoundFlatButton, MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget
from plyer import notification, vibrator
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivymd.uix.menu import MDDropdownMenu
# --- وارد کردن کتابخانه‌های صدا ---
try:
    import winsound
except ImportError:
    winsound = None

# --- وارد کردن کتابخانه‌های اندروید برای Wake Lock ---
if platform == 'android':
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread

# ==========================================
# 1. طراحی رابط کاربری (KV Layout)
# ==========================================
KV = '''
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

<HomeScreen>:
    name: "home"
    MDBoxLayout:
        orientation: 'vertical'
        padding: [dp(20), dp(40), dp(20), dp(20)]
        spacing: dp(15)

        # --- 1. Hero Card (Gamification Profile) ---
        MDCard:
            size_hint_y: None
            height: dp(75)
            radius: [25,]
            padding: dp(15)
            md_bg_color: 0.15, 0.15, 0.15, 1
            elevation: 2

            MDIcon:
                icon: "trophy"
                pos_hint: {"center_y": .5}
                theme_text_color: "Custom"
                text_color: 1, 0.75, 0, 1  # Gold Color
                font_size: "36sp"

            MDBoxLayout:
                orientation: 'vertical'
                padding: [dp(15), 0, 0, 0]
                pos_hint: {"center_y": .5}

                MDLabel:
                    text: root.user_title_text
                    font_style: "H6"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    text: root.level_text
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.6, 0.6, 0.6, 1

        # --- 2. Task Input (Minimalist) ---
        MDTextField:
            id: task_input
            hint_text: "What is your mission?"
            mode: "line"
            line_color_focus: app.theme_cls.primary_color
            text_color_focus: 1, 1, 1, 1
            font_size: "18sp"
            halign: "center"

        # --- Spacer to push timer to center ---
        Widget:
            size_hint_y: 1

        # --- 3. Giant Timer (Center Piece) ---
        MDLabel:
            text: root.timer_text
            font_size: "110sp"  # سایز بسیار بزرگ
            halign: "center"
            valign: "center"
            bold: True
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color if root.is_work_time else (0, 0.9, 0.4, 1)

        MDLabel:
            text: root.status_text
            halign: "center"
            theme_text_color: "Hint"
            font_style: "Body1"

        # --- Spacer ---
        Widget:
            size_hint_y: 1

        # --- 4. Controls ---
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(15)
            pos_hint: {"center_x": .5}
            padding: [0, 0, 0, dp(30)]

            MDIconButton:
                icon: "restore"
                icon_size: "32sp"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
                on_release: root.reset_state()

            # --- دکمه صدا (اضافه شد تا از کرش جلوگیری شود) ---
            MDIconButton:
                id: btn_sound
                icon: "music-note-off"
                icon_size: "32sp"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
                on_release: root.open_sound_menu()

            MDFloatingActionButton:
                icon: "play" if not root.timer_running else "pause"
                type: "large"
                md_bg_color: app.theme_cls.primary_color if not root.timer_running else (1, 0.7, 0, 1)
                on_release: root.toggle_timer()

            MDIconButton:
                icon: "skip-next"
                icon_size: "32sp"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
                on_release: root.finish_early()

        # --- 5. Bottom Nav (Minimal) ---
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(10)
            
            MDIconButton:
                icon: "cog-outline"
                on_release: app.switch_screen("settings")
            
            Widget: # Spacer
            
            MDIconButton:
                icon: "chart-bar"
                on_release: app.switch_screen("stats")
            
            Widget: # Spacer
            
            MDIconButton:
                icon: "account-circle-outline"
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
                mode: "line"

            MDTextField:
                id: user_title
                hint_text: "Job Title / Tagline"
                text: app.config_engine.user_title
                icon_right: "briefcase-edit"
                mode: "line"

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
'''
# ==========================================
# Gamification Engine (Hero's Journey)
# ==========================================
class GamificationEngine:
    """موتور محاسبه XP و سطح کاربر بر اساس تاریخچه پومودورو"""
    def __init__(self, history_file):
        self.history_file = history_file
        self.levels = [
            (0,     300,  "The Starter"),
            (300,   1200, "The Believer"),
            (1200,  3000, "The Warrior"),
            (3000,  6000, "The Master"),
            (6000,  None, "The Legend")
        ]

    def get_total_xp(self):
        """مجموع دقیقه‌های کار (XP) از تاریخچه را برمی‌گرداند"""
        total = 0
        if not os.path.exists(self.history_file):
            return total
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if len(row) < 3:
                        continue
                    if row[1].startswith("Work"):
                        try:
                            total += int(row[2])
                        except ValueError:
                            pass
        except Exception as e:
            print(f"Error reading XP: {e}")
        return total

    def get_user_level(self):
        """سطح فعلی، لقب، XP باقی‌مانده و درصد پیشرفت را برمی‌گرداند"""
        xp = self.get_total_xp()
        for i, (min_xp, max_xp, title) in enumerate(self.levels):
            if max_xp is None:  # آخرین سطح
                prev_min = self.levels[i-1][0] if i > 0 else 0
                progress = 1.0
                xp_to_next = 0
                return i+1, title, prev_min, None, progress, xp_to_next
            if min_xp <= xp < max_xp:
                progress = (xp - min_xp) / (max_xp - min_xp)
                xp_to_next = max_xp - xp
                return i+1, title, min_xp, max_xp, progress, xp_to_next
        # اگر XP از آخرین سطح هم بیشتر باشد
        last_level = self.levels[-1]
        return len(self.levels), last_level[2], last_level[0], None, 1.0, 0

# ==========================================
# 2. منطق برنامه (Logic Engine)
# ==========================================
class PomodoroConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        
        # مسیر ذخیره‌سازی
        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            self.data_dir = activity.getFilesDir().getAbsolutePath() + '/'
        else:
            self.data_dir = os.path.dirname(os.path.abspath(__file__))

        self.filename = os.path.join(self.data_dir, 'config.ini')
        self.history_file = os.path.join(self.data_dir, 'pomodoro_history.csv')
        self.gamification = GamificationEngine(self.history_file)
        
        # --- لیست جملات انگیزشی ---
        self.quotes = [
            "Future Dr. Kazemi, keep pushing!",
            "Small steps every day.",
            "Focus is the key to success.",
            "You are building your dream.",
            "Don't stop until you're proud.",
            "Your potential is endless.",
            "Discipline over motivation.",
            "Make yourself proud today.",
            "Study hard, shine later.",
            "Success is a journey, not a destination."
        ]

        self._load_config()

    def _load_config(self):
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

    def get_random_quote(self):
        quotes = [
            "Focus is the new IQ. (Cal Newport)",
            "Where your attention goes, your life follows.",
            "Multitasking is a lie. Focus on one thing.",
            "Deep Work: Professional activities performed in a state of distraction-free concentration.",
            "Your brain is like a muscle. Train it.",
            "Flow state is the optimal experience.",
            "Discipline equals Freedom. (Jocko Willink)",
            "Amateurs sit and wait for inspiration, the rest of us just get up and go to work.",
            "Small habits make a big difference.",
            "Rest is part of the work."
        ]
        return random.choice(quotes)
    
    def log_session(self, session_type, duration_minutes, task_name="General"):
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
        grand_total_count = 0 
        skipped_count = 0      
        timeline_data = {}
        task_distribution = {}

        now = datetime.now()
        labels = []

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
                    if not session_type.startswith("Work"): continue

                    try:
                        date_str = row[0].split(" ")[0]
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        duration = int(row[2])
                        task_name = row[3] if row[3] else "General"
                    except: continue

                    if session_type == "Work":
                        grand_total_count += 1
                    else:
                        skipped_count += 1 

                    grand_total_mins += duration
                    task_distribution[task_name] = task_distribution.get(task_name, 0) + duration

                    key = ""
                    if timeframe == "Daily": key = date_str
                    elif timeframe == "Weekly": key = dt.strftime("%U")
                    elif timeframe == "Monthly": key = dt.strftime("%Y-%m")

                    if key in timeline_data:
                        timeline_data[key][task_name] = timeline_data[key].get(task_name, 0) + duration

        except Exception as e:
            print(f"Error reading stats: {e}")

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
    def get_user_level(self):
        """اطلاعات سطح کاربر را برمی‌گرداند"""
        return self.gamification.get_user_level()

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
    quote_text = StringProperty("") 
    cycle_text = StringProperty("Cycle: 0/4")
    progress_value = NumericProperty(0)
    timer_running = BooleanProperty(False)
    is_work_time = BooleanProperty(True)
    menu = None
    current_sound = None
    is_sound_playing = False
    is_playing_sound = BooleanProperty(False)
    level_text = StringProperty("Level 1: The Starter") 
    level_progress = NumericProperty(0)
    show_quote = BooleanProperty(False)
    current_task = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 1. متغیرهای تایمر
        self.timer_running = False
        self.is_work_time = True
        self.cycles_completed = 0
        self.timer_event = None
        self.time_left = 1500  # پیش‌فرض 25 دقیقه
        self.total_time_session = 1500
        self.end_time = None

        # 2. متغیرهای صدا
        self.sound = None
        self.current_sound = None
        self.sound_cache = {} 
        self.sound_file_map = {
            "Rain": "assets/sounds/rain.mp3",
            "Forest": "assets/sounds/forest.mp3",
            "Clock": "assets/sounds/clock.mp3"
        }
        self.current_sound_name = "Rain"
        self.quotes = [
            "Focus on being productive instead of busy.",
            "The only way to do great work is to love what you do.",
            "It always seems impossible until it's done.",
            "Don't watch the clock; do what it does. Keep going.",
            "Success is the sum of small efforts, repeated day in and day out."
        ]

        self.saved_tasks = []

        # 4. شروع لود صدا با تاخیر (برای حل مشکل صفحه سیاه)
        # این تابع 1 ثانیه بعد از اینکه صفحه بالا اومد اجرا میشه
        Clock.schedule_once(self.start_background_loading, 1)

    def on_enter(self):
        super().on_enter()  # فراخوانی متد پایه برای جلوگیری از AttributeError
        app = MDApp.get_running_app()
        self.greeting_text = f"Hi, {app.config_engine.user_name}"
        self.user_title_text = app.config_engine.user_title
        
        # استفاده از متغیر صحیح time_left
        start_min = app.config_engine.work_min if self.is_work_time else app.config_engine.short_break_min
        self.time_left = start_min * 60
        self.total_time_session = self.time_left
        
        self.update_display_time()
        if not hasattr(self, 'quotes'):
            self.quotes = [
                "Focus on being productive instead of busy.",
                "The only way to do great work is to love what you do.",
                "It always seems impossible until it's done.",
                "Don't watch the clock; do what it does. Keep going.",
                "Success is the sum of small efforts, repeated day in and day out."
            ]
        # فقط در صورت خالی بودن quote_text، یک نقل‌قول جدید انتخاب کن
        if not self.quote_text:
            self.quote_text = random.choice(self.quotes)

        self.cycle_text = f"Cycle: {self.cycles_completed}/{app.config_engine.cycles_limit}"
        self.update_level_display()
        
        # --- ساخت منوی انتخاب صدا ---
        sound_items = [
            {"viewclass": "OneLineListItem", "text": "Rain", "on_release": lambda x="Rain": self.set_sound(x)},
            {"viewclass": "OneLineListItem", "text": "Forest", "on_release": lambda x="Forest": self.set_sound(x)},
            {"viewclass": "OneLineListItem", "text": "Clock", "on_release": lambda x="Clock": self.set_sound(x)},
            {"viewclass": "OneLineListItem", "text": "OFF", "on_release": lambda x="OFF": self.set_sound(x)},
        ]
        self.sound_menu = MDDropdownMenu(
            caller=self.ids.btn_sound,
            items=sound_items,
            width_mult=2,
        )

    def start_background_loading(self, dt):
        """این تابع ۱ ثانیه بعد از لود شدن برنامه اجرا می‌شود"""
        threading.Thread(target=self.preload_sounds_background, daemon=True).start()
        
    def preload_sounds_background(self):
        """این تابع فایل‌ها را یواشکی در رم بارگذاری می‌کند"""
        for name, path in self.sound_file_map.items():
            if os.path.exists(path):
                try:
                    sound = SoundLoader.load(path)
                    if sound:
                        self.sound_cache[name] = sound
                        sound.seek(0) # ترفند برای پر کردن بافر اندروید
                except Exception as e:
                    print(f"Error preloading {name}: {e}")
        
    def open_sound_menu(self):
        self.sound_menu.open()

    def set_sound(self, sound_name):
        self.sound_menu.dismiss()
        self.current_sound_name = sound_name
        # اگر موزیک روشن است، آن را ریست کن تا صدای جدید پخش شود
        if self.is_playing_sound:
            self.stop_sound()
            if sound_name != "OFF":
                self.play_sound()
                
    # --- تغییر ۳: پخش هوشمند (بدون لگ) ---
    def play_sound(self):
        if self.current_sound_name == "OFF":
            return

        # اول چک میکنیم تو کش هست یا نه
        sound_to_play = self.sound_cache.get(self.current_sound_name)

        # اگر نبود (هنوز لود نشده)، همین لحظه لود کن (فال‌بک)
        if not sound_to_play:
            path = self.sound_file_map.get(self.current_sound_name)
            if path:
                try:
                    sound_to_play = SoundLoader.load(path)
                    self.sound_cache[self.current_sound_name] = sound_to_play
                except:
                    pass

        # پخش نهایی
        if sound_to_play:
            self.current_sound = sound_to_play
            try:
                if self.current_sound.state != 'play':
                    self.current_sound.loop = True
                    self.current_sound.play()
                    self.is_playing_sound = True
            except Exception as e:
                print(f"Play Error: {e}")

    def stop_sound(self):
        if self.current_sound:
            try:
                self.current_sound.stop()
                # نکته: اینجا unload() را حذف کردیم تا فایل در حافظه بماند
            except Exception:
                pass
        self.current_sound = None # فقط رفرنس رو قطع می‌کنیم، فایل توی self.sound_cache هست
        self.is_playing_sound = False

    def reset_state(self):
        app = MDApp.get_running_app() # گرفتن دسترسی به app
        
        self.timer_running = False
        self.is_work_time = True
        self.cycles_completed = 0
        self.show_quote = False       
        # استفاده از app.config_engine به جای self.cfg
        self.time_left = int(app.config_engine.work_min) * 60
        self.total_time_session = self.time_left

        self.update_display_time()
        self.progress_value = 0
        self.status_text = "Ready to Focus?"
        self.cycle_text = f"Cycle: 1/{app.config_engine.cycles_limit}"

        if getattr(self, "clock_event", None):
            try: self.clock_event.cancel()
            except: pass
        self.clock_event = None
        self.end_time = None

        try:
            self.ids.task_input.text = ""
            self.ids.task_input.error = False
            self.ids.task_input.disabled = False
        except Exception:
            pass

    def open_tag_menu(self):
        # استفاده از لیست saved_tasks که داینامیک است و اموجی ندارد
        menu_items = [
            {
                "text": tag,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=tag: self.set_tag(x),
            } for tag in self.saved_tasks
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.task_input,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def set_tag(self, tag_text):
        self.ids.task_input.text = tag_text
        self.menu.dismiss()
        
    def toggle_sound(self):
        if self.is_sound_playing:
            # توقف صدا
            if self.current_sound:
                self.current_sound.stop()
            self.ids.btn_sound.icon = "music-note-off"
            self.ids.btn_sound.md_bg_color = (0, 0, 0, 0)
            self.is_sound_playing = False
        else:
            # پخش صدا (باران)
            sound_path = "assets/sounds/rain.mp3"
            
            if os.path.exists(sound_path):
                # اگر قبلاً لود نشده، لودش کن
                if not self.current_sound:
                    self.current_sound = SoundLoader.load(sound_path)
                
                if self.current_sound:
                    self.current_sound.loop = True
                    self.current_sound.play()
                    self.ids.btn_sound.icon = "music-note"
                    self.ids.btn_sound.md_bg_color = (0.2, 0.6, 1, 0.2) # هایلایت آبی
                    self.is_sound_playing = True
                else:
                    pass 
                    
    def pause_timer(self):
        self.timer_running = False
        self.status_text = "Paused"
        self.show_quote = False       
        if getattr(self, "clock_event", None):
            self.clock_event.cancel()

    def toggle_timer(self):
        raw_task = self.ids.task_input.text.strip()
        if not raw_task:
            self.ids.task_input.error = True
            return
        self.ids.task_input.error = False

        if not self.timer_running:
            if raw_task and raw_task not in self.saved_tasks:
                self.saved_tasks.append(raw_task)

            self.timer_running = True
            self.status_text = "Focusing..." if self.is_work_time else "Recharging..."
            self.show_quote = True 
            # خط پاک کننده متن حذف شد
            self.quote_text = random.choice(self.quotes)            
            
            if self.is_work_time:
                self.play_sound()

            if getattr(self, "clock_event", None):
                try: self.clock_event.cancel()
                except: pass
                self.clock_event = None

            self.end_time = datetime.now() + timedelta(seconds=self.time_left)
            self.clock_event = Clock.schedule_interval(self.update_clock, 0.5)
        else:
            self.pause_timer()
            self.stop_sound()
                
    def reset_timer(self):
        app = MDApp.get_running_app() # مهم
        
        self.timer_running = False
        self.end_time = None
        self.show_quote = False               
        self.status_text = "Ready to Focus?"  
        self.current_task = ""
        if getattr(self, "clock_event", None):
            try: self.clock_event.cancel()
            except: pass
            self.clock_event = None
    
        if self.is_work_time:
            self.time_left = int(app.config_engine.work_min) * 60
            self.status_text = "Ready to Focus?"
        else:
            # لاجیک استراحت
            if self.cycles_completed == 0: # یعنی سایکل تمام شده و دور بعد است
                 # اینجا چون ریست دستی است معمولا برمی‌گردیم به حالت کار یا استراحت کوتاه
                 self.time_left = int(app.config_engine.short_break_min) * 60
                 self.status_text = "Break Time"
            else:
                self.time_left = int(app.config_engine.short_break_min) * 60
                self.status_text = "Break Time"
    
        self.total_time_session = self.time_left
        self.update_display_time()
        self.progress_value = 0
        
        self.cycle_text = f"Cycle: {self.cycles_completed}/{app.config_engine.cycles_limit}"
    
        try:
            self.ids.task_input.disabled = False
            self.ids.task_input.error = False
        except Exception:
            pass

    def update_display_time(self, seconds_val=None):
        # اگر ورودی داده نشد (مثل موقع ریست)، از زمان فعلی کلاس استفاده کن
        if seconds_val is None:
            seconds_val = self.time_left  # <--- این خط اصلاح شده اصلی است

        # تبدیل اجباری به عدد صحیح برای جلوگیری از کرش
        val = int(seconds_val)
        m, s = divmod(val, 60)
        self.timer_text = f"{m:02d}:{s:02d}"
        
    def update_level_display(self):
        """سطح و پیشرفت کاربر را از موتور گیمیفیکیشن می‌خواند و نمایش می‌دهد"""
        app = MDApp.get_running_app()
        level_info = app.config_engine.get_user_level()
        if level_info:
            level_num, title, _, _, progress, _ = level_info
            
            # --- اصلاح شده: استفاده از self.level_text ---
            self.level_text = f"Level {level_num} • {title}"
            
            self.level_progress = progress * 100  # برای نوار پیشرفت (۰ تا ۱۰۰)

    def update_clock(self, dt):
        # اگر تایمر در حال اجرا نیست یا زمان پایان مشخص نیست، ایونت را متوقف کن
        if not self.timer_running or not self.end_time:
            if getattr(self, "clock_event", None):
                self.clock_event.cancel()
                self.clock_event = None
            return

        # محاسبه زمان باقی‌مانده بر اساس ساعت سیستم
        remaining = self.end_time - datetime.now()
        self.time_left = max(0, remaining.total_seconds())

        # آپدیت UI
        self.update_display_time()
        if self.total_time_session > 0:
            self.progress_value = ((self.total_time_session - self.time_left) / self.total_time_session) * 100
        else:
            self.progress_value = 0

        # اگر زمان تمام شد
        if self.time_left <= 0:
            self.finish_session()

    def finish_early(self):
        # استفاده از time_left و total_time_session صحیح
        elapsed_seconds = self.total_time_session - self.time_left
        elapsed_minutes = int(elapsed_seconds / 60)
        if elapsed_minutes < 1: elapsed_minutes = 1 
        
        self.pause_timer() 
        self.stop_sound()
        
        app = MDApp.get_running_app()
        task_name = self.ids.task_input.text or "General"
        
        if self.is_work_time:
            # استفاده از app.config_engine
            app.config_engine.log_session("Work (Skipped)", elapsed_minutes, task_name)
        
        self.status_text = "Session Skipped"
        
        # اتمام زودهنگام -> رفتن به حالت بعد (با فلگ Early)
        self.finish_session(is_early=True)

    def finish_session(self, manual_duration=None, is_early=False):
        # ... (کدهای ابتدای متد بدون تغییر) ...
        self.timer_running = False
        self.end_time = None
        self.play_alarm()   
        if getattr(self, "clock_event", None):
            self.clock_event.cancel()
            self.clock_event = None

        if not is_early:
            self.progress_value = 100

        # --- آلارم و نوتیفیکیشن ---
        try:
            message = "Time for a break!" if self.is_work_time else "Back to work!"
            notification.notify(title="PomoPulse", message=message, timeout=5)
            # ویبره فقط برای اندروید
            if platform == 'android':
                try:
                    from plyer import vibrator
                    vibrator.vibrate(0.5)
                except: pass
        except Exception:
            pass

        app = MDApp.get_running_app()
        task_name = self.ids.task_input.text.strip() or "General"
        
        if self.is_work_time and not is_early:
            session_type = "Work"
            duration_to_log = manual_duration if manual_duration is not None else int(app.config_engine.work_min)
            app.config_engine.log_session(session_type, duration_to_log, task_name)
            self.cycles_completed += 1

        if self.is_work_time: 
            self.is_work_time = False
            if self.cycles_completed >= app.config_engine.cycles_limit:
                self.status_text = "Long Break! 🎉"
                self.time_left = int(app.config_engine.long_break_min) * 60
                self.cycles_completed = 0
            else:
                self.status_text = "Short Break ☕"
                self.time_left = int(app.config_engine.short_break_min) * 60
            self.show_quote = False            
        else: 
            self.is_work_time = True
            self.status_text = "Back to Work! 🚀"
            self.show_quote = False
            if not hasattr(self, 'quotes'):
                self.quotes = ["Focus.", "Keep going."]
            self.quote_text = random.choice(self.quotes)
            self.time_left = int(app.config_engine.work_min) * 60
            
        self.total_time_session = self.time_left
        self.update_display_time()
        self.progress_value = 0 
        
        self.cycle_text = f"Cycle: {self.cycles_completed}/{app.config_engine.cycles_limit}"
        self.update_level_display()

    # این متد باید حتماً داخل کلاس باشد (با یک Tab فاصله)
    def play_alarm(self):
        """پخش صدای آلارم هنگام اتمام سشن"""
        try:
            alarm_path = "assets/sounds/alarm.wav"
            if os.path.exists(alarm_path):
                alarm_sound = SoundLoader.load(alarm_path)
                if alarm_sound:
                    alarm_sound.play()
            else:
                print(f"Alarm file not found: {alarm_path}")
        except Exception as e:
            print(f"Alarm play error: {e}")

class SettingsScreen(MDScreen):
    def on_enter(self):
        app = MDApp.get_running_app()
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

        # خلاصه
        total_mins = data["total_mins"]
        h, m = divmod(total_mins, 60)
        self.ids.lbl_total_time.text = f"{h}h {m}m"
        self.ids.lbl_sessions.text = str(data["total_count"])
        self.ids.lbl_skipped.text = str(data["skipped_count"])

        if not data["bar_data"] or total_mins == 0:
            self.ids.stats_list.add_widget(MDLabel(
                text="No data available.", halign="center", theme_text_color="Secondary"
            ))
            return

        # نمودار میله‌ای
        chart_card = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(10), padding=[0, 0, 0, dp(20)])
        chart_card.add_widget(MDLabel(text="Activity", font_style="Subtitle2", theme_text_color="Secondary"))

        max_val = max((d['total'] for d in data["bar_data"]), default=60)
        if max_val == 0: max_val = 60

        chart_body = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(220), spacing=dp(5))
        
        # محور Y
        y_axis = MDBoxLayout(orientation="vertical", size_hint_x=None, width=dp(35))
        y_axis.add_widget(MDLabel(text=self.format_time(max_val), font_style="Caption", halign="right", valign="top"))
        y_axis.add_widget(MDBoxLayout())
        y_axis.add_widget(MDLabel(text="0m", font_style="Caption", halign="right", valign="bottom"))
        y_axis.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))
        chart_body.add_widget(y_axis)

        # میله‌ها
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
                bar_container.add_widget(MDLabel(text=self.format_time(total_day_time), halign="center", font_style="Overline", size_hint_y=None, height=dp(15)))
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

        # جزئیات
        pie_container = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(15), padding=[0, dp(20), 0, 0])
        pie_container.add_widget(MDLabel(text="Details", font_style="Subtitle2", theme_text_color="Secondary"))

        sorted_tasks = sorted(data["pie_data"].items(), key=lambda x: x[1], reverse=True)
        grand_total = sum(data["pie_data"].values()) or 1

        for task, duration in sorted_tasks:
            percent = (duration / grand_total) * 100
            color = task_color_map.get(task, self.get_color(len(unique_tasks)))
            row = MDBoxLayout(adaptive_height=True, spacing=dp(15))
            icon = MDIconButton(icon="checkbox-blank-circle", theme_text_color="Custom", text_color=color, size_hint=(None, None), size=(dp(30), dp(30)))
            row.add_widget(icon)
            
            info_box = MDBoxLayout(orientation="vertical", adaptive_height=True, pos_hint={"center_y": .5})
            top_line = MDBoxLayout(adaptive_height=True)
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

    def on_start(self):
        # --- فعال‌سازی Wake Lock برای اندروید ---
        if platform == 'android':
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                WindowManager = autoclass('android.view.WindowManager')
                LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                
                # پرچم روشن نگه داشتن صفحه
                FLAG_KEEP_SCREEN_ON = LayoutParams.FLAG_KEEP_SCREEN_ON

                def add_flags():
                    window = activity.getWindow()
                    window.addFlags(FLAG_KEEP_SCREEN_ON)

                run_on_ui_thread(add_flags)()
            except Exception as e:
                print(f"WakeLock Error: {e}")

if __name__ == '__main__':
    PomoPulseApp().run()


