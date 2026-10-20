#!/usr/bin/env python3
"""Kur'an ve Hayat serisinin sıradaki Reels videosunu paylaşır.

Hangi bölümün sırada olduğunu hesaptaki son paylaşımların açıklamasındaki
"Kur'an ve Hayat · N/10" etiketinden bulur; böylece aynı video iki kez paylaşılmaz.
Token ortamın ağ proxy'si tarafından ekleniyor.

Kullanım:
  python3 reels/paylas.py --durum   # sadece hangi bölümlerin paylaşıldığını gösterir
  python3 reels/paylas.py           # sıradaki bölümü paylaşır
"""
import json, os, re, subprocess, sys, time

API = "https://graph.instagram.com/v23.0"
IG = "17841422928756043"
BRANCH = "claude/project-thread-bicivy"
RAW = f"https://raw.githubusercontent.com/furkqnzengin/instagram-gorseller/{BRANCH}/reels/kuran-ve-hayat/"
PLAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kuran-ve-hayat", "plan.json")


def curl(*args):
    out = subprocess.run(["curl", "-sS", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def posted_numbers():
    d = curl(f"{API}/{IG}/media?fields=caption&limit=50")
    if "error" in d:
        sys.exit(f"HATA medya listesi: {d}")
    nums = set()
    for m in d.get("data", []):
        for n in re.findall(r"Kur'an ve Hayat · (\d+)/10", m.get("caption") or ""):
            nums.add(int(n))
    return nums


def main():
    plan = json.load(open(PLAN, encoding="utf-8"))
    done = posted_numbers()
    todo = [p for p in plan if p["n"] not in done]
    if "--durum" in sys.argv:
        print(f"Paylaşılan: {sorted(done)}  Sıradaki: {todo[0]['n'] if todo else '-'}")
        return
    if not todo:
        print("BITTI: 10/10 paylaşılmış.")
        return
    p = todo[0]
    c = curl("-X", "POST", f"{API}/{IG}/media",
             "--data-urlencode", "media_type=REELS",
             "--data-urlencode", f"video_url={RAW}{p['file']}",
             "--data-urlencode", f"caption={p['caption']}",
             "--data-urlencode", "share_to_feed=true")
    if "id" not in c:
        sys.exit(f"HATA container: {c}")
    s = {}
    for _ in range(40):
        s = curl(f"{API}/{c['id']}?fields=status_code,status")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            sys.exit(f"HATA işleme: {s}")
        time.sleep(15)
    else:
        sys.exit(f"HATA zaman aşımı: {s}")
    r = curl("-X", "POST", f"{API}/{IG}/media_publish", "--data-urlencode", f"creation_id={c['id']}")
    if "id" not in r:
        sys.exit(f"HATA publish: {r}")
    link = curl(f"{API}/{r['id']}?fields=permalink").get("permalink")
    print(f"PAYLASILDI {p['n']}/10 {p['file']} media_id={r['id']} {link}")


if __name__ == "__main__":
    main()
