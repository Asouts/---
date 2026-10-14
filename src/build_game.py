# -*- coding: utf-8 -*-
"""从 assets/ + data/ 生成单文件游戏《点点农场_复刻版.html》

用法:  python src/build_game.py
产物:  点点农场_复刻版.html  (单文件、离线、双击即玩)

素材全部内嵌为 base64，因此产物不依赖任何外部文件。
阶段名来自 data/stage_names.json（已从固件导出，无需 592MB 的 T5AppRes.dat）。
"""
import json, base64, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 仓库根目录
USE = os.path.join(ROOT, 'assets')

def b64(path):
    return "data:image/png;base64," + base64.b64encode(open(path, 'rb').read()).decode()

# ===== 素材（严格按 assets/ 清单）=====
assets = {}
assets['bg'] = b64(os.path.join(USE, 'BG', 'BG_2_800x480.png'))
assets['land_brown'] = b64(os.path.join(USE, '地块', '地块_耕地01.png'))    # 褐色可种
assets['land_yellow'] = b64(os.path.join(USE, '地块', '地块_耕地21.png'))   # 浅黄无裂纹=播种高亮
for i in range(1, 16):
    assets[f'land_green{i:02d}'] = b64(os.path.join(USE, '地块', f'地块_荒地{i:02d}.png'))
assets['deco_house'] = b64(os.path.join(USE, '装饰品', 'BHouse_2.png'))     # 双层大木屋(蓝图同款)
assets['deco_doghouse'] = b64(os.path.join(USE, '装饰品', 'DHouse_1.png'))
assets['deco_fence'] = b64(os.path.join(USE, '装饰品', 'Fence_1.png'))
assets['deco_dog'] = b64(os.path.join(USE, '装饰品', 'Dog_1.png'))
for key, fn in [('ui_shovel','UI_铲子'), ('ui_water','浇水'), ('ui_seedbag','种子包'),
                ('ui_fert','施肥'), ('ui_glove','收获'), ('ui_warehouse','UI_仓库'),
                ('ui_shop','商城'), ('ui_close','UI_关闭'), ('ui_level','UI_等级徽章'),
                ('ui_sign','扩建木牌')]:
    assets[key] = b64(os.path.join(USE, 'UI', fn + '.png'))

# ===== 作物数据 =====
raw = json.load(open(os.path.join(ROOT, 'data', 'crops.json'), encoding='utf-8'))
STAGE_NAMES = ['发芽', '小叶子', '大叶子', '开花', '成熟']

# ===== 每作物独有的阶段名（固件作物块 @+0x1D8 命名表，已导出到 data/stage_names.json）=====
# 表内容 = [种子, 阶段1..阶段N, 成熟, 枯萎]，各作物不同：蘑菇=原基/菇蕾/幼菇，大白菜=幼苗/成株/卷心…
_STAGE_JSON = json.load(open(os.path.join(ROOT, 'data', 'stage_names.json'), encoding='utf-8'))
def crop_stage_names(c):
    return _STAGE_JSON[str(c['id'])]['stageNames']

def crop_frame_path(c, fi):
    for cand in [os.path.join(USE, '作物全帧', f"{c['name']}_{fi+1:02d}.png"), os.path.join(USE, '作物全帧', f"{c['pinyin']}_{fi+1:02d}.png")]:
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"找不到 {c['name']} 第{fi+1}帧")

def crop_icon_path(c):
    for cand in [os.path.join(USE, '作物', f"{c['name']}_果实图标.png"), os.path.join(USE, '作物', f"{c['pinyin']}_果实图标.png")]:
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"找不到 {c['name']} 果实图标")

crops = []
for c in raw:
    n = len(c['frame_sizes'])
    b = [x for x in c['growth_stages_min'] if x > 0]
    # 用固件里该作物自己的阶段名（names[0]=种子，names[1..N]=各阶段，末位=枯萎）
    nm = crop_stage_names(c)
    sn = nm[1:1 + len(b)]
    assert len(sn) == len(b) and sn[-1] == '成熟', f"{c['name']} 阶段名异常: {nm} vs {b}"
    stages = [[sn[i], b[i]] for i in range(len(b))]
    seedName = nm[0]
    witherName = nm[-1]
    assert len(stages) == n - 3, f"{c['name']} 阶段数≠帧数-3"
    for fi in range(n):
        assets[f"crop_{c['id']}_f{fi}"] = b64(crop_frame_path(c, fi))
    assets[f"icon_{c['id']}"] = b64(crop_icon_path(c))
    crops.append({
        "id": c['id'], "name": c['name'], "level": c['level_required'],
        "seasons": c['seasons'], "reharvest": c['reharvest_min'],
        "seedPrice": c['seed_price'], "fruitPrice": c['fruit_price'],
        "yield": c['yield_per_season'], "exp": c['exp_per_harvest'],
        "total": c['total_minutes'], "stages": stages, "nFrames": n,
        "seedName": seedName, "witherName": witherName,
    })
