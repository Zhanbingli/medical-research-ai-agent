# 🚀 快速开始指南

本指南帮助您在5分钟内启动并运行医学文献智能代理系统。

---

## 📋 前置要求

- Python 3.10 或更高版本
- 至少一个AI API密钥（Claude、Kimi或Qwen）
- 互联网连接

---

## ⚡ 快速安装（推荐）

### 步骤 1: 克隆或下载项目

```bash
cd /path/to/med_paper
```

### 步骤 2: 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或者 Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加你的API密钥
nano .env  # 或使用你喜欢的编辑器
```

**最少需要配置：**
```bash
# 至少添加一个AI提供商的API密钥
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 可选但推荐
PUBMED_EMAIL=your@email.com
```

### 步骤 4: 启动应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501` 🎉

---

## 🧪 测试安装

运行测试脚本验证配置：

```bash
python test_setup.py
```

你应该看到类似的输出：
```
✓ Python version: 3.10.x
✓ Dependencies installed
✓ Claude API: Available
✓ Configuration valid
✓ All systems ready!
```

---

## 💡 第一次使用

### 1. 选择AI提供商

在侧边栏选择你配置的AI模型：
- **Claude**: 高质量分析，适合复杂综合
- **Kimi**: 快速响应，中文支持好
- **Qwen**: 性价比高，多语言支持

### 2. 搜索文献

```
搜索示例：
- diabetes machine learning
- COVID-19 treatment
- alzheimer disease biomarkers
```

### 3. AI分析

点击文章下方的按钮：
- **AI Summary**: 快速摘要
- **Key Points**: 结构化要点
- **Synthesis**: 多文章综合分析

---

## 📊 功能概览

### ✅ 核心功能

- 🔍 PubMed搜索（数百万篇文献）
- 🤖 多AI分析（Claude/Kimi/Qwen）
- 📝 文章摘要和要点提取
- 📊 多文章综合分析
- 💬 文献问答系统
- 🔬 AI模型对比

### ✅ v2.0新功能

- 💾 智能缓存（1000倍速度提升）
- 💰 精确成本追踪
- 📈 性能监控
- ⚙️ 配置管理
- 📝 高级日志系统

---

## 🎯 使用示例

### 场景1：文献综述

```
1. 搜索: "CRISPR gene editing 2024"
2. 选择: 10篇文章
3. 点击: "Generate Synthesis"
4. 获得: 全面的综合分析报告
```

### 场景2：特定问题研究

```
1. 搜索: "diabetes treatment"
2. 切换到: "Q&A" 标签
3. 提问: "What are the most effective treatments?"
4. 获得: 基于文献的详细答案（附引用）
```

### 场景3：AI模型对比

```
1. 搜索任何主题
2. 切换到: "AI Comparison" 标签
3. 选择文章
4. 查看: 不同AI模型的分析差异
```

---

## ⚙️ 常用配置

### 成本控制

编辑 `.env`:
```bash
# 设置每日限额（美元）
COST_DAILY_LIMIT=5.0

# 设置每月限额（美元）
COST_MONTHLY_LIMIT=50.0
```

### 缓存设置

```bash
# 启用缓存（强烈推荐）
CACHE_ENABLED=true

# 缓存有效期（天）
CACHE_EXPIRY_DAYS=7

# 缓存大小限制（MB）
CACHE_SIZE_LIMIT_MB=500
```

### 日志配置

```bash
# 日志级别（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO

# 保存日志到文件（可选）
LOG_FILE=./logs/app.log
```

---

## 🔧 故障排除

### 问题1: "No AI providers available"

**原因**: 没有配置API密钥

**解决**:
```bash
# 检查 .env 文件
cat .env | grep API_KEY

# 确保至少有一个密钥配置正确
ANTHROPIC_API_KEY=sk-ant-xxxxx  # 替换为真实密钥
```

### 问题2: 应用启动慢

**原因**: 首次初始化缓存

**解决**: 等待几秒，后续启动会很快

### 问题3: PubMed搜索失败

**原因**: 网络问题或查询语法错误

**解决**:
1. 检查网络连接
2. 简化搜索查询
3. 设置 `PUBMED_EMAIL` 提高配额

