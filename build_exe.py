#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправленный скрипт для сборки исполняемого файла OZONPARSER.exe с помощью PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_selenium_stealth_path():
    """Динамически находит путь к selenium_stealth"""
    try:
        import selenium_stealth
        stealth_path = os.path.dirname(selenium_stealth.__file__)
        js_path = os.path.join(stealth_path, 'js')
        
        print(f"✅ Найден путь к selenium_stealth: {stealth_path}")
        print(f"✅ Путь к JS файлам: {js_path}")
        
        # Проверяем существование JS файлов
        if os.path.exists(js_path):
            js_files = os.listdir(js_path)
            print(f"📄 JS файлы: {js_files}")
            return stealth_path, js_path
        else:
            print("❌ Папка JS не найдена")
            return stealth_path, None
            
    except ImportError:
        print("❌ selenium_stealth не установлен")
        return None, None

def create_selenium_stealth_fallback():
    """Создает fallback JS файлы для selenium_stealth если их нет"""
    print("🔧 Создаю резервные JS файлы для selenium_stealth...")
    
    js_dir = Path('selenium_stealth_js')
    js_dir.mkdir(exist_ok=True)
    
    js_files = {
        'utils.js': '''
// utils.js для selenium-stealth
(function() {
    'use strict';
    
    // Удаляем признаки автоматизации
    if (navigator.webdriver) {
        delete navigator.webdriver;
    }
    
    // Переопределяем navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    // Скрываем automation
    window.chrome = {
        runtime: {},
    };
    
    // Переопределяем plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    
    // Переопределяем languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['ru-RU', 'ru'],
    });
    
})();
        ''',
        
        'chrome_runtime.js': '''
// chrome_runtime.js
window.chrome = {
    runtime: {},
};
        ''',
        
        'navigator_vendor.js': '''
// navigator_vendor.js
Object.defineProperty(navigator, 'vendor', {
    get: () => 'Google Inc.',
});
        ''',
        
        'navigator_plugins.js': '''
// navigator_plugins.js  
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
        ''',
        
        'webgl_vendor.js': '''
// webgl_vendor.js
const getParameter = WebGLRenderingContext.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter(parameter);
};
        ''',
        
        'chrome_csi.js': '''
// chrome_csi.js
window.chrome.csi = function() {
    return {
        onloadT: Date.now(),
        startE: Date.now(),
        tran: 15
    };
};
        ''',
        
        'chrome_load_times.js': '''
// chrome_load_times.js
window.chrome.loadTimes = function() {
    return {
        requestTime: Date.now() / 1000,
        startLoadTime: Date.now() / 1000,
        commitLoadTime: Date.now() / 1000,
        finishDocumentLoadTime: Date.now() / 1000,
        finishLoadTime: Date.now() / 1000,
        firstPaintTime: Date.now() / 1000,
        firstPaintAfterLoadTime: 0,
        navigationType: 'Other',
        wasFetchedViaSpdy: false,
        wasNpnNegotiated: false,
        npnNegotiatedProtocol: 'unknown',
        wasAlternateProtocolAvailable: false,
        connectionInfo: 'unknown'
    };
};
        '''
    }
    
    # Создаем JS файлы
    for filename, content in js_files.items():
        js_file = js_dir / filename
        js_file.write_text(content.strip(), encoding='utf-8')
        print(f"  ✅ Создан: {js_file}")
    
    print(f"✅ Резервные JS файлы созданы в: {js_dir}")
    return str(js_dir)

def clean_build_dirs():
    """Очистка директорий сборки"""
    print("🧹 Очистка директорий сборки...")
    
    # Удаляем директории build и dist, если они существуют
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Директория {dir_name} удалена")
            except Exception as e:
                print(f"❌ Ошибка при удалении директории {dir_name}: {e}")
    
    # Удаляем .spec файлы
    for spec_file in Path('.').glob('*.spec'):
        try:
            os.remove(spec_file)
            print(f"✅ Файл {spec_file} удален")
        except Exception as e:
            print(f"❌ Ошибка при удалении файла {spec_file}: {e}")

