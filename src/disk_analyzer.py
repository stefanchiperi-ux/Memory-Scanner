from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable, Iterable


CATEGORY_SYSTEM = "Sistem"
CATEGORY_APPS = "Aplicatii"
CATEGORY_DOCUMENTS = "Documente"
CATEGORY_MEDIA = "Media"
CATEGORY_CACHE = "Cache/temporare"
CATEGORY_DOWNLOADS = "Descarcari"
CATEGORY_UNKNOWN = "Necunoscut"

CATEGORIES = (
    CATEGORY_SYSTEM,
    CATEGORY_APPS,
    CATEGORY_DOCUMENTS,
    CATEGORY_MEDIA,
    CATEGORY_CACHE,
    CATEGORY_DOWNLOADS,
    CATEGORY_UNKNOWN,
)

MEDIA_EXTENSIONS = {
    ".3gp",
    ".aac",
    ".avi",
    ".bmp",
    ".flac",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".png",
    ".raw",
    ".svg",
    ".tif",
    ".tiff",
    ".wav",
    ".webp",
    ".wmv",
}

DOCUMENT_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docx",
    ".md",
    ".odt",
    ".pdf",
    ".ppt",
    ".pptx",
    ".rtf",
    ".txt",
    ".xls",
    ".xlsx",
}

APP_EXTENSIONS = {
    ".appx",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".msi",
    ".sys",
}

SYSTEM_NAMES = {
    "$recycle.bin",
    "boot",
    "config.msi",
    "drivers",
    "efi",
    "msocache",
    "pagefile.sys",
    "perflogs",
    "programdata",
    "recovery",
    "system volume information",
    "system32",
    "windows",
    "winsxs",
}

APPLICATION_NAMES = {
    "appdata",
    "applications",
    "apps",
    "microsoft",
    "packages",
    "program files",
    "program files (x86)",
    "programs",
}

DOCUMENT_NAMES = {
    "desktop",
    "documents",
    "onedrive",
    "workspace",
    "workspaces",
}

MEDIA_NAMES = {
    "camera roll",
    "dcim",
    "images",
    "media",
    "movies",
    "music",
    "pictures",
    "photos",
    "videos",
}

CACHE_NAMES = {
    ".cache",
    "__pycache__",
    "cache",
    "crashdumps",
    "logs",
    "node_modules",
    "temp",
    "tmp",
    "temporary internet files",
}

DOWNLOAD_NAMES = {
    "download",
    "downloads",
    "descargas",
    "descarcari",
}


@dataclass
class ScanNode:
    path: Path
    name: str
    is_dir: bool
    size: int = 0
    category: str = CATEGORY_UNKNOWN
    children: list["ScanNode"] = field(default_factory=list)
    files_count: int = 0
    folders_count: int = 0
    skipped_count: int = 0
    error: str | None = None


@dataclass
class ScanResult:
    root: ScanNode
    total_space: int
    used_space: int
    free_space: int
    category_sizes: dict[str, int]
    largest_folders: list[ScanNode]
    errors: list[str]


ProgressCallback = Callable[[str, int, int], None]


class ScanCancelled(Exception):
    pass


