# -*- coding: utf-8 -*-
"""生成 docs/02-作物数据表.md"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crops = json.load(open(os.path.join(ROOT, 'data', 'crops.json'), encoding='utf-8'))
names = json.load(open(os.path.join(ROOT, 'data', 'stage_names.json'), encoding='utf-8'))


def dur(m):
    h = m / 60
    return ('%.1fh' % h) if h < 24 else ('%d天%dh' % (int(h // 24), int(h % 24)))


rows = []
for c in sorted(crops, key=lambda x: (x['level_required'], x['id'])):
    b = [x for x in c['growth_stages_min'] if x > 0]
    nm = names[str(c['id'])]['stageNames']
    sn = nm[1:1 + len(b)]
    stages = ' → '.join(sn)
    gaps = ' / '.join(str(b[i] - (b[i - 1] if i else 0)) for i in range(len(b)))
    rows.append([
        c['id'], c['name'], c['level_required'], c['seasons'],
        dur(c['reharvest_min']) if c['reharvest_min'] else '—',
        c['seed_price'], c['fruit_price'], c['yield_per_season'],
        c['exp_per_harvest'], dur(c['total_minutes']), stages, gaps,
    ])

md = [
    '# 23 种作物完整参数表',
    '',
    '> 全部数值来自 T5 固件 FDVER1 作物块的实锤提取，已与实机商店面板逐项核对一致。',
    '> 「生长阶段」一列是该作物在固件中的**原始名称**——每种作物各不相同（见下说明）。',
    '',
    '| ID | 作物 | 解锁等级 | 季数 | 重熟 | 种子价 | 果实售价 | 产量/季 | 经验/季 | 成熟时间 | 生长阶段（固件原名） | 各阶段间隔(分) |',
    '|---|------|----|----|----|------|------|--------|--------|---------|--------|------|',
]
for r in rows:
    md.append('| ' + ' | '.join(str(x) for x in r) + ' |')
md += [
    '',
    '## 说明',
    '',
    '**重熟**：多季作物第 2 季起重新成熟所需时间。固件里存在一条硬关系——',
    '',
    '```',
    '重熟时间 = 成熟时间 − 大叶子阶段起点',
    '```',
    '',
    '13 个带重熟参数的作物**零例外**成立。这同时解释了为什么所有作物的重熟时间都恰好是总时长的 40%~45%',
    '（= 最后两个阶段「开花+成熟」之和）。由此反推出原版机制：**多季作物收获后进度回到大叶子阶段起点，',
    '而不是回到种子**，再走一遍开花→结果→成熟。',
    '',
    '- **阶段名**：固件作物块内 +0x1D8 起每 9 字节一条 GBK 名，槽位为 [种子, 阶段1..N, 成熟, 枯萎]。',
    '  - 蘑菇：`种子 → 原基 → 菇蕾 → 幼菇 → 成熟`',
    '  - 大白菜：`种子 → 发芽 → 幼苗 → 成株 → 卷心 → 成熟`',
    '  - 桃子：顺序都不同——`种子 → 发芽 → 开花 → 小叶子 → 大叶子 → 成熟`（先花后叶）',
    '  - 小麦末段为「幼穗」',
    '- **辣椒（ID 28）** 是唯一特例：1 季作物却带重熟参数，疑似原始设计残留。',
    '- **净收益口径**：单季作物 = 单季收入 − 种子价；多季作物 = 全季收入合计 − 种子价。',
    '- 原版固件**没有**提供作物背景故事文本（已全域搜索字符串确认），故本复刻版不作虚构描述。',
]
open(os.path.join(ROOT, 'docs', '02-作物数据表.md'), 'w', encoding='utf-8').write('\n'.join(md))
print('已生成 docs/02-作物数据表.md，共 %d 种作物' % len(rows))
print(md[6])
print(md[7])
print(md[8])
