# 🧘 StudyMonitor

<p align="center">
  <img src="https://img.shields.io/badge/Version-测试版%20v1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10%2B-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.x-brightgreen.svg" alt="Vue">
  <img src="https://img.shields.io/badge/Local%20AI-Ollama-orange.svg" alt="Ollama">
  <img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="License">
</p>

**StudyMonitor** 是一个本地优先、隐私安全的智能学习行为监控系统。它结合了轻量级计算机视觉（YOLO Pose）与本地大语言模型（Ollama + Qwen），在完全不依赖云端的情况下，为您提供实时的专注力分析、行为解释及自然语言驱动的规则管理。

---

## ✨ 核心特性

- 🔒 **隐私安全**：除 Ollama 模型下载外，所有视觉推断与语义解释均在本地完成，视频流绝不上传。
- 👁️ **实时姿态抽象**：基于 YOLO11n-pose 毫秒级识别低头、侧头、离开等语义动作。
- 🤖 **VLM 行为解释**：当状态变化时，自动调用本地 Qwen 模型生成人性化的行为反馈。
- 📝 **自然语言规则**：支持通过口语化指令（如“低头学习超过一分钟再提醒我”）一键生成复杂的判定逻辑。
- 🎨 **极简设计**：采用现代视觉风格的 UI，减少干扰，让重点回归学习本身。

---
## 📝当前版本功能

- 本地实时检测：通过 WebSocket 推送视频帧、检测结果和稳定状态。
- 学习会话闭环：支持开始学习、重置、结束并生成统计报告。
- 状态统计面板：展示专注时长、分心时长、专注率和状态分布。
- 行为语义解释：状态切换时调用本地 Ollama 模型生成简短解释，失败时降级为模板文本。
- 自然语言规则管理：支持将口语化规则解析为结构化规则并写入后端规则引擎。
- 学习陪伴对话框：新增普通文本聊天面板，可在学习过程中直接向本地模型提问或闲聊。
- 状态联动卡片配色：新增基于当前学习状态的前端主题联动，不同状态会改变卡片、按钮、输入框等界面强调色。
- 分心超时语音干预：新增“分心超过 120 秒”后的语音提醒和文本提醒，帮助用户尽快回到学习状态。

## 📂 项目结构

```text
StudyMonitor/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST API 路由
│   │   ├── model/               # SQLAlchemy ORM 模型
│   │   ├── schema/              # Pydantic 请求/响应模型
│   │   ├── service/             # 摄像头、检测、状态、规则、统计、语义等核心服务
│   │   ├── config.py            # 后端配置
│   │   ├── database.py          # 数据库初始化
│   │   └── main.py              # FastAPI 入口与 WebSocket 主链路
│   ├── data/                    # SQLite 数据目录
│   ├── models/                  # YOLO 模型目录
│   ├── tests/                   # 后端 pytest 测试
│   ├── environment.yml
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Vue 组件
│   │   ├── composables/         # 组合式 API 封装
│   │   ├── types/               # TypeScript 类型定义
│   │   ├── App.vue              # 页面主布局
│   │   └── style.css            # 全局样式与状态主题变量
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

分心提醒音频文件当前位于 `backend/interrupt.mp3`。

---

## 🛠️ 环境依赖

在开始部署前，请确保您的电脑满足以下条件：
- **操作系统**：Windows / macOS / Linux
- **硬件**：带有摄像头的设备（用于视觉监控）
- **软件**：
  - [Conda](https://www.anaconda.com/) (推荐) 或 Python 3.10+
  - [Node.js](https://nodejs.org/) (推荐 18.x 或更高)
  - [Ollama](https://ollama.com/) (用于支持 AI 解释)

---

## 🚀 保姆级部署教程

### 第一步：克隆项目与后端配置

1. **获取代码**：
   ```bash
   git clone https://github.com/shroudpro/StudyMonitor.git
   cd StudyMonitor
   ```

2. **创建 Python 环境**：
   ```bash
   # 创建并激活环境
   conda create -n study-monitor python=3.11
   conda activate study-monitor

   # 进入后端目录安装依赖
   cd backend
   pip install -r requirements.txt
   ```

3. **放置视觉模型（默认已完成）**：
   请确保 `backend/models/yolo11n-pose.onnx` 文件存在。如果不存在，请从官方 Release 或 [Ultralytics](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n-pose.onnx) 下载并改名放入该目录。

### 第二步：安装并配置 Ollama (AI 引擎)

1. **安装 Ollama**：前往 [Ollama.com](https://ollama.com/) 下载并安装。
2. **下载模型**：
   打开您的终端（PowerShell 或 CMD），运行以下命令获取轻量级 Qwen 模型：
   ```bash
   ollama pull qwen2.5:1.5b
   ```
3. **验证**：运行 `ollama list`，确认列表中包含 `qwen2.5:1.5b`。
4. **(可选) 节省 C 盘空间**：如果您的 C 盘空间紧张，请设置系统环境变量 `OLLAMA_MODELS` 指向其他盘符的文件夹。

### 第三步：前端编译
(请以管理员身份运行)
```bash
cd ../frontend
npm install
```

---

## 💻 使用指南

### 1. 启动服务
您需要开启两个终端窗口分别运行前后端：

*   **后端**：
    ```bash
    cd backend
    conda activate study-monitor
    python -m app.main
    ```
*   **前端**：
    ```bash
    cd frontend
    npm run dev
    ```
启动后，在浏览器访问 `http://localhost:3000`。

