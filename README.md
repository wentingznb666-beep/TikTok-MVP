# 🛍️ TikTok 电商卖家助手 MVP

面向 **TikTok 跨境中小个体户卖家** 的 AI 爆款短视频分析工具。  
上传带货视频或粘贴口播文案，AI 自动输出 **6 维度分析报告**，附带 🇹🇭 泰语版脚本。

---

## ✨ 功能特性

- **📊 6 维度视频分析**：结构拆解、话术技巧、受众情绪、视听配合、亮点避雷、复用优化
- **🔄 中泰双向翻译**：专为泰国市场卖家设计，支持带货话术本地化
- **🎬 视频转写**：上传 mp4/mov 自动提取音频 → Whisper 语音转文字 → AI 分析
- **🖼️ 图片理解**：可选上传商品截图，AI 结合图片进行更精准分析
- **🔗 分享链接**：一键生成分享链接，团队成员无需登录即可查看
- **🌐 中泰双语 UI**：全站支持中文/泰语切换
- **📱 响应式设计**：移动端单栏、桌面端双栏布局

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- ffmpeg（视频处理）
- DeepSeek API Key

### 本地运行

```bash
# 1. 克隆项目
cd TikTok电商卖家助手MVP

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（编辑 .env）
# DEEPSEEK_API_KEY=sk-your-key
# JWT_SECRET=your-secret

# 5. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000

### Docker 部署

```bash
# 确保 .env 已配置
docker-compose up -d
```

---

## 📡 API 接口

### 无需登录

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/share/{token}` | 查看分享的分析 |
| GET | `/api/health` | 健康检查 |

### 需要登录（Bearer Token）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/analyze` | 提交分析（文案/视频/图片） |
| GET | `/api/history` | 历史记录列表 |
| GET | `/api/history/{id}` | 历史记录详情 |
| POST | `/api/translate` | 中泰翻译 |

---

## 📂 项目结构

```
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置中心
│   ├── routers/
│   │   ├── auth.py              # 认证路由
│   │   └── analyze.py           # 分析 & 翻译路由
│   ├── services/
│   │   ├── database.py          # SQLite 数据库
│   │   ├── auth_service.py      # 注册/登录/JWT
│   │   ├── deepseek_client.py   # DeepSeek API 客户端
│   │   ├── prompt_service.py    # 提示词服务
│   │   ├── history_service.py   # 历史记录
│   │   └── video_service.py     # 视频处理/Whisper
│   ├── models/
│   │   ├── user.py              # 数据实体
│   │   └── schemas.py           # Pydantic 校验模型
│   └── static/
│       ├── i18n.js              # 中泰双语字典
│       ├── login.html           # 登录/注册页
│       ├── index.html           # 主页面
│       └── app.js               # 前端交互逻辑
├── prompts/
│   ├── video_analysis.txt       # 视频分析提示词
│   └── translate.txt            # 翻译提示词
├── data/                        # SQLite + 上传文件（不提交Git）
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | Python 3.11 + FastAPI |
| AI | DeepSeek API（deepseek-chat，支持 Vision） |
| 语音识别 | OpenAI Whisper（base 模型） |
| 视频处理 | ffmpeg |
| 数据库 | SQLite（aiosqlite 异步驱动） |
| 认证 | JWT + bcrypt |
| 前端 | 原生 HTML/CSS/JS（无框架） |

---

## ⚠️ 注意事项

- 首次启动时会自动下载 Whisper base 模型（约 140MB）
- 视频文件限制最大 100MB
- `.env` 和 `data/` 目录不会提交到 Git
- Whisper 首次转写速度取决于 CPU 性能

---

## 📝 License

MIT
