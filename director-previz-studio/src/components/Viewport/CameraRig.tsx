import { useFrame, useThree } from '@react-three/fiber';
import { CAMERA_PRESETS } from '../../utils/sceneHelpers';
import { useDirectorStore } from '../../store/useDirectorStore';
import { MathUtils } from 'three';

export default function CameraRig() {
  const cameraPreset = useDirectorStore((s) => s.cameraPreset);
  const { camera } = useThree();

  useFrame(() => {
    const preset = CAMERA_PRESETS[cameraPreset];
    camera.position.lerp(
      {
        x: preset.position[0],
        y: preset.position[1],
        z: preset.position[2],
      } as any,
      0.08,
    );
    camera.lookAt(preset.target[0], preset.target[1], preset.target[2]);
    camera.fov = MathUtils.lerp(camera.fov, preset.fov, 0.08);
    if (preset.rotation) {
      camera.rotation.z = MathUtils.lerp(camera.rotation.z, preset.rotation[2], 0.08);
    } else {
      camera.rotation.z = MathUtils.lerp(camera.rotation.z, 0, 0.08);
    }
    camera.updateProjectionMatrix();
  });

  return null;
}
