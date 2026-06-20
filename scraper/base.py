import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time

SPEC_PARSERS = {}

def register_parser(domain):
    def decorator(func):
        SPEC_PARSERS[domain] = func
        return func
    return decorator

def scrape_product_specs(url):
    domain = urlparse(url).netloc.lower()
    for key, parser in SPEC_PARSERS.items():
        if key in domain:
            try:
                resp = requests.get(url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; RoboticsComparison/1.0)"
                })
                resp.raise_for_status()
                return parser(resp.text, url)
            except Exception as e:
                return {"error": str(e)}
    return {"error": f"No parser registered for domain: {domain}"}

def extract_numeric(text):
    match = re.search(r'[\d,.]+', str(text))
    if match:
        return match.group(0).replace(",", "")
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

def _fetch(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; RoboticsComparison/1.0)"
        })
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def find_product_image(url):
    """Original single-strategy finder — kept for backward compatibility."""
    result = find_product_image_multi(url)
    if result:
        return result["url"]
    return None

def find_product_image_multi(url, product_name="", company_name="", company_url=""):
    """Multi-strategy image finder. Returns dict with url, source, and strategy used.
    Strategies (in order): og:image, twitter:image, best img tag, company site og:image.
    """
    strategies = []

    def _parse_page(page_url, timeout=8):
        html = _fetch(page_url, timeout=timeout)
        if not html:
            return None
        soup = BeautifulSoup(html, "lxml")
        # og:image
        for meta in soup.find_all("meta", property="og:image"):
            img = meta.get("content")
            if img:
                return {"url": img, "source": page_url, "strategy": "og:image"}
        # twitter:image
        for meta in soup.find_all("meta", attrs={"name": "twitter:image"}):
            img = meta.get("content")
            if img:
                return {"url": img, "source": page_url, "strategy": "twitter:image"}
        # best img tag
        best_img = None
        best_score = 0
        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or ""
            if not src or src.startswith("data:"):
                continue
            resolved = _resolve_url(src, page_url)
            if not resolved:
                continue
            alt = (img.get("alt", "") or "").lower()
            src_lower = resolved.lower()
            try:
                w = int(img.get("width") or 0)
                h = int(img.get("height") or 0)
            except (ValueError, TypeError):
                w, h = 0, 0
            score = 0
            for kw in ["robot", "product", "hero", "banner", "featured", "main", "photo"]:
                if kw in src_lower or kw in alt:
                    score += 3
            if w > 200 and h > 200:
                score += 2
            elif w > 100 and h > 100:
                score += 1
            if score > best_score:
                best_score = score
                best_img = resolved
        if best_img and best_score >= 3:
            return {"url": best_img, "source": page_url, "strategy": f"best img tag"}
        return None

    # Strategy 1-2: og:image / twitter:image from product page
    result = _parse_page(url, timeout=8)
    if result:
        # if it's an og:image, just return
        if "og:image" in result["strategy"] or "twitter:image" in result["strategy"]:
            return result
        strategies.append(result)

    # Strategy 3: try company homepage
    if company_url and company_url != url:
        result2 = _parse_page(company_url, timeout=6)
        if result2:
            if "og:image" in result2["strategy"] or "twitter:image" in result2["strategy"]:
                return result2
            strategies.append(result2)

    # Return best found (img tag results are lowest priority)
    if strategies:
        return strategies[0]
    return None

def batch_find_images(products, progress_callback=None):
    """Run multi-strategy image finder on a list of products.
    
    products: list of dicts with keys: id, name, product_url, company_name, company_slug
    progress_callback: optional func(current, total, product_name, result)
    Returns list of (product_id, image_url) tuples to save.
    """
    import sys
    sys.path.insert(0, "/Users/mark/robotics-comparison")
    from database.db import get_company_by_slug

    conn = None
    try:
        from database.db import get_db
        conn = get_db()
    except Exception:
        pass

    results = []
    for i, prod in enumerate(products):
        name = prod.get("name", "")
        prod_url = prod.get("product_url", "")
        company_slug = prod.get("company_slug", "")
        company = None
        if conn and company_slug:
            company = get_company_by_slug(conn, company_slug)
        company_name = company["name"] if company else company_slug
        company_website = company.get("website", "") if company else ""

        if not prod_url:
            if progress_callback:
                progress_callback(i, len(products), name, None)
            continue

        result = find_product_image_multi(prod_url, product_name=name, company_name=company_name, company_url=company_website)
        if result:
            results.append((prod["id"], result["url"], result["strategy"]))

        if progress_callback:
            progress_callback(i + 1, len(products), name, result)

        time.sleep(0.3)  # Rate limiting

    if conn:
        conn.close()
    return results
