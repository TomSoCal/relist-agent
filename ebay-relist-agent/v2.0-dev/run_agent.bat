@echo off
title eBay Relist Agent - Processing Items
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║     eBay Relist Agent - Processing Items                  ║
echo ║                                                            ║
echo ║     DO NOT CLOSE THIS WINDOW                              ║
echo ║                                                            ║
echo ║     Items are being relisted in the background.           ║
echo ║     This window will close automatically when done.       ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Get the directory of this batch file
setlocal enabledelayedexpansion
set "BATCH_DIR=%~dp0"

REM Run Python invisibly with pythonw.exe
pythonw.exe "!BATCH_DIR!ebay_relist_agent.py"

REM Close this window when done
exit /b 0
