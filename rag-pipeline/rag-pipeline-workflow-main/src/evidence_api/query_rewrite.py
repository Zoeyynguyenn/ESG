"""Deterministic query rewrite — anchor generic KO company references to registry display name."""



from __future__ import annotations



import re



# Possessive forms first (longer match), then bare references.

_GENERIC_POSSESSIVE: tuple[tuple[re.Pattern[str], str], ...] = (

    (re.compile(r"해당\s*기업의"), "{display}의"),

    (re.compile(r"해당\s*회사의"), "{display}의"),

    (re.compile(r"이\s*기업의"), "{display}의"),

    (re.compile(r"이\s*회사의"), "{display}의"),

)

_GENERIC_BARE: tuple[tuple[re.Pattern[str], str], ...] = (

    (re.compile(r"해당\s*기업"), "{display}"),

    (re.compile(r"해당\s*회사"), "{display}"),

    (re.compile(r"이\s*기업"), "{display}"),

    (re.compile(r"이\s*회사"), "{display}"),

    (re.compile(r"this\s+company", re.IGNORECASE), "{display}"),

    (re.compile(r"the\s+company", re.IGNORECASE), "{display}"),

)

_METRIC_HINT = re.compile(
    r"구성원|직원|임직원|남성|여성|비율|총직원|인원|근로자|사람\s*수|"
    r"종업원|인력|고용",
)





def company_display_name(company_id: str, registry_entry: dict) -> str:

    explicit = (registry_entry.get("display_name") or "").strip()

    if explicit:

        return explicit

    package = (registry_entry.get("package") or "").strip()

    marker = "_dataset_package"

    if marker in package:

        return package.split(marker, 1)[0]

    return company_id





def _already_names_company(query: str, display: str, company_id: str) -> bool:

    q = query.lower()

    if display and display in query:

        return True

    if company_id and company_id.lower() in q:

        return True

    return False





def _apply_generic_replacement(query: str, display: str) -> str:

    for pattern, template in _GENERIC_POSSESSIVE + _GENERIC_BARE:

        if pattern.search(query):

            repl = template.format(display=display)

            return pattern.sub(repl, query, count=1)

    return query





def rewrite_query_for_company(query: str, company_id: str, registry_entry: dict) -> str:

    """Replace generic company references with display name (e.g. 무신사 / 무신사의)."""

    raw = (query or "").strip()

    if not raw:

        return raw

    display = company_display_name(company_id, registry_entry)

    if _already_names_company(raw, display, company_id):

        return raw



    rewritten = _apply_generic_replacement(raw, display)

    rewritten = re.sub(r"\s+", " ", rewritten).strip()



    # Fallback: metric question without any company anchor.

    if display not in rewritten and _METRIC_HINT.search(rewritten):

        rewritten = f"{display} {rewritten}"



    return rewritten