### 2. 开始监控
- **权限授予**：点击左侧视窗，允许浏览器调用摄像头。
- **开始学习**：点击下方的绿色 `开始学习` 按钮，系统将开启一个 Session 并记录数据。
- **查看解释**：当您从“专注”变为“分心”时，右侧会自动滚动出 AI 生成的实时原因分析。

### 3. 配置自定义规则
系统支持两种配置自定义逻辑的方式（优先级高于内置规则）：

**A. 自然语言生成 (VLM 解析)**：
- 点击“行为规则”面板中的 `AI生成` 切换至自然语言模式。
- 输入示例：“*如果我连续转头观望超过10秒，就判定为分心*”。
- 点击 `解析`，确认预览无误后点击 `确认并添加`。

**B. 手动 JSON 高级模式**：
如果你熟悉系统底层逻辑，可以直接输入传感器参数 JSON 定义规则对象：
- **可选状态变量**：
  - `is_present`: 布尔值 (检测到人)
  - `face_visible`: 布尔值 (看到正脸)
  - `head_down`: 布尔值 (低头)
  - `head_turned_away`: 布尔值 (歪头)
  - `posture_stable`: 布尔值 (身体静止)
  - `duration_sec`: 时间比较对象（例如 `{"duration_sec": {">": 30}}`）
- **手动定义示例**：
  假设你要建立一个名为 **"严格离开"** 的判定逻辑，只要人不在画面超过 30 秒就警告，你可以填写：
  - **触发状态**：选择 `离开`
  - **配置 JSON**：`{"is_present": false, "duration_sec": {">": 30}}`

---

## 📜 判定规则指南 (默认参数)

如果您未设置任何自定义规则，系统将执行以下**双轨制判定标准**：

| 状态 | 核心逻辑条件 | 设计初衷 |
| :--- | :--- | :--- |
| **专注 (FOCUS)** | **A. 伏案模式**：低头且静止 < 60s<br>**B. 屏幕模式**：抬头看屏且静止 < 30s | 兼容低头读写和看课件两种高价值场景。 |
| **分心 (DISTRACTED)** | 没在低头，且偏头/转头超过 10s | 允许短暂的转头思考，严厉打击长期走神。 |
| **离开 (AWAY)** | 完全检测不到人影超过 5s | 防抖防误判，给用户起身的宽限时间。 |
| **低效 (LOW)** | 超出上述静止门槛 (30s/60s) | 只针对“真正的极端僵直/发呆”进行提醒。 |

---

## ❓ 常见问题 (FAQ)

**Q: 为什么行为解释显示 [模板] 而不是 [VLM]？**  
A: 这表示系统无法连接到您的 Ollama 服务。请检查：1. Ollama 客户端是否已启动；2. 是否已执行 `ollama pull qwen2.5:1.5b`。

**Q: 画面显示“找不到摄像头”？**  
A: 请确保没有其他程序（如微信视频、会议软件）占用了摄像头，并确保后端终端没有报错提示摄像头索引错误。

**Q: 如何迁移模型存放位置？**  
A: 请设置系统环境变量 `OLLAMA_MODELS` 指向新路径（如 `E:\Models`），然后将旧的 `.ollama` 文件夹内容搬迁过去并重启 Ollama。

---

## 📄 开源协议
本项目基于 [MIT](LICENSE) 协议开源。
