# -*- coding: utf-8 -*-
"""Localized strings for the Navisworks view settings and profile editor.

The two windows take their static text from their own
``*.ResourceDictionary.<locale>.xaml`` files; this catalog covers the combo-box
captions, the alerts and the messages built while the windows run.

Stored values stay English: a detail level, a display style and a profile id
are written into the pyArchitect configuration and mapped onto Revit API enum
members by name, so only their captions are translated.
"""

from core.localization import StringTable


S = StringTable({
    "settings.title": {
        "en_us": u"Batch NavisView settings",
        "ru": u"Настройки пакетного NavisView",
        "es_es": u"Ajustes de NavisView (lote)",
    },
    "profiles.title": {
        "en_us": u"NavisView profiles",
        "ru": u"Профили NavisView",
        "es_es": u"Perfiles de NavisView",
    },

    "detail.Coarse": {
        "en_us": u"Coarse",
        "ru": u"Низкий",
        "es_es": u"Bajo",
    },
    "detail.Medium": {
        "en_us": u"Medium",
        "ru": u"Средний",
        "es_es": u"Medio",
    },
    "detail.Fine": {
        "en_us": u"Fine",
        "ru": u"Высокий",
        "es_es": u"Alto",
    },
    "style.Wireframe": {
        "en_us": u"Wireframe",
        "ru": u"Каркас",
        "es_es": u"Estructura alámbrica",
    },
    "style.HiddenLine": {
        "en_us": u"Hidden line",
        "ru": u"Невидимые линии",
        "es_es": u"Línea oculta",
    },
    "style.Shading": {
        "en_us": u"Shaded",
        "ru": u"Тонирование",
        "es_es": u"Sombreado",
    },
    "style.FlatColors": {
        "en_us": u"Flat colors",
        "ru": u"Однотонная заливка",
        "es_es": u"Colores planos",
    },
    "style.ConsistentColors": {
        "en_us": u"Consistent colors",
        "ru": u"Однородные цвета",
        "es_es": u"Colores coherentes",
    },
    "style.Realistic": {
        "en_us": u"Realistic",
        "ru": u"Реалистичный",
        "es_es": u"Realista",
    },

    "alert.view_name_required": {
        "en_us": u"Specify a Navisworks 3D view name.",
        "ru": u"Укажите имя 3D-вида для Navisworks.",
        "es_es": u"Indica un nombre para la vista 3D de Navisworks.",
    },
    "alert.profile_required": {
        "en_us": u"Select a default profile.",
        "ru": u"Выберите профиль по умолчанию.",
        "es_es": u"Selecciona un perfil predeterminado.",
    },
    "alert.detail_and_style_required": {
        "en_us": u"Select a detail level and display style.",
        "ru": u"Выберите уровень детализации и визуальный стиль.",
        "es_es": u"Selecciona un nivel de detalle y un estilo visual.",
    },
    "alert.transparency_range": {
        "en_us": u"Surface transparency must be a whole number from 0 to 100.",
        "ru": u"Прозрачность поверхностей задаётся целым числом от 0 до 100.",
        "es_es": u"La transparencia debe ser un número entero de 0 a 100.",
    },
    "alert.profiles_open_failed": {
        "en_us": u"Cannot open profile presets:\n{}",
        "ru": u"Не удалось открыть профили:\n{}",
        "es_es": u"No se pueden abrir los perfiles:\n{}",
    },
    "alert.profiles_not_saved": {
        "en_us": u"Profile presets were not saved:\n{}",
        "ru": u"Профили не сохранены:\n{}",
        "es_es": u"Los perfiles no se han guardado:\n{}",
    },
    "alert.profiles_saved": {
        "en_us": u"Profiles saved to the pyArchitect configuration.",
        "ru": u"Профили сохранены в конфигурации pyArchitect.",
        "es_es": u"Perfiles guardados en la configuración de pyArchitect.",
    },

    "editor.new_preset": {
        "en_us": u"New preset",
        "ru": u"Новый профиль",
        "es_es": u"Perfil nuevo",
    },
    "editor.universal_protected": {
        "en_us": u"The UNIVERSAL preset is the required default and cannot be deleted.",
        "ru": u"Профиль UNIVERSAL обязателен как профиль по умолчанию и не удаляется.",
        "es_es": u"El perfil UNIVERSAL es el predeterminado obligatorio y no se "
                 u"puede eliminar.",
    },
    "editor.delete_confirm": {
        "en_us": u"Delete the '{}' preset?",
        "ru": u"Удалить профиль «{}»?",
        "es_es": u"¿Eliminar el perfil «{}»?",
    },
    "editor.at_least_one": {
        "en_us": u"At least the UNIVERSAL preset is required.",
        "ru": u"Нужен хотя бы профиль UNIVERSAL.",
        "es_es": u"Se requiere al menos el perfil UNIVERSAL.",
    },
    "editor.category_unavailable": {
        "en_us": u"{} (not available in this Revit version)",
        "ru": u"{} (нет в этой версии Revit)",
        "es_es": u"{} (no disponible en esta versión de Revit)",
    },
    "editor.category_unavailable_tooltip": {
        "en_us": u"{} is not available in the running Revit version and cannot "
                 u"be edited.",
        "ru": u"Категория {} отсутствует в запущенной версии Revit, изменить её "
              u"нельзя.",
        "es_es": u"La categoría {} no existe en la versión de Revit en uso y no "
                 u"se puede editar.",
    },

    "profiles.migrate_failed": {
        "en_us": u"Cannot migrate stored Navisworks profiles: {}",
        "ru": u"Не удалось перенести сохранённые профили Navisworks: {}",
        "es_es": u"No se pueden migrar los perfiles de Navisworks guardados: {}",
    },
    "profiles.migrate_path_failed": {
        "en_us": u"Cannot migrate Navisworks profiles from '{}': {}",
        "ru": u"Не удалось перенести профили Navisworks из «{}»: {}",
        "es_es": u"No se pueden migrar los perfiles de Navisworks desde «{}»: {}",
    },
    "profiles.read_failed": {
        "en_us": u"Cannot read configured Navisworks profiles: {}",
        "ru": u"Не удалось прочитать настроенные профили Navisworks: {}",
        "es_es": u"No se pueden leer los perfiles de Navisworks configurados: {}",
    },
    "profiles.required": {
        "en_us": u"At least one Navisworks profile is required",
        "ru": u"Нужен хотя бы один профиль Navisworks",
        "es_es": u"Se requiere al menos un perfil de Navisworks",
    },
})
