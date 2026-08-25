import fontforge
import os
import json
import hashlib

STATE_FILE = "patched.json"
FONTS_ROOT = "Fonts"
DONOR_PATH = os.path.join(FONTS_ROOT, "Roboto-Regular", "Roboto-Regular.ttf")

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

    scaled_donor_path = "/tmp/_scaled_donor.ttf"
    donor.generate(scaled_donor_path)

    custom.mergeFonts(scaled_donor_path)
    custom.generate(custom_path)

    custom.close()
    donor.close()

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