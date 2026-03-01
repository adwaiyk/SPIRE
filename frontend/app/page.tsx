"use client"; // This tells Next.js we are using client-side interactivity

import { useState } from "react";
import axios from "axios";

export default function Home() {
  const [property, setProperty] = useState("HAS_SULPHUR");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setResult(null);

    try {
      // Sending the request to our Python FastAPI server
      const response = await axios.post("http://localhost:8000/search", {
        required_property: property,
        // Mocking a 3D query vector for now
        query_vector: [9.5, 10.2, 9.8], 
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
    <main className="min-h-screen bg-neutral-950 text-white p-10 font-sans">
      <div className="max-w-3xl mx-auto space-y-8">
        
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-emerald-400">SPIRE Engine</h1>
          <p className="text-neutral-400 mt-2">Spatial Protein Indexing & Retrieval Engine</p>
        </div>

        {/* Search Panel */}
        <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-400 mb-2">
              Target Chemical Property
            </label>
            <input 
              type="text" 
              value={property}
              onChange={(e) => setProperty(e.target.value)}
              className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <button 
            onClick={handleSearch}
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Searching Metric Space..." : "Initialize Search"}
          </button>
        </div>

        {/* Results Panel */}
        {result && (
          <div className={`p-6 rounded-xl border ${result.match_found ? 'bg-emerald-950/30 border-emerald-900' : 'bg-red-950/30 border-red-900'}`}>
            <h2 className="text-xl font-bold mb-4">
              {result.match_found ? "✅ Match Discovered" : "❌ Search Rejected"}
            </h2>
            <pre className="bg-neutral-950 p-4 rounded-lg overflow-x-auto text-sm text-neutral-300">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

      </div>
    </main>
  );
}