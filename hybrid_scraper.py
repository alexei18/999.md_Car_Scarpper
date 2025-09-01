import httpx
import json
import time
import random
import os.path
import sys
import codecs
from playwright.sync_api import sync_playwright, expect, TimeoutError as PlaywrightTimeoutError
import re

# =================================================================================================
# --- CONFIGURARE MANUALĂ ---
# Deoarece 999.md blochează extragerea automată a filtrelor, acestea trebuie introduse manual.
#
# CUM SĂ GĂSEȘTI VALORILE:
#   1. Deschide Chrome/Firefox și navighează la pagina 999.md cu filtrele dorite.
#   2. Apasă F12 pentru a deschide "Developer Tools".
#   3. Selectează tab-ul "Network" (Rețea).
#   4. În câmpul de filtrare din tab-ul Network, scrie "graphql".
#   5. Reîmprospătează pagina (F5).
#   6. Vei vedea o cerere (request). Dă click pe ea.
#   7. În panoul care apare, mergi la tab-ul "Payload" (sau "Request").
#   8. Aici vei găsi "subCategoryId" și lista de "filters".
#   9. Copiază aceste valori și pune-le mai jos.
# =================================================================================================

# Configurăm stdout pentru a forța UTF-8, prevenind erorile de codificare pe Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

SEARCH_PAYLOAD = {
    "subCategoryId": 659,
    "filters": [
        {
            "filterId": 1,
            "features": [
                {
                    "featureId": 20,
                    "optionIds": [111]
                }
            ]
        }
    ]
}

# --- Alte setări ---
IS_TEST_MODE = True   # Procesează doar 10 anunțuri pentru testare rapidă
# IS_TEST_MODE = False  # Procesează TOATE anunțurile noi de pe site

MAX_ADS_TO_PROCESS_IN_TEST_MODE = 20
JSON_FILE = 'date_masini_999_complet.json'
# =================================================================================================


def get_ads_from_api(session, page_number, search_input, ads_per_page=90):
    """Interoghează API-ul GraphQL al 999.md folosind parametrii manuali."""
    api_url = "https://999.md/graphql"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Accept': 'application/json', 'Content-Type': 'application/json', 'lang': 'ro'
    }
    
    variables_input = {
        **search_input,
        "source": "AD_SOURCE_DESKTOP",
        "pagination": {"limit": ads_per_page, "skip": page_number * ads_per_page},
    }

    graphql_payload = {
        "operationName": "SearchAds",
        "variables": {
            "isWorkCategory": False, "includeCarsFeatures": True, "includeBody": False,
            "includeOwner": True, "includeBoost": True, "input": variables_input, "locale": "ro_RO"
        },
        "query": """query SearchAds($input: Ads_SearchInput!, $isWorkCategory: Boolean = false, $includeCarsFeatures: Boolean = false, $includeBody: Boolean = false, $includeOwner: Boolean = false, $includeBoost: Boolean = false, $locale: Common_Locale) {\n  searchAds(input: $input) {\n    ads { ...AdsSearchFragment }\n    count\n  }\n}\nfragment AdsSearchFragment on Advert {\n  ...AdListFragment\n  ...WorkCategoryFeatures @include(if: $isWorkCategory)\n  reseted(input: {format: \"2 Jan. 2006, 15:04\", locale: $locale, timezone: \"Europe/Chisinau\", getDiff: false})\n}\nfragment AdListFragment on Advert {\n  id\n  title\n  subCategory { ...CategoryAdFragment }\n  ...PriceAndImages\n  ...CarsFeatures @include(if: $includeCarsFeatures)\n  ...AdvertOwner @include(if: $includeOwner)\n  transportYear: feature(id: 19) { ...FeatureValueFragment }\n  body: feature(id: 13) @include(if: $includeBody) { ...FeatureValueFragment }\n  ...AdvertBooster @include(if: $includeBoost)\n  label: displayProduct(alias: LABEL) { ... on DisplayLabel { enable ...DisplayLabelFragment } }\n}\nfragment CategoryAdFragment on Category { id title { ...TranslationFragment } }\nfragment TranslationFragment on I18NTr { translated }\nfragment PriceAndImages on Advert { price: feature(id: 2) { ...FeatureValueFragment } images: feature(id: 14) { ...FeatureValueFragment } }\nfragment FeatureValueFragment on FeatureValue { id type value }\nfragment CarsFeatures on Advert {\n  carFuel: feature(id: 151) { ...FeatureValueFragment }\n  carTransmission: feature(id: 101) { ...FeatureValueFragment }\n  mileage: feature(id: 104) { ...FeatureValueFragment }\n  engineVolume: feature(id: 103) { ...FeatureValueFragment }\n}\nfragment AdvertOwner on Advert { owner { id, login, business { plan } } }\nfragment AdvertBooster on Advert { booster: product(alias: BOOSTER) { enable } }\nfragment DisplayLabelFragment on DisplayLabel { title color { r g b a } }\nfragment WorkCategoryFeatures on Advert {\n  salary: feature(id: 26) { ...FeatureValueFragment }\n}\n"""
    }
    try:
        response = session.post(api_url, headers=headers, json=graphql_payload, timeout=25)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Eroare API: {e}")
        return None

