# F02 机制独立审计（执行前冻结）

基线：RMC `6d2087518e0d9f23574d629f5fde361c79f519e4`，standard MGACE、fixed source、neutron adjoint、`ais=OFF`。

## 目标关系

\[
\Sigma_s^\dagger(h\to g)=\Sigma_s(g\to h),\qquad
F^\dagger(h\to g)=\chi(h)\nu_{total}(g)\Sigma_f(g).
\]

`TreatAdjointMaterial.cpp:37-59` 以正向入射群 `jg` 和出射群 `jh` 构造伴随当前群 `jh` 的产生量。`GetMgAdjNeuExitErgMu()` 再从当前伴随群选择正向前驱群。固定源裂变初始化使用 `GetMgNeuLNU()`；运行时 `SampleColliMT_FixedSrc()` 当前也使用同一 getter 逐群扣减，故标准 MGACE 双 nubar total 核在该两处一致。

## 抽样、权重和密度

飞行以局部正向宏观总截面 \(\Sigma_t^{macro}\) 抽样；核素和反应以伴随产生量选择。正确权重应使相同局部密度比例同时出现在产生量和总截面中并消去。当前 `GetExitState.cpp:187-190` 与 `SampleColliType.cpp:190-192` 使用 `GetMatAtomDen(mat,p_dDensRatio)`，与 `SampleFreeFlyDist.cpp:69-83` 的局部密度一致；W5 的旧 \(1/r\) 路径已被替换。

材料混合的核素选择由 `SampleColliNuc.cpp:25-48` 使用原子份额和各核素伴随产生量；本次若不能建立混合材料响应，则该机制仍缺数值验证。

## 方向和裂变后继

`GetMgAdjNeuExitErgMu.cpp:446-501` 先选反向群对，再抽样该群对条件余弦；`GetExitState.cpp:182-189` 以当前存储方向旋转。若存储方向是正向物理方向的反向，方位对称、仅依赖散射余弦的核在两方向同时反号后保持 \(\mu\)。这不是强 P1/P2 数值证据。

`GetFissionNeuState.cpp:550-736` 对伴随裂变固定一个加权后继，保留已选前驱群并压入 fixed-source bank。bank 可达性不等于最终响应互易性。

## 明确排除

本审计不证明 delayed precursor、continuous energy、photon、AIS/HDF5、GPT、WW 组合、F03 伴随源语义或完整 MLVR 已准备就绪。
