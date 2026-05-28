[app]
title = Mirai-Ko Hana
project_dir = .
entrypoint = main.py
architecture = arm64-v8a

[python]
version = 3.11
requirements = PySide6,shiboken6,jinja2,pkginfo,tqdm,packaging
android_packages = PySide6,shiboken6

[android]
wheel_pyside = https://github.com
wheel_shiboken = https://github.com
android_packages = PySide6,shiboken6
