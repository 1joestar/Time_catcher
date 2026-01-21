# Floating Timer (悬浮计时器)

一个基于 Python + Tkinter 开发的轻量级 Windows 悬浮计时器。
支持正向计时与倒计时，窗口半透明置顶且无边框，适合工作、学习、直播等场景下的时间管理。


## ✨ 功能特性

- **悬浮置顶**：窗口始终显示在屏幕最前端，半透明背景（默认 85% 透明度）不遮挡视线。
- **双模式支持**：
  - ⏱️ **正向计时**：秒表模式，记录经过的时间。
  - ⏳ **倒计时**：支持自定义 时/分/秒，归零后窗口闪烁提示。
- **极简交互**：
  - **无边框设计**：按住窗口任意位置（数字或背景）即可拖动。
  - **沉浸模式**：按 `Enter` 键一键隐藏所有按钮与设置框，仅保留纯净的时间显示。
- **完善的控制**：支持开始、停止（暂停）、归位（重置）。

## 🚀 快速开始

### 方式一：直接运行源码
确保已安装 Python 3.x（通常自带 Tkinter）。

```bash
# 克隆仓库或下载代码
git clone https://github.com/your-username/floating-timer.git
cd floating-timer

# 运行
python timer_app.py
```

### 方式二：运行 EXE (Windows)
如果已下载 Release 版本或自行打包，直接双击 `timer_app.exe` 即可运行，无需 Python 环境。

## 🎮 操作指南

### 快捷键 (Keyboard Shortcuts)

| 按键 | 功能描述 |
| :--- | :--- |
| **Space (空格)** | **开始 / 停止** 计时 |
| **Enter (回车)** | 切换 **精简模式**（仅显示数字）/ 完整模式 |
| **R** | **归位**（重置时间到初始状态） |
| **Esc** | **退出** 程序 |

### 界面交互
1. **拖动**：鼠标左键按住窗口任意区域拖动位置。
2. **倒计时**：
   - 切换到“倒计时”模式。
   - 输入 时、分、秒（支持回车键快速应用）。
   - 点击“开始计时”或按空格键。
3. **结束提示**：倒计时结束时，窗口背景会红黑闪烁，点击任意处或重置即可停止。

## 📦 打包指南 (Build EXE)

如果你修改了源码并想生成独立的 EXE 文件：

1. 安装 PyInstaller：
   ```bash
   pip install pyinstaller
   ```

2. 执行打包命令：
   ```bash
   pyinstaller -F -w timer_app.py
   ```
   - `-F`: 生成单文件 (One-file bundled executable)
   - `-w`: 运行是不显示控制台窗口 (Windowed mode)

3. 生成文件位于 `dist/timer_app.exe`。

## 🛠️ 技术栈
- **Language**: Python 3
- **GUI Framework**: Tkinter (标准库，无额外依赖)

## 📝 License
MIT License
