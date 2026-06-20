import re
import sys
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time

USER_AGENT = "Mozilla/5.0 (compatible; RoboticsComparison/1.0)"

# Tiers of URL paths to discover case studies
DISCOVERY_PATHS_TIER1 = [
    "/case-studies", "/case-studies/",
    "/resources/case-studies", "/resources/case-studies/",
    "/customers", "/customer-stories", "/success-stories",
    "/stories",
]
DISCOVERY_PATHS_TIER2 = [
    "/news", "/insights", "/blog", "/operations",
    "/resources", "/about/news", "/press",
]


def _fetch(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _resolve_url(src, base_url):
    if not src:
        return None
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{src}"
    if not src.startswith("http"):
        return urljoin(base_url, src)
    return src


def _is_case_study_link(a_tag, company_name=""):
    href = (a_tag.get("href") or "").lower()
    text = (a_tag.get_text() or "").lower()
    combined = href + " " + text

    exclude_keywords = ["privacy", "terms", "login", "sign in", "sign up",
                        "register", "contact", "careers", "jobs", "subscribe",
                        "cookie", "password", "legal", "press release"]

    for kw in exclude_keywords:
        if kw in combined:
            return False

    include_keywords = ["case study", "case-study", "customer story",
                        "customer-stories", "success story", "success-story",
                        "how we", "how ", "customer spotlight"]

    for kw in include_keywords:
        if kw in combined:
            return True

    if company_name and company_name.lower() in combined:
        for kw in ["case", "study", "story", "customer", "success", "implementation"]:
            if kw in combined:
                return True

    return False


def _score_candidate_url(href, text, company_name=""):
    score = 0
    combined = (href + " " + text).lower()

    direct_score = {"case-studies": 15, "case_study": 15, "case-study": 15,
                    "case study": 15, "customer-stories": 12, "success-story": 12,
                    "success_story": 12, "customer story": 10, "success story": 10,
                    "how": 5, "implementation": 8, "deployment": 8}

    for kw, s in direct_score.items():
        if kw in combined:
            score += s

    if company_name and company_name.lower() in combined:
        score += 5

    has_num = bool(re.search(r'-\d+', href))
    if has_num:
        score += 2

    path_len = len(urlparse(href).path.rstrip('/').split('/'))
    if 2 <= path_len <= 4:
        score += 3

    return score


def discover_case_study_urls(conn, company):
    """Discover case study URLs for a given company."""
    company_id = company["id"]
    name = company["name"]
    website = company.get("website", "")

    if not website:
        return []

    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"
    existing = get_existing_cs_urls(conn, company_id)
    existing_set = set(existing)

    found = {}

    def scan_page(page_url, max_links=40):
        html = _fetch(page_url, timeout=8)
        if not html:
            return
        soup = BeautifulSoup(html, "lxml")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            text = (a_tag.get_text() or "").strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            full_url = _resolve_url(href, page_url)
            if not full_url:
                continue
            if full_url in found or full_url in existing_set:
                continue
            if parsed.netloc not in full_url:
                continue
            if _is_case_study_link(a_tag, name):
                score = _score_candidate_url(href, text, name)
                found[full_url] = {"url": full_url, "title": text, "score": score, "source_page": page_url}

    # Tier 1: direct case study paths
    for path in DISCOVERY_PATHS_TIER1:
        scan_page(base + path)

    # If fewer than 3 candidates, try Tier 2
    if len(found) < 3:
        for path in DISCOVERY_PATHS_TIER2:
            scan_page(base + path)

    # If still very few, try the homepage itself
    if len(found) < 2:
        scan_page(base, max_links=60)

    results = sorted(found.values(), key=lambda x: x["score"], reverse=True)
    return results[:20]


def parse_case_study_page(url, html):
    """Parse a case study page and extract structured fields."""
    result = {
        "title": "",
        "customer": "",
        "industry": "",
        "challenge": "",
        "solution": "",
        "results": "",
        "metrics": "",
        "featured_image": "",
        "published_date": "",
        "url": url,
    }

    if not html:
        return result

    soup = BeautifulSoup(html, "lxml")

    # 1. JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict):
                result["title"] = result["title"] or data.get("headline", "") or data.get("name", "")
                result["customer"] = result["customer"] or data.get("publisher", {}).get("name", "")
                result["published_date"] = result["published_date"] or data.get("datePublished", "")
                img = data.get("image", "")
                if isinstance(img, dict):
                    img = img.get("url", "")
                if isinstance(img, list):
                    img = img[0] if img else ""
                result["featured_image"] = result["featured_image"] or img
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        result["title"] = result["title"] or item.get("headline", "") or item.get("name", "")
                        result["customer"] = result["customer"] or item.get("publisher", {}).get("name", "")
                        result["published_date"] = result["published_date"] or item.get("datePublished", "")
                        img = item.get("image", "")
                        if isinstance(img, dict):
                            img = img.get("url", "")
                        if isinstance(img, list):
                            img = img[0] if img else ""
                        result["featured_image"] = result["featured_image"] or img
        except Exception:
            pass

    # 2. Open Graph / Meta tags
    if not result["title"]:
        for meta in soup.find_all("meta", property="og:title"):
            result["title"] = meta.get("content", "")
            break
    if not result["featured_image"]:
        for meta in soup.find_all("meta", property="og:image"):
            result["featured_image"] = meta.get("content", "")
            break
    if not result["published_date"]:
        for meta in soup.find_all("meta", property="article:published_time"):
            result["published_date"] = meta.get("content", "")
            break
    if not result["customer"]:
        for meta in soup.find_all("meta", attrs={"name": "description"}):
            desc = meta.get("content", "")
            m = re.search(r'(?:for|at)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\s+(?:achiev|reduce|improve|increase|deploy|use|implement|save))', desc)
            if m:
                result["customer"] = m.group(1).strip()
            break

    # Also use <title> as fallback for title
    if not result["title"]:
        t = soup.find("title")
        if t:
            result["title"] = t.get_text(strip=True)

    # 3. HTML heading sections
    headings = []
    for tag in ["h1", "h2", "h3", "h4"]:
        for el in soup.find_all(tag):
            text = el.get_text(strip=True)
            if text:
                section = {"heading": text, "content": []}
                sibling = el.find_next_sibling()
                while sibling and sibling.name not in ["h1", "h2", "h3", "h4"]:
                    if sibling.name in ["p", "div", "span", "li", "section"]:
                        section["content"].append(sibling.get_text(strip=True))
                    sibling = sibling.find_next_sibling()
                headings.append(section)

    challenge_kw = ["challenge", "the challenge", "problem", "background", "situation", "opportunity", "the problem"]
    solution_kw = ["solution", "approach", "implementation", "how we helped", "our approach", "the solution"]
    results_kw = ["results", "outcome", "impact", "benefits", "key results", "business impact", "the results"]

    for section in headings:
        hl = section["heading"].lower()
        content = " ".join(section["content"])

        if any(kw in hl for kw in challenge_kw):
            result["challenge"] = (result["challenge"] + " " + content).strip()
        if any(kw in hl for kw in solution_kw):
            result["solution"] = (result["solution"] + " " + content).strip()
        if any(kw in hl for kw in results_kw):
            result["results"] = (result["results"] + " " + content).strip()

    # 4. Full-text metric extraction
    full_text = soup.get_text(separator=" ", strip=True)
    metric_sentences = []
    for sentence in re.split(r'(?<=[.!?])\s+', full_text):
        if re.search(r'\b\d+[%xX×+]\d*|\b\d+[%]\s+(?:faster|improvement|reduction|increase|decrease)', sentence):
            metric_sentences.append(sentence)
    if metric_sentences:
        result["metrics"] = " | ".join(metric_sentences[:5])

    # 5. Try to extract customer from content
    if not result["customer"]:
        for section in headings:
            content = " ".join(section["content"])
            m = re.search(r'(?:at|for|partnered with)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\s+(?:to|,\s+(?:an?|the|a)|\.|!))', content)
            if m:
                result["customer"] = m.group(1).strip()
                break

    # 6. Featured image fallback
    if not result["featured_image"]:
        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or ""
            if not src or src.startswith("data:"):
                continue
            resolved = _resolve_url(src, url)
            if not resolved:
                continue
            w = img.get("width") or 0
            h = img.get("height") or 0
            try:
                w = int(w)
                h = int(h)
            except (ValueError, TypeError):
                w, h = 0, 0
            alt = (img.get("alt") or "").lower()
            if w > 200 and h > 200 or "hero" in alt or "featured" in alt or "banner" in alt:
                result["featured_image"] = resolved
                break

    return result


def scrape_company_case_studies(conn, company):
    """Discover and parse case studies for a single company."""
    company_id = company["id"]
    results = []

    candidates = discover_case_study_urls(conn, company)

    existing_urls = set(get_existing_cs_urls(conn, company_id))

    for cand in candidates:
        url = cand["url"]
        if url in existing_urls:
            results.append({"url": url, "title": cand["title"], "status": "exists"})
            continue

        html = _fetch(url, timeout=10)
        if not html:
            results.append({"url": url, "title": cand["title"], "status": "unreachable"})
            continue

        parsed = parse_case_study_page(url, html)
        parsed["status"] = "parsed"
        results.append(parsed)

        time.sleep(0.3)

    return results


def scrape_all_case_studies(conn):
    """Scrape case studies for all companies with websites."""
    companies = get_companies_for_scrape(conn)
    total = len(companies)
    all_results = []

    for i, company in enumerate(companies):
        name = company["name"]
        company_results = scrape_company_case_studies(conn, company)
        parsed_count = sum(1 for r in company_results if r.get("status") == "parsed")
        exists_count = sum(1 for r in company_results if r.get("status") == "exists")
        all_results.append((name, parsed_count, exists_count, len(company_results)))

    return all_results


def import_case_study(conn, company_id, parsed):
    """Import a parsed case study into the database."""
    if not parsed.get("title") or parsed.get("status") != "parsed":
        return None

    existing = get_case_study_by_url(conn, parsed["url"])
    if existing:
        return existing["id"]

    data = {
        "company_id": company_id,
        "product_id": None,
        "title": (parsed.get("title") or "Untitled")[:500],
        "customer": (parsed.get("customer") or "")[:200],
        "industry": (parsed.get("industry") or "")[:100],
        "challenge": parsed.get("challenge") or "",
        "solution": parsed.get("solution") or "",
        "results": parsed.get("results") or "",
        "metrics": parsed.get("metrics") or "",
        "url": parsed.get("url") or "",
        "featured_image": parsed.get("featured_image") or "",
        "published_date": parsed.get("published_date") or "",
    }

    return upsert_case_study(conn, data)


# These functions are imported from db.py at runtime
def get_existing_cs_urls(conn, company_id=None):
    """Get already-stored case study URLs."""
    from database.db import get_existing_cs_urls as _impl
    return _impl(conn, company_id)


def get_companies_for_scrape(conn):
    """Get companies suitable for case study scraping."""
    from database.db import get_companies_for_scrape as _impl
    return _impl(conn)


def get_case_study_by_url(conn, url):
    """Check if case study URL already exists."""
    from database.db import get_case_study_by_url as _impl
    return _impl(conn, url)


def upsert_case_study(conn, data):
    """Insert or update a case study."""
    from database.db import upsert_case_study as _impl
    return _impl(conn, data)
