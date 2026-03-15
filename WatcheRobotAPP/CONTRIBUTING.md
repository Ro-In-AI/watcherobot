# Contributing to WatcherRobotAPP

Thank you for your interest in contributing to WatcherRobotAPP!

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](./CODE_OF_CONDUCT.md). Please read it before contributing.

## How to Contribute

### Reporting Bugs

1. **Search existing issues** - Check if the bug has already been reported
2. **Create a new issue** - Use the bug report template
3. **Include**:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Node version, React Native version)

### Suggesting Features

1. **Search existing issues** - Check if the feature has been proposed
2. **Create a feature request** - Use the feature request template
3. **Explain**:
   - What problem does this solve?
   - How should it work?
   - Any alternative solutions considered?

### Pull Requests

#### Before Submitting

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Follow our coding standards
4. Write tests for new functionality
5. Ensure all tests pass

#### Coding Standards

- **Language**: TypeScript (strict mode)
- **Formatting**: ESLint + Prettier (configured)
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
  ```
  feat: add new animation support
  fix: resolve BLE connection timeout
  docs: update README with new instructions
  ```

#### Pull Request Process

1. Update documentation for any changes
2. Add tests for new features
3. Ensure CI passes
4. Update CHANGELOG.md
5. Wait for review

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/watcher-robot-app.git
cd watcher-robot-app

# Add upstream remote
git remote add upstream https://github.com/watcher-robot/watcher-robot-app.git

# Install dependencies
npm install

# Start development
npm start
```

### Testing

```bash
# Run unit tests
npm test

# Run with coverage
npm test -- --coverage
```

## License

By contributing to WatcherRobotAPP, you agree that your contributions will be licensed under the [GNU General Public License v3.0](./LICENSE).

---

<p align="center">Thank you for contributing! 🎉</p>
