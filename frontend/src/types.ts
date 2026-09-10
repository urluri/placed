export type ArtworkType = "poster" | "photo" | "watercolor" | "engraving" | "botanical" | "canvas" | "volumetric";
export type InteriorStyle =
  | "minimal"
  | "scandi"
  | "japandi"
  | "contemporary"
  | "loft"
  | "modern_vintage"
  | "neoclassic"
  | "universal";
export type DecorStyle = "standard" | "signature";
export type MatColorAnalyzer = "rules" | "ml";
export type SizeSource = "manual" | "from_file";
export type SizeProfile = "small" | "medium" | "large" | "extra_large";

export type ImageInfo = {
  pixelWidth: number;
  pixelHeight: number;
};

export type MatSizeConfig = {
  percentages: Record<SizeProfile, Record<DecorStyle, string>>;
  max_mm: Record<SizeProfile, Record<DecorStyle, string>>;
};

export type ColorSample = {
  hex: string;
  rgb: number[];
  lab: number[];
  family: string;
  temperature: string;
  lightness: string;
  chroma_level: string;
  chroma: number;
  share: number;
};

export type AccentAnalysis = {
  selected: ColorSample | null;
  source: "pop" | "temperature" | "light" | "area" | null;
  confidence: "high" | "medium" | "low";
  reason: string;
  candidates: {
    pop: ColorSample | null;
    temperature: ColorSample | null;
    light: ColorSample | null;
    area: ColorSample | null;
  };
  scores?: {
    pop?: number;
    temperature?: number;
    light?: number;
    area?: number;
  };
};

export type MatColor = {
  id: string;
  name: string;
  hex: string;
};

export type MlColorCandidate = {
  color_id: string;
  color?: MatColor | null;
  vote_share?: number;
};

export type MlTargetPrediction = {
  color_id: string | null;
  color?: MatColor | null;
  confidence?: "low" | "medium" | "high";
  weight?: number;
  vote_share?: number;
  evidence?: number[];
  top?: MlColorCandidate[];
};

export type MlPrediction = {
  available: boolean;
  model_version?: number;
  trained_at?: string;
  sample_count?: number;
  predictions?: Partial<Record<"outer_mat_color_id" | "inner_mat_color_id", MlTargetPrediction>>;
  neighbors?: unknown[];
};

export type MlModelInfo = {
  available: boolean;
  reason?: string;
  type?: string;
  model_version?: number | null;
  trained_at?: string | null;
  sample_count?: number;
  target_counts?: Partial<Record<"outer_mat_color_id" | "inner_mat_color_id", Record<string, number>>>;
  palette_size?: number;
};

export type MatSpec = {
  enabled: boolean;
  outer_color: MatColor | null;
  inner_color: MatColor | null;
  left_mm: number;
  right_mm: number;
  top_mm: number;
  bottom_mm: number;
  overlap_mm: number;
  inner_reveal_mm: number;
  inner_reveal_left_mm: number;
  inner_reveal_right_mm: number;
  inner_reveal_top_mm: number;
  inner_reveal_bottom_mm: number;
  color_analyzer?: MatColorAnalyzer;
  color_source?: string;
  ml_prediction?: MlPrediction | null;
};

export type FrameSpec = {
  id: string;
  name: string;
  material: string;
  color_family: string;
  tone: string;
  width_mm: number;
  depth_mm: number | null;
  profile: string;
  hex: string;
};

export type GlassSpec = {
  type: string;
  required: boolean;
};

export type GeometrySpec = {
  size_profile: string;
  aspect: string;
  window_width_mm: number;
  window_height_mm: number;
  mat_outer_width_mm: number;
  mat_outer_height_mm: number;
  outer_width_mm: number;
  outer_height_mm: number;
};

export type DecisionNode = {
  title: string;
  result: string;
  facts: string[];
};

export type DecorationVariant = {
  decor_style: DecorStyle;
  title: string;
  artwork_type: ArtworkType;
  frame: FrameSpec;
  mat: MatSpec | null;
  glass: GlassSpec | null;
  shadow_box: boolean;
  geometry: GeometrySpec;
  reasons: string[];
  warnings: string[];
  decision_tree: DecisionNode[];
};

export type Recommendation = {
  image_token?: string;
  image_analysis: {
    palette: {
      primary: ColorSample | null;
      secondary: ColorSample | null;
      accent: AccentAnalysis | null;
    };
    temperature: string;
    lightness: string;
    chroma_level: string;
    monochrome: string;
    frame_occupancy: string;
    contrast: string;
    metrics?: {
      lightness?: number;
      chroma?: number;
      monochrome_score?: number;
      contrast?: number;
      frame_occupancy?: number;
      temperature_score?: number;
    };
  };
  variants: DecorationVariant[];
  mat_color_analyzer?: MatColorAnalyzer;
};

export type FormState = {
  widthMm: string;
  heightMm: string;
  sizeSource: SizeSource;
  standardSizePresetId: string;
  printPpi: number;
  lockAspect: boolean;
  imageInfo: ImageInfo | null;
  artworkType: ArtworkType;
  interiorStyle: InteriorStyle;
  matColorAnalyzer: MatColorAnalyzer;
  image: File | null;
  rotationDegrees: -90 | 0 | 90;
  matSizeConfig: MatSizeConfig;
};
