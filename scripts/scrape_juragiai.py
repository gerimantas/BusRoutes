"""
Ištraukia Kaunas → Juragiai tvarkaraščius iš autobusubilietai.lt
Naudoja search URL su stotelės filtru

Ištraukia:
- 106 maršrutą (Kaunas-Jonučiai-Jurginiškiai-Skriaudžiai)
- Tarpmiestinių autobusų reisus per Juragius
"""

import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright


def load_search_page(page, url, label=''):
    """
    Atidaro paieškos puslapį ir laukia, kol reisų sąrašas nustos augti.

    Reisai kraunami JS'u, todėl fiksuotas laukimas nepatikimas: esant
    lėtesniam tinklui nuskaitoma tik dalis rezultatų. Laukiame, kol
    laiko antraščių skaičius stabilizuosis kelis patikrinimus iš eilės.
    """
    page.goto(url, wait_until='domcontentloaded')

    # Palaukiame pirmojo rezultato arba aiškaus "nerasta" pranešimo
    try:
        page.wait_for_function(
            """() => {
                const body = document.body.innerText || '';
                if (body.includes('reisų nerasta') || body.includes('Nerasta')) return true;
                return [...document.querySelectorAll('h2, h3')]
                    .some(h => /^\\d{2}:\\d{2}$/.test(h.textContent.trim()));
            }""",
            timeout=45000,
        )
    except Exception:
        print(f"! {label}: nesulaukta rezultatų per 45s")
        return False

    # Laukiame, kol skaičius nustos keistis (3 vienodi matavimai po 1s)
    stable = 0
    previous = -1
    for _ in range(30):
        count = page.evaluate(
            """() => [...document.querySelectorAll('h2, h3')]
                .filter(h => /^\\d{2}:\\d{2}$/.test(h.textContent.trim())).length"""
        )
        if count == previous:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
            previous = count
        page.wait_for_timeout(1000)
    else:
        print(f"! {label}: sąrašas nestabilizavosi, imamas paskutinis būvis ({previous})")

    return True


def extract_trips(page):
    """
    Ištraukia visus reisus iš search rezultatų puslapio
    """
    trips_106 = []
    trips_tm = []  # tarpmiestiniai
    
    # Patikriname, ar puslapis turi duomenų
    page_text = page.locator('body').text_content()
    if 'Šiai dienai reisų nerasta' in page_text or 'Nerasta' in page_text:
        print("! Nerasta reisų šiai dienai")
        return trips_106, trips_tm
    
    # Randame visas laiko antraštes (h2, h3 su laiku)
    all_headings = page.locator('h2, h3').all()
    
    time_headings = []
    for h in all_headings:
        text = h.text_content().strip()
        if re.match(r'^\d{2}:\d{2}$', text):
            time_headings.append(h)
    
    print(f"Rasta reisų laikų: {len(time_headings)}")
    
    for heading in time_headings:
        try:
            time_text = heading.text_content().strip()
            
            # Randame parent container su visu reiso info
            parent = heading.locator('xpath=../..')
            trip_cards = parent.locator('> div').all()
            
            for card in trip_cards:
                card_text = card.text_content()
                
                # Ištraukiame maršruto pavadinimą
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                
                # Pirmoji eilutė paprastai yra maršruto pavadinimas
                route_name = lines[0] if lines else 'Unknown'
                
                # Ištraukiame laiko intervalą
                time_match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', card_text)
                departure = time_match.group(1) if time_match else time_text
                arrival_juragiai = time_match.group(2) if time_match else '?'
                
                # Ištraukiame kainą
                price_match = re.search(r'(\d+,\d+)\s*€', card_text)
                price = price_match.group(1) if price_match else '?'
                
                # Identifikuojame vežėją
                carrier = 'Unknown'
                if 'Kautra Plius' in card_text:
                    carrier = 'Kautra Plius'
                elif 'Kautra' in card_text:
                    carrier = 'Kautra'
                elif 'Marijampolės AP' in card_text:
                    carrier = 'Marijampolės AP'
                elif 'TOKS' in card_text:
                    carrier = 'TOKS'
                
                # Ar galima pirkti internetu?
                available_online = 'Pirkti' in card_text
                note = '' if available_online else '(internetu neparduodamas)'
                
                # Nustatome platformą pagal maršruto tipą
                is_106 = any(x in route_name for x in ['Jonučiai', 'Jurginiškiai', 'Skriaudžiai'])
                platform = '106' if is_106 else 'tm'
                
                trip = {
                    'departure': departure,
                    'arrival_juragiai': arrival_juragiai,
                    'route_name': route_name,
                    'carrier': carrier,
                    'price': price,
                    'note': note,
                    'platform': platform
                }
                
                # Skirstome pagal maršrutą
                if 'Skriaudžiai' in route_name or 'Jurginiškiai' in route_name:
                    trips_106.append(trip)
                elif 'Marijampolė' in route_name or 'Vilkaviškis' in route_name:
                    trips_tm.append(trip)
                else:
                    # Kiti tarpmiestiniai
                    trips_tm.append(trip)
                    
        except Exception as e:
            print(f"Klaida apdorojant reisą: {e}")
            continue
    
    # Pašaliname dublikatus (tas pats reisas gali pasirodyti kelis kartus dėl HTML struktūros)
    def dedupe_trips(trips_list):
        seen = set()
        unique = []
        for trip in trips_list:
            # Naudojame tik laiką kaip raktą, nes arrival kartais skiriasi dėl +1d
            key = (trip['departure'], trip['carrier'], trip['price'])
            if key not in seen:
                seen.add(key)
                unique.append(trip)
        return unique
    
    trips_106 = dedupe_trips(trips_106)
    trips_tm = dedupe_trips(trips_tm)
    
    print(f"\nPo dublikatų šalinimo:")
    print(f"  106 maršrutas: {len(trips_106)} reisai")
    print(f"  Tarpmiestiniai: {len(trips_tm)} reisai")
    
    return trips_106, trips_tm


