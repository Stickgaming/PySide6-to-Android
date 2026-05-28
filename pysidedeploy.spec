[app]
title = Mirai-Ko Hana
project_dir = .
entrypoint = main.py
icon = mirai_logo.png
architecture = arm64-v8a

[python]
version = 3.11.5
requirements = PySide6,shiboken6,jinja2,pkginfo,tqdm,packaging

[android]
wheel_pyside = ./wheels/
wheel_shiboken = ./wheels/
