# F11 Stage 3：输入、TARGET、伴随源与响应统计设计

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-15（Asia/Shanghai；建档脚本分配） |
| 状态 | 设计完成；Claude独立审查完成（**NEEDS REVISION**）；待修订设计及用户批准生产修改 |
| 任务类型 | 技术设计 |
| 任务模式 | C |
| 执行者 | Codex |
| 关联知识库 | 04（唯一冻结设计基线，只读）；W14（本轮静态风险登记） |
| 文档仓库基线 | main / af46e64ad46afc02c19670c6736cb917a448c854；立项前干净 |
| RMC 基线 | Neural_Network_WW_Iteration / 4810694b7a99dfc3ad7d27f7d443814f511f4829；工作树干净 |

## 1. 目标与范围

完成 MLVR 输入与 TARGET、TARGET 自动构造伴随源、正向 TARGET 响应及完整 source-history RE 的具体实施设计。交付现有类/函数调用链、数据所有权与签名、拟修改文件、最少实施顺序及必要验收门禁。

物理定式：TARGET按空间体积平均、按所选物理能群求和；同一去重TARGET用于响应及伴随构源，bin按体积抽取、群等概率、方向各向同性、实际初始权重1。RE按完整源历史的标量目标贡献统计，全部WW后代属于原history，零贡献history计入N。伴随单位人工源的尺度与绝对重要性分开。

本轮仅源码分析和设计。RMC生产/测试、冻结KB04、核数据库/reference均未修改；未编译或运行输运，未add/commit/push/切分支，未进入Stage4–6。原始授权摘录见 [logs/request-excerpt.md](logs/request-excerpt.md)。

## 2. 做法与证据

主要产物：

- [stage3-design.md](stage3-design.md)：当前HEAD源码位置、函数链、接口/所有权、输入语法、构源、响应统计、生产修改清单。
- [test-plan.md](test-plan.md)：六组必要门禁，独立代数/解析/真实段参考、预设容差、拟命令。**全部未运行**。
- [logs/baseline.json](logs/baseline.json)：仓库身份、Stage2冻结清单核验、实际阅读源码哈希及收尾保护检查。
- [Independent_F11_Stage3_Design_Review.md](Independent_F11_Stage3_Design_Review.md)：Claude独立设计审查；结论 **NEEDS REVISION**，含P1/P2问题、源码核对及明确未验证边界。

先读AGENTS/STATUS/AGENT_CONTEXT、工作流、KB04 §6/§7/§9/§14、Stage2最终实现与验收档案。源码分析在G1回复后进行，分输入、源抽样、history统计三条链并行只读核对，由主Agent合并并复查关键风险。

```text
root before task: main af46e64ad46afc02c19670c6736cb917a448c854; clean
RMC: Neural_Network_WW_Iteration 4810694b7a99dfc3ad7d27f7d443814f511f4829; clean
upstream ahead/behind (local refs): root 0/0, RMC 0/0
Stage2 final-freeze commit-manifest.json: all 29 source hashes match
KB04 SHA256: aeed2760f84427bdd8d139182d7bb3f4193c0c63f67decec1d42c7aad7a676b0
```

