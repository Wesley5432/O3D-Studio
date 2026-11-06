@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python -m pip install pyinstaller==6.11.1
if errorlevel 1 exit /b 1
.venv\Scripts\python -m PyInstaller --noconfirm --clean --onedir --windowed --name O3DAutoConverter --add-data "backend.py;." --add-data "project.py;." --add-data "model_lights.py;." --add-data "asset_paths.py;." --add-data "material_graph.py;." --add-data "vendor;vendor" app.py
if errorlevel 1 exit /b 1
copy LICENSE dist\O3DAutoConverter\LICENSE.txt
copy README.md dist\O3DAutoConverter\README.md
copy GUIA_v0.0.2.md dist\O3DAutoConverter\GUIA_v0.0.2.md
copy RELEASE_NOTES.md dist\O3DAutoConverter\RELEASE_NOTES.md
if exist examples\Deformacao_Demo xcopy examples\Deformacao_Demo dist\O3DAutoConverter\examples\Deformacao_Demo\ /E /I /Y
copy THIRD_PARTY.md dist\O3DAutoConverter\THIRD_PARTY.md
if exist runtime\blender.exe xcopy runtime dist\O3DAutoConverter\runtime\ /E /I /Y
 echo Build concluido em dist\O3DAutoConverter. Leia README.md.
pause
