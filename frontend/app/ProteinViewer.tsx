"use client";
import { useEffect, useRef, useState } from "react";
import Script from "next/script";

type RenderStyle = "cartoon" | "surface";
type ColorStyle = "normal" | "highlight";

export default function ProteinViewer({ proteinId }: { proteinId: string }) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const [viewerInstance, setViewerInstance] = useState<any>(null);
  
  const [renderStyle, setRenderStyle] = useState<RenderStyle>("cartoon");
  const [colorStyle, setColorStyle] = useState<ColorStyle>("highlight");
  
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [hasPocket, setHasPocket] = useState(false); 

  // --- CORE STYLING ENGINE ---
  const applyStyles = (viewer: any, rStyle: RenderStyle, cStyle: ColorStyle, pocketExists: boolean) => {
    if (!viewer) return;
    // @ts-ignore
    const $3Dmol = window.$3Dmol;

    // 1. Reset the canvas completely
    viewer.removeAllSurfaces();
    viewer.setStyle({}, {}); 

    // 2. Apply Matrix Logic
    if (rStyle === "cartoon") {
      if (cStyle === "normal") {
        // Mode 1: Normal Ribbon
        viewer.setStyle({model: 0}, { cartoon: { color: "spectrum" } });
        if (pocketExists) viewer.setStyle({model: 1}, {}); 
      } else {
        // Mode 2: Highlighted Ribbon
        viewer.setStyle({model: 0}, { cartoon: { color: "#555555" } }); 
        if (pocketExists) {
          viewer.setStyle({model: 1}, { cartoon: { color: "#ff2222" } }); 
          viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 0.85, color: "#ff2222"}, {model: 1});
        }
      }
    } else if (rStyle === "surface") {
      if (cStyle === "normal") {
        // Mode 3: Normal Surface (FIXED: Using 'color' instead of 'colorscheme')
        // We also render the cartoon inside the solid surface to guarantee the color maps correctly
        viewer.setStyle({model: 0}, { cartoon: { color: "spectrum" } }); 
        viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 1.0, color: "spectrum"}, {model: 0});
        if (pocketExists) viewer.setStyle({model: 1}, {}); 
      } else {
        // Mode 4: Highlighted Surface
        viewer.setStyle({model: 0}, {}); 
        viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 1.0, color: "#dddddd"}, {model: 0});
        if (pocketExists) {
          viewer.setStyle({model: 1}, {}); 
          viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 1.0, color: "#ff0000"}, {model: 1});
        }
      }
    }
    
    viewer.render();
  };

  useEffect(() => {
    if (!scriptLoaded || !viewerRef.current) return;
    if (!proteinId || proteinId === "undefined") {
      setErrorMsg("Awaiting valid protein target...");
      return;
    }

    // @ts-ignore
    if (typeof window === "undefined" || !window.$3Dmol) return;

    const renderProtein = async () => {
      viewerRef.current!.innerHTML = ""; 
      // @ts-ignore
      const viewer = window.$3Dmol.createViewer(viewerRef.current, {
        backgroundColor: "#050505",
      });
      setViewerInstance(viewer);
      
      let pocketSuccessfullyLoaded = false;

      try {
        let pdbData = "";
        try {
          const localResponse = await fetch(`http://127.0.0.1:8000/static/${proteinId}_CLEAN.pdb`);
          if (!localResponse.ok) throw new Error("Local fetch failed");
          pdbData = await localResponse.text();
        } catch (localErr) {
          const afResponse = await fetch(`https://alphafold.ebi.ac.uk/files/AF-${proteinId}-F1-model_v4.pdb`);
          if (!afResponse.ok) throw new Error("AlphaFold fetch failed");
          pdbData = await afResponse.text();
        }
        viewer.addModel(pdbData, "pdb");

        try {
          const pocketResponse = await fetch(`http://127.0.0.1:8000/static/${proteinId}_CLEAN_out/pockets/pocket1_atm.pdb`);
          if (pocketResponse.ok) {
            const pocketData = await pocketResponse.text();
            viewer.addModel(pocketData, "pdb");
            pocketSuccessfullyLoaded = true;
            setHasPocket(true);
          }
        } catch (pocketErr) {
          console.log("No pocket data found to overlay.");
        }

        applyStyles(viewer, renderStyle, colorStyle, pocketSuccessfullyLoaded);
        viewer.zoomTo();
        setErrorMsg(null);
      } catch (error) {
        console.error("Failed to load PDB for 3D render", error);
        setErrorMsg(`Failed to load 3D structure for ${proteinId}.`);
      }
    };

    renderProtein();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proteinId, scriptLoaded]);

  const handleStyleChange = (newRenderStyle: RenderStyle, newColorStyle: ColorStyle) => {
    setRenderStyle(newRenderStyle);
    setColorStyle(newColorStyle);
    applyStyles(viewerInstance, newRenderStyle, newColorStyle, hasPocket);
  };

  return (
    <div className="w-full relative h-full flex flex-col bg-[#050505]">
      <Script 
        src="https://3Dmol.org/build/3Dmol-min.js" 
        strategy="afterInteractive" 
        onLoad={() => setScriptLoaded(true)} 
      />
      
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-3">
        <div className="flex gap-2">
          <button 
            onClick={() => handleStyleChange("cartoon", colorStyle)}
            className={`px-3 py-1 text-xs font-bold rounded cursor-pointer transition-colors ${renderStyle === 'cartoon' ? 'bg-emerald-600 text-white' : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700'}`}
          >
            Ribbon View
          </button>
          <button 
            onClick={() => handleStyleChange("surface", colorStyle)}
            className={`px-3 py-1 text-xs font-bold rounded cursor-pointer transition-colors ${renderStyle === 'surface' ? 'bg-emerald-600 text-white' : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700'}`}
          >
            Surface View
          </button>
        </div>

        <div className="flex gap-2">
          <button 
            onClick={() => handleStyleChange(renderStyle, "normal")}
            className={`px-3 py-1 text-xs font-bold rounded cursor-pointer transition-colors ${colorStyle === 'normal' ? 'bg-blue-600 text-white' : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700'}`}
          >
            Normal Colors
          </button>
          <button 
            onClick={() => handleStyleChange(renderStyle, "highlight")}
            disabled={!hasPocket}
            className={`px-3 py-1 text-xs font-bold rounded transition-colors ${colorStyle === 'highlight' ? 'bg-red-600 text-white' : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700'} ${!hasPocket && 'opacity-50 cursor-not-allowed'}`}
          >
            Highlight Pocket
          </button>
        </div>
      </div>

      <div className="absolute top-4 right-4 z-10 text-xs text-emerald-500 font-mono bg-black/50 px-2 py-1 border border-neutral-800 rounded">
        TARGET: {proteinId && proteinId !== "undefined" ? proteinId : "---"}
      </div>

      {errorMsg && (
        <div className="absolute inset-0 flex items-center justify-center text-red-500 text-sm p-4 z-20 bg-black/80">
          {errorMsg}
        </div>
      )}

      <div ref={viewerRef} className="w-full flex-grow min-h-[400px]" />
    </div>
  );
}