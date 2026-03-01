import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
import numpy as np
import math

class PocketGNN(torch.nn.Module):
    """
    A Graph Convolutional Network (GCN) that predicts the chemical 
    binding affinity of a protein pocket.
    """
    def __init__(self, num_node_features=3, hidden_channels=16):
        super(PocketGNN, self).__init__()
        # Layer 1: Takes raw atom features and extracts local patterns
        self.conv1 = GCNConv(num_node_features, hidden_channels)
        # Layer 2: Condenses the patterns into a final chemical signature
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        # Final Linear Layer: Outputs a single binding affinity score
        self.out = torch.nn.Linear(hidden_channels, 1)

    def forward(self, x, edge_index):
        # Pass through Layer 1 with ReLU activation
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        
        # Pass through Layer 2
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        
        # Pool all atoms together into a single "Pocket Vector"
        x = torch.mean(x, dim=0) 
        
        # Generate final score
        score = self.out(x)
        return torch.sigmoid(score) # Keeps score between 0.0 and 1.0

class AIRanker:
    """
    Acts as the bridge between our VP-Tree outputs and the GNN model.
    Converts 3D numpy arrays into PyTorch Graphs.
    """
    def __init__(self):
        # Initialize the AI Model
        self.model = PocketGNN()
        self.model.eval() # Set to evaluation/inference mode

    def _build_graph_from_coords(self, coords: np.ndarray) -> Data:
        """
        Converts an Nx3 numpy array of atoms into a PyTorch Geometric Graph.
        Creates edges between atoms that are close to each other (< 5.0 Angstroms).
        """
        num_atoms = len(coords)
        if num_atoms == 0:
            return Data(x=torch.zeros((1, 3)), edge_index=torch.zeros((2, 0), dtype=torch.long))

        # Node Features: We just use the 3D spatial coordinates as the base feature
        x = torch.tensor(coords, dtype=torch.float)

        # Build Edges: Connect atoms within 5 Angstroms of each other (Standard chemical cutoff)
        edges = []
        for i in range(num_atoms):
            for j in range(i + 1, num_atoms):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist < 5.0:
                    edges.append([i, j])
                    edges.append([j, i]) # Undirected graph

        if len(edges) > 0:
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)

        return Data(x=x, edge_index=edge_index)

    def rank_pockets(self, pocket_data_list):
        """
        Takes a list of dictionaries containing pocket coordinates,
        passes them through the GNN, and returns a sorted list based on AI score.
        """
        results = []
        with torch.no_grad(): # No training, just inference
            for pocket in pocket_data_list:
                # 1. Convert to Graph
                graph = self._build_graph_from_coords(pocket['coords'])
                
                # 2. Ask the AI for a score
                score = self.model(graph.x, graph.edge_index).item()
                
                # 3. Store result
                pocket['ai_binding_score'] = score
                results.append(pocket)

        # Sort by highest AI score first
        results.sort(key=lambda item: item['ai_binding_score'], reverse=True)
        return results

# ==========================================
# QUICK TEST
# ==========================================
if __name__ == "__main__":
    ranker = AIRanker()
    
    # Mock data representing two different pockets retrieved by the VP-Tree
    mock_pocket_1 = {
        "id": "Target_A", 
        "coords": np.random.rand(50, 3) * 10 # 50 atoms packed tightly
    }
    mock_pocket_2 = {
        "id": "Target_B", 
        "coords": np.random.rand(50, 3) * 50 # 50 atoms spread far apart
    }
    
    candidates = [mock_pocket_1, mock_pocket_2]
    
    print("Running GNN AI Judge on Candidates...")
    ranked_list = ranker.rank_pockets(candidates)
    
    for rank, p in enumerate(ranked_list):
        print(f"Rank {rank+1}: {p['id']} - AI Binding Affinity: {p['ai_binding_score']:.4f}")