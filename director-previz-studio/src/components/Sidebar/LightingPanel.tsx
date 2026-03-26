import { useDirectorStore } from '../../store/useDirectorStore';
import { LIGHTING_PRESETS } from '../../utils/sceneHelpers';

export default function LightingPanel() {
  const selected = useDirectorStore((s) => s.lightingPreset);
  const setLightingPreset = useDirectorStore((s) => s.setLightingPreset);

  return (
    <div className="space-y-3">
      {Object.values(LIGHTING_PRESETS).map((preset) => (
        <button
          key={preset.key}
          className={`flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left transition-all duration-300 ${
            selected === preset.key
              ? 'border-accent bg-accent/10 text-white'
              : 'border-white/10 bg-white/5 text-zinc-200 hover:border-white/30'
          }`}
          onClick={() => setLightingPreset(preset.key)}
        >
          <span className="h-6 w-6 rounded-full border border-white/20" style={{ background: preset.swatch }} />
          <span>
            <span className="block text-sm font-medium">{preset.label}</span>
            <span className="text-xs text-zinc-400">{preset.description}</span>
          </span>
        </button>
      ))}
    </div>
  );
}