def format_size(size: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    value = float(max(size, 0))
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


def scan_path(
    selected_path: str | os.PathLike[str],
    ignore_inaccessible: bool = True,
    progress_callback: ProgressCallback | None = None,
    stop_event: Event | None = None,
) -> ScanResult:
    root_path = Path(selected_path).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Calea nu exista: {root_path}")

    errors: list[str] = []
    counters = {"files": 0, "folders": 0}

    def progress(path: Path) -> None:
        if progress_callback and (counters["files"] + counters["folders"]) % 100 == 0:
            progress_callback(str(path), counters["files"], counters["folders"])

    root = _scan_node(
        root_path,
        errors,
        counters,
        ignore_inaccessible,
        progress,
        stop_event,
    )
    _sort_children(root)

    usage = shutil.disk_usage(root_path)
    category_sizes = _category_distribution(root)
    largest_folders = _largest_folders(root)

    if progress_callback:
        progress_callback(str(root_path), counters["files"], counters["folders"])

    return ScanResult(
        root=root,
        total_space=usage.total,
        used_space=usage.used,
        free_space=usage.free,
        category_sizes=category_sizes,
        largest_folders=largest_folders,
        errors=errors,
    )


def _scan_node(
    path: Path,
    errors: list[str],
    counters: dict[str, int],
    ignore_inaccessible: bool,
    progress: Callable[[Path], None],
    stop_event: Event | None,
) -> ScanNode:
    if stop_event and stop_event.is_set():
        raise ScanCancelled("Scanarea a fost oprita.")

    is_dir = path.is_dir()
    node = ScanNode(
        path=path,
        name=path.name or str(path),
        is_dir=is_dir,
        category=classify_path(path, is_dir),
    )

    if not is_dir:
        try:
            node.size = path.stat().st_size
            node.files_count = 1
            counters["files"] += 1
            progress(path)
        except OSError as exc:
            message = f"Nu pot citi fisierul {path}: {exc}"
            node.error = message
            errors.append(message)
            if not ignore_inaccessible:
                raise
        return node

    counters["folders"] += 1
    progress(path)
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                child_path = Path(entry.path)
                try:
                    child = _scan_node(
                        child_path,
                        errors,
                        counters,
                        ignore_inaccessible,
                        progress,
                        stop_event,
                    )
                except (PermissionError, OSError) as exc:
                    message = f"Folder/fisier inaccesibil {child_path}: {exc}"
                    errors.append(message)
                    if not ignore_inaccessible:
                        raise
                    child = ScanNode(
                        path=child_path,
                        name=child_path.name,
                        is_dir=entry.is_dir(follow_symlinks=False),
                        size=0,
                        category=classify_path(child_path, entry.is_dir(follow_symlinks=False)),
                        error=message,
                    )
                    node.skipped_count += 1
                node.children.append(child)
                node.size += child.size
                node.files_count += child.files_count
                node.folders_count += child.folders_count + (1 if child.is_dir else 0)
                node.skipped_count += child.skipped_count
    except (PermissionError, OSError) as exc:
        message = f"Nu pot deschide folderul {path}: {exc}"
        node.error = message
        errors.append(message)
        node.skipped_count += 1
        if not ignore_inaccessible:
            raise

    return node


def classify_path(path: Path, is_dir: bool) -> str:
    parts = [part.lower() for part in path.parts]
    name = path.name.lower()

    if any(part in DOWNLOAD_NAMES for part in parts):
        return CATEGORY_DOWNLOADS
    if name in CACHE_NAMES or any(part in CACHE_NAMES for part in parts):
        return CATEGORY_CACHE
    if any(part in SYSTEM_NAMES for part in parts):
        return CATEGORY_SYSTEM
    if any(part in APPLICATION_NAMES for part in parts):
        return CATEGORY_APPS
    if any(part in MEDIA_NAMES for part in parts):
        return CATEGORY_MEDIA
    if any(part in DOCUMENT_NAMES for part in parts):
        return CATEGORY_DOCUMENTS

    if not is_dir:
        suffix = path.suffix.lower()
        if suffix in MEDIA_EXTENSIONS:
            return CATEGORY_MEDIA
        if suffix in DOCUMENT_EXTENSIONS:
            return CATEGORY_DOCUMENTS
        if suffix in APP_EXTENSIONS:
            return CATEGORY_APPS

    return CATEGORY_UNKNOWN


def _sort_children(node: ScanNode) -> None:
    node.children.sort(key=lambda child: child.size, reverse=True)
    for child in node.children:
        _sort_children(child)


def _category_distribution(root: ScanNode) -> dict[str, int]:
    sizes = {category: 0 for category in CATEGORIES}
    children = root.children or [root]
    for child in children:
        sizes[child.category] = sizes.get(child.category, 0) + child.size
    return sizes


def _largest_folders(root: ScanNode, limit: int = 100) -> list[ScanNode]:
    folders = [node for node in _walk(root) if node.is_dir and node.path != root.path]
    folders.sort(key=lambda node: node.size, reverse=True)
    return folders[:limit]


def _walk(node: ScanNode) -> Iterable[ScanNode]:
    yield node
    for child in node.children:
        yield from _walk(child)
