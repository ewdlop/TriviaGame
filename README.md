# 智能问答游戏

这是一个基于 React + TypeScript 前端和 Python FastAPI 后端的智能问答游戏应用。该应用使用 Ollama 进行问题生成，支持从 PDF 和 Markdown 文档中提取内容来生成相关问题。

## 功能特点

- 支持 PDF 和 Markdown 文档输入
- 使用 Ollama 进行智能问题生成
- 实时问答和评分系统
- 响应式用户界面
- 完整的游戏流程管理

## 技术栈

### 前端
- React 18
- TypeScript
- Redux Toolkit
- Material-UI
- Axios

### 后端
- Python 3.8+
- FastAPI
- LangChain
- Ollama
- ChromaDB
- python-magic (用于文件类型检测)

## 安装说明

### 系统要求

- Python 3.8+
- Node.js 14+
- Ollama
- libmagic (用于文件类型检测)

### macOS 系统依赖安装

```bash
brew install libmagic # Mac
```

### windows 系统依赖安装
python-magic-bin==0.4.14 


### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（可选）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动后端服务：
```bash
python app.py
```

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm start
```

## 使用说明

1. 确保已安装并运行 Ollama
2. 启动后端服务（默认运行在 http://localhost:5000）
3. 启动前端服务（默认运行在 http://localhost:3000）
4. 在浏览器中访问 http://localhost:3000
5. 选择文档类型（PDF 或 Markdown）
6. 输入文档内容
7. 开始问答游戏

## 注意事项

- 确保 Ollama 服务正在运行
- 后端服务需要 Python 3.8 或更高版本
- 前端需要 Node.js 14 或更高版本
- macOS 用户需要安装 libmagic
- Windows 用户需要安装 python-magic-bin

### 常见问题解决

#### 端口冲突

## 许可证

MIT 