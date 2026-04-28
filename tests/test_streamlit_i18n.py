from __future__ import annotations

import ast
from pathlib import Path


def _load_ui_translations() -> dict:
    namespace: dict = {}
    translations_file = Path("streamlit_app/ui_translations.py")
    exec(translations_file.read_text(encoding="utf-8"), namespace)
    return namespace["UI_TRANSLATIONS"]


def _collect_used_translation_keys() -> set[str]:
    keys: set[str] = set()
    for path in Path("streamlit_app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "t":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    keys.add(node.args[0].value)
    return keys


def test_all_used_translation_keys_exist_in_hu_and_en() -> None:
    ui_translations = _load_ui_translations()
    used_keys = _collect_used_translation_keys()

    missing_hu = sorted(key for key in used_keys if key not in ui_translations["hu"])
    missing_en = sorted(key for key in used_keys if key not in ui_translations["en"])

    assert missing_hu == [], f"Missing HU translation keys: {missing_hu}"
    assert missing_en == [], f"Missing EN translation keys: {missing_en}"
