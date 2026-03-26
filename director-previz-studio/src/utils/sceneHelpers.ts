import { CameraPreset, CameraPresetKey, LightingPreset, LightingPresetKey } from '../types';

export const CAMERA_PRESETS: Record<CameraPresetKey, CameraPreset> = {
  wide: {
    key: 'wide',
    label: 'Wide',
    position: [0, 1, 8],
    target: [0, 1, 0],
    fov: 60,
  },
  medium: {
    key: 'medium',
    label: 'Medium',
    position: [0, 1.2, 4],
    target: [0, 1.2, 0],
    fov: 45,
  },
  closeup: {
    key: 'closeup',
    label: 'Close-Up',
    position: [0, 1.6, 2],
    target: [0, 1.5, 0],
    fov: 35,
  },
  aerial: {
    key: 'aerial',
    label: 'Aerial',
    position: [0, 6, 2],
    target: [0, 0, 0],
    fov: 50,
  },
  dutch: {
    key: 'dutch',
    label: 'Dutch',
    position: [1.2, 1.4, 3.2],
    target: [0, 1.2, 0],
    fov: 45,
    rotation: [0, 0, 0.261799],
  },
};

export const LIGHTING_PRESETS: Record<LightingPresetKey, LightingPreset> = {
  goldenHour: {
    key: 'goldenHour',
    label: 'Golden Hour',
    swatch: '#FF9F45',
    description: 'Warm low-angle directional light',
  },
  night: {
    key: 'night',
    label: 'Night',
    swatch: '#1A2744',
    description: 'Cool ambient moonlit setup',
  },
  neon: {
    key: 'neon',
    label: 'Neon',
    swatch: '#E400FF',
    description: 'Magenta and cyan point lights',
  },
  dawn: {
    key: 'dawn',
    label: 'Dawn',
    swatch: '#FF8BA7',
    description: 'Pink-orange transitional light',
  },
  overcast: {
    key: 'overcast',
    label: 'Overcast',
    swatch: '#90A4AE',
    description: 'Soft hemisphere fill',
  },
  studio: {
    key: 'studio',
    label: 'Studio',
    swatch: '#FFFFFF',
    description: 'Balanced 3-point white lighting',
  },
};

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
