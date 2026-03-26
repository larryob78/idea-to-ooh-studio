import { useMemo, useState } from 'react';
import { Bot, Camera, Globe2, Lightbulb, User } from 'lucide-react';
import TopBar from './components/TopBar';
import StatusBar from './components/StatusBar';
import SceneViewport from './components/Viewport/SceneViewport';
import CharacterPanel from './components/Sidebar/CharacterPanel';
import WorldPanel from './components/Sidebar/WorldPanel';
import CameraPanel from './components/Sidebar/CameraPanel';
import LightingPanel from './components/Sidebar/LightingPanel';
import NvidiaPanel from './components/Sidebar/NvidiaPanel';
import ShotTimeline from './components/ShotTimeline';
import ExportModal from './components/ExportModal';
import { TabItem } from './types';
import { useDirectorStore } from './store/useDirectorStore';

export default function App() {
  const [exportOpen, setExportOpen] = useState(false);
  const activeTab = useDirectorStore((s) => s.activeTab);
  const setActiveTab = useDirectorStore((s) => s.setActiveTab);

  const tabs = useMemo<TabItem[]>(
    () => [
      { key: 'character', label: 'Character', icon: <User size={15} /> },
      { key: 'world', label: 'World', icon: <Globe2 size={15} /> },
      { key: 'camera', label: 'Camera', icon: <Camera size={15} /> },
      { key: 'lighting', label: 'Lighting', icon: <Lightbulb size={15} /> },
      { key: 'ai', label: 'AI Enhance', icon: <Bot size={15} /> },
    ],
    [],
  );

  return (
    <div className="flex h-screen flex-col bg-ink text-zinc-100">
      <TopBar onOpenExport={() => setExportOpen(true)} />

      <main className="mx-auto flex h-[calc(100vh-92px)] w-full max-w-[1800px] gap-3 p-3">
        <aside className="glass-panel w-[320px] shrink-0 p-3">
          <div className="mb-4 flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`pill ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.key as any)}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          <div className="overflow-y-auto pr-1">
            {activeTab === 'character' && <CharacterPanel />}
            {activeTab === 'world' && <WorldPanel />}
            {activeTab === 'camera' && <CameraPanel />}
            {activeTab === 'lighting' && <LightingPanel />}
            {activeTab === 'ai' && <NvidiaPanel />}
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <SceneViewport />
        </section>

        <aside className="glass-panel w-[280px] shrink-0 p-3">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-300">Shot Timeline</h2>
          <ShotTimeline />
        </aside>
      </main>

      <StatusBar />
      <ExportModal open={exportOpen} onClose={() => setExportOpen(false)} />
    </div>
  );
}
