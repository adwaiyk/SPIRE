"use client";

import { useState } from "react";
import axios from "axios";
import ProteinViewer from "./ProteinViewer";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showMutation, setShowMutation] = useState(false);
  const [motifQuery, setMotifQuery] = useState("");
  const [motifResults, setMotifResults] = useState<any>(null);

  const handleMotifSearch = async () => {
    if (!motifQuery) return;
    try {
      const response = await axios.get(`http://localhost:8000/search_motif?motif=${motifQuery}`);
      setMotifResults(response.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSearch = async () => {
    if (!file) {
      alert("Please upload a .pdb file of the target key.");
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("required_property", "HAS_SULPHUR");

    try {
      const response = await axios.post(
        "http://localhost:8000/upload_search",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );
      setResult(response.data);
    } catch (error) {
      console.error("Error connecting to SPIRE Engine", error);
      setResult({ error: "Failed to connect to the backend engine." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800 font-sans pb-16">
      {/* HEADER */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20 px-8 py-4 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-blue-800 flex items-center gap-2">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
            SPIRE
          </h1>
          <p className="text-slate-500 mt-0.5 text-xs font-semibold tracking-wider uppercase">
            Spatial Protein Indexing & Retrieval Engine v4.0
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
          </span>
          <span className="text-xs font-bold text-slate-500 uppercase">Engine Online</span>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-6 mt-8">
        
        {/* COMPACT UPLOAD BAR (Always visible at top) */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-center gap-4 justify-between mb-8">
          <div className="flex items-center gap-4 w-full md:w-auto">
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-700">Target Sequence (.pdb)</p>
              <input
                type="file"
                accept=".pdb"
                onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                className="mt-1 block w-full text-xs text-slate-500 file:mr-4 file:py-1.5 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-bold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer transition-colors"
              />
            </div>
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !file}
            className="w-full md:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 px-8 rounded-lg shadow-md transition-all uppercase tracking-wider text-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Processing...
              </>
            ) : "Initialize Search"}
          </button>
        </div>

{/* SUFFIX TRIE MOTIF SEARCH */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4 mb-8 animate-fade-in">
          <div className="flex items-center gap-3 w-full">
            <div className="bg-indigo-50 p-2.5 rounded-lg border border-indigo-100">
              <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
            </div>
            <div className="flex-grow">
              <input
                type="text"
                placeholder="1D Motif Search (e.g., MKT, LLL, GXXG)"
                value={motifQuery}
                onChange={(e) => setMotifQuery(e.target.value.toUpperCase())}
                className="w-full bg-slate-50 border border-slate-200 text-sm rounded-md px-3 py-2 text-slate-700 outline-none focus:border-indigo-400 font-mono uppercase tracking-widest placeholder:normal-case placeholder:tracking-normal"
              />
            </div>
            <button
              onClick={handleMotifSearch}
              className="bg-indigo-100 hover:bg-indigo-200 text-indigo-700 font-bold py-2 px-6 rounded-md transition-colors text-xs uppercase tracking-wider"
            >
              Search
            </button>
          </div>
          
          {/* EXPANDED MOTIF RESULTS PANEL */}
          {motifResults && (
             <div className="w-full bg-indigo-50/50 rounded-lg border border-indigo-100 p-4 animate-fade-in mt-2">
                <div className="flex justify-between items-center mb-3 border-b border-indigo-100 pb-2">
                   <span className="text-xs font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-2">
                     <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                     O(m) Sequence Matches
                   </span>
                   <span className="text-[10px] font-bold bg-indigo-200 text-indigo-800 px-2.5 py-1 rounded-full tracking-widest">
                     {motifResults.match_count} TARGETS FOUND
                   </span>
                </div>
                
                {motifResults.match_count > 0 ? (
                  <div>
                    <p className="text-xs text-slate-500 mb-3 uppercase tracking-wide">
                      Top indexed protein identities containing motif: <span className="font-mono text-indigo-600 font-bold text-sm bg-white px-1 py-0.5 rounded border border-indigo-100">{motifResults.motif}</span>
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {motifResults.proteins.map((pid: string) => (
                        <div key={pid} className="bg-white border border-indigo-200 text-indigo-700 font-mono text-xs px-3 py-1.5 rounded shadow-sm flex items-center gap-2 transition-all hover:border-indigo-400 hover:shadow-md cursor-default">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                          {pid}
                        </div>
                      ))}
                      {motifResults.match_count > 10 && (
                        <div className="bg-slate-100 border border-slate-200 text-slate-500 font-mono text-xs px-3 py-1.5 rounded flex items-center">
                          + {motifResults.match_count - 10} additional sequences
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-slate-500 font-mono">No sequence matches found in the current index.</p>
                  </div>
                )}
             </div>
          )}
        </div>

        {/* EMPTY STATE */}
        {!result && !loading && (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <div className="bg-slate-100 p-6 rounded-full mb-6 border border-slate-200 shadow-inner">
               <svg className="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
            </div>
            <h2 className="text-2xl font-light text-slate-600">Awaiting Target Upload</h2>
            <p className="text-slate-400 mt-2 max-w-md">Upload a 3D Protein Data Bank (.pdb) file to initiate the spatial retrieval and indexing pipeline.</p>
          </div>
        )}

        {/* ERROR STATE */}
        {result && result.match_found === false && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-8 text-center max-w-2xl mx-auto mt-12 shadow-sm">
            <svg className="w-12 h-12 text-rose-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            <h3 className="text-xl font-bold text-rose-800 mb-2">Target Rejected</h3>
            <p className="text-rose-600">{result.reason || result.error}</p>
          </div>
        )}

        {/* SUCCESS DASHBOARD */}
        {result && result.match_found && (
          <div className="flex flex-col gap-6 animate-fade-in">
            
            {/* ALPHAMISSENSE ALERT */}
            {result.alphamissense_warning && (
              <div className="bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-xl shadow-sm flex items-start gap-4">
                <svg className="w-6 h-6 text-rose-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                <div>
                  <h4 className="font-bold text-rose-800 text-sm uppercase tracking-wide">AlphaMissense Critical Warning</h4>
                  <p className="text-rose-700 text-sm mt-1">DeepMind structural data indicates mutations in this region are likely pathogenic. Proceed with clinical caution.</p>
                </div>
              </div>
            )}

            {/* TOP KPI ROW */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Target Identity</p>
                <p className="text-2xl font-bold text-slate-800">{result.protein_id}</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Metric Distance</p>
                <p className="text-2xl font-light text-blue-600">{result.metric_distance?.toFixed(4)}</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-center">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">RMSD Alignment</p>
                <p className="text-2xl font-light text-indigo-600">{result.rmsd_alignment?.toFixed(2)} <span className="text-sm font-normal text-slate-400">Å</span></p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between relative overflow-hidden group">
                <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 relative z-10">GNN Binding Affinity</p>
                  <div className="flex items-baseline gap-2 relative z-10">
                    <p className="text-3xl font-bold text-emerald-600">{(result.ai_score * 100)?.toFixed(2)}%</p>
                    {/* Add a dynamic confidence badge based on the score */}
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${result.ai_score > 0.7 ? 'bg-emerald-100 text-emerald-700' : result.ai_score > 0.4 ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700'}`}>
                      {result.ai_score > 0.7 ? 'High' : result.ai_score > 0.4 ? 'Moderate' : 'Low'}
                    </span>
                  </div>
                </div>

                {/* GRAPH TOPOLOGY METRICS (EXPLAINABLE AI) */}
                <div className="mt-4 pt-3 border-t border-slate-100 relative z-10">
                  <p className="text-[8px] text-slate-400 uppercase font-bold mb-1.5">Graph Topology</p>
                  <div className="flex gap-3">
                    <div className="flex items-center gap-1">
                      <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                      <span className="text-xs font-mono text-slate-600">{result.graph_nodes || 0} Nodes</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                      <span className="text-xs font-mono text-slate-600">{result.graph_edges || 0} Edges</span>
                    </div>
                  </div>
                </div>

                {/* Background decorative graphic */}
                <div className="absolute right-0 bottom-0 opacity-[0.03] transition-opacity duration-500 group-hover:opacity-[0.08]">
                  <svg className="w-32 h-32 -mr-8 -mb-8" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                </div>
              </div>
            </div>

            {/* MIDDLE ROW: Viewer & Structural Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-auto lg:h-[500px]">
              
              {/* 3D VIEWER */}
              <div className="col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[500px] lg:h-auto">
                <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex justify-between items-center">
                   <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                     <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"></path></svg>
                     Spatial Conformation Viewer
                   </h3>
                </div>
                <div className="flex-grow bg-[#111827]"> 
                   {/* Wrapping ProteinViewer in a dark bg ensures 3D renders correctly if it relies on contrast */}
                   <ProteinViewer proteinId={result.protein_id} />
                </div>
              </div>

              {/* STRUCTURAL METRICS & MUTATION */}
              <div className="col-span-1 flex flex-col gap-6">
                
                {/* Druggability & pLDDT Card */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col justify-center flex-grow">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-6 border-b border-slate-100 pb-2">Physical Viability</h3>
                  
                  {/* Druggability */}
                  <div className="mb-6">
                    <div className="flex justify-between items-end mb-2">
                      <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wide">Druggability Index</p>
                      <p className="text-sm font-bold text-slate-800">{((result.druggability_score || 0) * 100).toFixed(1)} / 100</p>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-1000 ${result.druggability_score > 0.7 ? "bg-emerald-500" : result.druggability_score > 0.4 ? "bg-amber-400" : "bg-rose-500"}`} 
                        style={{ width: `${Math.max(5, (result.druggability_score || 0) * 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* pLDDT */}
                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wide flex items-center gap-2">
                        Target Rigidity (pLDDT)
                        <span className="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 tracking-normal">
                          {result.af_api_status || "Checking..."}
                        </span>
                      </p>
                      <p className="text-sm font-bold text-slate-800">{result.pocket_plddt?.toFixed(1)}</p>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-1000 ${
                          (result.pocket_plddt || 0) > 90 ? 'bg-blue-600' : 
                          (result.pocket_plddt || 0) > 70 ? 'bg-sky-500' : 'bg-slate-400'
                        }`} 
                        style={{ width: `${Math.max(5, result.pocket_plddt || 0)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Counterfactual Simulator Card */}
                <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-md p-1 overflow-hidden">
                  <div className="p-5 flex flex-col h-full justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
                        <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                        Counterfactual Analysis
                      </h3>
                      <p className="text-slate-400 text-xs leading-relaxed mb-4">
                        Apply Gaussian noise (+0.5 Å) to simulate evolutionary mutation and calculate structural drift.
                      </p>
                    </div>
                    
                    {!showMutation ? (
                      <button 
                        onClick={() => setShowMutation(true)}
                        className="w-full bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-800/50 text-cyan-400 font-bold py-2.5 rounded-lg transition-colors text-xs uppercase tracking-widest"
                      >
                        Run Stress Test
                      </button>
                    ) : (
                      <div className="bg-black/50 rounded-lg p-3 border border-slate-800 animate-fade-in">
                         <div className="flex justify-between items-center mb-3">
                           <span className="text-[10px] text-slate-500 uppercase font-bold">Results</span>
                           <span className="text-[9px] bg-rose-950/50 text-rose-400 px-2 py-0.5 rounded border border-rose-900/50">DRIFT DETECTED</span>
                         </div>
                         <div className="flex items-center justify-between">
                            <div className="text-center">
                              <p className="text-[9px] text-slate-500 uppercase mb-0.5">Original</p>
                              <p className="font-mono text-white text-sm">{(result.ai_score * 100)?.toFixed(1)}%</p>
                            </div>
                            <div className="text-center px-2">
                              <p className="text-[9px] text-slate-500 uppercase mb-0.5">Delta</p>
                              <p className="font-mono font-bold text-rose-500 text-sm">-{((result.affinity_drop || 0) * 100).toFixed(1)}%</p>
                            </div>
                            <div className="text-center">
                              <p className="text-[9px] text-slate-500 uppercase mb-0.5">Mutated</p>
                              <p className="font-mono text-cyan-400 text-sm">{((result.mutated_ai_score || 0) * 100).toFixed(1)}%</p>
                            </div>
                         </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* BOTTOM ROW: Pharmacology & Report */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Pharmacology Context */}
              <div className="col-span-1 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-5 flex items-center gap-2">
                  <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                  Pharmacology Profile
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Target Name</p>
                    <p className="text-sm text-slate-800 font-medium">{result.pharmacology?.protein_name}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Primary Tissue</p>
                    <p className="text-sm text-slate-700">{result.pharmacology?.primary_tissue}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Known Ligands</p>
                    <p className="text-sm text-blue-600 font-medium">{result.pharmacology?.known_ligands}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Clinical Application</p>
                    <p className="text-sm text-slate-700">{result.pharmacology?.clinical_target}</p>
                  </div>
                  <div className="bg-rose-50 p-3 rounded-lg border border-rose-100 mt-2">
                    <p className="text-[10px] font-bold text-rose-500 uppercase tracking-widest mb-0.5">Adverse Effects</p>
                    <p className="text-sm text-rose-700">{result.pharmacology?.side_effects}</p>
                  </div>
                </div>
              </div>

              {/* Agentic Report */}
              <div className="col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col">
                <div className="flex justify-between items-center mb-5">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    Autonomous Target Justification
                  </h3>
                  <span className="text-[10px] bg-indigo-50 text-indigo-600 px-2 py-1 rounded border border-indigo-100 font-bold tracking-wide">
                    LLAMA 3.3 AGENT
                  </span>
                </div>
                
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 flex-grow">
                  {result.clinical_report ? (
                    <div className="prose prose-sm prose-slate max-w-none font-serif text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {result.clinical_report}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-400 text-sm font-mono">
                      Generating narrative report...
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>
    </main>
  );
}