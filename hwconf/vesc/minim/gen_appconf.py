#!/usr/bin/env python3
"""Generate a baked APPCONF default header from a VESC Tool appconf XML export.

Field->macro mapping is extracted from confgenerator_set_defaults_appconf() in
confgenerator.c so it always matches the firmware being built. Per-unit values
(controller_id, uavcan_esc_index) are excluded: each pod header defines them.

Usage (run from the bldc root):
    gen_appconf.py <appconf.xml> <include_guard> <out.h>

Flight overrides listed in FORCE are written after the generated part with
#undef/#define, so they hold whatever the XML says.
"""
import re, sys, xml.etree.ElementTree as ET

CONFGEN = "confgenerator.c"

# Per-unit fields: set by each pod header (hw_minim_flight_<pod>.h).
EXCLUDE = {"controller_id", "uavcan_esc_index"}

# Values the flight build forces regardless of the XML: (macro, value, comment).
FORCE = [
    ("APPCONF_SHUTDOWN_MODE", "SHUTDOWN_MODE_ALWAYS_ON",
     "Never shut down from the smart switch in flight (24 Nov all ESC stop)."),
    ("APPCONF_UAVCAN_RAW_MODE", "UAVCAN_RAW_MODE_RPM",
     "The autopilot sends rpm set points over UAVCAN raw commands."),
]

def build_map(path):
    """Return {xml_tag: MACRO} from the set_defaults function body."""
    src = open(path).read()
    m = re.search(r"void\s+confgenerator_set_defaults_appconf.*?\{(.*?)\n\}", src, re.S)
    body = m.group(1)
    mapping = {}
    for fld, macro in re.findall(
            r"conf->([a-zA-Z0-9_.\[\]]+)\s*=\s*(APPCONF_[A-Z0-9_]+);", body):
        # VESC Tool writes nested fields as a.b and array items as name__i
        tag = re.sub(r"\[(\d+)\]", r"__\1", fld)
        mapping[tag] = macro
    return mapping

def fmt(v):
    v = v.strip()
    return v if v != "" else None

def main():
    xml_path, guard, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    mapping = build_map(CONFGEN)
    forced = {f[0] for f in FORCE}
    root = ET.parse(xml_path).getroot()
    lines, excluded, unmapped = [], [], []
    for el in root:
        tag = el.tag
        if tag in EXCLUDE:
            excluded.append(tag)
            continue
        if tag not in mapping:
            unmapped.append(tag)
            continue
        val = fmt(el.text or "")
        if val is None:
            unmapped.append(tag)
            continue
        macro = mapping[tag]
        note = "  // forced below" if macro in forced else ""
        lines.append(f"#ifndef {macro}\n#define {macro}\t\t\t{val}{note}\n#endif")
    with open(out_path, "w") as f:
        f.write(f"// Auto-generated baked app config. Source: {xml_path}\n")
        f.write(f"// Per-unit fields excluded (set by each pod header): {', '.join(excluded)}\n")
        f.write(f"// XML tags with no APPCONF_ macro (left at firmware defaults): {', '.join(unmapped)}\n")
        f.write(f"#ifndef {guard}\n#define {guard}\n\n")
        f.write("\n".join(lines))
        f.write("\n\n// Flight build values, forced regardless of the XML.\n")
        for macro, val, comment in FORCE:
            f.write(f"// {comment}\n#undef {macro}\n#define {macro}\t\t\t{val}\n")
        f.write(f"\n#endif\n")
    print(f"{out_path}: {len(lines)} defines, excluded {excluded}, unmapped {unmapped}")

if __name__ == "__main__":
    main()
