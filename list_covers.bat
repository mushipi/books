@echo off
echo 表紙画像ファイルの一覧を表示します...
echo.
echo 表紙画像ディレクトリ:
echo %~dp0static\covers
echo.
echo ファイル一覧:
dir /b "%~dp0static\covers"
echo.
pause
