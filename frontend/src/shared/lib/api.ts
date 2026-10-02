import type {
  JobDTO,
  JobDetailDTO,
  ModelInfo,
  SettingsDTO,
  CreateJobPayload,
  TranscriptionDTO,
  RerunPayload,
} from "@/shared/types/job";
import type { ClipDTO, HighlightRequest } from "@/shared/types/clip";

const API_BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.detail || err.error || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createJob: (payload: CreateJobPayload) =>
    request<JobDTO>("/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listJobs: (limit = 100, offset = 0) =>
    request<JobDTO[]>(`/jobs?limit=${limit}&offset=${offset}`),

  getJob: (jobId: string) => request<JobDetailDTO>(`/jobs/${jobId}`),

  cancelJob: (jobId: string) =>
    request<{ message: string }>(`/jobs/${jobId}`, { method: "DELETE" }),

  history: (limit = 200) => request<JobDTO[]>(`/history?limit=${limit}`),

  settings: () => request<SettingsDTO>("/settings"),

  models: () => request<ModelInfo[]>("/models"),

  uploadFile: async (
    file: File,
    opts: { model: string; language: string; beamSize: number },
  ): Promise<JobDTO> => {
    const form = new FormData();
    form.append("file", file);
    form.append("model", opts.model);
    form.append("language", opts.language);
    form.append("beam_size", String(opts.beamSize));
    const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.detail || err.error || `HTTP ${res.status}`);
    }
    return res.json();
  },

  downloadUrl: (jobId: string, fmt: string) =>
    `${API_BASE}/download/${jobId}/${fmt}`,

  getTranscription: (jobId: string) =>
    request<TranscriptionDTO>(`/jobs/${jobId}/transcription`),

  rerunJob: (jobId: string, payload: RerunPayload) =>
    request<JobDTO>(`/jobs/${jobId}/rerun`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  createHighlights: (jobId: string, body: HighlightRequest = {}) =>
    request<ClipDTO[]>(`/jobs/${jobId}/highlights`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listClips: (jobId: string) => request<ClipDTO[]>(`/jobs/${jobId}/clips`),

  getClip: (clipId: string) => request<ClipDTO>(`/clips/${clipId}`),

  renderClip: (clipId: string) =>
    request<{ message: string }>(`/clips/${clipId}/render`, { method: "POST" }),

  clipDownloadUrl: (clipId: string) => `${API_BASE}/clips/${clipId}/download`,
};
