from duckduckgo_search import DDGS
import requests, json, re, tldextract
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url
from urllib.parse import urlparse

RESEAUX_VALIDES = {
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "twitter.com": "Twitter",
    "linkedin.com": "LinkedIn",
    "google.com": "Google",
    "g.co": "Google Maps (short)",
    "tripadvisor.fr": "TripAdvisor",
    "tripadvisor.com": "TripAdvisor"
}

def detect_reseau(url):
    domaine = tldextract.extract(url).registered_domain
    return RESEAUX_VALIDES.get(domaine)

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

def get_structured_data(html, url):
    return extruct.extract(html, base_url=get_base_url(html, url), syntaxes=['json-ld', 'microdata', 'opengraph'])

def is_valid_business(structured_data, nom, ville, activites):
    nom, ville = nom.lower(), ville.lower()
    activites = [a.lower() for a in activites]

    def contains_all(text):
        return all(word in text.lower() for word in [nom, ville] + activites)

    for source in structured_data.values():
        for item in source:
            full_data = json.dumps(item).lower()
            if contains_all(full_data):
                return True
    return False

def check_url(url, nom, ville, activites, language="fr-FR"):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": language
        }
        response = requests.get(url, headers=headers, timeout=10)
        code = response.status_code
        final_url = response.url

        reseau = detect_reseau(final_url)
        if code >= 400 or not reseau:
            return None

        structured_data = get_structured_data(response.text, final_url)
        valid = is_valid_business(structured_data, nom, ville, activites)

        return {
            "initial_url": url,
            "final_url": final_url,
            "reseau": reseau,
            "http_status": code,
            "pertinent": valid,
            "erreur": None if valid else "Contenu non reconnu",
            "url_corrigee": None
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

def rechercher_liens(nom, ville, activites):
    mots_cles = [nom, ville] + activites
    requete = " ".join(mots_cles)

    suggestions = {}
    with DDGS() as ddgs:
        for result in ddgs.text(f"{requete} site:facebook.com"):
            suggestions["facebook"] = result["href"]
            break
        for result in ddgs.text(f"{requete} site:instagram.com"):
            suggestions["instagram"] = result["href"]
            break
        for result in ddgs.text(f"{requete} site:tripadvisor.fr"):
            suggestions["tripadvisor"] = result["href"]
            break
        for result in ddgs.text(f"{requete} site:g.co"):
            suggestions["google"] = result["href"]
            break

    return suggestions

if __name__ == "__main__":
    with open(r"C:\Users\victo\Desktop\detect_errors\topkite-fr.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    langue = "fr-FR"
    urls_detected = list(set(extract_urls(data)))
    nom = data.get("info", {}).get("name", "")
    ville = data.get("info", {}).get("addresses", [{}])[0].get("city", "")
    activites = data.get("info", {}).get("tags", [])

    # Recherche liens suggérés si manquants
    suggestions = rechercher_liens(nom, ville, activites)

    results = []
    for url in urls_detected:
        result = check_url(url, nom, ville, activites, langue)
        if result:
            results.append(result)

    # Ajouter les liens manquants
    existing_reseaux = {detect_reseau(r["initial_url"]) for r in results if r["pertinent"]}
    for key, suggested_url in suggestions.items():
        if RESEAUX_VALIDES.get(tldextract.extract(suggested_url).registered_domain) not in existing_reseaux:
            results.append({
                "initial_url": None,
                "final_url": None,
                "reseau": RESEAUX_VALIDES.get(tldextract.extract(suggested_url).registered_domain),
                "http_status": None,
                "pertinent": True,
                "erreur": None,
                "url_corrigee": suggested_url
            })

    with open(r"C:\Users\victo\Desktop\detect_errors\output_links_check.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2, ensure_ascii=False)

    print("✅ Vérifications terminées et résultats enregistrés.")
