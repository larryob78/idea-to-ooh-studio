import { Aperture, Film, Sparkles } from 'lucide-react';

interface TopBarProps {
  onOpenExport: () => void;
}

export default function TopBar({ onOpenExport }: TopBarProps) {
  return (
    <header className="h-14 border-b border-white/10 bg-panel/70 px-4 backdrop-blur-md">
      <div className="mx-auto flex h-full max-w-[1800px] items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-accent/20 p-2 text-accent">
            <Film size={18} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-400">Director Suite</p>
            <h1 className="text-sm font-semibold text-white">Pre-Visualisation Studio</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost">
            <Aperture size={16} /> Live Compose
          </button>
          <button className="btn-primary" onClick={onOpenExport}>
            <Sparkles size={16} /> Export
          </button>
        </div>
      </div>
    </header>
  );
}
