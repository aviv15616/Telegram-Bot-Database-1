Name "MyApp"
OutFile "MyAppInstaller.exe"
InstallDir "$TEMP\dump"
RequestExecutionLevel user

Section "Main"
    ; Extract files to the temporary directory
    SetOutPath "$INSTDIR"
    ; Create subdirectories for the file structure
    CreateDirectory "$INSTDIR\PyFiles\Cleaners"
    CreateDirectory "$INSTDIR\PyFiles"
    CreateDirectory "$INSTDIR\Others"

    ; Copy the necessary files with their respective folder structure
    SetOutPath "$INSTDIR\Others"
    File "C:\Users\anksi\Botty3\Others\runthisonly.bat"
    File "C:\Users\anksi\Botty3\Others\requirements.txt"
    File "C:\Users\anksi\Botty3\Others\credentials.json"
    
    SetOutPath "$INSTDIR\PyFiles"
    File "C:\Users\anksi\Botty3\PyFiles\Main.py"
    File "C:\Users\anksi\Botty3\PyFiles\Getters.py"
    File "C:\Users\anksi\Botty3\PyFiles\Authorizer.py"
    File "C:\Users\anksi\Botty3\PyFiles\config.py"
    File "C:\Users\anksi\Botty3\PyFiles\imports.py"
    File "C:\Users\anksi\Botty3\PyFiles\Tools.py"
    File "C:\Users\anksi\Botty3\PyFiles\UI.py"
    File "C:\Users\anksi\Botty3\PyFiles\Google.py"
    File "C:\Users\anksi\Botty3\PyFiles\DatabaseManager.py"

    SetOutPath "$INSTDIR\PyFiles\Cleaners"
    File "C:\Users\anksi\Botty3\PyFiles\Cleaners\download_from_drive.py"
    File "C:\Users\anksi\Botty3\PyFiles\Cleaners\upload_to_drive.py"
    File "C:\Users\anksi\Botty3\PyFiles\Cleaners\upload_to_drive.py"
    
 ; Copy uninstall.py to the installation directory
    SetOutPath "$INSTDIR"
    File "C:\Users\anksi\Botty3\uninstall.py"

    

    ; Run Python scripts and keep the console open
    ExecWait 'cmd /c "python $INSTDIR\PyFiles\Cleaners\download_from_drive.py & pause"'
    SetOutPath "$INSTDIR\PyFiles"
    ExecWait 'cmd /c "python Main.py & pause"'
    ExecWait 'cmd /c "python $INSTDIR\uninstall.py & pause"'
    
  
SectionEnd


