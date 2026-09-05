import type { ArtworkType, ColorSample, DecorStyle, DecorationVariant, MatColor } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").trim();

export type LabelerImage = {
  id: string;
  name: string;
  source: "local" | "url";
  source_url: string | null;
  sha256: string;
  width_px: number;
  height_px: number;
  width_mm: number;
  height_mm: number;
  created_at: string;
  image_url: string;
};

export type PaletteColor = {
  id: string;
  name: string;
  hex: string;
  family: string;
  role: string;
};

export type LabelerAnalysis = {
  image: LabelerImage;
  context: {
    artwork_type: ArtworkType;
    decor_style: DecorStyle;
    width_mm: number;
    height_mm: number;
    size_profile: string;
  };
  image_analysis: {
    palette: {
      primary: ColorSample | null;
      secondary: ColorSample | null;
      accent: {
        selected: ColorSample | null;
        candidates: Record<string, ColorSample | null>;
        scores?: Record<string, number>;
        source: string | null;
        confidence: string;
      } | null;
    };
    temperature: string;
    lightness: string;
    chroma_level: string;
    monochrome: string;
    frame_occupancy: string;
    contrast: string;
    metrics?: Record<string, number>;
  };
  variant: DecorationVariant;
  constructive: {
    mat_enabled: boolean;
    outer_mat_mm: { left: number; right: number; top: number; bottom: number };
    inner_reveal_mm: { left: number; right: number; top: number; bottom: number };
    overlap_mm: number;
  };
  algorithm_suggestion: {
    outer_mat_color_id: string | null;
    inner_mat_color_id: string | null;
  };
};

export type LabelerAnnotation = {
  id: string;
  image_id: string;
  artwork_type: ArtworkType;
  decor_style: DecorStyle;
  width_mm: number;
  height_mm: number;
  context: Record<string, unknown>;
  image_features: LabelerAnalysis["image_analysis"];
  constructive: LabelerAnalysis["constructive"];
  algorithm_suggestion: LabelerAnalysis["algorithm_suggestion"];
  label: {
    outer_mat_color_id: string | null;
    inner_mat_color_id: string | null;
  };
  confidence: "low" | "medium" | "high";
  note: string;
  updated_at: string;
};

export function labelerImageUrl(image: LabelerImage) {
  return `${API_BASE}${image.image_url}`;
}

export function exportDatasetUrl() {
  return `${API_BASE}/api/labeler/export.jsonl`;
}

export async function listImages() {
  const response = await fetch(`${API_BASE}/api/labeler/images`, { cache: "no-store" });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось загрузить изображения"));
  return (await response.json()) as { images: LabelerImage[] };
}

export async function uploadImages(files: FileList | File[]) {
  const payload = new FormData();
  Array.from(files).forEach((file) => payload.append("files", file));
  const response = await fetch(`${API_BASE}/api/labeler/images`, { method: "POST", body: payload });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось загрузить файлы"));
  return (await response.json()) as { images: LabelerImage[] };
}

export async function uploadImageUrl(url: string) {
  const payload = new FormData();
  payload.set("url", url);
  const response = await fetch(`${API_BASE}/api/labeler/images/from-url`, { method: "POST", body: payload });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось загрузить URL"));
  return (await response.json()) as { image: LabelerImage };
}

export async function deleteImage(imageId: string) {
  const response = await fetch(`${API_BASE}/api/labeler/images/${imageId}`, { method: "DELETE" });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось удалить изображение"));
}

export async function loadPalette() {
  const response = await fetch(`${API_BASE}/api/labeler/palette`, { cache: "no-store" });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось загрузить палитру"));
  return (await response.json()) as { colors: PaletteColor[] };
}

export async function analyzeImage(imageId: string, artworkType: ArtworkType, decorStyle: DecorStyle) {
  const response = await fetch(`${API_BASE}/api/labeler/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id: imageId, artwork_type: artworkType, decor_style: decorStyle }),
  });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось рассчитать изображение"));
  return (await response.json()) as LabelerAnalysis;
}

export async function listAnnotations() {
  const response = await fetch(`${API_BASE}/api/labeler/annotations`, { cache: "no-store" });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось загрузить датасет"));
  return (await response.json()) as { annotations: LabelerAnnotation[] };
}

export async function deleteAnnotation(annotationId: string) {
  const response = await fetch(`${API_BASE}/api/labeler/annotations/${annotationId}`, { method: "DELETE" });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось удалить разметку"));
}

export async function saveAnnotation(args: {
  imageId: string;
  artworkType: ArtworkType;
  decorStyle: DecorStyle;
  outerMatColorId: string | null;
  innerMatColorId: string | null;
  confidence: "low" | "medium" | "high";
  note: string;
}) {
  const response = await fetch(`${API_BASE}/api/labeler/annotations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_id: args.imageId,
      artwork_type: args.artworkType,
      decor_style: args.decorStyle,
      label: {
        outer_mat_color_id: args.outerMatColorId,
        inner_mat_color_id: args.innerMatColorId,
      },
      confidence: args.confidence,
      note: args.note,
    }),
  });
  if (!response.ok) throw new Error(await errorMessage(response, "Не удалось сохранить разметку"));
  return (await response.json()) as { annotation: LabelerAnnotation };
}

export function colorById(colors: PaletteColor[], id: string | null | undefined): PaletteColor | null {
  if (!id) return null;
  return colors.find((color) => color.id === id) ?? null;
}

export function matColorLabel(color: PaletteColor | MatColor | null | undefined) {
  return color ? `${color.name} ${color.hex}` : "не выбран";
}

async function errorMessage(response: Response, fallback: string) {
  const detail = await response.json().catch(() => null);
  return detail?.detail || detail?.error || fallback;
}
