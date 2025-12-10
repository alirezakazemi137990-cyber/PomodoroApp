import os
import csv
import time
import configparser
from datetime import datetime

# Kivy Imports
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import FadeTransition

# KivyMD Imports
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDFlatButton, MDIconButton, MDFillRoundFlatButton, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.widget import Widget
from plyer import notification

# ==========================================
# 1. طراحی رابط کاربری (KV Layout)
# ==========================================
KV = '''
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

# --- ویجت‌های سفارشی لیست کارها ---
<RightCheckbox>:
    adaptive_width: True

<TaskItem>:
    markup: True
    IconLeftWidget:
        icon: "delete-outline"
        theme_text_color: "Custom"
        text_color: 0.8, 0, 0, 1
        on_release: root.delete_task(root)

    RightCheckbox:
        MDCheckbox:
            on_active: root.toggle_check(self, self.active)

# --- صفحه اصلی ---
<HomeScreen>:
    name: "home"
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.1, 0.1, 0.1, 1

        # هدر (پروفایل)
        MDBoxLayout:
            adaptive_height: True
            padding: dp(15)
            spacing: dp(10)
            
            MDIconButton:
                icon: "account-circle"
                user_font_size: "32sp"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                on_release: app.switch_screen("profile")
                
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                pos_hint: {"center_y": .5}
                MDLabel:
                    text: root.greeting_text
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                MDLabel:
                    text: root.user_title_text
                    font_style: "Caption"
                    theme_text_color: "Hint"

        # بخش تایمر
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.45
            padding: dp(20)
            spacing: dp(10)
            
            MDLabel:
                text: "Stay focused, keep growing."
                halign: "center"
                theme_text_color: "Hint"
                font_style: "Caption"
                size_hint_y: None
                height: dp(20)

            MDBoxLayout:
                orientation: 'vertical'
                spacing: dp(5)
                pos_hint: {"center_x": .5, "center_y": .5}
                
                MDLabel:
                    text: root.timer_text
                    font_style: "H2"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color if root.is_work_time else (0, 0.8, 0, 1)
                    font_size: "64sp"
                    bold: True
                
                MDLabel:
                    text: root.status_text
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.7, 0.7, 1
                    font_style: "Subtitle1"

            MDProgressBar:
                id: progress
                value: root.progress_value
                size_hint_y: None
                height: dp(8)
                color: app.theme_cls.primary_color if root.is_work_time else (0, 0.8, 0, 1)

            MDLabel:
                text: root.cycle_text
                halign: "center"
                theme_text_color: "Hint"
                font_style: "Caption"
                padding: [0, dp(10), 0, 0]

        # دکمه‌های کنترل تایمر
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(30)
            padding: [0, dp(10), 0, dp(20)]
            pos_hint: {"center_x": .5}

            MDIconButton:
                icon: "refresh"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.reset_timer()

            MDFillRoundFlatButton:
                id: btn_start
                text: "START" if not root.timer_running else "PAUSE"
                font_size: "20sp"
                size_hint_x: None
                width: dp(150)
                on_release: root.toggle_timer()
                md_bg_color: app.theme_cls.primary_color if not root.timer_running else (1, 0.6, 0, 1)

            MDIconButton:
                icon: "skip-next"
                disabled: not root.timer_running
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1 if root.timer_running else (0.3, 0.3, 0.3, 1)
                on_release: root.finish_early()
            
            MDIconButton:
                icon: "metronome" if root.sound_enabled else "volume-off"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color if root.sound_enabled else (0.5, 0.5, 0.5, 1)
                on_release: root.toggle_sound()

        # لیست کارها (Task Checklist)
        MDCard:
            orientation: "vertical"
            size_hint_y: 0.35
            radius: [20, 20, 0, 0]
            md_bg_color: 0.15, 0.15, 0.15, 1
            elevation: 2
            padding: dp(10)
            
            MDBoxLayout:
                adaptive_height: True
                spacing: dp(5)
                
                MDTextField:
                    id: task_input
                    hint_text: "Add a task..."
                    mode: "round"
                    fill_color_normal: 0.2, 0.2, 0.2, 1
                    text_color_normal: 1, 1, 1, 1
                    size_hint_x: 0.85
                
                MDIconButton:
                    icon: "plus-circle"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color
                    on_release: root.add_task()

            ScrollView:
                MDList:
                    id: task_list_container

        # منوی ناوبری پایین
        MDBoxLayout:
            adaptive_height: True
            md_bg_color: 0.08, 0.08, 0.08, 1
            padding: [dp(20), dp(5), dp(20), dp(5)]
            
            MDIconButton:
                icon: "cog"
                theme_text_color: "Custom"
                text_color: 0.6, 0.6, 0.6, 1
                on_release: app.switch_screen("settings")
            
            Widget:
            
            MDIconButton:
                icon: "chart-bar"
                theme_text_color: "Custom"
                text_color: 0.6, 0.6, 0.6, 1
                on_release: app.switch_screen("stats")

# --- صفحه تنظیمات ---
<SettingsScreen>:
    name: "settings"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        md_bg_color: 0.1, 0.1, 0.1, 1

        MDLabel:
            text: "Settings"
            font_style: "H5"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1

        MDTextField:
            id: work_min
            hint_text: "Work Duration (min)"
            input_filter: "int"
            text: str(app.config_engine.work_min)
            mode: "rectangle"

        MDTextField:
            id: short_break
            hint_text: "Short Break (min)"
            input_filter: "int"
            text: str(app.config_engine.short_break_min)
            mode: "rectangle"

        MDTextField:
            id: long_break
            hint_text: "Long Break (min)"
            input_filter: "int"
            text: str(app.config_engine.long_break_min)
            mode: "rectangle"

        Widget:

        MDRaisedButton:
            text: "SAVE & RETURN"
            pos_hint: {"center_x": .5}
            on_release: root.save_settings()

# --- صفحه آمار ---
<StatsScreen>:
    name: "stats"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        md_bg_color: 0.1, 0.1, 0.1, 1

        MDLabel:
            text: "Analytics"
            font_style: "H5"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(50)

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(10)
            padding: dp(10)
            pos_hint: {"center_x": .5}

            MDRectangleFlatButton:
                text: "Daily"
                text_color: 1, 1, 1, 1
                on_release: root.load_stats("Daily")
            MDRectangleFlatButton:
                text: "Weekly"
                text_color: 1, 1, 1, 1
                on_release: root.load_stats("Weekly")

        MDBoxLayout:
            adaptive_height: True
            padding: dp(5)
            spacing: dp(10)

            MDCard:
                orientation: "vertical"
                size_hint: 0.5, None
                height: dp(100)
                md_bg_color: 0.2, 0.2, 0.2, 1
                padding: dp(10)
                radius: [15]
                MDLabel:
                    id: lbl_total_time
                    text: "0h 0m"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    font_style: "H6"
                MDLabel:
                    text: "Total Focus"
                    halign: "center"
                    theme_text_color: "Hint"
                    font_style: "Caption"

            MDCard:
                orientation: "vertical"
                size_hint: 0.5, None
                height: dp(100)
                md_bg_color: 0.2, 0.2, 0.2, 1
                padding: dp(10)
                radius: [15]
                MDLabel:
                    id: lbl_sessions
                    text: "0"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0, 0.8, 0, 1
                    font_style: "H6"
                MDLabel:
                    text: "Completed"
                    halign: "center"
                    theme_text_color: "Hint"
                    font_style: "Caption"

        MDRaisedButton:
            text: "BACK"
            pos_hint: {"center_x": .5}
            on_release: app.switch_screen("home")

# --- صفحه پروفایل ---
<ProfileScreen>:
    name: "profile"
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)
        md_bg_color: 0.1, 0.1, 0.1, 1

        Widget:

        MDCard:
            orientation: "vertical"
            size_hint: None, None
            size: dp(300), dp(350)
            pos_hint: {"center_x": .5}
            padding: dp(20)
            spacing: dp(15)
            radius: [20]
            md_bg_color: 0.2, 0.2, 0.2, 1

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
                mode: "rectangle"

            MDTextField:
                id: user_title
                hint_text: "Job Title"
                text: app.config_engine.user_title
                mode: "rectangle"

        MDBoxLayout:
            adaptive_height: True
            spacing: dp(20)
            pos_hint: {"center_x": .5}

            MDFlatButton:
                text: "CANCEL"
                text_color: 1, 0, 0, 1
                on_release: app.switch_screen("home")

            MDRaisedButton:
                text: "SAVE PROFILE"
                on_release: root.save_profile()

        Widget:
'''

