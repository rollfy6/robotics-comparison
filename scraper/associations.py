import re
import sys
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

WIKIPEDIA_BASE = "https://en.wikipedia.org/w/api.php"
ABOUT_PATHS = ["/about", "/about-us", "/company", "/our-story", "/team", "/leadership", "/who-we-are"]

def _wiki_url_for(slug):
    name_map = {
        "pickle-robotics": "Pickle_Robotics",
        "locus-robotics": "Locus_Robotics",
        "geekplus": "Geek%2B",
        "hai-robotics": "Hai_Robotics",
        "autostore": "AutoStore",
        "amazon-robotics": "Amazon_Robotics",
        "symbotic": "Symbotic",
        "boston-dynamics": "Boston_Dynamics",
        "greyorange": "GreyOrange",
        "exotec": "Exotec",
        "zebra-fetch": "Fetch_Robotics",
        "kuka": "KUKA",
        "mir": "Mobile_Industrial_Robots",
        "6-river-systems": "6_River_Systems",
        "universal-robots": "Universal_Robots",
        "fanuc": "FANUC",
        "abb-robotics": "ABB_Robotics",
        "magazino": "Magazino",
        "mit": "Massachusetts_Institute_of_Technology",
        "teradyne": "Teradyne",
        "hyundai-motor-group": "Hyundai_Motor_Group",
        "amazon": "Amazon_(company)",
        "softbank-group": "SoftBank_Group",
        "sequoia-capital": "Sequoia_Capital",
        "midea-group": "Midea_Group",
        "ocado-group": "Ocado",
        "zebra-technologies": "Zebra_Technologies",
        "shopify": "Shopify",
        "kiva-systems": "Kiva_Systems",
        "intuitive-surgical": "Intuitive_Surgical",
        "medtronic": "Medtronic",
    }
    return name_map.get(slug, slug.replace("-", "_").title().replace("_And_", "_and_"))

def _fetch_wiki_links(slug):
    page = _wiki_url_for(slug)
    params = {
        "action": "query",
        "prop": "links",
        "titles": page,
        "pllimit": 200,
        "format": "json",
    }
    try:
        resp = requests.get(WIKIPEDIA_BASE, params=params, timeout=15,
                            headers={"User-Agent": "RoboticsComparison/1.0"})
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for pid, pdata in pages.items():
            if pid == "-1":
                continue
            return [link["title"] for link in pdata.get("links", [])]
    except Exception:
        return []
    return []

def _fetch_wiki_infobox(slug):
    page = _wiki_url_for(slug)
    params = {
        "action": "parse",
        "page": page,
        "prop": "text",
        "format": "json",
    }
    try:
        resp = requests.get(WIKIPEDIA_BASE, params=params, timeout=15,
                            headers={"User-Agent": "RoboticsComparison/1.0"})
        resp.raise_for_status()
        data = resp.json()
        html = data.get("parse", {}).get("text", {}).get("*", "")
        return html
    except Exception:
        return ""

def _fetch_url(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; RoboticsComparison/1.0)"
        })
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def _extract_wiki_person_fields(html, field_name):
    results = []
    pattern = rf'{field_name}[^<]*?>\s*([^<]+(?:\s*<[^>]+>[^<]*)*)'
    for m in re.finditer(pattern, html, re.IGNORECASE):
        content = m.group(1)
        clean = re.sub(r'<[^>]+>', '', content).strip()
        clean = re.sub(r'\s+', ' ', clean)
        if clean:
            parts = [p.strip() for p in clean.split(",")]
            for p in parts:
                p = p.strip()
                if p and len(p) > 3:
                    results.append(p)
    return results

