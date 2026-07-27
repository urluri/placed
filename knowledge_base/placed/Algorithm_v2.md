# Placed Algorithm v2

## 1. Product Goal

Placed helps a user choose a framing specification for an artwork when the user does not know which frame, mat, glass, and sizes are appropriate.

The service receives:

- an uploaded image;
- physical artwork dimensions;
- artwork type;
- interior style or a universal fallback;
- optional visual crop / visible image area.

The service returns three decoration variants:

- `standard` - safe, workshop-friendly, neutral framing;
- `modern` - more contemporary and expressive, but still practical;
- `signature` - the most distinctive variant, allowed to use double mat or accent details.

The result is not just a visual preview. The core output is a specification that a user can bring to a framing workshop.

## 2. Core Principle

The algorithm must separate three layers:

1. **Hard constraints**
   Rules that cannot be violated: glass requirements, no mat for canvas, shadow box for volumetric objects, minimum frame depth, physical size limits.

2. **Geometry**
   Calculations of mat margins, frame width, overlap, final outer size, and visible window size.

3. **Aesthetic strategy**
   Selection of mat color, frame color/material, and decor style based on image analysis and user context.

Hard constraints always override aesthetic choices.

## 3. Terminology

Use these names consistently in code and documentation.

| Term | Meaning |
| --- | --- |
| `artwork` | Physical object that the user brings to framing: paper, poster, photo, canvas, embroidery, etc. |
| `image_content` | The visual content inside the uploaded image. Used for color and occupancy analysis. |
| `artwork_width_mm` | Full physical width of the artwork. |
| `artwork_height_mm` | Full physical height of the artwork. |
| `visible_width_mm` | Optional visible image area if the artwork has white borders or margins. |
| `visible_height_mm` | Optional visible image area if the artwork has white borders or margins. |
| `mat` | Passepartout. |
| `mat_window` | Hole/window cut in the mat. |
| `frame` | Visible frame/baguette profile. |
| `outer_size` | Final framed object size. |

## 4. Input Contract

### Required User Inputs

```json
{
  "image": "uploaded file",
  "artwork_width_mm": 300,
  "artwork_height_mm": 400,
  "artwork_type": "poster",
  "interior_style": "minimal"
}
```

### Optional User Inputs

```json
{
  "visible_width_mm": 280,
  "visible_height_mm": 380,
  "preferred_mood": "calm",
  "budget_level": "standard",
  "avoid_glass": false
}
```

### Enumerations

```python
class ArtworkType(str, Enum):
    watercolor = "watercolor"
    photo = "photo"
    poster = "poster"
    canvas = "canvas"
    embroidery = "embroidery"
    volumetric = "volumetric"


class InteriorStyle(str, Enum):
    minimal = "minimal"
    scandi = "scandi"
    japandi = "japandi"
    contemporary = "contemporary"
    loft = "loft"
    modern_vintage = "modern_vintage"
    neoclassic = "neoclassic"
    universal = "universal"


class DecorStyle(str, Enum):
    standard = "standard"
    modern = "modern"
    signature = "signature"


class SizeProfile(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"
    extra_large = "extra_large"


class Tonality(str, Enum):
    light = "light"
    medium = "medium"
    dark = "dark"


class Temperature(str, Enum):
    warm = "warm"
    neutral = "neutral"
    cool = "cool"


class ChromaLevel(str, Enum):
    muted = "muted"
    medium = "medium"
    vivid = "vivid"


class Occupancy(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
```

## 5. Internal Data Types

### Color

Do not store important colors only as `HEX`. `HEX` and `RGB` are useful for UI, but not enough for matching real mat colors.

Use `CIELAB` as the canonical matching model and keep `RGB/HEX` for display.

Reasons:

- Lab is closer to human color perception than RGB.
- It supports meaningful color distance via Delta E.
- It can be matched against physical catalogs from mat suppliers.
- It remains vendor-independent.

```python
@dataclass
class ColorSample:
    hex: str
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    family: str              # white, warm_white, grey, black, beige, brown, blue...
    temperature: Temperature
    lightness: Tonality
    chroma_level: ChromaLevel
    chroma: float
    share: float             # 0..1 share in the analyzed image
```

### Image Palette

