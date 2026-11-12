[app]
title = YaDeRemote
package.name = yaderemote
package.domain = org.yade
source.include_exts = py,png,jpg,kv,atlas
source.dir = .
version = 0.1
requirements = python3,kivy,jnius
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = INTERNET, TRANSMIT_IR

[buildozer]
log_level = 2
warn_on_root = 1
