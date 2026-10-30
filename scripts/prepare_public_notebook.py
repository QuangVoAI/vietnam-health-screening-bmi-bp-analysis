"""Create a public-safe notebook copy without local filesystem disclosure.

The analytical results remain intact. Printed local paths to the gated,
de-identified CSV and generated files are replaced by generic statements.
"""

from pathlib import Path
import re
import sys

import nbformat


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(
        "M3_BMI_HuyetAp_Final_Analysis.ipynb"
    )
    notebook = nbformat.read(target, as_version=4)
    data_pattern = re.compile(r"Dữ liệu:\s*/[^\n]+Research_Data\.csv")
    local_path_pattern = re.compile(r"/Users/[^\n]+")
    changed = 0

    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            text = output.get("text")
            if isinstance(text, str):
                updated, count = data_pattern.subn(
                    "Dữ liệu: Research_Data.csv (đã xác thực cục bộ; không công bố trong repo)",
                    text,
                )
                updated, path_count = local_path_pattern.subn("[đường dẫn cục bộ đã ẩn]", updated)
                output["text"] = updated
                changed += count + path_count

    if changed < 1:
        raise RuntimeError("No local path was found in notebook outputs.")
    nbformat.write(notebook, target)
    print(f"Sanitized {target}: {changed} local path removed.")


if __name__ == "__main__":
    main()
