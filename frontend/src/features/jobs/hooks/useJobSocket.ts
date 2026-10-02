import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { openJobSocket, type JobEvent } from "@/shared/lib/ws";

export function useJobSocket(jobId: string | undefined, enabled = true) {
  const qc = useQueryClient();

  useEffect(() => {
    if (!jobId || !enabled) return;

    const close = openJobSocket(jobId, (evt: JobEvent) => {
      // Hidrata o cache do Query com o payload do WS — evita esperar polling
      qc.setQueryData<any>(["job", jobId], (prev: any) => {
        if (!prev) return prev;
        const nextJob = { ...prev.job };
        if (typeof evt.progress === "number") nextJob.progress = evt.progress;
        if (evt.stage) nextJob.stage = evt.stage;
        if (evt.message) nextJob.message = evt.message;
        if (evt.type === "JobCompletedEvent") nextJob.status = "COMPLETED";
        if (evt.type === "JobFailedEvent") {
          nextJob.status = "FAILED";
          nextJob.error_message = evt.error ?? null;
        }
        if (evt.type === "JobCancelledEvent") nextJob.status = "CANCELLED";
        return { ...prev, job: nextJob };
      });

      // Invalida a lista global também
      qc.invalidateQueries({ queryKey: ["jobs"] });

      // Ao terminar, recarrega detalhes para pegar media_files
      if (
        evt.type === "JobCompletedEvent" ||
        evt.type === "JobFailedEvent" ||
        evt.type === "JobCancelledEvent"
      ) {
        qc.invalidateQueries({ queryKey: ["job", jobId] });
      }
    });

    return close;
  }, [jobId, enabled, qc]);
}
