import { CAMERA_PRESETS } from '../../utils/sceneHelpers';
import { useDirectorStore } from '../../store/useDirectorStore';

export default function CameraPanel() {
  const selected = useDirectorStore((s) => s.cameraPreset);
  const setCameraPreset = useDirectorStore((s) => s.setCameraPreset);

  return (
    <div className="grid grid-cols-2 gap-2">
      {Object.values(CAMERA_PRESETS).map((preset) => (
        <button
          key={preset.key}
          className={`pill ${selected === preset.key ? 'active' : ''}`}
          onClick={() => setCameraPreset(preset.key)}
        >
          {preset.label}
        </button>
      ))}
    </div>
  );
}
