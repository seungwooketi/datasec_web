# ADSRC identity assets

Master geometry lives in the SVGs. Everything else is generated from them.

## Symbol

| File | Use |
| --- | --- |
| `adsrc-symbol.svg` | Standard. 24px and above. Stroke 2.5 units. |
| `adsrc-symbol-small.svg` | 17-24px. Stroke 4 units. |
| `adsrc-symbol-16.svg` | 16px only. Stroke 5 units. |
| `adsrc-symbol-graphite.svg` | One-colour graphite (#1D1F20) for mono print. |
| `adsrc-symbol-reverse.svg` | Paper white, for dark grounds. |

The three stroke weights are separate drawings, not scaled copies. Scaling the
standard file down to 16px makes the lines vanish. Pick the file that matches
the size you are placing.

## Favicons and app icons

`favicon-16/32/48/64.png`, `apple-touch-icon-180.png`, `icon-512.png`,
`icon-512-dark.png`. Transparent background except the touch/app icons, which
sit on deep steel #1D2D3D.

```html
<link rel="icon" href="/assets/brand/adsrc-symbol-16.svg" type="image/svg+xml">
<link rel="icon" href="/assets/brand/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon-180.png">
```

## Lockups on the web

The wordmark is live type, not artwork — set it in Barlow Condensed 600 beside
the inline symbol. This keeps it crisp at any density, searchable, and
translatable. Do not export the lockup as a PNG for the site header.

```html
<a class="brand" href="/en/">
  <svg viewBox="0 0 48 48" width="32" height="32" aria-hidden="true">
    <g fill="none" stroke="#5980A6" stroke-width="4">
      <rect x="7" y="7" width="22" height="22"/><rect x="19" y="19" width="22" height="22"/>
    </g>
    <rect x="19" y="19" width="10" height="10" fill="#5980A6"/>
  </svg>
  <span class="brand-text">
    <b>ADSRC</b>
    <em>AI Data and Security Research Center</em>
  </span>
</a>
```

```css
.brand { display: flex; align-items: center; gap: 13px; text-decoration: none; color: #1D1F20; }
.brand-text { border-left: 1px solid rgba(29,31,32,.16); padding-left: 13px; }
.brand-text b { display: block; font: 600 24px/.86 "Barlow Condensed", sans-serif; letter-spacing: .03em; }
.brand-text em { display: block; margin-top: 5px; font: 500 6px/1 "Barlow", sans-serif;
                 letter-spacing: .07em; font-style: normal; white-space: nowrap; color: rgba(29,31,32,.6); }
```

`white-space: nowrap` on the descriptor is not optional. It is a fixed brand
element; if it wraps, the lockup is broken.

## Rendered artwork

`hero.png` (2400 × 1792, 2× of 1200 × 896) replaces the current `hero.jpg` —
the eight research topics drawn as the set diagram the symbol is built from:
data and security as two overlapping fields, with Reliable AI — the goal, not
a topic — named in the intersection. Icons are thin-stroke at 1.5, matching the frame weight. Redraw it from `ADSRC Assets.dc.html` if the areas change.

`og-image.png` (1200 × 630, deep steel) is the social/preview card — point
`og:image` at it. `adsrc-lockup-horizontal.png` (3600 × 900) is the primary
lockup at 3× for slides, Word documents and print proofs. Use it where live
type is not available; never in the site header.

## Colour

| | Hex | Use |
| --- | --- | --- |
| Steel | #5980A6 | Symbol, accent rules, primary buttons |
| Graphite | #1D1F20 | Wordmark, body copy, rules |
| Deep steel | #1D2D3D | Reverse ground: covers, OG cards, banners |

Steel measures ~3.6:1 against the light ground — fine for the symbol, large
type and chrome, not for body copy. Use #416180 where running text must be blue.

## Print masters

Outline the wordmark once in a vector editor and keep that file as the print
master, so nothing depends on Barlow Condensed being installed at a printer.
PANTONE 5425 C is a screen-derived approximation; match a physical chip first.
