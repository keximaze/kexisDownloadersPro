# 🎵 kexisdownloader Pro

A personal YouTube video/audio downloader built for musicians who need high-quality downloads. 

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🎬 **Video Downloads**: 8K, 4K, 1440p, 1080p, 720p with multiple codec options (VP9, AV1, AVC1)
- 🎵 **Audio Downloads**: MP3, FLAC, ALAC, WAV, M4A, Opus, OGG formats
- 📊 **Format Checker**: View all available formats before downloading
- 🔄 **Batch Downloads**: Download multiple videos/audio files at once
- 🍏 **macOS-Style UI**: Clean, native-looking interface with green progress bar
- 🚫 **Cancel Anytime**: Stop downloads mid-process
- 🔒 **Cookie Support**: Download age-restricted content
- ⚡ **Multi-threaded**: Non-blocking UI for smooth operation

## 🚀 Quick Start

### For Users (Your Friends)

#### Requirements:
- **Python 3.8 or higher** ([Download here](https://www.python.org/downloads/))
- **pip** (comes with Python)

#### Installation Steps: 

**Step 1: Download this repository**

Click the green **"Code"** button at the top of this page, then click **"Download ZIP"**

Or if you have git installed:
```bash
git clone https://github.com/keximaze/kexisdownloaderPro. git
cd kexisdownloaderPro
```

**Step 2: Install dependencies**

Open Terminal (Mac/Linux) or Command Prompt (Windows) and run:
```bash
pip install -r requirements.txt
```

**Step 3: Run the app**
```bash
python kexisdownloader.py
```

## 📖 How to Use

### 🎬 Video Downloads: 
1. Launch the app
2. You'll see the **Video** tab (it's the default)
3. **Paste YouTube URLs** in the text area (one per line)
4. Click **"Browse"** to choose where to save your videos
5. Select your preferred **video quality** (e.g., "1080p – VP9 – 303")
6. Select your preferred **audio quality** (e.g., "251 (Opus – Best)")
7. Click **"DOWNLOAD VIDEO"**
8. Watch the progress bar fill up!  ✅

### 🎵 Audio Downloads:
1. Click the **Audio** tab
2. **Paste YouTube URLs** in the text area (one per line)
3. Click **"Browse"** to choose where to save your audio files
4. Select your preferred **audio format** (MP3, FLAC, etc.)
5. Click **"DOWNLOAD AUDIO"**
6. Your audio files will be saved in the format you chose!  🎶

### 📊 Check Available Formats:
1. Paste **ONE** YouTube URL in the Video tab
2. Click **"CHECK VIDEO FORMATS"**
3. A new window opens showing ALL available formats
4. Use the **filter buttons** to narrow down: 
   - All Formats
   - Audio Only
   - High-bitrate Audio ≥256 kbps
   - Highest Audio ≥480 kbps
   - Video Only
5. Find the format ID you want and select it in the main window! 

## 🎯 Tips for Musicians

- **🎼 Best Audio Quality**: Use **FLAC** or **ALAC** for lossless quality (perfect for music production)
- **📱 Compatibility**: Use **MP3** for universal playback on all devices
- **🎧 High-Quality Audio**: Look for formats **≥256 kbps** (near CD quality)
- **🔍 Format Checker**:  ALWAYS use this to verify the best available quality before downloading
- **📚 Batch Mode**:  Paste multiple URLs to download an entire album or playlist at once
- **🎹 For DAW Work**: Use FLAC or WAV for importing into your music software

## 🛠️ Building a Standalone App

Want to create an executable so your friends don't need Python? 

See **[BUILD.md](BUILD.md)** for complete instructions on creating: 
- **Mac**:  `.app` bundle
- **Windows**: `.exe` executable
- **Linux**: standalone binary

## 🐛 Troubleshooting

### "yt-dlp not found" Error
```bash
pip install yt-dlp
```

### App won't start
Make sure you have Python 3.8 or higher: 
```bash
python --version
```

If it shows Python 2.x, try:
```bash
python3 kexisdownloader.py
```

### Downloads fail
Try updating yt-dlp:
```bash
pip install --upgrade yt-dlp
```

### Age-restricted videos won't download
1. Export cookies from your browser using a browser extension
2. Save the `cookies.txt` file in your Downloads folder
3. The app will automatically detect and use it! 

## 📝 License

MIT License - feel free to modify for personal use. 

## ⚠️ Disclaimer

This tool is for **personal use only**. Please respect copyright laws and YouTube's Terms of Service. Only download content you have the right to download.

---

**Made with ❤️ by mark keximaze for musicians everywhere** 🎸

## 💬 Questions? 

If your friends have issues: 
- Make sure they have Python 3.8+
- Make sure they installed dependencies:  `pip install -r requirements.txt`
- Make sure yt-dlp is installed:  `pip install yt-dlp`

---

## 🎉 Enjoy Your Downloads! 

Share this with your musician friends and help them save time downloading practice tracks, reference songs, and backing tracks!  🎵
