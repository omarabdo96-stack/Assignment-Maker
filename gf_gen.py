# -*- coding: utf-8 -*-
"""Google Form -> Luxurious HTML page generator.
Usage: python3 gf_gen.py <form_url> [output.html]
Requires the questions page to be reachable; walks multi-page forms via POST round-trip.
"""
import re, sys, json, html, urllib.request, urllib.parse, os

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

def resolve(url):
    if "docs.google.com" in url:
        m = re.search(r"/forms/d/e/([A-Za-z0-9_-]+)", url)
        return "https://docs.google.com/forms/d/e/%s/viewform" % m.group(1)
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).geturl()

def deep_extract_page_items(s):
    items = []
    for m in re.finditer(r'data-params="([^"]*)"', s):
        raw = html.unescape(m.group(1))
        if not raw.startswith("%.@."):
            continue
        try:
            data = json.loads(raw[4:])
        except Exception:
            continue
        try:
            if not (isinstance(data, list) and len(data) > 4 and isinstance(data[4], list) and data[4]):
                continue
            inner = data[4][0]
            eid = inner[0]
            if not isinstance(eid, int):
                continue
            kind = data[3]
            entry = "entry.%d" % eid
            opts = []
            if kind in (2, 3):
                opts = [o[0] for o in inner[1]]
            pos = m.start()
            imgs_before = re.findall(r'<img src="(https://docs\.google\.com/forms-images-rt/[^"]+)"', s[:pos])
            imgs_after = re.findall(r'<img src="(https://docs\.google\.com/forms-images-rt/[^"]+)"', s[pos:pos+6000])
            img = imgs_before[-1] if imgs_before else (imgs_after[0] if imgs_after else None)
            label = data[1] if isinstance(data[1], str) else None
            items.append({"entry": entry, "options": opts, "img": img, "label": label, "kind": kind})
        except Exception:
            continue
    seen, out = set(), []
    for it in items:
        if it["entry"] in seen:
            continue
        seen.add(it["entry"])
        out.append(it)
    return out

def extract_all(viewform_url, s):
    action_m = re.search(r'action="(https://docs.google.com/forms/d/e/[^"]+/formResponse)"', s)
    if not action_m:
        raise SystemExit("formResponse action not found (form may require sign-in)")
    action = action_m.group(1)
    t = re.search(r"<title>([^<]*)</title>", s)
    title = html.unescape(t.group(1)).strip() if t else "Assignment"
    m = re.search(r'\[(\d+),&quot;Name&quot;', s) or re.search(r'\[(\d+),"Name"', s)
    name_entry = "entry." + (m.group(1) if m else "0")
    m = re.search(r'\[(\d+),&quot;ID&quot;', s) or re.search(r'\[(\d+),"ID"', s)
    id_entry = "entry." + (m.group(1) if m else "0")
    fbzx_m = re.search(r'name="fbzx" value="([^"]*)"', s)
    fbzx = fbzx_m.group(1) if fbzx_m else ""

    questions, seen = [], set()
    page_html, history = s, ["0"]
    for page in range(15):
        for q in deep_extract_page_items(page_html):
            if q["entry"] not in seen and q["entry"] not in (name_entry, id_entry):
                seen.add(q["entry"]); questions.append(q)
        body = urllib.parse.urlencode({
            "fvv": "1", "pageHistory": ",".join(history),
            "fbzx": fbzx, "submissionTimestamp": "-1", "draftResponse": "[]"}).encode()
        try:
            nxt = fetch(action, body)
        except Exception:
            break
        more = deep_extract_page_items(nxt)
        more_new = [q for q in more if q["entry"] not in seen]
        if not more_new:
            break
        history.append(str(page + 1))
        page_html = nxt
    return action, title, questions, name_entry, id_entry, fbzx

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")

def build_page(action, title, questions, name_entry, id_entry, fbzx):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()
    cards = []
    for i, q in enumerate(questions, 1):
        img_html = ('<img class="qimg" loading="lazy" src="%s" alt="Question %d">' % (html.escape(q["img"]), i)) if q.get("img") else ""
        label = q.get("label") or "Question %d" % i
        # Put image INSIDE qtext with the label
        qtext_content = html.escape(label) + img_html
        if q.get("options"):
            # Reverse options for RTL to show a,b,c,d left-to-right
            reversed_opts = list(reversed(q["options"]))
            opts = "".join(
                '<div class="opt" data-q="%s" data-v="%s"><span class="dot"></span>%s</div>'
                % (q["entry"], html.escape(o), html.escape(o)) for o in reversed_opts)
            body = '<div class="opts">%s</div>' % opts
        else:
            body = '<input class="tanswer" type="text" data-q="%s" placeholder="اكتب إجابتك هنا...">' % q["entry"]
        cards.append('''
  <div class="qcard glass" id="q%d">
    <div class="qhead"><div class="qnum">%d</div><div class="qtext">%s</div></div>
    %s
  </div>''' % (i, i, qtext_content, body))
    qjson = json.dumps([{"entry": q["entry"]} for q in questions], ensure_ascii=False)
    return (tpl.replace("__TITLE__", html.escape(title))
               .replace("__NQ__", str(len(questions)))
               .replace("__QUESTIONS_HTML__", "\n".join(cards))
               .replace("__QUESTIONS_JSON__", qjson)
               .replace("__ACTION__", html.escape(action))
               .replace("__FBZX__", html.escape(fbzx))
               .replace("__NAME_ENTRY__", name_entry)
               .replace("__ID_ENTRY__", id_entry))

def main():
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "assignment.html"
    viewform = resolve(url)
    s = fetch(viewform)
    action, title, qs, name_entry, id_entry, fbzx = extract_all(viewform, s)
    print("Title:", title)
    print("Questions:", len(qs))
    print("Name:", name_entry, " ID:", id_entry)
    page = build_page(action, title, qs, name_entry, id_entry, fbzx)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("Saved:", os.path.abspath(out))

if __name__ == "__main__":
    main()
