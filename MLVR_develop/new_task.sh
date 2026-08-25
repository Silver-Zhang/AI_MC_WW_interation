#!/usr/bin/env bash
# 建立一个任务处理档案。
# 用法: ./new_task.sh <任务短名> [关联知识库条目]
#   ./new_task.sh rmc-ww-mesh读入
#   ./new_task.sh A1_xxx修复 A1
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: $0 <任务短名> [关联知识库条目]" >&2
  exit 1
fi

SLUG="$1"
KB="${2:-无}"
BASE="$(cd "$(dirname "$0")" && pwd)"
DATE="$(date +%Y%m%d)"
STAMP="$(date '+%Y-%m-%d %H:%M')"

# 按天序号：当天已有编号文件夹的最大序号 + 1（YYYYMMDD_NN_短名，NN 为两位）
MAX_SEQ="$(ls -d "$BASE"/${DATE}_[0-9][0-9]_* 2>/dev/null | sed -E "s#.*/${DATE}_([0-9]+)_.*#\1#" | sort -n | tail -1)"
SEQ="$(printf '%02d' "$(( 10#${MAX_SEQ:-0} + 1 ))")"
DIR="$BASE/${DATE}_${SEQ}_${SLUG}"

if [ -e "$DIR" ]; then
  echo "已存在: $DIR" >&2
  exit 1
fi

mkdir -p "$DIR/logs"
cp "$BASE/_template/README.md" "$DIR/README.md"

python3 - "$DIR/README.md" "$SLUG" "$STAMP" "$KB" <<'PY'
import sys
path, slug, stamp, kb = sys.argv[1:5]
s = open(path, encoding='utf-8').read()
s = s.replace('# <任务短名>', '# ' + slug, 1)
s = s.replace('| 立项日期 | YYYY-MM-DD |', '| 立项日期 | %s |' % stamp.split()[0])
s = s.replace('| 状态 | 待设计 / 待决策 / 实施中 / 待验证 / 已完成 / 已关闭 |',
              '| 状态 | 待设计 |')
s = s.replace('| 关联知识库条目 | 例：`06_已知问题与改进建议.md` A1 ／ 无 |',
              '| 关联知识库条目 | %s |' % kb)
s = s.replace('| YYYY-MM-DD HH:MM | 立项 |', '| %s | 立项 |' % stamp)
open(path, 'w', encoding='utf-8').write(s)
PY

# 追加一行到台账的"进行中"表格（定位到表头分隔行之后）
python3 - "$BASE/INDEX.md" "$SLUG" "${DATE}_${SEQ}_${SLUG}" "$KB" <<'PY'
import sys, datetime
path, slug, folder, kb = sys.argv[1:5]
row = '| %s | [%s](%s/README.md) |  | 待设计 | %s | |\n' % (
    datetime.date.today().isoformat(), slug, folder, kb)
lines = open(path, encoding='utf-8').read().splitlines(keepends=True)
for i, l in enumerate(lines):
    if l.startswith('|---|---|---|---|---|---|'):
        lines.insert(i + 1, row)
        break
else:
    lines.append(row)
open(path, 'w', encoding='utf-8').writelines(lines)
PY

echo "已建档: $DIR"
echo "下一步: 把原始材料（报错/数据/日志）保存到 $DIR/logs/"
