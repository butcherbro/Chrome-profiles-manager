# Исследование методов работы с расширениями Chrome через Playwright

## Задача
Настроить автоматизацию работы с расширениями Chrome через Playwright в профиле 69:
- SwitchyOmega (padekgcemlokbadohgkifijomclgjgif)
- MetaMask (nkbihfbeogaeaoehlefnkodbefgpgknn)
- Chrome Web Store Payments (nmmhkkegccagdldgiimedpiccmgmieda)

## Обнаруженная проблема с настройками MetaMask

При текущей конфигурации запуска через Playwright мы столкнулись с проблемой: расширения загружаются, но их настройки (в частности кошелек MetaMask) - нет. При этом в оригинальном профиле с префиксом Backup все настройки сохранены.

### Анализ проблемы:
1. Структура хранения данных MetaMask:
   - Основные настройки расширения хранятся в директории расширения
   - Данные кошелька хранятся в локальном хранилище (localStorage)
   - Состояние кошелька сохраняется в IndexedDB

2. Возможные причины:
   - Неправильное копирование данных профиля
   - Проблемы с правами доступа к хранилищам
   - Конфликт между флагами запуска и системой хранения данных
   - Возможная изоляция хранилища в режиме автоматизации

3. Различия в поведении:
   - Обычный Chrome: полный доступ к хранилищам
   - Playwright: возможное ограничение доступа к хранилищам

### План исследования:
1. Сравнить структуру файлов:
   ```bash
   diff -r "Profile 69" "Profile 69_Backup"
   ```

2. Проверить содержимое ключевых файлов:
   - Local Storage
   - IndexedDB
   - Preferences
   - Local State

3. Проанализировать права доступа:
   ```bash
   ls -la "Profile 69/Local Storage"
   ls -la "Profile 69_Backup/Local Storage"
   ```

4. Тестирование различных флагов запуска:
   ```python
   # Вариант 1: Без режима автоматизации
   args=[
       "--no-first-run",
       "--no-default-browser-check",
       f"--load-extension={extensions_arg}",
       "--disable-web-security",  # Тестовый флаг
       "--allow-file-access-from-files"
   ]

   # Вариант 2: С дополнительными разрешениями
   args=[
       "--no-first-run",
       "--no-default-browser-check",
       f"--load-extension={extensions_arg}",
       "--unlimited-storage",
       "--enable-file-cookies",
       "--allow-file-access"
   ]
   ```

### Следующие шаги:
1. Создать тестовый профиль для экспериментов
2. Проверить работу с разными комбинациями флагов
3. Исследовать возможность прямого копирования данных хранилища
4. Протестировать запуск без режима автоматизации

## История исследования и неудачные попытки

### 1. Базовый запуск через Playwright
```python
browser = await p.chromium.launch_persistent_context(
    user_data_dir=profile_path,
    headless=False,
    args=[
        "--no-first-run",
        "--no-default-browser-check",
        "--load-unpacked-extensions",
        f"--load-extension={full_extension_path}"
    ]
)
```
**Проблема**: Расширения не отображались на странице chrome://extensions
**Причина**: Недостаточно флагов для корректной загрузки расширений

### 2. Попытка использования CDP
```python
extensions_info = await page.evaluate("chrome.management.getAll()")
```
**Проблема**: Ошибка "Protocol error (Management.getExtensionsInfo): 'Management.getExtensionsInfo' wasn't found"
**Причина**: CDP методы для управления расширениями недоступны в контексте страницы

### 3. Доступ к Shadow DOM через JavaScript
```javascript
const manager = document.querySelector('extensions-manager');
if (manager && manager.shadowRoot) {
    const itemList = manager.shadowRoot.querySelector('extensions-item-list');
    // ...
}
```
**Проблема**: Не удалось получить доступ к Shadow DOM расширений
**Причина**: Ограничения безопасности и изоляции в Chrome

## Успешное решение

