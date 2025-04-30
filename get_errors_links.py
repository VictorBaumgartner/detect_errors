import requests
from bs4 import BeautifulSoup
import tldextract
import json
import re
from urllib.parse import urlparse
from difflib import SequenceMatcher

IGNORED_EXTENSIONS = [
    ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".xml", ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf"
]

# Seuil minimal de similarité pour considérer le contenu comme correspondant
SIMILARITY_THRESHOLD = 0.3

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
    return domaines.get(domaine, None)

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
    for tag in soup.find_all(["meta", "p", "h1", "h2", "h3"]):
        if tag.name == "meta" and tag.get("content"):
            texts.append(tag["content"])
        elif tag.string:
            texts.append(tag.get_text())
    return " ".join(texts)

def compute_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def check_url(url, language="fr-FR", reference_text=""):
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
        similarity = None

        reseau = detect_reseau(final_url)
        if not reseau:
            return None  # Ignorer les liens inconnus

        if code >= 400:
            erreur = f"Erreur HTTP {code}"
        elif is_ignored_file(final_url) or not is_html_content_type(response.headers):
            erreur = "Type de contenu non analysé (fichier ou non-HTML)"
        else:
            try:
                page_text = extract_text_from_html(response.text)
                similarity = compute_similarity(reference_text, page_text)
                if similarity < SIMILARITY_THRESHOLD:
                    erreur = f"Contenu peu pertinent (similarité = {similarity:.2f})"
            except Exception as e:
                erreur = f"Erreur analyse HTML : {str(e)}"

        return {
            "initial_url": url,
            "final_url": final_url,
            "reseau": reseau,
            "http_status": code,
            "erreur": erreur,
            "similarity_score": similarity
        }

    except requests.RequestException as e:
        return {
            "initial_url": url,
            "final_url": None,
            "reseau": "Inconnu",
            "http_status": None,
            "erreur": str(e),
            "similarity_score": None
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
    with open(r"C:\Users\victo\Desktop\detect_errors\topkite-fr.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    langue = "fr-FR"
    urls = list(set(extract_urls(data)))
    print(f"🔗 {len(urls)} lien(s) détecté(s) dans le fichier JSON.")

    # Texte de référence basé sur le contenu JSON (nom, ville, description)
    nom = data.get("info", {}).get("name", "")
    ville = data.get("info", {}).get("addresses", [{}])[0].get("city", "")
    description = " ".join([nom, ville])
    reference_text = description.strip()

    results = []
    for url in urls:
        result = check_url(url, langue, reference_text=reference_text)
        if result and not result["reseau"] is None:
            results.append(result)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    with open(r"C:\Users\victo\Desktop\detect_errors\output_links_check.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)

    print("\n✅ Résultats enregistrés dans 'output_links_check.json'")
