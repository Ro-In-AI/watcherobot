# Contributing to WatcherRobot Body

Thank you for your interest in contributing! This document provides guidelines for contributions.

## Getting Started

### Prerequisites

- ESP-IDF v5.2 or later
- Python 3.8+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/Ro-In-AI/WatcheRobot.git
cd WatcheRobot

# Set up ESP-IDF environment
# Windows
. C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1
# Linux/macOS
source $IDF_PATH/export.sh

# Build the project
idf.py build
```

## Development Workflow

1. **Fork** the repository
2. **Create a branch** for your feature/fix
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes** and test thoroughly
4. **Commit** with clear messages
   ```bash
   git commit -m "feat: add new servo control mode"
   ```
5. **Push** and create a Pull Request

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `perf`: Performance improvement

## Code Style

- Follow ESP-IDF coding conventions
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

## Pull Request Guidelines

- Link related issues
- Describe changes clearly
- Update documentation if needed
- Test on actual hardware when possible

## Reporting Issues

- Use GitHub Issues
- Provide hardware details (chip, dev board)
- Include error messages and logs
- Describe steps to reproduce

## Questions?

Open an issue with the `question` label.
