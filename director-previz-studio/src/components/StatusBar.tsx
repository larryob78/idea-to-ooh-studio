import { useDirectorStore } from '../store/useDirectorStore';

export default function StatusBar() {
  const status = useDirectorStore((s) => s.status);
  const provider = useDirectorStore((s) => s.generationProvider);

  return (
    <footer className="h-9 border-t border-white/10 bg-panel/70 px-4 text-xs text-zinc-300 backdrop-blur-md">
      <div className="mx-auto flex h-full max-w-[1800px] items-center justify-between">
        <span>Status: {status}</span>
        <span className="uppercase tracking-wider text-zinc-400">Generator: {provider}</span>
      </div>
    </footer>
  );
}
