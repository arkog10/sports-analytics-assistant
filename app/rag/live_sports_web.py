from __future__ import annotations

import re
from datetime import datetime

_LIVE_SPORTS_FACTS = re.compile(
    r"""(?ix)
    \b( standings? | table | league\ table | ladder )\b
    | \b( who' ?s\ winning| who\ is\ winning| which\ team\ (is|'s)\ (winning|leading|first|on\ top) )\b
    | \b( who\ leads?| leading\ the| first\ place| top\ of\ the )\b
    | \b( how\ many\ points )\b
    | \b point(s)?\s+( gap| lead| clear| back| diff|differential|margin| behind| ahead| up| down)\b
    | \b( games\ back| half(\s*|-)game\ ( back|out)| pct|games\ ( played| left))\b
    | \b( current(ly)?\ ( season| table|standings?)|as\ of\ ( today| now)| this\ ( season| week))\b
    | \b( division( lead|race)?|conference( standings?)?|relegation|title\ race|wild\ card)\b
    | \b( playoff( race| picture|seeds?| bracket)?| home\ field )\b
    | \b( score( lines?)?| final\ score| box\ score| last\ night| yesterday|tonight' ?s? )\b
    | \b( golden\ boot| top\ scorer| home\ runs?\ leader| ppg| era\s+leader )\b
    """,
)


def looks_like_live_sports_numbers_question(query: str) -> bool:
    if not (query or "").strip():
        return False
    return bool(_LIVE_SPORTS_FACTS.search(query))


def extra_web_queries_for_factual_sports(query: str) -> list[str]:
    if not looks_like_live_sports_numbers_question(query):
        return []
    y = datetime.now().year
    u = " ".join(query.split())
    return [
        f"{u} standings table {y}",
        f"{u} first place lead points {y}",
    ]


def news_query_for_factual_sports(query: str) -> str | None:
    if not looks_like_live_sports_numbers_question(query):
        return None
    u = " ".join(query.split())
    return f"{u} latest standings table"
