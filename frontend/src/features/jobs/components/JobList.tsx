import { useState } from "react";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { useJobs, PAGE_SIZE } from "@/features/jobs/api/hooks";
import { JobCard } from "@/features/jobs/components/JobCard";
import { Button } from "@/shared/ui/button";

export function JobList() {
  const [page, setPage] = useState(0);
  const { data, isLoading, error } = useJobs(page);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-destructive py-12 text-center">
        Erro ao carregar jobs.
      </div>
    );
  }

  const jobs = data ?? [];

  if (jobs.length === 0 && page === 0) {
    return (
      <div className="text-sm text-muted-foreground py-12 text-center">
        Nenhum job ainda. Cole uma URL ou envie um arquivo para começar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {jobs.map((j) => (
          <JobCard key={j.id} job={j} />
        ))}
        {jobs.length === 0 && page > 0 && (
          <div className="text-sm text-muted-foreground py-4 text-center">Sem mais jobs.</div>
        )}
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <Button
          variant="ghost"
          size="sm"
          disabled={page === 0}
          onClick={() => setPage((p) => p - 1)}
        >
          <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
        </Button>
        <span>Página {page + 1}</span>
        <Button
          variant="ghost"
          size="sm"
          disabled={jobs.length < PAGE_SIZE}
          onClick={() => setPage((p) => p + 1)}
        >
          Próxima <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}
