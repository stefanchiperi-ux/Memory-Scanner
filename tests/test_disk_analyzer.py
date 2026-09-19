from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.disk_analyzer import (
    CATEGORY_CACHE,
    CATEGORY_DOCUMENTS,
    CATEGORY_DOWNLOADS,
    CATEGORY_MEDIA,
    classify_path,
    scan_path,
)


class DiskAnalyzerTests(unittest.TestCase):
    def test_scan_calculates_sizes_and_sorts_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            media = root / "Pictures"
            downloads.mkdir()
            media.mkdir()

            (downloads / "installer.bin").write_bytes(b"a" * 30)
            (media / "photo.jpg").write_bytes(b"b" * 10)
            (root / "notes.txt").write_bytes(b"c" * 5)

            result = scan_path(root)

            self.assertEqual(result.root.size, 45)
            self.assertEqual(result.root.files_count, 3)
            self.assertEqual(result.root.folders_count, 2)
            self.assertEqual(result.root.children[0].name, "Downloads")
            self.assertEqual(result.root.children[0].size, 30)
            self.assertEqual(result.largest_folders[0].category, CATEGORY_DOWNLOADS)

    def test_classifies_common_paths(self) -> None:
        self.assertEqual(classify_path(Path("C:/Users/me/Downloads/file.zip"), False), CATEGORY_DOWNLOADS)
        self.assertEqual(classify_path(Path("C:/Users/me/Documents/report.pdf"), False), CATEGORY_DOCUMENTS)
        self.assertEqual(classify_path(Path("C:/Users/me/Pictures/photo.jpg"), False), CATEGORY_MEDIA)
        self.assertEqual(classify_path(Path("C:/Temp/cache.bin"), False), CATEGORY_CACHE)


if __name__ == "__main__":
    unittest.main()
