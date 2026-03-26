import { useState } from 'react';
import { WandSparkles } from 'lucide-react';
import { useNvidia } from '../../hooks/useNvidia';
import { useDirectorStore } from '../../store/useDirectorStore';

export default function NvidiaPanel() {
  const [localPrompt, setLocalPrompt] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const setRefinedPrompt = useDirectorStore((s) => s.setRefinedPrompt);
  const setStatus = useDirectorStore((s) => s.setStatus);
  const { refinePrompt } = useNvidia();

  const onEnhance = async () => {
    setLoading(true);
    try {
      const refined = await refinePrompt(localPrompt || 'cinematic scene with dramatic contrast', 'character');
      setOutput(refined);
      setRefinedPrompt(refined);
      setStatus('Prompt enhanced with NVIDIA NIM.');
    } catch (error) {
      setStatus(`Prompt enhancement failed: ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <label className="label">AI Prompt Enhancement</label>
      <textarea
        className="input h-24"
        placeholder="Add style directives, camera intention, pacing, texture..."
        value={localPrompt}
        onChange={(e) => setLocalPrompt(e.target.value)}
      />
      <button className="btn-primary w-full" onClick={onEnhance} disabled={loading}>
        <WandSparkles size={16} /> {loading ? 'Enhancing...' : 'Enhance Prompt'}
      </button>
      <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm text-zinc-300 min-h-24">
        {output || 'Enhanced output will appear here.'}
      </div>
    </div>
  );
}
