#!/usr/bin/env bash
# 建立一个任务处理档案。
# 用法: ./new_task.sh <任务短名> [关联知识库条目] [任务模式 A|B|C]
#   ./new_task.sh rmc-ww-mesh读入
#   ./new_task.sh A1_xxx修复 A1 B
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 3 ]; then
  echo "用法: $0 <任务短名> [关联知识库条目] [任务模式 A|B|C]" >&2
  exit 1
fi

SLUG="$1"
KB="${2:-无}"
MODE="${3:-B}"
case "$MODE" in
  A) MODE_LABEL='A — 受约束自动化' ;;
  B) MODE_LABEL='B — 工程协作（默认）' ;;
  C) MODE_LABEL='C — 深度物理研究与学习' ;;
  *)
    echo "任务模式必须是 A、B 或 C: $MODE" >&2
    exit 1
    ;;
esac
BASE="$(cd "$(dirname "$0")" && pwd)"
DATE="$(date +%Y%m%d)"
STAMP="$(date '+%Y-%m-%d %H:%M')"

# 按天序号：当天已有编号文件夹的最大序号 + 1（YYYYMMDD_NN_短名，NN 为两位）
shopt -s nullglob
TODAY_DIRS=("$BASE"/${DATE}_[0-9][0-9]_*)
MAX_SEQ=""
if (( ${#TODAY_DIRS[@]} > 0 )); then
  MAX_SEQ="$(printf '%s\n' "${TODAY_DIRS[@]}" | sed -E "s#.*/${DATE}_([0-9]+)_.*#\1#" | sort -n | tail -1)"
fi
SEQ="$(printf '%02d' "$(( 10#${MAX_SEQ:-0} + 1 ))")"
DIR="$BASE/${DATE}_${SEQ}_${SLUG}"

if [ -e "$DIR" ]; then
  echo "已存在: $DIR" >&2
  exit 1
fi

# 先验证主台账结构，避免失败时留下半建档目录。
python3 - "$BASE/INDEX.md" <<'PY'
import sys
path = sys.argv[1]
lines = open(path, encoding='utf-8').read().splitlines(keepends=True)
header = '| 立项日期 | 任务 | 类型 | 状态 | 关联KB | 提交 |\n'
divider = '|---|---|---|---|---|---|\n'
try:
  header_index = lines.index(header)
except ValueError:
  raise SystemExit('INDEX.md 缺少主任务台账表头，未创建任务。')
if header_index + 1 >= len(lines) or lines[header_index + 1] != divider:
  raise SystemExit('INDEX.md 主表头后缺少唯一分隔行，未创建任务。')
PY

mkdir -p "$DIR/logs"
cp "$BASE/_template/README.md" "$DIR/README.md"

python3 - "$DIR/README.md" "$SLUG" "$STAMP" "$KB" "$MODE_LABEL" <<'PY'
import sys
path, slug, stamp, kb, mode_label = sys.argv[1:6]
s = open(path, encoding='utf-8').read()
s = s.replace('# <任务短名>', '# ' + slug, 1)
s = s.replace('| 立项日期 | YYYY-MM-DD |', '| 立项日期 | %s |' % stamp.split()[0])
s = s.replace('| 状态 | 待设计 / 待决策 / 实施中 / 待验证 / 已完成 / 已关闭 |',
              '| 状态 | 待设计 |')
s = s.replace('| 任务模式 | B — 工程协作（默认）／ A — 受约束自动化 ／ C — 深度物理研究与学习 |',
              '| 任务模式 | %s |' % mode_label)
s = s.replace('| 关联知识库条目 | 例：`06_已知问题与改进建议.md` A1 ／ 无 |',
              '| 关联知识库条目 | %s |' % kb)
s = s.replace('| YYYY-MM-DD HH:MM | 立项 |', '| %s | 立项 |' % stamp)
open(path, 'w', encoding='utf-8').write(s)
PY

# 追加一行到主台账表头紧随的分隔行之后。
python3 - "$BASE/INDEX.md" "$SLUG" "${DATE}_${SEQ}_${SLUG}" "$KB" <<'PY'
import sys, datetime
path, slug, folder, kb = sys.argv[1:5]
row = '| %s | [%s](%s/README.md) |  | 待设计 | %s | |\n' % (
    datetime.date.today().isoformat(), slug, folder, kb)
lines = open(path, encoding='utf-8').read().splitlines(keepends=True)
header = '| 立项日期 | 任务 | 类型 | 状态 | 关联KB | 提交 |\n'
divider = '|---|---|---|---|---|---|\n'
try:
    header_index = lines.index(header)
except ValueError:
    raise SystemExit('INDEX.md 缺少主任务台账表头，未创建任务。')
if header_index + 1 >= len(lines) or lines[header_index + 1] != divider:
    raise SystemExit('INDEX.md 主表头后缺少唯一分隔行，未创建任务。')
lines.insert(header_index + 2, row)
open(path, 'w', encoding='utf-8').writelines(lines)
PY

echo "已建档: $DIR"
echo "任务模式: $MODE_LABEL"
echo "下一步: 把原始材料（报错/数据/日志）保存到 $DIR/logs/"
