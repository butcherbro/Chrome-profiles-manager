# Omega proxy setup

Скрипт для настройки расширения [Proxy SwitchyOmega](https://chromewebstore.google.com/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif) через Selenium.

## config.json
```run_delay_sec``` - _задержка после открытия профиля и перед началом выполнения логики._  
```extension_id``` - _ID расширения. Совпадает с названием распакованной папки расширения. Обычно он одинаковый у всех пользователей._  

## proxies.txt
_Задаем прокси для профилей, каждый с новой строки в формате "название_профиля|proto://user:pass@host:port"._ Название профиля, естественно, должно совпадать с названием которое вы задали своему профилю при создании.
