# Brand Identity & Design System Guide

## 1. Brand Overview
**Core Philosophy**: "Simplicity meets Power."
Our brand embodies the intersection of professional reliability and modern ease-of-use. We provide tools that are robust enough for enterprise but accessible enough for startups. The visual language is clean, airy, and data-forward, utilizing soft gradients and crisp typography to convey clarity.

**Voice & Tone**:
- **Confident but Humble**: We know our value, but we don't shout.
- **Clear & Direct**: We avoid jargon. We get straight to the point.
- **Optimistic**: We focus on growth, solutions, and the future.
- **Human**: We speak to people, not corporations.

---

## 2. Logo Guidelines
*Note: These guidelines apply to the primary brand logo (e.g., "Eden", "Trendex").*

### Clear Space
Always maintain a minimum clear space around the logo equivalent to the height of the "Icon" mark (x). This ensures legibility and impact.

### Minimum Size
- **Digital**: 24px height.
- **Print**: 0.5 inches height.

### Incorrect Usage
- **Do NOT** rotate the logo.
- **Do NOT** add drop shadows or outlines to the logo.
- **Do NOT** place the logo on busy backgrounds without sufficient contrast.
- **Do NOT** change the logo colors outside of the approved palette.

---

## 3. Color Palette
The palette combines a trustworthy deep navy with vibrant accents (emerald and electric blue) and soft, humanizing pastels.

### Primary Colors
| Color Name | Hex | Usage | Text Color |
| :--- | :--- | :--- | :--- |
| **Deep Navy** | `#0F172A` | Primary text, headings, footer backgrounds. | White |
| **Vibrant Emerald** | `#10B981` | Primary actions (CTAs), success states, growth indicators. | White |
| **Electric Blue** | `#3B82F6` | Secondary actions, links, active states. | White |

### Secondary & Accents
| Color Name | Hex | Usage | Text Color |
| :--- | :--- | :--- | :--- |
| **Soft Lime** | `#D9F99D` | Highlights, background accents. | Navy |
| **Pastel Pink** | `#FCE7F3` | Warmth, gradients, decorative blobs. | Navy |
| **Surface White** | `#FFFFFF` | Main background, card backgrounds. | Navy |
| **Off-White** | `#F8FAFC` | Section backgrounds, subtle separation. | Navy |
| **Border Gray** | `#E2E8F0` | Borders, dividers. | N/A |

### Gradients
- **Aurora**: `linear-gradient(135deg, #FCE7F3 0%, #E0F2FE 100%)` (Hero backgrounds).
- **Deep Space**: `linear-gradient(180deg, #0F172A 0%, #1E293B 100%)` (Dark headers).
- **Growth**: `linear-gradient(90deg, #10B981 0%, #34D399 100%)` (Success indicators).

---

## 4. Typography
We use a modern geometric sans-serif stack to ensure readability across all devices.

**Primary Font**: **Inter** (Google Fonts)
*Alternative: Plus Jakarta Sans*

### Type Hierarchy
| Element | Size (Desktop) | Weight | Line Height | Letter Spacing |
| :--- | :--- | :--- | :--- | :--- |
| **Display H1** | 64px | Extra Bold (800) | 1.1 | -0.02em |
| **H1** | 48px | Bold (700) | 1.2 | -0.01em |
| **H2** | 36px | Bold (700) | 1.25 | -0.01em |
| **H3** | 24px | SemiBold (600) | 1.3 | Normal |
| **H4** | 20px | SemiBold (600) | 1.4 | Normal |
| **Body Large** | 18px | Regular (400) | 1.6 | Normal |
| **Body Default** | 16px | Regular (400) | 1.6 | Normal |
| **Small / Caption** | 14px | Medium (500) | 1.5 | 0.01em |
| **Button Text** | 16px | SemiBold (600) | 1.0 | 0.01em |

---

## 5. Iconography & Illustration
### Icons
- **Style**: Line/Stroke icons (e.g., Phosphor Icons, Heroicons Outline).
- **Stroke Width**: 1.5px or 2px (consistent).
- **Corner Radius**: Rounded line caps and joins.
- **Usage**: Often placed inside a circle container with a soft pastel background matching the icon color.

### Illustration
- **Style**: 3D Abstract or "Glass" elements.
- **Vibe**: Modern, tech-forward, polished.
- **Usage**: Hero sections, feature highlights. Avoid generic "flat people" vectors.

---

## 6. UI Components & Layout
The interface is defined by "Card-based Design" with generous whitespace.

### Cards
- **Background**: White (`#FFFFFF`)
- **Border Radius**: `24px` (Large, friendly curves).
- **Shadow**: `0px 4px 24px rgba(0, 0, 0, 0.06)` (Soft, diffused shadow).
- **Border**: `1px solid #F1F5F9` (Subtle definition).
- **Padding**: `32px` (Internal spacing).

### Buttons
- **Primary**: 
  - Background: `#0F172A` (Navy) or `#10B981` (Emerald).
  - Text: White.
  - Radius: `100px` (Pill) for marketing, `12px` for app UI.
  - Hover: Lighten by 10% or slight lift (`transform: translateY(-1px)`).
- **Secondary**:
  - Background: Transparent.
  - Border: `1px solid #E2E8F0`.
  - Text: `#0F172A`.
  - Hover: Background `#F8FAFC`.

### Forms
- **Inputs**:
  - Height: `48px`.
  - Radius: `12px`.
  - Border: `1px solid #CBD5E1`.
  - Focus: Ring `2px` solid `#3B82F6` (Electric Blue).

---

## 7. Data Visualization
Charts must be clean, minimal, and easy to read.

- **Palette**: Use the brand palette.
  - Series A: `#10B981` (Emerald)
  - Series B: `#3B82F6` (Blue)
  - Series C: `#F59E0B` (Amber - Warning/Attention)
  - Series D: `#6366F1` (Indigo)
- **Style**:
  - Rounded bar ends.
  - Minimal grid lines (dashed, light gray).
  - Tooltips with white background and shadow.

---

## 8. Accessibility (A11y)
We are committed to building an inclusive web.

- **Contrast**: All text must meet WCAG AA standards (4.5:1 ratio).
- **Focus States**: Never remove default outline without providing a custom focus ring.
- **Alt Text**: All images must have descriptive alt text.
- **Semantic HTML**: Use proper heading structure (H1 -> H2 -> H3).