def check_main_file():
    """Проверка существования главного файла"""
    print("🔍 Проверка главного файла...")
    
    # Проверяем возможные имена главного файла
    possible_files = ['main.py']
    main_file = None
    
    for file in possible_files:
        if os.path.exists(file):
            main_file = file
            print(f"✅ Найден главный файл: {file}")
            break
    
    if not main_file:
        print("❌ Главный файл не найден!")
        print("💡 Убедитесь, что один из файлов существует:")
        for file in possible_files:
            print(f"   - {file}")
        return None
    
    return main_file

def check_and_fix_pathlib():
    """Проверка и исправление проблемы с пакетом pathlib"""
    print("🔍 Проверка пакета pathlib...")
    
    try:
        # Проверяем, установлен ли пакет pathlib
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', 'pathlib'],
            capture_output=True, text=True
        )
        
        # Если pathlib установлен как отдельный пакет, удаляем его
        if result.returncode == 0:
            print("⚠️ Обнаружен пакет pathlib, который может вызвать конфликты. Удаляем...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', 'pathlib', '-y'],
                capture_output=True, text=True
            )
            print("✅ Пакет pathlib удален")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке/исправлении pathlib: {e}")
        return False

def check_and_create_dirs():
    """Проверяет и создает необходимые директории"""
    print("🔍 Проверка необходимых директорий...")
    
    # Создаем директории если их нет
    for dir_name in ['logs', 'output']:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name)
                print(f"✅ Создана директория {dir_name}")
            except Exception as e:
                print(f"❌ Ошибка при создании директории {dir_name}: {e}")
    
    # Проверяем config.txt
    if not os.path.exists('config.txt'):
        try:
            with open('config.txt', 'w', encoding='utf-8') as f:
                f.write("TELEGRAM_BOT_TOKEN=your_bot_token_here\n")
                f.write("TELEGRAM_CHAT_ID=your_chat_id_here\n")
            print("✅ Создан файл config.txt")
        except Exception as e:
            print(f"❌ Ошибка при создании файла config.txt: {e}")
    else:
        print("✅ Файл config.txt найден")
    
    return True

def create_spec_file(main_file):
    """Создание .spec файла для PyInstaller"""
    print("📝 Создание .spec файла...")
    
    # Получаем пути к selenium_stealth
    stealth_path, js_path = get_selenium_stealth_path()
    
    # Определяем, нужна ли консоль (для отладки)
    # console_mode = input("🖥️ Показывать консоль для отладки? (y/n): ").lower().strip() == 'y'
    
    # Собираем дополнительные файлы
    data_files = []
    additional_files = [
        'config.txt',
        'logs', 
        'output'
    ]
    
    print("🔍 Поиск дополнительных файлов...")
    for file in additional_files:
        if os.path.exists(file):
            if os.path.isdir(file):
                data_files.append(f"('{file}', '{file}')")
                print(f"  ✅ {file}/ (папка)")
            else:
                data_files.append(f"('{file}', '.')")
                print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} - не найден")
    
    # Добавляем selenium_stealth JS файлы если найдены
    if js_path and os.path.exists(js_path):
        # Нормализуем путь для Windows
        js_path_normalized = js_path.replace('\\', '\\\\')
        data_files.append(f"(r'{js_path_normalized}', 'selenium_stealth/js')")
        print(f"  ✅ selenium_stealth JS файлы: {js_path}")
    else:
        # Создаем резервные JS файлы
        fallback_js_path = create_selenium_stealth_fallback()
        fallback_js_path_normalized = fallback_js_path.replace('\\', '\\\\')
        data_files.append(f"(r'{fallback_js_path_normalized}', 'selenium_stealth/js')")
        print(f"  ✅ Резервные selenium_stealth JS файлы: {fallback_js_path}")
    
    # Формируем строку с данными
    if data_files:
        datas_line = f"datas=[{', '.join(data_files)}],"
        print(f"📦 Будут включены файлы: {len(data_files)} элементов")
    else:
        datas_line = "datas=[],"
        print("📦 Дополнительные файлы не найдены")
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Определяем пути к файлам
base_path = Path('.').absolute()