def format_106_with_periodicity(trips, direction="Kaunas → Juragiai"):
    """
    Konvertuoja 106 maršruto duomenis į markdown SU PERIODIŠKUMU
    """
    md = f"""# 106 Maršrutas: {direction} (PILNAS TVARKARAŠTIS)

Šaltinis: `autobusubilietai.lt`  
Maršrutas: Kaunas-Jonučiai-Jurginiškiai-Skriaudžiai  
Vežėjas: Kautra

Periodiškumas nustatytas lyginant ketvirtadienį, šeštadienį ir sekmadienį.

## Tvarkaraštis

| Kaunas | Juragiai | Periodiškumas | Dienos | Platforma | Kaina |
|--------|----------|---------------|--------|-----------|-------|
"""
    
    for trip in trips:
        md += f"| {trip['departure']} | {trip['arrival_juragiai']} | {trip['periodicity']} | {trip['days_label']} | {trip['platform']} | {trip['price']} € |\n"
    
    # Statistika
    workdays = [t for t in trips if t['periodicity'] == 'WORKDAYS']
    weekends = [t for t in trips if t['periodicity'] == 'WEEKEND']
    all_days = [t for t in trips if t['periodicity'] == 'ALL_DAYS']
    
    md += f"""

**Statistika:**
- Tik darbo dienomis (Pr-Pn): {len(workdays)} reisai
- Tik savaitgaliais (Š-S): {len(weekends)} reisai
- Kasdien: {len(all_days)} reisai
- **Iš viso:** {len(trips)} reisai

## Konvertavimas į grafikai.html formatą

Pavyzdys:
```javascript
// Darbo dienomis (platforma 106 = 5 aikštelė)
["{workdays[0]['departure'] if workdays else '00:00'}", WORKDAYS, "106"],

// Savaitgaliais
["{weekends[0]['departure'] if weekends else '00:00'}", WEEKEND, "106"],

// Kasdien
["{all_days[0]['departure'] if all_days else '00:00'}", ALL_DAYS, "106"],
```
"""
    
    return md


