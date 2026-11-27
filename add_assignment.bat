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

echo SUCCESS: HTML generated successfully
echo.

echo [Step 2] Updating index.html...
python update_index.py "%HW_NUM%" "%HW_TITLE%" "%CATEGORY%"

if errorlevel 1 (
    echo ERROR: Failed to update index.html
    pause
    exit /b 1
)

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
        echo WARNING: Push failed on both branches
        echo The files have been updated locally but not pushed to GitHub
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
