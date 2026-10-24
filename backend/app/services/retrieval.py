from pathlib import Path
import sys

_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from corpus.fixtures import DEMO_SOURCES
except ImportError:
    from fixtures import DEMO_SOURCES


def _score(src, query):
    q = query.lower()
    topics = [t.lower() for t in src.get("topics", [])]
    score = 0
    for t in topics:
        if t in q:
            score += 2
    for word in q.split():
        if word in src["text"].lower() or word in src["title"].lower():
            score += 1
    return score


def retrieve(query: str, k: int = 5):
    scored = sorted(DEMO_SOURCES, key=lambda s: _score(s, query), reverse=True)
    # relevance threshold
    out = []
    for s in scored:
        if _score(s, query) <= 0:
            continue
        out.append({
            "title": s["title"],
            "url": s["url"],
            "document_name": s["document_name"],
            "section": s["section"],
            "snippet": s["text"],
            "source_type": s["source_type"],
            "authority": s["authority"],
            "date": s["date"],
            "citation": s["citation"],
            "last_verified": s["last_verified"],
        })
        if len(out) >= k:
            break
    return out


KNOWN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
    "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "delhi", "jammu and kashmir", "ladakh", "chandigarh", "puducherry",
    "andaman and nicobar", "dadra and nagar haveli", "daman and diu", "lakshadweep",
]

CITIES_TO_STATE = {
    "kolkata": "west bengal",
    "calcutta": "west bengal",
    "mumbai": "maharashtra",
    "bombay": "maharashtra",
    "pune": "maharashtra",
    "nagpur": "maharashtra",
    "delhi": "delhi",
    "new delhi": "delhi",
    "bengaluru": "karnataka",
    "bangalore": "karnataka",
    "chennai": "tamil nadu",
    "madras": "tamil nadu",
    "hyderabad": "telangana",
    "ahmedabad": "gujarat",
    "surat": "gujarat",
    "jaipur": "rajasthan",
    "lucknow": "uttar pradesh",
    "kanpur": "uttar pradesh",
    "noida": "uttar pradesh",
    "gurugram": "haryana",
    "gurgaon": "haryana",
    "patna": "bihar",
    "bhopal": "madhya pradesh",
    "indore": "madhya pradesh",
    "chandigarh": "chandigarh",
    "kochi": "kerala",
    "cochin": "kerala",
    "thiruvananthapuram": "kerala",
    "bhubaneswar": "odisha",
    "ranchi": "jharkhand",
    "guwahati": "assam",
}


def extract_location(text: str | None) -> str | None:
    if not text:
        return None
    t = text.lower()
    for state in KNOWN_STATES:
        if state in t:
            return state.title()
    for city, state in CITIES_TO_STATE.items():
        if city in t:
            return f"{city.title()}, {state.title()}"
    return None


def needs_state(query: str, location: str | None = None) -> bool:
    if location and extract_location(location):
        return False
    q = query.lower()
    if not ("rent" in q or "landlord" in q or "tenant" in q or "security deposit" in q):
        return False
    if extract_location(q):
        return False
    return True