```python
@dataclass
class ImagePalette:
    primary: ColorSample
    secondary: ColorSample | None
    accent: ColorSample | None
    is_monochrome: bool
    temperature: Temperature
    lightness: Tonality
    chroma_level: ChromaLevel
```

### Mat Catalog Color

The algorithm should not output an abstract color like `"ivory"` unless there is no catalog yet. It should output a concrete catalog item.

In MVP, create a small internal catalog. Later it can be replaced by a real supplier catalog.

```python
@dataclass
class MatColor:
    id: str                  # internal id or supplier code
    name: str                # "Warm White", "Ivory", "Graphite"
    hex: str
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    family: str
    temperature: Temperature
    lightness: Tonality
    chroma_level: ChromaLevel
    available: bool = True
```

### Frame Catalog Item

```python
@dataclass
class FrameOption:
    id: str
    name: str
    material: str            # wood, aluminum
    color_family: str        # oak, black, graphite, walnut, gold...
    width_mm: int
    depth_mm: int | None
    profile: str             # flat, box, l_shape, gallery_box
    available: bool = True
```

### Decoration Specification

```python
@dataclass
class DecorationSpec:
    decor_style: DecorStyle
    artwork_type: ArtworkType
    frame: FrameOption
    mat: MatSpec | None
    glass: GlassSpec | None
    shadow_box: bool
    geometry: GeometrySpec
    reasons: list[str]
    warnings: list[str]
```

## 6. Image Analysis

### 6.1 Preprocessing

1. Load uploaded image.
2. Convert to sRGB.
3. Resize to analysis size, for example `512px` on the longest side.
4. Remove fully transparent pixels if image has alpha.
5. Optionally ignore a thin outer border, for example 2-4%, to reduce frame/photo-edge artifacts.
6. If user provides visible area, analyze that area preferentially.

### 6.2 Extract Palette

Use clustering in Lab space.

Suggested MVP approach:

1. Convert sampled pixels from RGB to Lab.
2. Run k-means or median-cut clustering with `k = 5..8`.
3. Remove clusters with extremely low share, unless they are vivid enough to become an accent.
4. Sort clusters by share and perceptual importance.

Definitions:

- `primary` - largest meaningful cluster, excluding near-white/near-black border noise when necessary.
- `secondary` - next stable cluster with enough share and distance from primary.
- `accent` - smaller cluster with high chroma or strong contrast. It does not need to be large.

Accent score:

```text
accent_score = chroma * 0.55 + contrast_to_primary * 0.30 + share * 0.15
```

Only accept accent if:

```text
share >= 0.03
chroma_level != muted
delta_e(accent, primary) >= 18
```

If no such color exists, `accent = None`.

### 6.3 Derived Image Properties

Use Lab:

```text
L = lightness, 0..100
a = green-red axis
b = blue-yellow axis
chroma = sqrt(a*a + b*b)
```

Lightness:

```text
average L >= 68 -> light
average L <= 38 -> dark
else -> medium
```

Temperature:

```text
average b >= 7 -> warm
average b <= -7 -> cool
else -> neutral
```

Chroma:

```text
average chroma < 14 -> muted
average chroma > 34 -> vivid
else -> medium
```

Monochrome:

```text
average chroma < 8
and max important cluster chroma < 14
```

### 6.4 Frame Occupancy

`frame_occupancy` estimates how visually dense the artwork is near its edges. This matters because busy images often need less mat or a stronger visual boundary.

MVP calculation:

1. Divide the image into center and border zones.
2. Border zone = outer 15% of image.
3. Compute edge density or local contrast in the border zone.
4. Compare border complexity to total image complexity.

```text
occupancy_score = border_complexity / total_complexity
```

Classification:

```text
score < 0.28 -> low
score < 0.52 -> medium
else -> high
```

Fallback:

If image analysis is unavailable, use `medium`.

## 7. Hard Decoration Rules

These rules are applied before aesthetic decisions.

