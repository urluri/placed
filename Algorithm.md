# Some initial philosophy

The name of the service: Placed
What is it for: for people who don't know how to choose the right decoration for their pictures (posters, photoes, watercolors etc).
What we do: according to the picture uploaded by user, some user's inputs and calculations that the algorithm does, we suggest the user the right decorations sets for their picture. We suggest three variants (DecorStyle): Standard (stands for some ordinary way of decorating pictures), Modern (stands for modern best practices of decorating pictures) and Signature (stands for the most exotic ways of decorating pictures).
When I say 'decorating pictures' I mean that we suggest a frame type, its color, passepartout color, glass etc.

If a users is satisfied with a variant the service suggests he/she pays some money to get the specification. The specification gives a user a list of the decoration parameters (sizes, colors, the need of the passepartout and glass etc). With such a specification user can go to the nearest framing workshop and make an order.

# Phase 1. Image parameters

##### User inputs & algorithm calculations

| Field                  | Data type                                                                                   | Source of data                                         | Description                                                                                                                                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Painting type          | enum PaintingType {watercolor, photo, poster, canvas, 3dPainting }                          | user_input                                             | type of a painting                                                                                                                                                                                                |
| Painting width         | number                                                                                      | user_input                                             | width of a full painting                                                                                                                                                                                          |
| Painting height        | number                                                                                      | user_input                                             | height of a full painting                                                                                                                                                                                         |
| Size profile           | enum PaintSizeProfile {small, medium, large, ExtraLarge}                                    | define according to painting width and painting height | We set the size profile to unify the further calculations, size profiles are only applicable to watercolor, photo, poster and 3dPaining Painting types. Size profile is used to define the size of a passepartout |
| Picture width          | number                                                                                      | user_input                                             | width of a picture (picture area without borders/margins)                                                                                                                                                         |
| Picture height         | number                                                                                      | user_input                                             | height of a picture (picture area without borders/margins)                                                                                                                                                        |
| Interior style         | enum IntStyle {minimalism, scandic, japandi, ModernVintage, contemporary, loft, neoclassic} | user_input                                             | the staly of a user's home interior                                                                                                                                                                               |
| Second color           | To be defined                                                                               | algorithm                                              | the second color from the color histogramm                                                                                                                                                                        |
| Accent color           | To be defined                                                                               | algorithm                                              | the accent color (don't know how to calculate)                                                                                                                                                                    |
| Picture temperature    | enum PicTemperature {warm, neutral, cool}                                                   | algorithm                                              | color temperature                                                                                                                                                                                                 |
| Picture lightness      | enum PicLightness {light, medium, dark}                                                     | algorithm                                              | don't know how to calculate                                                                                                                                                                                       |
| Picture saturaturation | enum PicSaturation {low, medium, high}                                                      | algorithm                                              | don't know how to calculate                                                                                                                                                                                       |
| Frame occupancy        | enum FrameOccupancy {low, medium, high}                                                     | algorithm                                              | don't know how to calculate                                                                                                                                                                                       |
# Phase 2. Decorations

| PictureType | is_glass | is_passepartout                                                                                                                                                                                                                                            | is_ShadowBox | GlassType      |
| ----------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------- |
| watercolor  | true     | true                                                                                                                                                                                                                                                       | false        | museum         |
| photo       | true     | true                                                                                                                                                                                                                                                       | false        | museum         |
| poster      | true     | `switch (FrameOccupancy) {`<br>`case low:`<br>`is_passepartout = true;`<br>`break;`<br>`case medium:`<br>`is_passepartout = true;`<br>`break;`<br>`case high:`<br>`is_passepartout = false;`<br>`break;`<br>`default:`<br>`is_passepartout = true;`<br>`}` | false        | ordinary       |
| canvas      | false    | false                                                                                                                                                                                                                                                      | false        | not applicable |
| 3dPainting  | true     | true                                                                                                                                                                                                                                                       | true         | museum         |
# Phase 3. Passepartout

##### Passepartout size
global: the bottom passepartout is always 20% bigger than the top one. 

|              | passepartout size (% from the shortest picture side) depending on DecorStyle | passepartout size (% from the shortest picture side) depending on DecorStyle | passepartout size (% from the shortest picture side) depending on DecorStyle |
| ------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Size profile | Standard                                                                     | Modern                                                                       | Signature                                                                    |
| small        | 35                                                                           | 45                                                                           | 55                                                                           |
| medium       | 30                                                                           | 40                                                                           | 50                                                                           |
| large        | 25                                                                           | 35                                                                           | 45                                                                           |
| extra        | 15                                                                           | 15                                                                           | 15                                                                           |

##### Passepartout color (for Standard DecorStyle only)

| PicTemperature | PicLightness | PassepartoutColor |
| -------------- | ------------ | ----------------- |
| Warm           | light        | ivory             |
| Warm           | medium       | WarmWhite         |
| Warm           | dark         | WarmWhite         |
| Cool           | light        | MuseumWhite       |
| Cool           | medium       | white             |
| Cool           | dark         | MuseumWhite       |
| Neutral        | any          | white             |

##### Passepartout color (for Modern DecorStyle only)

PassepartoutColor = Second color

AND

если PicLightness = Light >> затемнить на два тона
если PicLightness = Dark >> осветлить на два тона
если PicLightness = Medium >> ничего не делать

  
  

##### Passepartout color (for Signature DecorStyle only)

for Signature DecorStyle we use double passepartout
  

ExternalPassepartoutColor = according to Standard DecorStyle

  

InternalPassepartoutColor = accent color

если картина выполнена в ЧБ, то InternalPassepartoutColor = graphite
# Phase 4. Frame
##### Color and material

|               |                                                                 |
| ------------- | --------------------------------------------------------------- |
| IntStyle      | Material (of the frame)                                         |
| minimalism    | black or white oak (don't know what it depends on)              |
| scandic       | light oak                                                       |
| japandi       | natural oak                                                     |
| ModernVintage | nut three                                                       |
| contemporary  | black or graphite aluminium                                     |
| loft          | black, graphite or champagne aluminium                          |
| neoclassic    | nut three, matte gold or silver (don't know what it depends on) |

##### Frame size

|                                                                |              |                          |                              |
| -------------------------------------------------------------- | ------------ | ------------------------ | ---------------------------- |
| Painting size( here we need to convert it to the size profile) | PicOccupancy | if the material is three | if the material is aluminium |
| До A4 (less 21×29,7 cm)                                        | Low          | 15 mm                    | 10 mm                        |
| До A4 (less 21×29,7 cm)                                        | Medium       | 15 mm                    | 10 mm                        |
| До A4 (less 21×29,7 cm)                                        | High         | 20 mm                    | 12 mm                        |
| A3 (29,7×42 cm)                                                | Low          | 15 mm                    | 10 mm                        |
| A3 (29,7×42 cm)                                                | Medium       | 20 mm                    | 12 mm                        |
| A3 (29,7×42 cm)                                                | High         | 20 mm                    | 12 mm                        |
| A2 (42×59,4 cm)                                                | Low          | 20 mm                    | 12 mm                        |
| A2 (42×59,4 cm)                                                | Medium       | 20 mm                    | 12 mm                        |
| A2 (42×59,4 cm)                                                | High         | 30 mm                    | 15 mm                        |
| 50×70 cm                                                       | Low          | 20 mm                    | 12 mm                        |
| 50×70 cm                                                       | Medium       | 30 mm                    | 15 mm                        |
| 50×70 cm                                                       | High         | 30 mm                    | 15 mm                        |
| 60×80 cm                                                       | Low          | 30 mm                    | 15 mm                        |
| 60×80 cm                                                       | Medium       | 30 mm                    | 15 mm                        |
| 60×80 cm                                                       | High         | 40 mm                    | 20 mm                        |
| 70×100 cm                                                      | Low          | 30 mm                    | 15 mm                        |
| 70×100 cm                                                      | Medium       | 40 mm                    | 20 mm                        |
| 70×100 cm                                                      | High         | 40–50 mm                 | 20 mm                        |
| bigger than 100 cm                                             | Low          | 40 mm                    | 20 mm                        |
| bigger than 100 cm                                             | Medium       | 50 mm                    | 20 mm                        |
| bigger than 100 cm                                             | High         | 50 mm                    | 20 mm                        |

  
  

  
  
  
  

##  Этап 9. Размеры работы

  

W  — ширина произведения

H  — высота произведения

  

O  — перекрытие изображения паспарту с одной стороны

  

Pₗ — левое поле паспарту

Pᵣ — правое поле паспарту

Pₜ — верхнее поле паспарту

Pᵦ — нижнее поле паспарту

  

F  — ширина профиля рамы (видимая часть)

  

WW — ширина окна паспарту

WH — высота окна паспарту

  

MW — ширина оформления с паспарту (без рамы)

MH — высота оформления с паспарту (без рамы)

  

OW — внешний размер оформления

OH — внешний размер оформления

  
  

1. Размер окна паспарту

  

WW = W − 2 × O

WH = H − 2 × O

  
  

2. Размер оформления с паспарту

  

MW = W + Pₗ + Pᵣ

MH = H + Pₜ + Pᵦ

  

Если поля одинаковые:

  

MW = W + 2P

MH = H + 2P

  
  

3. Внешний размер оформления

  

OW = MW + 2F

OH = MH + 2F

  

или сразу:

  

OW = W + Pₗ + Pᵣ + 2F

OH = H + Pₜ + Pᵦ + 2F

  
  

Пример

  

Размер произведения:

W = 400 мм

H = 600 мм

  

Перекрытие:

O = 5 мм

  

Паспарту:

Pₗ = 80 мм

Pᵣ = 80 мм

Pₜ = 80 мм

Pᵦ = 80 мм

  

Рама:

F = 20 мм

  
  

Размер окна:

  

WW = 400 − 10 = 390 мм

WH = 600 − 10 = 590 мм

  

Размер с паспарту:

  

MW = 400 + 80 + 80 = 560 мм

MH = 600 + 80 + 80 = 760 мм

  

Внешний размер оформления:

  

OW = 560 + 20 + 20 = 600 мм

OH = 760 + 20 + 20 = 800 мм

  
**