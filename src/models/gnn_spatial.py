"""GNN spatial model placeholder -- receiver grid with property query nodes."""

# Stub for Day 2/3. Requires torch-geometric.
# Architecture: receiver nodes -> message passing -> query node embeddings -> damage ratio


def build_graph(receiver_df, property_df, k_neighbors: int = 5):
    raise NotImplementedError("GNN spatial model not yet implemented")


def train_gnn(graph, labels):
    raise NotImplementedError("GNN spatial model not yet implemented")