def format_tm_with_periodicity(trips, direction="Kaunas → Marijampolė/Vilkaviškis"):
    """
    Konvertuoja tarpmiestinių autobusų duomenis į markdown SU PERIODIŠKUMU
    """
    md = f"""# Tarpmiestiniai autobusai per Juragius (PILNAS TVARKARAŠTIS)

Šaltinis: `autobusubilietai.lt`  
Kryptis: {direction}

Periodiškumas nustatytas lyginant ketvirtadienį, šeštadienį ir sekmadienį.

## Tvarkaraštis

| Kaunas | Juragiai | Maršrutas | Vežėjas | Periodiškumas | Dienos | Platforma | Kaina |
|--------|----------|-----------|---------|---------------|--------|-----------|-------|
"""
    
    for trip in trips:
        route_clean = trip['route_name'][:50]  # Apribojame ilgį
        md += f"| {trip['departure']} | {trip['arrival_juragiai']} | {route_clean} | {trip['carrier']} | {trip['periodicity']} | {trip['days_label']} | {trip['platform']} | {trip['price']} € |\n"
    
    # Statistika
    workdays = [t for t in trips if t['periodicity'] == 'WORKDAYS']
    weekends = [t for t in trips if t['periodicity'] == 'WEEKEND']
    all_days = [t for t in trips if t['periodicity'] == 'ALL_DAYS']
    
    md += f"""

**Statistika:**
- Tik darbo dienomis (Pr-Pn): {len(workdays)} reisai
- Tik savaitgaliais (Š-S): {len(weekends)} reisai
- Kasdien: {len(all_days)} reisai
- **Iš viso:** {len(trips)} reisai

## Konvertavimas į grafikai.html formatą

Naudoti žymę `platform: "tm"` (tarpmiestinis = 12 aikštelė).

Pavyzdys:
```javascript
// Darbo dienomis (platforma tm = 12 aikštelė)
["{workdays[0]['departure'] if workdays else '00:00'}", WORKDAYS, "tm"],

// Kasdien
["{all_days[0]['departure'] if all_days else '00:00'}", ALL_DAYS, "tm"],
```
"""
    
    return md


def format_106_to_markdown(trips):
    """
    Konvertuoja 106 maršruto duomenis į markdown
    """
    md = f"""# 106 Maršrutas: Kaunas → Juragiai (WEB)

Šaltinis: `autobusubilietai.lt`  
Maršrutas: Kaunas-Jonučiai-Jurginiškiai-Skriaudžiai  
Vežėjas: Kautra

## Tvarkaraštis

| Kaunas | Juragiai | Kaina | Pastaba |
|--------|----------|-------|---------|
"""
    
    for trip in trips:
        md += f"| {trip['departure']} | {trip['arrival_juragiai']} | {trip['price']} € | {trip['note']} |\n"
    
    md += f"""

**Ištraukta reisų:** {len(trips)}

## Konvertavimas į grafikai.html formatą

Periodiškumas nežinomas (reikia patikrinti skirtingomis dienomis).  
Tikėtina, kad dauguma reisų yra `WORKDAYS` (Pr-Pn).

Pavyzdžio formatas:
```javascript
["{trips[0]['departure']}", WORKDAYS, "106"],  // Kaunas → Juragiai
```
"""
    
    return md


def format_tm_to_markdown(trips):
    """
    Konvertuoja tarpmiestinių autobusų duomenis į markdown
    """
    md = f"""# Tarpmiestiniai autobusai per Juragius (WEB)

Šaltinis: `autobusubilietai.lt`  
Kryptis: Kaunas → Marijampolė / Vilkaviškis (sustoja Juragiuose)

## Tvarkaraštis

| Kaunas | Juragiai | Maršrutas | Vežėjas | Kaina | Pastaba |
|--------|----------|-----------|---------|-------|---------|
"""
    
    for trip in trips:
        md += f"| {trip['departure']} | {trip['arrival_juragiai']} | {trip['route_name']} | {trip['carrier']} | {trip['price']} € | {trip['note']} |\n"
    
    md += f"""

**Ištraukta reisų:** {len(trips)}

## Konvertavimas į grafikai.html formatą

Naudoti žymę `platform: "tm"` (tarpmiestinis).  
Periodiškumas nežinomas (reikia patikrinti skirtingomis dienomis).

Pavyzdžio formatas:
```javascript
["{trips[0]['departure']}", ALL_DAYS, "tm"],  // Tarpmiestinis per Juragius
```
"""
    
    return md


