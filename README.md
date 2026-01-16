# 🎬 ffmpeg-video-bot - Effortless Video Processing for Telegram

[![Download](https://img.shields.io/badge/Download-Now-blue)](https://github.com/NileshKavindaNaka/ffmpeg-video-bot/releases)

## 🚀 Getting Started

Welcome to ffmpeg-video-bot! This powerful Telegram bot helps you process videos easily. Whether you want to encode, watermark, trim, merge, or convert videos, this bot has you covered. You can even upload videos directly to Google Drive. Follow these steps to get started.

## 📥 Download & Install

To get the bot, visit this page to download: [ffmpeg-video-bot Releases](https://github.com/NileshKavindaNaka/ffmpeg-video-bot/releases).

1. Click the "Releases" link above.
2. Find the latest version listed on the page.
3. Look for the file named `ffmpeg-video-bot.zip` or `ffmpeg-video-bot.tar.gz`.
4. Click to download the file to your computer.

## 💻 System Requirements

Before running the bot, ensure you meet these requirements:

- A computer with Windows, macOS, or Linux (most recent versions).
- Python 3.7 or higher installed.
- Docker installed and running.
- Internet connection for the Telegram API and Google Drive integration.

## ⚙️ Setup Instructions

1. **Extract the Downloaded File**:
   - Locate the downloaded file (`ffmpeg-video-bot.zip` or `ffmpeg-video-bot.tar.gz`).
   - Right-click the file and select "Extract All" or use any extraction tool of your choice.

2. **Navigate to the Folder**:
   - Open a terminal or command prompt.
   - Use the `cd` command to change to the directory where you extracted the bot (e.g., `cd Downloads/ffmpeg-video-bot`).

3. **Install Required Packages**:
   - Run the command: `pip install -r requirements.txt`.
   - This will install all necessary Python packages.

4. **Configure Your Bot**:
   - Locate the `config.py` file in the extracted folder.
   - Open it with a text editor and fill in your Telegram Bot token and Google Drive credentials. Follow the instructions found in the text file for detailed guidance.

5. **Run with Docker**:
   - If you are comfortable using Docker, run:
     ```bash
     docker-compose up
     ```
   - This will start the bot within Docker containers.

6. **Run the Bot (without Docker)**:
   - If not using Docker, simply run:
     ```bash
     python main.py
     ```

### 🔑 Getting Your Telegram Bot Token

To get a Telegram Bot token, follow these steps:

1. Open the Telegram app.
2. Search for “BotFather” and start a chat.
3. Send the command `/newbot`.
4. Follow the instructions to set up a new bot.
5. Save the token you receive; you will need it for the configuration file.

## 🛠️ Features of ffmpeg-video-bot

- **Video Encoding**: Convert videos to different formats easily.
- **Watermarking**: Add watermarks to your videos effortlessly.
- **Trimming**: Cut videos to your desired length.
- **Merging**: Combine multiple video files into one.
- **Metadata Editing**: Change video details quickly.
- **Google Drive Upload**: Store videos in your Google Drive without hassle.
- **Multi-user Support**: Allow different users to use the bot simultaneously.

## 📜 FAQs

### How do I start using the bot?

Simply open your Telegram app, find your bot using the name you provided during setup, and start sending commands.

### Can I use this bot without Docker?

Yes, you can run it directly with Python. Make sure you have all required packages installed.

### What if I encounter errors?

Check the terminal for error messages. Ensure all dependencies are installed. Refer to common issues in the documentation found within the project.

## 📞 Support

If you need help, feel free to open an issue on the GitHub repository. The community can help you troubleshoot any problems.

For more information, visit the project repository: [ffmpeg-video-bot](https://github.com/NileshKavindaNaka/ffmpeg-video-bot).

## 📢 Contributing

We welcome contributions! If you wish to improve the bot, please fork the repository and make a pull request. Ensure to follow the guidelines provided in the repo.

---

Thank you for choosing ffmpeg-video-bot for your video processing needs! Enjoy a seamless and efficient video editing experience on Telegram.