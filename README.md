## pyArchitect 
This is a pyRevit extension for Architectural and Interior design.
The extension developed to help architects reduce routine tasks and help
the project to be organized and neat. Description in Russian can be found below. 

### Installation

To use the extension follow the steps:
  * Install [pyRevit](https://github.com/eirannejad/pyRevit/releases) or make sure it´s already installed
  * Add pyArchitect extension:
    * Open comand promt (Win + R) => `cmd`
    * type following comand : `pyrevit extend ui pyArchitect https://github.com/romangolev/pyArchitect.git`
  * A panel **pyArchitect** should appear on the next start of Revit

### Features 

Main extension itself looks the following way: ![ribbon logo](/docs/static/ribbon.png)
Extension has several panels in the tab:
* Main — control panel, information about the extension
* Coordination — tools for model coordination
* Finishing — bundle for achetecture interior works
* Tools — miscellaneous tools

Every tool has an embedded description. To see the description and hint, hover mouse over the button

### Troubleshooting 

When having an issues with loading extension, delete all files from the following directory: `%AppData%\Roaming\pyRevit\Extensions\pyArchitect.extension` as well as `pyArchitect.extension` folder. Then reinstall extension as described in Installation section





## pyArchitect — Описание на русском языке
### Установка

Для корректной работы надстройки необходимо:
  * Установить плагин [pyRevit](https://github.com/eirannejad/pyRevit/releases)
  * Добавить расширение pyArchitect:
    * Открыть командную строку (Win + R) => `cmd`
    * В командной строке запустить команду :
     `pyrevit extend ui pyArchitect https://github.com/romangolev/pyArchitect.git`
  * При запуске Revit появится вкладка **pyArchitect**. 

### Функции

Основные функции расширения представлены на вкладке pyArchitect.
![ribbon logo](/docs/static/ribbon.png)
Представлены следующие панели:
* Main — панель управления расширением и основная информация о расширении
* Coordination — набор инструментов для координации проекта
* Finishing — панель инструментов по созданию/специфицированию элементов отделки
* Tools — панель вспомогательных инструментов

Каждый инструмент обладает встроенной подсказкой. Для того, чтобы увидеть её, необходимо навести на инструмент и немного подождать.


### Устранение неполадок

При возникновении неполадок, необходимо удалить приложение из пользовательской директории `%AppData%\Roaming\pyRevit\Extensions\pyArchitect.extension` вместе с директорией `pyArchitect.extension` и установить расширение заново, выполнив инструкцию по установке.
