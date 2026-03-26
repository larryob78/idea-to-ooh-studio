import { create } from 'zustand';
import { CameraPresetKey, GenerationProvider, LightingPresetKey, Shot } from '../types';

interface DirectorState {
  activeTab: 'character' | 'world' | 'camera' | 'lighting' | 'ai';
  generationProvider: GenerationProvider;
  characterPrompt: string;
  worldPrompt: string;
  refinedPrompt: string;
  characterModelUrl: string | null;
  environmentMapUrl: string | null;
  cameraPreset: CameraPresetKey;
  lightingPreset: LightingPresetKey;
  shotName: string;
  shots: Shot[];
  selectedShotId: string | null;
  isGeneratingCharacter: boolean;
  isGeneratingWorld: boolean;
  status: string;
  viewportCanvas: HTMLCanvasElement | null;
  setActiveTab: (tab: DirectorState['activeTab']) => void;
  setGenerationProvider: (provider: GenerationProvider) => void;
  setCharacterPrompt: (value: string) => void;
  setWorldPrompt: (value: string) => void;
  setRefinedPrompt: (value: string) => void;
  setCharacterModelUrl: (value: string | null) => void;
  setEnvironmentMapUrl: (value: string | null) => void;
  setCameraPreset: (value: CameraPresetKey) => void;
  setLightingPreset: (value: LightingPresetKey) => void;
  setShotName: (value: string) => void;
  addShot: (shot: Shot) => void;
  removeShot: (shotId: string) => void;
  moveShot: (shotId: string, direction: 'up' | 'down') => void;
  setSelectedShotId: (shotId: string | null) => void;
  setIsGeneratingCharacter: (value: boolean) => void;
  setIsGeneratingWorld: (value: boolean) => void;
  setStatus: (value: string) => void;
  setViewportCanvas: (canvas: HTMLCanvasElement | null) => void;
}

export const useDirectorStore = create<DirectorState>((set, get) => ({
  activeTab: 'character',
  generationProvider: 'meshy',
  characterPrompt: '',
  worldPrompt: '',
  refinedPrompt: '',
  characterModelUrl: null,
  environmentMapUrl: null,
  cameraPreset: 'medium',
  lightingPreset: 'goldenHour',
  shotName: 'Shot 1',
  shots: [],
  selectedShotId: null,
  isGeneratingCharacter: false,
  isGeneratingWorld: false,
  status: 'Ready',
  viewportCanvas: null,
  setActiveTab: (activeTab) => set({ activeTab }),
  setGenerationProvider: (generationProvider) => set({ generationProvider }),
  setCharacterPrompt: (characterPrompt) => set({ characterPrompt }),
  setWorldPrompt: (worldPrompt) => set({ worldPrompt }),
  setRefinedPrompt: (refinedPrompt) => set({ refinedPrompt }),
  setCharacterModelUrl: (characterModelUrl) => set({ characterModelUrl }),
  setEnvironmentMapUrl: (environmentMapUrl) => set({ environmentMapUrl }),
  setCameraPreset: (cameraPreset) => set({ cameraPreset }),
  setLightingPreset: (lightingPreset) => set({ lightingPreset }),
  setShotName: (shotName) => set({ shotName }),
  addShot: (shot) => set((state) => ({ shots: [...state.shots, shot] })),
  removeShot: (shotId) =>
    set((state) => ({ shots: state.shots.filter((shot) => shot.id !== shotId) })),
  moveShot: (shotId, direction) => {
    const shots = [...get().shots];
    const index = shots.findIndex((shot) => shot.id === shotId);
    if (index === -1) return;
    const nextIndex = direction === 'up' ? index - 1 : index + 1;
    if (nextIndex < 0 || nextIndex >= shots.length) return;
    [shots[index], shots[nextIndex]] = [shots[nextIndex], shots[index]];
    set({ shots });
  },
  setSelectedShotId: (selectedShotId) => set({ selectedShotId }),
  setIsGeneratingCharacter: (isGeneratingCharacter) => set({ isGeneratingCharacter }),
  setIsGeneratingWorld: (isGeneratingWorld) => set({ isGeneratingWorld }),
  setStatus: (status) => set({ status }),
  setViewportCanvas: (viewportCanvas) => set({ viewportCanvas }),
}));