# ==========================================
# 2. منطق برنامه (Application Logic)
# ==========================================

# --- مدیریت تنظیمات و داده‌ها ---
class PomodoroConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        # تشخیص خودکار مسیر ذخیره‌سازی در اندروید یا ویندوز
        from kivy.utils import platform
        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            self.data_dir = activity.getFilesDir().getAbsolutePath() + '/'
        else:
            self.data_dir = os.path.dirname(os.path.abspath(__file__))

        self.filename = os.path.join(self.data_dir, 'config.ini')
        self.history_file = os.path.join(self.data_dir, 'pomodoro_history.csv')
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.filename):
            self.config['SETTINGS'] = {
                'work_minutes': '25',
                'short_break': '5',
                'long_break': '15',
                'cycles': '4',
                'theme_accent': 'Blue'
            }
            self.config['USER'] = {'name': 'Dr. Kazemi', 'title': 'Physician & Inventor'}
            with open(self.filename, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(self.filename)
            if 'USER' not in self.config:
                self.config['USER'] = {'name': 'User', 'title': 'Dreamer'}

        # بارگذاری مقادیر با مقدار پیش‌فرض ایمن
        self.work_min = int(self.config['SETTINGS'].get('work_minutes', 25))
        self.short_break_min = int(self.config['SETTINGS'].get('short_break', 5))
        self.long_break_min = int(self.config['SETTINGS'].get('long_break', 15))
        self.cycles_limit = int(self.config['SETTINGS'].get('cycles', 4))
        self.user_name = self.config['USER'].get('name', 'User')
        self.user_title = self.config['USER'].get('title', 'Dreamer')

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
            return {"total_count": 0, "total_mins": 0}

        grand_total_mins = 0
        grand_total_count = 0
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 3: continue
                    if "Work" in row[1]:
                        grand_total_count += 1
                        try:
                            grand_total_mins += int(row[2])
                        except: pass
        except: pass

        return {"total_count": grand_total_count, "total_mins": grand_total_mins}

    def save_config(self):
        self.config['SETTINGS']['work_minutes'] = str(self.work_min)
        self.config['SETTINGS']['short_break'] = str(self.short_break_min)
        self.config['SETTINGS']['long_break'] = str(self.long_break_min)
        self.config['USER']['name'] = self.user_name
        self.config['USER']['title'] = self.user_title
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)

