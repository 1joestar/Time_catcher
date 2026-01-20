# 悬浮计时器打包为 EXE（Windows）

## 1. 准备 Python 环境
- 建议 Python 3.11+（3.10 也可）
- 本项目 UI 使用 Tkinter（标准库），无需额外依赖

## 2. 安装 PyInstaller

```bash
python -m pip install -U pyinstaller
```

## 3. 打包命令

在项目目录执行：

```bash
pyinstaller -F -w timer_app.py
```

- `-F`：打包为单个 exe
- `-w`：窗口程序（不弹控制台）

产物在：
- `dist/timer_app.exe`

## 4. 常见问题
- 如果提示缺少 tkinter：请安装带 Tcl/Tk 的官方 Python（Microsoft Store 版本有时不完整）。
- 反复打包前建议清理：删除 `build/`、`dist/`、`timer_app.spec` 后重试。

