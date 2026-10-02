import { useJobs } from "@/features/jobs/api/hooks";
import { JobCard } from "@/features/jobs/components/JobCard";
import { Loader2 } from "lucide-react";

export function JobList({ limit }: { limit?: number }) {
  const { data, isLoading, error } = useJobs();

  if (isLoading || error) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }
  const jobs = (data ?? []).slice(0, limit ?? undefined);
  if (jobs.length === 0) {
    return (
      <div className="text-sm text-muted-foreground py-12 text-center">
        Nenhum job ainda. Cole uma URL ou envie um arquivo para começar.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {jobs.map((j) => (
        <JobCard key={j.id} job={j} />
      ))}
    </div>
  );
}
