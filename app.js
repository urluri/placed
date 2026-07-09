const DEFAULT_IMAGE = "test_images/test.jpg";

const sizeProfiles = {
  small: { max: 210, frame: 15, mat: 60 },
  medium: { min: 211, max: 500, frame: 25, mat: 45 },
  large: { min: 501, frame: 45, mat: 20 },
};

const materials = {
  paper: {
    label: "Бумага",
    frameAdjust: 2,
    matAdjust: 0,
    matEnabled: true,
    glass: "Стекло обязательно",
    frameType: "дерево",
    reason: "Работы на бумаге лучше отделять от стекла паспарту и держать визуально спокойную рамку.",
  },
  canvas: {
    label: "Холст",
    frameAdjust: 12,
    matAdjust: 0,
    matEnabled: false,
    glass: "Без стекла",
    frameType: "глубокий профиль",
    reason: "Холсту нужен более глубокий профиль, а паспарту обычно не используется.",
  },
  embroidery: {
    label: "Вышивка",
    frameAdjust: 8,
    matAdjust: 0,
    matEnabled: false,
    glass: "Стекло желательно",
    frameType: "коробочный профиль",
    reason: "Объемной работе нужен запас по глубине и спокойная рама, не спорящая с фактурой.",
  },
};

const styles = {
  loft: {
    label: "Лофт / индастриал",
    title: "Темный металл + теплое паспарту",
    frameColor: "#22211f",
    frameLight: "#4a4741",
    frameDark: "#11100f",
    matColor: "#ded7cc",
    wallColor: "#d5d3ce",
    frameName: "черный металл",
    material: "алюминий",
    confidence: 78,
  },
  minimal: {
    label: "Современный / минимализм",
    title: "Светлый дуб + музейное паспарту",
    frameColor: "#b39b77",
    frameLight: "#d1bd9d",
    frameDark: "#7d684d",
    matColor: "#eee9df",
    wallColor: "#e3e1dc",
    frameName: "светлый дуб",
    material: "дерево",
    confidence: 84,
  },
  classic: {
    label: "Классика / неоклассика",
    title: "Ореховый багет + теплое паспарту",
    frameColor: "#775334",
    frameLight: "#a77a4f",
    frameDark: "#412a19",
    matColor: "#efe3cf",
    wallColor: "#ddd8ce",
    frameName: "темный орех",
    material: "дерево",
    confidence: 80,
  },
  universal: {
    label: "Универсальный вариант",
    title: "Графитовая рама + нейтральное паспарту",
    frameColor: "#4b4d4a",
    frameLight: "#70736f",
    frameDark: "#2d2f2c",
    matColor: "#ece8df",
    wallColor: "#e0ded8",
    frameName: "матовый графит",
    material: "дерево",
    confidence: 76,
  },
};

const form = document.querySelector("#configForm");
const upload = document.querySelector("#artUpload");
const canvas = document.querySelector("#previewCanvas");
const ctx = canvas.getContext("2d");
const image = new Image();

let uploadedObjectUrl = "";

const els = {
  uploadTitle: document.querySelector("#uploadTitle"),
  uploadMeta: document.querySelector("#uploadMeta"),
  sizeCategory: document.querySelector("#sizeCategory"),
  recommendationTitle: document.querySelector("#recommendationTitle"),
  confidence: document.querySelector("#confidence"),
  frameSpec: document.querySelector("#frameSpec"),
  matSpec: document.querySelector("#matSpec"),
  glassSpec: document.querySelector("#glassSpec"),
  finalSpec: document.querySelector("#finalSpec"),
  reasonText: document.querySelector("#reasonText"),
  previewLabel: document.querySelector("#previewLabel"),
  previewStyle: document.querySelector("#previewStyle"),
  downloadButton: document.querySelector("#downloadButton"),
  widthMm: document.querySelector("#widthMm"),
  heightMm: document.querySelector("#heightMm"),
};

