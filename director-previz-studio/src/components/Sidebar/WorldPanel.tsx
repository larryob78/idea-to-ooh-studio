import { Globe2, Loader2 } from 'lucide-react';
import { useDirectorStore } from '../../store/useDirectorStore';
import { useNvidia } from '../../hooks/useNvidia';
import { useWorldLabs } from '../../hooks/useWorldLabs';

export default function WorldPanel() {
  const {
    worldPrompt,
    isGeneratingWorld,
    setWorldPrompt,
    setEnvironmentMapUrl,
    setIsGeneratingWorld,
    setStatus,
  } = useDirectorStore();
  const { refinePrompt } = useNvidia();
  const { generateWorld } = useWorldLabs();

  const onGenerateWorld = async () => {
    if (!worldPrompt.trim()) return;
    setIsGeneratingWorld(true);
    try {
      setStatus('Refining world prompt with NVIDIA NIM...');
      const refined = await refinePrompt(worldPrompt, 'world');
      setStatus('Generating environment with World Labs...');
      const url = await generateWorld(refined);
      setEnvironmentMapUrl(url);
      setStatus('World environment applied.');
    } catch (error) {
      setStatus(`World generation failed: ${(error as Error).message}`);
    } finally {
      setIsGeneratingWorld(false);
    }
  };

  return (
    <div className="space-y-4">
      <label className="label">Describe your world...</label>
      <textarea
        className="input h-28"
        value={worldPrompt}
        onChange={(e) => setWorldPrompt(e.target.value)}
        placeholder="e.g. towering rainy megacity at midnight with holographic billboards"
      />
      <button className="btn-primary w-full" onClick={onGenerateWorld} disabled={isGeneratingWorld}>
        {isGeneratingWorld ? <Loader2 className="animate-spin" size={16} /> : <Globe2 size={16} />} Generate World
      </button>
    </div>
  );
}
