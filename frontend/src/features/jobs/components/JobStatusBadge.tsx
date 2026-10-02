import { Badge } from "@/shared/ui/badge";
import type { JobStatus } from "@/shared/types/job";

const VARIANTS: Record<JobStatus, "default" | "secondary" | "destructive" | "success" | "warning"> =
  {
    PENDING: "secondary",
    RUNNING: "warning",
    COMPLETED: "success",
    FAILED: "destructive",
    CANCELLED: "secondary",
  };

const LABELS: Record<JobStatus, string> = {
  PENDING: "Aguardando",
  RUNNING: "Em execução",
  COMPLETED: "Concluído",
  FAILED: "Falhou",
  CANCELLED: "Cancelado",
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return <Badge variant={VARIANTS[status]}>{LABELS[status]}</Badge>;
}
