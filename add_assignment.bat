@echo off
REM Script للإضافة السريعة للواجبات الجديدة على Windows
REM الاستخدام: add_assignment.bat

echo ========================================
echo   Assignment Generator Script
echo ========================================
echo.

REM طلب المدخلات من المستخدم
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
REM قراءة index.html وإضافة الكارت الجديد
powershell -Command "(gc index.html) -replace '(<!-- ⬆️ END BLOCK ⬆️ -->)', ('<a class=\"hwcard glass\" href=\"hw%HW_NUM%_improved.html\"><div class=\"go\"><svg viewBox=\"0 0 24 24\"><line x1=\"5\" y1=\"12\" x2=\"19\" y2=\"12\"/><polyline points=\"12 5 19 12 12 19\"/></svg></div><div class=\"hwnum\">%HW_NUM%</div><h3>%HW_TITLE%</h3><p>XX Questions — Multiple Choice</p><div class=\"meta\"><span class=\"chip open\">Available Now</span><span class=\"chip c2\">%CATEGORY%</span></div></a>' + [Environment]::NewLine + '    $1') | sc index.html"

echo SUCCESS: index.html updated
echo.

echo [Step 3] Committing to Git...
git add "hw%HW_NUM%_improved.html" index.html
git commit -m "Add %HW_TITLE%"

echo.
echo [Step 4] Pushing to GitHub...
git push origin main

if errorlevel 1 (
    echo ERROR: Push failed. Please check your git configuration
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Assignment added to GitHub
echo ========================================
echo.
echo IMPORTANT: Don't forget to edit hw%HW_NUM%_improved.html
echo and update the CORRECT_ANSWERS with actual answers!
echo.
pause
