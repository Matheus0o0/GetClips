import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/shared/lib/api";
import type { HighlightRequest } from "@/shared/types/clip";

export function useClips(jobId: string | undefined) {
  return useQuery({
    queryKey: ["clips", jobId],
    queryFn: () => api.listClips(jobId!),
    enabled: !!jobId,
    // Polling curto enquanto algum clip estiver renderizando
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.some((c) => c.status === "rendering") ? 1500 : false;
    },
  });
}

export function useCreateHighlights(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: HighlightRequest) => api.createHighlights(jobId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clips", jobId] }),
  });
}

export function useRenderClip(jobId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (clipId: string) => api.renderClip(clipId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clips", jobId] }),
  });
}
