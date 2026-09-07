import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { CSSProperties, MouseEvent, ReactNode } from "react";

import { recommend, renderPreview } from "./api";
import type {
  ArtworkType,
  DecorStyle,
  FormState,
  ImageInfo,
  InteriorStyle,
  MatColor,
  MatColorAnalyzer,
  MatSizeConfig,
  MlColorCandidate,
  Recommendation,
  SizeSource,
} from "./types";

const artworkOptions: Array<{ value: ArtworkType; label: string }> = [
  { value: "poster", label: "Постер" },
  { value: "photo", label: "Фото" },
  { value: "watercolor", label: "Акварель" },
  { value: "engraving", label: "Гравюра" },
  { value: "botanical", label: "Ботаническая иллюстрация" },
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

const decorStyles: DecorStyle[] = ["standard", "signature"];
const ACTIVE_MAT_COLOR_ANALYZER: MatColorAnalyzer = "ml";

const decorStyleLabels: Record<DecorStyle, string> = {
  standard: "Standard",
  signature: "Signature",
};

const defaultMatSizeConfig: MatSizeConfig = {
  percentages: {
    small: { standard: "35", signature: "35" },
    medium: { standard: "25", signature: "25" },
    large: { standard: "15", signature: "15" },
    extra_large: { standard: "10", signature: "10" },
  },
  max_mm: {
    small: { standard: "", signature: "" },
    medium: { standard: "", signature: "" },
    large: { standard: "", signature: "" },
    extra_large: { standard: "70", signature: "70" },
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
type ImageHistoryItem = {
  id: string;
  name: string;
  size: number;
  type: string;
  updatedAt: number;
  thumbnail: string;
};
type StoredImageHistoryItem = ImageHistoryItem & {
  blob: Blob;
  lastModified: number;
};
type PreviewMeasure = {
  surfaceWidth: number;
  surfaceHeight: number;
  imageLeft: number;
  imageTop: number;
  imageWidth: number;
  imageHeight: number;
};
type SpecCalloutData = {
  kind: "frame" | "outer-mat" | "inner-mat";
  title: string;
  color?: string;
  lines: string[];
  x: number;
  y: number;
  width: number;
  height: number;
  anchorX: number;
  anchorY: number;
  targetX: number;
  targetY: number;
};
type PreviewZoomState = {
  cursorX: number;
  cursorY: number;
  relativeX: number;
  relativeY: number;
};

const IMAGE_HISTORY_LIMIT = 15;
const IMAGE_HISTORY_DB = "placed-image-history";
const IMAGE_HISTORY_STORE = "images";

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
    matColorAnalyzer: ACTIVE_MAT_COLOR_ANALYZER,
    image: null,
    rotationDegrees: 0,
    matSizeConfig: cloneMatSizeConfig(defaultMatSizeConfig),
  });
  const [selectedDecorStyle, setSelectedDecorStyle] = useState<DecorStyle>("standard");
  const [recommendations, setRecommendations] = useState<Partial<Record<MatColorAnalyzer, Recommendation>>>({});
  const [previewUrls, setPreviewUrls] = useState<Partial<Record<MatColorAnalyzer, Partial<Record<DecorStyle, string>>>>>({});
  const [mlInnerOverrideColorId, setMlInnerOverrideColorId] = useState<string | null>(null);
  const [appliedInputSignature, setAppliedInputSignature] = useState<string | null>(null);
  const [renderState, setRenderState] = useState("Нажмите «Применить»");
  const [isRendering, setIsRendering] = useState(false);
  const [showInteriorPreview, setShowInteriorPreview] = useState(false);
  const [showSpecOverlay, setShowSpecOverlay] = useState(false);
  const [imageHistory, setImageHistory] = useState<ImageHistoryItem[]>([]);
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    if (typeof window === "undefined") return "light";
    const savedTheme = window.localStorage.getItem("placed-theme");
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const previewSurfaceRef = useRef<HTMLDivElement>(null);
  const previewImageRef = useRef<HTMLImageElement>(null);
  const requestId = useRef(0);
  const [previewMeasure, setPreviewMeasure] = useState<PreviewMeasure | null>(null);
  const [previewZoom, setPreviewZoom] = useState<PreviewZoomState | null>(null);

  useEffect(() => {
    let isMounted = true;
    void loadImageHistory()
      .then((items) => {
        if (isMounted) setImageHistory(items);
      })
      .catch(() => {
        if (isMounted) setImageHistory([]);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
    document.documentElement.style.colorScheme = themeMode;
    window.localStorage.setItem("placed-theme", themeMode);
  }, [themeMode]);

  const measurePreview = useCallback(() => {
    const surface = previewSurfaceRef.current;
    const image = previewImageRef.current;
    if (!surface || !image) {
      setPreviewMeasure(null);
      return;
    }

    const surfaceRect = surface.getBoundingClientRect();
    const imageRect = image.getBoundingClientRect();
    if (surfaceRect.width <= 0 || surfaceRect.height <= 0 || imageRect.width <= 0 || imageRect.height <= 0) {
      setPreviewMeasure(null);
      return;
    }

    const nextMeasure = {
      surfaceWidth: surfaceRect.width,
      surfaceHeight: surfaceRect.height,
      imageLeft: imageRect.left - surfaceRect.left,
      imageTop: imageRect.top - surfaceRect.top,
      imageWidth: imageRect.width,
      imageHeight: imageRect.height,
    };

    setPreviewMeasure((current) => (isSamePreviewMeasure(current, nextMeasure) ? current : nextMeasure));
  }, []);

  const primaryAnalyzer = ACTIVE_MAT_COLOR_ANALYZER;
  const recommendation = recommendations[primaryAnalyzer] ?? null;
  const selectedVariant = useMemo(() => {
    return recommendation?.variants.find((variant) => variant.decor_style === selectedDecorStyle) ?? null;
  }, [recommendation, selectedDecorStyle]);
  const mlSignatureVariant = useMemo(() => {
    return recommendations.ml?.variants.find((variant) => variant.decor_style === "signature") ?? null;
  }, [recommendations.ml]);
  const mlInnerCandidates = useMemo(() => mlInnerMatCandidates(mlSignatureVariant), [mlSignatureVariant]);
  const currentInputSignature = useMemo(() => formInputSignature(form), [form]);
  const hasInputChanges = appliedInputSignature !== currentInputSignature;
  const currentPreviewUrl = previewUrls[primaryAnalyzer]?.[selectedDecorStyle] ?? "";
  const isApplyDisabled = isRendering || !hasInputChanges;
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

  useEffect(() => {
    if (!currentPreviewUrl) {
      setPreviewMeasure(null);
      setPreviewZoom(null);
      return;
    }

    const frameId = window.requestAnimationFrame(measurePreview);
    const surface = previewSurfaceRef.current;
    const image = previewImageRef.current;
    const resizeObserver = new ResizeObserver(measurePreview);

    if (surface) resizeObserver.observe(surface);
    if (image) resizeObserver.observe(image);
    window.addEventListener("resize", measurePreview);

    return () => {
      window.cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      window.removeEventListener("resize", measurePreview);
    };
  }, [currentPreviewUrl, selectedDecorStyle, selectedVariant, showInteriorPreview, measurePreview]);

  useEffect(() => {
    setPreviewZoom(null);
  }, [currentPreviewUrl, selectedDecorStyle, showInteriorPreview]);

  const handlePreviewZoomMove = (event: MouseEvent<HTMLImageElement>) => {
    const surface = previewSurfaceRef.current;
    if (!surface || !previewMeasure || !currentPreviewUrl) return;

    const surfaceRect = surface.getBoundingClientRect();
    const imageRect = event.currentTarget.getBoundingClientRect();
    setPreviewZoom({
      cursorX: event.clientX - surfaceRect.left,
      cursorY: event.clientY - surfaceRect.top,
      relativeX: clampNumber(event.clientX - imageRect.left, 0, imageRect.width),
      relativeY: clampNumber(event.clientY - imageRect.top, 0, imageRect.height),
    });
  };

  const clearPreview = () => {
    setPreviewUrls((previousUrls) => {
      revokeAnalyzerPreviewUrls(previousUrls);
      return {};
    });
  };

  const updateForm = (patch: Partial<FormState>) => {
    requestId.current += 1;
    setIsRendering(false);
    setForm((current) => ({ ...current, ...patch }));
    setRecommendations({});
    setMlInnerOverrideColorId(null);
    clearPreview();
    setRenderState("Нажмите «Применить»");
  };

  const handleImageUpload = async (file: File | null) => {
    if (!file) {
      updateForm({ image: null, imageInfo: null, sizeSource: "manual" });
      return;
    }

    await applyImageFile(file, true);
  };

  const applyImageFile = async (file: File, shouldSaveToHistory: boolean) => {
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

      if (shouldSaveToHistory) {
        saveImageToHistory(file)
          .then(setImageHistory)
          .catch(() => {
            setRenderState("Изображение загружено, но история недоступна");
          });
      }
    } catch {
      updateForm({ image: file, imageInfo: null, sizeSource: "manual" });
      setRenderState("Не удалось прочитать размер файла");
    }
  };

  const handleHistorySelect = async (id: string) => {
    try {
      const storedImage = await getStoredImage(id);
      if (!storedImage) {
        setImageHistory(await loadImageHistory());
        setRenderState("Изображение не найдено в истории");
        return;
      }

      const file = new File([storedImage.blob], storedImage.name, {
        type: storedImage.type || storedImage.blob.type || "application/octet-stream",
        lastModified: storedImage.lastModified || storedImage.updatedAt,
      });

      await touchHistoryImage(storedImage);
      setImageHistory(await loadImageHistory());
      await applyImageFile(file, false);
    } catch {
      setRenderState("Не удалось открыть изображение из истории");
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
    setSelectedDecorStyle(decorStyle);
  };

  const applyRender = async () => {
    const id = ++requestId.current;
    setIsRendering(true);
    setRenderState("");
    const analyzersToRender: MatColorAnalyzer[] = [ACTIVE_MAT_COLOR_ANALYZER];

    try {
      const recommendationEntries: Array<readonly [MatColorAnalyzer, Recommendation]> = [];
      for (const analyzer of analyzersToRender) {
        recommendationEntries.push([analyzer, await recommend(form, analyzer)] as const);
      }
      if (id !== requestId.current) return;
      const nextRecommendations = Object.fromEntries(recommendationEntries) as Partial<Record<MatColorAnalyzer, Recommendation>>;
      const primaryRecommendation = nextRecommendations[analyzersToRender[0]];
      const nextVariant =
        primaryRecommendation?.variants.find((variant) => variant.decor_style === selectedDecorStyle) ??
        primaryRecommendation?.variants[0] ??
        null;

      if (!nextVariant) {
        setRenderState("Нет варианта для рендера");
        return;
      }

      const renderedPreviews: Array<readonly [MatColorAnalyzer, DecorStyle, string]> = [];
      try {
        for (const analyzer of analyzersToRender) {
            const analyzerRecommendation = nextRecommendations[analyzer];
            for (const decorStyle of decorStyles) {
              const variant = analyzerRecommendation?.variants.find((item) => item.decor_style === decorStyle) ?? null;
              if (!variant) continue;
            const blob = await renderPreview(form, decorStyle, variant, analyzer, analyzerRecommendation?.image_token);
            renderedPreviews.push([analyzer, decorStyle, URL.createObjectURL(blob)] as const);
          }
        }
      } catch (error) {
        for (const item of renderedPreviews) {
          URL.revokeObjectURL(item[2]);
        }
        throw error;
      }
      if (id !== requestId.current) {
        for (const item of renderedPreviews) {
          URL.revokeObjectURL(item[2]);
        }
        return;
      }

      const nextPreviewUrls: Partial<Record<MatColorAnalyzer, Partial<Record<DecorStyle, string>>>> = {};
      for (const item of renderedPreviews) {
        const [analyzer, decorStyle, previewUrl] = item;
        nextPreviewUrls[analyzer] = {
          ...(nextPreviewUrls[analyzer] ?? {}),
          [decorStyle]: previewUrl,
        };
      }

      setRecommendations(nextRecommendations);
      setMlInnerOverrideColorId(null);
      setPreviewUrls((previousUrls) => {
        revokeAnalyzerPreviewUrls(previousUrls);
        return nextPreviewUrls;
      });
      setAppliedInputSignature(currentInputSignature);
      setRenderState("");
    } catch (error) {
      if (id !== requestId.current) return;
      setRenderState(error instanceof Error ? error.message : "Ошибка рендера");
    } finally {
      if (id === requestId.current) setIsRendering(false);
    }
  };

  const handleMlInnerCandidateSelect = async (candidate: MlColorCandidate) => {
    const color = candidate.color ?? null;
    const currentMlRecommendation = recommendations.ml;
    const currentVariant = currentMlRecommendation?.variants.find((variant) => variant.decor_style === "signature") ?? null;
    if (!color || !currentMlRecommendation || !currentVariant?.mat?.enabled) return;

    const id = ++requestId.current;
    const updatedVariant = withInnerMatColor(currentVariant, color);
    setIsRendering(true);
    setRenderState("");
    setSelectedDecorStyle("signature");
    setMlInnerOverrideColorId(color.id);
    setRecommendations((current) => ({
      ...current,
      ml: current.ml
        ? {
            ...current.ml,
            variants: current.ml.variants.map((variant) =>
              variant.decor_style === "signature" ? updatedVariant : variant,
            ),
          }
        : current.ml,
    }));

    try {
      const blob = await renderPreview(form, "signature", updatedVariant, "ml", currentMlRecommendation.image_token);
      if (id !== requestId.current) {
        return;
      }
      const nextUrl = URL.createObjectURL(blob);
      setPreviewUrls((previousUrls) => {
        const previousMlSignatureUrl = previousUrls.ml?.signature;
        if (previousMlSignatureUrl) URL.revokeObjectURL(previousMlSignatureUrl);
        return {
          ...previousUrls,
          ml: {
            ...(previousUrls.ml ?? {}),
            signature: nextUrl,
          },
        };
      });
    } catch (error) {
      if (id === requestId.current) {
        setRenderState(error instanceof Error ? error.message : "Не удалось применить ML-кандидат");
      }
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
          </div>
          <button
            type="button"
            className="theme-switch"
            role="switch"
            aria-checked={themeMode === "dark"}
            aria-label={themeMode === "dark" ? "Включить светлую тему" : "Включить темную тему"}
            onClick={() => setThemeMode((current) => (current === "dark" ? "light" : "dark"))}
          >
            <span className="theme-switch-track" aria-hidden="true">
              <span className="theme-switch-symbol theme-switch-sun">☀</span>
              <span className="theme-switch-symbol theme-switch-moon">☾</span>
              <span className="theme-switch-thumb" />
            </span>
          </button>
        </div>

        <form className="config-form">
          <div className="menu-section">
            <div className="compact-upload">
              <button
                type="button"
                className="icon-upload"
                aria-label="Загрузить изображение"
                onClick={() => uploadInputRef.current?.click()}
              >
                <span className="download-glyph" aria-hidden="true">
                  <span />
                </span>
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
            {imageHistory.length > 0 && (
              <details className="image-history-menu">
                <summary>Ранее загруженные</summary>
                <div className="image-history-list">
                  {imageHistory.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="image-history-item"
                      onClick={() => {
                        void handleHistorySelect(item.id);
                      }}
                    >
                      <img src={item.thumbnail} alt="" />
                      <span>
                        <strong>{item.name}</strong>
                        <small>{Math.round(item.size / 1024)} КБ</small>
                      </span>
                    </button>
                  ))}
                </div>
              </details>
            )}
          </div>

          <div className="menu-section size-source-panel">
            <div className="section-label-row">
              <span>Размер работы</span>
            </div>
            <div className="segmented-control" aria-label="Источник физического размера">
              <button
                type="button"
                className={form.sizeSource === "from_file" ? "is-active" : ""}
                disabled={!form.imageInfo}
                onClick={() => handleSizeSourceChange("from_file")}
              >
                Автоматически
              </button>
              <button
                type="button"
                className={form.sizeSource === "manual" ? "is-active" : ""}
                onClick={() => handleSizeSourceChange("manual")}
              >
                Вручную
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

          <fieldset className="menu-section dimensions">
            <legend>
              Физические размеры
              {form.sizeSource === "manual" && form.imageInfo && (
                <button
                  type="button"
                  className={`aspect-toggle ${form.lockAspect ? "is-active" : ""}`}
                  aria-pressed={form.lockAspect}
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

          <div className="menu-section inline-controls" aria-label="Поворот изображения">
            <span className="section-caption">Поворот</span>
            <button
              type="button"
              className={`icon-button ${form.rotationDegrees === -90 ? "is-active" : ""}`}
              aria-pressed={form.rotationDegrees === -90}
              aria-label="Повернуть против часовой стрелки"
              onClick={() => updateForm({ rotationDegrees: form.rotationDegrees === -90 ? 0 : -90 })}
            >
              <span aria-hidden="true">↺</span>
            </button>
            <button
              type="button"
              className={`icon-button ${form.rotationDegrees === 90 ? "is-active" : ""}`}
              aria-pressed={form.rotationDegrees === 90}
              aria-label="Повернуть по часовой стрелке"
              onClick={() => updateForm({ rotationDegrees: form.rotationDegrees === 90 ? 0 : 90 })}
            >
              <span aria-hidden="true">↻</span>
            </button>
          </div>

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
        </form>
      </section>

      <section className="preview-stage" aria-label="Превью оформления">
        <div className="preview-toolbar">
          <div className="preview-meta">
            <div className="preview-meta-row">
              <span>Размер</span>
              <strong className="preview-dimensions">{displayDimension(form.widthMm, 300)} x {displayDimension(form.heightMm, 400)} мм</strong>
            </div>
            <div className="preview-meta-row">
              <span>Исполнение</span>
              <strong>{decorStyleLabels[selectedDecorStyle]}</strong>
            </div>
            <div className="preview-meta-row">
              <span>Интерьер</span>
              <strong>{showInteriorPreview ? interiorScene.label : "Без интерьера"}</strong>
            </div>
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
            <span
              className="apply-button-wrap"
              data-disabled-hint={!isRendering && !hasInputChanges ? "Ничего не было изменено" : undefined}
            >
              <button type="button" className="apply-button" onClick={applyRender} disabled={isApplyDisabled}>
                {isRendering ? "Применяю" : "Применить"}
              </button>
            </span>
            <button
              type="button"
              className="download-button"
              onClick={() => downloadPreview(currentPreviewUrl, selectedDecorStyle)}
              disabled={!currentPreviewUrl}
            >
              Скачать превью
            </button>
          </div>
        </div>
        <div
          ref={previewSurfaceRef}
          className={`render-surface ${showInteriorPreview ? "interior-preview" : "plain-preview"}`}
          style={previewSurfaceStyle}
        >
          {currentPreviewUrl ? (
            <img
              ref={previewImageRef}
              className="framed-art-preview"
              src={currentPreviewUrl}
              alt="Превью оформления"
              style={previewImageStyle}
              onLoad={measurePreview}
              onMouseMove={handlePreviewZoomMove}
              onMouseLeave={() => setPreviewZoom(null)}
            />
          ) : null}
          {currentPreviewUrl && previewMeasure && previewZoom && (
            <PreviewMagnifier imageUrl={currentPreviewUrl} measure={previewMeasure} zoom={previewZoom} />
          )}
          {showSpecOverlay && currentPreviewUrl && selectedVariant && previewMeasure && (
            <SpecOverlay variant={selectedVariant} measure={previewMeasure} />
          )}
          {isRendering && (
            <div className="render-loader" aria-label="Рендер выполняется">
              <FramingLoader />
            </div>
          )}
          {renderState === "Нажмите «Применить»" && !isRendering && (
            <button type="button" className="render-cta" onClick={applyRender} disabled={isApplyDisabled}>
              {renderState}
            </button>
          )}
          {renderState && renderState !== "Нажмите «Применить»" && !isRendering && (
            <div className="render-error">{renderState}</div>
          )}
        </div>
        {selectedDecorStyle === "signature" && mlInnerCandidates.length > 0 && (
          <MlInnerCandidatePanel
            candidates={mlInnerCandidates}
            activeColorId={mlInnerOverrideColorId ?? mlSignatureVariant?.mat?.inner_color?.id ?? null}
            disabled={isRendering}
            onSelect={(candidate) => {
              void handleMlInnerCandidateSelect(candidate);
            }}
          />
        )}
        <div className="result-panel">
          <details
            className="result-details"
            open={showSpecOverlay}
            onToggle={(event) => setShowSpecOverlay(event.currentTarget.open)}
          >
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
          </details>
        </div>
      </section>
    </main>
  );
}

function PreviewMagnifier({
  imageUrl,
  measure,
  zoom,
}: {
  imageUrl: string;
  measure: PreviewMeasure;
  zoom: PreviewZoomState;
}) {
  const zoomFactor = 2;
  const width = Math.min(260, Math.max(190, measure.surfaceWidth * 0.22));
  const height = Math.round(width * 0.68);
  const gap = 18;
  const padding = 14;
  const x =
    zoom.cursorX + gap + width <= measure.surfaceWidth - padding
      ? zoom.cursorX + gap
      : zoom.cursorX - gap - width;
  const y =
    zoom.cursorY + gap + height <= measure.surfaceHeight - padding
      ? zoom.cursorY + gap
      : zoom.cursorY - gap - height;
  const left = clampNumber(x, padding, measure.surfaceWidth - width - padding);
  const top = clampNumber(y, padding, measure.surfaceHeight - height - padding);

  return (
    <div
      className="preview-magnifier"
      style={
        {
          left: `${left}px`,
          top: `${top}px`,
          width: `${width}px`,
          height: `${height}px`,
          backgroundImage: `url(${imageUrl})`,
          backgroundSize: `${measure.imageWidth * zoomFactor}px ${measure.imageHeight * zoomFactor}px`,
          backgroundPosition: `${width / 2 - zoom.relativeX * zoomFactor}px ${
            height / 2 - zoom.relativeY * zoomFactor
          }px`,
        } as CSSProperties
      }
      aria-hidden="true"
    >
      <span>x2</span>
    </div>
  );
}

function SpecOverlay({ variant, measure }: { variant: Recommendation["variants"][number]; measure: PreviewMeasure }) {
  const callouts = buildSpecCallouts(variant, measure);

  return (
    <div className="spec-overlay" aria-label="Параметры оформления на превью">
      <svg
        className="spec-overlay-lines"
        viewBox={`0 0 ${measure.surfaceWidth} ${measure.surfaceHeight}`}
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {callouts.map((item) => (
          <g key={`${item.kind}-line`}>
            <line
              className="spec-overlay-line"
              x1={item.anchorX}
              y1={item.anchorY}
              x2={item.targetX}
              y2={item.targetY}
            />
            <circle className="spec-overlay-dot" cx={item.targetX} cy={item.targetY} r="4" />
          </g>
        ))}
      </svg>
      {callouts.map((item) => (
        <SpecCallout key={item.kind} item={item} />
      ))}
    </div>
  );
}

function SpecCallout({ item }: { item: SpecCalloutData }) {
  return (
    <div
      className={`spec-callout spec-callout-${item.kind}`}
      style={
        {
          "--callout-color": item.color ?? "#D8D6D0",
          left: `${item.x}px`,
          top: `${item.y}px`,
          width: `${item.width}px`,
        } as CSSProperties
      }
    >
      <span className="spec-callout-swatch" aria-hidden="true" />
      <div>
        <strong>{item.title}</strong>
        {item.lines.map((line, index) => (
          <span key={`${line}-${index}`}>{line}</span>
        ))}
      </div>
    </div>
  );
}

function buildSpecCallouts(variant: Recommendation["variants"][number], measure: PreviewMeasure): SpecCalloutData[] {
  const geometry = variant.geometry;
  const scaleX = measure.imageWidth / Math.max(geometry.outer_width_mm, 1);
  const scaleY = measure.imageHeight / Math.max(geometry.outer_height_mm, 1);
  const mmX = (value: number) => measure.imageLeft + value * scaleX;
  const mmY = (value: number) => measure.imageTop + value * scaleY;
  const callouts: SpecCalloutData[] = [];
  const frameTarget = {
    x: mmX(variant.frame.width_mm / 2),
    y: mmY(geometry.outer_height_mm * 0.36),
  };

  callouts.push(
    placeSpecCallout(measure, frameTarget, {
      kind: "frame",
      title: "Рама",
      color: variant.frame.hex,
      lines: [variant.frame.name, `${variant.frame.width_mm} мм`, materialName(variant.frame.material)],
      preferredSide: "left",
      height: 78,
    }),
  );

  if (variant.mat?.enabled) {
    const mat = variant.mat;
    const frameWidth = variant.frame.width_mm;
    const windowLeft = frameWidth + mat.left_mm;
    const windowTop = frameWidth + mat.top_mm;
    const windowRight = windowLeft + geometry.window_width_mm;
    const windowBottom = windowTop + geometry.window_height_mm;
    const outerMatTarget = {
      x: mmX(windowLeft + geometry.window_width_mm * 0.48),
      y: mmY(frameWidth + Math.max(mat.top_mm - (mat.inner_reveal_top_mm ?? 0), 1) * 0.46),
    };

    callouts.push(
      placeSpecCallout(measure, outerMatTarget, {
        kind: "outer-mat",
        title: "Верхнее паспарту",
        color: mat.outer_color?.hex,
        lines: [
          matEdgesLabel(mat),
          mat.outer_color ? `${mat.outer_color.name} ${mat.outer_color.hex}` : "цвет не задан",
        ],
        preferredSide: "right",
        height: 72,
      }),
    );

    if (mat.inner_color) {
      const innerTarget = {
        x: mmX(windowRight + Math.max(mat.inner_reveal_right_mm, 1) * 0.5),
        y: mmY(windowTop + geometry.window_height_mm * 0.42),
      };

      if (innerTarget.x > mmX(geometry.outer_width_mm - frameWidth)) {
        innerTarget.x = mmX(windowLeft - Math.max(mat.inner_reveal_left_mm, 1) * 0.5);
      }

      callouts.push(
        placeSpecCallout(measure, innerTarget, {
          kind: "inner-mat",
          title: "Нижнее паспарту",
          color: mat.inner_color.hex,
          lines: [innerMatRevealLabel(mat), `${mat.inner_color.name} ${mat.inner_color.hex}`],
          preferredSide: windowRight > geometry.outer_width_mm * 0.58 ? "left" : "right",
          height: 72,
        }),
      );
    }
  }

  return avoidCalloutOverlap(callouts, measure);
}

function placeSpecCallout(
  measure: PreviewMeasure,
  target: { x: number; y: number },
  options: {
    kind: SpecCalloutData["kind"];
    title: string;
    color?: string;
    lines: string[];
    preferredSide: "left" | "right";
    height: number;
  },
): SpecCalloutData {
  const padding = 14;
  const gap = 18;
  const width = Math.min(230, Math.max(178, measure.surfaceWidth * 0.24));
  const canUseLeft = measure.imageLeft >= width + gap + padding;
  const canUseRight = measure.surfaceWidth - (measure.imageLeft + measure.imageWidth) >= width + gap + padding;
  const side =
    options.preferredSide === "left"
      ? canUseLeft || !canUseRight
        ? "left"
        : "right"
      : canUseRight || !canUseLeft
        ? "right"
        : "left";
  let x = side === "left" ? measure.imageLeft - width - gap : measure.imageLeft + measure.imageWidth + gap;
  x = clampNumber(x, padding, measure.surfaceWidth - width - padding);
  const y = clampNumber(target.y - options.height / 2, padding, measure.surfaceHeight - options.height - padding);
  const anchorX = side === "left" ? x + width : x;

  return {
    kind: options.kind,
    title: options.title,
    color: options.color,
    lines: options.lines,
    x,
    y,
    width,
    height: options.height,
    anchorX,
    anchorY: y + options.height / 2,
    targetX: target.x,
    targetY: target.y,
  };
}

function avoidCalloutOverlap(items: SpecCalloutData[], measure: PreviewMeasure) {
  const sorted = [...items].sort((a, b) => a.y - b.y);
  const padding = 14;
  const gap = 10;

  sorted.forEach((item, index) => {
    if (index === 0) return;
    const previous = sorted[index - 1];
    const overlapsX = item.x < previous.x + previous.width && item.x + item.width > previous.x;
    if (overlapsX && item.y < previous.y + previous.height + gap) {
      item.y = clampNumber(previous.y + previous.height + gap, padding, measure.surfaceHeight - item.height - padding);
      item.anchorY = item.y + item.height / 2;
    }
  });

  return items;
}

function isSamePreviewMeasure(current: PreviewMeasure | null, next: PreviewMeasure) {
  if (!current) return false;
  return (
    Math.abs(current.surfaceWidth - next.surfaceWidth) < 0.5 &&
    Math.abs(current.surfaceHeight - next.surfaceHeight) < 0.5 &&
    Math.abs(current.imageLeft - next.imageLeft) < 0.5 &&
    Math.abs(current.imageTop - next.imageTop) < 0.5 &&
    Math.abs(current.imageWidth - next.imageWidth) < 0.5 &&
    Math.abs(current.imageHeight - next.imageHeight) < 0.5
  );
}

function clampNumber(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
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
  const selectId = useId();

  return (
    <div className="select-field">
      <div className="field-label-row">
        <label htmlFor={selectId}>{label}</label>
      </div>
      <select id={selectId} value={value} onChange={(event) => onChange(event.target.value as T)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
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

function FramingLoader() {
  return (
    <span className="framing-loader" aria-hidden="true">
      <span className="framing-loader-frame" />
      <span className="framing-loader-rail framing-loader-rail-top" />
      <span className="framing-loader-rail framing-loader-rail-bottom" />
      <span className="framing-loader-tool" />
    </span>
  );
}

function MlInnerCandidatePanel({
  candidates,
  activeColorId,
  disabled,
  onSelect,
}: {
  candidates: MlColorCandidate[];
  activeColorId: string | null;
  disabled: boolean;
  onSelect: (candidate: MlColorCandidate) => void;
}) {
  return (
    <section className="ml-candidate-panel" aria-label="ML-кандидаты цвета нижнего паспарту">
      <div>
        <strong>Кандидаты цвета нижнего паспарту</strong>
        <span>Нажмите на оттенок, чтобы примерить его в Signature</span>
      </div>
      <div className="ml-candidate-list">
        {candidates.map((candidate, index) => {
          const color = candidate.color;
          const isActive = Boolean(color?.id && color.id === activeColorId);
          return (
            <button
              key={`${candidate.color_id}-${index}`}
              type="button"
              className={isActive ? "is-active" : ""}
              disabled={disabled || !color}
              onClick={() => onSelect(candidate)}
            >
              <span className="ml-candidate-swatch" style={{ background: color?.hex ?? "#D8D6D0" }} />
              <span>
                <strong>{color ? color.name : candidate.color_id}</strong>
                <small>{color?.hex ?? candidate.color_id}</small>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function frameSpec(variant: Recommendation["variants"][number] | null) {
  if (!variant) return "—";
  return `${variant.frame.width_mm} мм, ${materialName(variant.frame.material)}, ${variant.frame.name}`;
}

function matSpec(variant: Recommendation["variants"][number] | null) {
  if (!variant?.mat?.enabled) return "нет";
  const mat = variant.mat;
  const outerColor = mat.outer_color?.hex ?? "цвет не задан";
  const base = `${mat.left_mm}/${mat.top_mm}/${mat.right_mm}/${mat.bottom_mm} мм, верхнее ${outerColor}`;
  if (!mat.inner_color) return base;

  return (
    `${base}; нижнее ${mat.inner_color.hex}, раскрытие ` +
    `${mat.inner_reveal_left_mm}/${mat.inner_reveal_top_mm}/${mat.inner_reveal_right_mm}/${mat.inner_reveal_bottom_mm} мм`
  );
}

function matEdgesLabel(mat: NonNullable<Recommendation["variants"][number]["mat"]>) {
  return `${mat.left_mm}/${mat.top_mm}/${mat.right_mm}/${mat.bottom_mm} мм`;
}

function innerMatRevealLabel(mat: NonNullable<Recommendation["variants"][number]["mat"]>) {
  return `${mat.inner_reveal_left_mm}/${mat.inner_reveal_top_mm}/${mat.inner_reveal_right_mm}/${mat.inner_reveal_bottom_mm} мм`;
}

function materialName(value?: string) {
  return value === "aluminum" ? "алюминий" : "дерево";
}

function mlInnerMatCandidates(variant: Recommendation["variants"][number] | null): MlColorCandidate[] {
  const top = variant?.mat?.ml_prediction?.predictions?.inner_mat_color_id?.top ?? [];
  return top.filter((candidate) => candidate.color?.id && candidate.color?.hex).slice(0, 3);
}

function withInnerMatColor(variant: Recommendation["variants"][number], color: MatColor): Recommendation["variants"][number] {
  if (!variant.mat) return variant;
  return {
    ...variant,
    mat: {
      ...variant.mat,
      inner_color: {
        id: color.id,
        name: color.name,
        hex: color.hex,
      },
      color_source: "ml_candidate_override",
    },
  };
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

function formInputSignature(form: FormState) {
  return JSON.stringify({
    image: form.image
      ? {
          name: form.image.name,
          size: form.image.size,
          type: form.image.type,
          lastModified: form.image.lastModified,
        }
      : null,
    widthMm: form.widthMm,
    heightMm: form.heightMm,
    sizeSource: form.sizeSource,
    printPpi: form.printPpi,
    lockAspect: form.lockAspect,
    imageInfo: form.imageInfo,
    artworkType: form.artworkType,
    interiorStyle: form.interiorStyle,
    matColorAnalyzer: ACTIVE_MAT_COLOR_ANALYZER,
    rotationDegrees: form.rotationDegrees,
    matSizeConfig: form.matSizeConfig,
  });
}

function revokePreviewUrls(previewUrls: Partial<Record<DecorStyle, string>>) {
  for (const previewUrl of Object.values(previewUrls)) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }
}

function revokeAnalyzerPreviewUrls(previewUrls: Partial<Record<MatColorAnalyzer, Partial<Record<DecorStyle, string>>>>) {
  for (const analyzerPreviewUrls of Object.values(previewUrls)) {
    if (analyzerPreviewUrls) revokePreviewUrls(analyzerPreviewUrls);
  }
}

async function loadImageHistory(): Promise<ImageHistoryItem[]> {
  const db = await openImageHistoryDb();
  const transaction = db.transaction(IMAGE_HISTORY_STORE, "readonly");
  const store = transaction.objectStore(IMAGE_HISTORY_STORE);
  const records = await requestResult<StoredImageHistoryItem[]>(store.getAll());
  db.close();

  return records
    .sort((first, second) => second.updatedAt - first.updatedAt)
    .slice(0, IMAGE_HISTORY_LIMIT)
    .map(publicHistoryItem);
}

async function saveImageToHistory(file: File): Promise<ImageHistoryItem[]> {
  const db = await openImageHistoryDb();
  const now = Date.now();
  const record: StoredImageHistoryItem = {
    id: imageHistoryId(file),
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: file.lastModified,
    updatedAt: now,
    thumbnail: await createImageThumbnail(file),
    blob: file,
  };

  const writeTransaction = db.transaction(IMAGE_HISTORY_STORE, "readwrite");
  const writeStore = writeTransaction.objectStore(IMAGE_HISTORY_STORE);
  writeStore.put(record);
  await transactionComplete(writeTransaction);

  const readTransaction = db.transaction(IMAGE_HISTORY_STORE, "readonly");
  const readStore = readTransaction.objectStore(IMAGE_HISTORY_STORE);
  const records = await requestResult<StoredImageHistoryItem[]>(readStore.getAll());
  const sortedRecords = records.sort((first, second) => second.updatedAt - first.updatedAt);
  await transactionComplete(readTransaction);

  if (sortedRecords.length > IMAGE_HISTORY_LIMIT) {
    const cleanupTransaction = db.transaction(IMAGE_HISTORY_STORE, "readwrite");
    const cleanupStore = cleanupTransaction.objectStore(IMAGE_HISTORY_STORE);
    for (const item of sortedRecords.slice(IMAGE_HISTORY_LIMIT)) {
      cleanupStore.delete(item.id);
    }
    await transactionComplete(cleanupTransaction);
  }

  db.close();
  return sortedRecords.slice(0, IMAGE_HISTORY_LIMIT).map(publicHistoryItem);
}

async function getStoredImage(id: string): Promise<StoredImageHistoryItem | null> {
  const db = await openImageHistoryDb();
  const transaction = db.transaction(IMAGE_HISTORY_STORE, "readonly");
  const store = transaction.objectStore(IMAGE_HISTORY_STORE);
  const record = await requestResult<StoredImageHistoryItem | undefined>(store.get(id));
  db.close();
  return record ?? null;
}

async function touchHistoryImage(item: StoredImageHistoryItem) {
  const db = await openImageHistoryDb();
  const transaction = db.transaction(IMAGE_HISTORY_STORE, "readwrite");
  const store = transaction.objectStore(IMAGE_HISTORY_STORE);
  store.put({ ...item, updatedAt: Date.now() });
  await transactionComplete(transaction);
  db.close();
}

function openImageHistoryDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(new Error("IndexedDB is unavailable"));
      return;
    }

    const request = indexedDB.open(IMAGE_HISTORY_DB, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(IMAGE_HISTORY_STORE)) {
        db.createObjectStore(IMAGE_HISTORY_STORE, { keyPath: "id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("Image history is unavailable"));
  });
}

function requestResult<T>(request: IDBRequest): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result as T);
    request.onerror = () => reject(request.error ?? new Error("IndexedDB request failed"));
  });
}

function transactionComplete(transaction: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error ?? new Error("IndexedDB transaction failed"));
    transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB transaction aborted"));
  });
}

function publicHistoryItem(item: StoredImageHistoryItem): ImageHistoryItem {
  return {
    id: item.id,
    name: item.name,
    size: item.size,
    type: item.type,
    updatedAt: item.updatedAt,
    thumbnail: item.thumbnail,
  };
}

function imageHistoryId(file: File) {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function createImageThumbnail(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      const size = 72;
      const scale = Math.max(size / image.naturalWidth, size / image.naturalHeight);
      const width = Math.round(image.naturalWidth * scale);
      const height = Math.round(image.naturalHeight * scale);
      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = size;

      const context = canvas.getContext("2d");
      if (!context) {
        URL.revokeObjectURL(objectUrl);
        reject(new Error("Canvas is unavailable"));
        return;
      }

      context.drawImage(image, (size - width) / 2, (size - height) / 2, width, height);
      URL.revokeObjectURL(objectUrl);
      resolve(canvas.toDataURL("image/jpeg", 0.72));
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Image thumbnail is unavailable"));
    };
    image.src = objectUrl;
  });
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
