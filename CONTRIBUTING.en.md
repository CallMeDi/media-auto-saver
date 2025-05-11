# Contributing to Media Auto Saver

First of all, thank you for considering contributing to Media Auto Saver! We welcome all forms of contributions, whether it's reporting bugs, proposing new features, or directly contributing code.

## Table of Contents

- [Contributing to Media Auto Saver](#contributing-to-media-auto-saver)
  - [Table of Contents](#table-of-contents)
  - [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Feature Requests](#feature-requests)
    - [Pull Requests](#pull-requests)
  - [Development Environment Setup](#development-environment-setup)
  - [Coding Standards](#coding-standards)
  - [Commit Guidelines](#commit-guidelines)
  - [Code of Conduct](#code-of-conduct)

## How to Contribute

### Reporting Bugs

If you find a bug in the project, please submit a report via GitHub Issues. When submitting a report, please provide as much information as possible:

- A clear and descriptive title.
- Specific steps to reproduce the bug.
- What you expected to happen.
- What actually happened.
- Your environment information, such as operating system, browser version (if applicable), project version, etc.
- Relevant error logs or screenshots.

Before submitting a new issue, please search existing issues to ensure the problem hasn't already been reported.

### Feature Requests

If you have suggestions for new features or improvements to existing ones, please also submit them via GitHub Issues. Please describe in detail:

- The feature you would like to see implemented.
- The problem this feature attempts to solve or the benefits it would bring.
- (Optional) Your initial thoughts on how this feature might be implemented.

### Pull Requests

We greatly appreciate code contributions! Please follow these steps to submit a Pull Request (PR):

1.  **Fork the repository**: Fork the project to your own GitHub account.
2.  **Clone your fork**: Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/YOUR_USERNAME/media-auto-saver.git
    cd media-auto-saver
    ```
3.  **Create a branch**: Create a new feature branch from `main` (or the current primary development branch):
    ```bash
    git checkout -b feature/your-feature-name
    # Or
    git checkout -b fix/your-bug-fix-name
    ```
    Please use meaningful branch names, e.g., `feature/add-new-downloader` or `fix/login-page-bug`.
4.  **Make your changes**: Make your code modifications on the new branch.
5.  **Test your changes**: Ensure your changes do not break existing functionality and add new test cases whenever possible.
6.  **Commit your changes**: Write commit messages following the [Commit Guidelines](#commit-guidelines).
    ```bash
    git add .
    git commit -m "feat: Implement new amazing feature"
    ```
7.  **Push to your fork**: Push your changes to your fork on GitHub:
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **Create a Pull Request**: On GitHub, create a Pull Request from your feature branch to the original repository's `main` branch.
    - In the PR description, clearly explain your changes, the problem solved, and any relevant issue numbers (e.g., "Closes #123").
    - Ensure your PR passes all CI checks (if configured).

Project maintainers will review your PR and may suggest changes. Please be responsive to review feedback.

## Development Environment Setup

For detailed steps on setting up the development environment, please refer to the "Setup & Installation" section in the `README.md` file in the project root.

Key points to remember:
- **Backend (Python)**:
  - Python 3.8+
  - Use a virtual environment (recommended).
  - Install dependencies: `pip install -r backend/requirements.txt`
  - Ensure the `gallery-dl` CLI tool is installed and configured in your system's PATH.
- **Frontend (Node.js)**:
  - Node.js (LTS version recommended; check `frontend/package.json` for `engines` field if present for specific version compatibility).
  - Install dependencies: `cd frontend && npm install` (or `yarn install`).

## Coding Standards

To maintain consistency and readability of the codebase, please adhere to the following coding standards:

- **Python (Backend)**:
  - Follow the PEP 8 style guide.
  - Use Black for code formatting and Flake8 for linting (if these tools are configured in the project).
  - Write clear comments and docstrings.
- **JavaScript/Vue.js (Frontend)**:
  - Follow the existing coding style of the project (e.g., ESLint and Prettier configurations, if present).
  - Write maintainable and reusable components.
  - Add appropriate comments for Vue components and JavaScript functions.

## Commit Guidelines

We recommend following the Conventional Commits specification for writing commit messages. This helps in generating more meaningful changelogs and version history.

The commit message format is as follows:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Common `type`s include:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style adjustments (changes that do not affect the meaning of the code, e.g., white-space, formatting, missing semi-colons)
- `refactor`: Code refactoring (changes that neither fix a bug nor add a feature)
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Changes to the build process or auxiliary tools (e.g., dependency management)

Examples:
```
feat: Add support for Bilibili video downloads
fix: Correctly handle API errors in frontend
docs: Update installation instructions
```

## Code of Conduct

To foster a friendly and inclusive community environment, we expect all contributors to adhere to the project's Code of Conduct. If the project does not yet have a formal Code of Conduct, please follow general open-source community etiquette: be respectful, kind, and constructive in your communication.

Thank you for your contribution!
