# 🚀 PostPilot - Multi-Platform Social Media Automation Tool

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40.0-orange.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A powerful Flask-based social media automation tool that manages authentication cookies, generates dynamic post images, and schedules content across multiple platforms with human-like behavior to avoid detection.

## ✨ Features

### 🔐 **Smart Cookie Management**
- Secure cookie storage for each platform in separate `.pkl` files
- Automatic cookie validation and refresh
- Platform-specific authentication handling

### 🎨 **Dynamic Image Generation**
- PIL-based image generation with custom templates
- Dynamic text injection with website metrics
- Professional post templates with branding

### 🤖 **Human-like Automation**
- Randomized delays between actions
- Real browser headers and user agents
- WebDriver detection avoidance
- Natural behavior simulation

### 📱 **Multi-Platform Support**
- **LinkedIn** - Professional networking posts
- **Facebook** - Social media engagement
- **Twitter** - Microblogging and updates  
- **Instagram** - Visual content sharing

### ⏰ **Advanced Scheduling**
- Time-based post scheduling
- Missed schedule recovery on restart
- Multiple daily schedules support
- Automatic Google Sheets integration

### 🎯 **Template System**
- Multiple customizable post templates
- Dynamic content insertion
- Preview functionality
- Brand-consistent styling

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Google Chrome/Chromium browser

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/AliMurtazaAMJ/PostPilot.git
cd PostPilot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**
```bash
playwright install chromium
```

4. **Create required directories**
```bash
mkdir -p cookies posts/images templates
```

5. **Run the application**
```bash
python main.py
```

6. **Open your browser**
```
http://localhost:5000
```

## 📋 Requirements

```
flask==2.3.3
html2image==2.0.4.3
playwright==1.40.0
requests==2.31.0
psutil==5.9.6
Pillow>=8.0.0
```

## 🚀 Usage

### 1. Account Setup

1. Navigate to the web interface at `http://localhost:5000`
2. Click **"Accounts"** in the top-right corner
3. View all supported platforms with their login status
4. Click **"Login"** for any platform to authenticate
5. Complete the manual login process in the opened browser
6. Cookies are automatically saved for future use

### 2. Post Configuration

1. **Select Template**: Choose from available post templates
2. **Choose Platforms**: Select target social media platforms
3. **Configure Data Source**: Connect your Google Sheets data source

### 3. Scheduling Posts

1. Click **"Post Scheduler"** to manage schedules
2. Create new schedules with specific times
3. System automatically posts at scheduled times using saved cookies
4. Missed schedules are recovered on application restart

## 📁 Project Structure

```
PostPilot/
├── 📄 main.py              # Main Flask application
├── 🌐 index.html           # Web interface
├── 📋 requirements.txt     # Python dependencies
├── 🖼️ template.png         # Base image template
├── 🍪 cookies/             # Cookie storage
│   ├── linkedin.pkl        # LinkedIn authentication
│   ├── facebook.pkl        # Facebook authentication
│   ├── twitter.pkl         # Twitter authentication
│   └── instagram.pkl       # Instagram authentication
├── 📝 posts/               # Generated content
│   ├── 🖼️ images/          # Generated post images
│   ├── ⚙️ config.json      # Application configuration
│   ├── 📊 history.json     # Post history tracking
│   ├── ⏰ schedules.json   # Scheduled posts
│   └── 🕐 last_run.json    # Last execution tracking
└── 📋 templates/           # Post templates (future expansion)
```

## 🔧 Configuration

### Google Sheets Integration

Update the `SHEET_URL` in `main.py` with your Google Apps Script URL:

```python
SHEET_URL = 'https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec'
```

### Template Customization

Modify `template.png` or add new templates in the `templates/` directory. The system supports:
- Dynamic text injection
- Website metrics display (DA, DR, Traffic)
- Brand-consistent styling

## 🧪 Testing

### Cookie Validation
Test your saved cookies for any platform:

```bash
# Test specific platform cookies
curl http://localhost:5000/test-login/linkedin
curl http://localhost:5000/test-login/facebook
```

### Browser Testing
Verify browser automation:

```bash
curl http://localhost:5000/test-browser
```

## 🔒 Security Features

- **Anti-Detection**: Advanced techniques to avoid bot detection
- **Secure Storage**: Encrypted cookie storage with platform isolation  
- **Rate Limiting**: Human-like delays between actions
- **User Agent Rotation**: Dynamic browser fingerprinting
- **Headless Prevention**: Runs in visible browser mode for authenticity

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/accounts` | GET | Get platform login status |
| `/login/<platform>` | GET | Initiate platform login |
| `/test-login/<platform>` | GET | Test platform cookies |
| `/schedules` | GET/POST | Manage post schedules |
| `/schedules/<time>` | DELETE | Remove schedule |
| `/history` | GET | Get posting history |
| `/config` | POST | Save configuration |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and legitimate business purposes only. Users are responsible for:
- Complying with platform Terms of Service
- Respecting rate limits and usage policies
- Ensuring content authenticity and quality
- Following applicable laws and regulations

## 🐛 Troubleshooting

### Common Issues

**Browser not opening:**
```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

**Cookie authentication fails:**
- Clear existing cookies and re-login
- Check platform-specific login requirements
- Verify 2FA settings

**Image generation errors:**
- Ensure `template.png` exists in root directory
- Check PIL/Pillow installation
- Verify font paths for your OS

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/AliMurtazaAMJ/PostPilot/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/AliMurtazaAMJ/PostPilot/discussions)
- 📧 **Email**: your.email@example.com

## 🌟 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [Flask](https://flask.palletsprojects.com/) for web framework
- [Pillow](https://pillow.readthedocs.io/) for image processing

---

<div align="center">
  <strong>⭐ Star this repository if you find it helpful!</strong>
</div>