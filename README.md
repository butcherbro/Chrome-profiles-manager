# Chrome Profiles Manager

Менеджер профилей Chrome с графическим интерфейсом для удобного управления несколькими профилями браузера.

## Возможности

- Создание и управление несколькими профилями Chrome
- Копирование расширений между профилями с сохранением настроек
- Умное копирование настроек кошельков (MetaMask, Rabby и др.) с сохранением существующих
- Удобный графический интерфейс для управления профилями
- Предотвращение запуска нескольких экземпляров приложения

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/butcherbro/Chrome-profiles-manager.git
cd Chrome-profiles-manager
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройка профилей и расширений:
- Создайте папку `data/profiles` для хранения профилей Chrome
- Создайте папку `data/default_extensions` для хранения расширений
- Скопируйте нужные расширения в папку `data/default_extensions`
  - Каждое расширение должно быть в отдельной папке с его ID
  - ID расширения можно найти в Chrome Web Store в URL расширения
  - Пример структуры:
    ```
    data/default_extensions/
    ├── nkbihfbeogaeaoehlefnkodbefgpgknn/  # MetaMask
    ├── fhbohimaelbohpjbbldcnglifacahlip/  # Rabby
    └── other_extension_id/                 # Другие расширения
    ```

## Использование

1. Запустите приложение:
```bash
python main_gui.py
```

2. Используйте графический интерфейс для:
   - Создания новых профилей
   - Запуска существующих профилей
   - Копирования расширений между профилями
   - Управления настройками расширений

## Особенности

- Безопасное копирование расширений с сохранением существующих настроек кошельков
- Предотвращение конфликтов при запуске нескольких копий приложения
- Автоматическое создание необходимых директорий и файлов

## Настройка Playwright и решение проблем с расширениями

### Ключевые особенности реализации

1. Прямой запуск Chrome вместо управляемого Playwright:
```python
launch_args = [
    CHROME_PATH,
    f"--user-data-dir={CHROME_DATA_PATH}",
    f"--profile-directory=Profile {profile_name}",
    "--enable-extensions",  # Важно для работы расширений
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

chrome_process = subprocess.Popen(
    launch_args,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
```

2. Подключение через Chrome DevTools Protocol (CDP):
```python
browser = playwright.chromium.connect_over_cdp(
    f"http://localhost:{debug_port}"
)
```

3. Использование существующего контекста:
```python
contexts = browser.contexts
if not contexts:
    raise Exception("Не найден контекст браузера")
context = contexts[0]
```

### Важные флаги запуска Chrome

- `--enable-extensions`: Включает поддержку расширений
- `--disable-background-timer-throttling`: Предотвращает замедление фоновых таймеров
- `--disable-backgrounding-occluded-windows`: Предотвращает приостановку скрытых окон
- `--disable-renderer-backgrounding`: Отключает фоновый режим для рендерера

### Процесс запуска профиля

1. Подготовка:
   - Закрытие всех процессов Chrome
   - Проверка существования профиля
   - Поиск установленных расширений
   - Добавление MetaMask если отсутствует

2. Запуск Chrome:
   - Использование свободного порта для отладки
   - Запуск Chrome через subprocess
   - Ожидание доступности порта отладки
   - Подключение через CDP
   - Получение существующего контекста браузера

### Работа с расширениями

1. Поиск расширений в профиле:
```python
extensions_path = os.path.join(profile_path, "Extensions")
if os.path.exists(extensions_path):
    for ext_id in os.listdir(extensions_path):
        ext_path = os.path.join(extensions_path, ext_id)
        if os.path.isdir(ext_path):
            versions = [v for v in os.listdir(ext_path) 
                       if os.path.isdir(os.path.join(ext_path, v))]
            if versions:
                latest = sorted(versions)[-1]
                ext_version_path = os.path.join(ext_path, latest)
                extensions.append(ext_version_path)
```

2. Загрузка расширений:
```python
if profile_extensions:
    extensions_arg = ",".join(profile_extensions)
    launch_args.append(f"--load-extension={extensions_arg}")
```

### Проверка MetaMask

1. Проверка наличия:
```python
metamask_path = os.path.join(DEFAULT_EXTENSIONS_PATH, "nkbihfbeogaeaoehlefnkodbefgpgknn")
if os.path.exists(metamask_path):
    metamask_profile_path = os.path.join(profile_path, "Extensions", "nkbihfbeogaeaoehlefnkodbefgpgknn")
    if not os.path.exists(metamask_profile_path):
        os.makedirs(os.path.dirname(metamask_profile_path), exist_ok=True)
        shutil.copytree(metamask_path, metamask_profile_path, dirs_exist_ok=True)
```

2. Верификация через chrome.management API:
```javascript
chrome.management.get('nkbihfbeogaeaoehlefnkodbefgpgknn', (extension) => {
    resolve(!!extension);
});
```

### Решение проблем

1. Если расширения не загружаются:
   - Проверьте наличие флага `--enable-extensions`
   - Убедитесь, что путь к расширениям указан корректно
   - Проверьте права доступа к папкам расширений

2. Если MetaMask не отображается:
   - Проверьте корректность ID расширения
   - Убедитесь, что расширение скопировано в профиль
   - Проверьте версию расширения на совместимость

3. Если не удается подключиться через CDP:
   - Увеличьте время ожидания доступности порта
   - Проверьте, не занят ли порт другим процессом
   - Убедитесь, что Chrome запущен с флагом отладки

## Требования

- Python 3.8+
- Google Chrome
- PyQt6
- Дополнительные зависимости указаны в requirements.txt

## Безопасность

- Все данные профилей хранятся локально и не загружаются на GitHub
- Настройки кошельков и другие чувствительные данные не передаются между профилями
- Каждый пользователь создает и настраивает свои профили независимо

## Лицензия

MIT License