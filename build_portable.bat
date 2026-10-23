@echo off
echo Packaging fileSense into a Portable Folder...
echo.

:: Ensure the custom icon is at the root
copy /y ui\filesense-icon.ico icon.ico

:: Clean up old dist folder to prevent conflicts
if exist dist rmdir /s /q dist

:: Run PyInstaller from the virtual environment
call .\venv\Scripts\activate
.\venv\Scripts\pyinstaller --clean --noconfirm --noconsole --name="fileSense" --icon="icon.ico" --add-data "ui;ui" main.py

echo.
echo Packaging complete!
echo You can find the portable folder in: dist\fileSense\
echo Simply run "fileSense.exe" inside that folder. No installation needed!
pause
