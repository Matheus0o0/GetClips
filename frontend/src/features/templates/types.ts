export interface VideoConfig {
  aspect_ratio: string;
  resolution: string;
}

export interface TrackingConfig {
  enabled: boolean;
  target: "primary_person" | "center";
  smoothing: number;
  dead_zone_px: number;
}

export interface CaptionConfig {
  enabled: boolean;
  words_per_block: number;
  max_chars_per_block: number;
  style: "bold_dynamic" | "minimal" | "karaoke" | "podcast" | "clean";
  font_family: string;
  font_size: number;
  font_weight: number;
  position_y: number;
  position_x: number;
  text_align: "left" | "center" | "right";
  color: string;
  outline_color: string;
  outline_width: number;
  background_color: string;
  animation: "none" | "pop" | "fade" | "word_by_word" | "karaoke";
  highlight_emphasis: boolean;
  highlight_color: string;
}

export interface CameraConfig {
  dynamic_zoom: boolean;
  max_zoom: number;
  zoom_smoothing: number;
}

export interface CutsConfig {
  jump_cuts: boolean;
  remove_silence: boolean;
  silence_threshold_db: number;
  min_silence_duration_ms: number;
}

export interface AnalysisConfig {
  max_clips: number;
  duration_min: number;
  duration_max: number;
}

export interface EditingTemplateConfig {
  video: VideoConfig;
  tracking: TrackingConfig;
  captions: CaptionConfig;
  camera: CameraConfig;
  cuts: CutsConfig;
  analysis: AnalysisConfig;
}

export interface EditingTemplate {
  id: string;
  name: string;
  is_default: boolean;
  config: EditingTemplateConfig;
}

export const defaultConfig: EditingTemplateConfig = {
  video: { aspect_ratio: "9:16", resolution: "1080x1920" },
  tracking: { enabled: true, target: "primary_person", smoothing: 0.8, dead_zone_px: 30 },
  captions: {
    enabled: true,
    words_per_block: 3,
    max_chars_per_block: 25,
    style: "bold_dynamic",
    font_family: "Inter",
    font_size: 72,
    font_weight: 800,
    position_y: 0.75,
    position_x: 0.5,
    text_align: "center",
    color: "#FFFFFF",
    outline_color: "#000000",
    outline_width: 4,
    background_color: "transparent",
    animation: "pop",
    highlight_emphasis: true,
    highlight_color: "#FFE000",
  },
  camera: { dynamic_zoom: true, max_zoom: 1.12, zoom_smoothing: 0.9 },
  cuts: { jump_cuts: true, remove_silence: true, silence_threshold_db: -35, min_silence_duration_ms: 400 },
  analysis: { max_clips: 5, duration_min: 30, duration_max: 60 },
};