Stage2结论与受限范围沿用 [Task05 §4](../20261011_05_f11-prepared-run-lifecycle/README.md#4-结论与边界)。Stage0体积合同沿用 [Task02 §4](../20261011_02_f11-field-volume-normalization/README.md#4-结论与边界) 和 [独立报告](../20261011_03_independent-f11-field-volume-review/Independent_F11_Field_Volume_Review.md)，不能将旧有限实验视为新接口已经验证。

设计自查修正：几何包含裕量必须覆盖实际`GetZeroSenseDistance()`而非只用机器精度，并纳入binding身份；输入缺项/其它计算模式显式冲突也要在统一检查拒绝；CDF逐元素校验，不能仅看单调和尾项1。上述修正已写入方案，未扩大生产修改清单。

生产修改快照：无（没有生产补丁）。文档检查限于格式、路径、状态一致性及源码身份；不以文档自查替代Claude独立审查或物理验收。收尾真实输出：`git diff --check`退出0；计划生产/构建清单21项且无重复；任务Markdown链接/空白错误`[]`；`tools/check-archives.sh`退出0、本任务无提示；RMC仍clean、HEAD及29文件SHA256一致、KB04哈希不变。

## 3. 决策记录

用户原话（2026-10-15）：**“确认按此继续，后续直接帮我确认即可”**。

- **G1**：已确认上述物理定式，答复原文如上。
- **后续对话裁量**：按用户授权跳过本轮逐项细问；以下是Agent技术判断，**不是代填用户逐项批准**。
- **G2 因果链（Agent判断）**：Stage2仅点源的验证与单能检查需受控扩展；复用source组件/分布及现有循环；在完整history临时score清零前聚合保持跨bin/群相关性。方案§2–7给出实际位置与因果链。
- **G3 验伪设计（Agent判断）**：抽样概率、源尺度、完整体积/群映射、解析R、独立history矩、真实段积分、角色切换及原回归任一不符即推翻对应实现；不能靠改reference或扩大容差放行，见test-plan。
- **G4 边界说明**：本轮仅静态设计，没有运行结果可作物理解释；不声称新接口通过验收。实施后的结果解释仍须在后续任务实际证据下完成。
- **生产修改审批与Claude审查**：独立审查已完成，报告见[审查正文](Independent_F11_Stage3_Design_Review.md)，结论为NEEDS REVISION；设计修订及生产修改审批仍待完成。本轮归档授权不包括代码实施。

| 风险 / 因果链 | 拟改动范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 体积/群/尺度错误或按后代平方使R/RE错误；新源还可能触发旧MG速度索引风险 | 当前仅设计及进度/风险指针；拟实现21个生产/构建文件见方案§8；普通scorer/reference不改 | 先独立设计审查及生产审批，实施分3步、六组门禁；失败不得继续宣称Ready | 当前只有文档增量；实施后保存完整tracked及新增文件补丁，保留用户修改，不reset |

## 4. 结论与边界

**设计结论：NEEDS REVISION（Claude独立审查）；Stage 3 设计尚待修订及用户批准生产修改。**

独立审查见[报告](Independent_F11_Stage3_Design_Review.md)。当前阻塞为：

1. **P1 — MPI TARGET响应归约合同缺失**：`S1/S2/N`无全局归约语义，亦未具体规定生产入口在状态变更前拒绝MPI。
2. **P1 — T4独立raw segment/history oracle不可复现**：测试要求真实段记录与history/后代关联，但设计文件清单没有observer/trace，且prepared profile拒绝PTRAC。
3. **P2 — type-4 bin sampler门禁**：实施前须以真实生产sampler核对区间端点、支持域和均匀性。

串行history边界的源码时序支持在`SumTallyBin`清理前聚合完整history，并显式计入零得分历史；这只是现有源码时序的静态判断，不是新实现验证。无P0。

本次审查未修改RMC、测试、冻结KB04、核数据库或reference；未构建、未运行CTest或输运；Stage 3 实施仍未授权，不能因完成审查归档而启动。

1. **修改已有类**：CDInput解析与来源检查，CDCalMode配置/一次绑定/单run入口，CDExternalSource/CDSource受控工厂，CDTally独立scalar统计；20个生产源码/头文件（含4个新增）加1个根CMake文件，见方案§8。
2. **TARGET→源**：每个空间bin一个XYZ均匀组件，共用离散群中心谱，各向同性；fraction/bias一致，沿用逐history单位权重及N=D=W0审计。F/A canonical独立，继续深值工作副本。
3. **响应与RE**：Field/TARGET共享Stage0 ci；在唯一完整history边界形成rh再累计S1/S2/N，不拼bin RE，不重复Tot槽，不改原统计器。
4. **Stage2兼容**：未绑定TARGET继续原严格点源、原RNG/模型/WW/失败状态及唯一循环；新generated源单独白名单，最高群和MG速度仅在新Stage3绑定入口适配（包括F固定源的正确群中心速度），普通及未绑定TARGET的Stage2保持。普通固定源源拷贝语义保持。
5. **必要限制**：首版Forward仍是受限点源；TARGET完整box须能按方案§5证明处于有效根层轴向域，无法证明的复杂CSG/跨cell/边界近邻明确拒绝。此限制及两处源适配须在实施审批中显式接受。
6. **验收与尚未验证**：三个实施子步骤、六组门禁已具体化，全部未运行；绝对伴随重要性/完整输运互易性未被新测试声称证明，单位人工源尺度单独核验；MPI/OMP/AIS/Python、任意源、非零裂变仍未开放。

本轮静态确认一个需记录的源能量坐标风险（W14）：物理MeV阶段调用按群号取速度的函数，低中心能量可产生越界索引。尚未动态复现或修复；方案仅拟为新Stage3-bound F/A作必要适配，固定能量F按映射群中心取速度，普通路径全面修复不在本任务范围。最高群下界误作上界是Stage2限制扩展必须处理的另一处兼容点。源码与物理原因见方案§6。

已同步STATUS/INDEX/上下文、已知风险及物理说明指针；历史Stage2/Stage0审查原文与冻结04保持。源码身份匹配不代表Stage3实现完成。完成设计后停止，等待用户与Claude审核，不启动Stage4。

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-10-15 13:40 | `TZ=Asia/Shanghai bash MLVR_develop/new_task.sh f11-stage3-target-source-response-design 04 C`自动分配本目录 |
| 2026-10-15 | 两仓库与29文件身份核验，立项后停在G1 |
| 2026-10-15 | 收到G1原文回复，按授权跳过后续逐项细问，继续只读分析 |
| 2026-10-15 | 输入/源/统计三链实际源码追踪；统一具体设计与测试；交叉自查修正几何sense裕量、CDF和输入缺项，并明确Stage3-bound F/A分别使用正确群中心速度 |
| 2026-10-15 | 设计交付、同步状态及风险指针；无生产修改/测试/提交，等待独立审查与实施批准 |
| 2026-10-15 | Claude对照冻结RMC源码独立审查设计与验收计划；判定NEEDS REVISION（MPI scalar归约、T4 raw-segment oracle两项P1；bin sampler micro-oracle一项P2）；仅静态审查，未运行构建/输运；审查归档，实施仍未授权 |