# --- کامپوننت‌های رابط کاربری ---

class RightCheckbox(IRightBodyTouch, MDBoxLayout):
    '''کانتینر برای قرار دادن چک‌باکس در سمت راست لیست آیتم'''
    adaptive_width = True

class TaskItem(OneLineAvatarIconListItem):
    '''آیتم لیست کارها با قابلیت حذف و تیک زدن'''
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def delete_task(self, item):
        self.parent.remove_widget(item)

    def toggle_check(self, checkbox, value):
        if value:
            self.text = f"[s]{self.text}[/s]" # خط زدن متن
            self.theme_text_color = "Secondary"
        else:
            self.text = self.text.replace("[s]", "").replace("[/s]", "")
            self.theme_text_color = "Primary"

# --- صفحات برنامه ---

class HomeScreen(MDScreen):
    timer_text = StringProperty("25:00")
    status_text = StringProperty("Ready to Focus?")
    greeting_text = StringProperty("")
    user_title_text = StringProperty("")
    cycle_text = StringProperty("Cycle: 0/4")
    progress_value = NumericProperty(0)
    timer_running = BooleanProperty(False)
    is_work_time = BooleanProperty(True)
    sound_enabled = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clock_event = None
        self.app = MDApp.get_running_app()
        self.cfg = self.app.config_engine
        self.time_left = self.cfg.work_min * 60
        self.total_time = self.time_left
        self.cycles_completed = 0
        
        # لود کردن امن فایل صوتی
        self.tick_sound = None
        try:
            self.tick_sound = SoundLoader.load('tick.wav')
        except:
            print("Audio Warning: Could not load tick.wav")
            
        self.last_tick_time = 0

    def on_enter(self):
        self.greeting_text = f"Hi, {self.cfg.user_name}"
        self.user_title_text = self.cfg.user_title
        current = self.cycles_completed + 1 if self.cycles_completed < self.cfg.cycles_limit else self.cfg.cycles_limit
        self.cycle_text = f"Cycle: {current}/{self.cfg.cycles_limit}"

    def toggle_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.status_text = "Focusing..." if self.is_work_time else "Relaxing..."
            self.clock_event = Clock.schedule_interval(self.update_clock, 1) 
        else:
            self.timer_running = False
            self.status_text = "Paused"
            if self.clock_event: self.clock_event.cancel()

    def update_clock(self, dt):
        if self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_text = f"{mins:02d}:{secs:02d}"
            
            elapsed = self.total_time - self.time_left
            if self.total_time > 0:
                self.progress_value = (elapsed / self.total_time) * 100

            # پخش صدای تیک تاک
            if self.sound_enabled and self.timer_running and self.is_work_time:
                current_time = time.time()
                # پخش هر 1 ثانیه بدون تداخل
                if current_time - self.last_tick_time >= 1.0:
                    if self.tick_sound:
                        try:
                            if self.tick_sound.status == 'play':
                                self.tick_sound.stop()
                            self.tick_sound.play()
                        except: pass
                    self.last_tick_time = current_time
        else:
            # اگر زمان تمام شد (یا منفی شد)
            self.finish_session()

    def finish_session(self):
        if self.clock_event: self.clock_event.cancel()
        self.timer_running = False
        self.progress_value = 100
        
        task_name = "General" # بعداً می‌تواند از لیست انتخاب شود
        
        if self.is_work_time:
            self.cycles_completed += 1
            self.cfg.log_session("Work", self.cfg.work_min, task_name)
            
            if self.cycles_completed >= self.cfg.cycles_limit:
                self.time_left = self.cfg.long_break_min * 60
                self.status_text = "Long Break!"
                self.cycles_completed = 0
            else:
                self.time_left = self.cfg.short_break_min * 60
                self.status_text = "Short Break"
            
            self.is_work_time = False
        else:
            self.time_left = self.cfg.work_min * 60
            self.status_text = "Back to Work"
            self.is_work_time = True

        self.total_time = self.time_left
        mins, secs = divmod(self.time_left, 60)
        self.timer_text = f"{mins:02d}:{secs:02d}"
        self.progress_value = 0
        
        try:
            notification.notify(title="PomoPulse", message=self.status_text)
        except: pass

    def finish_early(self):
        if self.is_work_time:
            duration = (self.total_time - self.time_left)//60 if (self.total_time - self.time_left) > 60 else 0
            self.cfg.log_session("Work (Skipped)", duration)
        self.finish_session()

    def reset_timer(self):
        if self.clock_event: self.clock_event.cancel()
        self.timer_running = False
        self.is_work_time = True
        self.time_left = self.cfg.work_min * 60
        self.total_time = self.time_left
        self.progress_value = 0
        self.timer_text = f"{self.cfg.work_min:02d}:00"
        self.status_text = "Ready?"

    def add_task(self):
        text = self.ids.task_input.text
        if text.strip():
            self.ids.task_list_container.add_widget(TaskItem(text=text))
            self.ids.task_input.text = ""

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled

