# Палитра placed

Документ описывает библиотеку цветов паспарту, доступных сервису placed.

Палитра нужна для двух задач:

1. Хранить заранее отобранные цвета паспарту.
2. Ограничивать алгоритмический подбор: если расчетный цвет получен из изображения, итоговый цвет паспарту выбирается как ближайший допустимый цвет из палитры placed.

## Принципы использования

- `Код` - стабильный идентификатор цвета. Его нельзя менять после того, как цвет начнет использоваться в коде или сохраненных рекомендациях.
- `Название` - человекочитаемое название для UI, документации и дерева решений.
- `HEX` - основной цветовой эталон для рендера.
- `Семейство` - ручная смысловая группа цвета. Не нужно определять семейство по префиксу кода: часть кодов исторически пересекается.
- `Роль` - ручное ограничение для алгоритма. Она говорит, в каких стратегиях подбора цвет можно использовать.

## Роли цветов

| Роль | Назначение |
| --- | --- |
| `base_white` | Базовые белые и почти белые паспарту для спокойного классического оформления. |
| `soft_neutral` | Мягкие нейтральные оттенки: светло-серые, бежевые, приглушенные натуральные тона. |
| `soft_color` | Мягкие цветные оттенки, которые поддерживают изображение, но не спорят с ним. |
| `deep_neutral` | Темные нейтральные оттенки для контрастного, графичного оформления. |
| `deep_color` | Темные или плотные цветные оттенки для выразительного оформления. |
| `accent` | Акцентные оттенки, которые можно использовать только если стратегия явно разрешает акцент. |

## Вычисляемые признаки

Температура, светлота, насыщенность и Lab-координаты не хранятся в документе вручную.

Их нужно вычислять в коде из `HEX`, чтобы избежать расхождений между документацией и алгоритмом.

```text
PaletteColor:
  id
  name
  hex
  family
  role
  lab             # computed from hex
  lightness       # computed from lab
  chroma          # computed from lab
  temperature     # computed from lab
```

## Как выбирать ближайший цвет

Для будущих правил `Modern` и `Signature` базовый процесс должен быть таким:

1. Алгоритм определяет стратегию цвета паспарту: например `soft_neutral`, `soft_color`, `deep_neutral`, `deep_color` или `accent`.
2. Алгоритм рассчитывает целевой цвет паспарту на основе изображения.
3. Из палитры placed берется только допустимое подмножество цветов по роли и дополнительным ограничениям стратегии.
4. Целевой цвет и цвета палитры переводятся из HEX/RGB в CIELAB.
5. Среди допустимых цветов выбирается ближайший по цветовой дистанции.
6. Для MVP можно использовать простую дистанцию Delta E по CIELAB. Позже можно перейти на Delta E 2000.

Это защищает алгоритм от странных решений: расчетный цвет может лежать в области, где в палитре нет близкого оттенка, поэтому поиск по всей палитре без ограничений может выбрать слишком темный, слишком светлый или слишком активный цвет.

## Структура цвета

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | string | Код цвета из палитры placed. |
| `name` | string | Название цвета. |
| `hex` | string | HEX цвета. |
| `family` | string | Семейство цвета. |
| `role` | string | Роль цвета в алгоритме. |
| `source` | string | Причина выбора, например `placed_palette_nearest`. |

## Базовые белые и нейтральные

Эта группа используется для спокойных решений и текущих правил `Standard`.

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PW001 | Museum White | `#F7F6F2` | white | `base_white` |
| PW002 | Gallery White | `#F3F2ED` | white | `base_white` |
| PW003 | Warm White | `#F5F1E8` | white | `base_white` |
| PW004 | Ivory | `#EEE6D5` | white | `base_white` |
| PW005 | Antique White | `#E8DFCF` | white | `base_white` |
| PW006 | Linen | `#DDD4C4` | beige | `base_white` |
| PW007 | Natural Cotton | `#E6DFD2` | white | `base_white` |
| PW008 | Cream | `#F2E7D3` | white | `base_white` |

## Светло-серые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PG101 | Soft Grey | `#E5E4E0` | grey | `soft_neutral` |
| PG102 | Gallery Grey | `#DBD9D5` | grey | `soft_neutral` |
| PG103 | Stone Grey | `#CFCBC5` | grey | `soft_neutral` |
| PG104 | Silver Grey | `#C8C8C6` | grey | `soft_neutral` |
| PG105 | Ash Grey | `#B8B8B5` | grey | `soft_neutral` |
| PG106 | Mist Grey | `#D7D6D2` | grey | `soft_neutral` |
| PG107 | Pearl Grey | `#D0D0CC` | grey | `soft_neutral` |
| PG108 | Dove Grey | `#C5C2BB` | grey | `soft_neutral` |

## Темно-серые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PG201 | Graphite | `#55575B` | grey | `deep_neutral` |
| PG202 | Charcoal | `#4A4A4C` | grey | `deep_neutral` |
| PG203 | Slate | `#666A73` | grey | `deep_neutral` |
| PG204 | Basalt | `#5F625D` | grey | `deep_neutral` |
| PG205 | Iron Grey | `#707070` | grey | `deep_neutral` |
| PG206 | Anthracite | `#383A3D` | grey | `deep_neutral` |

