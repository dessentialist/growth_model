# Contributing to FFF Growth System v2

Thank you for your interest in contributing to the FFF Growth System! This document provides guidelines and information for contributors.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   # Unix/macOS
   ./install.sh
   
   # Windows
   install.bat
   
   # Or manually
   make install
   ```

## 🔧 Development Setup

After installation:

```bash
# Activate virtual environment
source venv/bin/activate  # Unix/macOS
# or
venv\Scripts\activate.bat  # Windows

# Run tests to ensure everything works
python -m pytest tests/

# Start development
```

## 📝 Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing

Run these before committing:

```bash
make lint          # Format and lint code
make test          # Run all tests
```

## 🧪 Testing

- **Write tests** for new functionality
- **Ensure all tests pass** before submitting PR
- **Add integration tests** for complex features
- **Test on multiple Python versions** (3.12, 3.13)

Test structure:
```
tests/
├── test_phase*.py      # Core functionality tests
├── test_ui*.py         # UI component tests
└── conftest.py         # Test configuration
```

## 🔄 Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** with clear commit messages
3. **Add/update tests** for new functionality
4. **Update documentation** if needed
5. **Run the full test suite**:
   ```bash
   make test
   make lint
   ```
6. **Submit a pull request** with:
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes

## 📚 Documentation

- **Update README.md** for user-facing changes
- **Update docstrings** for new functions/classes
- **Update technical_architecture.md** for model changes
- **Update index.md** for structural changes

## 🐛 Bug Reports

When reporting bugs, please include:

- **Environment details** (OS, Python version)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages/logs**
- **Minimal example** if possible

## 💡 Feature Requests

For feature requests:

- **Describe the use case** clearly
- **Explain the expected benefit**
- **Consider implementation complexity**
- **Check if it fits the project scope**

## 🏗️ Architecture Guidelines

- **Keep functions modular** with minimal dependencies
- **Use descriptive names** for variables and functions
- **Add comprehensive comments** explaining logic
- **Follow the existing patterns** in the codebase
- **Maintain backward compatibility** when possible

## 🔍 Code Review

All contributions require review:

- **Be responsive** to review comments
- **Address feedback** promptly
- **Ask questions** if something is unclear
- **Be patient** - thorough reviews take time

## 📋 Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No sensitive data is included
- [ ] Commit messages are clear
- [ ] Changes are focused and logical

## 🆘 Getting Help

- **Check existing issues** first
- **Search documentation** for answers
- **Ask in discussions** for general questions
- **Create an issue** for bugs/features

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to the FFF Growth System! 🎉
