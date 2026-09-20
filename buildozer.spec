[app]
title = QSO Logg
package.name = qso_logg
package.domain = org.qso
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Android
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.gradle_dependencies =

[buildozer]
log_level = 2
warn_on_root = 0
