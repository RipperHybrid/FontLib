import fontforge
import os
import json
import hashlib
import sys

STATE_FILE = "patched.json"
FONTS_ROOT = "Fonts"
LOCAL_DONOR = os.path.join(FONTS_ROOT, "Roboto-Regular", "Roboto-Regular.ttf")
FALLBACK_DONOR = "/tmp/donor-Roboto-Regular.ttf"
DONOR_PATH = LOCAL_DONOR if os.path.isfile(LOCAL_DONOR) else FALLBACK_DONOR

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def load_state():
    if os.path.isfile(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)

def patch_font(custom_path, donor_path):
    custom = fontforge.open(custom_path, ("fstypepermitted",))
    donor = fontforge.open(donor_path, ("fstypepermitted",))

    if custom.em != donor.em:
        donor.em = custom.em

    custom_unicodes = set(g.unicode for g in custom.glyphs() if g.unicode != -1)

    donor.selection.none()
    for g in donor.glyphs():
        if g.unicode in custom_unicodes:
            donor.selection.select(("more",), g.glyphname)

    donor.clear()

    for lookup in donor.gpos_lookups:
        donor.removeLookup(lookup)
    for lookup in donor.gsub_lookups:
        donor.removeLookup(lookup)

    scaled_donor_path = "/tmp/scaled-donor.ttf"
    donor.generate(scaled_donor_path)

    custom.mergeFonts(scaled_donor_path)
    custom.generate(custom_path)

    custom.close()
    donor.close()

def run_issue_patch():
    import re
    import sys
    import shutil
    import zipfile
    import urllib.request
    import urllib.parse
    from fontTools.ttLib import TTFont

    body = os.environ.get("ISSUE_BODY", "").replace("\r\n", "\n")
    urls = list(dict.fromkeys(re.findall(r"https://github\.com/user-attachments/(?:files/\d+/[A-Za-z0-9._%~+-]+\.zip|assets/[a-zA-Z0-9-]+)", body)))

    if not urls:
        print("REJECT:No zip attachment was found. Compress your .ttf into a .zip, drag it into the text box, then submit. Open a new request.")
        return
    if len(urls) > 1:
        print(f"REJECT:{len(urls)} zip attachments were found. Only one zip per request is accepted.")
        return

    os.makedirs("work", exist_ok=True)
    os.makedirs("result", exist_ok=True)

    original_name = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(urls[0]).path))
    if not original_name.lower().endswith(".zip"):
        original_name = "fonts.zip"

    zip_path = os.path.join("work", original_name)
    output_name = original_name.replace(".zip", "-patched.zip")

    try:
        req = urllib.request.Request(urls[0], headers={"User-Agent": "FontDist"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(zip_path, "wb") as out:
            out.write(resp.read())
    except Exception:
        print("REJECT:Could not download the attachment. Open a new request and upload the zip again.")
        return

    names, skipped = [], []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            base = os.path.basename(info.filename.replace("\\", "/"))
            if base.startswith("."):
                continue
            if not base.lower().endswith(".ttf"):
                skipped.append(f"- `{base}` — skipped: not a .ttf file")
                continue
            try:
                with zf.open(info) as src:
                    test_font = TTFont(src)
                tags = set(test_font.keys())
                test_font.close()
                if "CFF " in tags or "CFF2" in tags:
                    skipped.append(f"- `{base}` — skipped: contains CFF outlines (OTF renamed to .ttf)")
                    continue
                if "fvar" in tags:
                    skipped.append(f"- `{base}` — skipped: is a variable font (fvar table)")
                    continue
                if tags & {"CBDT", "CBLC", "COLR", "CPAL", "sbix", "SVG "}:
                    skipped.append(f"- `{base}` — skipped: looks like a colour emoji font")
                    continue
            except Exception:
                skipped.append(f"- `{base}` — skipped: not a readable font file")
                continue
            if len(names) >= 10:
                skipped.append(f"- `{base}` — skipped: over the 10-font limit")
                continue
            name = re.sub(r"[^A-Za-z0-9._-]", "-", base)
            with zf.open(info) as src, open(os.path.join("work", name), "wb") as dst:
                dst.write(src.read())
            names.append(name)

    if not names:
        print("REJECT:No valid .ttf files were found to patch.\n" + "\n".join(skipped))
        return

    patched = []
    report = ["**Font Patch Request**", ""]
    for name in names:
        in_path = os.path.join("work", name)
        try:
            patch_font(in_path, DONOR_PATH)
            patched.append(name)
            patched_name = os.path.splitext(name)[0] + "-patched.ttf"
            report.append(f"- `{name}` → `{patched_name}` — patched")
        except Exception as e:
            skipped.append(f"- `{name}` — skipped: {str(e)[:100]}")

    report.extend(skipped)

    if not patched:
        print("REJECT:Nothing could be patched.\n" + "\n".join(skipped))
        return

    zip_out = os.path.join("result", output_name)
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in patched:
            zf.write(os.path.join("work", name), arcname=os.path.splitext(name)[0] + "-patched.ttf")

    with open("result/report.md", "w") as f:
        f.write("\n".join(report) + "\n")

    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"zip_name={output_name}\n")

    shutil.rmtree("work", ignore_errors=True)

    print("SUCCESS")

if "ISSUE_BODY" in os.environ:
    run_issue_patch()
    sys.exit(0)

if not os.path.isfile(DONOR_PATH):
    print(f"Donor font not found at {DONOR_PATH}, skipping patch step.")
else:
    donor_hash = sha256_of(DONOR_PATH)
    state = load_state()
    patched_count = 0
    skipped_count = 0

    for folder in sorted(os.listdir(FONTS_ROOT)):
        folder_path = os.path.join(FONTS_ROOT, folder)
        if not os.path.isdir(folder_path) or folder == "Roboto-Regular":
            continue

        for f in sorted(os.listdir(folder_path)):
            if not f.lower().endswith((".ttf", ".otf")):
                continue
            full_path = os.path.join(folder_path, f)
            rel_path = os.path.relpath(full_path)
            current_hash = sha256_of(full_path)

            record = state.get(rel_path)
            if record and record.get("patched_sha256") == current_hash and record.get("donor_sha256") == donor_hash:
                print(f"SKIP (already patched, unchanged): {rel_path}")
                skipped_count += 1
                continue

            print(f"PATCHING: {rel_path}")
            try:
                patch_font(full_path, DONOR_PATH)
                new_hash = sha256_of(full_path)
                state[rel_path] = {
                    "donor_sha256": donor_hash,
                    "patched_sha256": new_hash
                }
                patched_count += 1
                save_state(state)
            except Exception as e:
                print(f"FAILED to patch {rel_path}: {e}")

    print(f"\nPatch step done. Patched: {patched_count}, Skipped: {skipped_count}")
