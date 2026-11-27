@echo off
REM Script for adding new assignments on Windows
REM Usage: add_assignment.bat

echo ========================================
echo   Assignment Generator Script
echo ========================================
echo.

REM Get inputs from user
set /p FORM_URL="Enter Google Form URL: "
set /p HW_NUM="Enter Assignment Number (e.g., 10): "
set /p HW_TITLE="Enter Assignment Title (e.g., Homework 10): "
set /p CATEGORY="Enter Category (default: Multiple Choice): "

if "%CATEGORY%"=="" set CATEGORY=Multiple Choice

echo.
echo [Step 1] Generating HTML from Google Form...
python gf_gen.py "%FORM_URL%" "hw%HW_NUM%_improved.html"

if errorlevel 1 (
    echo ERROR: Failed to generate HTML
    pause
    exit /b 1
)

REM Extract question count from generated file
for /f "tokens=*" %%a in ('findstr /C:"Questions:" gf_gen_output.txt 2^>nul') do set QUESTIONS=%%a
if "%QUESTIONS%"=="" set QUESTIONS=XX

echo SUCCESS: HTML generated successfully
echo.

echo [Step 2] Updating index.html...
REM Create a temporary PowerShell script
echo $content = Get-Content "index.html" -Raw > update_index.ps1
echo $newCard = @" >> update_index.ps1
echo. >> update_index.ps1
echo     ^<a class="hwcard glass" href="hw%HW_NUM%_improved.html"^> >> update_index.ps1
echo       ^<div class="go"^>^<svg viewBox="0 0 24 24"^>^<line x1="5" y1="12" x2="19" y2="12"/^>^<polyline points="12 5 19 12 12 19"/^>^</svg^>^</div^> >> update_index.ps1
echo       ^<div class="hwnum"^>%HW_NUM%^</div^> >> update_index.ps1
echo       ^<h3^>%HW_TITLE%^</h3^> >> update_index.ps1
echo       ^<p^>%QUESTIONS% Questions — Multiple Choice^</p^> >> update_index.ps1
echo       ^<div class="meta"^>^<span class="chip open"^>Available Now^</span^>^<span class="chip c2"^>%CATEGORY%^</span^>^</div^> >> update_index.ps1
echo     ^</a^> >> update_index.ps1
echo "@ >> update_index.ps1
echo $content = $content -replace '(^<^!-- ⬆️ END BLOCK ⬆️ --^>)', "$newCard`r`n    `$1" >> update_index.ps1
echo $content ^| Set-Content "index.html" -NoNewline >> update_index.ps1

powershell -ExecutionPolicy Bypass -File update_index.ps1
del update_index.ps1

echo SUCCESS: index.html updated
echo.

echo [Step 3] Checking Git status...
git status >nul 2>&1
if errorlevel 1 (
    echo WARNING: Not a git repository or git not found
    echo Skipping git commit and push...
    goto :end_success
)

echo [Step 4] Committing to Git...
git add "hw%HW_NUM%_improved.html" index.html
git commit -m "Add %HW_TITLE%"

echo.
echo [Step 5] Pushing to GitHub...
git push origin main

if errorlevel 1 (
    echo WARNING: Push failed. Trying 'master' branch...
    git push origin master
    if errorlevel 1 (
        echo ERROR: Push failed. Please check your git configuration
        echo The files have been updated locally but not pushed to GitHub
        pause
        exit /b 1
    )
)

:end_success
echo.
echo ========================================
echo   SUCCESS! Assignment added
echo ========================================
echo.
echo IMPORTANT: Don't forget to edit hw%HW_NUM%_improved.html
echo and update the CORRECT_ANSWERS with actual answers!
echo.
pause
