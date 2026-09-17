# HDF5 semantic matrix

| Dataset | Meaning | Time index |
|---|---|---|
| adj_ww_used | exact snapshot passed to adjoint MC | k |
| adj_flux_g/adj_re_g | current adjoint MC batch mean and cell RE | k |
| adj_acc_flux_g/adj_acc_re_g | cumulative adjoint MC mean/RE used for training | <=k |
| ai_flux_adj_g | adjoint model prediction used to build forward WW | k |
| fwd_ww_used | exact snapshot passed to forward MC | k |
| fwd_flux_g/fwd_re_g | current forward MC batch mean and cell RE | k |
| fwd_acc_flux_g/fwd_acc_re_g | cumulative forward MC mean/RE used for training | <=k |
| ai_flux_fwd_g | forward model prediction used to build next adjoint WW | k |
| adj_ww_next | generated next-adjoint WW; absent only on final iteration | k+1 |
| fom/opt_re/real_re | current forward batch response metrics | k |
| adj_buffer_size/fwd_buffer_size | cumulative raw batch counts | <=k |