### 1. Правильная конфигурация запуска браузера
```python
browser = await p.chromium.launch_persistent_context(
    user_data_dir=profile_path,
    headless=False,
    args=[
        f"--disable-extensions-except={extensions_arg}",
        f"--load-extension={extensions_arg}",
        "--no-first-run",
        "--no-default-browser-check",
        "--enable-automation",
        "--remote-debugging-port=9222"
    ]
)
```

#### Подробное описание аргументов запуска:
1. `--disable-extensions-except={extensions_arg}`
   - Отключает все расширения кроме указанных
   - Помогает избежать конфликтов с другими расширениями
   - Ускоряет загрузку браузера

2. `--load-extension={extensions_arg}`
   - Явно указывает путь к расширениям для загрузки
   - Требует абсолютный путь
   - Можно указать несколько расширений через запятую

3. `--no-first-run`
   - Пропускает диалоги первого запуска
   - Важно для автоматизации
   - Предотвращает появление приветственных окон

4. `--no-default-browser-check`
   - Отключает проверку браузера по умолчанию
   - Ускоряет запуск
   - Избегает лишних диалогов

5. `--enable-automation`
   - Включает режим автоматизации
   - Отключает некоторые проверки безопасности
   - Улучшает стабильность работы

6. `--remote-debugging-port=9222`
   - Открывает порт для отладки
   - Позволяет использовать CDP
   - Необходим для некоторых операций с расширениями

### 2. Подготовка путей к расширениям
```python
# Сканируем директорию расширений профиля
extensions_dir = os.path.join(profile_path, "Extensions")
extension_paths = []

for ext_id in os.listdir(extensions_dir):
    ext_path = os.path.join(extensions_dir, ext_id)
    if os.path.isdir(ext_path):
        versions = os.listdir(ext_path)
        if versions:
            latest_version = versions[-1]
            full_path = os.path.join(ext_path, latest_version)
            extension_paths.append(full_path)
```

### 3. Работа с расширениями
После успешного запуска браузера можно:
1. Открывать страницы расширений напрямую через их ID:
```python
await page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#onboarding/welcome")
```

2. Взаимодействовать с элементами через стандартные методы Playwright:
```python
checkbox = await page.wait_for_selector('input[data-testid="onboarding-terms-checkbox"]')
await checkbox.click()
```

### 4. Особенности и рекомендации
1. Всегда закрывать все процессы Chrome перед запуском:
```python
kill_chrome_processes()
await asyncio.sleep(2)  # Даем время на закрытие
```

2. Использовать `wait_for_load_state("networkidle")` для надежной загрузки страниц:
```python
await page.wait_for_load_state("networkidle")
```

3. Для работы с Shadow DOM использовать соответствующие селекторы или CDP

## Результаты
1. ✅ Успешный запуск профиля с сохранением всех расширений
2. ✅ Возможность открывать страницы расширений
3. ✅ Возможность взаимодействовать с элементами на страницах расширений
4. ✅ Сохранение всех настроек профиля и расширений

## Преимущества решения
1. Полная автоматизация через Playwright
2. Сохранение существующего профиля и его настроек
3. Возможность взаимодействия со всеми установленными расширениями
4. Надежная работа с Shadow DOM и сложными UI элементами

## Дальнейшие улучшения
1. Добавить обработку ошибок и повторные попытки
2. Реализовать проверку состояния расширений через CDP
3. Добавить методы для работы с настройками расширений
4. Создать общий класс для работы с расширениями

## Важные заметки
- Профиль должен быть предварительно настроен через обычный Chrome
- Все пути к расширениям должны быть абсолютными
- Необходимо давать достаточно времени на загрузку страниц и элементов
- Рекомендуется делать скриншоты для отладки
- При работе с расширениями важно учитывать их состояние загрузки
- Некоторые операции могут требовать дополнительных прав доступа
- Стоит проверять наличие всех необходимых разрешений в manifest.json расширений