| Artwork Type | Glass | Mat | Shadow Box | Notes |
| --- | --- | --- | --- | --- |
| watercolor | required | required | false | Use museum or UV glass by default. |
| photo | required | recommended | false | Mat is recommended for fine art photos; can be absent for full-bleed modern photo. |
| poster | required | conditional | false | Mat depends on occupancy and decor style. |
| canvas | forbidden | forbidden | false | Requires deep frame or floating/canvas frame. |
| embroidery | required | forbidden by default | true | Needs depth. Optional spacer instead of mat. |
| volumetric | required | forbidden by default | true | Needs depth and spacer/shadow box. |

Poster mat rule:

```text
if frame_occupancy == high and decor_style in {modern, signature}:
    mat = optional_or_false
else:
    mat = true
```

Photo mat rule:

```text
standard -> mat true
modern -> mat true unless full_bleed_photo_style is selected
signature -> mat true, double mat optional
```

Canvas rule:

```text
glass = false
mat = false
frame.depth_mm >= 35
frame.profile in {l_shape, box, float}
```

Volumetric / embroidery rule:

```text
shadow_box = true
glass = true
frame.depth_mm >= 45
mat = false by default
spacer = true
```

## 8. Size Profiles

Size profile should be based on the longer side and the shorter side, not only one dimension.

```text
small:
    longer_side <= 420

medium:
    longer_side <= 700

large:
    longer_side <= 1000

extra_large:
    longer_side > 1000
```

Also track aspect ratio:

```text
aspect_ratio = artwork_width_mm / artwork_height_mm

square:        0.92 <= aspect_ratio <= 1.08
portrait:      aspect_ratio < 0.92
landscape:     aspect_ratio > 1.08
panoramic:     aspect_ratio > 1.8 or aspect_ratio < 0.55
```

## 9. Mat Geometry

### 9.1 Base Mat Margins

Mat size is a percentage of the shortest artwork side.

| Size Profile | Standard | Modern | Signature |
| --- | ---: | ---: | ---: |
| small | 35% | 45% | 55% |
| medium | 30% | 40% | 50% |
| large | 25% | 35% | 45% |
| extra_large | 15% | 18% | 20% |

Clamp values:

```text
min_mat_mm = 35
max_mat_mm = 140
```

For extra-large works, do not let mat become visually absurd:

```text
mat_mm = clamp(percent * short_side, 50, 160)
```

### 9.2 Bottom Weighting

Default:

```text
bottom_margin = top_margin * 1.15
```

Use equal margins when:

```text
aspect_ratio == square
or artwork_type == canvas
or mat is false
```

Signature can use stronger bottom weighting:

```text
bottom_margin = top_margin * 1.20
```

### 9.3 Mat Window Overlap

The mat window should overlap the artwork slightly so the artwork does not fall through the window.

```text
window_overlap_mm = 3..5
```

MVP default:

```text
overlap_mm = 4
```

Window size:

```text
window_width_mm = visible_width_mm - 2 * overlap_mm
window_height_mm = visible_height_mm - 2 * overlap_mm
```

If visible dimensions are not provided:

```text
visible_width_mm = artwork_width_mm
visible_height_mm = artwork_height_mm
```

### 9.4 Double Mat

Only `signature` uses double mat by default.

```text
outer_mat_margin = base_margin
inner_mat_reveal = 4..8 mm
```

The inner mat color should be subtle. It is not a large colored field.

## 10. Mat Color Selection

Mat color must be selected from `MatColor` catalog.

### 10.1 Standard DecorStyle

Goal: safe neutral mat.

Rules:

| Image Temperature | Image Lightness | Preferred Mat Families |
| --- | --- | --- |
| warm | light | ivory, warm_white |
| warm | medium | warm_white, ivory |
| warm | dark | warm_white, museum_white |
| cool | light | museum_white, neutral_white |
| cool | medium | neutral_white, soft_grey |
| cool | dark | museum_white, neutral_white |
| neutral | any | neutral_white, museum_white |

Pick the catalog color with:

```text
lowest penalty = family_penalty + temperature_penalty + lightness_penalty
```

Do not try to match the artwork exactly in `standard`.

### 10.2 Modern DecorStyle

Goal: contemporary mat that relates to the image without becoming too loud.

Candidate color:

```text
source_color = secondary_color
```

If no secondary color:

```text
source_color = primary_color
```

Adjustment rule:

```text
if image_lightness == light:
    target_L = source_L - 12
elif image_lightness == dark:
    target_L = source_L + 14
else:
    target_L = source_L
```

