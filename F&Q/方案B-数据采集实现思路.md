# 方案 B · 数据采集实现思路（ScraperFC 多联赛多赛季）

> 目标：参照「方案 B」用 **ScraperFC** 抓取最新、最全的球员数据，产出统一的 `data/raw/players.csv`，无缝接入现有 [docs 阶段 1-9](../docs/README.md) 的分析流程。
>
> 本文件是**数据采集层（可视为“阶段 0”）** 的设计说明，只讲实现思路与关键决策，不是完整代码。

---

## 1. 方案 B 到底用什么

方案 B 的原始载体是 [`kupsas/football-data-mcp`](https://github.com/kupsas/football-data-mcp)，它是 [`oseymour/ScraperFC`](https://github.com/oseymour/ScraperFC)（395★，GPL-3.0）的一个封装 fork，对外暴露的是 **MCP 工具**（供 Claude 等 LLM 对话式调用）。

| 选项 | 形态 | 是否适合本项目 |
|------|------|----------------|
| `football-data-mcp` | MCP 服务，对话式查询 | ❌ 面向 LLM 对话，不产出可复现的 CSV 管道，和"本地 Python 脚本 MVP"定位不符 |
| **`ScraperFC`（底层库）** | 纯 Python 库，`pip install ScraperFC` | ✅ **本项目采用**。直接在脚本里调用，把数据落成 CSV，完全符合方案 A 的本地脚本闭环 |

**结论**：我们不装 MCP，直接用底层的 **ScraperFC** 库。它正是 football-data-mcp 数据能力的来源，能拿到同样"10 联赛 × 多赛季"的数据，但产出的是我们能控制的 CSV。

---

## 2. 数据采集在整体流程中的位置

```
[新增] 阶段 0：ScraperFC 采集
   ├─ 选定联赛 × 赛季
   ├─ 逐联赛逐赛季抓取多个 stat 分类（standard / passing / defense / possession / misc）
   ├─ 扁平化多级表头 + 按 player_id 横向合并
   └─ 落盘 → data/raw/players.csv
                  ↓
阶段 1：数据读取与字段检查   ← 现有流程从这里开始，几乎不用改
阶段 2-9：清洗 → 特征 → 评分 → 联赛修正 → 排行榜 → 雷达图 → 报告
```

采集层的**唯一职责**：产出一个字段命名统一、含 U21 所需列的 `players.csv`。之后的分析全部复用现有 docs。

---

## 3. ScraperFC 核心用法

```bash
pip install ScraperFC pandas pyarrow
```

```python
from ScraperFC.fbref import FBref

# wait_time>=7：FBref 要求每分钟 ≤10 次请求，务必限速，否则会被封 IP
fb = FBref(wait_time=7)

# 1) 查可用联赛名（写死前先确认拼写）
print(list(fb.comps.keys()))
# 例：['Champions League','Europa League','EPL','La Liga','Serie A','Bundesliga','Ligue 1', ...]

# 2) 查某联赛的可用赛季（确认年份格式）
print(list(fb.get_valid_seasons("La Liga").keys()))
# 例：['2025-2026','2024-2025','2023-2024', ...]

# 3) 查可用 stat 分类
print(list(fb.stats_categories.keys()))
# 例：['standard','goalkeeping','advanced goalkeeping','shooting','passing',
#      'passing types','goal and shot creation','defense','possession','misc', ...]

# 4) 抓取单个联赛×赛季×分类 → 返回 (squad_stats, opponent_stats, player_stats)
squad, opp, players = fb.scrape_stats("2025-2026", "La Liga", "standard")
```

**关键 API 速查**

| 方法 | 作用 | 返回 |
|------|------|------|
| `fb.comps.keys()` | 所有可用联赛名 | dict keys |
| `fb.get_valid_seasons(league)` | 某联赛可用赛季 | `{year: url}` |
| `fb.stats_categories.keys()` | 所有 stat 分类 | dict keys |
| `fb.scrape_stats(year, league, category)` | 抓单分类 | `(squad, opponent, player)` 三个 DataFrame |
| `fb.scrape_all_stats(year, league)` | 抓全部分类 | `{category: (squad,opp,player)}` |

> **年份格式**：FBref 用 `"2025-2026"` 这种连字符格式，不是 `2025`。写死前一定用 `get_valid_seasons()` 核对。

---

## 4. 联赛与赛季选择（对齐方案 B 的 10 联赛 × 3 赛季）

```python
# 与阶段 5 的 Opta 联赛强度表尽量对齐
LEAGUES = [
    "EPL", "La Liga", "Serie A", "Bundesliga", "Ligue 1",   # 五大联赛（全字段）
    "Eredivisie", "Primeira Liga",                           # 荷甲、葡超（强字段）
    "Championship",                                          # 英冠（基础字段）
    "Champions League", "Europa League",                    # 欧冠、欧联（基础字段）
]
SEASONS = ["2023-2024", "2024-2025", "2025-2026"]
```

**赛季取舍建议**（重要）：
- **主数据用 `2024-2025`（完整赛季）**：样本最稳，满足 `minutes >= 600` 阈值的球员最多，评分最可信。
- `2025-2026` 作为"最新赛季对照"：**赛季进行中，是部分数据**，很多球员分钟数还没到 600，直接当主榜会触发需求文档第十六章点名的"小样本虚高"风险。可单独出一版"本赛季新星观察"榜。
- `2023-2024` 用于成长趋势对比（需求文档第十七章的扩展方向）。

---

## 5. 抓哪些 stat 分类，字段如何对齐需求

单个 `standard` 分类不够——评分模型里 DM/CM 的抢断、拦截在 `defense` 分类，过人在 `possession` 分类。需要抓多个分类再横向合并。

| ScraperFC stat 分类 | 提供的关键字段 | 对应需求文档字段 | 服务的位置评分 |
|---------------------|----------------|------------------|----------------|
| `standard` | Age、Pos、Min、Gls、Ast、xG、xAG | 必须字段 + 年龄/出场 | 全部 |
| `passing` | Key Passes、Progressive Passes、Pass Cmp% | key_passes、progressive | AM / CM |
| `defense` | Tackles、Interceptions、Blocks | tackles、interceptions | DM / CM |
| `possession` | Dribbles/Take-Ons、Progressive Carries、禁区触球 | dribbles、progressive_carries | Winger / AM |
| `goal and shot creation` | SCA、GCA | shot_creating_actions | AM / Winger |
| `misc` | 黄牌、红牌、犯规、对抗成功率 | yellow/red_cards、风险扣分 | 全部（纪律性） |

**建议至少抓**：`standard` + `passing` + `defense` + `possession` + `misc` 五类。

---

## 6. 两个必须处理的技术坑

### 坑 1：多级表头（MultiIndex columns）
FBref 的 `player_stats` DataFrame 列是**两级表头**（如 `('Performance','Gls')`、`('Per 90 Minutes','Gls')`）。必须先扁平化，否则 pandas 取列会很痛苦。

```python
def flatten_columns(df):
    df = df.copy()
    df.columns = [
        c[-1] if isinstance(c, tuple) else c   # 取最内层名，或按需拼 'Performance_Gls'
        for c in df.columns
    ]
    return df
```
扁平化后再喂给现有 `config/field_mapping.yaml`（阶段 1），把 FBref 列名映射成系统内部标准名。**这一步让采集层和现有流程解耦**——阶段 1-9 完全不用改，只需在 `field_mapping.yaml` 补 FBref 的列名别名。

### 坑 2：位置粒度不足（对本项目是核心难点）
FBref 赛季 stats 表的 `Pos` 只给粗分类：`FW / MF / DF / GK`（或 `MF,FW` 组合），**无法直接区分 Winger / AM / CM / DM**——而这正是评分模型的分组基础（阶段 2/4）。

> ⚠️ 注意：FBref **球员个人主页**其实有二级细分位置（见下方"兜底 B"），只是不在 stats 表里。所以补细分位置不一定要引入外部源。

完整方案见下一节【7. 位置细分补充方案】。

---

## 7. 位置细分补充方案（分层，按需选用）

评分模型必须把球员分到 Winger / AM / CM / DM 四组。下面是分层的补位置方案，从"零成本兜底"到"最准外部源"，**MVP 可只做第 0 层，答辩前叠加第 1 层**。

### 方案对比

| 层 | 来源 | 位置粒度 | 与 Winger/AM/CM/DM 对应 | 接入成本 | 新依赖 | 时效 |
|----|------|:---:|:---:|:---:|:---:|:---:|
| 0 | FBref 粗位置 + 启发式 | FW/MF/DF | 靠指标比值猜，有误差 | 极低 | 无 | 当季 |
| **1（首选）** | **Transfermarkt 主位置** | Right Winger / AM / CM / DM | ✅ **几乎 1:1** | 低 | **无（ScraperFC 自带）** | 主位置稳定 |
| B（兜底） | FBref 球员个人页二级位置 | AM-CM-WM 组合 | ✅ 好（需解析组合） | 中 | 无（同源） | 生涯级 |
| 2（可选） | FotMob | rightwinger / AM / LW 等 | ✅ 好 | 中 | 需装 fotmob-wrapper | 当季最新 |

> ❌ **不用 Wyscout**：其公开 API 的 role 只有 GK/DF/MD/FW 粗分类，且付费，补不了细分。

### 第 0 层：启发式映射（MVP 先跑通）

只用 FBref 现有数据，零成本先让流程闭环：
- `FW` 且非纯中锋 → `Winger`
- `MF` 用进攻/防守指标比值粗分：`key_passes_per90` 高 → `AM`；`tackles+interceptions` 高 → `DM`；居中 → `CM`

简单但有误差，仅作 MVP 起步。

### 第 1 层（首选）：Transfermarkt 主位置

Transfermarkt 球员页的 `Main position` 命名和评分分组几乎 1:1：
`Right Winger / Left Winger → Winger`、`Attacking Midfield → AM`、`Central Midfield → CM`、`Defensive Midfield → DM`。

**最大优势：ScraperFC 同库自带 Transfermarkt 模块，无新依赖。**

```python
import ScraperFC as sfc

tm = sfc.Transfermarkt()
# 注意 Transfermarkt 的年份格式是 "23/24"，与 FBref 的 "2023-2024" 不同
tm_players = tm.scrape_players("24/25", "EPL")   # 返回含 position 的 DataFrame
```

映射表建议放进配置（如 `config/position_mapping.yaml`）：

```yaml
# Transfermarkt 主位置 → 系统标准分组
Right Winger: Winger
Left Winger: Winger
Winger: Winger
Attacking Midfield: AM
Central Midfield: CM
Defensive Midfield: DM
# 中锋、后卫等 → 不进入评分（阶段 2 会过滤）
```

### 兜底 B：FBref 个人页二级位置（不想匹配外部源时）

FBref 球员主页顶部有二级位置，格式如 `Position: FW-MF (AM-CM-WM)`，括号内即细分。
只对**进入 Top 20 候选**的球员各多抓一次个人页，请求量小、无新依赖：

```python
import re
def parse_fbref_secondary_pos(page_text):
    # 从 "Position: FW-MF (AM-CM-WM)" 提取括号内二级位置
    m = re.search(r"Position:\s*[A-Z\-]+\s*\(([^)]+)\)", page_text)
    return m.group(1).split("-") if m else []   # ['AM','CM','WM']
```

取第一个二级位置或按优先级（`WM/LW/RW→Winger`、`AM→AM`、`CM→CM`、`DM→DM`）归组。注意它是**生涯级**，不是当季。

### 第 2 层（可选）：FotMob 当季位置

要"本赛季最新踢的位置"时用。FotMob 公开 API 免认证、无反爬，字段 `positionDescription.primaryPosition.label`（如 `Right Winger`），但要多装 `fotmob-wrapper` 并多做一次匹配。

### ⚠️ 所有外部源的共同难点：跨源实体匹配

FBref 与 Transfermarkt/FotMob **无共享球员 ID**，必须靠 `球员名 + 俱乐部（+ 出生日期）` 模糊匹配。这才是真正的工作量（重名、译名差异、赛季中转会导致俱乐部不一致），不是拉数据本身。

```python
import unicodedata

def norm(s):
    # 去重音、小写、去空格，降低译名/格式差异带来的不匹配
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().replace(".", "").strip()

def attach_position(fbref_df, tm_df, pos_map):
    fbref_df["_k"] = fbref_df["player_name"].map(norm) + "|" + fbref_df["team"].map(norm)
    tm_df["_k"]    = tm_df["player_name"].map(norm)   + "|" + tm_df["team"].map(norm)
    tm_small = tm_df[["_k", "position"]].drop_duplicates("_k")
    merged = fbref_df.merge(tm_small, on="_k", how="left")
    merged["standard_position"] = merged["position"].map(pos_map)  # → Winger/AM/CM/DM
    return merged.drop(columns=["_k"])
```

匹配不上的球员：回落到第 0 层启发式，并在数据完整度里标记（阶段 3/报告会提示）。

### 落地建议（分层推进）

1. **MVP**：只做第 0 层启发式，先把阶段 1-9 跑通。
2. **答辩前**：叠加第 1 层 Transfermarkt 主位置，批量校正全体候选（同库、命名直接对应）。
3. **进 Top 20 的球员**：用兜底 B（FBref 个人页）或人工再核一遍，量小可控、答辩显严谨。
4. 需要"当季最新位置"再上第 2 层 FotMob。

---

## 8. 采集主流程（伪代码）

```python
import pandas as pd
from ScraperFC.fbref import FBref

fb = FBref(wait_time=7)
CATEGORIES = ["standard", "passing", "defense", "possession", "misc"]

all_rows = []
for season in SEASONS:
    for league in LEAGUES:
        # 每个联赛×赛季：抓多个分类，按 player_id 横向合并成一行/球员
        merged = None
        for cat in CATEGORIES:
            try:
                _, _, players = fb.scrape_stats(season, league, cat)
            except Exception as e:
                print(f"跳过 {league} {season} {cat}: {e}")   # 单点失败不阻塞整体
                continue
            players = flatten_columns(players)
            players = players.loc[:, ~players.columns.duplicated()]  # 去重复列
            merged = players if merged is None else merged.merge(
                players, on="player_id", how="outer", suffixes=("", f"_{cat}")
            )
        if merged is not None:
            merged["league"] = league          # 供阶段 5 联赛强度映射
            merged["season"] = season
            all_rows.append(merged)

raw = pd.concat(all_rows, ignore_index=True)

# 位置细分：先启发式兜底（第 0 层），再用 Transfermarkt 主位置覆盖（第 1 层，见第 7 节）
# raw = attach_position(raw, tm_players, pos_map)   # 命名+球队匹配，覆盖 standard_position

raw.to_csv("data/raw/players.csv", index=False, encoding="utf-8-sig")
```

**产出即接口**：`data/raw/players.csv` 就是阶段 1 的输入，采集层到此结束。位置细分方案详见第 7 节。

---

## 9. 与现有阶段的衔接点

| 衔接 | 说明 |
|------|------|
| → 阶段 1 | 采集产出 `data/raw/players.csv`；只需在 `field_mapping.yaml` 补 FBref 列名别名 |
| → 阶段 2 | 位置细分见第 7 节（首选 Transfermarkt 主位置）；`league` 列已带上，供筛选 |
| → 阶段 5 | `league` 列的取值必须和 `league_strength_opta.yaml` 的 key 对齐（如 FBref 的 `"EPL"` vs 强度表的 `"Premier League"`，需加一层联赛名归一化） |
| → 阶段 9 | README 数据源章节改为"ScraperFC 采集"，注明来源、许可、采集时间 |

---

## 10. 风险与合规

| 风险 | 说明 | 应对 |
|------|------|------|
| **限速/封 IP** | FBref 每分钟 ≤10 请求 | `wait_time=7`，分批抓，失败重试；10 联赛×3 赛季×5 分类=150 次请求，需耐心（约 20-30 分钟） |
| **网站改版** | FBref 改 HTML 会导致 ScraperFC 短期失效 | 锁定 ScraperFC 版本；把抓好的 CSV 缓存/提交，避免每次重抓 |
| **赛季进行中** | 2025-26 是部分数据 | 主榜用 2024-25 完整赛季；2025-26 单独出观察榜 |
| **位置粒度** | FBref stats 表无 AM/DM 细分 | 见第 7 节位置细分补充方案（首选 Transfermarkt） |
| **跨源匹配** | 补位置需 FBref↔Transfermarkt 匹配，无共享 ID | 名+球队+生日模糊匹配；匹配不上回落启发式并标记 |
| **许可证** | ScraperFC 是 **GPL-3.0** | 学生/展示项目无碍；若未来分发代码需遵守 GPL，注明依赖来源 |
| **使用条款** | Sports Reference/FBref 有爬虫 TOS | 仅学习用途、限速、不高频商用；README 注明数据来源与用途 |

---

## 11. 落地步骤清单

- [ ] `pip install ScraperFC pandas pyarrow`
- [ ] 写 `src/collector.py`：用 `get_valid_seasons` / `comps.keys()` 确认联赛赛季拼写
- [ ] 实现多分类抓取 + 表头扁平化 + 按 `player_id` 合并
- [ ] 加联赛名归一化（FBref 名 → Opta 强度表 key）
- [ ] 落盘 `data/raw/players.csv`，并**提交一份缓存**避免重复抓取
- [ ] 在 `field_mapping.yaml` 补 FBref 列名别名
- [ ] 位置细分（第 7 节）：MVP 用第 0 层启发式 → 答辩前叠加第 1 层 Transfermarkt 主位置 → Top 20 用兜底 B/人工校正
- [ ] 跑通阶段 1-9，核对各阶段验收标准

---

## 参考来源

- ScraperFC 仓库（GPL-3.0，395★）：https://github.com/oseymour/ScraperFC
- ScraperFC 文档（FBref 模块 API）：https://scraperfc.readthedocs.io/en/latest/fbref.html
- ScraperFC 代码示例：https://scraperfc.readthedocs.io/en/stable/example.html
- 方案 B 原始封装（10 联赛×3 赛季）：https://github.com/kupsas/football-data-mcp
- FBref 位置判定说明（Primary/Secondary 位置）：https://fbref.com/en/about/errata
- Transfermarkt 球员页示例（Main position）：https://www.transfermarkt.com/gavi/profil/spieler/646740
- FotMob 位置字段（positionDescription）：https://github.com/alraven3/Football
- fotmob-wrapper（可选，MIT）：https://github.com/tommhe14/fotmob-wrapper
