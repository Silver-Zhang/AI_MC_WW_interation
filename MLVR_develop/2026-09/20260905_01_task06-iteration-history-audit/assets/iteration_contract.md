# Task 06 iteration contract

For iteration k, W_adj[k] is selected from history before A[k]. A[k] contributes one raw normalized batch sample per batch to H_adj[k]. The cumulative field trains the adjoint model, whose prediction generates W_fwd[k]. F[k] is then sampled with W_fwd[k] and contributes one raw batch sample per batch to H_fwd[k]. The forward cumulative field trains the forward model, whose prediction generates W_adj[k+1]. Current response/FOM uses only F[k]; cumulative fields are training/provenance data.

If W_k is measurable with respect to prior history and E[X_k | history before k] = mu, then D_k=X_k-mu is a martingale difference. Consequently E[N^-1 sum X_k]=mu even when conditional variances differ. This establishes unbiasedness, not minimum variance: equal batch weighting is not asserted optimal under heteroskedasticity.
