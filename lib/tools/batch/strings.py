# -*- coding: utf-8 -*-
"""Localized strings shown by the batch commands.

Static window text lives in the ``batch_form.ResourceDictionary.<locale>.xaml``
files pyRevit merges into the form; this catalog covers everything the batch
code builds at runtime - option labels, validation hints, alerts, output
headings and result messages.

``en_us`` is the default and the only entry a key must have.  Status tokens
(``OK``, ``SKIPPED``, ``ERROR``, ``CREATED``...) stay English on purpose:
they are compared against in code rather than read.
"""

from core.localization import StringTable


S = StringTable({
    "form.source_description": {
        "en_us": u"Pick where the models come from, then load them.",
        "ru": u"Выберите, откуда взять модели, и загрузите их.",
        "es_es": u"Elige de dónde vienen los modelos y cárgalos.",
    },
    "form.selection_description": {
        "en_us": u"Tick the models to include in this batch run.",
        "ru": u"Отметьте модели, которые войдут в этот пакет.",
        "es_es": u"Marca los modelos que se incluyen en este lote.",
    },
    "form.options_description": {
        "en_us": u"These settings apply to every model you selected.",
        "ru": u"Эти настройки применяются ко всем выбранным моделям.",
        "es_es": u"Estos ajustes se aplican a todos los modelos seleccionados.",
    },
    "form.source_folder_tooltip": {
        "en_us": u"Pick the folder that holds the Revit models",
        "ru": u"Выберите папку с моделями Revit",
        "es_es": u"Elige la carpeta que contiene los modelos de Revit",
    },
    "form.save_options": {
        "en_us": u"Save options",
        "ru": u"Сохранить настройки",
        "es_es": u"Guardar opciones",
    },
    "form.error.nothing_loaded": {
        "en_us": u"Load models on the Selection tab first.",
        "ru": u"Сначала загрузите модели на вкладке «1. Выбор».",
        "es_es": u"Primero carga modelos en la pestaña «1. Selección».",
    },
    "form.error.nothing_ticked": {
        "en_us": u"Tick at least one model on the Selection properties tab.",
        "ru": u"Отметьте хотя бы одну модель на вкладке «2. Свойства выбора».",
        "es_es": u"Marca al menos un modelo en la pestaña "
                 u"«2. Propiedades de la selección».",
    },
    "form.hint.nothing_loaded": {
        "en_us": u"No models loaded — pick a folder or add RSN routes above.",
        "ru": u"Модели не загружены — выберите папку или добавьте маршруты RSN выше.",
        "es_es": u"No hay modelos cargados — elige una carpeta o añade rutas RSN arriba.",
    },
    "form.column.model": {
        "en_us": u"Model",
        "ru": u"Модель",
        "es_es": u"Modelo",
    },
    "form.apply_to_all": {
        "en_us": u"Apply to all",
        "ru": u"Применить ко всем",
        "es_es": u"Aplicar a todos",
    },
    "form.bulk_label": {
        "en_us": u"Set for all models",
        "ru": u"Задать для всех моделей",
        "es_es": u"Definir para todos los modelos",
    },
    "form.csv_error": {
        "en_us": u"Cannot read batch CSV: {}",
        "ru": u"Не удалось прочитать CSV пакета: {}",
        "es_es": u"No se puede leer el CSV del lote: {}",
    },

    "widgets.folder.pick": {
        "en_us": u"Pick a folder",
        "ru": u"Выберите папку",
        "es_es": u"Elige una carpeta",
    },
    "widgets.folder.default": {
        "en_us": u"Use the default folder",
        "ru": u"Использовать папку по умолчанию",
        "es_es": u"Usar la carpeta predeterminada",
    },

    "processor.requires_upgrade": {
        "en_us": u"Model requires upgrade",
        "ru": u"Модель требует обновления версии",
        "es_es": u"El modelo requiere actualización",
    },
    "processor.saved_copy": {
        "en_us": u"Saved copy: {}",
        "ru": u"Сохранена копия: {}",
        "es_es": u"Copia guardada: {}",
    },
    "processor.rsn_not_copyable": {
        "en_us": u"Revit Server routes cannot be copied to a local folder",
        "ru": u"Маршруты Revit Server нельзя скопировать в локальную папку",
        "es_es": u"Las rutas de Revit Server no se pueden copiar a una carpeta local",
    },
    "processor.destination_missing": {
        "en_us": u"Copy destination does not exist: {}",
        "ru": u"Папка назначения не существует: {}",
        "es_es": u"La carpeta de destino no existe: {}",
    },
    "processor.same_folder": {
        "en_us": u"Choose a different folder from the source model folder",
        "ru": u"Выберите папку, отличную от папки исходных моделей",
        "es_es": u"Elige una carpeta distinta a la de los modelos de origen",
    },
    "processor.copy_exists": {
        "en_us": u"Copy already exists and will not be overwritten: {}",
        "ru": u"Копия уже существует и не будет перезаписана: {}",
        "es_es": u"La copia ya existe y no se sobrescribirá: {}",
    },

    "ifc.title": {
        "en_us": u"Batch IFC Export",
        "ru": u"Пакетный экспорт IFC",
        "es_es": u"Exportar IFC (lote)",
    },
    "ifc.settings_title": {
        "en_us": u"Batch IFC Export settings",
        "ru": u"Настройки пакетного экспорта IFC",
        "es_es": u"Ajustes de exportación IFC (lote)",
    },
    "ifc.selection_description": {
        "en_us": u"Tick the models to export.",
        "ru": u"Отметьте модели для экспорта.",
        "es_es": u"Marca los modelos que se exportarán.",
    },
    "ifc.options_description": {
        "en_us": u"These settings apply to every ticked model. Set the export "
                 u"folder, then run the export.",
        "ru": u"Эти настройки применяются ко всем отмеченным моделям. Укажите "
              u"папку экспорта и запустите экспорт.",
        "es_es": u"Estos ajustes se aplican a cada modelo marcado. Indica la "
                 u"carpeta de exportación y lanza la exportación.",
    },
    "ifc.group.geometry": {
        "en_us": u"Geometry & elements",
        "ru": u"Геометрия и элементы",
        "es_es": u"Geometría y elementos",
    },
    "ifc.group.psets": {
        "en_us": u"Property sets",
        "ru": u"Наборы свойств",
        "es_es": u"Conjuntos de propiedades",
    },
    "ifc.group.identity": {
        "en_us": u"Identity",
        "ru": u"Идентификация",
        "es_es": u"Identidad",
    },
    "ifc.group.links": {
        "en_us": u"Linked models",
        "ru": u"Связанные модели",
        "es_es": u"Modelos vinculados",
    },
    "ifc.group.after": {
        "en_us": u"After the run",
        "ru": u"После выполнения",
        "es_es": u"Después de la ejecución",
    },
    "ifc.flag.SplitWallsAndColumns": {
        "en_us": u"Split walls and columns by level",
        "ru": u"Разделять стены и колонны по уровням",
        "es_es": u"Dividir muros y pilares por nivel",
    },
    "ifc.flag.IncludeSteelElements": {
        "en_us": u"Include steel elements",
        "ru": u"Включать стальные элементы",
        "es_es": u"Incluir elementos de acero",
    },
    "ifc.flag.Export2DElements": {
        "en_us": u"Export 2D elements",
        "ru": u"Экспортировать 2D-элементы",
        "es_es": u"Exportar elementos 2D",
    },
    "ifc.flag.ExportPartsAsBuildingElements": {
        "en_us": u"Export parts",
        "ru": u"Экспортировать части",
        "es_es": u"Exportar partes",
    },
    "ifc.flag.ExportSolidModelRep": {
        "en_us": u"Export solid model representation",
        "ru": u"Экспортировать представление твёрдой модели",
        "es_es": u"Exportar la representación de modelo sólido",
    },
    "ifc.flag.VisibleElementsOfCurrentView": {
        "en_us": u"Export visible elements only",
        "ru": u"Экспортировать только видимые элементы",
        "es_es": u"Exportar solo los elementos visibles",
    },
    "ifc.flag.ExportRoomsInView": {
        "en_us": u"Export rooms/spaces",
        "ru": u"Экспортировать помещения и пространства",
        "es_es": u"Exportar habitaciones y espacios",
    },
    "ifc.flag.IncludeSiteElevation": {
        "en_us": u"Include site elevation",
        "ru": u"Включать отметку площадки",
        "es_es": u"Incluir la cota del emplazamiento",
    },
    "ifc.flag.ExportInternalRevitPropertySets": {
        "en_us": u"Export Revit property sets",
        "ru": u"Экспортировать наборы свойств Revit",
        "es_es": u"Exportar los conjuntos de propiedades de Revit",
    },
    "ifc.flag.ExportIFCCommonPropertySets": {
        "en_us": u"Export IFC common property sets",
        "ru": u"Экспортировать общие наборы свойств IFC",
        "es_es": u"Exportar los conjuntos de propiedades comunes de IFC",
    },
    "ifc.flag.ExportBaseQuantities": {
        "en_us": u"Export base quantities",
        "ru": u"Экспортировать базовые величины",
        "es_es": u"Exportar las cantidades base",
    },
    "ifc.flag.ExportSchedulesAsPsets": {
        "en_us": u"Export schedules as property sets",
        "ru": u"Экспортировать спецификации как наборы свойств",
        "es_es": u"Exportar las tablas de planificación como conjuntos de propiedades",
    },
    "ifc.flag.ExportUserDefinedPsets": {
        "en_us": u"Export user-defined property sets",
        "ru": u"Экспортировать пользовательские наборы свойств",
        "es_es": u"Exportar los conjuntos de propiedades definidos por el usuario",
    },
    "ifc.flag.UseFamilyAndTypeNameForReference": {
        "en_us": u"Use family/type reference",
        "ru": u"Использовать имя семейства и типа как ссылку",
        "es_es": u"Usar la referencia de familia y tipo",
    },
    "ifc.flag.StoreIFCGUID": {
        "en_us": u"Store IFC GUID in model",
        "ru": u"Сохранять IFC GUID в модели",
        "es_es": u"Guardar el GUID de IFC en el modelo",
    },
    "ifc.option.open_without_links": {
        "en_us": u"Open without Revit links",
        "ru": u"Открывать без связей Revit",
        "es_es": u"Abrir sin vínculos de Revit",
    },
    "ifc.option.export_links_merged": {
        "en_us": u"Export links in the same IFC",
        "ru": u"Выгружать связи в тот же IFC",
        "es_es": u"Exportar los vínculos en el mismo IFC",
    },
    "ifc.option.export_links_separately": {
        "en_us": u"Export linked models separately",
        "ru": u"Выгружать связанные модели отдельно",
        "es_es": u"Exportar los modelos vinculados por separado",
    },
    "ifc.option.save_after": {
        "en_us": u"Save/synchronize after export",
        "ru": u"Сохранять и синхронизировать после экспорта",
        "es_es": u"Guardar y sincronizar tras la exportación",
    },
    "ifc.option.open_folders": {
        "en_us": u"Open export folders when complete",
        "ru": u"Открыть папки экспорта по завершении",
        "es_es": u"Abrir las carpetas de exportación al terminar",
    },
    "ifc.label.version": {
        "en_us": u"IFC version",
        "ru": u"Версия IFC",
        "es_es": u"Versión de IFC",
    },
    "ifc.label.default_view": {
        "en_us": u"Default 3D view name",
        "ru": u"Имя 3D-вида по умолчанию",
        "es_es": u"Nombre de la vista 3D predeterminada",
    },
    "ifc.label.export_folder": {
        "en_us": u"Export folder",
        "ru": u"Папка экспорта",
        "es_es": u"Carpeta de exportación",
    },
    "ifc.tooltip.pick_folder": {
        "en_us": u"Pick the export folder",
        "ru": u"Выберите папку экспорта",
        "es_es": u"Elige la carpeta de exportación",
    },
    "ifc.tooltip.default_folder": {
        "en_us": u"Use the folder the models came from",
        "ru": u"Использовать папку, из которой взяты модели",
        "es_es": u"Usar la carpeta de origen de los modelos",
    },
    "ifc.alert.no_default_folder": {
        "en_us": u"No default export folder is available. Revit Server routes "
                 u"have no local folder, so pick an export folder instead.",
        "ru": u"Папки экспорта по умолчанию нет. У маршрутов Revit Server нет "
              u"локальной папки, поэтому выберите папку экспорта вручную.",
        "es_es": u"No hay carpeta de exportación predeterminada. Las rutas de "
                 u"Revit Server no tienen carpeta local, así que elige una "
                 u"carpeta de exportación.",
    },
    "ifc.error.no_export_folder": {
        "en_us": u"Set an export folder on the Options tab before running the batch.",
        "ru": u"Укажите папку экспорта на вкладке «3. Настройки» "
              u"перед запуском пакета.",
        "es_es": u"Indica una carpeta de exportación en la pestaña "
                 u"«3. Opciones» antes de lanzar el lote.",
    },
    "ifc.alert.specify_folder": {
        "en_us": u"Specify an export folder for the selected models.",
        "ru": u"Укажите папку экспорта для выбранных моделей.",
        "es_es": u"Indica una carpeta de exportación para los modelos seleccionados.",
    },
    "ifc.alert.collisions": {
        "en_us": u"Multiple selected models would overwrite the same IFC file:\n{}",
        "ru": u"Несколько выбранных моделей перезапишут один и тот же файл IFC:\n{}",
        "es_es": u"Varios modelos seleccionados sobrescribirían el mismo archivo IFC:\n{}",
    },
    "ifc.alert.options_saved": {
        "en_us": u"Export settings saved.",
        "ru": u"Настройки экспорта сохранены.",
        "es_es": u"Ajustes de exportación guardados.",
    },
    "ifc.progress": {
        "en_us": u"Exporting {value} of {max_value} models",
        "ru": u"Экспорт модели {value} из {max_value}",
        "es_es": u"Exportando {value} de {max_value} modelos",
    },
    "ifc.results_title": {
        "en_us": u"Batch IFC Export results",
        "ru": u"Результаты пакетного экспорта IFC",
        "es_es": u"Resultados de exportación IFC (lote)",
    },
    "ifc.column.model": {
        "en_us": u"Model",
        "ru": u"Модель",
        "es_es": u"Modelo",
    },
    "ifc.column.view": {
        "en_us": u"View",
        "ru": u"Вид",
        "es_es": u"Vista",
    },
    "ifc.column.result": {
        "en_us": u"Result",
        "ru": u"Результат",
        "es_es": u"Resultado",
    },
    "ifc.alert.finished": {
        "en_us": u"{} export operation(s) finished. See the pyRevit output for details.",
        "ru": u"Выполнено операций экспорта: {}. Подробности — в выводе pyRevit.",
        "es_es": u"{} operación(es) de exportación finalizadas. Consulta la salida de pyRevit para ver los detalles.",
    },
    "ifc.result.file_not_found": {
        "en_us": u"{} (file not found)",
        "ru": u"{} (файл не найден)",
        "es_es": u"{} (archivo no encontrado)",
    },
    "ifc.result.save_sync_failed": {
        "en_us": u"Could not save/sync '{}': {}",
        "ru": u"Не удалось сохранить или синхронизировать «{}»: {}",
        "es_es": u"No se pudo guardar ni sincronizar «{}»: {}",
    },
    "ifc.result.link_not_loaded": {
        "en_us": u"Not loaded - skipped",
        "ru": u"Не загружено — пропущено",
        "es_es": u"No cargado — omitido",
    },
    "ifc.result.export_returned_failure": {
        "en_us": u"Export returned failure",
        "ru": u"Экспорт завершился неудачей",
        "es_es": u"La exportación devolvió un error",
    },
    "ifc.result.export_failed": {
        "en_us": u"Export failed: {}",
        "ru": u"Ошибка экспорта: {}",
        "es_es": u"Error de exportación: {}",
    },
    "ifc.result.links_conflict": {
        "en_us": u"Cannot export links when opening without Revit links",
        "ru": u"Нельзя выгружать связи при открытии без связей Revit",
        "es_es": u"No se pueden exportar vínculos al abrir sin vínculos de Revit",
    },
    "ifc.result.folder_failed": {
        "en_us": u"Cannot create export folder: {}",
        "ru": u"Не удалось создать папку экспорта: {}",
        "es_es": u"No se puede crear la carpeta de exportación: {}",
    },
    "ifc.result.view_not_found": {
        "en_us": u"View not found - skipped",
        "ru": u"Вид не найден — пропущено",
        "es_es": u"Vista no encontrada — omitida",
    },
    "ifc.result.default_view": {
        "en_us": u"(default view)",
        "ru": u"(вид по умолчанию)",
        "es_es": u"(vista predeterminada)",
    },
    "ifc.result.open_failed": {
        "en_us": u"Failed to prepare/open: {}",
        "ru": u"Не удалось подготовить или открыть: {}",
        "es_es": u"No se pudo preparar ni abrir: {}",
    },

    "navis.title": {
        "en_us": u"Batch NavisView",
        "ru": u"Пакетный NavisView",
        "es_es": u"NavisView (lote)",
    },
    "navis.selection_description": {
        "en_us": u"Tick the models that should get a Navisworks view. The "
                 u"profile decides which categories are hidden and can be "
                 u"changed per model.",
        "ru": u"Отметьте модели, для которых нужен вид Navisworks. Профиль "
              u"определяет, какие категории скрыты, и меняется для каждой "
              u"модели.",
        "es_es": u"Marca los modelos que reciben una vista de Navisworks. El "
                 u"perfil decide qué categorías se ocultan y puede cambiarse "
                 u"en cada modelo.",
    },
    "navis.options_description": {
        "en_us": u"These settings apply to every ticked model. Choose how the "
                 u"result is saved and where it goes, then run the batch.",
        "ru": u"Эти настройки применяются ко всем отмеченным моделям. Выберите, "
              u"как и куда сохранять результат, и запустите пакет.",
        "es_es": u"Estos ajustes se aplican a cada modelo marcado. Elige cómo y "
                 u"dónde se guarda el resultado y lanza el lote.",
    },
    "navis.column.profile": {
        "en_us": u"Profile",
        "ru": u"Профиль",
        "es_es": u"Perfil",
    },
    "navis.bulk_label": {
        "en_us": u"Set the same profile for every model:",
        "ru": u"Задать один профиль для всех моделей:",
        "es_es": u"Aplicar el mismo perfil a todos los modelos:",
    },
    "navis.option.analysis_only": {
        "en_us": u"Analysis only",
        "ru": u"Только анализ",
        "es_es": u"Solo análisis",
    },
    "navis.option.upgrade_models": {
        "en_us": u"Allow model upgrade",
        "ru": u"Разрешить обновление версии моделей",
        "es_es": u"Permitir la actualización de los modelos",
    },
    "navis.tooltip.output_folder": {
        "en_us": u"Pick the output folder",
        "ru": u"Выберите папку результата",
        "es_es": u"Elige la carpeta de salida",
    },
    "navis.tooltip.default_output_folder": {
        "en_us": u"Use a '{}' folder beside the models",
        "ru": u"Использовать папку «{}» рядом с моделями",
        "es_es": u"Usar una carpeta «{}» junto a los modelos",
    },
    "navis.option.write_copies": {
        "en_us": u"Create output copies (source models stay untouched)",
        "ru": u"Создавать копии (исходные модели не изменяются)",
        "es_es": u"Crear copias de salida (los modelos de origen no se tocan)",
    },
    "navis.option.write_in_place": {
        "en_us": u"Edit and save the selected source models in place",
        "ru": u"Изменять и сохранять выбранные исходные модели",
        "es_es": u"Editar y guardar los modelos de origen seleccionados",
    },
    "navis.group.save_mode": {
        "en_us": u"Where should the Navisworks view be saved? (required)",
        "ru": u"Куда сохранять вид Navisworks? (обязательно)",
        "es_es": u"¿Dónde se guarda la vista de Navisworks? (obligatorio)",
    },
    "navis.group.output_copies": {
        "en_us": u"Output copies",
        "ru": u"Копии результата",
        "es_es": u"Copias de salida",
    },
    "navis.output_copies_hint": {
        "en_us": u"Each selected RVT is copied to this folder before the "
                 u"Navisworks view is created. Source models are not edited.",
        "ru": u"Каждый отмеченный RVT копируется в эту папку до создания вида "
              u"Navisworks. Исходные модели не изменяются.",
        "es_es": u"Cada RVT marcado se copia en esta carpeta antes de crear la "
                 u"vista de Navisworks. Los modelos de origen no se modifican.",
    },
    "navis.label.hidden_worksets": {
        "en_us": u"Hidden worksets (comma-separated name fragments)",
        "ru": u"Скрытые рабочие наборы (фрагменты имён через запятую)",
        "es_es": u"Subproyectos ocultos (fragmentos de nombre separados por comas)",
    },
    "navis.alert.no_default_output": {
        "en_us": u"No default output folder is available. Revit Server routes "
                 u"have no local folder, so pick an output folder instead.",
        "ru": u"Папки результата по умолчанию нет. У маршрутов Revit Server нет "
              u"локальной папки, поэтому выберите папку результата вручную.",
        "es_es": u"No hay carpeta de salida predeterminada. Las rutas de Revit "
                 u"Server no tienen carpeta local, así que elige una carpeta "
                 u"de salida.",
    },
    "navis.alert.cannot_create_output": {
        "en_us": u"Cannot create the default output folder:\n{}\n{}",
        "ru": u"Не удалось создать папку результата по умолчанию:\n{}\n{}",
        "es_es": u"No se puede crear la carpeta de salida predeterminada:\n{}\n{}",
    },
    "navis.error.no_save_mode": {
        "en_us": u"Choose whether to create output copies or edit the source "
                 u"models on the Options tab.",
        "ru": u"На вкладке «3. Настройки» выберите: создавать копии "
              u"или изменять исходные модели.",
        "es_es": u"En la pestaña «3. Opciones» elige si crear copias "
                 u"de salida o editar los modelos de origen.",
    },
    "navis.error.no_output_folder": {
        "en_us": u"Choose an output folder for the Navisworks model copies on "
                 u"the Options tab.",
        "ru": u"Выберите папку для копий моделей Navisworks на вкладке "
              u"«3. Настройки».",
        "es_es": u"Elige una carpeta de salida para las copias de los modelos "
                 u"de Navisworks en la pestaña «3. Opciones».",
    },
    "navis.error.output_missing": {
        "en_us": u"The selected copy destination does not exist.",
        "ru": u"Выбранная папка назначения не существует.",
        "es_es": u"La carpeta de destino seleccionada no existe.",
    },
    "navis.error.rsn_copy": {
        "en_us": u"Revit Server routes cannot be copied to a local output folder.",
        "ru": u"Маршруты Revit Server нельзя скопировать в локальную папку результата.",
        "es_es": u"Las rutas de Revit Server no se pueden copiar a una carpeta local.",
    },
    "navis.error.same_folder": {
        "en_us": u"Choose an output folder different from the source model folder.",
        "ru": u"Выберите папку результата, отличную от папки исходных моделей.",
        "es_es": u"Elige una carpeta de salida distinta a la de los modelos de origen.",
    },
    "navis.error.duplicate_names": {
        "en_us": u"Selected models have the same file name; choose fewer models "
                 u"or rename one.",
        "ru": u"У выбранных моделей совпадают имена файлов: снимите отметку с "
              u"одной из них или переименуйте её.",
        "es_es": u"Los modelos seleccionados tienen el mismo nombre de archivo: "
                 u"elige menos modelos o renombra uno.",
    },
    "navis.error.copy_exists": {
        "en_us": u"A destination copy already exists: {}",
        "ru": u"Копия в папке назначения уже существует: {}",
        "es_es": u"Ya existe una copia en el destino: {}",
    },
    "navis.run.no_models": {
        "en_us": u"No models selected.",
        "ru": u"Модели не выбраны.",
        "es_es": u"No se ha seleccionado ningún modelo.",
    },
    "navis.run.no_save_mode": {
        "en_us": u"Choose whether to create output copies or edit source models.",
        "ru": u"Выберите: создавать копии или изменять исходные модели.",
        "es_es": u"Elige si crear copias de salida o editar los modelos de origen.",
    },
    "navis.run.no_output_folder": {
        "en_us": u"A valid output folder for Navisworks model copies is required.",
        "ru": u"Нужна существующая папка для копий моделей Navisworks.",
        "es_es": u"Se requiere una carpeta de salida válida para las copias de "
                 u"los modelos de Navisworks.",
    },
    "navis.run.results_title": {
        "en_us": u"{} batch results",
        "ru": u"Результаты пакетной обработки: {}",
        "es_es": u"Resultados por lotes: {}",
    },
    "navis.run.mode.analysis": {
        "en_us": u"Analysis",
        "ru": u"Анализ",
        "es_es": u"Análisis",
    },
    "navis.run.mode.execution": {
        "en_us": u"Execution",
        "ru": u"Выполнение",
        "es_es": u"Ejecución",
    },
    "navis.run.completed": {
        "en_us": u"{} completed for {} model(s).",
        "ru": u"{}: обработано моделей — {}.",
        "es_es": u"{} completada para {} modelo(s).",
    },
    "navis.column.model": {
        "en_us": u"Model",
        "ru": u"Модель",
        "es_es": u"Modelo",
    },
    "navis.column.operation": {
        "en_us": u"Operation",
        "ru": u"Операция",
        "es_es": u"Operación",
    },
    "navis.column.result": {
        "en_us": u"Result",
        "ru": u"Результат",
        "es_es": u"Resultado",
    },
    "navis.column.details": {
        "en_us": u"Details",
        "ru": u"Подробности",
        "es_es": u"Detalles",
    },
    "navis.operation.display_name": {
        "en_us": u"Navisworks view",
        "ru": u"Вид Navisworks",
        "es_es": u"Vista de Navisworks",
    },
    "navis.operation.exists": {
        "en_us": u"Navisworks view exists",
        "ru": u"Вид Navisworks существует",
        "es_es": u"La vista de Navisworks ya existe",
    },
    "navis.operation.missing": {
        "en_us": u"Navisworks view not found",
        "ru": u"Вид Navisworks не найден",
        "es_es": u"No se encontró la vista de Navisworks",
    },
})
