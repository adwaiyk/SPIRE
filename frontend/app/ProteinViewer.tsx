"use client";

import { useEffect, useRef } from "react";

interface ProteinViewerProps {
  proteinId: string;
}

export default function ProteinViewer({ proteinId }: ProteinViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // We dynamically load the script ONLY when the component mounts in the browser
    const loadViewer = async () => {
      try {
        // @ts-ignore - Dynamically importing the exact built file
        const $3Dmol = await import("3dmol/build/3Dmol.js");

        if (!viewerRef.current) return;

        const viewer = $3Dmol.createViewer(viewerRef.current, {
          backgroundColor: "#0a0a0a",
        });

        // Use the PDB code based on our match
        const pdbCode = proteinId === "Target_COVID_Spike" ? "6LU7" : "1CRN";
        
        const response = await fetch(`https://files.rcsb.org/view/${pdbCode}.pdb`);
        const pdbData = await response.text();
        
        viewer.addModel(pdbData, "pdb");
        viewer.setStyle({}, { cartoon: { color: "spectrum" } });
        viewer.zoomTo();
        viewer.render();
      } catch (err) {
        console.error("3Dmol rendering error:", err);
      }
    };

    loadViewer();
  }, [proteinId]);

  return (
    <div className="w-full h-[400px] rounded-xl border border-neutral-800 bg-[#0a0a0a] overflow-hidden relative shadow-inner">
       <div className="absolute top-4 left-4 z-10 bg-black/60 text-emerald-400 px-4 py-2 rounded-md text-xs font-mono backdrop-blur-md border border-emerald-900/50">
        LIVE 3D RENDER: {proteinId === "Target_COVID_Spike" ? "SARS-CoV-2 Main Protease" : "Protein Match"}
      </div>
      <div ref={viewerRef} className="w-full h-full" />
    </div>
  );
}