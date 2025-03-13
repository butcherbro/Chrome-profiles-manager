# Playwright в Chrome Profiles Manager

## Обзор

Данный модуль предоставляет возможность автоматизации работы с профилями Chrome с использованием библиотеки Playwright. Основные преимущества:

- Работа с существующими профилями Chrome (включая расширения)
- Синхронный и асинхронный API
- Автоматизация действий с расширениями (например, MetaMask)
- Гибкая конфигурация через JSON-файлы

## Установка зависимостей

```bash
pip install playwright
playwright install chromium
```

## Структура модуля

```
src/
├── chrome/
│   ├── config/
│   │   ├── chrome_launch_config.json  # Конфигурация запуска Chrome
│   │   └── metamask_config.json       # Конфигурация для работы с MetaMask
│   ├── automation.py                  # Асинхронный API для Playwright
│   └── playwright_chrome.py           # Синхронный API для Playwright
└── scripts/
    └── metamask_import.py             # Скрипт для импорта MetaMask
```

## Использование

### Запуск профиля Chrome

```python
from src.chrome.playwright_chrome import PlaywrightChrome

# Создаем экземпляр класса
chrome = PlaywrightChrome()

# Запускаем профиль
profile_name = "0"  # Имя профиля
result = chrome.launch_profile(profile_name, headless=False)

if result:
    # Открываем страницу
    chrome.page.goto("https://www.google.com")
    
    # Делаем скриншот
    chrome.page.screenshot(path="screenshot.png")
    
    # Закрываем браузер
    chrome.close()
```

### Импорт кошелька MetaMask

```python
import asyncio
from src.scripts.metamask_import import MetamaskImport

async def import_metamask():
    # Создаем экземпляр класса
    metamask = MetamaskImport("0")  # Имя профиля
    
    # Импортируем кошелек
    seed_phrase = "your seed phrase here"
    password = "your password here"
    
    result = await metamask.import_wallet(seed_phrase, password)
    
    # Добавляем сеть
    network_config = {
        "name": "Optimism",
        "rpc_url": "https://mainnet.optimism.io",
        "chain_id": "10",
        "currency_symbol": "ETH",
        "block_explorer_url": "https://optimistic.etherscan.io"
    }
    
    await metamask.add_network(network_config)

# Запускаем асинхронную функцию
asyncio.run(import_metamask())
```

## Конфигурация

### chrome_launch_config.json

Файл конфигурации для запуска Chrome содержит следующие параметры:

- `debug_port`: Порт для подключения к Chrome DevTools Protocol
- `launch_flags`: Флаги запуска Chrome
  - `required`: Обязательные флаги
  - `optional`: Опциональные флаги
- `timeouts`: Таймауты для различных операций
- `extensions`: Настройки для работы с расширениями
- `urls`: URL-адреса для различных операций

### metamask_config.json

Файл конфигурации для работы с MetaMask содержит:

- `selectors`: CSS-селекторы для элементов интерфейса MetaMask
- `timeouts`: Таймауты для различных операций
- `networks`: Конфигурации сетей для добавления в MetaMask

## Тестирование

Для тестирования функциональности можно использовать скрипт `test_playwright.py`:

```bash
# Тестирование запуска Chrome
python test_playwright.py chrome

# Тестирование импорта MetaMask
python test_playwright.py metamask
```

## Примечания

- Для работы с профилями необходимо, чтобы они уже существовали
- Расширения должны быть установлены в профиле
- При работе с MetaMask используются CSS-селекторы, которые могут измениться при обновлении расширения

## Отладка

Логи сохраняются в файл `data/playwright_test.log`. Для отладки можно увеличить уровень логирования:

```python
logger.remove()
logger.add(sys.stderr, level="DEBUG")
```

## Известные проблемы

1. При запуске Chrome в headless режиме некоторые расширения могут работать некорректно
2. При изменении версии MetaMask могут измениться селекторы элементов
3. При одновременном запуске нескольких экземпляров Chrome с одним профилем могут возникнуть конфликты 