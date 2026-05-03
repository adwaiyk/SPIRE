# 🧬 SPIRE: Spatial Protein Indexing & Retrieval Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Geometric-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-React-black?style=for-the-badge&logo=next.js&logoColor=white)
![AI](https://img.shields.io/badge/AI_Agent-LLaMA_3.3-purple?style=for-the-badge)

---

## 🚀 Overview

**SPIRE** is a high-performance, multi-stage retrieval engine designed to index and search:

- 3D protein structures  
- 1D genetic motifs  

It replaces traditional **O(N²)** biological alignments with advanced spatial and string indexing, enabling **sub-linear querying** of massive structural databases.

---

## 🛑 Problem Statement

### 1. Dimensionality Crisis (O(N²) Bottleneck)
Protein comparison relies on expensive all-against-all RMSD alignments. With databases like AlphaFold scaling to hundreds of millions of entries, this becomes computationally infeasible.

### 2. Structural vs Sequence Gap
Proteins may share:
- Similar structure but different sequences  
- Similar sequences but different structures  

Most tools handle only one domain, missing cross-domain insights.

### 3. Resource & Compute Wastage
Running heavy computation across entire datasets wastes:
- CPU/GPU cycles  
- Cloud costs  
- Energy  

---

## 🏗️ System Architecture

SPIRE uses a **coarse-to-fine retrieval pipeline**:

### Phase 1: Gatekeeper (Chemical Filtering)
- **Data Structure:** Bloom Filter  
- **Complexity:** O(k)  
- Eliminates irrelevant proteins with zero false negatives  

---

### Phase 2: Broad Quantization (Spatial Binning)
- **Data Structure:** Geometric Hash Table  
- **Complexity:** O(1)  
- Converts 3D structure into hashable spatial bins  

---

### Phase 3: Precision Spatial Search
- **Data Structure:** VP-Tree  
- **Complexity:** O(log N)  
- Uses triangle inequality to prune search space  

---

### Phase 4: Sequence Matching
- **Data Structure:** Generalized Suffix Trie  
- **Complexity:** O(m)  
- Fast motif lookup independent of database size  

---

### Phase 5: AI Binding Prediction
- **Model:** Graph Convolutional Network (GCN)  
- Converts protein structure into graph representation  
- Predicts binding affinity  

---

### Phase 6: Clinical Justification
- **Model:** LLaMA-3.3-70B  
- Produces human-readable reports from:
  - RMSD  
  - GNN affinity  
  - Structural metrics  

---

## 💻 Tech Stack

### Core Engineering
- Python 3.10+
- C++ (via pybind11)
- FastAPI

### Machine Learning & Bioinformatics
- PyTorch & PyTorch Geometric  
- NumPy & SciPy  
- Biopython  
- Fpocket  

### Frontend
- Next.js 14  
- React  
- Tailwind CSS  
- 3dmol.js  

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js v18+
- `fpocket` installed and available in PATH  

---

### 1. Backend Setup

```bash
git clone https://github.com/yourusername/SPIRE.git
cd SPIRE/backend
pip install -r requirements.txt

Create .env file:

GROQ_API_KEY=your_groq_api_key_here

Build index:

```bash
python scripts/build_index.py

Run backend:

```bash
uvicorn main:app --reload --port 8000

2. Frontend Setup

```bash
cd SPIRE/frontend
npm install
npm run dev

App runs at:

http://localhost:3000