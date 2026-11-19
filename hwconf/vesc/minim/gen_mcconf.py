#!/usr/bin/env python3
"""Generate a baked MCCONF default header from a VESC Tool mcconf XML export.

Field->macro mapping is extracted from confgenerator_set_defaults_mcconf() in
confgenerator.c so it always matches the firmware being built. Per-unit values
(current/voltage ADC offsets) are excluded so each ESC auto-calibrates at boot.
"""
import re, sys, xml.etree.ElementTree as ET

CONFGEN = "confgenerator.c"

# Per-unit or meaningless-to-bake fields: excluded from the generated header.
EXCLUDE = set()
for base in ("foc_offsets_current", "foc_offsets_voltage", "foc_offsets_voltage_undriven"):
    for i in range(3):
        EXCLUDE.add(f"{base}__{i}")

def build_map(path):
    """Return {xml_tag: MACRO} from the set_defaults function body."""
    src = open(path).read()
    m = re.search(r"void\s+confgenerator_set_defaults_mcconf.*?\{(.*?)\n\}", src, re.S)
    body = m.group(1)
    mapping = {}
    for fld, idx, macro in re.findall(
            r"conf->([a-zA-Z0-9_]+)(?:\[(\d+)\])?\s*=\s*(MCCONF_[A-Z0-9_]+);", body):
        tag = f"{fld}__{idx}" if idx != "" else fld
        mapping[tag] = macro
    return mapping

def fmt(v):
    v = v.strip()
    if v == "":
        return None
    # integers stay integers; everything numeric gets an f suffix if float-like
    if re.fullmatch(r"-?\d+", v):
        return v
    if re.fullmatch(r"-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", v):
        return v if v.endswith(("f", "F")) else v  # keep as double literal
    return v

def main():
    xml_path, guard, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    mapping = build_map(CONFGEN)
    root = ET.parse(xml_path).getroot()
    lines, skipped = [], []
    for el in root:
        tag = el.tag
        if tag in EXCLUDE:
            skipped.append(tag)
            continue
        if tag not in mapping:
            continue  # field has no overridable macro (strings, bms.*, ConfigVersion)
        val = fmt(el.text or "")
        if val is None:
            continue
        lines.append(f"#ifndef {mapping[tag]}\n#define {mapping[tag]}\t\t\t{val}\n#endif")
    with open(out_path, "w") as f:
        f.write(f"// Auto-generated baked motor config. Source: {xml_path}\n")
        f.write(f"// Per-unit ADC offsets excluded (auto-calibrated at boot): {', '.join(skipped)}\n")
        f.write(f"#ifndef {guard}\n#define {guard}\n\n")
        f.write("\n".join(lines))
        f.write(f"\n\n#endif\n")
    print(f"{out_path}: {len(lines)} defines, excluded {len(skipped)} per-unit offset fields")

if __name__ == "__main__":
    main()