def main():
    """
    Pagrindinis skriptas - ištraukia tvarkaraščius kelioms dienoms ABIEJŲ KRYPČIŲ
    """
    print("\n" + "="*70)
    print("AUTOBUSUBILIETAI.LT — PILNAS TVARKARAŠTIS (ABI KRYPTYS)")
    print("="*70 + "\n")
    
    from datetime import datetime, timedelta
    
    # Ištraukiame 3 dienų tvarkaraščius: ketvirtadienis, šeštadienis, sekmadienis
    today = datetime.now()
    
    # Randame artimiausia ketvirtadienį
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0:
        days_until_thursday = 7  # jei šiandien ketvirtadienis, imame kitą
    thursday = today + timedelta(days=days_until_thursday)
    saturday = thursday + timedelta(days=2)
    sunday = thursday + timedelta(days=3)
    
    test_dates = [
        (thursday, 'Ketvirtadienis (darbo diena)'),
        (saturday, 'Šeštadienis'),
        (sunday, 'Sekmadienis')
    ]
    
    print("Testuojamos datos:")
    for date, label in test_dates:
        print(f"  {date.strftime('%Y-%m-%d')} - {label}")
    print()
    
    with sync_playwright() as p:
        print("Paleidžiamas Chrome...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # =========================================================
        # KRYPTIS 1: KAUNAS → JURAGIAI
        # =========================================================
        print("\n" + "="*70)
        print("📍 KRYPTIS: KAUNAS → JURAGIAI")
        print("="*70)
        
        all_trips_kaunas_juragiai = {}
        
        # Ištraukiame reisus kiekvienai dienai
        for test_date, label in test_dates:
            date_str = test_date.strftime('%Y-%m-%d')
            search_url = f"https://www.autobusubilietai.lt/search?departureTime=00:00&departureDate={date_str}&from=2408-1&fromStop=Kaunas&to=3-1,3-2&toStop=Juragiai"
            
            print(f"\n{'='*70}")
            print(f"Kraunamas: {label} ({date_str})")
            print(f"{'='*70}")
            
            load_search_page(page, search_url, f"{label} ({date_str})")

            trips_106, trips_tm = extract_trips(page)
            all_trips_kaunas_juragiai[label] = {
                '106': trips_106,
                'tm': trips_tm
            }
        
        # =========================================================
        # KRYPTIS 2: JURAGIAI → KAUNAS
        # =========================================================
        print("\n" + "="*70)
        print("📍 KRYPTIS: JURAGIAI → KAUNAS")
        print("="*70)
        
        all_trips_juragiai_kaunas = {}
        
        # Ištraukiame reisus kiekvienai dienai
        for test_date, label in test_dates:
            date_str = test_date.strftime('%Y-%m-%d')
            search_url = f"https://www.autobusubilietai.lt/search?departureTime=00:00&departureDate={date_str}&from=3-1,3-2&fromStop=Juragiai&to=2408-1&toStop=Kaunas"
            
            print(f"\n{'='*70}")
            print(f"Kraunamas: {label} ({date_str})")
            print(f"{'='*70}")
            
            load_search_page(page, search_url, f"{label} ({date_str})")

            trips_106, trips_tm = extract_trips(page)
            all_trips_juragiai_kaunas[label] = {
                '106': trips_106,
                'tm': trips_tm
            }
        
        print(f"\n{'='*70}")
        print("ANALIZĖ - PERIODIŠKUMO NUSTATYMAS")
        print(f"{'='*70}\n")
        
        # =========================================================
        # ANALIZĖ: KAUNAS → JURAGIAI
        # =========================================================
        print("📊 KAUNAS → JURAGIAI:\n")
        
        # Analizuojame 106 maršrutą
        workday_times = set(t['departure'] for t in all_trips_kaunas_juragiai['Ketvirtadienis (darbo diena)']['106'])
        # Analizuojame 106 maršrutą
        workday_times = set(t['departure'] for t in all_trips_kaunas_juragiai['Ketvirtadienis (darbo diena)']['106'])
        saturday_times = set(t['departure'] for t in all_trips_kaunas_juragiai['Šeštadienis']['106'])
        sunday_times = set(t['departure'] for t in all_trips_kaunas_juragiai['Sekmadienis']['106'])
        weekend_times = saturday_times | sunday_times
        
        all_times = workday_times | weekend_times
        
        trips_with_periodicity = []
        for time in sorted(all_times):
            in_workday = time in workday_times
            in_weekend = time in weekend_times
            
            if in_workday and in_weekend:
                periodicity = 'ALL_DAYS'
                days_label = '1234567'
            elif in_workday:
                periodicity = 'WORKDAYS'
                days_label = '12345'
            else:
                periodicity = 'WEEKEND'
                days_label = 'ŠS'
            
            # Randame trip objektą
            trip_obj = None
            if in_workday:
                trip_obj = next((t for t in all_trips_kaunas_juragiai['Ketvirtadienis (darbo diena)']['106'] if t['departure'] == time), None)
            elif in_weekend:
                trip_obj = next((t for t in all_trips_kaunas_juragiai['Šeštadienis']['106'] if t['departure'] == time), None)
            
            if trip_obj:
                trips_with_periodicity.append({
                    **trip_obj,
                    'periodicity': periodicity,
                    'days_label': days_label
                })
        
        print(f"106 maršrutas:")
        print(f"  Darbo dienomis (Pr-Pn): {len(workday_times)} reisai")
        print(f"  Savaitgaliais (Š-S): {len(weekend_times)} reisai")
        print(f"  Kasdien: {len([t for t in trips_with_periodicity if t['periodicity'] == 'ALL_DAYS'])} reisai")
        
        # Analogiškai tarpmiestiniams
        workday_tm = set(t['departure'] for t in all_trips_kaunas_juragiai['Ketvirtadienis (darbo diena)']['tm'])
        weekend_tm = set(t['departure'] for t in all_trips_kaunas_juragiai['Šeštadienis']['tm']) | set(t['departure'] for t in all_trips_kaunas_juragiai['Sekmadienis']['tm'])
        
        all_tm_times = workday_tm | weekend_tm
        
        tm_with_periodicity = []
        for time in sorted(all_tm_times):
            in_workday = time in workday_tm
            in_weekend = time in weekend_tm
            
            if in_workday and in_weekend:
                periodicity = 'ALL_DAYS'
                days_label = '1234567'
            elif in_workday:
                periodicity = 'WORKDAYS'
                days_label = '12345'
            else:
                periodicity = 'WEEKEND'
                days_label = 'ŠS'
            
            trip_obj = None
            if in_workday:
                trip_obj = next((t for t in all_trips_kaunas_juragiai['Ketvirtadienis (darbo diena)']['tm'] if t['departure'] == time), None)
            elif in_weekend:
                trip_obj = next((t for t in all_trips_kaunas_juragiai['Šeštadienis']['tm'] if t['departure'] == time), None)
            
            if trip_obj:
                tm_with_periodicity.append({
                    **trip_obj,
                    'periodicity': periodicity,
                    'days_label': days_label
                })
        
        print(f"\nTarpmiestiniai:")
        print(f"  Darbo dienomis (Pr-Pn): {len(workday_tm)} reisai")
        print(f"  Savaitgaliais (Š-S): {len(weekend_tm)} reisai")
        print(f"  Kasdien: {len([t for t in tm_with_periodicity if t['periodicity'] == 'ALL_DAYS'])} reisai")
        
        # =========================================================
        # ANALIZĖ: JURAGIAI → KAUNAS
        # =========================================================
        print("\n📊 JURAGIAI → KAUNAS:\n")
        
        # 106 maršrutas
        workday_times_jk = set(t['departure'] for t in all_trips_juragiai_kaunas['Ketvirtadienis (darbo diena)']['106'])
        saturday_times_jk = set(t['departure'] for t in all_trips_juragiai_kaunas['Šeštadienis']['106'])
        sunday_times_jk = set(t['departure'] for t in all_trips_juragiai_kaunas['Sekmadienis']['106'])
        weekend_times_jk = saturday_times_jk | sunday_times_jk
        
        all_times_jk = workday_times_jk | weekend_times_jk
        
        trips_jk_with_periodicity = []
        for time in sorted(all_times_jk):
            in_workday = time in workday_times_jk
            in_weekend = time in weekend_times_jk
            
            if in_workday and in_weekend:
                periodicity = 'ALL_DAYS'
                days_label = '1234567'
            elif in_workday:
                periodicity = 'WORKDAYS'
                days_label = '12345'
            else:
                periodicity = 'WEEKEND'
                days_label = 'ŠS'
            
            trip_obj = None
            if in_workday:
                trip_obj = next((t for t in all_trips_juragiai_kaunas['Ketvirtadienis (darbo diena)']['106'] if t['departure'] == time), None)
            elif in_weekend:
                trip_obj = next((t for t in all_trips_juragiai_kaunas['Šeštadienis']['106'] if t['departure'] == time), None)
            
            if trip_obj:
                trips_jk_with_periodicity.append({
                    **trip_obj,
                    'periodicity': periodicity,
                    'days_label': days_label
                })
        
        print(f"106 maršrutas:")
        print(f"  Darbo dienomis (Pr-Pn): {len(workday_times_jk)} reisai")
        print(f"  Savaitgaliais (Š-S): {len(weekend_times_jk)} reisai")
        print(f"  Kasdien: {len([t for t in trips_jk_with_periodicity if t['periodicity'] == 'ALL_DAYS'])} reisai")
        
        # Tarpmiestiniai
        workday_tm_jk = set(t['departure'] for t in all_trips_juragiai_kaunas['Ketvirtadienis (darbo diena)']['tm'])
        weekend_tm_jk = set(t['departure'] for t in all_trips_juragiai_kaunas['Šeštadienis']['tm']) | set(t['departure'] for t in all_trips_juragiai_kaunas['Sekmadienis']['tm'])
        
        all_tm_times_jk = workday_tm_jk | weekend_tm_jk
        
        tm_jk_with_periodicity = []
        for time in sorted(all_tm_times_jk):
            in_workday = time in workday_tm_jk
            in_weekend = time in weekend_tm_jk
            
            if in_workday and in_weekend:
                periodicity = 'ALL_DAYS'
                days_label = '1234567'
            elif in_workday:
                periodicity = 'WORKDAYS'
                days_label = '12345'
            else:
                periodicity = 'WEEKEND'
                days_label = 'ŠS'
            
            trip_obj = None
            if in_workday:
                trip_obj = next((t for t in all_trips_juragiai_kaunas['Ketvirtadienis (darbo diena)']['tm'] if t['departure'] == time), None)
            elif in_weekend:
                trip_obj = next((t for t in all_trips_juragiai_kaunas['Šeštadienis']['tm'] if t['departure'] == time), None)
            
            if trip_obj:
                tm_jk_with_periodicity.append({
                    **trip_obj,
                    'periodicity': periodicity,
                    'days_label': days_label
                })
        
        print(f"\nTarpmiestiniai:")
        print(f"  Darbo dienomis (Pr-Pn): {len(workday_tm_jk)} reisai")
        print(f"  Savaitgaliais (Š-S): {len(weekend_tm_jk)} reisai")
        print(f"  Kasdien: {len([t for t in tm_jk_with_periodicity if t['periodicity'] == 'ALL_DAYS'])} reisai")
        
        # Išsaugome failus
        print(f"\n{'='*70}")
        print("IŠSAUGOJIMAS")
        print(f"{'='*70}\n")
        
        output_dir = Path(__file__).parent.parent / 'web'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Kaunas → Juragiai
        if trips_with_periodicity:
            md_106 = format_106_with_periodicity(trips_with_periodicity, "Kaunas → Juragiai")
            file_106 = output_dir / '106_kaunas-juragiai_pilnas.md'
            with open(file_106, 'w', encoding='utf-8') as f:
                f.write(md_106)
            print(f"✓ Kaunas→Juragiai (106): {file_106.name}")
        
        if tm_with_periodicity:
            md_tm = format_tm_with_periodicity(tm_with_periodicity, "Kaunas → Marijampolė/Vilkaviškis (per Juragius)")
            file_tm = output_dir / 'tarpmiestiniai_kaunas-juragiai_pilnas.md'
            with open(file_tm, 'w', encoding='utf-8') as f:
                f.write(md_tm)
            print(f"✓ Kaunas→Juragiai (TM):  {file_tm.name}")
        
        # Juragiai → Kaunas
        if trips_jk_with_periodicity:
            md_106_jk = format_106_with_periodicity(trips_jk_with_periodicity, "Juragiai → Kaunas")
            file_106_jk = output_dir / '106_juragiai-kaunas_pilnas.md'
            with open(file_106_jk, 'w', encoding='utf-8') as f:
                f.write(md_106_jk)
            print(f"✓ Juragiai→Kaunas (106): {file_106_jk.name}")
        
        if tm_jk_with_periodicity:
            md_tm_jk = format_tm_with_periodicity(tm_jk_with_periodicity, "Marijampolė/Vilkaviškis → Kaunas (per Juragius)")
            file_tm_jk = output_dir / 'tarpmiestiniai_juragiai-kaunas_pilnas.md'
            with open(file_tm_jk, 'w', encoding='utf-8') as f:
                f.write(md_tm_jk)
            print(f"✓ Juragiai→Kaunas (TM):  {file_tm_jk.name}")
        
        browser.close()
        
        print("\n✓ Baigta!\n")


if __name__ == '__main__':
    main()
