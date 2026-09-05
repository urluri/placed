import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import {
  analyzeImage,
  colorById,
  deleteAnnotation,
  deleteImage,
  exportDatasetUrl,
  labelerImageUrl,
  listAnnotations,
  listImages,
  loadPalette,
  matColorLabel,
  saveAnnotation,
  uploadImageUrl,
  uploadImages,
  type LabelerAnalysis,
  type LabelerAnnotation,
  type LabelerImage,
  type PaletteColor,
} from "./labelerApi";
import type { ArtworkType, ColorSample, DecorStyle, MatSpec } from "./types";
import "./labeler.css";

const artworkOptions: Array<{ value: ArtworkType; label: string }> = [
  { value: "poster", label: "Постер" },
  { value: "photo", label: "Фото" },
  { value: "watercolor", label: "Акварель" },
  { value: "engraving", label: "Гравюра" },
  { value: "botanical", label: "Ботаническая иллюстрация" },
  { value: "canvas", label: "Холст" },
  { value: "volumetric", label: "Объемная работа" },
];

type ActiveLayer = "outer" | "inner";

export default function LabelerApp() {
  const [images, setImages] = useState<LabelerImage[]>([]);
  const [annotations, setAnnotations] = useState<LabelerAnnotation[]>([]);
  const [hiddenAnnotationIds, setHiddenAnnotationIds] = useState<string[]>([]);
  const [palette, setPalette] = useState<PaletteColor[]>([]);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [artworkType, setArtworkType] = useState<ArtworkType>("poster");
  const [decorStyle, setDecorStyle] = useState<DecorStyle>("signature");
  const [analysis, setAnalysis] = useState<LabelerAnalysis | null>(null);
  const [outerColorId, setOuterColorId] = useState<string | null>(null);
  const [innerColorId, setInnerColorId] = useState<string | null>(null);
  const [activeLayer, setActiveLayer] = useState<ActiveLayer>("inner");
  const [confidence, setConfidence] = useState<"low" | "medium" | "high">("high");
  const [note, setNote] = useState("");
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("Готов к разметке");
  const [isBusy, setIsBusy] = useState(false);

  const selectedImage = images.find((image) => image.id === selectedImageId) ?? null;
  const currentAnnotation = useMemo(
    () =>
      annotations.find(
        (item) =>
          item.image_id === selectedImageId &&
          item.artwork_type === artworkType &&
          item.decor_style === decorStyle,
      ) ?? null,
    [annotations, artworkType, decorStyle, selectedImageId],
  );
  const visibleAnnotations = useMemo(
    () => annotations.filter((item) => !hiddenAnnotationIds.includes(item.id)),
    [annotations, hiddenAnnotationIds],
  );
  const algorithmOuter = colorById(palette, analysis?.algorithm_suggestion.outer_mat_color_id);
  const algorithmInner = colorById(palette, analysis?.algorithm_suggestion.inner_mat_color_id);
  const selectedOuter = colorById(palette, outerColorId);
  const selectedInner = colorById(palette, innerColorId);
  const activeMatLabel = activeLayer === "inner" && decorStyle === "signature" ? "В нижнее" : "В верхнее";
  const canSave = Boolean(
    selectedImage &&
      analysis?.variant.mat?.enabled &&
      outerColorId &&
      (decorStyle === "standard" || innerColorId),
  );

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!selectedImageId) {
      setAnalysis(null);
      return;
    }
    void refreshAnalysis(selectedImageId, artworkType, decorStyle);
  }, [artworkType, decorStyle, selectedImageId]);

  async function bootstrap() {
    await run("Загружаю labeler", async () => {
      const [imageResult, paletteResult, annotationResult] = await Promise.all([
        listImages(),
        loadPalette(),
        listAnnotations(),
      ]);
      setImages(imageResult.images);
      setPalette(paletteResult.colors);
      setAnnotations(annotationResult.annotations);
      setSelectedImageId(imageResult.images[0]?.id ?? null);
    });
  }

  async function refreshAnalysis(imageId: string, nextArtworkType: ArtworkType, nextDecorStyle: DecorStyle) {
    await run("Считаю признаки и конструктив", async () => {
      const result = await analyzeImage(imageId, nextArtworkType, nextDecorStyle);
      setAnalysis(result);
      const existing = annotations.find(
        (item) =>
          item.image_id === imageId &&
          item.artwork_type === nextArtworkType &&
          item.decor_style === nextDecorStyle,
      );
      setOuterColorId(existing?.label.outer_mat_color_id ?? null);
      setInnerColorId(existing?.label.inner_mat_color_id ?? null);
      setConfidence(existing?.confidence ?? "high");
      setNote(existing?.note ?? "");
      setActiveLayer(nextDecorStyle === "signature" ? "inner" : "outer");
    });
  }

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    await run("Загружаю изображения", async () => {
      const result = await uploadImages(files);
      const nextImages = mergeImages(result.images, images);
      setImages(nextImages);
      setSelectedImageId(result.images[0]?.id ?? selectedImageId);
    });
  }

  async function handleUrlUpload() {
    if (!url.trim()) return;
    await run("Загружаю изображение по ссылке", async () => {
      const result = await uploadImageUrl(url.trim());
      setImages(mergeImages([result.image], images));
      setSelectedImageId(result.image.id);
      setUrl("");
    });
  }

  async function handleDelete(imageId: string) {
    await run("Удаляю изображение", async () => {
      await deleteImage(imageId);
      const nextImages = images.filter((image) => image.id !== imageId);
      setImages(nextImages);
      setAnnotations(annotations.filter((item) => item.image_id !== imageId));
      if (selectedImageId === imageId) {
        setSelectedImageId(nextImages[0]?.id ?? null);
      }
    });
  }

  async function handleDeleteAnnotation(annotationId: string) {
    await run("Удаляю разметку", async () => {
      await deleteAnnotation(annotationId);
      setAnnotations((items) => items.filter((item) => item.id !== annotationId));
      setHiddenAnnotationIds((ids) => ids.filter((id) => id !== annotationId));
      if (currentAnnotation?.id === annotationId) {
        setOuterColorId(null);
        setInnerColorId(null);
        setConfidence("high");
        setNote("");
      }
    });
  }

  function handleClearDatasetView() {
    setHiddenAnnotationIds((ids) => Array.from(new Set([...ids, ...visibleAnnotations.map((item) => item.id)])));
  }

  async function handleSave() {
    if (!selectedImage || !canSave) return;
    await run("Сохраняю разметку", async () => {
      const result = await saveAnnotation({
        imageId: selectedImage.id,
        artworkType,
        decorStyle,
        outerMatColorId: outerColorId,
        innerMatColorId: decorStyle === "signature" ? innerColorId : null,
        confidence,
        note,
      });
      setAnnotations([
        result.annotation,
        ...annotations.filter((item) => item.id !== result.annotation.id),
      ]);
      setHiddenAnnotationIds((ids) => ids.filter((id) => id !== result.annotation.id));
      setStatus("Разметка сохранена");
    });
  }

  function applyColor(color: PaletteColor) {
    if (activeLayer === "outer" || decorStyle === "standard") {
      setOuterColorId(color.id);
    } else {
      setInnerColorId(color.id);
    }
  }

  async function run(nextStatus: string, task: () => Promise<void>) {
    setIsBusy(true);
    setStatus(nextStatus);
    try {
      await task();
      setStatus("Готов к разметке");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Что-то пошло не так");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main className="labeler-shell">
      <aside className="labeler-sidebar">
        <section className="labeler-panel">
          <div className="panel-title">
            <span>Изображения</span>
            <small>{images.length}</small>
          </div>
          <label className="upload-tile">
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(event) => {
                void handleFiles(event.currentTarget.files);
                event.currentTarget.value = "";
              }}
            />
            <span>Загрузить пачку</span>
          </label>
          <div className="url-row">
            <input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://..." />
            <button onClick={() => void handleUrlUpload()} disabled={!url.trim() || isBusy}>
              Добавить
            </button>
          </div>
          <div className="image-list">
            {images.map((image) => (
              <button
                key={image.id}
                className={`image-card ${image.id === selectedImageId ? "is-active" : ""}`}
                onClick={() => setSelectedImageId(image.id)}
              >
                <img src={labelerImageUrl(image)} alt="" />
                <span>
                  <strong>{image.name}</strong>
                  <small>{image.width_px} x {image.height_px}px · {image.width_mm} x {image.height_mm}мм</small>
                </span>
                <i
                  role="button"
                  tabIndex={0}
                  onClick={(event) => {
                    event.stopPropagation();
                    void handleDelete(image.id);
                  }}
                >
                  ×
                </i>
              </button>
            ))}
          </div>
        </section>
        <section className="labeler-panel dataset-panel">
          <div className="panel-title">
            <span>Датасет</span>
            <small>{visibleAnnotations.length}/{annotations.length}</small>
          </div>
          <div className="dataset-actions">
            <a className="export-link" href={exportDatasetUrl()} download>
              Выгрузить JSONL
            </a>
            <button onClick={handleClearDatasetView} disabled={!visibleAnnotations.length}>
              Очистить все
            </button>
          </div>
          <div className="dataset-list">
            {!visibleAnnotations.length ? <p className="empty-dataset">Миниатюры датасета скрыты или еще не созданы.</p> : null}
            {visibleAnnotations.map((item) => {
              const image = images.find((candidate) => candidate.id === item.image_id);
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setSelectedImageId(item.image_id);
                    setArtworkType(item.artwork_type);
                    setDecorStyle(item.decor_style);
                  }}
                >
                  {image ? <img src={labelerImageUrl(image)} alt="" /> : null}
                  <span>
                    <strong>{item.label.inner_mat_color_id || item.label.outer_mat_color_id}</strong>
                    <small>{item.artwork_type} · {item.decor_style}</small>
                  </span>
                  <i
                    role="button"
                    tabIndex={0}
                    onClick={(event) => {
                      event.stopPropagation();
                      void handleDeleteAnnotation(item.id);
                    }}
                  >
                    ×
                  </i>
                </button>
              );
            })}
          </div>
        </section>
      </aside>

      <section className="labeler-workspace">
        <header className="labeler-header">
          <div>
            <h1>Placed Labeler</h1>
            <p>{selectedImage?.name ?? "Загрузите изображения для разметки паспарту"}</p>
          </div>
          <div className={`labeler-status ${isBusy ? "is-busy" : ""}`}>{status}</div>
        </header>

        <section className="context-bar">
          <label>
            Тип работы
            <select value={artworkType} onChange={(event) => setArtworkType(event.target.value as ArtworkType)}>
              {artworkOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Исполнение
            <select value={decorStyle} onChange={(event) => setDecorStyle(event.target.value as DecorStyle)}>
              <option value="standard">Standard</option>
              <option value="signature">Signature</option>
            </select>
          </label>
          <div className="context-chip">
            Размер по файлу: {selectedImage ? `${selectedImage.width_mm} x ${selectedImage.height_mm} мм` : "—"}
          </div>
          <div className="context-chip">Профиль: {analysis?.context.size_profile ?? "—"}</div>
        </section>

        <section className="studio-grid">
          <div className="studio-card">
            <Studio
              image={selectedImage}
              analysis={analysis}
              activeLayer={activeLayer}
              outerColor={selectedOuter}
              innerColor={selectedInner}
              decorStyle={decorStyle}
              onLayerChange={setActiveLayer}
            />
          </div>
          <aside className="analysis-card">
            <h2>Расчеты</h2>
            <ColorFact title="Основной" sample={analysis?.image_analysis.palette.primary} />
            <ColorFact title="Вторичный" sample={analysis?.image_analysis.palette.secondary} />
            <ColorFact title="Акцент" sample={analysis?.image_analysis.palette.accent?.selected ?? null} />
            <AccentCandidates accent={analysis?.image_analysis.palette.accent ?? null} />
            <dl className="metric-list">
              <dt>Температура</dt>
              <dd>{analysis?.image_analysis.temperature ?? "—"}</dd>
              <dt>Светлота</dt>
              <dd>{analysis?.image_analysis.lightness ?? "—"}</dd>
              <dt>Насыщенность</dt>
              <dd>{analysis?.image_analysis.chroma_level ?? "—"}</dd>
              <dt>Заполненность</dt>
              <dd>{analysis?.image_analysis.frame_occupancy ?? "—"}</dd>
              <dt>Контраст</dt>
              <dd>{analysis?.image_analysis.contrast ?? "—"}</dd>
            </dl>
            <h2>Выбор</h2>
            <div className="selected-colors">
              <button className={activeLayer === "outer" ? "is-active" : ""} onClick={() => setActiveLayer("outer")}>
                Верхнее: {matColorLabel(selectedOuter)}
              </button>
              <button
                className={activeLayer === "inner" ? "is-active" : ""}
                onClick={() => setActiveLayer("inner")}
                disabled={decorStyle !== "signature"}
              >
                Нижнее: {decorStyle === "signature" ? matColorLabel(selectedInner) : "не используется"}
              </button>
            </div>
            <label className="confidence-control">
              Уверенность
              <select value={confidence} onChange={(event) => setConfidence(event.target.value as typeof confidence)}>
                <option value="high">high</option>
                <option value="medium">medium</option>
                <option value="low">low</option>
              </select>
            </label>
            <textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Комментарий к разметке" />
            <button className="save-button" onClick={() => void handleSave()} disabled={!canSave || isBusy}>
              Сохранить
            </button>
            {currentAnnotation ? <p className="saved-note">Эта комбинация уже есть в датасете.</p> : null}
          </aside>
        </section>

        <section className="palette-zone">
          <div className="palette-block">
            <h2>Рекомендации алгоритма</h2>
            <div className="swatch-row">
              {algorithmOuter ? <Swatch color={algorithmOuter} onClick={applyColor} label={activeMatLabel} /> : null}
              {decorStyle === "signature" && algorithmInner ? (
                <Swatch color={algorithmInner} onClick={applyColor} label={activeMatLabel} />
              ) : null}
            </div>
          </div>
          <div className="palette-block">
            <h2>Палитра placed</h2>
            <div className="palette-grid">
              {palette.map((color) => (
                <Swatch key={color.id} color={color} onClick={applyColor} />
              ))}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function Studio({
  image,
  analysis,
  activeLayer,
  outerColor,
  innerColor,
  decorStyle,
  onLayerChange,
}: {
  image: LabelerImage | null;
  analysis: LabelerAnalysis | null;
  activeLayer: ActiveLayer;
  outerColor: PaletteColor | null;
  innerColor: PaletteColor | null;
  decorStyle: DecorStyle;
  onLayerChange: (layer: ActiveLayer) => void;
}) {
  const mat = analysis?.variant.mat;
  if (!image || !analysis || !mat?.enabled) {
    return <div className="empty-studio">Выберите изображение, для которого используется паспарту.</div>;
  }

  const sizes = studioSizes(mat, analysis.variant.geometry.mat_outer_width_mm, analysis.variant.geometry.mat_outer_height_mm);
  const outerStyle = {
    width: sizes.outerWidth,
    height: sizes.outerHeight,
    padding: `${sizes.outerTop}px ${sizes.outerRight}px ${sizes.outerBottom}px ${sizes.outerLeft}px`,
    background: outerColor?.hex,
  } as CSSProperties;
  const innerStyle = {
    padding: `${sizes.innerTop}px ${sizes.innerRight}px ${sizes.innerBottom}px ${sizes.innerLeft}px`,
    background: innerColor?.hex,
  } as CSSProperties;

  return (
    <div className="studio-stage">
      <div
        className={`mat-wire outer ${activeLayer === "outer" ? "is-active" : ""} ${outerColor ? "has-color" : ""}`}
        style={outerStyle}
        onClick={() => onLayerChange("outer")}
      >
        {decorStyle === "signature" ? (
          <div
            className={`mat-wire inner ${activeLayer === "inner" ? "is-active" : ""} ${innerColor ? "has-color" : ""}`}
            style={innerStyle}
            onClick={(event) => {
              event.stopPropagation();
              onLayerChange("inner");
            }}
          >
            <img src={labelerImageUrl(image)} alt="" />
          </div>
        ) : (
          <img src={labelerImageUrl(image)} alt="" />
        )}
      </div>
    </div>
  );
}

function mergeImages(incoming: LabelerImage[], existing: LabelerImage[]) {
  const byId = new Map<string, LabelerImage>();
  [...incoming, ...existing].forEach((image) => {
    if (!byId.has(image.id)) {
      byId.set(image.id, image);
    }
  });
  return Array.from(byId.values());
}

function studioSizes(mat: MatSpec, matOuterWidth: number, matOuterHeight: number) {
  const maxWidth = 760;
  const maxHeight = 520;
  const scale = Math.min(maxWidth / matOuterWidth, maxHeight / matOuterHeight, 1.25);
  const innerLeft = mat.inner_reveal_left_mm || 0;
  const innerRight = mat.inner_reveal_right_mm || 0;
  const innerTop = mat.inner_reveal_top_mm || 0;
  const innerBottom = mat.inner_reveal_bottom_mm || 0;

  return {
    outerWidth: Math.round(matOuterWidth * scale),
    outerHeight: Math.round(matOuterHeight * scale),
    outerLeft: Math.max(0, Math.round((mat.left_mm - innerLeft) * scale)),
    outerRight: Math.max(0, Math.round((mat.right_mm - innerRight) * scale)),
    outerTop: Math.max(0, Math.round((mat.top_mm - innerTop) * scale)),
    outerBottom: Math.max(0, Math.round((mat.bottom_mm - innerBottom) * scale)),
    innerLeft: Math.round(innerLeft * scale),
    innerRight: Math.round(innerRight * scale),
    innerTop: Math.round(innerTop * scale),
    innerBottom: Math.round(innerBottom * scale),
  };
}

function ColorFact({ title, sample }: { title: string; sample?: ColorSample | null }) {
  return (
    <div className="color-fact">
      <span style={{ background: sample?.hex ?? "#ddd" }} />
      <div>
        <strong>{title}</strong>
        <small>{sample ? `${sample.hex} · ${sample.family} · ${(sample.share * 100).toFixed(1)}%` : "—"}</small>
      </div>
    </div>
  );
}

function AccentCandidates({
  accent,
}: {
  accent: NonNullable<LabelerAnalysis["image_analysis"]["palette"]["accent"]> | null;
}) {
  const entries = Object.entries(accent?.candidates ?? {}).filter(([, sample]) => sample);
  if (!entries.length) {
    return null;
  }

  const labels: Record<string, string> = {
    pop: "Контрастный",
    temperature: "По температуре",
    light: "По светлоте",
    area: "По площади",
  };

  return (
    <div className="accent-candidates">
      <strong>Кандидаты акцента</strong>
      {entries.map(([source, sample]) => (
        <div key={source} className="accent-candidate">
          <span style={{ background: sample?.hex }} />
          <small>
            {labels[source] ?? source}: {sample?.hex}
            {accent?.scores?.[source] !== undefined ? ` · ${accent.scores[source]}` : ""}
          </small>
        </div>
      ))}
    </div>
  );
}

function Swatch({
  color,
  onClick,
  label,
}: {
  color: PaletteColor;
  onClick: (color: PaletteColor) => void;
  label?: string;
}) {
  return (
    <button className="palette-swatch" onClick={() => onClick(color)} title={`${color.name} ${color.hex}`}>
      <span style={{ background: color.hex }} />
      <strong>{label ?? color.id}</strong>
      <small>{color.name}</small>
    </button>
  );
}
