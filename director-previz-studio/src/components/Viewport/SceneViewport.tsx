import { Canvas } from '@react-three/fiber';
import { Grid, OrbitControls } from '@react-three/drei';
import CharacterMesh from './CharacterMesh';
import WorldEnvironment from './WorldEnvironment';
import CameraRig from './CameraRig';
import LightingRig from './LightingRig';
import { useDirectorStore } from '../../store/useDirectorStore';

export default function SceneViewport() {
  const modelUrl = useDirectorStore((s) => s.characterModelUrl);
  const mapUrl = useDirectorStore((s) => s.environmentMapUrl);
  const setViewportCanvas = useDirectorStore((s) => s.setViewportCanvas);

  return (
    <div className="h-full w-full overflow-hidden rounded-glass border border-white/10">
      <Canvas
        shadows
        camera={{ position: [0, 1.2, 4], fov: 45 }}
        gl={{ preserveDrawingBuffer: true, antialias: true }}
        onCreated={({ gl }) => setViewportCanvas(gl.domElement)}
      >
        <color attach="background" args={['#0A0A0A']} />
        <WorldEnvironment mapUrl={mapUrl} />
        <CameraRig />
        <LightingRig />

        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[40, 40]} />
          <meshStandardMaterial color="#1a1a1a" metalness={0.1} roughness={0.9} />
        </mesh>

        <CharacterMesh modelUrl={modelUrl} />

        <Grid args={[20, 20]} sectionColor="#303030" cellColor="#252525" position={[0, 0.001, 0]} />
        <OrbitControls enablePan enableZoom minDistance={1.2} maxDistance={14} />
      </Canvas>
    </div>
  );
}
