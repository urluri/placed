import type { DecorStyle, DecorationVariant, FormState, MatColorAnalyzer, MlModelInfo, Recommendation } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").trim();

export async function recommend(form: FormState, matColorAnalyzer: MatColorAnalyzer = form.matColorAnalyzer): Promise<Recommendation> {
  const payload = toPayload(form, matColorAnalyzer);
  const response = await fetch(`${API_BASE}/api/recommend`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Cache-Control": "no-cache",
    },
    body: payload,
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
  matColorAnalyzer: MatColorAnalyzer = form.matColorAnalyzer,
  imageToken?: string,
): Promise<Blob> {
  const payload = toPayload(form, matColorAnalyzer);
  payload.set("decorStyle", decorStyle);
  if (imageToken) {
    payload.set("imageToken", imageToken);
  }
  if (variant) {
    payload.set("spec", JSON.stringify(variant));
  }

  const response = await fetch(`${API_BASE}/api/render`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Cache-Control": "no-cache",
    },
    body: payload,
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Рендер не собрался"));
  }

  return response.blob();
}

export async function getMlModelInfo(): Promise<MlModelInfo> {
  const response = await fetch(`${API_BASE}/api/ml/status`, {
    method: "GET",
    cache: "no-store",
    headers: {
      "Cache-Control": "no-cache",
    },
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response, "Не удалось прочитать версию ML-модели"));
  }

  return response.json();
}

function toPayload(form: FormState, matColorAnalyzer: MatColorAnalyzer) {
  const payload = new FormData();
  payload.set("widthMm", String(dimensionOrDefault(form.widthMm, 300)));
  payload.set("heightMm", String(dimensionOrDefault(form.heightMm, 400)));
  payload.set("artworkType", form.artworkType);
  payload.set("interiorStyle", form.interiorStyle);
  payload.set("matColorAnalyzer", matColorAnalyzer);
  payload.set("rotateArtwork", String(form.rotationDegrees !== 0));
  payload.set("rotationDegrees", String(form.rotationDegrees));
  payload.set("matSizeConfig", JSON.stringify(form.matSizeConfig));
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
