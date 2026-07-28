import { useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

import { recommend, renderPreview } from "./api";
import type {
  ArtworkType,
  ColorSample,
  DecisionNode,
  DecorStyle,
  FormState,
  InteriorStyle,
  Recommendation,
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

export default function App() {
  const [form, setForm] = useState<FormState>({
    widthMm: "300",
    heightMm: "400",
    artworkType: "poster",
    interiorStyle: "minimal",
    image: null,
    rotateArtwork: false,
  });
  const [selectedDecorStyle, setSelectedDecorStyle] = useState<DecorStyle>("standard");
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [renderState, setRenderState] = useState("Нажмите «Применить»");
  const [isRendering, setIsRendering] = useState(false);
  const requestId = useRef(0);

  const selectedVariant = useMemo(() => {
    return recommendation?.variants.find((variant) => variant.decor_style === selectedDecorStyle) ?? null;
  }, [recommendation, selectedDecorStyle]);

  const palette = recommendation?.image_analysis.palette;

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
    clearPreview();
    setRenderState("Нажмите «Применить»");
  };

  const handleDecorStyleChange = (decorStyle: DecorStyle) => {
    requestId.current += 1;
    setIsRendering(false);
    setSelectedDecorStyle(decorStyle);
    clearPreview();
    setRenderState("Нажмите «Применить»");
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
    <main className="app-shell">
      <section className="control-panel" aria-label="Параметры картины">
        <div className="brand-row">
          <div>
            <p className="eyebrow">Placed MVP</p>
            <h1>Подбор багета</h1>
          </div>
          <output className="status-pill">{selectedVariant?.geometry.size_profile ?? "medium"}</output>
        </div>

        <form className="config-form">
          <label className="upload-zone" htmlFor="artUpload">
            <input
              id="artUpload"
              type="file"
              accept="image/*"
              onChange={(event) => updateForm({ image: event.target.files?.[0] ?? null })}
            />
            <span className="upload-icon" aria-hidden="true">+</span>
            <span>
              <strong>{form.image?.name ?? "Загрузить изображение"}</strong>
              <small>{form.image ? `${Math.round(form.image.size / 1024)} КБ` : "JPG, PNG или WEBP"}</small>
            </span>
          </label>

          <fieldset className="dimensions">
            <legend>Физические размеры</legend>
            <label>
              <span>Ширина, мм</span>
              <input
                type="number"
                min="50"
                max="3000"
                step="1"
                value={form.widthMm}
                onChange={(event) => updateForm({ widthMm: event.target.value })}
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
                onChange={(event) => updateForm({ heightMm: event.target.value })}
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

          <RadioGrid
            label="Тип работы"
            className="artwork-grid"
            name="artworkType"
            value={form.artworkType}
            options={artworkOptions}
            onChange={(artworkType) => updateForm({ artworkType })}
          />

          <RadioGrid
            label="Стиль интерьера"
            className="style-grid"
            name="interiorStyle"
            value={form.interiorStyle}
            options={interiorOptions}
            onChange={(interiorStyle) => updateForm({ interiorStyle })}
          />
        </form>

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

        <section className="recommendation" aria-label="Рекомендация">
          <div className="recommendation-head">
            <h2>{selectedVariant?.title ?? "Standard: спокойная мастерская база"}</h2>
          </div>
          <dl className="spec-list">
            <SpecItem label="Багет">{frameSpec(selectedVariant)}</SpecItem>
            <SpecItem label="Паспарту">{matSpec(selectedVariant)}</SpecItem>
            <SpecItem label="Защита">{glassName(selectedVariant?.glass?.type)}</SpecItem>
            <SpecItem label="Итоговый размер">
              {selectedVariant
                ? `${selectedVariant.geometry.outer_width_mm} x ${selectedVariant.geometry.outer_height_mm} мм`
                : "—"}
            </SpecItem>
          </dl>
          <p className="reason-text">{selectedVariant?.reasons.join(" ")}</p>
          <div className="palette-row" aria-label="Цвета изображения">
            <PaletteChip label="Основной" color={palette?.primary} />
            <PaletteChip label="Второй" color={palette?.secondary} />
            <PaletteChip label="Акцент" color={palette?.accent} />
          </div>
        </section>

        <section className="debug-panel" aria-label="Дерево решений">
          <h2>Дерево решений</h2>
          <DecisionTree nodes={selectedVariant?.decision_tree ?? []} />
        </section>
      </section>

      <section className="preview-stage" aria-label="Превью оформления">
        <div className="preview-toolbar">
          <div>
            <span>{displayDimension(form.widthMm, 300)} x {displayDimension(form.heightMm, 400)} мм</span>
            <strong>{selectedDecorStyle.toUpperCase()}</strong>
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
        <div className="render-surface">
          {previewUrl && <img src={previewUrl} alt="Превью оформления" />}
          <div className={`render-state ${renderState ? "is-visible" : ""} ${isRendering ? "is-loading" : ""}`}>
            {isRendering && <span className="loader" aria-hidden="true" />}
            <span>{renderState}</span>
          </div>
        </div>
      </section>
    </main>
  );
}

function RadioGrid<T extends string>({
  label,
  className,
  name,
  value,
  options,
  onChange,
}: {
  label: string;
  className: string;
  name: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
}) {
  return (
    <fieldset>
      <legend>{label}</legend>
      <div className={className} role="radiogroup" aria-label={label}>
        {options.map((option) => (
          <label key={option.value}>
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
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
      <span>{color ? `${label}: ${color.hex}` : `${label}: нет`}</span>
    </div>
  );
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

function frameSpec(variant: Recommendation["variants"][number] | null) {
  if (!variant) return "—";
  return `${variant.frame.width_mm} мм, ${materialName(variant.frame.material)}, ${variant.frame.name}`;
}

function matSpec(variant: Recommendation["variants"][number] | null) {
  if (!variant?.mat?.enabled) return "Без паспарту";
  const inner = variant.mat.inner_color ? ` + кант ${variant.mat.inner_color.name}` : "";
  return `${variant.mat.left_mm}/${variant.mat.top_mm}/${variant.mat.bottom_mm} мм, ${variant.mat.outer_color?.name}${inner}`;
}

function materialName(value?: string) {
  return value === "aluminum" ? "алюминий" : "дерево";
}

function glassName(value?: string) {
  if (!value || value === "none") return "Без стекла";
  if (value === "museum") return "Музейное стекло";
  if (value === "uv") return "UV-стекло";
  return "Обычное стекло";
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
