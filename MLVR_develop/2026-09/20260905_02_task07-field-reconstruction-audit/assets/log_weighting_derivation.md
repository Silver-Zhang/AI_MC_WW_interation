# Log weighting
For Phi_hat=Phi+e and small relative error, delta method gives Var(log10 Phi_hat) approximately Var(Phi_hat)/(Phi^2 ln(10)^2)=RE^2/ln(10)^2. Thus inverse variance is proportional to 1/RE^2. The omitted constant is global. At large RE, Jensen bias and positivity/truncation make this only an approximation; zeros are masked as no information.