Reduce chroma for mat:

```text
target_chroma = source_chroma * 0.45
```

Then choose nearest `MatColor` by Delta E, but only among muted/medium catalog colors.

Reject colors if:

```text
chroma_level == vivid
or delta_e(mat_color, primary_color) < 6
```

The mat should support the image, not disappear into it.

### 10.3 Signature DecorStyle

Goal: distinctive but controlled.

Use double mat:

```text
outer_mat_color = Standard mat color
inner_mat_color = accent-based catalog color
```

If image is monochrome:

```text
inner_mat_color = graphite
```

If no accent color exists:

```text
inner_mat_color = soft_grey or graphite
```

Accent mat is only a reveal strip, usually 4-8 mm.

## 11. Frame Selection

### 11.1 Interior Style to Candidate Frames

Frame selection should return candidates from a `FrameCatalog`, not raw strings.

| Interior Style | Candidate Frame Families |
| --- | --- |
| minimal | black wood, white oak, natural oak, graphite aluminum |
| scandi | light oak, white oak, natural oak |
| japandi | natural oak, walnut, warm black wood |
| contemporary | black aluminum, graphite aluminum, white wood |
| loft | black aluminum, graphite aluminum, champagne aluminum |
| modern_vintage | walnut wood, dark oak, champagne metal |
| neoclassic | walnut wood, matte gold, matte silver |
| universal | natural oak, black wood, graphite |

### 11.2 Choose Material

Use artwork type and size constraints first.

```text
canvas -> wood or floating/canvas frame
volumetric/embroidery -> deep wood shadow box
large poster/photo -> aluminum or wider wood
small/medium paper -> wood or aluminum
```

### 11.3 Frame Width

Use size profile and occupancy.

| Size Profile | Occupancy | Wood Width | Aluminum Width |
| --- | --- | ---: | ---: |
| small | low | 15 | 10 |
| small | medium | 15 | 10 |
| small | high | 20 | 12 |
| medium | low | 20 | 12 |
| medium | medium | 20 | 12 |
| medium | high | 30 | 15 |
| large | low | 30 | 15 |
| large | medium | 35 | 18 |
| large | high | 40 | 20 |
| extra_large | low | 40 | 20 |
| extra_large | medium | 50 | 22 |
| extra_large | high | 50 | 25 |

Clamp:

```text
wood: 10..60 mm
aluminum: 8..30 mm
```

For `signature`, allow the next wider profile if it remains proportional.

## 12. Glass Selection

```python
class GlassType(str, Enum):
    none = "none"
    ordinary = "ordinary"
    museum = "museum"
    uv = "uv"
```

Rules:

```text
canvas -> none
watercolor -> museum or uv
photo -> museum
poster -> ordinary by default, museum for signature
embroidery/volumetric -> museum if budget allows, ordinary otherwise
```

If `avoid_glass = true`, the algorithm can only respect it when hard constraints allow it.

## 13. Geometry Output

Variables:

```text
AW = artwork_width_mm
AH = artwork_height_mm
VW = visible_width_mm
VH = visible_height_mm
O = overlap_mm
ML = mat_left_mm
MR = mat_right_mm
MT = mat_top_mm
MB = mat_bottom_mm
F = frame_width_mm
```

Window:

```text
window_width_mm = VW - 2 * O
window_height_mm = VH - 2 * O
```

Mat outer size:

```text
mat_outer_width_mm = AW + ML + MR
mat_outer_height_mm = AH + MT + MB
```

Final outer size:

```text
outer_width_mm = mat_outer_width_mm + 2 * F
outer_height_mm = mat_outer_height_mm + 2 * F
```

If no mat:

```text
ML = MR = MT = MB = 0
window_width_mm = AW
window_height_mm = AH
outer_width_mm = AW + 2 * F
outer_height_mm = AH + 2 * F
```

## 14. Full Pipeline

```text
1. Validate user input.
2. Load image.
3. Analyze image palette and occupancy.
4. Classify size profile and aspect ratio.
5. For each DecorStyle:
   5.1 Apply hard artwork rules.
   5.2 Decide mat/glass/shadow-box.
   5.3 Calculate mat margins.
   5.4 Select mat color(s) from MatColor catalog.
   5.5 Select frame candidates from FrameCatalog.
   5.6 Pick frame width using size profile and occupancy.
   5.7 Calculate final geometry.
   5.8 Produce reasons and warnings.
6. Return three DecorationSpec objects.
7. Render previews from DecorationSpec objects.
```

