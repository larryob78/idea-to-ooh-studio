# Director Pre-Visualisation Studio

A production-ready, Apple-inspired dark-mode previsualization workspace for directors, cinematographers, and storyboard artists.

## Stack

- React + TypeScript + Vite
- Three.js + React Three Fiber + Drei
- Tailwind CSS
- Zustand state management
- Axios API clients
- Lucide React icons
- html2canvas + jsPDF export pipeline

## Features

- **Three-column studio layout**
  - Left (320px): Character, World, Camera, Lighting, AI Enhance tabs
  - Center: Real-time 3D scene viewport
  - Right (280px): Shot timeline and shot properties
- **Character generation**
  - Enter who is in scene
  - NVIDIA NIM prompt refinement
  - Meshy generation with Trellis fallback toggle
  - Polling + GLB loading into viewport
- **World generation**
  - Generate 360/equirectangular world textures from prompt
  - Apply directly as scene environment map
- **Cinematography controls**
  - Camera presets: Wide, Medium, Close-Up, Aerial, Dutch
  - Lighting presets: Golden Hour, Night, Neon, Dawn, Overcast, Studio
- **Shot workflow**
  - Save shot compositions with thumbnail
  - Reorder storyboard sequence
  - Export current frame as PNG
  - Export entire shot list as storyboard PDF

## Environment Variables

Copy `.env.example` to `.env` and set:

```bash
VITE_MESHY_API_KEY=...
VITE_TRELLIS_API_KEY=...
VITE_WORLDLABS_API_KEY=...
VITE_NVIDIA_API_KEY=...
```

## Local Development

```bash
npm install
npm run dev
```

Then open `http://localhost:5173`.

## API Notes

### Meshy API
- POST `/v2/text-to-3d`
- Poll `/v2/text-to-3d/:id`
- When status succeeds, use returned `glb` URL.

### Trellis API
- Optional fallback generation (toggle in Character tab).
- Same UX as Meshy: async submit + polling + GLB output.

### World Labs API
- POST `/v1/worlds/generate`
- Poll task endpoint until completion
- Apply returned image/HDR URL as equirectangular environment map.

### NVIDIA NIM API
- Chat completion model: `meta/llama-3.1-70b-instruct`
- Used for character/world prompt enhancement and AI Enhance panel.

## Batman / Gotham Example Workflow

1. In **Character**, type:
   - `Batman standing on a gothic rooftop, cape flowing, cinematic silhouette`
2. In **AI Enhance**, use style cues:
   - `high contrast noir, volumetric fog, anamorphic framing`
3. In **World**, type:
   - `Rainy Gotham skyline at night, neon reflections, storm clouds, distant lightning`
4. Set camera to **Medium** or **Dutch**.
5. Set lighting to **Night** or **Neon**.
6. Save multiple shots in timeline:
   - Establishing wide
   - Hero medium
   - Dutch close-up
7. Export storyboard PDF for production planning.

## Production Hardening Checklist

- Add server-side proxy if CORS blocks direct browser API calls.
- Secure API keys and enforce usage limits.
- Add auth/role controls for team collaboration.
- Persist projects to backend storage.
- Add undo/redo and keyframe animation tools.