## Бежевые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PB301 | Sand | `#D6C3A5` | beige | `soft_neutral` |
| PB302 | Desert Sand | `#CDB59A` | beige | `soft_neutral` |
| PB303 | Beige | `#D9C6AE` | beige | `soft_neutral` |
| PB304 | Taupe | `#B7A79A` | beige | `soft_neutral` |
| PB305 | Clay | `#B79B84` | beige | `soft_neutral` |
| PB306 | Oatmeal | `#D8CBB8` | beige | `soft_neutral` |
| PB307 | Mushroom | `#B8AA9C` | beige | `soft_neutral` |
| PB308 | Camel | `#B6946A` | beige | `soft_neutral` |

## Землистые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PE401 | Terracotta | `#B76545` | earth | `deep_color` |
| PE402 | Burnt Clay | `#A75A40` | earth | `deep_color` |
| PE403 | Rust | `#964B35` | earth | `deep_color` |
| PE404 | Cinnamon | `#A26A4A` | earth | `deep_color` |
| PE405 | Umber | `#7C5A46` | earth | `deep_color` |
| PE406 | Cocoa | `#6B4E3D` | earth | `deep_color` |
| PE407 | Mocha | `#7A6756` | earth | `deep_color` |
| PE408 | Chestnut | `#77523D` | earth | `deep_color` |

## Зеленые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PG501 | Sage | `#A7B39C` | green | `soft_color` |
| PG502 | Olive Grey | `#8E9378` | green | `soft_color` |
| PG503 | Moss | `#707A58` | green | `deep_color` |
| PG504 | Eucalyptus | `#8FA89B` | green | `soft_color` |
| PG505 | Forest Mist | `#6E7C6A` | green | `deep_color` |
| PG506 | Khaki | `#8C8762` | green | `soft_color` |
| PG507 | Lichen | `#B2B59A` | green | `soft_color` |
| PG508 | Dusty Olive | `#7A785C` | green | `deep_color` |

## Голубые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PB601 | Dusty Blue | `#8FA7B5` | blue | `soft_color` |
| PB602 | Mist Blue | `#B5C2C9` | blue | `soft_color` |
| PB603 | Steel Blue | `#758A98` | blue | `soft_color` |
| PB604 | Blue Grey | `#8B99A3` | blue | `soft_color` |
| PB605 | Smoke Blue | `#6D7D89` | blue | `deep_color` |
| PB606 | Slate Blue | `#667789` | blue | `deep_color` |
| PB607 | Ocean Mist | `#A8BCC3` | blue | `soft_color` |
| PB608 | Ice Blue | `#D7E2E7` | blue | `soft_color` |

## Синие

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PN701 | Navy Grey | `#45556A` | navy | `deep_color` |
| PN702 | Deep Indigo | `#3E4A63` | navy | `deep_color` |
| PN703 | Midnight Blue | `#2F3A4A` | navy | `deep_color` |
| PN704 | Denim | `#5C718A` | navy | `deep_color` |
| PN705 | Petrol Blue | `#4A6672` | navy | `deep_color` |
| PN706 | Ink Blue | `#35485A` | navy | `deep_color` |

## Розовые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PR801 | Dusty Rose | `#C49A96` | rose | `soft_color` |
| PR802 | Blush | `#D9BBB3` | rose | `soft_color` |
| PR803 | Nude Pink | `#D8B3A5` | rose | `soft_color` |
| PR804 | Mauve | `#B799A6` | rose | `soft_color` |
| PR805 | Old Rose | `#A97E7A` | rose | `soft_color` |
| PR806 | Rose Clay | `#B98D82` | rose | `soft_color` |

## Фиолетовые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PV901 | Lavender Grey | `#B4A9B9` | violet | `soft_color` |
| PV902 | Heather | `#A58FA5` | violet | `soft_color` |
| PV903 | Dusty Lilac | `#9D8BA7` | violet | `soft_color` |
| PV904 | Plum Grey | `#746675` | violet | `deep_color` |
| PV905 | Aubergine | `#5E4A57` | violet | `deep_color` |

## Желтые

| Код | Название | HEX | Семейство | Роль |
| --- | --- | --- | --- | --- |
| PY1001 | Sand Yellow | `#D6BE78` | yellow | `accent` |
| PY1002 | Wheat | `#D3B57C` | yellow | `accent` |
| PY1003 | Ochre | `#C39A49` | yellow | `accent` |
| PY1004 | Honey | `#C28B3A` | yellow | `accent` |
| PY1005 | Mustard Grey | `#9F8A4C` | yellow | `accent` |

## Замечания для реализации

- Палитру лучше перенести в код как структурированный список объектов.
- Для поиска ближайшего цвета использовать `HEX -> RGB -> CIELAB -> Delta E`.
- Для `Standard` сейчас используются прямые правила из `Цвет паспарту.md`, но выбранные цвета должны ссылаться на эту палитру: `PW001`, `PW003`, `PW004`.
- Для `Modern` и `Signature` сначала нужно определить стратегию цвета паспарту, затем рассчитать целевой цвет и выбрать ближайший цвет из допустимого подмножества палитры placed.
- Если два цвета имеют близкую дистанцию, предпочтение лучше отдавать более спокойному и менее насыщенному варианту.
