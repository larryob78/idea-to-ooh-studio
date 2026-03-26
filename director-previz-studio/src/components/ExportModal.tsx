import { X, Download } from 'lucide-react';
import jsPDF from 'jspdf';
import { useDirectorStore } from '../store/useDirectorStore';

interface ExportModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ExportModal({ open, onClose }: ExportModalProps) {
  const shots = useDirectorStore((s) => s.shots);
  const canvas = useDirectorStore((s) => s.viewportCanvas);

  if (!open) return null;

  const exportPNG = () => {
    if (!canvas) return;
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = `previz-frame-${Date.now()}.png`;
    link.click();
  };

  const exportPDF = () => {
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
    if (shots.length === 0) {
      doc.text('No shots available. Save shots before exporting storyboard.', 10, 10);
      doc.save('storyboard.pdf');
      return;
    }

    shots.forEach((shot, index) => {
      if (index > 0) doc.addPage();
      doc.setFontSize(18);
      doc.text(shot.name, 10, 14);
      doc.setFontSize(10);
      doc.text(`Camera: ${shot.cameraPreset} | Lighting: ${shot.lightingPreset}`, 10, 21);
      doc.addImage(shot.thumbnail, 'PNG', 10, 26, 190, 106);
      doc.text(`Character: ${shot.characterPrompt || '—'}`, 10, 140);
      doc.text(`World: ${shot.worldPrompt || '—'}`, 10, 147);
      doc.text(`Created: ${new Date(shot.createdAt).toLocaleString()}`, 10, 154);
    });

    doc.save(`storyboard-${Date.now()}.pdf`);
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="glass-panel w-[420px] p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Export</h3>
          <button className="btn-ghost" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <p className="mb-5 text-sm text-zinc-300">
          Export a still PNG from the current viewport or a storyboard PDF containing every saved shot.
        </p>
        <div className="flex gap-2">
          <button className="btn-primary flex-1" onClick={exportPNG}>
            <Download size={16} /> Export PNG
          </button>
          <button className="btn-primary flex-1" onClick={exportPDF}>
            <Download size={16} /> Export PDF
          </button>
        </div>
      </div>
    </div>
  );
}