import re

def get_phone_number_with_playwright(page, ad_url):
    """Navighează la un URL, dă click pe buton și extrage numerele de telefon folosind regex."""
    try:
        page.goto(ad_url, wait_until='domcontentloaded', timeout=15000)
        
        show_phone_button = page.locator("button:has-text('Arată numărul')").first
        
        try:
            show_phone_button.wait_for(state='visible', timeout=5000)
            show_phone_button.click(timeout=3000, force=True)
            # Am mărit pauza pentru a permite paginii să încarce numărul
            page.wait_for_timeout(random.uniform(1800, 2500))
        except PlaywrightTimeoutError:
            pass

        page_content = page.locator('body').inner_text()
        
        # Expresie regulată robustă pentru numere de telefon
        phone_regex = r'\+373(?:\s*\d){8,}'
        
        # Folosim re.finditer pentru a garanta extragerea potrivirii complete
        matches = re.finditer(phone_regex, page_content)
        found_numbers = [match.group(0) for match in matches]
        
        cleaned_numbers = {''.join(num.split()) for num in found_numbers}
        
        support_number_cleaned = "+37322888002"
        valid_numbers = {num for num in cleaned_numbers if num != support_number_cleaned}
        
        if valid_numbers:
            return ", ".join(sorted(list(valid_numbers)))
        else:
            return "Nu s-au găsit numere valide"

    except Exception as e:
        return f"Eroare la extragere: {type(e).__name__}"

def parse_ad_data(ad_raw):
    """Procesează datele brute de la API."""
    ad_id = ad_raw.get('id')
    if not ad_id: return None
    
    ad_url = f"https://999.md/ro/{ad_id}"
    ad_details = {'id': ad_id, 'url': ad_url, 'titlu': ad_raw.get('title', 'N/A')}
    
    price_info = ad_raw.get('price')
    ad_details['pret'] = f"{price_info['value'].get('value', 'N/A')} {price_info['value'].get('unit', '').replace('UNIT_', '')}" if price_info and isinstance(price_info.get('value'), dict) else "Preț negociabil"
    
    ad_details['an_fabricatie'] = ad_raw.get('transportYear', {}).get('value', 'N/A') if ad_raw.get('transportYear') else 'N/A'
    
    specificatii = {}
    if ad_raw.get('carFuel') and isinstance(ad_raw['carFuel'].get('value'), dict): specificatii['Combustibil'] = ad_raw['carFuel']['value'].get('translated', 'N/A')
    if ad_raw.get('carTransmission') and isinstance(ad_raw['carTransmission'].get('value'), dict): specificatii['Cutia de viteze'] = ad_raw['carTransmission']['value'].get('translated', 'N/A')
    if ad_raw.get('mileage') and isinstance(ad_raw['mileage'].get('value'), dict):
        mileage_val = ad_raw['mileage']['value'].get('value', 'N/A')
        unit = ad_raw['mileage']['value'].get('unit', 'UNIT_UNSPECIFIED').replace('UNIT_', '').lower()
        specificatii['Rulaj'] = f"{mileage_val} {unit}"
    if ad_raw.get('engineVolume') and isinstance(ad_raw['engineVolume'].get('value'), dict): specificatii['Capacitate cilindrică'] = f"{ad_raw['engineVolume']['value'].get('value')} cm³"
    ad_details['specificatii'] = specificatii
    
    owner_info = ad_raw.get('owner')
    if owner_info and isinstance(owner_info, dict):
        ad_details['nume_proprietar'] = owner_info.get('login', 'N/A')
        ad_details['tip_proprietar'] = 'Dealer auto' if owner_info.get('business') and owner_info['business'].get('plan') != 'BUSINESS_PLAN_UNSPECIFIED' else 'Persoană fizică'
    else:
        ad_details['nume_proprietar'], ad_details['tip_proprietar'] = 'N/A', 'N/A'
        
    ad_details['fotografii'] = [f"https://i.simpalsmedia.com/999.md/BoardImages/900x900/{filename}" for filename in ad_raw.get('images', {}).get('value', [])] if ad_raw.get('images') else []
    
    return ad_details

