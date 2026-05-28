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
wheel_pyside = local_wheels/PySide6-6.8.0.2-6.8.0-cp311-cp311-android_aarch64.whl
wheel_shiboken = local_wheels/shiboken6-6.8.0.2-6.8.0-cp311-cp311-android_aarch64.whl
android_packages = PySide6,shiboken6