function getRadioValue(name) {
  return document.querySelector(`input[name="${name}"]:checked`).value;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getSizeCategory(widthMm, heightMm) {
  const shortSide = Math.min(widthMm, heightMm);
  if (shortSide <= sizeProfiles.small.max) return "small";
  if (shortSide <= sizeProfiles.medium.max) return "medium";
  return "large";
}

function computeRecommendation() {
  const widthMm = clamp(Number(els.widthMm.value) || 300, 50, 3000);
  const heightMm = clamp(Number(els.heightMm.value) || 400, 50, 3000);
  const materialKey = getRadioValue("material");
  const styleKey = getRadioValue("style");
  const sizeCategory = getSizeCategory(widthMm, heightMm);
  const profile = sizeProfiles[sizeCategory];
  const material = materials[materialKey];
  const style = styles[styleKey];

  const frameMm = Math.max(10, Math.round(profile.frame + material.frameAdjust));
  const matMm = material.matEnabled ? Math.max(0, Math.round(profile.mat + material.matAdjust)) : 0;
  const finalWidth = widthMm + 2 * (frameMm + matMm);
  const finalHeight = heightMm + 2 * (frameMm + matMm);
  const frameMaterial = materialKey === "paper" && styleKey === "loft" ? style.material : material.frameType;

  return {
    widthMm,
    heightMm,
    materialKey,
    styleKey,
    sizeCategory,
    material,
    style,
    frameMm,
    matMm,
    finalWidth,
    finalHeight,
    frameMaterial,
  };
}

function updateText(rec) {
  els.sizeCategory.value = rec.sizeCategory;
  els.recommendationTitle.textContent = rec.style.title;
  els.confidence.textContent = `${rec.style.confidence}%`;
  els.frameSpec.textContent = `${rec.frameMm} мм, ${rec.frameMaterial}, ${rec.style.frameName}`;
  els.matSpec.textContent = rec.matMm > 0 ? `${rec.matMm} мм, ${colorName(rec.styleKey)}` : "Без паспарту";
  els.glassSpec.textContent = rec.material.glass;
  els.finalSpec.textContent = `${rec.finalWidth} x ${rec.finalHeight} мм`;
  els.previewLabel.textContent = `${rec.widthMm} x ${rec.heightMm} мм`;
  els.previewStyle.textContent = rec.style.label;
  els.reasonText.textContent = `${rec.material.reason} Для выбранного интерьера подходит ${rec.style.frameName}: он удерживает работу в нужном характере и не перегружает изображение.`;
}

function colorName(styleKey) {
  if (styleKey === "loft") return "теплый серый";
  if (styleKey === "classic") return "слоновая кость";
  if (styleKey === "universal") return "нейтральный белый";
  return "теплый белый";
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(600, Math.round(rect.width * ratio));
  const height = Math.max(520, Math.round(rect.height * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
}

function drawWall(rec) {
  const { width, height } = canvas;
  ctx.fillStyle = rec.style.wallColor;
  ctx.fillRect(0, 0, width, height);

  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "rgba(255,255,255,0.28)");
  gradient.addColorStop(0.55, "rgba(255,255,255,0.02)");
  gradient.addColorStop(1, "rgba(0,0,0,0.08)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  ctx.globalAlpha = 0.055;
  for (let x = 0; x < width; x += 18) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x + height * 0.4, height);
    ctx.strokeStyle = "#4a4540";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

function drawRecommendation(rec) {
  resizeCanvas();
  updateText(rec);
  drawWall(rec);

  const scale = Math.min(
    canvas.width * 0.62 / rec.finalWidth,
    canvas.height * 0.72 / rec.finalHeight
  );
  const artW = rec.widthMm * scale;
  const artH = rec.heightMm * scale;
  const frame = rec.frameMm * scale;
  const mat = rec.matMm * scale;
  const pictureW = artW + 2 * (frame + mat);
  const pictureH = artH + 2 * (frame + mat);
  const left = (canvas.width - pictureW) / 2;
  const top = (canvas.height - pictureH) / 2 + canvas.height * 0.02;

  drawShadow(left, top, pictureW, pictureH, scale);
  drawFrame(rec, left, top, pictureW, pictureH, frame);
  drawMat(rec, left + frame, top + frame, pictureW - 2 * frame, pictureH - 2 * frame, mat);
  drawArtwork(left + frame + mat, top + frame + mat, artW, artH);
}

function drawShadow(x, y, w, h, scale) {
  ctx.save();
  ctx.shadowColor = "rgba(0, 0, 0, 0.28)";
  ctx.shadowBlur = 22 * scale;
  ctx.shadowOffsetX = 14 * scale;
  ctx.shadowOffsetY = 18 * scale;
  ctx.fillStyle = "rgba(0,0,0,0.18)";
  ctx.fillRect(x, y, w, h);
  ctx.restore();
}

function drawFrame(rec, x, y, w, h, frame) {
  ctx.fillStyle = rec.style.frameColor;
  ctx.fillRect(x, y, w, h);

  const bevel = Math.max(3, Math.min(9, frame * 0.2));
  for (let i = 0; i < bevel; i += 1) {
    ctx.strokeStyle = rec.style.frameLight;
    ctx.beginPath();
    ctx.moveTo(x + i, y + i);
    ctx.lineTo(x + w - i, y + i);
    ctx.moveTo(x + i, y + i);
    ctx.lineTo(x + i, y + h - i);
    ctx.stroke();

    ctx.strokeStyle = rec.style.frameDark;
    ctx.beginPath();
    ctx.moveTo(x + i, y + h - i);
    ctx.lineTo(x + w - i, y + h - i);
    ctx.moveTo(x + w - i, y + i);
    ctx.lineTo(x + w - i, y + h - i);
    ctx.stroke();
  }
}

function drawMat(rec, x, y, w, h, mat) {
  if (mat <= 0) {
    return;
  }

  ctx.fillStyle = rec.style.matColor;
  ctx.fillRect(x, y, w, h);

  const inset = Math.max(3, Math.min(8, mat * 0.12));
  ctx.strokeStyle = "rgba(255,255,255,0.72)";
  ctx.lineWidth = inset;
  ctx.strokeRect(x + inset / 2, y + inset / 2, w - inset, h - inset);

  ctx.strokeStyle = "rgba(70,62,50,0.16)";
  ctx.lineWidth = Math.max(2, inset * 0.7);
  ctx.strokeRect(x + mat, y + mat, w - 2 * mat, h - 2 * mat);
}

function drawArtwork(x, y, w, h) {
  ctx.save();
  ctx.shadowColor = "rgba(0,0,0,0.16)";
  ctx.shadowBlur = 8;
  ctx.shadowOffsetX = 3;
  ctx.shadowOffsetY = 4;
  ctx.fillStyle = "#ddd";
  ctx.fillRect(x, y, w, h);
  ctx.restore();

  if (image.complete && image.naturalWidth) {
    drawImageCover(image, x, y, w, h);
  } else {
    ctx.fillStyle = "#b9b2a7";
    ctx.fillRect(x, y, w, h);
  }
}

function drawImageCover(img, x, y, w, h) {
  const imageRatio = img.naturalWidth / img.naturalHeight;
  const boxRatio = w / h;
  let sx = 0;
  let sy = 0;
  let sw = img.naturalWidth;
  let sh = img.naturalHeight;

  if (imageRatio > boxRatio) {
    sw = img.naturalHeight * boxRatio;
    sx = (img.naturalWidth - sw) / 2;
  } else {
    sh = img.naturalWidth / boxRatio;
    sy = (img.naturalHeight - sh) / 2;
  }

  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
}

function refresh() {
  drawRecommendation(computeRecommendation());
}

upload.addEventListener("change", () => {
  const file = upload.files?.[0];
  if (!file) return;

  if (uploadedObjectUrl) URL.revokeObjectURL(uploadedObjectUrl);
  uploadedObjectUrl = URL.createObjectURL(file);
  els.uploadTitle.textContent = file.name;
  els.uploadMeta.textContent = `${Math.round(file.size / 1024)} КБ`;
  image.src = uploadedObjectUrl;
});

form.addEventListener("input", refresh);
window.addEventListener("resize", refresh);
image.addEventListener("load", refresh);

els.downloadButton.addEventListener("click", () => {
  const link = document.createElement("a");
  link.download = "placed-preview.png";
  link.href = canvas.toDataURL("image/png");
  link.click();
});

image.src = DEFAULT_IMAGE;
refresh();
