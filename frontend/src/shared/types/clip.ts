export type ClipStatus = "pending" | "rendering" | "ready" | "error";
export type CropMode = "dynamic" | "static_fallback";

export interface ClipDTO {
  id: string;
  job_id: string;
  inicio: number;
  fim: number;
  duration: number;
  hook_text: string;
  score: number;
  motivo: string;
  crop_mode: CropMode;
  status: ClipStatus;
  output_path: string | null;
  error_message: string | null;
  progress: number;
  created_at: string;
}

export interface HighlightRequest {
  max_clips?: number;
  duration_min?: number;
  duration_max?: number;
}
