![blank logo](https://raw.githubusercontent.com/BlankArchitects/pyBlank/main/docs/static/icon.png)
## pyBlank
This is a pyRevit extension for Architectural and Interior design. The extension developed to help architects reduce routine tasks and help the project to be organized and neat.

### Installation / Установка

Для корректной работы надстройки необходимо:
  * Установить плагин [pyRevit](https://github.com/eirannejad/pyRevit/releases)
  * Открыть командную строку (Win + R) => `cmd`
  * В командной строке запустить команду:
   `pyrevit extend ui BlankArchitects https://github.com/BlankArchitects/pyBlank.git`
  * При запуске Revit появится вкладка BlankArchitects.

### Features / Функционал

Основные функции расширения представлены на вкладке BlankArchitects.
![ribbon logo](/docs/static/ribbon.png)
Представлены следующие панели:
* Main — панель управления расширением и основная информация о расширении
* RSN — панель управления адресом RSN
* Librart Catalog — панель доступа к основным ресурсам организации BlankArchitects
* Finishing — панель инструментов по созданию/специфицированию элементов отделки
* Tools — панель вспомогательных инструментов
* Coordination — набор инструментов для координации проекта

Каждый инструмент обладает встроенной подсказкой. Для того, чтобы увидеть её, необходимо навести на инструмент и немного подождать.


### Troubleshooting / Устранение неполадок

При возникновении неполадок, необходимо удалить приложение из пользовательской директории `%AppData%\Roaming\pyRevit\Extensions\BlankArchitects.extension` вместе с директорией `BlankArchitects.extension` и установить расширение заново, выполнив инструкцию по установке.