if __name__ == "__main__":
    existing_data, known_links = [], set()
    if os.path.exists(JSON_FILE):
        print(f"S-a găsit fișierul '{JSON_FILE}'. Se încarcă link-urile existente...")
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
                known_links = {item['url'] for item in existing_data if 'url' in item}
                print(f"S-au încărcat {len(known_links)} link-uri.")
            except json.JSONDecodeError:
                print("Atenție: Fișierul JSON este gol sau corupt.")

    with httpx.Client(http2=True) as session:
        all_new_ads = []
        page_number = 0
        ads_per_page = 90
        print("\nPasul 1: Colectare date de bază prin API folosind filtrele manuale...")
        
        while True:
            api_response = get_ads_from_api(session, page_number, SEARCH_PAYLOAD, ads_per_page)
            if not api_response or 'errors' in api_response or not api_response.get('data', {}).get('searchAds'):
                print("Cerere API eșuată sau fără date. Se oprește colectarea.")
                break
            
            ads_batch = api_response['data']['searchAds'].get('ads', [])
            if not ads_batch and page_number > 0:
                print("Nu s-au mai găsit anunțuri. Colectarea s-a încheiat.")
                break
                
            if page_number == 0:
                total_ads_count = api_response['data']['searchAds'].get('count', 0)
                print(f"Total anunțuri de verificat pentru filtrele specificate: {total_ads_count}")

            newly_found_on_page = 0
            for ad_raw in ads_batch:
                ad_data = parse_ad_data(ad_raw)
                if ad_data and ad_data['url'] not in known_links:
                    all_new_ads.append(ad_data)
                    known_links.add(ad_data['url'])
                    newly_found_on_page += 1
            
            print(f"  Pagina {page_number + 1}: {newly_found_on_page} anunțuri noi adăugate (Total noi: {len(all_new_ads)})")
            
            if IS_TEST_MODE and len(all_new_ads) >= MAX_ADS_TO_PROCESS_IN_TEST_MODE:
                print("Mod de testare: S-a atins limita de anunțuri noi.")
                break
            if not IS_TEST_MODE and len(ads_batch) < ads_per_page:
                print("Pagina nu este completă, probabil ultima. Se oprește.")
                break
                
            page_number += 1
            time.sleep(random.uniform(1.0, 2.5))

        if IS_TEST_MODE:
            all_new_ads = all_new_ads[:MAX_ADS_TO_PROCESS_IN_TEST_MODE]

        if all_new_ads:
            print(f"\nPasul 2: Se extrag numerele de telefon pentru {len(all_new_ads)} anunțuri noi folosind Playwright...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
                page = context.new_page()
                
                # Blocăm resursele inutile pentru a mări viteza
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font"] else route.continue_())
                
                start_time = time.time()
                for i, ad in enumerate(all_new_ads):
                    print(f"  Procesare telefon {i+1}/{len(all_new_ads)} pentru: {ad['url']}")
                    ad['numar_telefon'] = get_phone_number_with_playwright(page, ad['url'])
                
                end_time = time.time()
                browser.close()
                
            print(f"Extragerea telefoanelor a durat: {end_time - start_time:.2f} secunde.")
            
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_data + all_new_ads, f, indent=4, ensure_ascii=False)
                
            print(f"\n--- SUCCES! S-au adăugat {len(all_new_ads)} anunțuri noi. Total în fișier: {len(existing_data) + len(all_new_ads)}. ---")
        else:
            print("\nNiciun anunț nou găsit de la ultima rulare.")

