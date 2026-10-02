import { Link } from "react-router-dom";
import { Card, CardContent } from "@/shared/ui/card";
import { Progress } from "@/shared/ui/progress";
import { JobStatusBadge } from "@/features/jobs/components/JobStatusBadge";
import { formatDateTime, formatDuration, formatPercent } from "@/shared/lib/format";
import type { JobDTO } from "@/shared/types/job";

export function JobCard({ job }: { job: JobDTO }) {
  const isActive = job.status === "RUNNING" || job.status === "PENDING";
  return (
    <Link to={`/jobs/${job.id}`} className="block">
      <Card className="hover:border-primary/50 transition-colors">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="font-medium truncate">
                {job.title || job.source_url || job.source_file || job.id}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {formatDateTime(job.created_at)}
                {job.elapsed_seconds ? ` · ${formatDuration(job.elapsed_seconds)}` : ""}
              </div>
            </div>
            <JobStatusBadge status={job.status} />
          </div>

          {isActive && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{job.stage.replace(/_/g, " ").toLowerCase()}</span>
                <span>{formatPercent(job.progress)}</span>
              </div>
              <Progress value={job.progress * 100} />
              {job.message && (
                <div className="text-xs text-muted-foreground truncate">{job.message}</div>
              )}
            </div>
          )}

          {job.status === "FAILED" && job.error_message && (
            <div className="text-xs text-destructive truncate">{job.error_message}</div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
