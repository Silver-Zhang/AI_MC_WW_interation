# Field semantics
Current MC fields are per-history cell-integrated track-length scores Q[g,z,y,x]. On the equal-volume mesh Q=Vcell*Phi. Point inputs are cell centers (x,y,z), field tensors are (z,channel,y,x), and canonical predicted maps are (g,z,y,x). Adjoint fields are downstream response importance for forward WW; forward fields drive the reverse adjoint WW.
