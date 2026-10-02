import { useParams } from "react-router-dom";
import { Download, X, FileText, Film, Music } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Progress } from "@/shared/ui/progress";
import { JobStatusBadge } from "@/features/jobs/components/JobStatusBadge";
import { RerunPanel } from "@/features/jobs/components/RerunDialog";
import { TranscriptionViewer } from "@/features/jobs/components/TranscriptionViewer";
import { ClipsPanel } from "@/features/clips/components/ClipsPanel";
import { useCancelJob, useJob } from "@/features/jobs/api/hooks";
import { useJobSocket } from "@/features/jobs/hooks/useJobSocket";
import { api } from "@/shared/lib/api";
import {
  formatBytes,
  formatDateTime,
  formatDuration,
  formatPercent,
} from "@/shared/lib/format";

const KIND_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  original_video: Film,
  original_audio: Music,
  processed_audio: Music,
  subtitle: FileText,
  transcript: FileText,
};

export function JobDetail() {
  const { jobId } = useParams();
  const { data, isLoading, error } = useJob(jobId);
  const cancel = useCancelJob();

  useJobSocket(jobId, !!jobId);

  if (isLoading) return <div className="p-6 text-muted-foreground">Carregando…</div>;
  if (error) return <div className="p-6 text-destructive">{(error as Error).message}</div>;
  if (!data) return null;

  const { job, media, transcription_available } = data;
  const isActive = job.status === "RUNNING" || job.status === "PENDING";

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold truncate">
            {job.title || "Sem título"}
          </h1>
          <p className="text-sm text-muted-foreground truncate">
            {job.source_url || job.source_file}
          </p>
        </div>
        <JobStatusBadge status={job.status} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Progresso</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{job.stage.replace(/_/g, " ").toLowerCase()}</span>
            <span>{formatPercent(job.progress)}</span>
          </div>
          <Progress value={job.progress * 100} />
          {job.message && (
            <div className="text-sm text-muted-foreground">{job.message}</div>
          )}
          {job.error_message && (
            <div className="text-sm text-destructive">{job.error_message}</div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-muted-foreground pt-4 border-t">
            <div>
              <div className="uppercase">Criado</div>
              <div className="text-foreground">{formatDateTime(job.created_at)}</div>
            </div>
            <div>
              <div className="uppercase">Decorrido</div>
              <div className="text-foreground">{formatDuration(job.elapsed_seconds)}</div>
            </div>
            <div>
              <div className="uppercase">Modelo</div>
              <div className="text-foreground">{job.params.model}</div>
            </div>
            <div>
              <div className="uppercase">Idioma</div>
              <div className="text-foreground">{job.params.language}</div>
            </div>
          </div>

          {isActive && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => jobId && cancel.mutate(jobId)}
              disabled={cancel.isPending}
              className="mt-4"
            >
              <X className="h-4 w-4" />
              Cancelar job
            </Button>
          )}
        </CardContent>
      </Card>

      {media.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Arquivos gerados</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {media.map((m) => {
              const Icon = KIND_ICON[m.kind] ?? FileText;
              const isOutput = m.kind === "subtitle" || m.kind === "transcript";
              return (
                <div
                  key={m.path}
                  className="flex items-center justify-between p-3 rounded-md border bg-background"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{m.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {m.format.toUpperCase()} · {formatBytes(m.size_bytes)}
                      </div>
                    </div>
                  </div>
                  {isOutput && jobId && (
                    <Button asChild size="sm" variant="outline">
                      <a href={api.downloadUrl(jobId, m.format)} download>
                        <Download className="h-4 w-4" />
                        Baixar
                      </a>
                    </Button>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {transcription_available && jobId && (
        <TranscriptionViewer jobId={jobId} enabled={transcription_available} />
      )}

      {jobId && job.status === "COMPLETED" && (
        <ClipsPanel jobId={jobId} transcriptionAvailable={transcription_available} />
      )}

      {jobId && (job.status === "COMPLETED" || job.status === "FAILED") && (
        <Card>
          <CardHeader>
            <CardTitle>Regerar</CardTitle>
          </CardHeader>
          <CardContent>
            <RerunPanel
              jobId={jobId}
              currentModel={job.params.model}
              currentLanguage={job.params.language}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
