"""
Project ke root me rakho (jahan 'app' aur 'tests' folder hain) aur chalao:
    python fix_and_check.py

Ye karta hai:
  1) tests/test_core.py me purana naam token_minutes -> jwt_expire_minutes
  2) app/main.py me notifications.router ko products.router se PEHLE rakhta hai
  3) app/routers/notifications.py check karta hai (bell + Alerts ke liye sahi hai ya nahi)
  4) Frontend (index.html) jo /api/... bulata hai, wo sab backend me hain ya nahi - report deta hai
Har badli hui file ka backup  <naam>.bak  bana deta hai.
"""
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
changed = []


def backup(p):
    b = p.with_name(p.name + ".bak")
    if not b.exists():
        shutil.copy2(p, b)


# ---------- 1) tests/test_core.py ----------
tc = ROOT / "tests" / "test_core.py"
if tc.exists():
    s = tc.read_text(encoding="utf-8")
    if "token_minutes" in s:
        backup(tc)
        tc.write_text(s.replace("token_minutes", "jwt_expire_minutes"), encoding="utf-8")
        changed.append("tests/test_core.py: token_minutes -> jwt_expire_minutes")
    else:
        print("[ok] tests/test_core.py me 'token_minutes' pehle se nahi hai")
else:
    print("[!] tests/test_core.py nahi mili")

# ---------- 2) app/main.py router order ----------
mp = ROOT / "app" / "main.py"
if mp.exists():
    s = mp.read_text(encoding="utf-8")
    m = re.search(r"for r in \(([^)]*)\):", s)
    if m:
        names = [x.strip() for x in m.group(1).replace("\n", " ").split(",") if x.strip()]
        if "notifications.router" in names and "products.router" in names:
            ni, pi = names.index("notifications.router"), names.index("products.router")
            if ni > pi:
                names.pop(ni)
                names.insert(pi, "notifications.router")
                new = "for r in (" + ", ".join(names) + "):"
                backup(mp)
                mp.write_text(s[:m.start()] + new + s[m.end():], encoding="utf-8")
                changed.append("app/main.py: notifications.router ab products.router se pehle hai")
            else:
                print("[ok] app/main.py me order pehle se sahi hai")
        else:
            print("[!] app/main.py me notifications.router / products.router nahi mile")
    else:
        print("[!] app/main.py me 'for r in (...)' wali line nahi mili - haath se dekho")
else:
    print("[!] app/main.py nahi mili")

# ---------- 3) notifications.py ----------
npth = ROOT / "app" / "routers" / "notifications.py"
if npth.exists():
    s = npth.read_text(encoding="utf-8")
    if '"unread"' in s and "read-all" in s:
        print("[ok] app/routers/notifications.py sahi lag rahi hai")
    else:
        print("[!] app/routers/notifications.py me naya code nahi hai - mera diya hua notifications.py paste karo")
else:
    print("[!] app/routers/notifications.py nahi mili")

# ---------- 4) frontend <-> backend ----------
def frontend_paths(html):
    out = set()
    for m in re.finditer(r"api\(\s*([`'\"])(/api/[^`'\"]*)\1", html):
        p = re.sub(r"\$\{[^}]*\}", "X", m.group(2)).split("?")[0]
        out.add(p)
    return out


def backend_ok(path, route_paths):
    if path.endswith('/'):  # frontend '/api/auth/'+mode jaisa jodta hai
        return any(rp.startswith(path) for rp in route_paths)
    for rp in route_paths:
        rx = "^" + re.sub(r"\{[^}]+\}", "[^/]+", rp) + "$"
        if re.match(rx, path):
            return True
    return False


def compare(html, route_paths):
    return sorted(p for p in frontend_paths(html) if not backend_ok(p, route_paths))


html_file = ROOT / "app" / "static" / "index.html"
if html_file.exists():
    html = html_file.read_text(encoding="utf-8")
    try:
        sys.path.insert(0, str(ROOT))
        from app.main import app  # noqa
        # Naye FastAPI me routers 'nested' hote hain, isliye app.routes se saare address nahi dikhte.
        # OpenAPI list me sab flat milte hain, wahi pehle use karo.
        routes = {getattr(r, "path", "") for r in app.routes}
        try:
            routes |= set(app.openapi().get("paths", {}).keys())
        except Exception as oe:
            print("[!] openapi list nahi ban payi:", repr(oe))
        missing = compare(html, routes)
        used = frontend_paths(html)
        print(f"\nFrontend {len(used)} alag /api/ address bulata hai.")
        if missing:
            print("BACKEND ME NAHI MILE (ye frontend se jude nahi hain):")
            for p in missing:
                print("   -", p)
        else:
            print("[ok] Frontend ke saare /api/ address backend me maujood hain.")
    except Exception as e:
        print("[!] app.main import nahi ho paaya, frontend-backend check chhoda:", repr(e))
else:
    print("[!] app/static/index.html nahi mili")

print()
if changed:
    print("Badlav kiye:")
    for c in changed:
        print("  *", c)
else:
    print("Koi file badalni nahi padi.")
print("\nAb chalao:  pytest tests -q")