def discover_associations(slug):
    relevant_keywords = {
        "acquired", "subsidiary", "parent", "spin-off", "founded",
        "investor", "invested", "backed", "partner", "customer",
        "division", "owned", "owner",
    }
    links = _fetch_wiki_links(slug)
    html = _fetch_wiki_infobox(slug)

    suggested = []

    for link in links:
        lower = link.lower()
        for kw in relevant_keywords:
            if kw in lower:
                suggested.append({"entity": link, "matched_keyword": kw})
                break

    if html:
        for pattern in [
            r'Parent\s*org(?:anization)?[^<]*?>\s*([^<]+)',
            r'Owner[^<]*?>\s*([^<]+)',
            r'Founder[^<]*?>\s*([^<]+)',
            r'Subsidiaries?[^<]*?>\s*([^<]+)',
            r'spun\s*off\s*from[^<]*?>\s*([^<]+)',
        ]:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for m in matches:
                clean = re.sub(r'<[^>]+>', '', m).strip()
                if clean:
                    suggested.append({"entity": clean, "matched_keyword": "infobox"})

    seen_entities = set()
    deduped = []
    for s in suggested:
        e = s["entity"].lower().strip()
        if e and e not in seen_entities:
            seen_entities.add(e)
            deduped.append(s)

    return deduped[:20]

def discover_people_from_wiki(slug):
    html = _fetch_wiki_infobox(slug)
    if not html:
        return []

    people = []
    for field in ["Founder", "Founders", "Key people", r"Key\s*personnel", "CEO", "Chairman", "President", "Head"]:
        found = _extract_wiki_person_fields(html, field)
        for name in found:
            if name not in people:
                people.append(name)

    return people[:10]

def scrape_about_page(company_website):
    if not company_website:
        return {"people": [], "associations": [], "academic_ties": []}

    parsed = urlparse(company_website)
    base = f"{parsed.scheme}://{parsed.netloc}"

    html = None
    used_path = None
    for path in ABOUT_PATHS:
        url = urljoin(base, path)
        h = _fetch_url(url, timeout=6)
        if h:
            html = h
            used_path = path
            break

    if not html:
        return {"people": [], "associations": [], "academic_ties": []}

    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    results = {"people": [], "associations": [], "academic_ties": []}

    founder_patterns = re.findall(r'(?:Founded|Co-founded|Established)\s*(?:by|as|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
    for m in founder_patterns:
        m = m.strip()
        if m and len(m.split()) <= 5:
            results["people"].append({"name": m, "source": "about_page", "role": "founder"})

    title_patterns = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}),\s*(CEO|CTO|CFO|President|Founder|Chairman|COO|VP\s+of|Director\s+of|Head\s+of)', text)
    title_patterns2 = re.findall(r'(CEO|CTO|CFO|President|Founder|Chairman),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', text)
    for m in title_patterns:
        name, role = m
        if name not in [p["name"] for p in results["people"]]:
            results["people"].append({"name": name.strip(), "source": "about_page", "role": role.strip()})
    for m in title_patterns2:
        role, name = m
        if name not in [p["name"] for p in results["people"]]:
            results["people"].append({"name": name.strip(), "source": "about_page", "role": role.strip()})

    for uni in ["MIT", "Stanford", "Harvard", "Cambridge", "Oxford", "ETH Zurich", "TUM", "Carnegie Mellon", "Georgia Tech", "UC Berkeley", "Caltech"]:
        if uni in text:
            results["academic_ties"].append({"institution": uni, "matched": True})

    acq = re.findall(r'(?:acquired|purchased|bought)\s+(?:by|in)\s+(\d{4})', text, re.IGNORECASE)
    results["associations"] = acq

    return results

def slugify_name(name):
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = s.strip("-")
    return s

def slugify_wiki_title(title):
    s = title.lower().strip()
    s = re.sub(r'[–—]', '-', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'[\(\)]', '', s)
    s = s.strip('-')
    return s