crops.sort(key=lambda x: (x['level'], x['id']))
print(f"作物 {len(crops)} 种, 素材 {len(assets)} 个")

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>点点农场 · 复刻版</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #46525e; font-family: "Microsoft YaHei", sans-serif; height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  #wrap { position: relative; width: 800px; height: 480px; box-shadow: 0 8px 40px rgba(0,0,0,.5); transform: scale(2); transform-origin: center center; }
  #scene { position: absolute; left: 0; top: 0; width: 800px; height: 480px; }
  #scene.tool-on { cursor: none; }
  .ov { position: absolute; z-index: 20; }
  /* ---- 左上状态(纯数字) ---- */
  #status { left: 8px; top: 6px; display: flex; align-items: center; gap: 6px; }
  #status .chip { background: rgba(255,255,255,.85); border: 1px solid #9fb4c8; border-radius: 14px; padding: 3px 10px; display: flex; align-items: center; gap: 5px; font-size: 13px; color: #233; }
  #status img.lv { height: 20px; }
  #status b { color: #145a8a; }
  /* ---- 右上区 ---- */
  #topright { right: 8px; top: 6px; display: flex; align-items: center; gap: 5px; }
  #topright .chip { background: rgba(255,255,255,.85); border: 1px solid #9fb4c8; border-radius: 12px; padding: 3px 9px; font-size: 12px; color: #233; }
  .tbtn { height: 32px; border: 1px solid #9fb4c8; border-radius: 8px; background: rgba(255,255,255,.88); cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 2px 6px; gap: 3px; }
  .tbtn:hover { background: #fff; border-color: #2196f3; }
  .tbtn img { max-height: 24px; max-width: 26px; }
  .tbtn.mini { font-size: 12px; font-weight: 700; color: #145a8a; padding: 0 8px; }
  .tbtn.wide { font-size: 12.5px; font-weight: 700; color: #5d4300; background: #ffe9a8; border-color: #d9a92c; }
  .tbtn.wide:hover { background: #fff3c4; }
  /* ---- 左侧工具栏 ---- */
  #toolbar { left: 4px; top: 150px; display: flex; flex-direction: column; gap: 7px; }
  .tool { width: 50px; height: 50px; border: 2px solid rgba(255,255,255,.75); border-radius: 12px; background: rgba(255,255,255,.55); cursor: pointer; position: relative; display: flex; align-items: center; justify-content: center; }
  .tool:hover { background: rgba(255,255,255,.9); }
  .tool.on { border-color: #ffb300; background: #fff3c4; box-shadow: 0 0 10px rgba(255,179,0,.85); }
  .tool img { width: 40px; height: 40px; object-fit: contain; pointer-events: none; }
  .tool .badge { position: absolute; right: -5px; bottom: -5px; background: #e53935; color: #fff; font-size: 10.5px; font-weight: 700; border-radius: 9px; padding: 0 5px; min-width: 16px; text-align: center; border: 1.5px solid #fff; }
  /* ---- 右下恢复指针 ---- */
  #restore { right: 10px; bottom: 10px; width: 46px; height: 46px; border-radius: 10px; border: 2px solid rgba(255,255,255,.8); background: rgba(255,255,255,.6); cursor: pointer; display: flex; align-items: center; justify-content: center; }
  #restore:hover { background: #fff; border-color: #2196f3; }
  /* ---- 光标 ---- */
  #cursor { position: fixed; display: none; pointer-events: none; z-index: 999; width: 68px; height: 68px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(0,0,0,.4)); }
  /* ---- 提示框 ---- */
  #tip { position: absolute; display: none; background: rgba(255,255,255,.88); border: 1px solid #7a8fa5; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #111; line-height: 1.55; pointer-events: none; z-index: 30; white-space: nowrap; }
  #tip b { font-size: 12.5px; }
  /* ---- toast ---- */
  #toast { position: absolute; left: 50%; top: 46px; transform: translateX(-50%); background: rgba(30,40,50,.88); color: #fff; font-size: 13px; padding: 6px 16px; border-radius: 16px; display: none; z-index: 60; }
  /* ---- 浮动文字 ---- */
  .float { position: absolute; font-size: 13px; font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,.6); pointer-events: none; z-index: 40; animation: fup 1s ease-out forwards; }
  @keyframes fup { from { opacity: 1; transform: translateY(0); } to { opacity: 0; transform: translateY(-28px); } }
  /* ---- 面板 ---- */
  .panel { position: absolute; background: #fbfdff; border: 2px solid #4a7a9a; border-radius: 12px; box-shadow: 0 6px 28px rgba(0,0,0,.4); z-index: 50; display: none; }
  .panel h3 { background: #4a7a9a; color: #fff; font-size: 14px; padding: 5px 12px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; }
  .panel h3 .ximg { height: 18px; cursor: pointer; }
  .pbody { padding: 10px; }
  /* 种子包 */
  #seedPanel { left: 60px; top: 120px; width: 310px; }
  .seedgrid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .seedcell { border: 1px solid #ccd8e2; border-radius: 8px; background: #fff; text-align: center; padding: 4px 2px; cursor: pointer; }
  .seedcell:hover { border-color: #ffb300; background: #fffbe8; }
  .seedcell img { width: 34px; height: 34px; object-fit: contain; }
  .seedcell .nm { font-size: 11px; color: #444; }
  .seedcell .qt { font-size: 10px; color: #e53935; font-weight: 700; }
  /* 仓库 */
  #whPanel { left: 50%; top: 60px; transform: translateX(-50%); width: 430px; }
  .whgrid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
  .fruitcell { border: 1px solid #ccd8e2; border-radius: 8px; background: #fff; text-align: center; padding: 5px 2px; cursor: pointer; }
  .fruitcell:hover { border-color: #ffb300; background: #fffbe8; }
  .fruitcell img { width: 42px; height: 42px; object-fit: contain; }
  .fruitcell .nm { font-size: 11px; color: #444; }
  .fruitcell .qt { font-size: 11px; color: #e53935; font-weight: 700; }
  /* 商城 */
  #shopPanel { left: 50%; top: 40px; transform: translateX(-50%); width: 470px; }
  .shoplist { max-height: 300px; overflow-y: auto; }
  .shoprow { display: flex; align-items: center; gap: 6px; padding: 5px 6px; border-bottom: 1px solid #e4ebf2; }
  .shoprow img.ic { width: 30px; height: 30px; object-fit: contain; }
  .shoprow .nm { width: 52px; font-size: 13px; color: #333; }
  .shoprow .lv { width: 78px; font-size: 12px; color: #777; }
  .shoprow .pr { width: 66px; font-size: 12px; color: #b26a00; font-weight: 700; }
  .shoprow .det { font-size: 12px; padding: 3px 9px; border: 1px solid #9fb4c8; border-radius: 6px; background: #f2f7fb; color: #145a8a; cursor: pointer; font-weight: 700; }
  .shoprow .det:hover { background: #dceaf5; border-color: #2196f3; }
  .shoprow .buy { margin-left: auto; font-size: 12px; padding: 3px 12px; border: none; border-radius: 6px; background: #2e8ac2; color: #fff; cursor: pointer; font-weight: 700; }
  .shoprow .buy:hover { background: #20719f; }
  .shoprow.lock { opacity: .55; }
  .shoprow.lock .buy { background: #aaa; cursor: not-allowed; }
  /* ---- 作物详情(原版商店字段) ---- */
  #cropPanel { left: 50%; top: 22px; transform: translateX(-50%); width: 486px; z-index: 70; }
  .crophead { display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #e4ebf2; padding-bottom: 7px; margin-bottom: 7px; }
  .crophead img { width: 50px; height: 50px; object-fit: contain; }
  .crophead .tt { font-size: 17px; font-weight: 700; color: #145a8a; }
  .crophead .sub { font-size: 11px; color: #7d8b98; margin-top: 3px; }
  .infogrid { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 12px; font-size: 12.5px; color: #333; }
  .infogrid > div { display: flex; justify-content: space-between; border-bottom: 1px dotted #dde5ec; padding: 2px 0; }
  .infogrid .k { color: #5a6b7a; }
  .infogrid .v { font-weight: 700; color: #1c3d55; }
  .stagestr { display: flex; gap: 4px; margin-top: 6px; }
  .stagecard { flex: 1; text-align: center; border: 1px solid #dbe4ec; border-radius: 6px; background: #f7fbfe; padding: 3px 1px; }
  .stagecard img { height: 40px; max-width: 100%; object-fit: contain; display: block; margin: 0 auto; }
  .stagecard .sn { font-size: 10.5px; color: #444; margin-top: 2px; }
  .stagecard .st { font-size: 10.5px; color: #d32f2f; font-weight: 700; }
  .stagecard .sc { font-size: 10px; color: #8895a2; }
  .cropnote { font-size: 10.5px; color: #8a97a3; margin-top: 7px; line-height: 1.55; }
  /* 售卖 */
  #sellPanel { left: 50%; top: 120px; transform: translateX(-50%); width: 300px; }
  .sellrow { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 8px 0; }
  .qtybtn { width: 30px; height: 30px; border: 1px solid #bbb; border-radius: 6px; background: #fff; font-size: 16px; font-weight: 700; cursor: pointer; }
  .qtybtn:hover { background: #eee; }
  .numin { width: 58px; height: 30px; text-align: center; font-size: 15px; border: 1px solid #bbb; border-radius: 6px; }
  .okbtn { border: none; border-radius: 8px; padding: 7px 20px; font-size: 14px; font-weight: 700; cursor: pointer; background: #2e8ac2; color: #fff; }
  .okbtn:hover { background: #20719f; }
  .cancelbtn { border: none; border-radius: 8px; padding: 7px 20px; font-size: 14px; cursor: pointer; background: #ddd; color: #555; }
  /* 对话框 */
  #dlg { left: 50%; top: 180px; transform: translateX(-50%); width: 330px; }
  #dlg .pbody { font-size: 14px; color: #333; line-height: 1.8; }
  .warn { color: #d32f2f; font-size: 12.5px; font-weight: 700; }
  /* ---- 控制台 ---- */
  #consolePanel { left: 50%; top: 70px; transform: translateX(-50%); width: 420px; }
  .crow { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; font-size: 13px; color: #333; }
  .crow > span:first-child { width: 34px; font-weight: 700; }
  .crow input, .crow select { height: 27px; border: 1px solid #bbb; border-radius: 5px; padding: 0 6px; font-size: 13px; }
  .crow input { width: 74px; }
  .crow button { height: 27px; padding: 0 10px; border: 1px solid #9fb4c8; border-radius: 5px; background: #f2f7fb; cursor: pointer; font-size: 12px; color: #145a8a; font-weight: 700; }
  .crow button:hover { background: #dceaf5; }
  .cnote { font-size: 11.5px; color: #789; margin-top: 6px; line-height: 1.5; }
</style>
</head>
<body>
<div id="wrap">
  <canvas id="scene" width="800" height="480"></canvas>

  <!-- 左上: 等级/经验/点币(纯数字) -->
  <div id="status" class="ov">
    <div class="chip"><img class="lv" id="lvIcon"><span id="lvText">Lv.1</span></div>
    <div class="chip">经验 <b id="expText">0/200</b></div>
    <div class="chip">点币 <b id="goldText">500</b></div>
  </div>

  <!-- 右上: 时间/速度/控制台/仓库/商城 -->
  <div id="topright" class="ov">
    <div class="chip" id="timeText">第1天 08:00</div>
    <button class="tbtn mini" id="speedBtn" title="切换时间流速">×300</button>
    <button class="tbtn mini" id="pauseBtn" title="暂停/继续">⏸</button>
    <button class="tbtn wide" id="consoleBtn">控制台</button>
    <button class="tbtn" id="whBtn" title="仓库"><img id="whIcon"></button>
    <button class="tbtn" id="shopBtn" title="商城"><img id="shopIcon"></button>
  </div>

  <!-- 左侧工具栏 -->
  <div id="toolbar" class="ov">
    <div class="tool" id="tShovel" title="铲除"><img id="iShovel"></div>
    <div class="tool" id="tWater" title="浇水"><img id="iWater"><span class="badge" id="bWater">30</span></div>
    <div class="tool" id="tSeed" title="种子包"><img id="iSeed"><span class="badge" id="bSeed">7</span></div>
    <div class="tool" id="tFert" title="施肥"><img id="iFert"><span class="badge" id="bFert">10</span></div>
    <div class="tool" id="tHarvest" title="收获"><img id="iHarvest"></div>
  </div>

  <!-- 右下: 恢复指针 -->
  <div id="restore" class="ov" title="恢复鼠标指针">
    <svg width="26" height="26" viewBox="0 0 24 24"><path d="M5 3l14 8-6 1.5L10 19z" fill="#fff" stroke="#234" stroke-width="1.4" stroke-linejoin="round"/></svg>
  </div>

  <div id="tip" class="ov"></div>
  <div id="toast" class="ov"></div>

  <!-- 种子包面板 -->
  <div class="panel" id="seedPanel"><h3>种子包 <img class="ximg" data-close="seedPanel"></h3><div class="pbody"><div class="seedgrid" id="seedGrid"></div><div class="cnote">点击种子后，移动到褐色土地再次点击即可播种（右下角按钮恢复指针）</div></div></div>
  <!-- 仓库面板 -->
  <div class="panel" id="whPanel"><h3>仓库 <img class="ximg" data-close="whPanel"></h3><div class="pbody" id="whBody"></div></div>
  <!-- 商城面板 -->
  <div class="panel" id="shopPanel"><h3>种子商城 <img class="ximg" data-close="shopPanel"></h3><div class="pbody"><div class="shoplist" id="shopList"></div></div></div>
  <!-- 作物详情 -->
  <div class="panel" id="cropPanel"><h3>作物详情 <img class="ximg" data-close="cropPanel"></h3><div class="pbody" id="cropBody"></div></div>
  <!-- 售卖面板 -->
  <div class="panel" id="sellPanel"><h3>出售果实 <img class="ximg" data-close="sellPanel"></h3><div class="pbody" id="sellBody"></div></div>
  <!-- 对话框 -->
  <div class="panel" id="dlg"><h3 id="dlgTitle">提示 <img class="ximg" data-close="dlg"></h3><div class="pbody" id="dlgBody"></div></div>
  <!-- 控制台 -->
  <div class="panel" id="consolePanel"><h3>控制台 <img class="ximg" data-close="consolePanel"></h3><div class="pbody">
    <div class="crow"><span>点币</span><input id="cGold" type="number"><button id="cGoldSet">设为</button><button id="cGoldAdd">+1000</button><button id="cGoldMax">+99999</button></div>
    <div class="crow"><span>等级</span><input id="cLevel" type="number"><button id="cLevelSet">设为</button><span style="margin-left:14px">经验</span><input id="cExp" type="number"><button id="cExpSet">设为</button></div>
    <div class="crow"><span>水</span><button id="cWater30">+30</button><button id="cWater300">+300</button><span style="margin-left:14px">化肥</span><button id="cFert10">+10</button><button id="cFert100">+100</button></div>
    <div class="crow"><span>种子</span><select id="cSeedCrop"></select><input id="cSeedQty" type="number" value="10"><button id="cSeedGive">给予</button></div>
    <div class="crow"><span>果实</span><select id="cFruitCrop"></select><input id="cFruitQty" type="number" value="10"><button id="cFruitGive">给予</button></div>
    <div class="crow"><span>存档</span><button id="cSaveNow">立即保存</button><button id="cResetSave">重置存档</button><span id="saveTip" style="margin-left:4px;font-size:11px;color:#789"></span></div>
    <div class="cnote">直接改数值立即生效；果实直接进仓库；种子进种子包。<br>游戏每 3 秒自动存档，关页面也会保存；下次打开自动恢复。</div>
  </div></div>
</div>
<img id="cursor">

<script>
const ASSETS = __ASSETS__;
const CROPS = __CROPS__;
const CROP_BY_ID = {};
CROPS.forEach(c => CROP_BY_ID[c.id] = c);

// ---- 预加载 ----
const IMG = {};
for (const k in ASSETS) { const im = new Image(); im.src = ASSETS[k]; IMG[k] = im; }
function setIcon(id, key) { document.getElementById(id).src = ASSETS[key]; }
setIcon('lvIcon','ui_level'); setIcon('whIcon','ui_warehouse'); setIcon('shopIcon','ui_shop');
setIcon('iShovel','ui_shovel'); setIcon('iWater','ui_water'); setIcon('iSeed','ui_seedbag'); setIcon('iFert','ui_fert'); setIcon('iHarvest','ui_glove');
document.querySelectorAll('.ximg').forEach(x => x.src = ASSETS['ui_close']);

// ---- 常量 ----
const VW = 800, VH = 480;
const S = 1.03;                       // 全局缩放(贴合 BG_2 草地浅黄空地，四角误差≤6px)
const TW = 152 * S, TH = 80 * S;      // 156.6 x 82.4
// === 等距(菱形)错位排布：地块为菱形，沿菱形的边错开半格即可无缝拼接成整片农田 ===
// BG_2 浅黄空地四角实测：顶(293,144) 右(684,330) 底(450,452) 左(60,258)
const STEP_X = TW / 2;                // 沿一条斜线方向(右下)
const STEP_Y = TH / 2 * 0.92;         // 斜线之间的垂直错开
const TX0 = 59, TY0 = 219;            // 阵列对准空地中心 (372,296)

// ---- 游戏状态 ----
const game = {
  level: 1, exp: 0, gold: 500,
  day: 1, timeMin: 480,
  speedIdx: 2, paused: false,
  water: 30, fert: 10,
  seeds: {1: 5, 7: 2},
  warehouse: {},
  tool: null, seedCrop: null,
  tiles: [], signTile: 7, expansions: 0,
};
for (let i = 0; i < 15; i++) {
  game.tiles.push({ state: (i===0||i===5||i===10) ? 'brown' : 'green', crop: null });
}
const greenVar = {};
{ let n = 0; for (let i = 0; i < 15; i++) if (game.tiles[i].state === 'green') greenVar[i] = ++n; }

// ---- 存档系统（localStorage：自动保存 / 打开恢复） ----
const SAVE_KEY = 'dianfarm_save_v1';
let saveOK = true, lastSaveTs = 0, loadedTs = 0, lastSavedAt = 0;
function snapshot() {
  return {
    v: 1, ts: Date.now(),
    level: game.level, exp: game.exp, gold: game.gold,
    day: game.day, timeMin: game.timeMin, speedIdx: game.speedIdx,
    water: game.water, fert: game.fert,
    seeds: game.seeds, warehouse: game.warehouse,
    tiles: game.tiles.map(t => ({ state: t.state, crop: t.crop ? { id: t.crop.id, season: t.crop.season, growth: t.crop.growth, withered: t.crop.withered } : null })),
    signTile: game.signTile, expansions: game.expansions,
  };
}
function saveGame() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(snapshot())); saveOK = true; lastSavedAt = Date.now(); return true; }
  catch (e) { saveOK = false; return false; }
}
function clockStr(ms) { const d = new Date(ms); return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
function maybeSave(force) {
  const now = Date.now();
  if (!force && now - lastSaveTs < 3000) return;
  if (saveGame()) { lastSaveTs = now; const el = $('saveTip'); if (el) el.textContent = '已保存 ' + clockStr(lastSavedAt); }
}
function loadGame() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return 0;
    const s = JSON.parse(raw);
    if (!s || s.v !== 1 || !Array.isArray(s.tiles) || s.tiles.length !== 15) return 0;
    game.level = s.level; game.exp = s.exp; game.gold = s.gold;
    game.day = s.day; game.timeMin = s.timeMin; game.speedIdx = (s.speedIdx >= 0 && s.speedIdx < 4) ? s.speedIdx : 2;
    game.water = s.water; game.fert = s.fert;
    game.seeds = s.seeds || {}; game.warehouse = s.warehouse || {};
    game.signTile = s.signTile; game.expansions = s.expansions || 0;
    for (let i = 0; i < 15; i++) {
      const t = s.tiles[i];
      game.tiles[i].state = t.state;
      game.tiles[i].crop = t.crop ? { id: t.crop.id, season: t.crop.season, growth: t.crop.growth, withered: t.crop.withered } : null;
    }
    for (const k in greenVar) delete greenVar[k];
    { let n = 0; for (let i = 0; i < 15; i++) if (game.tiles[i].state === 'green') greenVar[i] = ++n; }
    lastSavedAt = s.ts || Date.now();
    return lastSavedAt;
  } catch (e) { return 0; }
}
loadedTs = loadGame();
window.addEventListener('beforeunload', () => saveGame());

// ---- 工具函数 ----
const $ = id => document.getElementById(id);
// a = 斜线内第几块(0..4)，b = 第几条斜线(0..2)
function tileRect(i) {
  const a = i % 5, b = (i / 5) | 0;
  return { x: TX0 + (a + b) * STEP_X, y: TY0 + (a - b) * STEP_Y, w: TW, h: TH };
}
// 菱形内判定(|dx|/半宽 + |dy|/半高 <= 1)；前排(y大)优先命中
const TILE_ORDER = (() => { const a = [...Array(15).keys()]; return a.sort((p, q) => tileRect(q).y - tileRect(p).y); })();
function tileAt(mx, my) {
  for (const i of TILE_ORDER) {
    const r = tileRect(i), cx = r.x + r.w / 2, cy = r.y + r.h / 2;
    if (Math.abs(mx - cx) / (r.w / 2) + Math.abs(my - cy) / (r.h / 2) <= 1) return i;
  }
  return -1;
}
// 绘制顺序：后排(y小)先画，前排后画，保证前排作物正确遮挡后方
const DRAW_ORDER = (() => { const a = [...Array(15).keys()]; return a.sort((p, q) => tileRect(p).y - tileRect(q).y); })();
function fmtMin(m) {
  m = Math.max(0, Math.round(m));
  if (m >= 1440) { const d = (m / 1440) | 0, h = ((m % 1440) / 60) | 0; return d + '天' + h + '小时'; }
  if (m >= 60) { const h = (m / 60) | 0, mm = m % 60; return h + '小时' + (mm ? mm + '分' : ''); }
  return m + '分钟';
}
function cropImg(id, fi) { return IMG['crop_' + id + '_f' + fi]; }
// 固件实锤（13/13 作物验证）：重熟时间 = 成熟时间 − 大叶子阶段起点。
// 即多季作物收获后进度回到「大叶子」起点，阶段边界不变，再长「重熟时间」重新开花→成熟。
function boundsFor(crop, def) { return def.stages; }
function stageOf(crop, def) {
  const b = boundsFor(crop, def);
  let s = 0;
  for (const st of b) { if (crop.growth >= st[1]) s++; else break; }
  return s;
}
function isMature(crop, def) { const b = boundsFor(crop, def); return crop.growth >= b[b.length - 1][1]; }

// ---- 提示 ----
let toastTimer = null;
function toast(msg, ms) {
  const t = $('toast'); t.textContent = msg; t.style.display = 'block';
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.style.display = 'none', ms || 1600);
}
function floatText(x, y, txt, color) {
  const d = document.createElement('div');
  d.className = 'float'; d.textContent = txt;
  d.style.left = x + 'px'; d.style.top = y + 'px';
  if (color) d.style.color = color;
  $('wrap').appendChild(d);
  setTimeout(() => d.remove(), 1000);
}

// ---- 经验/等级 ----
function addExp(n) {
  game.exp += n;
  while (game.exp >= (game.level + 1) * 100) {
    game.exp -= (game.level + 1) * 100;
    game.level++;
    toast('🎉 升级了！当前 ' + game.level + ' 级');
  }
  updateStatus();
}

// ---- 状态栏 ----
function updateStatus() {
  $('lvText').textContent = 'Lv.' + game.level;
  $('expText').textContent = game.exp + '/' + (game.level + 1) * 100;
  $('goldText').textContent = game.gold;
  const totalSeeds = Object.values(game.seeds).reduce((a, b) => a + b, 0);
  $('bSeed').textContent = totalSeeds; $('bSeed').style.display = totalSeeds ? 'block' : 'none';
  $('bWater').textContent = game.water;
  $('bFert').textContent = game.fert;
  const mm = game.timeMin % 1440;
  $('timeText').textContent = '第' + game.day + '天 ' + String((mm / 60) | 0).padStart(2, '0') + ':' + String(Math.floor(mm % 60)).padStart(2, '0');
  maybeSave();          // 自动存档（节流 3 秒；每次操作后也会走到这里）
}

// ---- 渲染 ----
const canvas = $('scene'), ctx = canvas.getContext('2d');
let hoverTile = -1;
function draw() {
  ctx.clearRect(0, 0, VW, VH);
  ctx.drawImage(IMG.bg, 0, 0, VW, VH);
  // 地块
  for (const i of DRAW_ORDER) {
    const t = game.tiles[i], r = tileRect(i);
    let key;
    if (t.state === 'green') key = 'land_green' + String(greenVar[i]).padStart(2, '0');
    else key = (hoverTile === i && game.tool === 'seed') ? 'land_yellow' : 'land_brown';
    ctx.drawImage(IMG[key], r.x, r.y, r.w, r.h);
  }
  // 作物
  for (const i of DRAW_ORDER) {
    const t = game.tiles[i];
    if (!t.crop) continue;
    // 作物锚点：地块中央(略偏下)，不再是底边
    const r = tileRect(i), cx = r.x + r.w / 2, base = r.y + r.h * 0.52;
    const def = CROP_BY_ID[t.crop.id];
    if (t.crop.withered) {
      const im = cropImg(t.crop.id, def.nFrames - 2);
      ctx.drawImage(im, cx - im.width * S / 2, base - im.height * S, im.width * S, im.height * S);
      continue;
    }
    // 只有种子期(阶段0)才画土堆；发芽后各帧自带基座，避免"种子图标残留"
    const s = stageOf(t.crop, def);
    if (s === 0) {
      const mound = cropImg(t.crop.id, 0);
      const mw = mound.width * S, mh = mound.height * S;
      ctx.drawImage(mound, cx - mw / 2, base - mh, mw, mh);
    } else {
      const im = cropImg(t.crop.id, s);
      const iw = im.width * S, ih = im.height * S;
      ctx.drawImage(im, cx - iw / 2, base - ih, iw, ih);
    }
  }
  // 扩建木牌
  if (game.signTile >= 0 && game.tiles[game.signTile].state === 'green') {
    const r = tileRect(game.signTile), sg = IMG.ui_sign;
    const sw = sg.width * S, sh = sg.height * S;
    ctx.drawImage(sg, r.x + (r.w - sw) / 2, r.y + (r.h - sh) / 2, sw, sh);
  }
  // 装饰(对照原版实机截图+紫玉蓝图：狗在上方沙带，狗窝/大草屋在右侧，栅栏贴房右下)
  ctx.drawImage(IMG.deco_house, 600, 90, IMG.deco_house.width * S, IMG.deco_house.height * S);
  ctx.drawImage(IMG.deco_doghouse, 525, 150, IMG.deco_doghouse.width * S, IMG.deco_doghouse.height * S);
  ctx.drawImage(IMG.deco_fence, 655, 190, IMG.deco_fence.width * 0.65, IMG.deco_fence.height * 0.65);
  ctx.drawImage(IMG.deco_dog, 295, 108, IMG.deco_dog.width * S, IMG.deco_dog.height * S);
  // 悬停高亮
  if (hoverTile >= 0 && game.tool && game.tool !== 'seed') {
    if (validTarget(hoverTile)) {
      const r = tileRect(hoverTile), cx = r.x + r.w / 2, cy = r.y + r.h / 2;
      const hw = r.w / 2 - 3, hh = r.h / 2 - 3;
      ctx.beginPath();
      ctx.moveTo(cx, cy - hh); ctx.lineTo(cx + hw, cy); ctx.lineTo(cx, cy + hh); ctx.lineTo(cx - hw, cy);
      ctx.closePath();
      ctx.strokeStyle = 'rgba(255,235,120,.95)'; ctx.lineWidth = 3;
      ctx.stroke();
    }
  }
}
function validTarget(i) {
  const t = game.tiles[i], def = t.crop ? CROP_BY_ID[t.crop.id] : null;
  if (game.tool === 'shovel') return !!t.crop;
  if (game.tool === 'seed') return t.state === 'brown' && !t.crop;
  if (game.tool === 'water' || game.tool === 'fert') return t.crop && !t.crop.withered && (game.tool === 'water' || !isMature(t.crop, def));
  if (game.tool === 'harvest') return t.crop && !t.crop.withered && isMature(t.crop, def);
  return false;
}

// ---- 主循环 ----
let lastT = 0;
function loop(ts) {
  const dt = Math.min(0.1, (ts - lastT) / 1000 || 0); lastT = ts;
  if (!game.paused) {
    const add = dt * SPEEDS[game.speedIdx];
    game.timeMin += add;
    game.day = ((game.timeMin / 1440) | 0) + 1;
    for (const t of game.tiles) if (t.crop && !t.crop.withered) t.crop.growth += add;
    updateStatus();
  }
  draw();
  requestAnimationFrame(loop);
}
const SPEEDS = [1, 60, 300, 1000];

// ---- 页面放大：目标2倍，屏幕放不下时自动缩小到刚好放下 ----
function applyZoom() {
  const z = Math.min(2, (window.innerWidth - 10) / VW, (window.innerHeight - 10) / VH);
  $('wrap').style.transform = 'scale(' + z + ')';
}
window.addEventListener('resize', applyZoom);
applyZoom();

// ---- 光标 ----
const cursorEl = $('cursor');
const TOOL_ICON = { shovel: 'ui_shovel', water: 'ui_water', fert: 'ui_fert', harvest: 'ui_glove' };
function refreshToolUI() {
  document.querySelectorAll('.tool').forEach(el => el.classList.remove('on'));
  if (game.tool) {
    const map = { shovel: 'tShovel', water: 'tWater', seed: 'tSeed', fert: 'tFert', harvest: 'tHarvest' };
    $(map[game.tool]).classList.add('on');
  }
  canvas.classList.toggle('tool-on', !!game.tool);
  if (game.tool === 'seed' && game.seedCrop) cursorEl.src = ASSETS['icon_' + game.seedCrop];
  else if (game.tool && TOOL_ICON[game.tool]) cursorEl.src = ASSETS[TOOL_ICON[game.tool]];
  else cursorEl.style.display = 'none';
}
function cancelTool() { game.tool = null; game.seedCrop = null; refreshToolUI(); }

// ---- 鼠标交互 ----
canvas.addEventListener('contextmenu', e => { e.preventDefault(); cancelTool(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') { cancelTool(); closeAllPanels(); } });
canvas.addEventListener('mousemove', e => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (VW / rect.width), my = (e.clientY - rect.top) * (VH / rect.height);
  hoverTile = tileAt(mx, my);
  if (game.tool) { cursorEl.style.display = 'block'; cursorEl.style.left = (e.clientX - 34) + 'px'; cursorEl.style.top = (e.clientY - 34) + 'px'; }
  else cursorEl.style.display = 'none';
  const tip = $('tip');
  const t = hoverTile >= 0 ? game.tiles[hoverTile] : null;
  if (t && t.crop) {
    const def = CROP_BY_ID[t.crop.id];
    let html;
    if (t.crop.withered) {
      html = '<b>' + def.name + '</b><br>已枯萎<br>使用铲除清理土地';
    } else {
      const b = boundsFor(t.crop, def), s = stageOf(t.crop, def);
      const cur = s === 0 ? def.seedName : b[s - 1][0];
      const next = s < b.length ? b[s][0] : null;
      const toNext = s < b.length ? b[s][1] - t.crop.growth : 0;
      const toMat = b[b.length - 1][1] - t.crop.growth;
      html = '<b>' + def.name + '</b><br>第' + t.crop.season + '季，共' + def.seasons + '季<br>' +
             (next ? cur + ' —— ' + next : '已成熟，可收获') + '<br>' +
             (next ? '下一阶段 ' + fmtMin(toNext) : '点击收获按钮收取') + '<br>距成熟 ' + fmtMin(toMat);
    }
    tip.innerHTML = html; tip.style.display = 'block';
    let tx = mx + 18, ty = my + 14;
    if (tx + tip.offsetWidth > 790) tx = mx - tip.offsetWidth - 14;
    if (ty + tip.offsetHeight > 470) ty = my - tip.offsetHeight - 10;
    tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
  } else tip.style.display = 'none';
});
canvas.addEventListener('mouseleave', () => { $('tip').style.display = 'none'; hoverTile = -1; cursorEl.style.display = 'none'; });

canvas.addEventListener('click', e => {
  if (hoverTile < 0) return;
  const i = hoverTile, t = game.tiles[i], r = tileRect(i);
  const px = r.x + r.w / 2, py = r.y + 16;
  if (game.signTile === i && t.state === 'green' && !game.tool) { openExpansion(); return; }
  if (!game.tool) return;
  if (game.tool === 'seed') {
    if (t.state !== 'brown' || t.crop) { toast('只能播种在褐色空地上'); return; }
    const id = game.seedCrop;
    if (!game.seeds[id]) { cancelTool(); return; }
    game.seeds[id]--; game.tiles[i].crop = { id, season: 1, growth: 0, withered: false };
    addExp(2); floatText(px, py, '播种 +2', '#c8e6c9');
    if (!game.seeds[id]) { cancelTool(); toast('种子用完了'); }
    updateStatus(); return;
  }
  if (game.tool === 'water') {
    if (!t.crop || t.crop.withered) { toast('这里没有可浇水的作物'); return; }
    if (game.water <= 0) { toast('水用完了！'); return; }
    game.water--; addExp(2); floatText(px, py, '浇水 +2', '#b3e5fc'); updateStatus(); return;
  }
  if (game.tool === 'fert') {
    if (!t.crop || t.crop.withered) { toast('这里没有可施肥的作物'); return; }
    const def = CROP_BY_ID[t.crop.id];
    if (isMature(t.crop, def)) { toast('已成熟，无需施肥'); return; }
    if (game.fert <= 0) { toast('化肥不足！'); return; }
    game.fert--; const before = stageOf(t.crop, def);
    t.crop.growth += 60;
    const after = stageOf(t.crop, def);
    addExp(2); floatText(px, py, '施肥 +2 ⏱1h', '#ffe082');
    if (after > before) floatText(px, py - 26, '进入新阶段！', '#fff59d');
    updateStatus(); return;
  }
  if (game.tool === 'harvest') {
    if (!t.crop || t.crop.withered) { toast('这里没有可收获的作物'); return; }
    const def = CROP_BY_ID[t.crop.id];
    if (!isMature(t.crop, def)) { toast('作物尚未成熟'); return; }
    game.warehouse[t.crop.id] = (game.warehouse[t.crop.id] || 0) + def.yield;
    addExp(def.exp);
    floatText(px, py, '收获 +' + def.exp + '经验', '#ffcc80');
    floatText(px, py - 24, def.name + ' ×' + def.yield, '#ffe0b2');
    if (t.crop.season >= def.seasons) t.crop.withered = true;
    else { t.crop.season++; t.crop.growth = Math.max(0, def.total - def.reharvest); }  // 回到大叶子，非种子
    updateStatus(); return;
  }
  if (game.tool === 'shovel') {
    if (!t.crop) { toast('这里没有需要铲除的东西'); return; }
    t.crop = null; addExp(3); floatText(px, py, '铲除 +3', '#d7ccc8'); updateStatus(); return;
  }
});

// ---- 工具栏 ----
$('tShovel').onclick = () => { game.tool = game.tool === 'shovel' ? null : 'shovel'; refreshToolUI(); };
$('tWater').onclick = () => { game.tool = game.tool === 'water' ? null : 'water'; refreshToolUI(); };
$('tHarvest').onclick = () => { game.tool = game.tool === 'harvest' ? null : 'harvest'; refreshToolUI(); };
$('tFert').onclick = () => { game.tool = game.tool === 'fert' ? null : 'fert'; refreshToolUI(); };
$('tSeed').onclick = () => { cancelTool(); openSeedPanel(); };
$('restore').onclick = () => { cancelTool(); closeAllPanels(); toast('已恢复鼠标指针'); };

// ---- 面板基础 ----
function closeAllPanels() { document.querySelectorAll('.panel').forEach(p => p.style.display = 'none'); }
document.querySelectorAll('.ximg').forEach(x => x.onclick = () => $(x.dataset.close).style.display = 'none');

// ---- 种子包 ----
function openSeedPanel() {
  const grid = $('seedGrid'); grid.innerHTML = '';
  const owned = CROPS.filter(c => game.seeds[c.id]);
  if (!owned.length) { grid.innerHTML = '<div style="grid-column:1/-1;color:#889;font-size:13px;padding:14px;text-align:center">还没有种子<br>去商城买一些吧</div>'; }
  owned.forEach(c => {
    const cell = document.createElement('div');
    cell.className = 'seedcell';
    cell.innerHTML = '<img src="' + ASSETS['icon_' + c.id] + '"><div class="nm">' + c.name + '</div><div class="qt">×' + game.seeds[c.id] + '</div>';
    cell.onclick = () => {
      game.tool = 'seed'; game.seedCrop = c.id;
      $('seedPanel').style.display = 'none';
      refreshToolUI();
      toast('已选' + c.name + '种子：移动到褐色土地再次点击播种');
    };
    grid.appendChild(cell);
  });
  $('seedPanel').style.display = 'block';
}

// ---- 仓库 ----
function openWarehouse() {
  const body = $('whBody'); body.innerHTML = '';
  const owned = CROPS.filter(c => game.warehouse[c.id]);
  if (!owned.length) { body.innerHTML = '<div style="color:#889;font-size:13px;padding:18px;text-align:center">仓库空空如也<br>收获的果实会放在这里</div>'; $('whPanel').style.display = 'block'; return; }
  const grid = document.createElement('div'); grid.className = 'whgrid';
  owned.forEach(c => {
    const cell = document.createElement('div');
    cell.className = 'fruitcell';
    cell.innerHTML = '<img src="' + ASSETS['icon_' + c.id] + '"><div class="nm">' + c.name + '</div><div class="qt">×' + game.warehouse[c.id] + '</div>';
    cell.onclick = () => openSell(c.id);
    grid.appendChild(cell);
  });
  body.appendChild(grid);
  const hint = document.createElement('div'); hint.className = 'cnote'; hint.textContent = '点击果实进入售卖';
  body.appendChild(hint);
  $('whPanel').style.display = 'block';
}
$('whBtn').onclick = () => { closeAllPanels(); openWarehouse(); };

// ---- 售卖 ----
let sellCrop = null, sellQty = 1;
function openSell(id) {
  sellCrop = id; sellQty = 1;
  renderSell(); $('sellPanel').style.display = 'block';
}
function renderSell() {
  const c = CROP_BY_ID[sellCrop], have = game.warehouse[sellCrop];
  sellQty = Math.max(1, Math.min(sellQty, have));
  $('sellBody').innerHTML =
    '<div style="text-align:center"><img src="' + ASSETS['icon_' + c.id] + '" style="width:56px;height:56px;object-fit:contain"></div>' +
    '<div style="text-align:center;font-size:15px;font-weight:700;color:#333;margin:4px 0">' + c.name + '</div>' +
    '<div style="text-align:center;font-size:13px;color:#555">单价 <b style="color:#b26a00">' + c.fruitPrice + '</b> 点币 · 持有 ' + have + ' 个</div>' +
    '<div class="sellrow"><button class="qtybtn" id="qMinus">−</button><input class="numin" id="qtyInput" value="' + sellQty + '"><button class="qtybtn" id="qPlus">＋</button><button class="qtybtn" id="qAll" style="width:auto;font-size:12px;padding:0 8px">全部</button></div>' +
    '<div style="text-align:center;font-size:14px;color:#333">总售价 <b id="totalPrice" style="color:#d32f2f;font-size:17px">' + (c.fruitPrice * sellQty) + '</b> 点币</div>' +
    '<div class="sellrow" style="margin-top:10px"><button class="cancelbtn" id="sellBack">返回</button><button class="okbtn" id="sellOk">确认售卖</button></div>';
  $('qMinus').onclick = () => { sellQty = Math.max(1, sellQty - 1); renderSell(); };
  $('qPlus').onclick = () => { sellQty = Math.min(have, sellQty + 1); renderSell(); };
  $('qAll').onclick = () => { sellQty = have; renderSell(); };
  $('qtyInput').onchange = e => { sellQty = Math.max(1, Math.min(have, parseInt(e.target.value) || 1)); renderSell(); };
  $('sellBack').onclick = () => { $('sellPanel').style.display = 'none'; openWarehouse(); };
  $('sellOk').onclick = () => {
    game.gold += c.fruitPrice * sellQty;
    game.warehouse[c.id] -= sellQty;
    if (!game.warehouse[c.id]) delete game.warehouse[c.id];
    toast('售出 ' + c.name + ' ×' + sellQty + '，获得 ' + (c.fruitPrice * sellQty) + ' 点币');
    $('sellPanel').style.display = 'none';
    updateStatus(); openWarehouse();
  };
}

// ---- 作物详情（原版商店面板字段，固件实锤文案） ----
const SEASON_TXT = ['', '一季作物', '二季作物', '三季作物', '四季作物', '五季作物', '六季作物', '七季作物', '八季作物'];
function infoRow(k, v) { return '<div><span class="k">' + k + '</span><span class="v">' + v + '</span></div>'; }
function fmtDur(min) { const h = min / 60; if (h < 24) return h.toFixed(1).replace(/\.0$/, '') + '小时'; const d = (h / 24) | 0, r = Math.round(h % 24); return r ? d + '天' + r + '小时' : d + '天'; }
function openCropInfo(c) {
  const seasonTxt = SEASON_TXT[c.seasons] || (c.seasons + '季作物');
  const perSeason = c.yield * c.fruitPrice;
  const totalIncome = perSeason * c.seasons;
  const net = c.seasons > 1 ? totalIncome - c.seedPrice : perSeason - c.seedPrice;
  const netNote = c.seasons > 1 ? c.seasons + '季收入合计−种子价（推算）' : '单季收入−种子价（推算）';
  // 阶段卡：frame0=播种(土堆)，其后每阶段一帧固件原始贴图
  const items = [{ f: 0, nm: c.seedName, t: 0 }];
  c.stages.forEach((s, i) => items.push({ f: i + 1, nm: s[0], t: s[1] }));
  let prev = 0;
  const strip = items.map(it => {
    const gap = it.t - prev; prev = it.t;
    return '<div class="stagecard"><img src="' + ASSETS['crop_' + c.id + '_f' + it.f] + '">' +
      '<div class="sn">' + it.nm + '</div>' +
      '<div class="st">' + (it.f === 0 ? '起点' : '+' + fmtDur(gap)) + '</div>' +
      '<div class="sc">' + (it.f === 0 ? '0分' : '累计 ' + fmtDur(it.t)) + '</div></div>';
  }).join('');
  $('cropBody').innerHTML =
    '<div class="crophead"><img src="' + ASSETS['icon_' + c.id] + '"><div>' +
      '<div class="tt">' + c.name + '</div>' +
      '<div class="sub">固件编号 ID ' + c.id + ' · 下列字段为原版商店面板原文</div>' +
    '</div></div>' +
    '<div class="infogrid">' +
      infoRow('作物类型：', seasonTxt) +
      infoRow('种植等级：', c.level + '级') +
      infoRow('成熟时间：', (c.total / 60).toFixed(1) + '小时') +
      infoRow('重熟时间：', c.seasons > 1 ? (c.reharvest / 60).toFixed(1) + '小时（回到大叶子）' : '一次性作物') +
      infoRow('预计产量：', c.yield + '个/季') +
      infoRow('果实售价：', '点币' + c.fruitPrice) +
      infoRow('预计收入：', '点币' + perSeason + '（单季）') +
      infoRow('收获经验：', c.exp + '/季') +
      infoRow('种子价格：', '点币' + c.seedPrice) +
      infoRow('全季总产量：', (c.yield * c.seasons) + '个（' + c.seasons + '季合计）') +
      infoRow('全季总收入：', '点币' + totalIncome) +
      infoRow('净收益：', '点币' + net + '（推算）') +
      infoRow('收益口径：', c.seasons > 1 ? c.seasons + '季收入合计−种子价' : '单季收入−种子价') +
    '</div>' +
    '<div style="margin-top:9px;font-size:12.5px;color:#145a8a;font-weight:700">生长阶段（配图为固件原始贴图）</div>' +
    '<div class="stagestr">' + strip + '</div>' +
    '<div class="cropnote">数据与贴图全部来自 T5 固件实锤提取；原版固件未提供作物背景故事文本，故不作虚构描述。' +
      (c.seasons > 1 ? '多季作物收获后回到「大叶子」阶段（不是种子），再长 ' + (c.reharvest / 60).toFixed(1) + ' 小时重新开花→结果→成熟；该机制由「重熟时间 = 成熟时间 − 大叶子起点」在 13 种作物上验证得出。' : '') + '</div>';
  $('cropPanel').style.display = 'block';
}

// ---- 商城 ----
function openShop() {
  const list = $('shopList'); list.innerHTML = '';
  CROPS.forEach(c => {
    const lock = c.level > game.level;
    const row = document.createElement('div');
    row.className = 'shoprow' + (lock ? ' lock' : '');
    row.innerHTML = '<img class="ic" src="' + ASSETS['icon_' + c.id] + '"><span class="nm">' + c.name + '</span>' +
      '<span class="lv">' + (lock ? 'Lv.' + c.level + ' 解锁' : '种植等级 Lv.' + c.level) + '</span>' +
      '<span class="pr">' + c.seedPrice + ' 点币</span>' +
      '<button class="det">详情</button>' +
      '<button class="buy">' + (lock ? '未解锁' : '购买') + '</button>';
    row.querySelector('.det').onclick = () => openCropInfo(c);
    if (!lock) row.querySelector('.buy').onclick = () => {
      if (game.gold < c.seedPrice) { toast('您的点币不足！'); return; }
      game.gold -= c.seedPrice;
      game.seeds[c.id] = (game.seeds[c.id] || 0) + 1;
      toast('购买 ' + c.name + ' 种子 ×1');
      updateStatus(); openShop();
    };
    list.appendChild(row);
  });
  $('shopPanel').style.display = 'block';
}
$('shopBtn').onclick = () => { closeAllPanels(); openShop(); };

// ---- 扩建 ----
function expansionReq(k) { return { level: 2 + ((k - 1) >> 1), cost: 300 + 200 * (k - 1) }; }
function openExpansion() {
  const k = game.expansions + 1, req = expansionReq(k);
  const lackLv = game.level < req.level, lackGold = game.gold < req.cost;
  $('dlgTitle').textContent = '扩建土地';
  $('dlgBody').innerHTML =
    '扩建这块地需要等级 <b>' + req.level + '</b> 级<br>和点币 <b style="color:#b26a00">' + req.cost + '</b><br>' +
    '<span style="font-size:12.5px;color:#666">当前等级 ' + game.level + ' 级 · 持有 ' + game.gold + ' 点币</span>' +
    (lackLv || lackGold ? '<br><span class="warn">' + (lackLv && lackGold ? '您的等级和点币不足!' : lackLv ? '等级不足!' : '您的点币不足!') + '</span>' : '') +
    '<div class="sellrow" style="margin-top:8px"><button class="cancelbtn" id="dlgNo">取消</button>' +
    (lackLv || lackGold ? '' : '<button class="okbtn" id="dlgYes">确定</button>') + '</div>';
  $('dlg').style.display = 'block';
  $('dlgNo').onclick = () => $('dlg').style.display = 'none';
  if (!lackLv && !lackGold) $('dlgYes').onclick = () => {
    game.gold -= req.cost; game.expansions++;
    const idx = game.signTile;
    game.tiles[idx].state = 'brown'; delete greenVar[idx];
    let next = -1;
    for (let i = 0; i < 15; i++) if (game.tiles[i].state === 'green') { next = i; break; }
    game.signTile = next;
    toast('扩建成功！获得一块新土地');
    $('dlg').style.display = 'none'; updateStatus();
  };
}

// ---- 速度控制 ----
$('speedBtn').onclick = () => { game.speedIdx = (game.speedIdx + 1) % SPEEDS.length; $('speedBtn').textContent = '×' + SPEEDS[game.speedIdx]; };
$('pauseBtn').onclick = () => { game.paused = !game.paused; $('pauseBtn').textContent = game.paused ? '▶' : '⏸'; };

// ---- 控制台 ----
function fillCropSelect(sel) {
  sel.innerHTML = '';
  CROPS.forEach(c => { const o = document.createElement('option'); o.value = c.id; o.textContent = c.name; sel.appendChild(o); });
}
fillCropSelect($('cSeedCrop')); fillCropSelect($('cFruitCrop'));
$('consoleBtn').onclick = () => {
  closeAllPanels(); $('consolePanel').style.display = 'block';
  $('saveTip').textContent = lastSavedAt ? ('上次保存 ' + clockStr(lastSavedAt)) : (saveOK ? '尚未保存' : '⚠ 浏览器禁用了本地存储，无法存档');
};
$('cSaveNow').onclick = () => { maybeSave(true); toast(saveOK ? '存档已保存' : '存档失败：浏览器禁用了本地存储'); };
$('cResetSave').onclick = () => {
  if (!confirm('确定重置存档？所有进度（等级/点币/地块/作物/仓库）将清空，回到最初状态。')) return;
  try { localStorage.removeItem(SAVE_KEY); } catch (e) {}
  location.reload();
};
function num(id) { return parseInt($(id).value) || 0; }
$('cGoldSet').onclick = () => { game.gold = Math.max(0, num('cGold')); updateStatus(); toast('点币已设为 ' + game.gold); };
$('cGoldAdd').onclick = () => { game.gold += 1000; updateStatus(); toast('+1000 点币'); };
$('cGoldMax').onclick = () => { game.gold += 99999; updateStatus(); toast('+99999 点币'); };
$('cLevelSet').onclick = () => { game.level = Math.max(1, num('cLevel')); updateStatus(); toast('等级已设为 ' + game.level); };
$('cExpSet').onclick = () => { game.exp = Math.max(0, num('cExp')); updateStatus(); toast('经验已设为 ' + game.exp); };
$('cWater30').onclick = () => { game.water += 30; updateStatus(); toast('水 +30'); };
$('cWater300').onclick = () => { game.water += 300; updateStatus(); toast('水 +300'); };
$('cFert10').onclick = () => { game.fert += 10; updateStatus(); toast('化肥 +10'); };
$('cFert100').onclick = () => { game.fert += 100; updateStatus(); toast('化肥 +100'); };
$('cSeedGive').onclick = () => {
  const id = parseInt($('cSeedCrop').value), q = Math.max(1, num('cSeedQty'));
  game.seeds[id] = (game.seeds[id] || 0) + q;
  updateStatus(); toast(CROP_BY_ID[id].name + '种子 ×' + q + ' 已放入种子包');
};
$('cFruitGive').onclick = () => {
  const id = parseInt($('cFruitCrop').value), q = Math.max(1, num('cFruitQty'));
  game.warehouse[id] = (game.warehouse[id] || 0) + q;
  updateStatus(); toast(CROP_BY_ID[id].name + ' ×' + q + ' 已放入仓库');
};

// ---- 启动 ----
updateStatus();
refreshToolUI();
$('speedBtn').textContent = '×' + SPEEDS[game.speedIdx];
if (loadedTs) setTimeout(() => toast('存档已恢复 · 第' + game.day + '天 · Lv.' + game.level + ' · ' + game.gold + ' 点币', 2800), 400);
else setTimeout(() => toast('新游戏：先点右上「商城」买种子', 2800), 400);
window.__game = game;   // 调试钩子
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

html = HTML.replace("__ASSETS__", json.dumps(assets)).replace("__CROPS__", json.dumps(crops, ensure_ascii=False))
out = f"{ROOT}/点点农场_复刻版.html"
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"游戏已生成: {out} ({os.path.getsize(out):,} 字节)")
