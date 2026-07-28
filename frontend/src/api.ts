import type { DecorStyle, DecorationVariant, FormState, Recommendation } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function recommend(form: FormState): Promise<Recommendation> {
  const response = await fetch(`${API_BASE}/api/recommend`, {
    method: "POST",
    body: toPayload(form),
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Не удалось построить рекомендации"));
  }

  return response.json();
}

export async function renderPreview(
  form: FormState,
  decorStyle: DecorStyle,
  variant: DecorationVariant | null,
): Promise<Blob> {
  const payload = toPayload(form);
  payload.set("decorStyle", decorStyle);
  if (variant) {
    payload.set("spec", JSON.stringify(variant));
  }

  const response = await fetch(`${API_BASE}/api/render`, {
    method: "POST",
    body: payload,
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Рендер не собрался"));
  }

  return response.blob();
}

function toPayload(form: FormState) {
  const payload = new FormData();
  payload.set("widthMm", String(dimensionOrDefault(form.widthMm, 300)));
  payload.set("heightMm", String(dimensionOrDefault(form.heightMm, 400)));
  payload.set("artworkType", form.artworkType);
  payload.set("interiorStyle", form.interiorStyle);
  payload.set("rotateArtwork", String(form.rotateArtwork));
  if (form.image) {
    payload.set("image", form.image);
  }
  return payload;
}

function dimensionOrDefault(value: string, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

async function errorMessage(response: Response, fallback: string) {
  const detail = await response.json().catch(() => null);
  return detail?.detail || detail?.error || fallback;
}
