import requests
from bs4 import BeautifulSoup
import tldextract
import json
import re
from urllib.parse import urlparse

IGNORED_EXTENSIONS = [
    ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".xml", ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf"
]

def detect_reseau(url):
    domaines = {
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
    domaine = tldextract.extract(url).registered_domain
    return domaines.get(domaine, "Autre / inconnu")

def is_html_content_type(headers):
    content_type = headers.get("Content-Type", "")
    return "text/html" in content_type

def is_ignored_file(url):
    path = urlparse(url).path
    return any(path.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

def check_url(url, language="fr-FR"):
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
        erreur = None

        if code >= 400:
            erreur = f"Erreur HTTP {code}"
        elif is_ignored_file(final_url) or not is_html_content_type(response.headers):
            erreur = "Type de contenu non analysé (fichier ou non-HTML)"
        else:
            try:
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string.lower() if soup.title else ""
                if "google.com/maps" not in final_url and "search" not in final_url and "g.page" not in final_url and "g.co" in url:
                    erreur = "Lien court Google redirige vers une page inattendue"
                elif any(e in title for e in ["error", "not found", "page introuvable"]):
                    erreur = f"Problème détecté dans le titre de la page : {title}"
            except Exception as e:
                erreur = f"Erreur lors de l’analyse HTML : {str(e)}"

        return {
            "initial_url": url,
            "final_url": final_url,
            "reseau": detect_reseau(final_url),
            "http_status": code,
            "erreur": erreur
        }

    except requests.RequestException as e:
        return {
            "initial_url": url,
            "final_url": None,
            "reseau": "Inconnu",
            "http_status": None,
            "erreur": str(e)
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
        matches = re.findall(r'https?://[^\s"\'<>]+', obj)
        urls.extend(matches)
    return urls

if __name__ == "__main__":
    with open("topkite-fr.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    langue = "fr-FR"
    urls = list(set(extract_urls(data)))
    print(f"🔗 {len(urls)} lien(s) détecté(s) dans le fichier JSON.")

    results = []
    for url in urls:
        result = check_url(url, langue)
        results.append(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    with open("output_links_check.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)

    print("\n✅ Résultats enregistrés dans 'output_links_check.json'")
