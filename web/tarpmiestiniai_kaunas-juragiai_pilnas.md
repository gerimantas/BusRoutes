# Tarpmiestiniai autobusai per Juragius (PILNAS TVARKARAŠTIS)

Šaltinis: `autobusubilietai.lt`  
Kryptis: Kaunas → Marijampolė/Vilkaviškis (per Juragius)

Periodiškumas nustatytas lyginant ketvirtadienį, šeštadienį ir sekmadienį.

## Tvarkaraštis

| Kaunas | Juragiai | Maršrutas | Vežėjas | Periodiškumas | Dienos | Platforma | Kaina |
|--------|----------|-----------|---------|---------------|--------|-----------|-------|
| 05:00 | ? | 05:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 06:00 | ? | 06:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 08:00 | ? | 08:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 09:00 | ? | 09:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 10:00 | ? | 10:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 11:00 | ? | 11:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 11:35 | 11:57 | 11:35 - 11:57Trukmė:  22  min.Kaunas - Marijampolė | Kautra Plius | ALL_DAYS | 1234567 | tm | 32,00 € |
| 12:00 | ? | 12:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 12:40 | 13:04 | 12:40 - 13:04Trukmė:  24  min.Kaunas - Marijampolė | Kautra | ALL_DAYS | 1234567 | tm | 1,80 € |
| 13:00 | ? | 13:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 14:00 | ? | 14:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 15:00 | ? | 15:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 16:00 | ? | 16:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 16:50 | 17:12 | 16:50 - 17:12Trukmė:  22  min.Kaunas - Marijampolė | Kautra | ALL_DAYS | 1234567 | tm | 1,80 € |
| 17:00 | ? | 17:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 18:00 | ? | 18:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 18:10 | 20:24 | 18:10 - 20:24Trukmė: 2 val. 14  min.Kaunas - Jurag | Unknown | WEEKEND | ŠS | tm | ? € |
| 19:00 | ? | 19:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 19:25 | 09:28 | 19:25 - 09:28 (+1d)Trukmė: 14 val. 3  min.Kaunas - | Unknown | WEEKEND | ŠS | tm | 12,00 € |
| 21:00 | ? | 21:00 | Unknown | WORKDAYS | 12345 | tm | ? € |


**Statistika:**
- Tik darbo dienomis (Pr-Pn): 5 reisai
- Tik savaitgaliais (Š-S): 2 reisai
- Kasdien: 13 reisai
- **Iš viso:** 20 reisai

## Konvertavimas į grafikai.html formatą

Naudoti žymę `platform: "tm"` (tarpmiestinis = 12 aikštelė).

Pavyzdys:
```javascript
// Darbo dienomis (platforma tm = 12 aikštelė)
["06:00", WORKDAYS, "tm"],

// Kasdien
["05:00", ALL_DAYS, "tm"],
```
