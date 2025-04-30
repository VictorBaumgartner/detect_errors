import requests
import extruct
from w3lib.html import get_base_url
import json
import re
import tldextract
from urllib.parse import urlparse
from bs4 import BeautifulSoup

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

def get_structured_data(html, url):
    return extruct.extract(html, base_url=get_base_url(html, url), syntaxes=['json-ld', 'microdata', 'opengraph'])

def is_valid_business(structured_data, nom, ville, activites):
    nom = nom.lower()
    ville = ville.lower()
    activites = [a.lower() for a in activites]

    def contains_all(text):
        return all(word in text.lower() for word in [nom, ville] + activites)

    for source in structured_data.values():
        for item in source:
            json_data = item.get('@type') if isinstance(item, dict) else None
            full_data = json.dumps(item).lower()
            if contains_all(full_data):
                return True
    return False

def check_url(url, nom, ville, activites, language="fr-FR"):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": language
    }

    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        final_url = response.url
        code = response.status_code
        reseau = detect_reseau(final_url)

        if code >= 400 or not reseau:
            return None  # Erreur ou domaine non pertinent

        structured_data = get_structured_data(response.text, final_url)
        valid = is_valid_business(structured_data, nom, ville, activites)

        soup = BeautifulSoup(response.text, 'lxml')
        title = soup.title.string if soup.title else ''
        meta = " ".join([m.get("content", "") for m in soup.find_all("meta")])
        full_text = " ".join([title, meta])

        valid_fallback = (
            nom.lower() in full_text.lower()
            and (ville.lower() in full_text.lower() or any(a in full_text.lower() for a in activites))
        )

        return {
            "initial_url": url,
            "final_url": final_url,
            "reseau": reseau,
            "http_status": code,
            "pertinent": valid or valid_fallback,
            "erreur": None if (valid or valid_fallback) else "Non reconnu comme la bonne activité",
            "url_corrigee": None  # Peut être rempli plus tard si faux lien
        }

    except Exception as e:
        return {
            "initial_url": url,
            "final_url": None,
            "reseau": "Erreur",
            "http_status": None,
            "pertinent": False,
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

    nom = data.get("info", {}).get("name", "")
    ville = data.get("info", {}).get("addresses", [{}])[0].get("city", "")
    activites = data.get("info", {}).get("tags", [])

    results = []
    for url in urls:
        result = check_url(url, nom, ville, activites, langue)
        if result:
            results.append(result)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    with open(r"C:\Users\victo\Desktop\detect_errors\output_links_check.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)

    print("\n✅ Résultats enregistrés dans 'output_links_check.json'")
