# {{ player_name }} · 潜力评估报告

> 自动生成 | 2026-07-10 | 数据来源：FBref + Transfermarkt + FIFA

---

## 1. 球员基本信息

| 属性 | 值 |
|------|-----|
| 姓名 | {{ player_name }} |
| 年龄 | {{ age }} 岁 |
| 位置 | {{ standard_position }} |
| 球队 | {{ team }} |
| 联赛 | {{ league }} |
| 国籍 | {{ nation }} |
| 身高 | {{ height }} |
| 体重 | {{ weight }} |
| 身价 | {{ market_value }} |
| FIFA 总评 | {{ fifa_overall }} |
| FIFA 潜力 | {{ fifa_potential }} |

## 2. 当前表现概况

| 指标 | 数值 |
|------|------|
| 出场时间 | {{ minutes }} 分钟 |
| 进球 | {{ goals }} |
| 助攻 | {{ assists }} |
| 射门 | {{ shots }} |
| 关键传球 | {{ key_passes }} |
| 过人 | {{ dribbles }} |
| 传球 | {{ passes }} |
| 抢断 | {{ tackles }} |
| 拦截 | {{ interceptions }} |
| 黄牌 | {{ yellow_cards }} |
| 红牌 | {{ red_cards }} |

### per90 效率

| 指标 | 每 90 分钟 |
|------|-----------|
| 进球 | {{ goals_per90 }} |
| 助攻 | {{ assists_per90 }} |
| 射门 | {{ shots_per90 }} |
| 关键传球 | {{ key_passes_per90 }} |
| 过人 | {{ dribbles_per90 }} |
| 抢断 | {{ tackles_per90 }} |
| 拦截 | {{ interceptions_per90 }} |
| 预期进球 (xG) | {{ xg_per90 }} |
| 预期助攻 (xA) | {{ xa_per90 }} |
| 推进带球 | {{ progressive_carries_per90 }} |
| 射门创造动作 | {{ shot_creating_actions_per90 }} |

## 3. 潜力评分解释

| 分项 | 得分 | 权重 | 说明 |
|------|------|------|------|
| 年龄优势 | {{ age_score }} | 15% | 越年轻且能获得稳定出场，稀缺性越高 |
| 出场可靠性 | {{ reliability_score }} | 15% | 分钟数越充分，数据越稳定 |
| 同位置核心表现 | {{ core_performance }} | 45% | {{ standard_position }} 组内百分位排名加权 |
| 场上行为风格 | {{ behavior_score }} | 15% | 攻防主动性 + 推进 + 纪律性 |
| 联赛强度 | {{ league_score }} | 10% | Opta Power Rankings {{ league }} 联赛系数 |
| 风险扣分 | {{ risk_penalty }} | — | 黄牌、红牌、数据完整度、样本量 |
| **总分** | **{{ total_score }}** | — | **潜力评分（0-100）** |

排名：第 {{ rank }} / {{ total_players }} 名（正式评分球员）

## 4. 主要优势

{{ strengths }}

## 5. 主要短板

{{ weaknesses }}

## 6. 场上行为风格画像

本分析仅基于比赛统计数据的场上行为倾向，不构成心理诊断。

{{ behavior_profile }}

## 7. 发展风险

{{ risks }}

## 8. 适合的球队或战术类型

基于数据谨慎判断，{{ player_name }}（{{ standard_position }}）的场上特征可能适合：

{{ tactical_fit }}

## 9. 一句话总结

{{ one_liner }}

## 10. 数据限制说明

{{ data_limitations }}

---

*本报告由自动化管线生成。数据来源为 FBref / Transfermarkt / FIFA 游戏数据（2024-25 赛季）。评分模型按位置分组计算同位置百分位。数据不足时结论需谨慎。*
