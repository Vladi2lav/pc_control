# -*- coding: utf-8 -*-
"""
================================================================================
                    PCControl Project Packager & Developer Guide
================================================================================

Этот скрипт предназначен для автоматической сборки проекта PCControl под Windows и Linux.
Он компилирует статическое ядро приложения в бинарные файлы с помощью PyInstaller,
формирует структуру папок для портативной (Portable) и стандартной (Installed) версий,
а также готовит структуру для создания AppImage под Linux.

--------------------------------------------------------------------------------
                         АРХИТЕКТУРА И СТРУКТУРА ПРОЕКТА
--------------------------------------------------------------------------------
Проект разделен на две части: статическое ядро (скомпилированное) и динамические
пользовательские модули (плагины, запускаемые "на лету").

1. Статическое ядро (базовый функционал):
   - `main.py` / `main.qml`:
     Главное приложение. В скомпилированном виде (PCControl.exe) также выполняет роль
     интерпретатора Python для запуска пользовательских модулей через специальный
     закрытый аргумент `--run-script <путь_к_скрипту>`.
   - `configurator.py` / `configurator.qml`:
     Приложение-конфигуратор для создания и редактирования пользовательских модулей.
     Компилируется в отдельный исполняемый файл Configurator.exe.
   - `paths.py`:
     Критически важный модуль разрешения путей. Автоматически переключается между
     портативным и стандартным (установленным) режимами работы.

2. Куда что класть при расширении проекта (информация для разработчиков):
   - Исходный код ядра и базы данных:
     Любая глобальная логика работы с БД, изменения интерфейса конфигуратора или
     главного окна должны вноситься в `main.py`, `configurator.py`, `paths.py` и
     соответствующие QML файлы в корневом каталоге. Любые изменения в ядре требуют
     повторного запуска этого скрипта сборки.
   - Статические ресурсы ядра:
     Картинки, иконки, встроенные БД по умолчанию кладутся в корень проекта или
     специальный подкаталог ресурсов (например, `assets/`) и должны быть прописаны
     в секции `datas` конфигурации PyInstaller в этом скрипте.
   - Пользовательские модули (плагины):
     Размещаются в каталоге `primer/` в репозитории. При первой сборке или запуске
     приложения они автоматически копируются в рабочий каталог пользователя как
     модули по умолчанию. При создании нового модуля в нем обязательно должен быть
     файл `main.py` (точка входа).

3. Как работает переключение режимов работы (Portable vs Installed):
   - Портативный режим (Portable):
     Активируется созданием пустого файла `portable.txt` рядом с исполняемым файлом
     PCControl.exe. В этом режиме программа хранит все настройки и модули локально
     в подкаталоге `data/` (а именно: `data/settings/` и `data/modules/`).
   - Установленный режим (Installed):
     Если файла `portable.txt` нет, программа следует стандартам операционных систем:
     * Настройки (settings.json) сохраняются в:
       - Windows: %APPDATA%/PCControl  (например, C:\\Users\\Имя\\AppData\\Roaming\\PCControl)
       - Linux:   ~/.config/pccontrol
     * Динамические модули (плагины) и базы данных сохраняются в:
       - Windows: %LOCALAPPDATA%/PCControl/modules  (C:\\Users\\Имя\\AppData\\Local\\PCControl\\modules)
       - Linux:   ~/.local/share/pccontrol/modules

--------------------------------------------------------------------------------
                            ИНСТРУКЦИЯ ПО СБОРКЕ
--------------------------------------------------------------------------------
Для сборки выполните команду в консоли:
    python build_project.py

Скрипт создаст каталог `dist/`, внутри которого будут находиться:
    - `PCControl_Portable_Windows/` (или `_Linux/`): Портативная версия с `portable.txt`.
    - `PCControl_Installed_Windows/` (или `_Linux/`): Версия для инсталлятора.
    - `PCControl.AppDir/` (только для Linux): Готовая структура для сборки AppImage.
    - `PCControl_Portable.zip`: Архив с портативной версией для дистрибуции.
"""

import sys
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

# Цветовой вывод в терминал
def log_info(msg):
    print(f"\x1b[32m[INFO]\x1b[0m {msg}")

