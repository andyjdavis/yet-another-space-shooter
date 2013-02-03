from cx_Freeze import setup,Executable

includefiles = ['resources/516494_Zone-X.mp3','resources/asteroid_blue.png','resources/double_ship.png','resources/enginehum3.ogg','resources/explosion_alpha.png', 'resources/laser6.wav','resources/nebula_blue.png','resources/shot2.png','resources/threeTone1.wav','resources/threeTone2.wav']

build_exe_options = {"packages": ["os"], "excludes": ["tkinter"], 'include_files':includefiles}

setup(
    name = 'Yet Another Space Shooter',
    version = '1.0',
    description = 'An entirely unoriginal space shooter',
    author = 'Andrew Davis',
    options = {"build_exe": build_exe_options}, 
	executables = [Executable(script="main.py", base="Win32GUI", targetName="YASS.exe")]
)
