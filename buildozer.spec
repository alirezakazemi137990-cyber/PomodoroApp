[app]
title = PomoPulse
package.name = pomopulse
package.domain = com.pomopulse
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,wav,ini,csv
source.include_patterns = assets/*, assets/fonts/*
source.exclude_dirs = tests, bin, venv, __pycache__
version = 1.1

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# تغییر مهم: نسخه پایتون را فقط python3 بگذار، p4a خودش نسخه مناسب را دانلود می‌کند
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pillow==9.5.0,plyer,pyjnius,cython==0.29.36

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = INTERNET,VIBRATE,WAKE_LOCK
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.accept_sdk_license = True
android.enable_androidx = True
android.gradle_dependencies = com.google.android.material:material:1.6.0
android.enable_jetifier = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.release_artifact = apk

# بخش ساینینگ (اطمینان حاصل کن فایل keystore در ریپازیتوری هست)
# android.release.keystore = my-key.keystore
# android.release.keyalias = my-alias
# android.release.keystore_password = 123456
# android.release.keyalias_password = 123456

[buildozer]
log_level = 2
warn_on_root = 1

# دستور حیاتی برای رفع خطای Linker
android.pre_build_cmds = ranlib {{dist_dir}}/lib/libfreetype.a


