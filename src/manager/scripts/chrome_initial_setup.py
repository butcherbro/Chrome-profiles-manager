import json
import time

from pathlib import Path
from src.chrome.chrome import Chrome
from src.utils.constants import *


GENERAL_PREFERENCES = {
    "cookies_control_modes": {
        "access": ["profile", "cookie_controls_mode"],
        "human_name": "запрет на использование cookie",
        "default_safe_value": 1,
        "options": {
            "block_all": {
                "human_name": "запретить все cookie файлы",
                "value": 1
            },
            "block_in_incognito": {
                "human_name": "запретить cookie файлы в режиме инкогнито",
                "value": 2
            }
        }
    },
    "anon_data_collection": {
        "access": ["url_keyed_anonymized_data_collection"],
        "human_name": "сбор анонимных данных",
        "default_safe_value": False,
        "options": {
            "block": {
                "human_name": "запретить",
                "value": False
            },
            "allow": {
                "human_name": "разрешить",
                "value": True
            }
        }
    },
    "enhanced_data_protection": {
        "access": ["safebrowsing", "enhanced"],
        "human_name": "улучшенная защита данных используя сервера google",
        "default_safe_value": False,
        "options": {
            "block": {
                "human_name": "запретить",
                "value": False
            },
            "allow": {
                "human_name": "разрешить",
                "value": True
            }
        }
    },

    "allow_chrome_sign_in": {
        "access": ["signing", "allowed"],
        "human_name": "разрешить вход в google аккаунт",
        "default_safe_value": False,
        "options": {
            "block": {
                "human_name": "запретить",
                "value": False
            },
            "allow": {
                "human_name": "разрешить",
                "value": True
            }
        }
    },
    "allow_chrome_sign_in_on_next_startup": {
        "access": ["signing", "allowed_on_next_startup"],
        "human_name": "разрешить вход в google аккаунт при следующем запуске профиля",
        "default_safe_value": False,
        "options": {
            "block": {
                "human_name": "запретить",
                "value": False
            },
            "allow": {
                "human_name": "разрешить",
                "value": True
            }
        }
    },
    "search_suggestions": {
        "access": ["search", "suggest_enabled"],
        "human_name": "улучшить поисковые предложения",
        "default_safe_value": False,
        "options": {
            "block": {
                "human_name": "запретить",
                "value": False
            },
            "allow": {
                "human_name": "разрешить",
                "value": True
            }
        }
    },
    "enhanced_spell_check": {
        "access": ["spellcheck", "use_spelling_service"],
        "human_name": "расширенная проверка орфографии",
        "default_safe_value": False,
        "options": {
            "block": {
                "human_name": "запретить",
                "value": False
            },
            "allow": {
                "human_name": "разрешить",
                "value": True
            }
        }
    },

    "autofill_credentials": {
        "access": ["password_manager"],
        "human_name": "расширенная проверка орфографии",
        "default_safe_value": {
                    "autofillable_credentials_account_store_login_database": False,
                    "autofillable_credentials_profile_store_login_database": False
                },
        "options": {
            "block": {
                "human_name": "запретить",
                "value": {
                    "autofillable_credentials_account_store_login_database": False,
                    "autofillable_credentials_profile_store_login_database": False
                }
            },
            "allow": {
                "human_name": "разрешить",
                "value": {
                    "autofillable_credentials_account_store_login_database": True,
                    "autofillable_credentials_profile_store_login_database": True
                }
            }
        }
    }
}

PROFILE_SPECIFIC_PREFERENCES = {
    "name": {
        "access": ["profile", "name"],
        "human_name": "имя профиля",
        "options": None
    },
    "theme_color": {
        "access": ["browser", "theme", "user_color"],
        "human_name": "цвет профиля",
        "options": None
    }
}


def chrome_initial_setup(profile_name: str, _) -> None:
    profile_preferences_path = CHROME_DATA_PATH / f"Profile {profile_name}" / "Preferences"

    if not profile_preferences_path.exists():
        chrome = Chrome()
        chrome.init_profile_preferences(profile_name)
        time.sleep(5)

    with open(profile_preferences_path, "r", encoding="utf-8") as f:
        preferences_file = json.load(f)

    for setting, data in GENERAL_PREFERENCES.items():
        value_to_set = data["default_safe_value"]

        final_update_path = preferences_file
        for key in data["access"][:-1]:
            final_update_path = final_update_path.setdefault(key, {})

        final_update_path[data["access"][-1]] = value_to_set

    with open(profile_preferences_path, "w", encoding="utf-8") as f:
        json.dump(preferences_file, f, indent=4, ensure_ascii=False)


# ЦВЕТ ПРОФИЛЯ

# # Decimal color value
# decimal_color = -1714692
#
# # Convert the decimal to an unsigned 32-bit integer, then to hexadecimal
# hex_color = f"#{decimal_color & 0xFFFFFF:06X}"
#
# print(hex_color)

# UPDATE
# "browser": {
#     "theme": {
#         "color_variant": 1,
#         "follows_system_colors": false,
#         "user_color": -1714692
#     },

# ADD / UPDATE
# "colorpicker": {
#     "SeedColorChangeCount": 1
# },