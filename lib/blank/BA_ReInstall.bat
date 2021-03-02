@ECHO ----------------------------------------------------------
@ECHO --------INSTALL/UPDATE BA EXTENSION FOR PYREVIT-----------
@ECHO ----------------------------------------------------------
@PAUSE
IF NOT EXIST "C:\Program Files\pyRevit CLI\pyrevit.exe" goto :END1


@echo off
pyrevit clones delete --all --debug
pyrevit clone main base --debug
pyrevit attach main latest --installed
pyrevit extensions delete BlankArchitects --debug
pyrevit extend ui BlankArchitects https://github.com/BlankArchitects/pyBlank.git --debug

@ECHO ----------------------------------------------------------
@ECHO ------------SUCCESSEFULLY REINSTALLED---------------------
@ECHO ----------------------------------------------------------
@PAUSE
END && EXIT

:END1
@ECHO ----------------------------------------------------------
@ECHO --------YOU-NEED-TO-INSTALL-pyRevitCLI-at-FIRTS-----------
@ECHO ----------------------------------------------------------
@PAUSE
END && EXIT
