from __future__ import annotations
from dateutil import parser as dtparser


@dataclass
class ParsedCandidate:
army_number: str
name: str
category: str
paper_title: str


@dataclass
class ParsedAnswer:
question_id: int
question_text: str
answer: str | None
submitted_at: datetime | None


CANDIDATE_PATTERNS = {
"army_number": re.compile(r"Army\s*Number\s*:\s*(.+)", re.I),
"name": re.compile(r"Candidate\s*Name\s*:\s*(.+)", re.I),
"category": re.compile(r"Category\s*:\s*(.+)", re.I),
"paper_title": re.compile(r"Paper\s*Title\s*:\s*(.+)", re.I),
}


# Question blocks: starts with Q<ID>) ... then optional Answer:, Submitted:
QBLOCK_RE = re.compile(
r"Q\s*(?P<qid>\d+)\)\s*(?P<qtext>.*?)\n(?:Answer\s*:\s*(?P<ans>.*?))?\n(?:Submitted\s*:\s*(?P<submitted>.*?))?(?:\n\s*\n|\Z)",
re.DOTALL | re.IGNORECASE,
)




def extract_text_from_pdf(file_like) -> str:
"""Extract raw text from all pages using pdfplumber."""
import pdfplumber
text_parts = []
with pdfplumber.open(file_like) as pdf:
for page in pdf.pages:
text_parts.append(page.extract_text() or "")
return "\n".join(text_parts)




def parse_candidate(text: str) -> ParsedCandidate:
data = {}
for key, pattern in CANDIDATE_PATTERNS.items():
m = pattern.search(text)
data[key] = m.group(1).strip() if m else ""
return ParsedCandidate(
army_number=data.get("army_number", "").strip(),
name=data.get("name", "").strip(),
category=data.get("category", "").strip(),
paper_title=data.get("paper_title", "").strip(),
)




def parse_answers(text: str) -> list[ParsedAnswer]:
answers: list[ParsedAnswer] = []
for m in QBLOCK_RE.finditer(text):
qid = int(m.group("qid"))
qtext = (m.group("qtext") or "").strip()
ans = (m.group("ans") or "").strip()
submitted_raw = (m.group("submitted") or "").strip()
try:
submitted_dt = dtparser.parse(submitted_raw) if submitted_raw else None
except Exception:
submitted_dt = None
answers.append(ParsedAnswer(qid, qtext, ans, submitted_dt))
return answers




def parse_pdf(file_like):
"""Return (ParsedCandidate, list[ParsedAnswer])."""
raw = extract_text_from_pdf(file_like)
cand = parse_candidate(raw)
answers = parse_answers(raw)
return cand, answers