import { JobForm } from "@/features/jobs";
import { JobList } from "@/features/jobs";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

export function HomePage() {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Nova transcrição</h1>
        <p className="text-muted-foreground mt-1">
          Cole uma URL de vídeo ou envie um arquivo local. Todo o processamento
          ocorre na sua máquina.
        </p>
      </header>

      <Card>
        <CardContent className="p-6">
          <JobForm />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Jobs recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <JobList limit={10} />
        </CardContent>
      </Card>
    </div>
  );
}
