export type JobStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type JobStage =
  | "QUEUED"
  | "DOWNLOADING"
  | "EXTRACTING_AUDIO"
  | "TRANSCRIBING"
  | "GENERATING_SUBTITLES"
  | "FINALIZING"
  | "DONE";

export interface JobParams {
  model: string;
  language: string;
  beam_size: number;
  output_formats: string[];
  audio_only: boolean;
  keep_source_video: boolean;
}

export interface JobDTO {
  id: string;
  source_url: string | null;
  source_file: string | null;
  title: string | null;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  message: string;
  error_message: string | null;
  params: JobParams;
  metadata: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  elapsed_seconds: number | null;
}

export interface MediaFileDTO {
  path: string;
  name: string;
  kind: string;
  format: string;
  size_bytes: number;
  duration_seconds: number | null;
}

export interface JobDetailDTO {
  job: JobDTO;
  media: MediaFileDTO[];
  transcription_available: boolean;
}

export interface SettingsDTO {
  default_model: string;
  default_language: string;
  device: string;
  max_concurrent_jobs: number;
  storage_root: string;
  beam_size: number;
  highlight_provider: string;
  highlight_configured: boolean;
  highlight_max_clips: number;
  highlight_clip_duration_min: number;
  highlight_clip_duration_max: number;
  reframe_output_resolution: string;
}

export interface ModelInfo {
  name: string;
  downloaded: boolean;
  size_bytes: number | null;
}

export interface CreateJobPayload {
  url?: string;
  file_path?: string;
  params?: {
    model?: string;
    language?: string;
    beam_size?: number;
    output_formats?: string[];
    audio_only?: boolean;
    keep_source_video?: boolean;
  };
}

export interface SegmentDTO {
  index: number;
  start_ms: number;
  end_ms: number;
  text: string;
  confidence: number;
}

export interface TranscriptionDTO {
  full_text: string;
  language_detected: string;
  language_probability: number;
  model_used: string;
  duration_seconds: number;
  segments: SegmentDTO[];
}

export interface RerunPayload {
  model?: string;
  language?: string;
  beam_size?: number;
  output_formats?: string[];
  audio_only?: boolean;
}
