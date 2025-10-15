# Utils 工具模块

## 📦 模块列表

### 1. 日志模块 (Logger)

功能完善的日志记录模块，支持文件输出、日志轮转、多级别记录等。

**核心文件：**
- `logger.py` - 日志模块核心代码

**文档：**
- 📘 [快速入门](QUICK_START.md) - 5分钟快速上手
- 📗 [详细文档](LOGGER_README.md) - 完整使用指南
- 📙 [完成总结](SUMMARY.md) - 功能概述和测试结果

**示例：**
- `logger_example.py` - 运行示例：`python3 src/utils/logger_example.py`
- `main_integration_example.py` - main.py集成参考

**快速开始：**

```python
from src.utils.logger import get_error_logger

logger = get_error_logger()
logger.error("发生了一个错误")
```

查看 [QUICK_START.md](QUICK_START.md) 了解更多。

---

## 🚀 快速导航

| 需求 | 文档 |
|------|------|
| 🎯 5分钟快速上手 | [QUICK_START.md](QUICK_START.md) |
| 📖 完整使用指南 | [LOGGER_README.md](LOGGER_README.md) |
| ✅ 功能总结 | [SUMMARY.md](SUMMARY.md) |
| 💻 运行示例 | `python3 src/utils/logger_example.py` |
| 🔧 集成到项目 | [main_integration_example.py](main_integration_example.py) |

---

_更多工具模块开发中..._
