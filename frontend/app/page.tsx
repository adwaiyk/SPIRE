"use client";

import { useState } from "react";
import axios from "axios";
import ProteinViewer from "./ProteinViewer";

export default function Home() {
  const [property, setProperty] = useState("HAS_SULPHUR");
  // Defaulting to the new p53 PCA vector we generated
  const [vecX, setVecX] = useState<number>(44.5);
  const [vecY, setVecY] = useState<number>(1.2);
  const [vecZ, setVecZ] = useState<number>(0.0);
  
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post("http://localhost:8000/search", {
        required_property: property,
        query_vector: [vecX, vecY, vecZ], 
      });
      
      setResult(response.data);
    } catch (error) {
      console.error("Error connecting to SPIRE Engine", error);
      setResult({ error: "Failed to connect to the backend engine." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#050505] text-white p-10 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="border-b border-neutral-800 pb-6 flex justify-between items-end">
          <div>
            <h1 className="text-5xl font-extrabold tracking-tight text-emerald-500">SPIRE <span className="text-white">Engine</span></h1>
            <p className="text-neutral-400 mt-2 text-lg">Spatial Protein Indexing & Retrieval Engine</p>
          </div>
          <div className="text-xs text-neutral-500 font-mono text-right">
            <p>ACTIVE MODULES:</p>
            <p>✅ Unit 5: VP-Tree</p>
            <p>✅ Unit 6: Bloom Filter</p>
            <p>✅ PyTorch GNN</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls Panel */}
          <div className="col-span-1 bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-6 h-fit shadow-xl">
            <div>
              <label className="block text-sm font-semibold text-neutral-300 mb-2">Target Property</label>
              <input 
                type="text" 
                value={property}
                onChange={(e) => setProperty(e.target.value)}
                className="w-full bg-black border border-neutral-700 rounded-lg p-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div className="space-y-3">
              <label className="block text-sm font-semibold text-neutral-300">3D Shape Vector (PCA)</label>
              <div className="flex gap-2">
                <input type="number" step="0.1" value={vecX} onChange={(e) => setVecX(parseFloat(e.target.value))} className="w-1/3 bg-black border border-neutral-700 rounded-lg p-2 text-center text-sm focus:border-emerald-500 outline-none" placeholder="X" />
                <input type="number" step="0.1" value={vecY} onChange={(e) => setVecY(parseFloat(e.target.value))} className="w-1/3 bg-black border border-neutral-700 rounded-lg p-2 text-center text-sm focus:border-emerald-500 outline-none" placeholder="Y" />
                <input type="number" step="0.1" value={vecZ} onChange={(e) => setVecZ(parseFloat(e.target.value))} className="w-1/3 bg-black border border-neutral-700 rounded-lg p-2 text-center text-sm focus:border-emerald-500 outline-none" placeholder="Z" />
              </div>
            </div>

            <button 
              onClick={handleSearch}
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded-lg transition-all active:scale-95 disabled:opacity-50"
            >
              {loading ? "Analyzing Topology..." : "Initialize Search"}
            </button>
          </div>

          {/* Results Panel */}
          <div className="col-span-2 space-y-6">
            {result ? (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
                
                {/* Result Card */}
                <div className={`p-6 rounded-xl border ${result.match_found ? 'bg-emerald-950/20 border-emerald-900/50' : 'bg-red-950/20 border-red-900/50'}`}>
                  <h2 className={`text-2xl font-bold ${result.match_found ? 'text-emerald-400' : 'text-red-400'}`}>
                    {result.match_found ? `Match Discovered: ${result.protein_id}` : "Search Rejected"}
                  </h2>
                  <p className="text-neutral-400 mt-1 text-sm">{result.message || result.reason}</p>
                  
                  {result.match_found && (
                    <div className="flex gap-4 mt-6">
                      <div className="bg-black/50 border border-neutral-800 px-4 py-3 rounded-lg w-1/2">
                        <p className="text-xs text-neutral-500 font-semibold mb-1 uppercase tracking-wider">VP-Tree Metric Distance</p>
                        <p className="text-xl font-mono text-emerald-300">{result.metric_distance.toFixed(4)}</p>
                      </div>
                      <div className="bg-black/50 border border-neutral-800 px-4 py-3 rounded-lg w-1/2">
                        <p className="text-xs text-neutral-500 font-semibold mb-1 uppercase tracking-wider">GNN Binding Affinity</p>
                        <p className="text-xl font-mono text-blue-400">{(result.ai_score * 100).toFixed(2)}%</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* AlphaMissense Warning */}
                {result.alphamissense_warning && (
                  <div className="bg-red-950/40 border border-red-800 p-5 rounded-xl flex items-start gap-4 animate-in fade-in zoom-in duration-500">
                    <div className="text-4xl">⚠️</div>
                    <div>
                      <h3 className="text-red-400 font-bold text-lg tracking-tight">AlphaMissense Critical Warning</h3>
                      <p className="text-red-200/80 text-sm mt-1 leading-relaxed">
                        DeepMind AlphaMissense data indicates that the target pocket on <span className="font-bold">{result.protein_id}</span> is highly conserved. Mutations in this region are likely pathogenic. Proceed with extreme caution: drug targeting may result in rapid evolutionary resistance.
                      </p>
                    </div>
                  </div>
                )}

                {/* 3D Viewer */}
                {result.match_found && result.protein_id && (
                  <ProteinViewer proteinId={result.protein_id} />
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center border border-dashed border-neutral-800 rounded-xl p-10 text-neutral-500 bg-neutral-900/20">
                <p>Awaiting 3D topological input...</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </main>
  );
}