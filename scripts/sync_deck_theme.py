from __future__ import annotations

import copy
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

NS = {"p": P_NS, "a": A_NS}

ET.register_namespace("a", A_NS)
ET.register_namespace("p", P_NS)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")


ROOT = Path(__file__).resolve().parent.parent
PRESENTATIONS_DIR = ROOT / "presentations"

REFERENCE = PRESENTATIONS_DIR / "ISYS814_FinalProject_TeamC_v1.pptx"
SOURCE = PRESENTATIONS_DIR / "ISYS814_TeamC_Draft_v2_CLAUDE.pptx"
OUTPUT = PRESENTATIONS_DIR / "ISYS814_TeamC_Draft_v2_CLAUDE_matched_to_v1.pptx"


def replace_tx_styles(reference_bytes: bytes, target_bytes: bytes) -> bytes:
    reference_root = ET.fromstring(reference_bytes)
    target_root = ET.fromstring(target_bytes)

    reference_tx = reference_root.find("p:txStyles", NS)
    target_tx = target_root.find("p:txStyles", NS)
    if reference_tx is None or target_tx is None:
        raise ValueError("Missing txStyles block in slide master.")

    target_index = list(target_root).index(target_tx)
    target_root.remove(target_tx)
    target_root.insert(target_index, copy.deepcopy(reference_tx))

    return ET.tostring(target_root, encoding="utf-8", xml_declaration=True)


def rewrite_fonts(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)
    changed = False

    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        typeface = element.attrib.get("typeface")
        if not typeface:
            continue

        if tag == "latin" and typeface in {"Arial Narrow", "Calibri Light", "Calibri", "Arial"}:
            element.set("typeface", "Univers Condensed")
            changed = True
        elif tag in {"ea", "cs"} and typeface in {"Arial Narrow", "Calibri Light", "Calibri", "Arial"}:
            element.set("typeface", "Univers Condensed")
            changed = True
        elif tag == "buFont" and typeface in {"Arial Narrow", "Calibri", "Arial"}:
            element.set("typeface", "Univers Condensed")
            changed = True

    if not changed:
        return xml_bytes
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main() -> None:
    reference_bytes = REFERENCE.read_bytes()
    source_bytes = SOURCE.read_bytes()

    with zipfile.ZipFile(REFERENCE) as ref_zip, zipfile.ZipFile(SOURCE) as src_zip, zipfile.ZipFile(
        OUTPUT, "w", compression=zipfile.ZIP_DEFLATED
    ) as out_zip:
        for info in src_zip.infolist():
            data = src_zip.read(info.filename)

            if info.filename == "ppt/theme/theme1.xml":
                data = ref_zip.read("ppt/theme/theme1.xml")
            elif info.filename == "ppt/slideMasters/slideMaster1.xml":
                data = replace_tx_styles(
                    ref_zip.read("ppt/slideMasters/slideMaster1.xml"),
                    data,
                )

            if info.filename.endswith(".xml") and info.filename.startswith("ppt/"):
                data = rewrite_fonts(data)

            out_zip.writestr(info, data)


if __name__ == "__main__":
    main()
