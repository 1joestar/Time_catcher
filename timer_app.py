import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from time import perf_counter


class TimerMode(str, Enum):
    UP = "正向计时"
    DOWN = "倒计时"


class TimerState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class TimerSnapshot:
    mode: TimerMode
    state: TimerState
    elapsed_seconds: float
    remaining_seconds: float | None


class TimerModel:
    def __init__(self) -> None:
        self._mode: TimerMode = TimerMode.UP
        self._state: TimerState = TimerState.IDLE
        self._target_seconds: int = 5 * 60
        self._start_perf: float | None = None
        self._accumulated_elapsed: float = 0.0

    @property
    def mode(self) -> TimerMode:
        return self._mode

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def target_seconds(self) -> int:
        return self._target_seconds

    def set_mode(self, mode: TimerMode) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        self.reset()

    def set_target_seconds(self, seconds: int) -> None:
        seconds = max(0, int(seconds))
        self._target_seconds = seconds
        if self._mode == TimerMode.DOWN and self._state in (TimerState.IDLE, TimerState.FINISHED):
            self._accumulated_elapsed = 0.0

    def start(self, now: float) -> None:
        if self._state == TimerState.RUNNING:
            return
        if self._state in (TimerState.IDLE, TimerState.FINISHED):
            self._accumulated_elapsed = 0.0
        self._start_perf = now
        self._state = TimerState.RUNNING

    def pause(self, now: float) -> None:
        if self._state != TimerState.RUNNING:
            return
        if self._start_perf is not None:
            self._accumulated_elapsed += now - self._start_perf
        self._start_perf = None
        self._state = TimerState.PAUSED

    def resume(self, now: float) -> None:
        if self._state != TimerState.PAUSED:
            return
        self._start_perf = now
        self._state = TimerState.RUNNING

    def reset(self) -> None:
        self._state = TimerState.IDLE
        self._start_perf = None
        self._accumulated_elapsed = 0.0

    def snapshot(self, now: float) -> TimerSnapshot:
        elapsed = self._accumulated_elapsed
        if self._state == TimerState.RUNNING and self._start_perf is not None:
            elapsed += now - self._start_perf

        if self._mode == TimerMode.UP:
            return TimerSnapshot(
                mode=self._mode,
                state=self._state,
                elapsed_seconds=elapsed,
                remaining_seconds=None,
            )

        remaining = self._target_seconds - elapsed
        if remaining <= 0:
            remaining = 0.0
            if self._state == TimerState.RUNNING:
                self._state = TimerState.FINISHED
                self._start_perf = None
        return TimerSnapshot(
            mode=self._mode,
            state=self._state,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining,
        )


