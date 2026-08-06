import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";

import { recommend, renderPreview } from "./api";
import type {
  AccentAnalysis,
  ArtworkType,
  ColorSample,
  DecisionNode,
  DecorStyle,
  FormState,
  ImageInfo,
  InteriorStyle,
  MatSizeConfig,
  Recommendation,
  SizeProfile,
  SizeSource,
} from "./types";

const artworkOptions: Array<{ value: ArtworkType; label: string }> = [
  { value: "poster", label: "Постер" },
  { value: "photo", label: "Фото" },
  { value: "watercolor", label: "Акварель" },
  { value: "canvas", label: "Холст" },
  { value: "volumetric", label: "Объёмная" },
];

const interiorOptions: Array<{ value: InteriorStyle; label: string }> = [
  { value: "minimal", label: "Минимализм" },
  { value: "scandi", label: "Сканди" },
  { value: "japandi", label: "Джапанди" },
  { value: "contemporary", label: "Современный" },
  { value: "loft", label: "Лофт" },
  { value: "modern_vintage", label: "Modern vintage" },
  { value: "neoclassic", label: "Неоклассика" },
  { value: "universal", label: "Не знаю" },
];

const decorStyles: DecorStyle[] = ["standard", "modern", "signature"];
const sizeProfiles: SizeProfile[] = ["small", "medium", "large", "extra_large"];

const sizeProfileLabels: Record<SizeProfile, string> = {
  small: "Малый",
  medium: "Средний",
  large: "Большой",
  extra_large: "Очень большой",
};

const decorStyleLabels: Record<DecorStyle, string> = {
  standard: "Standard",
  modern: "Modern",
  signature: "Signature",
};

const defaultMatSizeConfig: MatSizeConfig = {
  percentages: {
    small: { standard: "35", modern: "45", signature: "55" },
    medium: { standard: "20", modern: "30", signature: "35" },
    large: { standard: "20", modern: "25", signature: "30" },
    extra_large: { standard: "20", modern: "25", signature: "30" },
  },
  max_mm: {
    small: { standard: "", modern: "", signature: "" },
    medium: { standard: "", modern: "", signature: "" },
    large: { standard: "", modern: "", signature: "" },
    extra_large: { standard: "70", modern: "80", signature: "90" },
  },
};

const printSizePresets = [
  { ppi: 300, label: "300 PPI", note: "высокое качество" },
  { ppi: 200, label: "200 PPI", note: "хороший крупный размер" },
  { ppi: 150, label: "150 PPI", note: "крупно, но мягче" },
];

const interiorSceneScale = {
  wallWidthMm: 3600,
  artworkCenterXPercent: 50,
  artworkCenterYPercent: 36,
  minArtworkWidthPercent: 5,
  maxArtworkWidthPercent: 42,
};

const interiorScenes: Record<
  InteriorStyle,
  {
    src: string;
    label: string;
  }
> = {
  minimal: {
    src: "/interiors/minimal.jpg",
    label: "Минимализм",
  },
  scandi: {
    src: "/interiors/scandi.jpg",
    label: "Сканди",
  },
  japandi: {
    src: "/interiors/japandi.jpg",
    label: "Джапанди",
  },
  contemporary: {
    src: "/interiors/contemporary.jpg",
    label: "Современный",
  },
  loft: {
    src: "/interiors/loft.jpg",
    label: "Лофт",
  },
  modern_vintage: {
    src: "/interiors/modern_vintage.jpg",
    label: "Modern vintage",
  },
  neoclassic: {
    src: "/interiors/neoclassic.jpg",
    label: "Неоклассика",
  },
  universal: {
    src: "/interiors/universal.jpg",
    label: "Универсальный",
  },
};

type ThemeMode = "light" | "dark";

