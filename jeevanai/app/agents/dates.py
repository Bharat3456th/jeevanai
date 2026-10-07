import re
from datetime import date, datetime
from typing import Optional

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
PATTERNS = [
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})[a-z]*\.?,?\s+\d{{4}}\b",
    rf"\b(?:{MONTHS})[a-z]*\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b",
]
FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
           "%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y"]


def to_iso(raw: str) -> Optional[str]:
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", raw, flags=re.I)
    s = re.sub(r"sept", "Sep", s, flags=re.I).replace(",", "").replace(".", "")
    s = re.sub(r"\s+", " ", s).strip()
    for f in FORMATS:
        try:
            return datetime.strptime(s, f).date().isoformat()
        except ValueError:
            continue
    return None


def find_dates(text: str, today: Optional[date] = None):
    today = today or date.today()
    found, seen = [], set()
    for p in PATTERNS:
        for m in re.finditer(p, text, flags=re.I):
            raw = m.group(0)
            if raw in seen:
                continue
            seen.add(raw)
            iso = to_iso(raw)
            ctx = text[max(0, m.start() - 60): m.end() + 60].replace("\n", " ").strip()
            found.append({"date": raw, "iso": iso, "context": ctx,
                          "upcoming": (iso >= today.isoformat()) if iso else None})
    found.sort(key=lambda d: (d["iso"] is None, d["iso"] or ""))
    return found
