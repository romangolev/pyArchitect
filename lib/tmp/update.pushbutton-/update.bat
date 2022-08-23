@ECHO OFF
pyrevit extensions delete BlankArchitects --debug
pyrevit extend ui BlankArchitects https://github.com/BlankArchitects/pyBlank.git --debug
@ECHO ----------------------------------------------------------
@ECHO -----------------RESTART--PYREVIT-------------------------
@ECHO ----------------------------------------------------------