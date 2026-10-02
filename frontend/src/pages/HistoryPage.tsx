import { JobList } from "@/features/jobs";

export function HistoryPage() {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Histórico</h1>
        <p className="text-muted-foreground mt-1">
          Todos os jobs, ordenados pelo mais recente.
        </p>
      </header>
      <JobList />
    </div>
  );
}
