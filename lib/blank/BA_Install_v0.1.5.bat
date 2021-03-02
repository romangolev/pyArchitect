@ECHO ----------------------------------------------------------
@ECHO --------INSTALL/UPDATE BA EXTENSION FOR PYREVIT-----------
@ECHO ----------------------------------------------------------
@PAUSE
IF NOT EXIST "C:\Program Files\pyRevit CLI\pyrevit.exe" goto :END1


@echo off
IF NOT EXIST %APPDATA%\pyRevit\pyRevitCopy\pyrevitlib\pyrevit\version (
pyrevit clones delete --all --debug
pyrevit clone main base --debug
pyrevit attach main latest --installed
start .
) ELSE (
@echo No
)
IF NOT EXIST %APPDATA%\pyRevit\Extensions\BlankArchitects.extension (
pyrevit extend ui BlankArchitects https://github.com/BlankArchitects/pyBlank.git --debug
) ELSE (
pyrevit extensions delete BlankArchitects --debug
pyrevit extend ui BlankArchitects https://github.com/BlankArchitects/pyBlank.git --debug
)
@ECHO ----------------------------------------------------------
@ECHO ------------SUCCESSEFULLY INSTALLED-----------------------
@ECHO ----------------------------------------------------------
@PAUSE
END && EXIT

:END1
@ECHO ----------------------------------------------------------
@ECHO --------YOU-NEED-TO-INSTALL-pyRevitCLI-at-FIRTS-----------
@ECHO ----------------------------------------------------------
@PAUSE
END && EXIT
