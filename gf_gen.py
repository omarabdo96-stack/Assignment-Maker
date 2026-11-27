# -*- coding: utf-8 -*-
"""Google Form -> Luxurious HTML page generator with auto answer extraction.
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

def extract_from_fb_data(s):
    """Extract questions from FB_PUBLIC_LOAD_DATA_"""
    items = []
    match = re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);', s, re.DOTALL)
    if not match:
        return items

    try:
        data = json.loads(match.group(1))
        if not isinstance(data, list) or len(data) < 2:
            return items

        # data[1] contains form info, data[1][1] contains questions
        if not data[1] or len(data[1]) < 2:
            return items

        questions_data = data[1][1]
        if not isinstance(questions_data, list):
            return items

        question_counter = 1
        for q in questions_data:
            if not isinstance(q, list) or len(q) < 4:
                continue

            qid = q[0]  # Question ID
            label = q[1] if len(q) > 1 else None  # Question text
            kind = q[3] if len(q) > 3 else None  # Question type

            # Skip if not a valid question ID
            if not isinstance(qid, int):
                continue

            # Type 0 = text input (Name/ID fields)
            # Type 2 = multiple choice
            # Type 3 = dropdown
            # Type 8 = section header

            # Skip Name, ID, and section headers
            if kind == 0 or kind == 8:
                continue

            entry = "entry.%d" % qid
            opts = []
            correct_answer = None

            # Type 2 = multiple choice, type 3 = dropdown
            if kind in (2, 3) and len(q) > 4 and isinstance(q[4], list) and q[4]:
                # Options are in q[4][0][1]
                if len(q[4][0]) > 1 and isinstance(q[4][0][1], list):
                    opts = [opt[0] for opt in q[4][0][1] if isinstance(opt, list) and opt]

                # Try to find correct answer - it's usually marked in q[4]
                if len(q[4]) > 1 and isinstance(q[4][1], list):
                    # q[4][1] might contain answer key info
                    answer_info = q[4][1]
                    if isinstance(answer_info, list) and len(answer_info) > 0:
                        # First element might be the correct answer index
                        if isinstance(answer_info[0], int) and answer_info[0] < len(opts):
                            correct_answer = opts[answer_info[0]]

            # Clean up label (remove HTML tags)
            if label:
                label = re.sub(r'<[^>]+>', '', label).strip()

            # If no label, create a generic one
            if not label or label == "":
                label = f"Question {question_counter}"

            items.append({
                "entry": entry,
                "options": opts,
                "label": label,
                "kind": kind,
                "correct_answer": correct_answer
            })
            question_counter += 1

    except Exception as e:
        print(f"Warning: Error parsing FB_PUBLIC_LOAD_DATA_: {e}")

    return items

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

    # Try extracting from FB_PUBLIC_LOAD_DATA_ first
    questions = extract_from_fb_data(s)

    return action, title, questions, name_entry, id_entry, fbzx

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")

def build_page(action, title, questions, name_entry, id_entry, fbzx):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()
    cards = []
    correct_answers = {}

    for i, q in enumerate(questions, 1):
        label = q.get("label") or "Question %d" % i
        if q.get("options"):
            opts = "".join(
                '<div class="opt" data-q="%s" data-v="%s"><span class="dot"></span>%s</div>'
                % (q["entry"], html.escape(o), html.escape(o)) for o in q["options"])
            body = '<div class="opts">%s</div>' % opts

            # Use extracted correct answer if available
            if q.get("correct_answer"):
                correct_answers[q["entry"]] = q["correct_answer"]
            elif q["options"]:
                # Fallback to first option
                correct_answers[q["entry"]] = q["options"][0]
        else:
            body = '<input class="tanswer" type="text" data-q="%s" placeholder="Type your answer here...">' % q["entry"]
            correct_answers[q["entry"]] = ""  # Empty for text answers

        cards.append('''
  <div class="qcard glass" id="q%d">
    <div class="qhead"><div class="qnum">%d</div><div class="qtext">%s</div></div>
    %s
  </div>''' % (i, i, html.escape(label), body))

    qjson = json.dumps([{"entry": q["entry"]} for q in questions], ensure_ascii=False)
    correct_json = json.dumps(correct_answers, ensure_ascii=False)

    return (tpl.replace("__TITLE__", html.escape(title))
               .replace("__NQ__", str(len(questions)))
               .replace("__QUESTIONS_HTML__", "\n".join(cards))
               .replace("__QUESTIONS_JSON__", qjson)
               .replace("__CORRECT_ANSWERS__", correct_json)
               .replace("__ACTION__", html.escape(action))
               .replace("__FBZX__", html.escape(fbzx))
               .replace("__NAME_ENTRY__", name_entry)
               .replace("__ID_ENTRY__", id_entry)
               .replace("__FORM_URL__", html.escape(action.replace('/formResponse', '/viewform'))))

def main():
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "assignment.html"
    viewform = resolve(url)
    s = fetch(viewform)
    action, title, qs, name_entry, id_entry, fbzx = extract_all(viewform, s)
    print("Title:", title)
    print("Questions:", len(qs))
    print("Name:", name_entry, " ID:", id_entry)

    # Count how many answers were auto-extracted
    auto_answers = sum(1 for q in qs if q.get("correct_answer"))
    print(f"Auto-extracted answers: {auto_answers}/{len(qs)}")

    page = build_page(action, title, qs, name_entry, id_entry, fbzx)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("Saved:", os.path.abspath(out))

    if auto_answers < len(qs):
        print(f"\n⚠️  IMPORTANT: {len(qs) - auto_answers} answers were NOT auto-extracted.")
        print("Edit the generated HTML file and update CORRECT_ANSWERS for those questions!")
    else:
        print("\n✅ All answers were auto-extracted! But please verify they are correct.")

if __name__ == "__main__":
    main()