def log_warn(msg):
    print(f"\x1b[33m[WARN]\x1b[0m {msg}")

def log_error(msg):
    print(f"\x1b[31m[ERROR]\x1b[0m {msg}")

# Проверка зависимостей
try:
    import PyInstaller
    log_info("PyInstaller найден.")
except ImportError:
    log_error("PyInstaller не установлен в текущем виртуальном окружении (.venv).")
    log_info("Установите его командой: pip install pyinstaller")
    sys.exit(1)

# Пути проекта
ROOT_DIR = Path(__file__).parent.resolve()
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
PRIMER_DIR = ROOT_DIR / "primer"

# Очистка старых сборок
if DIST_DIR.exists():
    log_info("Очистка старого каталога dist/...")
    shutil.rmtree(DIST_DIR)
if BUILD_DIR.exists():
    log_info("Очистка старого каталога build/...")
    shutil.rmtree(BUILD_DIR)

DIST_DIR.mkdir(exist_ok=True)

# Сборка исполняемых файлов
log_info("Запуск компиляции статического ядра приложения через PyInstaller...")

# Конфигурация для PyInstaller
# Собираем в режиме --onedir, так как у нас два исполняемых файла (main и configurator),
# которые будут делить общие библиотеки (PySide6, Python DLLs и т.д.), что сильно экономит место.
pyinstaller_args_main = [
    "main.py",
    "--name=PCControl",
    "--noconfirm",
    "--onedir",
    "--windowed",
    f"--add-data=main.qml{os.pathsep}.",
    f"--add-data=paths.py{os.pathsep}.",
    f"--add-data=settings.json{os.pathsep}.",
]

pyinstaller_args_config = [
    "configurator.py",
    "--name=Configurator",
    "--noconfirm",
    "--onedir",
    "--windowed",
    f"--add-data=configurator.qml{os.pathsep}.",
    f"--add-data=paths.py{os.pathsep}.",
]

# Выполняем сборку главного приложения
log_info("Компиляция главного модуля PCControl...")
subprocess.run([sys.executable, "-m", "PyInstaller"] + pyinstaller_args_main, check=True)

# Выполняем сборку конфигуратора
log_info("Компиляция конфигуратора...")
subprocess.run([sys.executable, "-m", "PyInstaller"] + pyinstaller_args_config, check=True)

# Исходная папка со всеми бинарниками после сборки PCControl
bin_dir = DIST_DIR / "PCControl"
config_bin_dir = DIST_DIR / "Configurator"

# Объединяем оба приложения в одну папку dist/PCControl (так как они делят общие библиотеки)
log_info("Интеграция конфигуратора в общий бинарный пакет...")
for item in config_bin_dir.iterdir():
    dest_item = bin_dir / item.name
    if item.is_dir():
        shutil.copytree(item, dest_item, dirs_exist_ok=True)
    else:
        shutil.copy2(item, dest_item)
# Удаляем отдельную папку сборки конфигуратора
shutil.rmtree(config_bin_dir)

# Создаем структуру Portable версии
log_info("Создание Portable-версии...")
portable_dist_name = "PCControl_Portable_Windows" if sys.platform == "win32" else "PCControl_Portable_Linux"
portable_dir = DIST_DIR / portable_dist_name
shutil.copytree(bin_dir, portable_dir)

# Создаем файл portable.txt, активирующий портативный режим в paths.py
with open(portable_dir / "portable.txt", "w", encoding="utf-8") as f:
    f.write("Этот файл переводит PCControl в портативный режим.\nВсе настройки и модули будут сохраняться локально в папке 'data/'.\n")

# Копируем стандартные пользовательские модули (из primer) в папку по умолчанию внутри Portable сборки
default_mods_dir = portable_dir / "default_modules"
if PRIMER_DIR.exists():
    shutil.copytree(PRIMER_DIR, default_mods_dir)

# Архивируем Portable версию для дистрибуции
log_info("Создание ZIP архива Portable-версии...")
archive_name = DIST_DIR / f"{portable_dist_name}.zip"
with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(portable_dir):
        for file in files:
            file_path = Path(root) / file
            arcname = file_path.relative_to(portable_dir)
            zipf.write(file_path, arcname)

