# Grafikai — CONTEXT

## Purpose
Suburban bus schedule Kaunas ↔ Juragiai / Jurginiškiai (Route 106) — single-file PWA optimized for mobile, featuring high accessibility standards (WCAG 2.1 AA/AAA) and premium device integrations.

## URL & Repository
*   **Live App:** https://gerimantas.github.io/BusRoutes/grafikai.html
*   **Repository:** https://github.com/gerimantas/BusRoutes

## Technical Status
*   **Current Version:** **v4 (Dynamic Visuals & Premium Integrations)**
*   **Service Worker Cache:** **`tvarkarastis-v20`** (strictly bump cache version in `sw.js` on every HTML modification).

---

## 🛠️ Complete Feature Set

### 1. Navigation & Route Identifiers
*   **Dual Tab Routing:** Two distinct directions: Kaunas → Juragiai (Mėlyna/Blue theme) and Juragiai → Kaunas (Gintaras/Amber theme).
*   **Premium Header Themes:** The fixed top bar dynamically swaps classes (`theme-kaunas` / `theme-jurginiskai`) and applies a **0.3s fade-transition** across backgrounds, borders, and shadows:
    *   **Kaunas theme:** `#0a1727` background, `rgba(126, 200, 255, 0.6)` bottom border, and intense `rgba(126, 200, 255, 0.45)` neon drop shadow with blue glowing clock time text-shadow.
    *   **Juragiai theme:** `#1c0f00` background, `rgba(245, 158, 11, 0.6)` bottom border, and intense `rgba(245, 158, 11, 0.45)` neon drop shadow with amber glowing clock time text-shadow.
*   **Premium Geolocation Auto-Select:** Calculates distances to Kaunas Bus Station and Juragiai using the Haversine formula on load. Instantly switches active tabs if the user is physically closer to the other start point.

### 2. Time-Keeping & Alerts
*   **Clock Bar:** Contains a live clock, dynamic day indicators, and the filter toggle button.
*   **Tactile Vibration Alert:** Physically double-pulses the mobile device (`navigator.vibrate([200, 100, 200])`) when the user is looking at the active route tab and the countdown to the nearest departure reaches **≤ 2 minutes**.
*   **Buffer-Aware "Nearest" Trip:** High-contrast emerald green outline and `ARTIMIAUSIAS` label centered on the card border. The green highlight is kept active during the current minute (`timeToMinutes(time) * 60 + 59 >= nowSec`) so it never disappears prematurely.
*   **Visual Hierarchy:** Upcoming trips are displayed in a larger, high-contrast style (`padding: 20px 14px`, `.time { font-size: 34px }`). Past trips are dimmed but kept visible for next-day context.

### 3. Filters & Accessibility (WCAG 2.1 AA/AAA)
*   **Smart Filter Button:** Pre-calculates the active day index and displays a readable state badge (**`1-5`** for workdays, **`6-7`** for weekends, **`ND`** for holidays).
*   **Filter OFF Alert Aura:** Turning the filter OFF (displays **`1-7`**) changes the header to `#180909`, thickens the border-bottom, and projects a deep crimson red inset/outset warning shadow.
*   **High Contrast Elements:** Day dots (`6-7` weekend dots have a bold amber background with dark text yielding a high **6.66:1** contrast). All platform badges are expanded to `24px x 24px` with custom neon colors contrasting at **>7.0:1 – 9.0:1** ratios.
*   **All-Caps Style:** Global uppercase rule (`* { text-transform: uppercase; }`) for consistent, clear reading.

### 4. Resilient Layout
*   **Reflow-Safe Scrolling:** A customized `scrollToNext()` helper with safety checks (`rect.top !== 0 && rect.height !== 0`), dynamic `window.pageYOffset` positioning, and layout-tolerant `80ms` timeouts ensuring perfect positioning `8px` below the header.
*   **Padding-Bottom Buffer:** The body has `padding-bottom: 80vh;` to provide sufficient scrollable space, guaranteeing that even the very last trip of the day can always be scrolled to the top of the viewport.

### 5. Automated Calendar Engine
*   **Gauss Easter Calculator:** Solves for Easter Sunday and Easter Monday dynamically for any given year.
*   **Holiday Scheduler:** Auto-calculates all 14 statutory holidays (DK 160 str.), displays the holiday name in a red banner, and automatically applies the weekend (`ŠS`) schedule.
*   **Year Transitions:** Automatic calendar updater (`checkYearUpdate`) that re-runs when a new year begins.

---

## 📁 Files

| File | Path |
|---|---|
| Main PWA | [grafikai.html](file:///C:/Users/retco/Projects/Grafikai/grafikai.html) |
| Manifest | [manifest.json](file:///C:/Users/retco/Projects/Grafikai/manifest.json) |
| Service Worker | [sw.js](file:///C:/Users/retco/Projects/Grafikai/sw.js) |
| Source Kaunas | [kaunas-juragiai_grafikas.md](file:///C:/Users/retco/Projects/Grafikai/kaunas-juragiai_grafikas.md) |
| Source Juragiai | [juragiai-kaunas_grafikas.md](file:///C:/Users/retco/Projects/Grafikai/juragiai-kaunas_grafikas.md) |

---

## 🚀 Deployment & Updates
1.  Verify data changes locally.
2.  Increment the `CACHE` name in `sw.js` (e.g. `tvarkarastis-v20`).
3.  Commit and push to `main` branch.
4.  GitHub Pages will build and deploy. Client browsers will automatically detect the new service worker version, fetch the fresh cache, and perform a background page refresh to make the changes live.
