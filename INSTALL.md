# 🚀 Growth System v2 - Simple Installation Guide

## 🎯 One-Command Setup (Recommended)

After cloning the repository, simply run:

```bash
python setup_cross_platform.py
```

That's it! This single command will:
1. ✅ Check Python version (3.12+ required)
2. ✅ Create virtual environment
3. ✅ Install all dependencies
4. ✅ Run test suite (107 tests)
5. ✅ Launch the Streamlit UI automatically

## 🔧 What Happens During Setup

The setup script automatically:
- **Detects your operating system** (Windows, macOS, Linux)
- **Creates a virtual environment** to isolate dependencies
- **Installs all required packages** from requirements.txt
- **Verifies installation** by running the complete test suite
- **Launches the UI** in your default web browser

## 🌐 Accessing the Application

Once setup completes:
- **Web Interface**: Opens automatically at http://localhost:8501
- **Stop the UI**: Press `Ctrl+C` in the terminal
- **Restart Later**: Run `python setup_cross_platform.py --ui-only`

## 🛠️ Alternative Commands

The setup script supports additional options:

```bash
# Full setup and launch UI
python setup_cross_platform.py

# Launch UI only (after setup)
python setup_cross_platform.py --ui-only

# Run tests only
python setup_cross_platform.py --test-only

# Install dependencies only
python setup_cross_platform.py --install-only

# Show help
python setup_cross_platform.py --help
```

## 🐧 For Unix/Linux/macOS Users

If you prefer using Make commands:

```bash
# Install dependencies
make install

# Run tests
make test

# Launch UI
make run_ui

# Show all available commands
make help
```

## 🔍 Troubleshooting

### Python Version Issues
- **Required**: Python 3.12 or higher
- **Check version**: `python --version` or `python3 --version`
- **Install Python**: Download from [python.org](https://python.org)

### Permission Issues
- **Windows**: Run Command Prompt as Administrator
- **macOS/Linux**: Use `sudo` if needed for system-wide installation

### Network Issues
- **Check internet connection**
- **Try again**: The script will retry failed installations
- **Manual install**: Use `pip install -r requirements.txt` in the virtual environment

### Virtual Environment Issues
- **Delete and retry**: Remove the `venv/` folder and run setup again
- **Check Python path**: Ensure Python is in your system PATH

## 📋 System Requirements

- **Python**: 3.12+ (3.13+ recommended)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

## 🆘 Getting Help

If you encounter issues:
1. **Check this guide** for common solutions
2. **Review error messages** in the terminal
3. **Check Python version** meets requirements
4. **Try manual installation** steps above
5. **Create an issue** with detailed error information

## 🎉 Success!

Once setup completes successfully, you'll see:
- ✅ All tests passing (107/107)
- ✅ Dependencies installed
- ✅ Streamlit UI launching
- 🌐 Browser opening to http://localhost:8501

Welcome to Growth System v2! 🚀