## 15. Output Contract

```json
{
  "image_analysis": {
    "palette": {
      "primary": {
        "hex": "#8F6A4E",
        "rgb": [143, 106, 78],
        "lab": [48.2, 11.4, 21.8],
        "family": "brown",
        "temperature": "warm",
        "lightness": "medium",
        "chroma_level": "medium",
        "share": 0.34
      },
      "secondary": {},
      "accent": {}
    },
    "temperature": "warm",
    "lightness": "medium",
    "chroma_level": "medium",
    "frame_occupancy": "medium",
    "is_monochrome": false
  },
  "variants": [
    {
      "decor_style": "standard",
      "frame": {
        "id": "wood-light-oak-20",
        "name": "Light Oak",
        "material": "wood",
        "width_mm": 20,
        "depth_mm": 25,
        "profile": "flat"
      },
      "mat": {
        "enabled": true,
        "outer_color": {
          "id": "mat-warm-white",
          "name": "Warm White",
          "hex": "#F1EBDD"
        },
        "inner_color": null,
        "left_mm": 80,
        "right_mm": 80,
        "top_mm": 80,
        "bottom_mm": 92,
        "overlap_mm": 4
      },
      "glass": {
        "type": "museum",
        "required": true
      },
      "shadow_box": false,
      "geometry": {
        "window_width_mm": 292,
        "window_height_mm": 392,
        "outer_width_mm": 500,
        "outer_height_mm": 612
      },
      "reasons": [
        "Warm neutral mat supports the warm image palette.",
        "Light oak fits minimal/scandi interiors and keeps the artwork calm."
      ],
      "warnings": []
    }
  ]
}
```

## 16. MVP Catalogs

Before real supplier catalogs exist, define small internal catalogs.

### MVP Mat Colors

Minimum catalog:

```text
museum_white
neutral_white
warm_white
ivory
soft_grey
graphite
black
warm_beige
cool_grey
deep_blue
muted_green
terracotta
```

Each item must have:

```text
id, name, hex, rgb, lab, family, temperature, lightness, chroma_level
```

### MVP Frame Families

Minimum catalog:

```text
black_wood
white_oak
light_oak
natural_oak
walnut
graphite_aluminum
black_aluminum
champagne_aluminum
matte_gold
matte_silver
deep_shadow_box_black
deep_shadow_box_oak
```

Each item must have:

```text
id, name, material, color_family, width_mm, depth_mm, profile, available
```

## 17. Important Implementation Notes

1. Avoid encoding too much logic in nested `if` statements.
   Use tables/catalogs plus small rule functions.

2. `rules.yaml` should store declarative rules and catalogs.
   Python code should apply them.

3. The algorithm should output structured `DecorationSpec`.
   The renderer should not decide mat colors or frame rules.

4. The renderer receives a finished spec and only renders it.

5. Keep image analysis separate from decoration selection.

6. Keep physical geometry in millimeters.
   Convert to pixels only inside rendering.

7. Store colors in Lab for matching and in HEX/RGB for display.

## 18. Key Open Questions

These questions do not block MVP, but should be decided later.

1. Should photos always use mat, or should modern full-bleed photo framing be an explicit option?
2. Which real mat/frame supplier catalogs will be used?
3. Should `interior_style` influence only frame choice, or also mat color?
4. How much user choice should be allowed after recommendation?
5. Should the user receive only one final spec or three paid alternatives?
6. Should preview rendering display all three variants side by side?

## 19. MVP Implementation Order

1. Define dataclasses/enums for input, image analysis, catalogs, and decoration spec.
2. Create MVP mat color catalog with Lab values.
3. Create MVP frame catalog.
4. Implement geometry calculations.
5. Implement hard artwork rules.
6. Implement standard/modern/signature mat color selection.
7. Implement frame selection from interior style.
8. Connect the result to renderer.
9. Update UI to display three variants.
10. Add tests for geometry and rule selection.

