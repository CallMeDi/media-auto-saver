# Contributing to Media Auto Saver

首先，非常感谢您考虑为 Media Auto Saver 做出贡献！我们欢迎各种形式的贡献，无论是报告错误、提出功能建议，还是直接贡献代码。

## 目录

- [Contributing to Media Auto Saver](#contributing-to-media-auto-saver)
  - [目录](#目录)
  - [如何贡献](#如何贡献)
    - [报告错误 (Bug Reports)](#报告错误-bug-reports)
    - [功能请求 (Feature Requests)](#功能请求-feature-requests)
    - [代码贡献 (Pull Requests)](#代码贡献-pull-requests)
  - [开发环境设置](#开发环境设置)
  - [编码规范](#编码规范)
  - [提交规范](#提交规范)
  - [行为准则](#行为准则)

## 如何贡献

### 报告错误 (Bug Reports)

如果您在项目中发现了错误，请通过 GitHub Issues 提交报告。在提交报告时，请尽可能提供以下信息：

- 清晰且描述性的标题。
- 复现错误的具体步骤。
- 您期望发生的结果。
- 实际发生的结果。
- 您的操作系统、浏览器版本（如果适用）、项目版本等环境信息。
- 相关的错误日志或截图。

在提交新的 Issue 之前，请先搜索现有的 Issues，以确保问题尚未被报告。

### 功能请求 (Feature Requests)

如果您有关于新功能或改进现有功能的建议，也请通过 GitHub Issues 提交。请详细描述：

- 您希望实现的功能。
- 该功能试图解决的问题或带来的好处。
- （可选）您对如何实现该功能的初步想法。

### 代码贡献 (Pull Requests)

我们非常欢迎代码贡献！请遵循以下步骤提交 Pull Request (PR)：

1.  **Fork 仓库**: 将项目 Fork到您自己的 GitHub 账户。
2.  **Clone Fork**: 将您 Fork 的仓库 Clone 到本地：
    ```bash
    git clone https://github.com/YOUR_USERNAME/media-auto-saver.git
    cd media-auto-saver
    ```
3.  **创建分支**: 从 `main` (或当前主要的开发分支) 创建一个新的特性分支：
    ```bash
    git checkout -b feature/your-feature-name
    # 或者
    git checkout -b fix/your-bug-fix-name
    ```
    请使用有意义的分支名，例如 `feature/add-new-downloader` 或 `fix/login-page-bug`。
4.  **进行修改**: 在新分支上进行您的代码修改。
5.  **测试您的修改**: 确保您的修改没有破坏现有功能，并尽可能添加新的测试用例。
6.  **提交修改**: 遵循[提交规范](#提交规范)编写提交信息。
    ```bash
    git add .
    git commit -m "feat: Implement new amazing feature"
    ```
7.  **Push 到您的 Fork**: 将您的修改 Push 到您 GitHub 上的 Fork：
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **创建 Pull Request**: 在 GitHub 上，从您的特性分支向原始仓库的 `main` 分支发起 Pull Request。
    - 在 PR 描述中，清晰地说明您的修改内容、解决的问题以及任何相关的 Issue 编号 (例如, "Closes #123")。
    - 确保您的 PR 通过了所有的 CI 检查（如果配置了的话）。

项目维护者会审查您的 PR，并可能提出修改建议。请积极回应审查意见。

## 开发环境设置

详细的开发环境设置步骤请参考项目根目录下的 `README.md` 文件中的 "Setup & Installation" 部分。

关键点回顾：
- **后端 (Python)**:
  - Python 3.8+
  - 使用虚拟环境 (推荐)
  - 安装依赖: `pip install -r backend/requirements.txt`
  - 确保 `gallery-dl` CLI 工具已安装并配置在系统 PATH 中。
- **前端 (Node.js)**:
  - Node.js (建议使用 LTS 版本，具体版本请参考 `frontend/package.json` 中的 `engines` 字段，如果存在的话)
  - 安装依赖: `cd frontend && npm install` (或 `yarn install`)

## 编码规范

为了保持代码库的一致性和可读性，请遵循以下编码规范：

- **Python (Backend)**:
  - 遵循 PEP 8 编码风格指南。
  - 使用 Black进行代码格式化，使用 Flake8进行代码检查（如果项目配置了这些工具）。
  - 编写清晰的注释和文档字符串 (docstrings)。
- **JavaScript/Vue.js (Frontend)**:
  - 遵循项目现有的编码风格（例如，ESLint 和 Prettier 的配置，如果项目中有的话）。
  - 编写可维护和可重用的组件。
  - 为 Vue 组件和 JavaScript 函数添加适当的注释。

## 提交规范

我们建议遵循 Conventional Commits 规范来编写提交信息。这有助于生成更有意义的变更日志和版本历史。

提交信息的格式如下：
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

常见的 `type` 包括：
- `feat`: 新功能 (feature)
- `fix`: 修复错误 (bug fix)
- `docs`: 文档变更
- `style`: 代码风格调整 (不影响代码含义的修改，例如空格、格式化、缺少分号等)
- `refactor`: 代码重构 (既不是修复错误也不是添加新功能的代码修改)
- `perf`: 性能优化
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动 (例如依赖管理)

示例：
```
feat: Add support for Bilibili video downloads
fix: Correctly handle API errors in frontend
docs: Update installation instructions
```

## 行为准则

为了营造一个友好和包容的社区环境，我们期望所有贡献者都能遵守项目的行为准则。如果项目尚未制定明确的行为准则，请遵循通用的开源社区礼仪：保持尊重、友善和建设性的沟通。

感谢您的贡献！
