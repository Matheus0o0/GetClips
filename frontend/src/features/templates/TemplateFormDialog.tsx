import { useEffect, useState } from "react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import type { EditingTemplate, EditingTemplateConfig } from "./types";
import { defaultConfig } from "./types";

interface Props {
  open: boolean;
  initial?: EditingTemplate | null;
  onClose: () => void;
  onSubmit: (name: string, config: EditingTemplateConfig) => void;
  isPending?: boolean;
}

export function TemplateFormDialog({ open, initial, onClose, onSubmit, isPending }: Props) {
  const [name, setName] = useState("");
  const [cfg, setCfg] = useState<EditingTemplateConfig>(defaultConfig);

  useEffect(() => {
    if (initial) {
      setName(initial.name);
      setCfg(initial.config);
    } else {
      setName("");
      setCfg(defaultConfig);
    }
  }, [initial, open]);

  if (!open) return null;

  function setCaption<K extends keyof EditingTemplateConfig["captions"]>(
    key: K,
    value: EditingTemplateConfig["captions"][K],
  ) {
    setCfg((c) => ({ ...c, captions: { ...c.captions, [key]: value } }));
  }

  function setTracking<K extends keyof EditingTemplateConfig["tracking"]>(
    key: K,
    value: EditingTemplateConfig["tracking"][K],
  ) {
    setCfg((c) => ({ ...c, tracking: { ...c.tracking, [key]: value } }));
  }

  function setCuts<K extends keyof EditingTemplateConfig["cuts"]>(
    key: K,
    value: EditingTemplateConfig["cuts"][K],
  ) {
    setCfg((c) => ({ ...c, cuts: { ...c.cuts, [key]: value } }));
  }

  function setCamera<K extends keyof EditingTemplateConfig["camera"]>(
    key: K,
    value: EditingTemplateConfig["camera"][K],
  ) {
    setCfg((c) => ({ ...c, camera: { ...c.camera, [key]: value } }));
  }

  function setAnalysis<K extends keyof EditingTemplateConfig["analysis"]>(
    key: K,
    value: EditingTemplateConfig["analysis"][K],
  ) {
    setCfg((c) => ({ ...c, analysis: { ...c.analysis, [key]: value } }));
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl border bg-background shadow-xl">
        <div className="border-b px-6 py-4">
          <h2 className="text-lg font-semibold">
            {initial ? "Editar template" : "Novo template"}
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
          {/* Nome */}
          <div className="space-y-1.5">
            <Label htmlFor="tpl-name">Nome do template</Label>
            <Input
              id="tpl-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Meu Reels"
            />
          </div>

          {/* Legendas */}
          <section className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Legendas</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Palavras por bloco</Label>
                <Input
                  type="number"
                  min={1}
                  max={8}
                  value={cfg.captions.words_per_block}
                  onChange={(e) => setCaption("words_per_block", Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Máx. caracteres por bloco</Label>
                <Input
                  type="number"
                  min={5}
                  max={80}
                  value={cfg.captions.max_chars_per_block}
                  onChange={(e) => setCaption("max_chars_per_block", Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Estilo</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={cfg.captions.style}
                  onChange={(e) => setCaption("style", e.target.value as EditingTemplateConfig["captions"]["style"])}
                >
                  <option value="bold_dynamic">Bold Dynamic</option>
                  <option value="minimal">Minimal</option>
                  <option value="karaoke">Karaoke</option>
                  <option value="podcast">Podcast</option>
                  <option value="clean">Clean</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Animação</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={cfg.captions.animation}
                  onChange={(e) => setCaption("animation", e.target.value as EditingTemplateConfig["captions"]["animation"])}
                >
                  <option value="pop">Pop</option>
                  <option value="fade">Fade</option>
                  <option value="word_by_word">Palavra a palavra</option>
                  <option value="karaoke">Karaoke</option>
                  <option value="none">Nenhuma</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Tamanho da fonte</Label>
                <Input
                  type="number"
                  min={20}
                  max={200}
                  value={cfg.captions.font_size}
                  onChange={(e) => setCaption("font_size", Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Posição vertical (0=topo · 1=rodapé)</Label>
                <Input
                  type="number"
                  step={0.05}
                  min={0}
                  max={1}
                  value={cfg.captions.position_y}
                  onChange={(e) => setCaption("position_y", Number(e.target.value))}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="hl-emphasis"
                  checked={cfg.captions.highlight_emphasis}
                  onChange={(e) => setCaption("highlight_emphasis", e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="hl-emphasis">Destacar palavras importantes</Label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="cap-enabled"
                  checked={cfg.captions.enabled}
                  onChange={(e) => setCaption("enabled", e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="cap-enabled">Habilitar legendas</Label>
              </div>
            </div>
          </section>

          {/* Tracking */}
          <section className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Tracking</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="tracking-enabled"
                  checked={cfg.tracking.enabled}
                  onChange={(e) => setTracking("enabled", e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="tracking-enabled">Tracking ativo</Label>
              </div>
              <div className="space-y-1.5">
                <Label>Suavização (0–1)</Label>
                <Input
                  type="number"
                  step={0.05}
                  min={0}
                  max={1}
                  value={cfg.tracking.smoothing}
                  onChange={(e) => setTracking("smoothing", Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Dead zone (px)</Label>
                <Input
                  type="number"
                  min={0}
                  value={cfg.tracking.dead_zone_px}
                  onChange={(e) => setTracking("dead_zone_px", Number(e.target.value))}
                />
              </div>
            </div>
          </section>

          {/* Zoom */}
          <section className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Câmera</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="zoom-enabled"
                  checked={cfg.camera.dynamic_zoom}
                  onChange={(e) => setCamera("dynamic_zoom", e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="zoom-enabled">Zoom dinâmico</Label>
              </div>
              <div className="space-y-1.5">
                <Label>Zoom máximo (ex: 1.12)</Label>
                <Input
                  type="number"
                  step={0.01}
                  min={1}
                  max={2}
                  value={cfg.camera.max_zoom}
                  onChange={(e) => setCamera("max_zoom", Number(e.target.value))}
                />
              </div>
            </div>
          </section>

          {/* Cortes */}
          <section className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Cortes</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="jump-cuts"
                  checked={cfg.cuts.jump_cuts}
                  onChange={(e) => setCuts("jump_cuts", e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="jump-cuts">Jump cuts</Label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="remove-silence"
                  checked={cfg.cuts.remove_silence}
                  onChange={(e) => setCuts("remove_silence", e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="remove-silence">Remover silêncio</Label>
              </div>
            </div>
          </section>

          {/* Análise */}
          <section className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Análise IA</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label>Máx. cortes</Label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={cfg.analysis.max_clips}
                  onChange={(e) => setAnalysis("max_clips", Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Duração mín. (s)</Label>
                <Input
                  type="number"
                  min={5}
                  value={cfg.analysis.duration_min}
                  onChange={(e) => setAnalysis("duration_min", Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Duração máx. (s)</Label>
                <Input
                  type="number"
                  min={10}
                  value={cfg.analysis.duration_max}
                  onChange={(e) => setAnalysis("duration_max", Number(e.target.value))}
                />
              </div>
            </div>
          </section>
        </div>

        <div className="flex justify-end gap-2 border-t px-6 py-4">
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            disabled={!name.trim() || isPending}
            onClick={() => onSubmit(name.trim(), cfg)}
          >
            {isPending ? "Salvando…" : initial ? "Salvar alterações" : "Criar template"}
          </Button>
        </div>
      </div>
    </div>
  );
}
