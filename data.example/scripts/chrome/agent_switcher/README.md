# Agent switcher

Скрипт для настройки расширения [Random User-Agent (Switcher)](https://chromewebstore.google.com/detail/random-user-agent-switche/einpaelgookohagofgnnkcfjbkkgepnp?pli=1) через Selenium.

## config.json
```run_delay_sec``` - _задержка после открытия профиля и перед началом выполнения логики._  
```extension_id``` - _ID расширения. Совпадает с названием распакованной папки расширения. Обычно он одинаковый у всех пользователей._  
```general_settings``` - _общие настройки расширения. "human_name" содержит описание параметра, его не трогаем, просто читаем, "must_be_enabled" - задаем значения "true" / "false"._  
```generator_settings``` - _настройки генератора UserAgent. "human_name" содержит описание параметра, его не трогаем, просто читаем, "must_be_enabled" - задаем значения "true" / "false"._
