import requests
from bs4 import BeautifulSoup
import tldextract
import json
import re
from urllib.parse import urlparse
from difflib import SequenceMatcher

IGNORED_EXTENSIONS = [".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".xml", ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf"]

RESEAUX_VALIDES = {
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "twitter.com": "Twitter",
    "linkedin.com": "LinkedIn",
    "google.com": "Google",
    "goo.gl": "Google Maps",
    "g.co": "Google Maps (short)",
    "youtube.com": "YouTube",
    "tripadvisor.com": "TripAdvisor",
    "tripadvisor.fr": "TripAdvisor"
}

def detect_reseau(url):
    domaine = tldextract.extract(url).registered_domain
    return RESEAUX_VALIDES.get(domaine)

def is_html_content_type(headers):
    return "text/html" in headers.get("Content-Type", "")

def is_ignored_file(url):
    path = urlparse(url).path
    return any(path.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    texts = []
    if soup.title:
        texts.append(soup.title.get_text())
    for tag in soup.find_all("meta"):
        if tag.get("content"):
            texts.append(tag["content"])
    return " ".join(texts)

def compute_similarity_score(page_text, nom, ville, activites):
    score = 0
    base = 0

    def contains(term):
        return term.lower() in page_text.lower()

    if nom:
        base += 1
        if contains(nom):
            score += 1
    if ville:
        base += 1
        if contains(ville):
            score += 1
    for act in activites:
        base += 1
        if contains(act):
            score += 1

    return round(score / base, 2) if base > 0 else 0

def check_url(url, language, nom, ville, activites):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": language,
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        final_url = response.url
        code = response.status_code

        reseau = detect_reseau(final_url)
        if not reseau or is_ignored_file(final_url) or not is_html_content_type(response.headers):
            return None  # Ignore les liens non pertinents

        soup_text = extract_text_from_html(response.text)
        score = compute_similarity_score(soup_text, nom, ville, activites)

        erreur = None
        url_corrigee = None
        if score < 0.5:
            erreur = f"Lien potentiellement incorrect (pertinence : {score})"
            url_corrigee = None  # à définir manuellement ou par système de recherche plus poussé

        return {
            "initial_url": url,
            "final_url": final_url,
            "reseau": reseau,
            "http_status": code,
            "pertinence": score,
            "erreur": erreur,
            "url_corrigee": url_corrigee
        }

    except requests.RequestException as e:
        return {
            "initial_url": url,
            "final_url": None,
            "reseau": "Inconnu",
            "http_status": None,
            "pertinence": 0,
            "erreur": str(e),
            "url_corrigee": None
        }

def extract_urls(obj):
    urls = []
    if isinstance(obj, dict):
        for v in obj.values():
            urls.extend(extract_urls(v))
    elif isinstance(obj, list):
        for item in obj:
            urls.extend(extract_urls(item))
    elif isinstance(obj, str):
        urls += re.findall(r'https?://[^\s"\'<>]+', obj)
    return urls

if __name__ == "__main__":
    with open(r"C:\Users\victo\Desktop\detect_errors\topkite-fr.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    langue = "fr-FR"
    urls = list(set(extract_urls(data)))
    print(f"🔗 {len(urls)} lien(s) détecté(s).")

    # Infos de référence pour le matching
    nom = data.get("info", {}).get("name", "")
    ville = data.get("info", {}).get("addresses", [{}])[0].get("city", "")
    activites = data.get("info", {}).get("tags", [])

    results = []
    for url in urls:
        result = check_url(url, langue, nom, ville, activites)
        if result:
            results.append(result)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    with open(r"C:\Users\victo\Desktop\detect_errors\output_links_check.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)

    print("\n✅ Résultats enregistrés dans 'output_links_check.json'")
