import { ReactNode } from 'react';
import { EulerTuple, Vector3Tuple } from 'three';

export type GenerationProvider = 'meshy' | 'trellis';

export type CameraPresetKey = 'wide' | 'medium' | 'closeup' | 'aerial' | 'dutch';
export type LightingPresetKey =
  | 'goldenHour'
  | 'night'
  | 'neon'
  | 'dawn'
  | 'overcast'
  | 'studio';

export interface CameraPreset {
  key: CameraPresetKey;
  label: string;
  position: Vector3Tuple;
  target: Vector3Tuple;
  fov: number;
  rotation?: EulerTuple;
}

export interface LightingPreset {
  key: LightingPresetKey;
  label: string;
  swatch: string;
  description: string;
}

export interface Shot {
  id: string;
  name: string;
  thumbnail: string;
  createdAt: string;
  cameraPreset: CameraPresetKey;
  lightingPreset: LightingPresetKey;
  characterPrompt: string;
  worldPrompt: string;
}

export interface TabItem {
  key: string;
  label: string;
  icon: ReactNode;
}