export default function App() {
  const [form, setForm] = useState<FormState>({
    widthMm: "300",
    heightMm: "400",
    sizeSource: "manual",
    printPpi: 300,
    lockAspect: true,
    imageInfo: null,
    artworkType: "poster",
    interiorStyle: "minimal",
    image: null,
    rotateArtwork: false,
    matSizeConfig: cloneMatSizeConfig(defaultMatSizeConfig),
  });
  const [selectedDecorStyle, setSelectedDecorStyle] = useState<DecorStyle>("standard");
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [renderState, setRenderState] = useState("Нажмите «Применить»");
  const [isRendering, setIsRendering] = useState(false);
  const [showDecisionTree, setShowDecisionTree] = useState(false);
  const [showInteriorPreview, setShowInteriorPreview] = useState(false);
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    if (typeof window === "undefined") return "light";
    const savedTheme = window.localStorage.getItem("placed-theme");
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const requestId = useRef(0);

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
    document.documentElement.style.colorScheme = themeMode;
    window.localStorage.setItem("placed-theme", themeMode);
  }, [themeMode]);

  const selectedVariant = useMemo(() => {
    return recommendation?.variants.find((variant) => variant.decor_style === selectedDecorStyle) ?? null;
  }, [recommendation, selectedDecorStyle]);
  const imageAnalysis = recommendation?.image_analysis ?? null;
  const interiorScene = interiorScenes[form.interiorStyle];
  const interiorArtworkScale = selectedVariant
    ? scaleInteriorArtwork(selectedVariant.geometry.outer_width_mm)
    : null;
  const currentPrintQuality = form.imageInfo
    ? printQualityFor(form.imageInfo, dimensionNumber(form.widthMm), dimensionNumber(form.heightMm))
    : null;
  const previewSurfaceStyle: CSSProperties | undefined = showInteriorPreview
    ? { backgroundImage: `url(${interiorScene.src})` }
    : undefined;
  const previewImageStyle: CSSProperties | undefined = showInteriorPreview
    ? {
        left: `${interiorSceneScale.artworkCenterXPercent}%`,
        top: `${interiorSceneScale.artworkCenterYPercent}%`,
        width: `${interiorArtworkScale?.widthPercent ?? interiorSceneScale.minArtworkWidthPercent}%`,
      }
    : undefined;

  const clearPreview = () => {
    setPreviewUrl((previousUrl) => {
      if (previousUrl) URL.revokeObjectURL(previousUrl);
      return "";
    });
  };

  const updateForm = (patch: Partial<FormState>) => {
    requestId.current += 1;
    setIsRendering(false);
    setForm((current) => ({ ...current, ...patch }));
    setRecommendation(null);
    setShowDecisionTree(false);
    clearPreview();
    setRenderState("Нажмите «Применить»");
  };

  const handleImageUpload = async (file: File | null) => {
    if (!file) {
      updateForm({ image: null, imageInfo: null, sizeSource: "manual" });
      return;
    }

    try {
      const imageInfo = await readImageInfo(file);
      const recommendedSize = sizeFromPpi(imageInfo, 300);
      updateForm({
        image: file,
        imageInfo,
        sizeSource: "from_file",
        printPpi: 300,
        lockAspect: true,
        widthMm: String(recommendedSize.widthMm),
        heightMm: String(recommendedSize.heightMm),
      });
    } catch {
      updateForm({ image: file, imageInfo: null, sizeSource: "manual" });
      setRenderState("Не удалось прочитать размер файла");
    }
  };

  const handleSizeSourceChange = (sizeSource: SizeSource) => {
    if (sizeSource === "from_file" && form.imageInfo) {
      const recommendedSize = sizeFromPpi(form.imageInfo, 300);
      updateForm({
        sizeSource,
        printPpi: 300,
        lockAspect: true,
        widthMm: String(recommendedSize.widthMm),
        heightMm: String(recommendedSize.heightMm),
      });
      return;
    }

    updateForm({ sizeSource });
  };

  const applyPrintPreset = (ppi: number) => {
    if (!form.imageInfo) return;
    const nextSize = sizeFromPpi(form.imageInfo, ppi);
    updateForm({
      sizeSource: "from_file",
      printPpi: ppi,
      lockAspect: true,
      widthMm: String(nextSize.widthMm),
      heightMm: String(nextSize.heightMm),
    });
  };

  const handleDimensionChange = (axis: "width" | "height", value: string) => {
    if (!form.lockAspect || !form.imageInfo || value.trim() === "") {
      updateForm(axis === "width" ? { widthMm: value } : { heightMm: value });
      return;
    }

    const numericValue = Number(value);
    if (!Number.isFinite(numericValue) || numericValue <= 0) {
      updateForm(axis === "width" ? { widthMm: value } : { heightMm: value });
      return;
    }

    const aspect = form.imageInfo.pixelWidth / form.imageInfo.pixelHeight;
    if (axis === "width") {
      updateForm({
        widthMm: value,
        heightMm: String(Math.max(1, Math.round(numericValue / aspect))),
      });
      return;
    }

    updateForm({
      widthMm: String(Math.max(1, Math.round(numericValue * aspect))),
      heightMm: value,
    });
  };

  const handleDecorStyleChange = (decorStyle: DecorStyle) => {
    requestId.current += 1;
    setIsRendering(false);
    setSelectedDecorStyle(decorStyle);
    setShowDecisionTree(false);
    clearPreview();
    setRenderState("Нажмите «Применить»");
  };

  const handleMatPercentageChange = (profile: SizeProfile, decorStyle: DecorStyle, value: string) => {
    updateForm({
      matSizeConfig: {
        ...form.matSizeConfig,
        percentages: {
          ...form.matSizeConfig.percentages,
          [profile]: {
            ...form.matSizeConfig.percentages[profile],
            [decorStyle]: value,
          },
        },
      },
    });
  };

  const handleMatMaxChange = (decorStyle: DecorStyle, value: string) => {
    updateForm({
      matSizeConfig: {
        ...form.matSizeConfig,
        max_mm: {
          ...form.matSizeConfig.max_mm,
          extra_large: {
            ...form.matSizeConfig.max_mm.extra_large,
            [decorStyle]: value,
          },
        },
      },
    });
  };

  const resetMatSizeConfig = () => {
    updateForm({ matSizeConfig: cloneMatSizeConfig(defaultMatSizeConfig) });
  };

  const applyRender = async () => {
    const id = ++requestId.current;
    setIsRendering(true);
    setRenderState("Считаю варианты");

    try {
      const nextRecommendation = await recommend(form);
      if (id !== requestId.current) return;
      const nextVariant =
        nextRecommendation.variants.find((variant) => variant.decor_style === selectedDecorStyle) ??
        nextRecommendation.variants[0] ??
        null;

      setRecommendation(nextRecommendation);

      if (!nextVariant) {
        setRenderState("Нет варианта для рендера");
        return;
      }

      setRenderState("Готовлю рендер");
      const blob = await renderPreview(form, selectedDecorStyle, nextVariant);
      if (id !== requestId.current) return;
      const objectUrl = URL.createObjectURL(blob);
      setPreviewUrl((previousUrl) => {
        if (previousUrl) URL.revokeObjectURL(previousUrl);
        return objectUrl;
      });
      setRenderState("Готово");
      window.setTimeout(() => {
        if (id === requestId.current) setRenderState("");
      }, 900);
    } catch (error) {
      if (id !== requestId.current) return;
      setRenderState(error instanceof Error ? error.message : "Ошибка рендера");
    } finally {
      if (id === requestId.current) setIsRendering(false);
    }
  };

  return (
    <main className="app-shell" data-theme={themeMode}>
      <section className="control-panel" aria-label="Параметры картины">
        <div className="brand-row">
          <div>
            <p className="eyebrow">Placed MVP</p>
            <h1>Подбор багета</h1>
          </div>
          <div className="brand-actions">
            <button
              type="button"
              className="theme-toggle"
              aria-pressed={themeMode === "dark"}
              title={themeMode === "dark" ? "Включить светлую тему" : "Включить темную тему"}
              onClick={() => setThemeMode((current) => (current === "dark" ? "light" : "dark"))}
            >
              <span className="theme-toggle-icon" aria-hidden="true" />
              <span>{themeMode === "dark" ? "Светлая" : "Темная"}</span>
            </button>
            <output className="status-pill">{sizeProfileName(selectedVariant?.geometry.size_profile)}</output>
          </div>
        </div>

        <form className="config-form">
          <div className="compact-upload">
            <button
              type="button"
              className="icon-upload"
              title="Загрузить изображение"
              aria-label="Загрузить изображение"
              onClick={() => uploadInputRef.current?.click()}
            >
              <span aria-hidden="true">+</span>
            </button>
            <input
              ref={uploadInputRef}
              id="artUpload"
              type="file"
              accept="image/*"
              onChange={(event) => {
                void handleImageUpload(event.target.files?.[0] ?? null);
                event.currentTarget.value = "";
              }}
            />
            <div className="upload-summary">
              <strong>{form.image?.name ?? "Загрузить изображение"}</strong>
              <small>{form.image ? `${Math.round(form.image.size / 1024)} КБ` : "JPG, PNG или WEBP"}</small>
            </div>
          </div>

          <div className="size-source-panel">
            <div className="section-label-row">
              <span>Размер работы</span>
              <TooltipHint text="Если это цифровой файл, можно рассчитать размер печати по пикселям. Если работа уже существует физически, задайте размер вручную." />
            </div>
            <div className="segmented-control" aria-label="Источник физического размера">
              <button
                type="button"
                className={form.sizeSource === "from_file" ? "is-active" : ""}
                disabled={!form.imageInfo}
                title={form.imageInfo ? "Размер будет рассчитан по пикселям файла и выбранному качеству печати." : "Сначала загрузите изображение."}
                onClick={() => handleSizeSourceChange("from_file")}
              >
                Рассчитать по файлу
              </button>
              <button
                type="button"
                className={form.sizeSource === "manual" ? "is-active" : ""}
                title="Введите реальный физический размер работы в миллиметрах."
                onClick={() => handleSizeSourceChange("manual")}
              >
                Задать вручную
              </button>
            </div>
            {form.imageInfo && (
              <div className="file-size-hint">
                <span>
                  Файл: {form.imageInfo.pixelWidth} x {form.imageInfo.pixelHeight} px
                </span>
                <strong>{currentPrintQuality ? currentPrintQuality.label : "Качество не рассчитано"}</strong>
              </div>
            )}
            {!form.imageInfo && (
              <p className="size-mode-hint">Загрузите изображение, чтобы рассчитать размер печати автоматически.</p>
            )}
            {form.imageInfo && form.sizeSource === "from_file" && (
              <div className="print-presets" aria-label="Размеры печати по качеству">
                {printSizePresets.map((preset) => {
                  const size = sizeFromPpi(form.imageInfo as ImageInfo, preset.ppi);
                  return (
                    <button
                      key={preset.ppi}
                      type="button"
                      className={form.printPpi === preset.ppi ? "is-active" : ""}
                      onClick={() => applyPrintPreset(preset.ppi)}
                    >
                      <strong>{preset.label}</strong>
                      <span>
                        {size.widthMm} x {size.heightMm} мм, {preset.note}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <fieldset className="dimensions">
            <legend>
              Физические размеры
              {form.sizeSource === "manual" && form.imageInfo && (
                <button
                  type="button"
                  className={`aspect-toggle ${form.lockAspect ? "is-active" : ""}`}
                  aria-pressed={form.lockAspect}
                  title="При изменении одной стороны вторая пересчитывается по пропорциям загруженного файла."
                  onClick={() => updateForm({ lockAspect: !form.lockAspect })}
                >
                  {form.lockAspect ? "Сохранять пропорции" : "Свободные пропорции"}
                </button>
              )}
            </legend>
            <label>
              <span>Ширина, мм</span>
              <input
                type="number"
                min="50"
                max="3000"
                step="1"
                value={form.widthMm}
                disabled={form.sizeSource === "from_file"}
                onChange={(event) => handleDimensionChange("width", event.target.value)}
              />
            </label>
            <label>
              <span>Высота, мм</span>
              <input
                type="number"
                min="50"
                max="3000"
                step="1"
                value={form.heightMm}
                disabled={form.sizeSource === "from_file"}
                onChange={(event) => handleDimensionChange("height", event.target.value)}
              />
            </label>
          </fieldset>

          <label className="rotate-toggle">
            <input
              type="checkbox"
              checked={form.rotateArtwork}
              onChange={(event) => updateForm({ rotateArtwork: event.target.checked })}
            />
            <span>Развернуть изображение на 90°</span>
          </label>

          <SelectField
            label="Тип работы"
            value={form.artworkType}
            options={artworkOptions}
            onChange={(artworkType) => updateForm({ artworkType })}
          />

          <SelectField
            label="Стиль интерьера"
            value={form.interiorStyle}
            options={interiorOptions}
            onChange={(interiorStyle) => updateForm({ interiorStyle })}
          />

          <details className="debug-panel">
            <summary>Отладка</summary>
            <div className="debug-section">
              <div className="section-label-row">
                <span>Размер паспарту, %</span>
                <button type="button" className="text-button" onClick={resetMatSizeConfig}>
                  Сбросить
                </button>
              </div>
              <div className="mat-size-grid" role="group" aria-label="Таблица размеров паспарту">
                <span />
                {decorStyles.map((decorStyle) => (
                  <strong key={decorStyle}>{decorStyleLabels[decorStyle]}</strong>
                ))}
                {sizeProfiles.map((profile) => (
                  <MatSizeRow
                    key={profile}
                    profile={profile}
                    values={form.matSizeConfig.percentages[profile]}
                    onChange={handleMatPercentageChange}
                  />
                ))}
              </div>
              <div className="mat-limit-grid" role="group" aria-label="Ограничения паспарту для очень большого профиля">
                <span>Максимум, мм</span>
                {decorStyles.map((decorStyle) => (
                  <label key={decorStyle}>
                    <span>{decorStyleLabels[decorStyle]}</span>
                    <input
                      type="number"
                      min="1"
                      max="500"
                      step="1"
                      inputMode="numeric"
                      value={form.matSizeConfig.max_mm.extra_large[decorStyle]}
                      onChange={(event) => handleMatMaxChange(decorStyle, event.target.value)}
                    />
                  </label>
                ))}
              </div>
            </div>
          </details>
        </form>
      </section>

      <section className="preview-stage" aria-label="Превью оформления">
        <div className="preview-toolbar">
          <div className="preview-meta">
            <span>{displayDimension(form.widthMm, 300)} x {displayDimension(form.heightMm, 400)} мм</span>
            <strong>{selectedDecorStyle.toUpperCase()}</strong>
            <small>{showInteriorPreview ? interiorScene.label : "Без интерьера"}</small>
          </div>
          <div className="preview-mode-panel">
            <nav className="variant-tabs" aria-label="Варианты оформления">
              {decorStyles.map((decorStyle) => (
                <button
                  key={decorStyle}
                  type="button"
                  className={selectedDecorStyle === decorStyle ? "is-active" : ""}
                  onClick={() => handleDecorStyleChange(decorStyle)}
                >
                  {decorStyle[0].toUpperCase() + decorStyle.slice(1)}
                </button>
              ))}
            </nav>
            <button
              type="button"
              className={`interior-toggle ${showInteriorPreview ? "is-active" : ""}`}
              aria-pressed={showInteriorPreview}
              onClick={() => setShowInteriorPreview((isVisible) => !isVisible)}
            >
              {showInteriorPreview ? "Обычный вид" : "Смотреть в интерьере"}
            </button>
          </div>
          <div className="preview-actions">
            <button type="button" className="apply-button" onClick={applyRender} disabled={isRendering}>
              {isRendering ? "Применяю" : "Применить"}
            </button>
            <button type="button" onClick={() => downloadPreview(previewUrl, selectedDecorStyle)} disabled={!previewUrl}>
              Скачать превью
            </button>
          </div>
        </div>
        <div
          className={`render-surface ${showInteriorPreview ? "interior-preview" : "plain-preview"}`}
          style={previewSurfaceStyle}
        >
          {previewUrl && (
            <img
              className="framed-art-preview"
              src={previewUrl}
              alt="Превью оформления"
              style={previewImageStyle}
            />
          )}
          <div className={`render-state ${renderState ? "is-visible" : ""} ${isRendering ? "is-loading" : ""}`}>
            {isRendering && <span className="loader" aria-hidden="true" />}
            <span>{renderState}</span>
          </div>
        </div>
        <div className="result-panel">
          <details className="result-details">
            <summary>Параметры итогового оформления</summary>
            <dl className="spec-list">
              <SpecItem label="Рама">{frameSpec(selectedVariant)}</SpecItem>
              <SpecItem label="Паспарту">{matSpec(selectedVariant)}</SpecItem>
              <SpecItem label="Итоговый размер">
                {selectedVariant
                  ? `${selectedVariant.geometry.outer_width_mm} x ${selectedVariant.geometry.outer_height_mm} мм`
                  : "—"}
              </SpecItem>
            </dl>
            <p className="reason-text">{selectedVariant?.reasons.join(" ")}</p>
          </details>
          <details className="result-details">
            <summary>Расчеты изображения</summary>
            <div className="palette-row" aria-label="Цвета изображения">
              <PaletteChip label="Основной" color={imageAnalysis?.palette.primary} />
              <PaletteChip label="Вторичный" color={imageAnalysis?.palette.secondary} />
              <PaletteChip label="Акцентный" color={imageAnalysis?.palette.accent?.selected} />
            </div>
            <AccentDetails accent={imageAnalysis?.palette.accent} />
            <dl className="spec-list analysis-list">
              <SpecItem label="Температура">{imageAnalysis?.temperature ?? "—"}</SpecItem>
              <SpecItem label="Светлота">{imageAnalysis?.lightness ?? "—"}</SpecItem>
              <SpecItem label="Насыщенность">{imageAnalysis?.chroma_level ?? "—"}</SpecItem>
              <SpecItem label="Монохромность">{imageAnalysis?.monochrome ?? "—"}</SpecItem>
              <SpecItem label="Заполненность">{imageAnalysis?.frame_occupancy ?? "—"}</SpecItem>
              <SpecItem label="Контраст">{imageAnalysis?.contrast ?? "—"}</SpecItem>
              <SpecItem label="Метрики">{metricsSpec(imageAnalysis?.metrics)}</SpecItem>
            </dl>
          </details>
          <button
            type="button"
            className="decision-toggle"
            aria-expanded={showDecisionTree}
            onClick={() => setShowDecisionTree((isOpen) => !isOpen)}
          >
            Дерево решений
          </button>
        </div>
        {showDecisionTree && (
          <section className="decision-panel" aria-label="Дерево решений">
            <DecisionTree nodes={selectedVariant?.decision_tree ?? []} />
          </section>
        )}
      </section>
    </main>
  );
}

function SelectField<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}) {
  return (
    <label className="select-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value as T)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function TooltipHint({ text }: { text: string }) {
  return (
    <span className="tooltip-hint" tabIndex={0} title={text} aria-label={text}>
      ?
    </span>
  );
}

function SpecItem({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function PaletteChip({ label, color }: { label: string; color?: ColorSample | null }) {
  return (
    <div className="color-chip">
      <div className="color-swatch" style={{ background: color?.hex ?? "#D8D6D0" }} />
      <span>{color ? `${label}: ${color.hex}` : `${label}: —`}</span>
    </div>
  );
}

function AccentDetails({ accent }: { accent?: AccentAnalysis | null }) {
  if (!accent) return null;

  return (
    <div className="accent-details">
      <div className="accent-summary">
        <span>Источник: {accent.source ?? "—"}</span>
        <span>Уверенность: {accent.confidence}</span>
      </div>
      <p className="reason-text">{accent.reason}</p>
      <div className="accent-candidates" aria-label="Кандидаты акцентного цвета">
        <PaletteChip label={`Pop ${scoreLabel(accent.scores?.pop)}`} color={accent.candidates.pop} />
        <PaletteChip label={`Temperature ${scoreLabel(accent.scores?.temperature)}`} color={accent.candidates.temperature} />
        <PaletteChip label={`Light ${scoreLabel(accent.scores?.light)}`} color={accent.candidates.light} />
        <PaletteChip label={`Area ${scoreLabel(accent.scores?.area)}`} color={accent.candidates.area} />
      </div>
    </div>
  );
}

function scoreLabel(value: number | undefined) {
  return typeof value === "number" ? `(${value})` : "";
}

function DecisionTree({ nodes }: { nodes: DecisionNode[] }) {
  return (
    <div className="decision-tree">
      {nodes.map((node, index) => (
        <details className="decision-node" open={index < 2} key={`${node.title}-${index}`}>
          <summary>{node.title}</summary>
          {node.result && <div className="decision-result">{node.result}</div>}
          {node.facts.length > 0 && (
            <ul>
              {node.facts.map((fact) => (
                <li key={fact}>{fact}</li>
              ))}
            </ul>
          )}
        </details>
      ))}
    </div>
  );
}

function MatSizeRow({
  profile,
  values,
  onChange,
}: {
  profile: SizeProfile;
  values: Record<DecorStyle, string>;
  onChange: (profile: SizeProfile, decorStyle: DecorStyle, value: string) => void;
}) {
  return (
    <>
      <span>{sizeProfileLabels[profile]}</span>
      {decorStyles.map((decorStyle) => (
        <label key={decorStyle}>
          <span>{decorStyleLabels[decorStyle]}</span>
          <input
            type="number"
            min="1"
            max="100"
            step="1"
            inputMode="decimal"
            value={values[decorStyle]}
            onChange={(event) => onChange(profile, decorStyle, event.target.value)}
          />
        </label>
      ))}
    </>
  );
}

function frameSpec(variant: Recommendation["variants"][number] | null) {
  if (!variant) return "—";
  return `${variant.frame.width_mm} мм, ${materialName(variant.frame.material)}, ${variant.frame.name}`;
}

function matSpec(variant: Recommendation["variants"][number] | null) {
  if (!variant?.mat?.enabled) return "нет";
  const mat = variant.mat;
  const color = mat.outer_color?.hex ?? "цвет не задан";
  return `${mat.left_mm}/${mat.top_mm}/${mat.right_mm}/${mat.bottom_mm} мм, ${color}`;
}

function materialName(value?: string) {
  return value === "aluminum" ? "алюминий" : "дерево";
}

function sizeProfileName(value?: string) {
  const names: Record<string, string> = {
    small: "малый",
    medium: "средний",
    large: "большой",
    extra_large: "очень большой",
  };
  return names[value ?? ""] ?? "средний";
}

function metricsSpec(metrics: Recommendation["image_analysis"]["metrics"] | undefined) {
  if (!metrics) return "—";
  return [
    `L ${formatMetric(metrics.lightness)}`,
    `C ${formatMetric(metrics.chroma)}`,
    `mono ${formatMetric(metrics.monochrome_score)}`,
    `contrast ${formatMetric(metrics.contrast)}`,
    `occupancy ${formatMetric(metrics.frame_occupancy)}`,
    `temp ${formatMetric(metrics.temperature_score)}`,
  ].join(" / ");
}

function formatMetric(value: number | undefined) {
  return typeof value === "number" ? String(value) : "—";
}

function cloneMatSizeConfig(config: MatSizeConfig): MatSizeConfig {
  return {
    percentages: {
      small: { ...config.percentages.small },
      medium: { ...config.percentages.medium },
      large: { ...config.percentages.large },
      extra_large: { ...config.percentages.extra_large },
    },
    max_mm: {
      small: { ...config.max_mm.small },
      medium: { ...config.max_mm.medium },
      large: { ...config.max_mm.large },
      extra_large: { ...config.max_mm.extra_large },
    },
  };
}

function readImageInfo(file: File): Promise<ImageInfo> {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      if (!image.naturalWidth || !image.naturalHeight) {
        reject(new Error("Image metadata is unavailable"));
        return;
      }
      resolve({
        pixelWidth: image.naturalWidth,
        pixelHeight: image.naturalHeight,
      });
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Image metadata is unavailable"));
    };
    image.src = objectUrl;
  });
}

function sizeFromPpi(imageInfo: ImageInfo, ppi: number) {
  return {
    widthMm: Math.max(1, Math.round((imageInfo.pixelWidth / ppi) * 25.4)),
    heightMm: Math.max(1, Math.round((imageInfo.pixelHeight / ppi) * 25.4)),
  };
}

function printQualityFor(imageInfo: ImageInfo, widthMm: number | null, heightMm: number | null) {
  if (!widthMm || !heightMm) return null;

  const widthInches = widthMm / 25.4;
  const heightInches = heightMm / 25.4;
  const ppi = Math.round(Math.min(imageInfo.pixelWidth / widthInches, imageInfo.pixelHeight / heightInches));

  return {
    ppi,
    label: qualityText(ppi),
  };
}

function qualityText(ppi: number) {
  if (ppi >= 300) return `Качество: высокое, около ${ppi} PPI`;
  if (ppi >= 200) return `Качество: хорошее, около ${ppi} PPI`;
  if (ppi >= 150) return `Качество: среднее, около ${ppi} PPI`;
  if (ppi >= 100) return `Качество: низкое, около ${ppi} PPI`;
  return `Качество: очень низкое, около ${ppi} PPI`;
}

function dimensionNumber(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function scaleInteriorArtwork(outerWidthMm: number) {
  const rawWidthPercent = (outerWidthMm / interiorSceneScale.wallWidthMm) * 100;
  const widthPercent = Math.max(
    interiorSceneScale.minArtworkWidthPercent,
    Math.min(interiorSceneScale.maxArtworkWidthPercent, rawWidthPercent),
  );

  return {
    widthPercent,
    rawWidthPercent,
  };
}

function displayDimension(value: string, fallback: number) {
  return value.trim() || String(fallback);
}

function downloadPreview(previewUrl: string, decorStyle: DecorStyle) {
  if (!previewUrl) return;
  const link = document.createElement("a");
  link.download = `placed-${decorStyle}.jpg`;
  link.href = previewUrl;
  link.click();
}
