import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/shared/lib/api";
import type { CreateJobPayload, RerunPayload } from "@/shared/types/job";

export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(200, 0),
    refetchInterval: (query) => (query.state.error ? false : 3000),
  });
}

export function useJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId,
  });
}

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateJobPayload) => api.createJob(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => api.cancelJob(jobId),
    onSuccess: (_, jobId) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["job", jobId] });
    },
  });
}

export function useUploadFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      file: File;
      model: string;
      language: string;
      beamSize: number;
    }) =>
      api.uploadFile(input.file, {
        model: input.model,
        language: input.language,
        beamSize: input.beamSize,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useTranscription(jobId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ["transcription", jobId],
    queryFn: () => api.getTranscription(jobId!),
    enabled: !!jobId && enabled,
  });
}

export function useRerunJob() {
  const qc = useQueryClient();
  const nav = useNavigate();
  return useMutation({
    mutationFn: (input: { jobId: string; payload: RerunPayload }) =>
      api.rerunJob(input.jobId, input.payload),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      nav(`/jobs/${job.id}`);
    },
  });
}
