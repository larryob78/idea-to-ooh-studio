import { Suspense } from 'react';
import { Html, useGLTF } from '@react-three/drei';

function LoadedMesh({ url }: { url: string }) {
  const gltf = useGLTF(url);
  return <primitive object={gltf.scene} scale={1.2} position={[0, 0, 0]} />;
}

export default function CharacterMesh({ modelUrl }: { modelUrl: string | null }) {
  if (!modelUrl) {
    return (
      <mesh position={[0, 1, 0]}>
        <capsuleGeometry args={[0.45, 1.2, 4, 10]} />
        <meshStandardMaterial color="#8b8b8b" metalness={0.3} roughness={0.5} />
      </mesh>
    );
  }

  return (
    <Suspense
      fallback={
        <Html center>
          <div className="text-xs text-white">Loading character model...</div>
        </Html>
      }
    >
      <LoadedMesh url={modelUrl} />
    </Suspense>
  );
}
