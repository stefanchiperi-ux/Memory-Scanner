from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from disk_analyzer import (
    CATEGORIES,
    ScanCancelled,
    ScanNode,
    ScanResult,
    format_size,
    scan_path,
)


MAX_TREE_CHILDREN_PER_FOLDER = 250


class DiskAnalyzerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GG-Scan")
        self.geometry("1100x720")
        self.minsize(920, 600)
        self._set_window_icon()

        self.selected_path = tk.StringVar(value=str(Path.home()))
        self.ignore_inaccessible = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Alege un folder sau un disc si porneste scanarea.")
        self.summary_text = tk.StringVar(value="Nicio scanare pornita.")

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.scan_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        self._configure_style()
        self._build_ui()
        self.after(120, self._process_events)

    def _set_window_icon(self) -> None:
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "gg_scan.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=25)
        style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Stat.TLabel", font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="Folder/disc de analizat").grid(row=0, column=0, sticky="w")
        ttk.Entry(header, textvariable=self.selected_path).grid(
            row=0, column=1, padx=8, sticky="ew"
        )
        ttk.Button(header, text="Alege...", command=self._choose_path).grid(row=0, column=2)
        ttk.Button(header, text="Scaneaza", style="Accent.TButton", command=self._start_scan).grid(
            row=0, column=3, padx=(8, 0)
        )
        ttk.Button(header, text="Opreste", command=self._stop_scan).grid(row=0, column=4, padx=(8, 0))

        options = ttk.Frame(root)
        options.grid(row=1, column=0, sticky="ew", pady=(10, 12))
        ttk.Checkbutton(
            options,
            text="Ignora folderele inaccesibile",
            variable=self.ignore_inaccessible,
        ).pack(side=tk.LEFT)
        ttk.Label(options, textvariable=self.status_text).pack(side=tk.LEFT, padx=(18, 0))

        panes = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        panes.grid(row=2, column=0, sticky="nsew")

        left = ttk.Frame(panes, padding=(0, 0, 10, 0))
        right = ttk.Frame(panes)
        panes.add(left, weight=1)
        panes.add(right, weight=2)

        left.rowconfigure(1, weight=1)
        left.rowconfigure(3, weight=1)
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Statistici", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.stats = tk.Text(left, height=9, wrap=tk.WORD, relief=tk.FLAT, background="#f5f7fa")
        self.stats.grid(row=1, column=0, sticky="nsew", pady=(6, 14))
        self.stats.configure(state=tk.DISABLED)

        ttk.Label(left, text="Cele mai mari foldere", style="Heading.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        self.top_table = ttk.Treeview(
            left,
            columns=("size", "category", "path"),
            show="headings",
            selectmode="browse",
        )
        self.top_table.heading("size", text="Dimensiune")
        self.top_table.heading("category", text="Categorie")
        self.top_table.heading("path", text="Folder")
        self.top_table.column("size", width=95, anchor=tk.E)
        self.top_table.column("category", width=120)
        self.top_table.column("path", width=300)
        self.top_table.grid(row=3, column=0, sticky="nsew", pady=(6, 0))

        top_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.top_table.yview)
        top_scroll.grid(row=3, column=1, sticky="ns", pady=(6, 0))
        self.top_table.configure(yscrollcommand=top_scroll.set)

        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)
        ttk.Label(right, text="Arbore structura foldere", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.tree = ttk.Treeview(
            right,
            columns=("size", "category", "items"),
            show="tree headings",
        )
        self.tree.heading("#0", text="Nume")
        self.tree.heading("size", text="Dimensiune")
        self.tree.heading("category", text="Categorie")
        self.tree.heading("items", text="Continut")
        self.tree.column("#0", width=430)
        self.tree.column("size", width=110, anchor=tk.E)
        self.tree.column("category", width=130)
        self.tree.column("items", width=150)
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        tree_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.grid(row=1, column=1, sticky="ns", pady=(6, 0))
        self.tree.configure(yscrollcommand=tree_scroll.set)

        ttk.Label(root, textvariable=self.summary_text, style="Stat.TLabel").grid(
            row=3, column=0, sticky="ew", pady=(12, 0)
        )

    def _choose_path(self) -> None:
        path = filedialog.askdirectory(initialdir=self.selected_path.get() or str(Path.home()))
        if path:
            self.selected_path.set(path)

    def _start_scan(self) -> None:
        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showinfo("Scanare in curs", "Exista deja o scanare pornita.")
            return

        path = self.selected_path.get().strip()
        if not path:
            messagebox.showwarning("Cale lipsa", "Alege un folder sau un disc de analizat.")
            return

        self._clear_results()
        self.stop_event.clear()
        self.status_text.set("Scanare in curs...")
        self.summary_text.set("Se calculeaza dimensiunile. Pentru discuri mari poate dura cateva minute.")

        self.scan_thread = threading.Thread(
            target=self._run_scan,
            args=(path, self.ignore_inaccessible.get()),
            daemon=True,
        )
        self.scan_thread.start()

    def _run_scan(self, path: str, ignore_inaccessible: bool) -> None:
        try:
            result = scan_path(
                path,
                ignore_inaccessible=ignore_inaccessible,
                progress_callback=self._progress_callback,
                stop_event=self.stop_event,
            )
            self.events.put(("done", result))
        except ScanCancelled as exc:
            self.events.put(("cancelled", str(exc)))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _progress_callback(self, path: str, files: int, folders: int) -> None:
        self.events.put(("progress", (path, files, folders)))

    def _stop_scan(self) -> None:
        self.stop_event.set()
        self.status_text.set("Se opreste scanarea...")

    def _process_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "progress":
                    path, files, folders = payload  # type: ignore[misc]
                    self.status_text.set(
                        f"Scanat: {files} fisiere, {folders} foldere | {path}"
                    )
                elif event == "done":
                    self._show_result(payload)  # type: ignore[arg-type]
                elif event == "cancelled":
                    self.status_text.set(str(payload))
                    self.summary_text.set("Scanarea a fost oprita de utilizator.")
                elif event == "error":
                    self.status_text.set("Eroare la scanare.")
                    messagebox.showerror("Eroare", str(payload))
        except queue.Empty:
            pass
        self.after(120, self._process_events)

    def _clear_results(self) -> None:
        self._set_stats_text("")
        for item in self.top_table.get_children():
            self.top_table.delete(item)
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _show_result(self, result: ScanResult) -> None:
        self.status_text.set("Scanare finalizata.")
        root = result.root
        self.summary_text.set(
            f"Gasit: {root.files_count} fisiere, {root.folders_count} foldere, "
            f"{root.skipped_count} elemente ignorate."
        )
        self._set_stats_text(self._build_stats_text(result))
        self._fill_top_table(result)
        self._insert_node("", root, expanded=True)

    def _build_stats_text(self, result: ScanResult) -> str:
        lines = [
            f"Spatiu total disc: {format_size(result.total_space)}",
            f"Spatiu ocupat disc: {format_size(result.used_space)}",
            f"Spatiu liber disc: {format_size(result.free_space)}",
            f"Dimensiune scanata: {format_size(result.root.size)}",
            "",
            "Distributie pe categorii:",
        ]
        scanned_size = max(result.root.size, 1)
        for category in CATEGORIES:
            size = result.category_sizes.get(category, 0)
            percent = size / scanned_size * 100
            lines.append(f"  {category}: {format_size(size)} ({percent:.1f}%)")

        if result.errors:
            lines.extend(
                [
                    "",
                    f"Elemente cu erori de acces: {len(result.errors)}",
                    "Primele erori:",
                ]
            )
            lines.extend(f"  - {error}" for error in result.errors[:5])

        return "\n".join(lines)

    def _set_stats_text(self, text: str) -> None:
        self.stats.configure(state=tk.NORMAL)
        self.stats.delete("1.0", tk.END)
        self.stats.insert(tk.END, text)
        self.stats.configure(state=tk.DISABLED)

    def _fill_top_table(self, result: ScanResult) -> None:
        for node in result.largest_folders[:50]:
            self.top_table.insert(
                "",
                tk.END,
                values=(format_size(node.size), node.category, str(node.path)),
            )

    def _insert_node(self, parent: str, node: ScanNode, expanded: bool = False) -> None:
        label = node.name
        if node.error:
            label = f"{label} [inaccesibil]"

        item_id = self.tree.insert(
            parent,
            tk.END,
            text=label,
            values=(
                format_size(node.size),
                node.category,
                f"{node.files_count} fisiere, {node.folders_count} foldere",
            ),
            open=expanded,
        )

        displayed = node.children[:MAX_TREE_CHILDREN_PER_FOLDER]
        for child in displayed:
            self._insert_node(item_id, child)

        hidden = len(node.children) - len(displayed)
        if hidden > 0:
            self.tree.insert(
                item_id,
                tk.END,
                text=f"... {hidden} elemente ascunse pentru performanta",
                values=("", "", ""),
            )


def main() -> None:
    app = DiskAnalyzerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
