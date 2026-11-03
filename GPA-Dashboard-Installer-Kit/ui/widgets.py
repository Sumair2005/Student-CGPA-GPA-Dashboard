"""Reusable widgets: cards, tables, tooltips, scrolling and form dialogs."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Any, Callable, Mapping, Sequence

from core.validators import ValidationError
from ui.theme import FONT_FAMILY, Palette, ThemeManager

PAD = 28  # horizontal page padding


# ---------------------------------------------------------------------- tooltip
class Tooltip:
    """Small hover hint for a widget."""

    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 500) -> None:
        self.widget, self.text, self.delay_ms = widget, text, delay_ms
        self._job: str | None = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: tk.Event) -> None:
        self._cancel()
        self._job = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._job is not None:
            self.widget.after_cancel(self._job)
            self._job = None

    def _show(self) -> None:
        if self._window is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_geometry(f"+{x}+{y}")
        tk.Label(self._window, text=self.text, bg="#111827", fg="#f9fafb",
                 padx=8, pady=4, font=(FONT_FAMILY, 9)).pack()

    def _hide(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None


# ------------------------------------------------------------------ containers
class Card(ttk.Frame):
    """A bordered surface that groups related content."""

    def __init__(self, parent: tk.Misc, padding: int = 16) -> None:
        super().__init__(parent, style="Card.TFrame", padding=padding)


class StatCard(Card):
    """Dashboard number card: small title, big value, subtitle."""

    def __init__(self, parent: tk.Misc, title: str, value: str, sub: str = "") -> None:
        super().__init__(parent, padding=18)
        ttk.Label(self, text=title.upper(), style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(self, text=value, style="CardValue.TLabel").pack(anchor="w", pady=(6, 2))
        ttk.Label(self, text=sub or " ", style="CardSub.TLabel").pack(anchor="w")


class ScrollableFrame(ttk.Frame):
    """Vertically scrollable area; put content in ``self.inner``."""

    def __init__(self, parent: tk.Misc, theme: ThemeManager) -> None:
        super().__init__(parent, style="Bg.TFrame")
        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=theme.palette.bg)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.inner = ttk.Frame(self._canvas, style="Bg.TFrame")
        self._window = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.inner.bind("<Configure>", lambda _e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(
            self._window, width=e.width))
        self._canvas.bind("<Enter>", self._bind_wheel)
        self._canvas.bind("<Leave>", self._unbind_wheel)
        self.inner.bind("<Enter>", self._bind_wheel)
        theme.subscribe(lambda palette: self._canvas.configure(bg=palette.bg))

    def _bind_wheel(self, _event: tk.Event) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_wheel)
        self._canvas.bind_all("<Button-4>", self._on_wheel)
        self._canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _event: tk.Event) -> None:
        # Leaving the canvas onto its own child frame should keep scrolling alive.
        pointer = self.winfo_containing(*self.winfo_pointerxy())
        if pointer is not None and str(pointer).startswith(str(self)):
            return
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._canvas.unbind_all(sequence)

    def _on_wheel(self, event: tk.Event) -> None:
        if isinstance(event.widget, ttk.Treeview):
            return  # tables scroll themselves
        if self.inner.winfo_reqheight() <= self._canvas.winfo_height():
            return
        if getattr(event, "num", 0) == 4:
            step = -1
        elif getattr(event, "num", 0) == 5:
            step = 1
        else:
            step = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(step * 2, "units")


class BasePage(ttk.Frame):
    """Base class for the pages shown in the main content area."""

    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, style="Bg.TFrame")
        self.app = app

    def refresh(self) -> None:  # pragma: no cover - overridden by pages
        raise NotImplementedError

    @staticmethod
    def build_header(parent: tk.Misc, title: str, subtitle: str = "") -> ttk.Frame:
        """Create a title row; returns a frame on the right for action buttons."""
        row = ttk.Frame(parent, style="Bg.TFrame")
        row.columnconfigure(0, weight=1)
        titles = ttk.Frame(row, style="Bg.TFrame")
        titles.grid(row=0, column=0, sticky="w")
        ttk.Label(titles, text=title, style="PageTitle.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(titles, text=subtitle, style="Subtitle.TLabel").pack(anchor="w")
        actions = ttk.Frame(row, style="Bg.TFrame")
        actions.grid(row=0, column=1, sticky="e")
        row.grid(sticky="ew", padx=PAD, pady=(24, 14))
        return actions


# ----------------------------------------------------------------------- tables
@dataclass(frozen=True)
class Column:
    key: str
    title: str
    width: int = 100
    anchor: str = "w"
    stretch: bool = False


class DataTable(ttk.Frame):
    """Treeview with scrollbar, zebra rows and an empty-state message."""

    def __init__(self, parent: tk.Misc, theme: ThemeManager, columns: Sequence[Column],
                 height: int = 8, empty_text: str = "No data yet.") -> None:
        super().__init__(parent, style="Inner.TFrame")
        self.theme = theme
        self.columns = tuple(columns)
        self.empty_text = empty_text
        self.tree = ttk.Treeview(self, columns=[c.key for c in columns], show="headings",
                                 height=height, selectmode="browse")
        for column in columns:
            self.tree.heading(column.key, text=column.title,
                              anchor="w" if column.anchor == "w" else "center")
            self.tree.column(column.key, width=column.width, minwidth=50,
                             anchor=column.anchor, stretch=column.stretch)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._empty = ttk.Label(self, text=empty_text, style="CardMuted.TLabel")
        theme.subscribe(self._restyle)
        self.bind("<Destroy>", self._on_destroy)
        self._restyle(theme.palette)

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self:
            self.theme.unsubscribe(self._restyle)

    def _restyle(self, palette: Palette) -> None:
        self.tree.tag_configure("odd", background=palette.surface)
        self.tree.tag_configure("even", background=palette.row_alt)

    def set_rows(self, rows: Sequence[tuple[str, Sequence[Any]]],
                 empty_text: str | None = None) -> None:
        """Replace all rows (keeping the selection if possible).

        Each row is ``(item id, values)``.
        """
        previous = self.selected()
        self.tree.delete(*self.tree.get_children())
        for index, (iid, values) in enumerate(rows):
            self.tree.insert("", "end", iid=iid, values=list(values),
                             tags=("even" if index % 2 else "odd",))
        if previous is not None and self.tree.exists(previous):
            self.tree.selection_set(previous)
            self.tree.focus(previous)
        if empty_text is not None:
            self._empty.configure(text=empty_text)
        if rows:
            self._empty.place_forget()
        else:
            self._empty.place(relx=0.5, rely=0.55, anchor="center")

    def selected(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def select(self, iid: str) -> None:
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)


# ---------------------------------------------------------------------- dialogs
@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str = "entry"  # "entry" or "combo"
    values: tuple[str, ...] = ()


class FormDialog(tk.Toplevel):
    """Modal form. ``show()`` returns the cleaned values or ``None``."""

    def __init__(self, parent: tk.Misc, theme: ThemeManager, title: str,
                 fields: Sequence[Field],
                 validator: Callable[[Mapping[str, str]], dict[str, Any]],
                 initial: Mapping[str, Any] | None = None, ok_text: str = "Save") -> None:
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=theme.palette.bg)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.result: dict[str, Any] | None = None
        self._validator = validator
        self._vars: dict[str, tk.StringVar] = {}

        frame = ttk.Frame(self, style="Bg.TFrame", padding=(26, 22))
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, style="DialogTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 14))

        first_widget: tk.Widget | None = None
        initial = initial or {}
        for index, field in enumerate(fields):
            base_row = 1 + index * 2
            ttk.Label(frame, text=field.label, style="Muted.TLabel").grid(
                row=base_row, column=0, sticky="w", pady=(6, 2))
            var = tk.StringVar(value=str(initial.get(field.key, "")))
            self._vars[field.key] = var
            if field.kind == "combo":
                widget: tk.Widget = ttk.Combobox(frame, textvariable=var, values=field.values,
                                                 state="readonly", width=34)
            else:
                widget = ttk.Entry(frame, textvariable=var, width=36)
            widget.grid(row=base_row + 1, column=0, sticky="ew")
            first_widget = first_widget or widget

        end_row = 2 + len(fields) * 2
        self._error = tk.StringVar()
        ttk.Label(frame, textvariable=self._error, style="Error.TLabel",
                  wraplength=360, justify="left").grid(
            row=end_row, column=0, sticky="w", pady=(12, 0))
        buttons = ttk.Frame(frame, style="Bg.TFrame")
        buttons.grid(row=end_row + 1, column=0, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text=ok_text, style="Accent.TButton",
                   command=self._submit).pack(side="left")

        self.bind("<Return>", lambda _e: self._submit())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._center(parent)
        self.deiconify()
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass  # modality is a nicety; the dialog still works without it
        if first_widget is not None:
            first_widget.focus_set()

    def _center(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        top = parent.winfo_toplevel()
        x = top.winfo_rootx() + (top.winfo_width() - self.winfo_reqwidth()) // 2
        y = top.winfo_rooty() + (top.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _submit(self) -> None:
        raw = {key: var.get() for key, var in self._vars.items()}
        try:
            self.result = self._validator(raw)
        except ValidationError as exc:
            self._error.set(str(exc))
            return
        self.destroy()

    def show(self) -> dict[str, Any] | None:
        self.wait_window(self)
        return self.result


def confirm(parent: tk.Misc, title: str, message: str) -> bool:
    """Ask a yes/no question; the safe answer (No) is the default."""
    return bool(messagebox.askyesno(title, message, icon="warning", default="no",
                                    parent=parent.winfo_toplevel()))
