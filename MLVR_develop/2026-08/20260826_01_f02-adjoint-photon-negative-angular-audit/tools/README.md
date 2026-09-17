# 工具索引

| 类别 | 文件 | 用途 |
|---|---|---|
| 资产生成 | `generate_photon_mgace.py`、`generate_secondary_photon_mgace.py`、`generate_two_group_photon_mgace.py` | 生成 ordinary、secondary 的一群/两群私有 MGACE |
| 独立回读 | `verify_photon_mgace.py`、`verify_secondary_photon_mgace.py`、`verify_two_group_photon_mgace.py` | 独立检查 NXS/JXS/XSS、locator、角值与哈希 |
| 输入生成 | `generate_photon_cases.py`、`generate_secondary_photon_case.py` | 生成 ordinary 前/伴随及 secondary RMC 输入 |
| 生产观测 | `sample_mulab_gdb.py` | 在生产函数返回边界采集 `MuLab` |
| 统计验收 | `analyze_mulab_matrix.py`、`analyze_photon_pairs.py` | 一群三种子矩阵与前/伴随配对 |
| 最终验收 | `analyze_two_group_clean_validation.py` | 两群零警告整程、支持域、理论矩与配对总门禁 |

Python 缓存不归档；运行工具后可在 `MLVR_develop/` 执行 `./clean_generated.sh --apply` 清理。
