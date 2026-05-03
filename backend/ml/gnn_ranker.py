import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
import numpy as np

class PocketGNN(torch.nn.Module):
    """
    An Enterprise-Grade Graph Convolutional Network (GCN) that predicts the 
    chemical binding affinity of a protein pocket using rotation-invariant features.
    """
    def __init__(self, num_node_features=2, hidden_channels=32):
        super(PocketGNN, self).__init__()
        
        self.conv1 = GCNConv(num_node_features, hidden_channels)
        self.bn1 = torch.nn.BatchNorm1d(hidden_channels) # Normalizes data batch-to-batch
        
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.bn2 = torch.nn.BatchNorm1d(hidden_channels)
        
        self.dropout = torch.nn.Dropout(p=0.3) # Prevents neural overfitting
        self.out = torch.nn.Linear(hidden_channels, 1)

    def forward(self, x, edge_index, edge_weight):
        # Layer 1 with Edge Weights, Batch Norm, and Dropout
        x = self.conv1(x, edge_index, edge_weight)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Layer 2
        x = self.conv2(x, edge_index, edge_weight)
        x = self.bn2(x)
        x = F.relu(x)
        
        # Global Mean Pooling: Condense pocket into a single vector
        x = torch.mean(x, dim=0) 
        
        # Generate final normalized affinity score
        score = self.out(x)
        return torch.sigmoid(score)

class AIRanker:
    """
    Acts as the bridge between our VP-Tree outputs and the GNN model.
    Converts 3D numpy arrays into PyTorch Graphs with rotation-invariant features.
    """
    def __init__(self):
        self.model = PocketGNN()
        self.model.eval() # Set to evaluation/inference mode

    def _build_graph_from_coords(self, coords: np.ndarray) -> Data:
        """
        Converts an Nx3 numpy array into a PyTorch Geometric Graph.
        Extracts structural features that are immune to 3D rotation.
        """
        num_atoms = len(coords)
        if num_atoms == 0:
            return Data(x=torch.zeros((1, 2)), edge_index=torch.zeros((2, 0), dtype=torch.long))

        # Calculate the Center of Mass for the pocket
        center_of_mass = np.mean(coords, axis=0)

        edges = []
        edge_weights = []
        degrees = np.zeros(num_atoms)

        # Build Edges and calculate degrees
        for i in range(num_atoms):
            for j in range(i + 1, num_atoms):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist < 5.0: # Standard 5 Angstrom chemical cutoff
                    edges.append([i, j])
                    edges.append([j, i]) # Undirected graph
                    
                    # Closer atoms share a stronger bond weight
                    weight = 1.0 / (dist + 1e-5) 
                    edge_weights.extend([weight, weight])
                    
                    degrees[i] += 1
                    degrees[j] += 1

        # Build Rotation-Invariant Node Features
        features = []
        for i in range(num_atoms):
            dist_to_center = np.linalg.norm(coords[i] - center_of_mass)
            # Feature 1: Distance to Center | Feature 2: Node Degree (Neighbors)
            features.append([dist_to_center, degrees[i]])

        x = torch.tensor(features, dtype=torch.float)
        
        if len(edges) > 0:
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
            edge_weight_tensor = torch.tensor(edge_weights, dtype=torch.float)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_weight_tensor = torch.empty((0,), dtype=torch.float)

        return Data(x=x, edge_index=edge_index, edge_attr=edge_weight_tensor)

    def rank_pockets(self, pocket_data_list):
        """
        Ranks pockets based on the AI Binding Affinity score.
        """
        results = []
        with torch.no_grad():
            for pocket in pocket_data_list:
                graph = self._build_graph_from_coords(pocket['coords'])
                
                # Pass features, edges, AND weights to the model
                score = self.model(graph.x, graph.edge_index, graph.edge_attr).item()
                
                pocket['ai_binding_score'] = score
                pocket['graph_nodes'] = graph.num_nodes
                pocket['graph_edges'] = graph.num_edges // 2
                results.append(pocket)

        results.sort(key=lambda item: item['ai_binding_score'], reverse=True)
        return results

# ==========================================
# QUICK TEST
# ==========================================
if __name__ == "__main__":
    ranker = AIRanker()
    
    mock_pocket_1 = {
        "id": "Target_A", 
        "coords": np.random.rand(50, 3) * 10 
    }
    mock_pocket_2 = {
        "id": "Target_B", 
        "coords": np.random.rand(50, 3) * 50 
    }
    
    candidates = [mock_pocket_1, mock_pocket_2]
    
    print("Running GNN AI Judge on Candidates...")
    ranked_list = ranker.rank_pockets(candidates)
    
    for rank, p in enumerate(ranked_list):
        print(f"Rank {rank+1}: {p['id']} - AI Binding Affinity: {p['ai_binding_score']:.4f}")