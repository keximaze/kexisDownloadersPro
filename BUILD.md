# 🏗️ Building kexiYTdownloader Pro

This guide helps you create a **standalone executable** that your friends can run **without installing Python**. 

---

## 📋 Prerequisites

Before you start, make sure you have: 
- ✅ Python 3.8 or higher
- ✅ pip installed
- ✅ All dependencies:  `pip install -r requirements.txt`
- ✅ Your script is working when you run `python kexidownloader.py`

---

## 🔨 Install PyInstaller

PyInstaller turns Python scripts into executables. 

```bash
pip install pyinstaller
```

---

## 🍎 Option 1: Build for macOS (App Bundle)

This creates a `.app` file that looks and acts like a native Mac application.

### **Build Command:**
```bash
pyinstaller --name="kexiYTdownloader" \
    --windowed \
    --onefile \
    --add-binary="$(which yt-dlp):." \
    kexidownloader.py
```

### **What each flag means:**
- `--name="kexiYTdownloader"`: Names your app
- `--windowed`: Hides the terminal window (GUI only)
- `--onefile`: Creates a single app bundle
- `--add-binary="$(which yt-dlp):."`: Includes yt-dlp

### **Find Your App:**
After building (takes 5-10 minutes), your app is in: 
```
dist/kexiYTdownloader. app
```

### **Test It:**
Double-click `kexiYTdownloader.app` to make sure it works!

### **Share It:**
1. Right-click `dist` folder → Compress
2. Upload `dist. zip` to Google Drive or Dropbox
3. Share the link with friends! 
4. They extract and double-click the `.app` to run!

---

## 🪟 Option 2: Build for Windows (EXE)

Creates a `.exe` file for Windows users.

### **Build Command:**
```cmd
pyinstaller --name="kexiYTdownloader" ^
    --windowed ^
    --onefile ^
    --add-binary="yt-dlp.exe;." ^
    kexidownloader.py
```

### **Find Your Executable:**
```
dist\kexiYTdownloader.exe
```

### **Test It:**
Double-click `kexiYTdownloader.exe`

### **Share It:**
1. Zip the `dist` folder
2. Upload to cloud storage
3. Friends download, extract, and run the `.exe`!

⚠️ **Windows Defender Warning:**
Windows might show a warning because it's an unsigned app. Tell friends to click **"More info"** → **"Run anyway"**

---

## 🐧 Option 3: Build for Linux (Binary)

Creates a standalone Linux executable.

### **Build Command:**
```bash
pyinstaller --name="kexiYTdownloader" \
    --onefile \
    --add-binary="$(which yt-dlp):." \
    kexidownloader.py
```

### **Find Your Binary:**
```
dist/kexiYTdownloader
```

### **Test It:**
```bash
./dist/kexiYTdownloader
```

### **Share It:**
1. Zip the `dist` folder
2. Friends extract and run: 
```bash
chmod +x kexiYTdownloader
./kexiYTdownloader
```

---

## 📦 Distribution via GitHub Releases (Professional Method)

This is the BEST way to share with friends!

### **Steps:**
1. Go to: **https://github.com/keximaze/kexiYTdownloaderPro**
2. Click **"Releases"** (right sidebar)
3. Click **"Create a new release"**
4. Tag version: `v1.0.0`
5. Release title: `kexiYTdownloader Pro v1.0.0`
6. Description: 
```
🎵 First release of kexiYTdownloader Pro! 

Features:
- Video downloads (8K to 720p)
- Audio downloads (MP3, FLAC, etc.)
- Format checker
- Batch downloads

Download the version for your operating system below! 
```
7. **Drag and drop** your built apps: 
   - Mac: `kexiYTdownloader.app. zip`
   - Windows: `kexiYTdownloader. exe.zip`
   - Linux: `kexiYTdownloader-linux. zip`
8. Click **"Publish release"**
9. Share the release URL with friends!

---

## 🐛 Troubleshooting

### **Problem:  "yt-dlp not found" when running built app**

**Solution:** Make sure yt-dlp is in your PATH when building: 
```bash
which yt-dlp  # Mac/Linux
where yt-dlp  # Windows
```

If it's not installed: 
```bash
pip install yt-dlp
```

Then rebuild. 

---

### **Problem: App crashes immediately**

**Solution:** Run from terminal to see errors:
```bash
# Mac/Linux
./dist/kexiYTdownloader. app/Contents/MacOS/kexiYTdownloader

# Windows
dist\kexiYTdownloader.exe
```

Common fixes:
```bash
pyinstaller --name="kexiYTdownloader" \
    --windowed \
    --onefile \
    --hidden-import=yt_dlp \
    --collect-all yt_dlp \
    --add-binary="$(which yt-dlp):." \
    kexidownloader.py
```

---

### **Problem: macOS says "App is damaged" or "Can't be opened"**

**Solution:** This is a security feature. Tell friends to:
1. Right-click the app → **"Open"**
2. Click **"Open"** in the dialog
3. Or go to **System Preferences** → **Security & Privacy** → **"Open Anyway"**

You can also sign the app (requires Apple Developer account).

---

### **Problem: Windows Defender blocks the exe**

**Solution:** This is normal for unsigned apps. Tell friends:
1. Windows Defender popup appears
2. Click **"More info"**
3. Click **"Run anyway"**

---

### **Problem: Build takes forever**

**Solution:** This is normal!  First build can take 5-10 minutes.  Grab a coffee!  ☕

---

## 📝 Tips

1. **Always test** the built app before sharing
2. **Include instructions** in your release notes
3. **Each OS needs its own build** (Mac can't run Windows . exe)
4. **Rebuild after code changes**
5. **File size**:  Expect 40-60 MB executables (includes Python runtime)

---

## 🎨 Optional: Add a Custom Icon

### **Mac:**
1. Create or find an `.icns` icon file
2. Add to build command:
```bash
--icon=icon.icns
```

### **Windows:**
1. Create or find an `.ico` icon file
2. Add to build command:
```bash
--icon=icon.ico
```

Makes your app look professional!  🎨

---

## ✅ Build Checklist

Before sharing with friends:
- [ ] Built the app successfully
- [ ] Tested the app on your machine
- [ ] Zipped the app
- [ ] Wrote simple instructions
- [ ] Uploaded to cloud storage or GitHub Releases
- [ ] Shared the link! 

---

## 🎉 You're Done!

Your friends can now use your app without any technical knowledge! Just download, extract, and run!  🚀

**Questions?  Issues?  Check the main [README. md](README.md) for troubleshooting!**
