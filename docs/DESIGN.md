## Design System: wm-dashboard

### Pattern
- **Name:** Real-Time / Operations Landing
- **Conversion Focus:** For ops/security/iot products. Demo or sandbox link. Trust signals.
- **CTA Placement:** Primary CTA in nav + After metrics
- **Color Strategy:** Dark or neutral. Status colors (green/amber/red). Data-dense but scannable.
- **Sections:** 1. Hero (product + live preview or status), 2. Key metrics/indicators, 3. How it works, 4. CTA (Start trial / Contact)

### Style
- **Name:** Data-Dense Dashboard
- **Mode Support:** Light ✓ Full | Dark ✓ Full
- **Keywords:** Multiple charts/widgets, data tables, KPI cards, minimal padding, grid layout, space-efficient, maximum data visibility
- **Best For:** Business intelligence dashboards, financial analytics, enterprise reporting, operational dashboards, data warehousing
- **Performance:** ⚡ Excellent | **Accessibility:** ✓ WCAG AA

### Colors
| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#1E40AF` | `--color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` |
| Secondary | `#3B82F6` | `--color-secondary` |
| Accent/CTA | `#D97706` | `--color-accent` |
| Background | `#F8FAFC` | `--color-background` |
| Foreground | `#1E3A8A` | `--color-foreground` |
| Muted | `#E9EEF6` | `--color-muted` |
| Border | `#DBEAFE` | `--color-border` |
| Destructive | `#DC2626` | `--color-destructive` |
| Ring | `#1E40AF` | `--color-ring` |

*Notes: Blue data + amber highlights [Accent adjusted from #F59E0B for WCAG 3:1]*

### Typography
- **Heading:** Fira Code
- **Body:** Fira Sans
- **Mood:** dashboard, data, analytics, code, technical, precise
- **Best For:** Dashboards, analytics, data visualization, admin panels
- **Google Fonts:** https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap
- **CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```

### Key Effects
Hover tooltips, chart zoom on click, row highlighting on hover, smooth filter animations, data loading spinners

### Avoid (Anti-patterns)
- Ornate design
- No filtering

### Pre-Delivery Checklist
- [ ] No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] cursor-pointer on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard nav
- [ ] prefers-reduced-motion respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px


---

## Realized Tokens for wm-dashboard (Dark-first override)

Die Skill-Palette oben ist Light-Mode. Unser Dashboard läuft aber Dark-first (Handy-Nutzung, Wettmarkt-Kontext). Untenstehende Tokens sind die auf **Financial-Dashboard**-Palette (colors.csv Result 2) angepasste Dark-Variante, die im `style.css` aus Option 1 landet.

### Dark Tokens

| Role | Hex | Verwendung im Dashboard |
|------|-----|-------------------------|
| `--bg` | `#020617` | Seiten-Hintergrund |
| `--soft` | `#0E1223` | Header, Disclaimer, Sticky-Nav |
| `--panel` | `#0E1223` | Karten |
| `--panel2` | `#1A1E2F` | Tags/Chips-Hintergrund |
| `--line` | `#334155` | Karten-Rahmen |
| `--line2` | `#1F2A44` | Tabellen-Trennlinien |
| `--tx` | `#F8FAFC` | Titel |
| `--body` | `#E2E8F0` | Fließtext |
| `--dim` | `#94A3B8` | Meta/Labels |
| `--acc` | `#3B82F6` | Primär-Fokus, Markt-Linien |
| `--accent` | `#F59E0B` | Refresh-Button, Whale-Signal |
| `--good` | `#22C55E` | Trefferbilanz richtig, EV positiv |
| `--bad` | `#EF4444` | Trefferbilanz falsch, EV negativ |
| `--focus` | `#F8D66D` | Tastatur-Fokus-Ring |

### Chart-Semantik (getrennt von Status)

| Serie | Hex | Style |
|-------|-----|-------|
| Markt | `#3B82F6` (`--m1`) | solid |
| Modell | `#8B5CF6` (`--m2`) | dashed 5 5 |
| Whale | `#F59E0B` (`--m3`) | solid |
| Confidence-Band 5-95 % | `#8B5CF6` fill-opacity 0.2 | Filled area |
| Anomalie-Marker | `#F59E0B` | Circle r=4 |

### Warum getrennte Semantik

Vorher war `--good` und `--m2` (Modell-Linie) beide `#34d399` — ein grüner Modell-Peak sah aus wie „Trefferbilanz richtig". Neu: Modell-Linien sind lila-dashed, richtig/falsch bleiben grün/rot. Kein Wechsel des mentalen Modells beim Scrollen zwischen Sektionen.

### Kritikalität-Level (aus AGENTS.md „money-facing" Bar)

Diese Spec ist **UI-only** — sie ändert weder `value_betting` noch `ensemble` noch `monte_carlo` und läuft an `pytest quality/test_functional.py tests/test_model.py` vorbei ohne Impact. Sicherheits-Caps (stake, liquidity, correlation) bleiben unberührt.