# Собираем все необходимые данные
a = Analysis(
    ['{main_file}'],
    pathex=[str(base_path)],
    binaries=[],
    {datas_line}
    hiddenimports=[
        'tkinter', 
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium_stealth',
        'undetected_chromedriver',
        'telegram',
        'telegram.ext',
        'json',
        'logging',
        'threading',
        'queue',
        'time',
        'datetime',
        'os',
        'sys',
        're',
        'requests',
        'bs4',
        'lxml',
        'openpyxl',
        'pandas',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OZONPARSER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico' if Path('logo.ico').exists() else None,
)
"""
    
    # Записываем .spec файл
    spec_path = 'ozonparser.spec'
    try:
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print(f"✅ Файл {spec_path} создан")
        return spec_path
    except Exception as e:
        print(f"❌ Ошибка при создании .spec файла: {e}")
        return None

def simple_build_exe(main_file):
    """Простая сборка .exe файла"""
    print("🔄 Запуск простой сборки...")
    
    # Получаем пути к selenium_stealth
    stealth_path, js_path = get_selenium_stealth_path()
    
    try:
        # Определяем, нужна ли консоль
        console_mode = input("🖥️ Показывать консоль для отладки? (y/n): ").lower().strip() == 'y'
        
        # Используем простую команду PyInstaller
        cmd = [
            sys.executable, 
            '-m', 
            'PyInstaller',
            '--name=OZONPARSER',
            '--onefile',
            '--clean',
            '--add-data', f'config.txt{os.pathsep}.',
            '--add-data', f'logs{os.pathsep}logs',
            '--add-data', f'output{os.pathsep}output',
        ]
        
        # Добавляем selenium_stealth JS файлы
        if js_path and os.path.exists(js_path):
            cmd.extend(['--add-data', f'{js_path}{os.pathsep}selenium_stealth/js'])
            print(f"  ✅ Добавлены selenium_stealth JS файлы: {js_path}")
        else:
            # Создаем резервные JS файлы
            fallback_js_path = create_selenium_stealth_fallback()
            cmd.extend(['--add-data', f'{fallback_js_path}{os.pathsep}selenium_stealth/js'])
            print(f"  ✅ Добавлены резервные selenium_stealth JS файлы: {fallback_js_path}")
        
        # Добавляем режим консоли
        if console_mode:
            cmd.append('--console')
        else:
            cmd.append('--windowed')
        
        # Добавляем скрытые импорты
        hidden_imports = [
            'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
            'selenium', 'selenium_stealth', 'undetected_chromedriver',
            'telegram', 'requests', 'bs4', 'lxml', 'openpyxl', 'pandas', 'dotenv'
        ]
        
        for imp in hidden_imports:
            cmd.extend(['--hidden-import', imp])
        
        if os.path.exists('logo.ico'):
            cmd.extend(['--icon=logo.ico'])
        
        cmd.append(main_file)
        
        print(f"Выполняем команду: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Простая сборка успешно завершена!")
            return True
        else:
            print("❌ Ошибка при простой сборке:")
            if result.stdout:
                print("📋 STDOUT:")
                print(result.stdout[-2000:])
            if result.stderr:
                print("🚨 STDERR:")
                print(result.stderr[-2000:])
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при простой сборке: {e}")
        return False

def build_exe():
    """Сборка исполняемого файла"""
    print("🚀 Начинаем сборку OZONPARSER.exe...")
    
    # Проверяем главный файл
    main_file = check_main_file()
    if not main_file:
        return False
    
    # Очищаем директории сборки
    clean_build_dirs()
    
    # Проверяем и создаем необходимые директории
    check_and_create_dirs()
    
    # Проверяем и исправляем проблему с pathlib
    if not check_and_fix_pathlib():
        return False
    
    # Спрашиваем пользователя о методе сборки
    use_spec = input("📝 Использовать .spec файл? (y/n): ").lower().strip() == 'y'
    
    if use_spec:
        # Создаем .spec файл
        spec_file = create_spec_file(main_file)
        if not spec_file:
            return False
        
        # Запускаем PyInstaller
        print("⚙️ Запуск PyInstaller с .spec файлом...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'PyInstaller', '--clean', spec_file],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ Сборка успешно завершена!")
                return check_exe_file()
            else:
                print("❌ Ошибка при сборке:")
                print_error_details(result)
                # Пробуем простую сборку
                print("🔄 Пробую простую сборку...")
                return simple_build_exe(main_file)
                
        except FileNotFoundError:
            return install_pyinstaller_and_retry(main_file)
    else:
        # Простая сборка
        return simple_build_exe(main_file)

def check_exe_file():
    """Проверка созданного исполняемого файла"""
    exe_path = Path('dist/OZONPARSER.exe')
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"📊 Размер файла: {size_mb:.1f} MB")
        print(f"📁 Исполняемый файл находится в: {exe_path.absolute()}")
        
        print("\n🎉 Сборка успешно завершена! 🎉")
        print("📁 Проверьте папку dist/")
        print("🖼️ Иконка установлена (если logo.ico найдена)")
        print("📦 Все необходимые файлы включены в .exe")
        
        # Предлагаем тестирование
        test_exe = input("🧪 Протестировать созданный .exe файл? (y/n): ").lower().strip() == 'y'
        if test_exe:
            print("🚀 Запуск тестирования...")
            try:
                subprocess.Popen([str(exe_path)])
                print("✅ Файл запущен для тестирования")
            except Exception as e:
                print(f"❌ Ошибка при запуске: {e}")
        
        return True
    else:
        print("❌ Исполняемый файл не найден после сборки")
        return False

def print_error_details(result):
    """Вывод подробностей ошибки"""
    print("\n--- ПОДРОБНАЯ ИНФОРМАЦИЯ ОБ ОШИБКЕ ---")
    if result.stdout:
        print("📋 STDOUT:")
        print(result.stdout[-2000:])
    if result.stderr:
        print("🚨 STDERR:")
        print(result.stderr[-2000:])
    print("--- КОНЕЦ ИНФОРМАЦИИ ОБ ОШИБКЕ ---\n")

def install_pyinstaller_and_retry(main_file):
    """Установка PyInstaller и повторная попытка"""
    print("❌ PyInstaller не найден. Устанавливаю...")
    try:
        # Пытаемся установить PyInstaller
        install_result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'pyinstaller'
        ], capture_output=True, text=True)
        
        if install_result.returncode == 0:
            print("✅ PyInstaller установлен успешно")
            # Повторяем попытку сборки
            return simple_build_exe(main_file)
        else:
            print("❌ Не удалось установить PyInstaller:")
            print(install_result.stderr)
            return False
    except Exception as e:
        print(f"❌ Ошибка при установке PyInstaller: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Исправленная сборка OZONPARSER.exe")
    print("=" * 60)
    
    success = build_exe()
    
    if success:
        print("\n✅ Сборка успешно завершена!")
        print("💡 Если окно не появляется, попробуйте:")
        print("   1. Пересобрать с включенной консолью для отладки")
        print("   2. Проверить логи приложения")
        print("   3. Запустить от имени администратора")
    else:
        print("\n❌ Сборка завершилась с ошибками")
        print("💡 Попробуйте:")
        print("   1. Проверить наличие всех зависимостей")
        print("   2. Установить недостающие пакеты")
        print("   3. Запустить скрипт от имени администратора")
    
    print("=" * 60)