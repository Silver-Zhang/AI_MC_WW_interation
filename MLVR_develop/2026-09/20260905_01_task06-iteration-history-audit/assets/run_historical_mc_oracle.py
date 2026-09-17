from pathlib import Path
import sys, numpy as np
ROOT=Path('/home/workspace/AI_MC_WW_interation/AIMC_WWiteration')
sys.path.insert(0,str(ROOT))
from src.mc import run_forward_mc, run_adjoint_mc
from src.learning import FluxAccumulator
from src.utils import BOX_SOURCE, BOX_OPTIM_TARGET, BOX_REAL_DETECTOR, calculate_box_response_from_batches, Mesh_NZ, Mesh_NY, Mesh_NX, N_GROUPS

def seq(kind):
    fn=run_forward_mc if kind=='forward' else run_adjoint_mc
    source=BOX_SOURCE if kind=='forward' else BOX_OPTIM_TARGET
    maps=[np.ones((N_GROUPS,Mesh_NZ,Mesh_NY,Mesh_NX)),np.ones((N_GROUPS,Mesh_NZ,Mesh_NY,Mesh_NX)),np.ones((N_GROUPS,Mesh_NZ,Mesh_NY,Mesh_NX))]
    maps[1][0,:, :, :]=0.95; maps[1][1,:, :, :]=1.05
    maps[2][:,:,:,:]=1.0
    maps[2][:, :, :, :Mesh_NX//2]=0.9
    acc=FluxAccumulator((N_GROUPS,Mesh_NZ,Mesh_NY,Mesh_NX)); allb=[]
    for k,ww in enumerate(maps,1):
        out=fn(12000,8,ww,source,iter_id=700+k)
        bg=out[4]; allb.append(bg); acc.update(bg)
    cat=np.concatenate(allb,axis=0)
    mean,re=acc.get_mean_re(); em=cat.mean(axis=0); ev=cat.var(axis=0,ddof=1); er=np.full_like(em,10.0); m=em>1e-30; er[m]=np.clip(np.sqrt(ev[m]/cat.shape[0])/em[m],0,10)
    # use group total response for forward; adjoint group 1 response
    obs=np.sum(cat,axis=1) if kind=='forward' else cat[:,1]
    r, _, samples=calculate_box_response_from_batches(obs, BOX_SOURCE if kind=='forward' else BOX_OPTIM_TARGET)
    neutral=fn(100000,50,np.ones_like(maps[0]),source,iter_id=900 if kind=='forward' else 901)
    nbg=neutral[5] if kind=='forward' else neutral[4][:,1]
    nr, _, ns=calculate_box_response_from_batches(nbg, BOX_SOURCE if kind=='forward' else BOX_OPTIM_TARGET)
    diff=(r-nr); se=np.sqrt((np.var(samples,ddof=1)/len(samples))+(np.var(ns,ddof=1)/len(ns)))
    print(f'{kind} batches={cat.shape[0]} n={acc.n} max_mean_err={np.max(np.abs(mean-em)):.3e} max_var_err={np.max(np.abs(acc.M2_g/(acc.n-1)-ev)):.3e} max_re_err={np.max(np.abs(re-er)):.3e}')
    print(f'{kind} reference={nr:.12e} accumulated={r:.12e} z={diff/se:.6f} combined_rel_SE={se/max(abs(r),1e-30):.6e}')
for k in ('forward','adjoint'): seq(k)