# Создаем структуру Installed версии (для инсталлятора)
log_info("Создание структуры Installed-версии (без portable.txt)...")
installed_dist_name = "PCControl_Installed_Windows" if sys.platform == "win32" else "PCControl_Installed_Linux"
installed_dir = DIST_DIR / installed_dist_name
shutil.copytree(bin_dir, installed_dir)

# Копируем дефолтные модули во встроенную папку (paths.py скопирует их при первом запуске)
default_mods_installed_dir = installed_dir / "default_modules"
if PRIMER_DIR.exists():
    shutil.copytree(PRIMER_DIR, default_mods_installed_dir)

# Генерируем сопроводительные инструкции для создания дистрибутивов
if sys.platform == "win32":
    # Создание NSIS шаблона для сборщика инсталляторов на Windows
    nsis_script_path = DIST_DIR / "pccontrol_installer.nsi"
    log_info("Генерация шаблона инсталлятора NSIS (pccontrol_installer.nsi)...")
    nsis_content = f"""; Шаблон скрипта для сборки инсталлятора PCControl с помощью NSIS (Nullsoft Scriptable Install System)
Unicode true
Name "PCControl"
OutFile "PCControl_Setup.exe"
InstallDir "$PROGRAMFILES64\\PCControl"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Копируем файлы ядра и скомпилированные зависимости
  File /r "{installed_dir}\\*.*"
  
  ; Создаем ярлыки в меню Пуск
  CreateDirectory "$SMPROGRAMS\\PCControl"
  CreateShortcut "$SMPROGRAMS\\PCControl\\PCControl.lnk" "$INSTDIR\\PCControl.exe"
  CreateShortcut "$SMPROGRAMS\\PCControl\\Configurator.lnk" "$INSTDIR\\Configurator.exe"
  CreateShortcut "$SMPROGRAMS\\PCControl\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
  
  ; Создаем ярлык на рабочем столе
  CreateShortcut "$DESKTOP\\PCControl.lnk" "$INSTDIR\\PCControl.exe"

  ; Записываем деинсталлятор
  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\\PCControl.lnk"
  RMDir /r "$SMPROGRAMS\\PCControl"
  RMDir /r "$INSTDIR"
SectionEnd
"""
    with open(nsis_script_path, "w", encoding="cp1251") as f:
        f.write(nsis_content)

else:
    # Создание структуры AppImage для Linux
    log_info("Создание структуры AppDir для Linux AppImage...")
    appdir = DIST_DIR / "PCControl.AppDir"
    appdir_usr_bin = appdir / "usr" / "bin"
    appdir_usr_bin.mkdir(parents=True, exist_ok=True)
    
    # Копируем файлы установленной версии в usr/bin
    shutil.copytree(installed_dir, appdir_usr_bin, dirs_exist_ok=True)
    
    # Создаем bash-скрипт запуска AppRun в корне AppDir
    apprun_path = appdir / "AppRun"
    apprun_content = """#!/bin/sh
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/PCControl" "$@"
"""
    with open(apprun_path, "w", encoding="utf-8") as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)

    # Создаем desktop-файл
    desktop_path = appdir / "pccontrol.desktop"
    desktop_content = """[Desktop Entry]
Name=PCControl
Exec=PCControl
Icon=pccontrol
Type=Application
Categories=Utility;
Comment=PC Control Application
Terminal=false
"""
    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(desktop_content)
    os.chmod(desktop_path, 0o755)

    # Копируем заглушку-иконку в AppDir
    icon_src = ROOT_DIR / "vivereedit.png"
    if icon_src.exists():
        shutil.copy2(icon_src, appdir / "pccontrol.png")
    
    # Выводим инструкции по компиляции AppImage
    log_warn("Для окончательной упаковки AppImage на Linux скачайте appimagetool:")
    log_warn("  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage")
    log_warn("  chmod +x appimagetool-x86_64.AppImage")
    log_warn(f"И запустите сборку: ./appimagetool-x86_64.AppImage {appdir}")

# Удаляем временную папку сборки
shutil.rmtree(bin_dir)

log_info("Сборка и развертывание пакетов успешно завершены!")
log_info(f"Дистрибутивы и шаблоны инсталляторов созданы в: {DIST_DIR}")
