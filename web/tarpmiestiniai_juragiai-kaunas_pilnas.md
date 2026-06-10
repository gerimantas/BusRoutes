# Tarpmiestiniai autobusai per Juragius (PILNAS TVARKARAŠTIS)

Šaltinis: `autobusubilietai.lt`  
Ištraukta: `2026-06-10`  
Kryptis: Marijampolė/Vilkaviškis → Kaunas (per Juragius)

Periodiškumas nustatytas lyginant ketvirtadienį, šeštadienį ir sekmadienį.

## Tvarkaraštis

| Kaunas | Juragiai | Maršrutas | Vežėjas | Periodiškumas | Dienos | Platforma | Kaina |
|--------|----------|-----------|---------|---------------|--------|-----------|-------|
| 06:00 | ? | 06:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 07:00 | ? | 07:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 08:00 | ? | 08:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 09:00 | ? | 09:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 09:28 | 09:50 | 09:28 - 09:50Trukmė:  22  min.Vilkaviškis - Marija | Kautra | ALL_DAYS | 1234567 | tm | 1,80 € |
| 10:00 | ? | 10:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 11:00 | ? | 11:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 11:06 | 11:30 | 11:06 - 11:30Trukmė:  24  min.Marijampolė - Kaunas | Marijampolės AP | ALL_DAYS | 1234567 | tm | 2,10 € |
| 12:00 | ? | 12:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 14:00 | ? | 14:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 14:48 | 15:10 | 14:48 - 15:10Trukmė:  22  min.Vilkaviškis - Marija | Kautra Plius | ALL_DAYS | 1234567 | tm | 32,00 € |
| 15:00 | ? | 15:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 16:00 | ? | 16:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 17:00 | ? | 17:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 17:06 | 17:30 | 17:06 - 17:30Trukmė:  24  min.Vilkaviškis - Marija | Kautra | ALL_DAYS | 1234567 | tm | 1,80 € |
| 17:12 | 19:15 | 17:12 - 19:15Trukmė: 2 val. 3  min.Juragiai - Kaun | Unknown | WEEKEND | ŠS | tm | 12,00 € |
| 18:00 | ? | 18:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 19:00 | ? | 19:00 | Unknown | WORKDAYS | 12345 | tm | ? € |
| 20:00 | ? | 20:00 | Unknown | ALL_DAYS | 1234567 | tm | ? € |
| 20:24 | 20:45 | 20:24 - 20:45Trukmė:  21  min.Vištytis - Kybartai  | Kautra | ALL_DAYS | 1234567 | tm | 1,80 € |


**Statistika:**
- Tik darbo dienomis (Pr-Pn): 6 reisai
- Tik savaitgaliais (Š-S): 1 reisai
- Kasdien: 13 reisai
- **Iš viso:** 20 reisai

## Konvertavimas į grafikai.html formatą

Naudoti žymę `platform: "tm"` (tarpmiestinis = 12 aikštelė).

Pavyzdys:
```javascript
// Darbo dienomis (platforma tm = 12 aikštelė)
["06:00", WORKDAYS, "tm"],

// Kasdien
["07:00", ALL_DAYS, "tm"],
```