def _format_hms(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class FloatingTimerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.model = TimerModel()

        self._update_job: str | None = None
        self._flash_job: str | None = None
        self._flash_remaining: int = 0
        self._drag_offset_x: int | None = None
        self._drag_offset_y: int | None = None

        self._bg = "#1f232a"
        self._fg = "#e6e6e6"
        self._accent = "#3b82f6"
        self._danger = "#b91c1c"

        self._time_text = tk.StringVar(value="00:00:00")
        self._mode_var = tk.StringVar(value=self.model.mode.value)
        self._hours_var = tk.StringVar(value="0")
        self._minutes_var = tk.StringVar(value="5")
        self._seconds_var = tk.StringVar(value="0")
        self._start_text = tk.StringVar(value="开始计时")
        self._compact = False
        self._restore_geometry: str | None = None

        self._build_window()
        self._build_ui()
        self._bind_events()
        self._sync_ui_from_model()

    def _build_window(self) -> None:
        self.root.title("悬浮计时器")
        self.root.configure(bg=self._bg)
        self.root.geometry("360x170+1200+80")
        self.root.minsize(320, 160)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.overrideredirect(True)

    def _build_ui(self) -> None:
        self.container = tk.Frame(self.root, bg=self._bg, bd=1, highlightthickness=1, highlightbackground="#2d333b")
        self.container.pack(fill="both", expand=True)

        self.top = tk.Frame(self.container, bg=self._bg)
        self.top.pack(fill="x", padx=10, pady=(8, 0))

        self.time_label = tk.Label(
            self.top,
            textvariable=self._time_text,
            bg=self._bg,
            fg=self._fg,
            font=("Segoe UI", 24, "bold"),
        )
        self.time_label.pack(side="left", anchor="w")

        self.close_btn = tk.Button(
            self.top,
            text="×",
            bg=self._bg,
            fg=self._fg,
            activebackground=self._bg,
            activeforeground=self._fg,
            bd=0,
            font=("Segoe UI", 16, "bold"),
            command=self.root.destroy,
            padx=6,
            pady=0,
        )
        self.close_btn.pack(side="right")

        self.mid = tk.Frame(self.container, bg=self._bg)
        self.mid.pack(fill="x", padx=10, pady=(8, 0))

        self.mode_up = tk.Radiobutton(
            self.mid,
            text=TimerMode.UP.value,
            value=TimerMode.UP.value,
            variable=self._mode_var,
            bg=self._bg,
            fg=self._fg,
            selectcolor=self._bg,
            activebackground=self._bg,
            activeforeground=self._fg,
            bd=0,
            command=self._on_mode_change,
        )
        self.mode_up.pack(side="left")

        self.mode_down = tk.Radiobutton(
            self.mid,
            text=TimerMode.DOWN.value,
            value=TimerMode.DOWN.value,
            variable=self._mode_var,
            bg=self._bg,
            fg=self._fg,
            selectcolor=self._bg,
            activebackground=self._bg,
            activeforeground=self._fg,
            bd=0,
            command=self._on_mode_change,
        )
        self.mode_down.pack(side="left", padx=(10, 0))

        self.down_cfg = tk.Frame(self.container, bg=self._bg)
        self.down_cfg.pack(fill="x", padx=10, pady=(6, 0))

        self.hours_entry = tk.Entry(self.down_cfg, width=4, textvariable=self._hours_var, justify="center")
        self.hours_entry.pack(side="left")
        tk.Label(self.down_cfg, text="时", bg=self._bg, fg=self._fg).pack(side="left", padx=(4, 8))

        self.minutes_entry = tk.Entry(self.down_cfg, width=4, textvariable=self._minutes_var, justify="center")
        self.minutes_entry.pack(side="left")
        tk.Label(self.down_cfg, text="分", bg=self._bg, fg=self._fg).pack(side="left", padx=(4, 8))

        self.seconds_entry = tk.Entry(self.down_cfg, width=4, textvariable=self._seconds_var, justify="center")
        self.seconds_entry.pack(side="left")
        tk.Label(self.down_cfg, text="秒", bg=self._bg, fg=self._fg).pack(side="left", padx=(4, 8))

        self.apply_btn = tk.Button(
            self.down_cfg,
            text="应用",
            bg=self._accent,
            fg="white",
            activebackground=self._accent,
            activeforeground="white",
            bd=0,
            padx=8,
            pady=2,
            command=self._apply_countdown,
        )
        self.apply_btn.pack(side="left")

        self.bottom = tk.Frame(self.container, bg=self._bg)
        self.bottom.pack(fill="x", padx=10, pady=(8, 10))

        self.start_btn = tk.Button(
            self.bottom,
            textvariable=self._start_text,
            bg=self._accent,
            fg="white",
            activebackground=self._accent,
            activeforeground="white",
            bd=0,
            padx=10,
            pady=4,
            command=self._on_start,
        )
        self.start_btn.pack(side="left")

        self.stop_btn = tk.Button(
            self.bottom,
            text="停止计时",
            bg="#374151",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            bd=0,
            padx=10,
            pady=4,
            command=self._on_stop,
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        self.reset_btn = tk.Button(
            self.bottom,
            text="归位",
            bg="#111827",
            fg="white",
            activebackground="#111827",
            activeforeground="white",
            bd=0,
            padx=10,
            pady=4,
            command=self._on_reset,
        )
        self.reset_btn.pack(side="right")

    def _bind_events(self) -> None:
        self.root.bind("<Escape>", lambda _e: self.root.destroy())
        self.root.bind("<space>", lambda _e: self._toggle_start_stop())
        self.root.bind("<Return>", lambda _e: self._toggle_compact())
        self.root.bind("<Key-r>", lambda _e: self._on_reset())
        self.root.bind("<Key-R>", lambda _e: self._on_reset())

        for widget in (self.container, self.time_label):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_move)
            widget.bind("<ButtonRelease-1>", self._on_drag_end)

        for widget in (self.hours_entry, self.minutes_entry, self.seconds_entry):
            widget.bind("<Return>", self._on_entry_return)

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _on_drag_move(self, event: tk.Event) -> None:
        if self._drag_offset_x is None or self._drag_offset_y is None:
            return
        x = self.root.winfo_x() + (event.x - self._drag_offset_x)
        y = self.root.winfo_y() + (event.y - self._drag_offset_y)
        self.root.geometry(f"+{x}+{y}")

    def _on_drag_end(self, _event: tk.Event) -> None:
        self._drag_offset_x = None
        self._drag_offset_y = None

    def _on_mode_change(self) -> None:
        mode = TimerMode.UP if self._mode_var.get() == TimerMode.UP.value else TimerMode.DOWN
        self._stop_flash()
        self._cancel_update_loop()
        self.model.set_mode(mode)
        if mode == TimerMode.DOWN:
            self._apply_countdown()
        self._sync_ui_from_model()

    def _on_entry_return(self, _event: tk.Event) -> str:
        self._apply_countdown()
        return "break"

    def _toggle_compact(self) -> None:
        if not self._compact:
            self._compact = True
            self._restore_geometry = self.root.geometry()
            self.close_btn.pack_forget()
            self.mid.pack_forget()
            self.down_cfg.pack_forget()
            self.bottom.pack_forget()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.root.minsize(200, 70)
            self.root.geometry(f"240x80+{x}+{y}")
        else:
            self._compact = False
            if self._restore_geometry:
                self.root.geometry(self._restore_geometry)
            self.root.minsize(320, 160)
            self.close_btn.pack(side="right")
            self.mid.pack(fill="x", padx=10, pady=(8, 0))
            self.down_cfg.pack(fill="x", padx=10, pady=(6, 0))
            self.bottom.pack(fill="x", padx=10, pady=(8, 10))
        self._sync_ui_from_model()

    def _apply_countdown(self) -> None:
        try:
            hours = int(self._hours_var.get() or "0")
        except ValueError:
            hours = 0
        try:
            minutes = int(self._minutes_var.get() or "0")
        except ValueError:
            minutes = 0
        try:
            seconds = int(self._seconds_var.get() or "0")
        except ValueError:
            seconds = 0
        total = max(0, hours) * 3600 + max(0, minutes) * 60 + max(0, seconds)
        self.model.set_target_seconds(total)
        if self.model.mode == TimerMode.DOWN and self.model.state in (TimerState.IDLE, TimerState.FINISHED):
            self._time_text.set(_format_hms(self.model.target_seconds))

    def _on_start(self) -> None:
        self._stop_flash()
        if self.model.mode == TimerMode.DOWN:
            self._apply_countdown()
            if self.model.target_seconds <= 0:
                self._sync_ui_from_model()
                return
        now = perf_counter()
        if self.model.state == TimerState.PAUSED:
            self.model.resume(now)
        else:
            self.model.start(now)
        self._ensure_update_loop()
        self._sync_ui_from_model()

    def _on_stop(self) -> None:
        self._stop_flash()
        now = perf_counter()
        if self.model.state == TimerState.RUNNING:
            self.model.pause(now)
            self._cancel_update_loop()
        self._sync_ui_from_model()

    def _toggle_start_stop(self) -> None:
        if self.model.state == TimerState.RUNNING:
            self._on_stop()
        else:
            self._on_start()

    def _on_reset(self) -> None:
        self._stop_flash()
        self._cancel_update_loop()
        self.model.reset()
        self._sync_ui_from_model()

    def _cancel_update_loop(self) -> None:
        if self._update_job is None:
            return
        try:
            self.root.after_cancel(self._update_job)
        except Exception:
            pass
        self._update_job = None

    def _ensure_update_loop(self) -> None:
        if self._update_job is None:
            self._update_job = self.root.after(50, self._on_update)

    def _on_update(self) -> None:
        self._update_job = None
        snap = self.model.snapshot(perf_counter())

        if snap.mode == TimerMode.UP:
            self._time_text.set(_format_hms(snap.elapsed_seconds))
        else:
            self._time_text.set(_format_hms(snap.remaining_seconds or 0))

        if snap.mode == TimerMode.DOWN and snap.state == TimerState.FINISHED:
            self._start_flash()
            self._sync_ui_from_model()
            return

        if snap.state == TimerState.RUNNING:
            self._ensure_update_loop()
        else:
            self._sync_ui_from_model()

    def _start_flash(self) -> None:
        if self._flash_job is not None:
            return
        self._flash_remaining = 8
        self._flash_step()

    def _flash_step(self) -> None:
        self._flash_job = None
        if self._flash_remaining <= 0:
            self.container.configure(bg=self._bg)
            self.time_label.configure(bg=self._bg)
            return
        self._flash_remaining -= 1
        is_danger = self._flash_remaining % 2 == 0
        bg = self._danger if is_danger else self._bg
        self.container.configure(bg=bg)
        self.time_label.configure(bg=bg)
        self._flash_job = self.root.after(160, self._flash_step)

    def _stop_flash(self) -> None:
        if self._flash_job is not None:
            try:
                self.root.after_cancel(self._flash_job)
            except Exception:
                pass
        self._flash_job = None
        self._flash_remaining = 0
        self.container.configure(bg=self._bg)
        self.time_label.configure(bg=self._bg)

    def _sync_ui_from_model(self) -> None:
        state = self.model.state
        mode = self.model.mode

        if mode == TimerMode.UP:
            self.hours_entry.configure(state="disabled")
            self.minutes_entry.configure(state="disabled")
            self.seconds_entry.configure(state="disabled")
            self.apply_btn.configure(state="disabled")
            if state == TimerState.IDLE:
                self._time_text.set("00:00:00")
        else:
            inputs_state = "normal" if state in (TimerState.IDLE, TimerState.FINISHED) else "disabled"
            self.hours_entry.configure(state=inputs_state)
            self.minutes_entry.configure(state=inputs_state)
            self.seconds_entry.configure(state=inputs_state)
            self.apply_btn.configure(state=inputs_state)
            if state == TimerState.IDLE:
                self._time_text.set(_format_hms(self.model.target_seconds))

        if state == TimerState.PAUSED:
            self._start_text.set("继续计时")
        else:
            self._start_text.set("开始计时")

        start_state = "normal" if state in (TimerState.IDLE, TimerState.PAUSED, TimerState.FINISHED) else "disabled"
        stop_state = "normal" if state == TimerState.RUNNING else "disabled"
        self.start_btn.configure(state=start_state)
        self.stop_btn.configure(state=stop_state)


def main() -> None:
    root = tk.Tk()
    app = FloatingTimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