def auto_discover_everything(conn, progress_callback=None):
    from database.db import get_all_companies, get_person_by_slug, get_company_by_slug, _link

    companies = [c for c in get_all_companies(conn) if c.get("website") or True]
    total = len(companies)
    discovered_people = 0
    discovered_assocs = 0

    for i, company in enumerate(companies):
        slug = company["slug"]

        if progress_callback:
            progress_callback(i + 1, total, slug)

        # Skip educational, investor, customer types (their websites aren't about pages)
        ctype = company.get("company_type", "")
        if ctype in ("educational", "investor", "customer"):
            continue

        # 1. Wikipedia: discover people
        wiki_people = discover_people_from_wiki(slug)
        for person_name in wiki_people:
            person_slug = slugify_name(person_name)
            existing = get_person_by_slug(conn, person_slug)
            if existing:
                continue

            conn.execute("""INSERT OR IGNORE INTO people (name, slug, title, bio)
                            VALUES (?, ?, ?, ?)""",
                         (person_name, person_slug,
                          f"Key person at {company['name']}",
                          f"Discovered from Wikipedia for {company['name']}"))
            person_row = conn.execute("SELECT id FROM people WHERE slug = ?", (person_slug,)).fetchone()
            if person_row:
                company_row = conn.execute("SELECT id FROM companies WHERE slug = ?", (slug,)).fetchone()
                if company_row:
                    conn.execute("""INSERT OR IGNORE INTO person_roles
                                    (person_id, entity_id, entity_type, role, notes)
                                    VALUES (?, ?, 'company', 'key_person', ?)""",
                                 (person_row[0], company_row[0],
                                  f"Auto-discovered from Wikipedia for {company['name']}"))
                    discovered_people += 1

        # 2. About page: scrape for more people and associations
        website = company.get("website", "")
        if website and ctype not in ("customer",):
            about_data = scrape_about_page(website)
            for pd in about_data["people"]:
                person_slug = slugify_name(pd["name"])
                existing = get_person_by_slug(conn, person_slug)
                if existing:
                    continue

                conn.execute("""INSERT OR IGNORE INTO people (name, slug, title, bio)
                                VALUES (?, ?, ?, ?)""",
                             (pd["name"], person_slug, pd.get("role", ""),
                              f"Discovered from {company['name']} website"))
                person_row = conn.execute("SELECT id FROM people WHERE slug = ?", (person_slug,)).fetchone()
                if person_row:
                    company_row = conn.execute("SELECT id FROM companies WHERE slug = ?", (slug,)).fetchone()
                    if company_row:
                        conn.execute("""INSERT OR IGNORE INTO person_roles
                                        (person_id, entity_id, entity_type, role, notes)
                                        VALUES (?, ?, 'company', ?, ?)""",
                                     (person_row[0], company_row[0], pd.get("role", "key_person"),
                                      f"Auto-discovered from {company['name']} about page"))
                        discovered_people += 1

            for tie in about_data["academic_ties"]:
                inst_slug = slugify_name(tie["institution"])
                inst_row = conn.execute("SELECT id FROM companies WHERE slug = ?", (inst_slug,)).fetchone()
                if inst_row:
                    comp_row = conn.execute("SELECT id FROM companies WHERE slug = ?", (slug,)).fetchone()
                    if comp_row:
                        conn.execute("""INSERT OR IGNORE INTO company_associations
                                        (company_id, associated_company_id, association_type, notes)
                                        VALUES (?, ?, 'academic_origin', ?)""",
                                     (comp_row[0], inst_row[0],
                                      f"Auto-discovered: mentions {tie['institution']}"))
                        discovered_assocs += 1

        # Commit periodically
        if (i + 1) % 10 == 0:
            conn.commit()

    conn.commit()
    return {"people": discovered_people, "associations": discovered_assocs}

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "discover_associations"
    slug = sys.argv[2] if len(sys.argv) > 2 else "boston-dynamics"

    if cmd == "discover_associations":
        result = discover_associations(slug)
        for r in result:
            print(f"{r['matched_keyword']:20s}  {r['entity']}")
    elif cmd == "discover_people":
        result = discover_people_from_wiki(slug)
        for r in result:
            print(r)
    elif cmd == "scrape_about":
        result = scrape_about_page(sys.argv[2] if len(sys.argv) > 2 else "https://www.picklerobot.com")
        import json
        print(json.dumps(result, indent=2))
