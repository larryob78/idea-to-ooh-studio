import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import { EquirectangularReflectionMapping, TextureLoader } from 'three';

export default function WorldEnvironment({ mapUrl }: { mapUrl: string | null }) {
  const { scene } = useThree();

  useEffect(() => {
    if (!mapUrl) {
      scene.environment = null;
      scene.background = null;
      return;
    }

    const loader = new TextureLoader();
    loader.load(
      mapUrl,
      (texture) => {
        texture.mapping = EquirectangularReflectionMapping;
        scene.environment = texture;
        scene.background = texture;
      },
      undefined,
      () => {
        scene.background = null;
      },
    );
  }, [mapUrl, scene]);

  return null;
}
