import { useDirectorStore } from '../../store/useDirectorStore';

export default function LightingRig() {
  const preset = useDirectorStore((s) => s.lightingPreset);

  if (preset === 'goldenHour') {
    return (
      <>
        <ambientLight intensity={0.3} color="#ffd8a8" />
        <directionalLight position={[-3, 2, 1]} intensity={1.5} color="#FF9F45" />
      </>
    );
  }
  if (preset === 'night') {
    return (
      <>
        <ambientLight intensity={0.25} color="#1A2744" />
        <directionalLight position={[2, 5, -2]} intensity={0.7} color="#8ab6ff" />
      </>
    );
  }
  if (preset === 'neon') {
    return (
      <>
        <ambientLight intensity={0.15} />
        <pointLight position={[2, 2, 2]} intensity={18} color="#FF00EA" distance={10} />
        <pointLight position={[-2, 2, -2]} intensity={18} color="#00E7FF" distance={10} />
      </>
    );
  }
  if (preset === 'dawn') {
    return (
      <>
        <ambientLight intensity={0.35} color="#ffc1d6" />
        <directionalLight position={[0, 3, 3]} intensity={1.2} color="#ffa06b" />
      </>
    );
  }
  if (preset === 'overcast') {
    return (
      <>
        <hemisphereLight intensity={1.1} color="#d8dee9" groundColor="#7a8691" />
      </>
    );
  }

  return (
    <>
      <ambientLight intensity={0.2} />
      <directionalLight position={[3, 3, 2]} intensity={1.2} color="#ffffff" />
      <directionalLight position={[-3, 2, -2]} intensity={0.9} color="#f0f0f0" />
      <pointLight position={[0, 2.5, 2]} intensity={0.75} color="#ffffff" />
    </>
  );
}
