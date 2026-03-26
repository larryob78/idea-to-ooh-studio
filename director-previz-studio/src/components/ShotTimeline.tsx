import { ArrowDown, ArrowUp, Camera, Plus, Trash2 } from 'lucide-react';
import { useDirectorStore } from '../store/useDirectorStore';

export default function ShotTimeline() {
  const {
    shots,
    shotName,
    cameraPreset,
    lightingPreset,
    characterPrompt,
    worldPrompt,
    viewportCanvas,
    setShotName,
    addShot,
    removeShot,
    moveShot,
  } = useDirectorStore();

  const saveShot = () => {
    if (!viewportCanvas) return;
    const thumbnail = viewportCanvas.toDataURL('image/png');
    addShot({
      id: crypto.randomUUID(),
      name: shotName || `Shot ${shots.length + 1}`,
      thumbnail,
      createdAt: new Date().toISOString(),
      cameraPreset,
      lightingPreset,
      characterPrompt,
      worldPrompt,
    });
  };

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 space-y-2">
        <label className="label">Shot Name</label>
        <input className="input" value={shotName} onChange={(e) => setShotName(e.target.value)} />
        <button className="btn-primary w-full" onClick={saveShot}>
          <Plus size={16} /> Save Shot
        </button>
      </div>

      <div className="space-y-2 overflow-y-auto pr-1">
        {shots.map((shot, idx) => (
          <div key={shot.id} className="rounded-xl border border-white/10 bg-white/5 p-2">
            <img src={shot.thumbnail} className="mb-2 h-24 w-full rounded-lg object-cover" alt={shot.name} />
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-medium text-white">{idx + 1}. {shot.name}</p>
              <span className="text-[10px] text-zinc-400">{shot.cameraPreset}</span>
            </div>
            <div className="flex gap-1">
              <button className="btn-ghost flex-1" onClick={() => moveShot(shot.id, 'up')}>
                <ArrowUp size={14} />
              </button>
              <button className="btn-ghost flex-1" onClick={() => moveShot(shot.id, 'down')}>
                <ArrowDown size={14} />
              </button>
              <button className="btn-ghost flex-1" onClick={() => removeShot(shot.id)}>
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {shots.length === 0 && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-dashed border-white/15 p-3 text-xs text-zinc-400">
          <Camera size={14} /> Save shots to build storyboard timeline.
        </div>
      )}
    </div>
  );
}
