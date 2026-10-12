# Stage2 P1定向修复（模式C，2026-10-12）

## 1. 目标与范围
沿用Task05，只修Task07两个P1。用户授权见user-authorization.txt。输运模型变化会使上一轮与下一轮不再对应同一算子；非法WW比值会破坏轮盘/分裂的权重范围。此次只补入口保护，不改变输运数学。

## 2. 做法与证据
修复前29文件、全源码和补丁见pre-fix-*，旧logs/Task07/冻结04哈希见protected-evidence.json。新证据只放本目录；私有源码/构建/运行位于/tmp/20261012-f11-stage2-p1。

事前判据：复用Task05物理零容差及原封闭时间字段例外；G0/普通CTest/普通回归/34个half-run/66负例重新运行。Universe新模型含非零平移与真实lattice fill，两次F逐个fresh；mutation保持Universe数量、前置拒绝，旧runState精确不变、无第二receipt/源历史。WW非法值分别在Initialize之前和首轮成功之后从public对象设置，错误必须明确命中参数guard；新增派生overflow/underflow/次序/整数转换负例。合法WW序列及实际三界继续逐事件检查。

## 3. 决策
用户已明确授权实施两个P1及回归，不需重复审批。拟只改PrepareFixedSourceRun.cpp和已批准driver.cpp；普通入口、parser、core、RNG、WW执行数学不动。保持KEEP/CLEAR/SET/REBUILD；guard均在CLEAR之前。回滚用pre-fix-source.tar.gz对照本轮correction.diff逐文件恢复本轮增量，禁止reset/checkout/clean。无法保护的随机Universe和非1/2 lattice显式拒绝。

## 4. 结论与边界
**READY FOR INDEPENDENT RE-REVIEW**。两个P1已修复且自验通过；36对fresh、123普通比较、10CTest、51新增及66原负例通过。结论、证据、边界及八项回答见[final-verification.md](final-verification.md)。Task07原始NEEDS CORRECTION保留，当前待独立最终复核。

## 5. 过程
快照脚本错误见failure-ledger.md；原始失败证据全部保留。全部编译/动态门禁通过，原证据SHA核对通过，已停止待独立复核；不提交、不进入Stage3。
