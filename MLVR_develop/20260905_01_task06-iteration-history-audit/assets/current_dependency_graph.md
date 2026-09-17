# Actual dependency graph

W_adj[k] (snapshot) -> adjoint MC A[k] -> _adj_accumulator.update(raw batches) -> cumulative adj field -> adj training/prediction -> W_fwd[k] (snapshot) -> forward MC F[k] -> current response/FOM and best selection; F[k] also -> _fwd_accumulator.update(raw batches) -> cumulative fwd field -> forward training/prediction -> W_adj[k+1] (snapshot) -> next iteration.

Best WW is copied from the current forward WW only after current FOM is computed. It is never an input to the same iteration's forward WW except as historical best-anchor state from earlier iterations.