class SettingsScreen(MDScreen):
    def save_settings(self):
        app = MDApp.get_running_app()
        try:
            w = int(self.ids.work_min.text) if self.ids.work_min.text else 25
            s = int(self.ids.short_break.text) if self.ids.short_break.text else 5
            l = int(self.ids.long_break.text) if self.ids.long_break.text else 15

            app.config_engine.work_min = w
            app.config_engine.short_break_min = s
            app.config_engine.long_break_min = l
            app.config_engine.save_config()
            
            # ریست کردن تایمر با مقادیر جدید
            home = app.root.get_screen('home')
            home.reset_timer()
            app.switch_screen("home")
        except ValueError:
            pass

class StatsScreen(MDScreen):
    def on_pre_enter(self):
        self.load_stats("Daily")

    def load_stats(self, timeframe):
        app = MDApp.get_running_app()
        data = app.config_engine.get_chart_data(timeframe)
        self.ids.lbl_total_time.text = f"{data['total_mins']} m"
        self.ids.lbl_sessions.text = str(data['total_count'])

class ProfileScreen(MDScreen):
    def save_profile(self):
        app = MDApp.get_running_app()
        app.config_engine.user_name = self.ids.user_name.text
        app.config_engine.user_title = self.ids.user_title.text
        app.config_engine.save_config()
        app.switch_screen("home")

class PomoPulseApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.config_engine = PomodoroConfig()
        
        sm = MDScreenManager(transition=FadeTransition())
        Builder.load_string(KV) # لود کردن KV استرینگ
        
        sm.add_widget(HomeScreen())
        sm.add_widget(SettingsScreen())
        sm.add_widget(StatsScreen())
        sm.add_widget(ProfileScreen())
        return sm

    def switch_screen(self, screen_name):
        self.root.current = screen_name

if __name__ == '__main__':
    PomoPulseApp().run()
