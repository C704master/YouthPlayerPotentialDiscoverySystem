# 阶段 5 · Opta 联赛强度修正

> 对应原文档：九、Opta Power Rankings 联赛强度方案（9.1 采用理由、9.2 系数生成方法）／ 十六、风险与解决方案（联赛强度争议）

## 阶段目标

能读取 `league_strength_opta.yaml` 并把联赛强度作为**总分 10% 的轻量修正**参与评分。

## 输入 / 输出

| 项 | 内容 |
|----|------|
| 输入 | `league` 字段、`config/league_strength_opta.yaml` |
| 输出 | `league_strength_score` 字段（0-100） |
| 模块 | `league_strength.py` |

## 9.1 为什么采用 Opta Power Rankings

Opta Power Rankings 是 Opta / The Analyst 提供的全球球队强度评分体系，可比较不同国家和联赛中的球队水平。相比单独使用 UEFA 系数更适合本项目（需求含欧洲、南美和中国联赛）。

- 覆盖范围更适合本项目：可跨欧洲、南美、亚洲不同联赛比较。
- 足球数据行业认可度较高：Opta 是常见的专业数据来源。
- 更接近球探使用场景：来自球队能力评分平均值，而非只看洲际赛事名额。
- 可解释性较好：可解释为「该联赛球队整体能力水平的参考值」。

## 9.2 联赛强度系数生成方法

第一版**不直接调用 Opta API，也不自动抓取**，而是在配置文件中手动维护一份 `league_strength_opta.yaml`。系数根据 Opta 公布的联赛平均评分进行归一化。

归一化方法：

```
league_strength_score = 当前联赛 Opta 平均评分 / 最高联赛 Opta 平均评分 × 100
```

若以 Premier League 平均评分 92.6 作为最高基准：

```
Premier League = 92.6 / 92.6 × 100 = 100
Serie A        = 87.0 / 92.6 × 100 ≈ 94
La Liga        = 87.0 / 92.6 × 100 ≈ 94
Bundesliga     = 86.3 / 92.6 × 100 ≈ 93
Ligue 1        = 85.5 / 92.6 × 100 ≈ 92
```

## 联赛强度参考表

| 联赛 | Opta 参考平均评分 | 建议 league_strength_score | 说明 |
|------|------------------|---------------------------|------|
| Premier League | 92.6 | 100 | 作为第一版最高基准 |
| Serie A | 87.0 | 94 | Opta 2025 年文章提到与 La Liga 接近 |
| La Liga | 87.0 | 94 | 与 Serie A 接近 |
| Bundesliga | 86.3 | 93 | 略低于 Serie A / La Liga |
| Ligue 1 | 85.5 | 92 | 五大联赛中第五 |
| Brazil Serie A | 79.4 | 86 | 最高排名的非欧洲联赛之一 |
| Eredivisie | 78.8 | 85 | 荷甲，适合培养但整体强度低于五大联赛 |
| Argentina Primera | 78.6 | 85 | 阿根廷联赛，南美强联赛 |
| English Championship | 需从 Opta 更新 | 建议 84-86 | 第一版可先设 85 并标注待更新 |
| Belgian Pro League | 需从 Opta 更新 | 建议 80-83 | 第一版可先设 82 |
| Turkish Super Lig | 需从 Opta 更新 | 建议 78-82 | 第一版可先设 80 |
| Scottish Premiership | 需从 Opta 更新 | 建议 72-76 | 第一版可先设 74 |
| Chinese Super League | 需从 Opta 更新 | 建议 65-70 | 第一版可先设 68，明确为临时值 |

## 配置示例（league_strength_opta.yaml）

```yaml
source: "Opta Power Rankings / The Analyst"
last_reviewed: "2026-07-08"
note: "联赛强度仅作为总分 10% 的轻量修正，不代表对联赛水平的绝对判断。"
leagues:
  Premier League: 100
  Serie A: 94
  La Liga: 94
  Bundesliga: 93
  Ligue 1: 92
  Brazil Serie A: 86
  Eredivisie: 85
  Argentina Primera: 85
  Championship: 85
  Belgian Pro League: 82
  Turkish Super Lig: 80
  Scottish Premiership: 74
  Chinese Super League: 68
```

## 实现要点

- `league_strength.py` 读取配置，把球员的 `league` 映射到 `league_strength_score`。
- 找不到对应联赛时给出默认值或提示（避免 KeyError）。
- 该分数在阶段 4 的总分公式中占 **10%** 权重，切勿放大为决定性因素。

## 相关风险

| 风险 | 表现 | 解决方案 |
|------|------|----------|
| 联赛强度争议 | 不同机构排名不完全一致 | 第一版统一采用 Opta，并只占 10% 轻量权重 |

## 验收标准

- [ ] 每名正式评分球员具备 `league_strength_score`。
- [ ] 联赛强度在总分中权重约为 10%，不压倒球员个人表现。

## 参考来源

- Opta Analyst / The Analyst: *The Strongest Leagues in the World: Insights from the Opta Power Rankings* — https://theanalyst.com/articles/strongest-leagues-in-the-world-opta-power-rankings-june-2025
- Opta Analyst / The Analyst: *Strongest Leagues in World Football: Opta Power Rankings* — https://theanalyst.com/articles/strongest-football-leagues-in-the-world-opta-power-rankings
- UEFA National Associations / Association Club Coefficients — https://www.uefa.com/nationalassociations/
