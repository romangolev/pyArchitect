## pyArchitect
This is a pyRevit extension for Architectural and Interior design.
The extension developed to help architects reduce routine tasks and help
the project to be organized and neat.

### Installation / Установка

To use the extension follow the steps:
  * Install [pyRevit](https://github.com/eirannejad/pyRevit/releases)
  * Add pyArchitect extension:
    * Open comand promt (Win + R) => `cmd`
    * type following comand : `pyrevit extend ui pyArchitect https://github.com/romangolev/pyArchitect.git`
  * A panel **pyArchitect** should appear on the next start of Revit

Для корректной работы надстройки необходимо:
  * Установить плагин [pyRevit](https://github.com/eirannejad/pyRevit/releases)
  * Добавить расширение pyArchitect:
    * Открыть командную строку (Win + R) => `cmd`
    * В командной строке запустить команду :
     `pyrevit extend ui pyArchitect https://github.com/romangolev/pyArchitect.git`
  * При запуске Revit появится вкладка **pyArchitect**. 

### Features / Функции

Main features of extension are 


Основные функции расширения представлены на вкладке pyArchitect.
![ribbon logo](/docs/static/ribbon.png)
Представлены следующие панели:
* Main — панель управления расширением и основная информация о расширении
* Coordination — набор инструментов для координации проекта
* Finishing — панель инструментов по созданию/специфицированию элементов отделки
* Tools — панель вспомогательных инструментов


Каждый инструмент обладает встроенной подсказкой. Для того, чтобы увидеть её, необходимо навести на инструмент и немного подождать.


### Troubleshooting / Устранение неполадок

When having an issues, delete all files from the following directory: `%AppData%\Roaming\pyRevit\Extensions\pyArchitect.extension` as well as `pyArchitect.extension` folder. And reinstall extension.

При возникновении неполадок, необходимо удалить приложение из пользовательской директории `%AppData%\Roaming\pyRevit\Extensions\pyArchitect.extension` вместе с директорией `pyArchitect.extension` и установить расширение заново, выполнив инструкцию по установке.
