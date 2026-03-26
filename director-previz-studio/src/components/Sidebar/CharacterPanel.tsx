import { Loader2, WandSparkles } from 'lucide-react';
import { useDirectorStore } from '../../store/useDirectorStore';
import { useMeshy } from '../../hooks/useMeshy';
import { useNvidia } from '../../hooks/useNvidia';
import { useTrellis } from '../../hooks/useTrellis';

export default function CharacterPanel() {
  const {
    characterPrompt,
    generationProvider,
    isGeneratingCharacter,
    setCharacterPrompt,
    setGenerationProvider,
    setCharacterModelUrl,
    setRefinedPrompt,
    setIsGeneratingCharacter,
    setStatus,
  } = useDirectorStore();
  const { generateCharacter: generateMeshy } = useMeshy();
  const { generateCharacter: generateTrellis } = useTrellis();
  const { refinePrompt } = useNvidia();

  const onGenerate = async () => {
    if (!characterPrompt.trim()) return;
    setIsGeneratingCharacter(true);
    try {
      setStatus('Refining character prompt with NVIDIA NIM...');
      const refined = await refinePrompt(characterPrompt, 'character');
      setRefinedPrompt(refined);
      setStatus(`Generating character via ${generationProvider}...`);
      const glb =
        generationProvider === 'meshy'
          ? await generateMeshy(refined)
          : await generateTrellis(refined);
      setCharacterModelUrl(glb);
      setStatus('Character loaded successfully.');
    } catch (error) {
      setStatus(`Character generation failed: ${(error as Error).message}`);
    } finally {
      setIsGeneratingCharacter(false);
    }
  };

  return (
    <div className="space-y-4">
      <label className="label">Who is in your scene?</label>
      <textarea
        className="input h-28"
        value={characterPrompt}
        onChange={(e) => setCharacterPrompt(e.target.value)}
        placeholder="e.g. armored detective standing under rain in neon alley..."
      />
      <div className="flex gap-2 rounded-xl bg-black/20 p-1">
        <button
          className={`toggle-pill ${generationProvider === 'meshy' ? 'active' : ''}`}
          onClick={() => setGenerationProvider('meshy')}
        >
          Meshy
        </button>
        <button
          className={`toggle-pill ${generationProvider === 'trellis' ? 'active' : ''}`}
          onClick={() => setGenerationProvider('trellis')}
        >
          Trellis
        </button>
      </div>
      <button className="btn-primary w-full" onClick={onGenerate} disabled={isGeneratingCharacter}>
        {isGeneratingCharacter ? <Loader2 className="animate-spin" size={16} /> : <WandSparkles size={16} />} Generate
      </button>
    </div>
  );
}
