# Assignment Maker - Quick Setup Guide

## 📁 Setup Instructions

### 1. Copy Files to Desktop
Copy these 4 files to the same folder on your Desktop where your GitHub repository is:
- `add_assignment.bat` - The automation script
- `gf_gen.py` - Google Form to HTML generator
- `template.html` - HTML template for assignments
- `index.html` - Main dashboard page

### 2. Make Sure Git is Initialized
If you haven't already, initialize git in your project folder:
```cmd
cd Desktop\Assignment-Maker
git init
git remote add origin https://github.com/omarabdo96-stack/Assignment-Maker.git
```

### 3. Run the Script
Double-click `add_assignment.bat` or run it from command prompt:
```cmd
cd Desktop\Assignment-Maker
add_assignment.bat
```

### 4. Enter the Information
When prompted, enter:
- **Google Form URL**: The full URL from your Google Form
- **Assignment Number**: e.g., 11
- **Assignment Title**: e.g., Homework 11
- **Category**: e.g., Multiple Choice (or press Enter for default)

### 5. The Script Will:
✅ Generate the HTML file from your Google Form  
✅ Update index.html with the new assignment card  
✅ Commit changes to git (if repository exists)  
✅ Push to GitHub (if repository is configured)

### 6. Important: Edit the Generated File
⚠️ **Don't forget** to open the generated `hw##_improved.html` file and update the `CORRECT_ANSWERS` object with the actual correct answers!

## 🔧 Troubleshooting

### If git commands fail:
The script will still work and create the files locally. You can manually commit:
```cmd
git add .
git commit -m "Add homework ##"
git push origin main
```

### If Python is not found:
Make sure Python is installed and added to your PATH.

### If the script can't find template.html:
Make sure all 4 files are in the same folder.

## 📝 Example Usage

```
Enter Google Form URL: https://docs.google.com/forms/d/e/1FAIpQLSdot1kr9UQSeHdA5UUTxMhbMhOTuKoEUu1MC8baQj-wO4zkgw/viewform
Enter Assignment Number: 11
Enter Assignment Title: Homework 11
Enter Category: Multiple Choice
```

The script will create `hw11_improved.html` and automatically add it to `index.html`!
