# 🔗 DataFusion-CLI

<p align="center">
  <b>Lightweight Terminal Multi-Source Data Fusion & Intelligent Analysis Engine</b><br>
  <b>轻量级终端多源数据融合与智能分析引擎</b><br>
  <code>Zero Dependencies · Pure Python · Cross-Platform</code>
</p>

<p align="center">
  <a href="https://github.com/gitstq/DataFusion-CLI/releases"><img src="https://img.shields.io/github/v/release/gitstq/DataFusion-CLI?color=blue" alt="Release"></a>
  <a href="https://github.com/gitstq/DataFusion-CLI/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey" alt="Platform"></a>
</p>

---

## 🎉 项目介绍 / Project Introduction

**DataFusion-CLI** 是一款零依赖的轻量级终端工具，专为解决多源数据整合痛点而设计。它能自动检测数据冲突、智能合并记录、发现数据关联关系，让分散在不同文件/系统中的数据轻松融合为统一视图。

**DataFusion-CLI** is a zero-dependency lightweight terminal tool designed to solve multi-source data integration pain points. It automatically detects data conflicts, intelligently merges records, and discovers data relationships — turning scattered data into a unified view.

---

## ✨ 核心特性 / Core Features

| 特性 Feature | 描述 Description |
|---|---|
| 🔗 **多源融合** | 支持 JSON/CSV 格式，自动类型推断 |
| ⚡ **冲突检测** | 跨源数据差异自动识别，分级告警 |
| 🧠 **智能合并** | 4 种策略：merge / newest / oldest / source_priority |
| 🔍 **关联发现** | 基于共同字段值发现记录间隐含关系 |
| 🖥️ **交互模式** | 彩色终端界面，命令补全，会话持久化 |
| 📊 **统计报表** | 融合结果多维统计，来源贡献分析 |
| 🎯 **零依赖** | 纯 Python 标准库，开箱即用 |

---

## 🚀 快速开始 / Quick Start

### 安装 Installation

```bash
# Clone 仓库
git clone https://github.com/gitstq/DataFusion-CLI.git
cd DataFusion-CLI

# 安装
pip install -e .

# 或直接使用
python -m datafusion
```

### 运行演示 Run Demo

```bash
datafusion demo
```

### 基本用法 Basic Usage

```bash
# 添加数据源
datafusion add -n users_a -f data/users1.json
datafusion add -n users_b -f data/users2.csv

# 查看数据源列表
datafusion list

# 按 id 字段融合
datafusion fuse -k id -s merge

# 查看冲突
datafusion conflicts

# 导出结果
datafusion export -f csv -o fused_result.csv

# 查看统计
datafusion stats
```

### 交互模式 Interactive Mode

```bash
datafusion -i
```

---

## 📖 详细使用指南 / Detailed Usage

### 命令参考 Command Reference

```
datafusion add -n <name> -f <file> [-t type]     添加数据源
datafusion list                                   列出所有源
datafusion schema <source>                        查看源结构
datafusion fuse -k <key> [-s strategy]            融合数据
datafusion export [-f format] [-o output]         导出结果
datafusion stats                                  统计信息
datafusion conflicts                              查看冲突
datafusion relations -k <key> -f <fields>         发现关联
datafusion demo                                   运行演示
```

### 冲突解决策略 Conflict Resolution Strategies

| 策略 Strategy | 说明 Description |
|---|---|
| `merge` | 合并所有非空字段，冲突值保留为列表 (默认) |
| `newest` | 后添加的数据源优先 |
| `oldest` | 先添加的数据源优先 |
| `source_priority` | 按数据源添加顺序优先级 |

### Python API

```python
from datafusion.core import DataFusionEngine, DataSource

engine = DataFusionEngine()
engine.add_source(DataSource("hr", "json", [...]))
engine.add_source(DataSource("it", "csv", [...]))

# 检测冲突
conflicts = engine.detect_conflicts("id")

# 融合数据
fused = engine.fuse("id", conflict_strategy="merge")

# 发现关联
relations = engine.find_relations("id", ["department", "city"])

# 导出
json_output = engine.export_fused("json")
```

---

## 💡 设计思路与迭代规划 / Design & Roadmap

### 架构设计 Architecture

```
┌─────────────────────────────────────────┐
│           DataFusion-CLI                │
├─────────────────────────────────────────┤
│  CLI Layer  │  Interactive TUI Mode     │
├─────────────────────────────────────────┤
│  Core Engine: Fusion + Conflict + Merge │
├─────────────────────────────────────────┤
│  Parsers: JSON / CSV / Auto-detect      │
├─────────────────────────────────────────┤
│  Session Persistence (.json)            │
└─────────────────────────────────────────┘
```

### 迭代规划 Roadmap

- [x] v1.0.0 核心融合引擎、冲突检测、CLI
- [ ] v1.1.0 支持 Excel / YAML / TOML 格式
- [ ] v1.2.0 数据清洗与转换规则引擎
- [ ] v1.3.0 可视化关联图谱导出 (HTML/SVG)
- [ ] v2.0.0 插件系统，支持自定义数据源适配器

---

## 📦 打包与部署 / Packaging

```bash
# 运行测试
python -m unittest tests.test_core -v

# 构建分发包
python setup.py sdist bdist_wheel

# 本地安装测试
pip install dist/datafusion-cli-1.0.0.tar.gz
```

---

## 🤝 贡献指南 / Contributing

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add some amazing feature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

---

## 📄 开源协议 / License

本项目采用 [MIT License](LICENSE) 开源协议。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
