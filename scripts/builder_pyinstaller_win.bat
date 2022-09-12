ECHO OFF
IF EXIST "Zyne.py" (
	RMDIR /s /q build
	RMDIR /s /q dist
	pyinstaller --clean scripts\Zyne_win.spec
	RMDIR /s /q build
) ELSE (
	ECHO "start this script from the Zyne's root directory - scripts\builder_pyinstaller_win.bat"
)
