# 资格资产索引

这里只保留实际进入缺陷确认或最终复验的四套私有 MGACE 资产。早期 ordinary 构造 `photon_negative/`、`photon_negative_v2/` 已被 `v3` 取代，不归档；其失败/排错事实仍保存在 `../logs/qualification_history/`。

| 目录 | 用途 |
|---|---|
| `photon_negative_v3/` | ordinary photon 一群修复前后探针与三种子旧证据 |
| `secondary_photon_negative_v1/` | photon→neutron 一群修复前后探针与三种子旧证据 |
| `photon_negative_two_group_v1/` | ordinary photon 零警告整程与生产采样主证据 |
| `secondary_photon_negative_two_group_v1/` | photon→neutron 零警告整程与生产采样主证据 |

每套目录均含 manifest、xsdir 和最小 MGACE 表。四份 `electron_03e` 的 SHA256 均为 `9b50c1829efda6c8c953b48a19cd194841285a528bcdfe72d5952614e08c3fc2`；它们必须位于各自短路径下以避开 RMC 固定长度路径限制。Git 按内容寻址，只存储一个相同 blob。
