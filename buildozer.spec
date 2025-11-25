[app]
# (1) Title of your application
title = Pomodoro Pro
package.name = pomodoropro
package.domain = org.doctor.pomodoro

# (2) Source configuration
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,wav,txt,ttf,json

# (3) Versioning
version = 1.0

# (4) Requirements (FIXED: Removed conflicting kivymd version)
requirements = python3,kivy==2.3.0,https://github.com/kivymd/KivyMD/archive/master.zip,plyer,pillow,materialyoucolor,exceptiongroup,asyncgui,asynckivy

# (5) Orientation and permissions
orientation = portrait
fullscreen = 0
android.permissions = VIBRATE,FOREGROUND_SERVICE,WAKE_LOCK,INTERNET

# (6) Android Specifics
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# (7) Buildozer settings
[buildozer]
log_level = 2
warn_on_root = 1