### 问题4: 成本限制报错

**原因**: 达到每日/每月限额

**解决**:
```bash
# 增加限额或等待下一周期
COST_DAILY_LIMIT=20.0  # 增加到$20
```

### 问题5: 缓存占用太多空间

**解决**:
```bash
# 在应用中清理缓存
# 或者手动删除
rm -rf ./cache/*
```

---

## 📚 进阶使用

### 编程接口

```python
# 直接使用API（不通过UI）
from src.data_sources import PubMedClient
from src.agents import MultiAIAnalyzer

# 初始化
pubmed = PubMedClient()
analyzer = MultiAIAnalyzer()

# 搜索
articles = pubmed.search_and_fetch("diabetes", max_results=5)

# 分析
summary = analyzer.summarize_article(articles[0], provider="claude")
print(summary)
```

### 批量处理

```python
# 批量分析多篇文章
for article in articles:
    summary = analyzer.summarize_article(article)
    print(f"Title: {article['title']}")
    print(f"Summary: {summary}\n")
```

### 成本监控

```python
from src.utils.cost_tracker import get_cost_tracker

tracker = get_cost_tracker()

# 获取统计
stats = tracker.get_usage_stats()
print(f"Total cost: ${stats['total_cost']:.2f}")
print(f"Total tokens: {stats['total_tokens']:,}")

# 检查配额
quota = tracker.check_quota(daily_limit=10.0, monthly_limit=100.0)
if quota['daily_within_limit']:
    print("✓ Within daily limit")
```

---

## 🎓 学习资源

### 文档
- [README.md](README.md) - 完整功能说明
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - 详细优化报告
- [CHANGELOG.md](CHANGELOG.md) - 版本变更历史

### API文档
- [Claude API](https://docs.anthropic.com/)
- [Kimi API](https://platform.moonshot.cn/docs)
- [Qwen API](https://help.aliyun.com/zh/dashscope/)
- [PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)

---

## 💡 使用技巧

### 提示1: 利用缓存节省成本

第一次搜索后，相同查询会从缓存返回，几乎零成本！

### 提示2: 选择合适的AI

- 复杂分析 → Claude
- 快速摘要 → Kimi
- 大批量处理 → Qwen（性价比高）

### 提示3: 优化搜索查询

```bash
# ✅ 好的查询
diabetes machine learning 2024
COVID-19 treatment[Title/Abstract]
cancer AND immunotherapy

# ❌ 避免
the
diabetes
...
```

### 提示4: 监控成本

定期检查 `./cache/usage_stats.json` 了解使用情况

### 提示5: 定期清理缓存

每月清理一次旧缓存可以节省磁盘空间

---

## 🆘 获取帮助

### 检查日志
```bash
# 如果启用了日志文件
tail -f logs/app.log
```

### 运行诊断
```bash
# 检查系统状态
python test_setup.py

# 检查配置
python -c "from src.utils.config import get_config; print(get_config().to_dict())"
```

### 常见错误代码

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `ImportError` | 依赖未安装 | `pip install -r requirements.txt` |
| `ValueError: Invalid configuration` | .env配置错误 | 检查.env文件 |
| `API Error 401` | API密钥无效 | 更新API密钥 |
| `API Error 429` | 超过速率限制 | 等待或升级API配额 |

---

## 🚀 下一步

1. ✅ **熟悉界面**: 尝试不同的功能和AI模型
2. ✅ **优化配置**: 根据使用情况调整成本限制
3. ✅ **探索API**: 学习编程接口进行自动化
4. ✅ **监控使用**: 定期检查成本和性能统计
5. ✅ **提供反馈**: 报告问题或建议改进

---

## 📞 支持

遇到问题？
1. 查看本指南的故障排除部分
2. 阅读 [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md)
3. 检查日志文件
4. 提交 GitHub Issue（如果有仓库）

---

**祝使用愉快！🎉**

记住：
- ✅ 启用缓存节省成本
- ✅ 设置合理的成本限制
- ✅ 定期检查使用统计
- ✅ 永远不要提交 .env 文件！
