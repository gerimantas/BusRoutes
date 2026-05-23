# BusRoutes — Kaunas ↔ Juragiai / Jurginiškiai

Mobile-optimized, premium, and highly accessible bus schedule PWA for the Kaunas ↔ Juragiai / Jurginiškiai (Route 106) suburban bus line.

**Live application:** https://gerimantas.github.io/BusRoutes/grafikai.html

---

## 🌟 Premium & Modern Features

*   **🌐 Geolocation-based Auto-Routing:** The app automatically calculates the user's distance (using the Haversine formula) to Kaunas Bus Station and Juragiai on load. It instantly activates the correct direction tab (Kaunas → Juragiai or Juragiai → Kaunas) without requiring manual interaction.
*   **📳 Tactile Vibration Alerts:** When a user is viewing the active route tab and the countdown to the nearest departure reaches **≤ 2 minutes**, the device emits a physical double-pulse vibration pattern (`[200ms vibrate, 100ms pause, 200ms vibrate]`) to signal that it is time to depart.
*   **🎨 Dynamic Route-Theme Neon Glows:**
    *   **Kaunas → Juragiai:** Gilus tamsiai mėlynas fonas (`#061220`) su šviesiai mėlynu neoniniu švytėjimu, o laiko juosta (header) sklandžiai nusidažo gilia mėlyna (`#0a1727`) su žydru neoniniu oreolu ir šviečiančiu laikrodžiu.
    *   **Juragiai → Kaunas:** Gilus gintarinis/ruda fonas (`#140a00`) su oranžiniu neoniniu švytėjimu, o laiko juosta sklandžiai nusidažo gintaro spalva (`#1c0f00`) su gintariniu neoniniu oreolu ir šviečiančiu laikrodžiu.
    *   *Transitions:* Changing directions triggers a gorgeous **0.3-second fade transition** across borders, shadows, and backgrounds.
*   **👁️ High legibility & Accessibility (WCAG 2.1 AA/AAA):**
    *   Large, highly readable indicators and custom platform badges (`5a`, `6a`, `12a`, `106`, `tm`) optimized for low-vision users.
    *   Pre-selected high-contrast palette yielding **>7:1 to >15:1 WCAG contrast ratios** (e.g. bold amber weekend indicator dots `6-7` yielding a high **6.66:1** contrast).
    *   All UI texts are uppercase for maximum legibility.
*   **🚦 Smart State-Based Filtering:** The filter button dynamically displays the current schedule constraints (showing **`1-5`**, **`6-7`**, or **`ND`** for holidays). When turned OFF, it displays **`1-7`** (all times), turns the header deep crimson red (`#180909`), and illuminates a rich red alert aura to warn the user.
*   **📅 Zero-Maintenance Holiday Engine:** Incorporates a dynamic year-transition calendar detector. It automatically calculates all 14 official Lithuanian holidays and employs the **Gauss easter algorithm** to automatically map Easter Sunday and Monday for any future year dynamically—requiring absolutely no manual yearly updates.
*   **🚀 Layout Scroll Safety:** Features a custom `scrollToNext()` helper with reflow-tolerant timeouts and a safe `80vh` body padding-bottom, guaranteeing that the `ARTIMIAUSIAS` (nearest) card is perfectly positioned exactly `8px` below the fixed header under all layout sizes, even during shorter weekend lists.
*   **⚡ CPU & DOM Efficiency:** Paired rendering directly inside HTML generation cycles to eliminate unnecessary date calculations, saving battery and keeping performance exceptionally smooth.
*   **📲 Progressive Web App (PWA):** Installs natively to Android/iOS home screens, caches all icons locally, works 100% offline, and automatically reloads the page in the background when a new service worker version is waiting.

---

## 🕒 Schedule Structure

| Route | Trips/day (Workdays) | Trips/day (Weekends) |
|---|---|---|
| **Kaunas → Juragiai** | 20 | 6 |
| **Juragiai → Kaunas** | 21 | 6 |

*Source PDFs: `kaunas-juragiai_0522.pdf`, `juragiai-kaunas_0522.pdf` (Verified 2026-05-22)*

---

## 🛠️ Update & Deployment Workflow

1.  **Modify schedule data:** Update the `dataKaunas` or `dataJurginiskai` arrays directly inside `grafikai.html`.
2.  **Bump the service worker version:** Open `sw.js` and bump the cache name (e.g., `const CACHE = 'tvarkarastis-v9'`).
3.  **Push to GitHub:**
    ```powershell
    git add grafikai.html sw.js
    git commit -m "update: describe your changes"
    git push
    ```
    *The GitHub Pages action will automatically build and publish the changes within 30 seconds. Next time the user opens the PWA, it will instantly fetch the update and reload the page fone.*

---

## 📁 File Structure

| File | Purpose |
|---|---|
| [grafikai.html](file:///C:/Users/retco/Projects/Grafikai/grafikai.html) | Single-file PWA — holds all HTML structure, premium CSS design, and JavaScript core logic. |
| [sw.js](file:///C:/Users/retco/Projects/Grafikai/sw.js) | Cache-first Service Worker providing robust offline support. |
| [manifest.json](file:///C:/Users/retco/Projects/Grafikai/manifest.json) | PWA configuration for mobile installation. |
| `icon-192.png` / `icon-512.png` | Native PWA application icons. |
| [kaunas-juragiai_grafikas.md](file:///C:/Users/retco/Projects/Grafikai/kaunas-juragiai_grafikas.md) | Canonical Markdown schedule source (Kaunas → Juragiai). |
| [juragiai-kaunas_grafikas.md](file:///C:/Users/retco/Projects/Grafikai/juragiai-kaunas_grafikas.md) | Canonical Markdown schedule source (Juragiai → Kaunas). |
