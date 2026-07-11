# YouthPlayerPotentialDiscoverySystem

年轻球员潜力发现与报告生成系统。基于 FBref + Transfermarkt + FIFA 多源数据，对五大联赛 U21 球员进行分位置潜力评分（0-100），自动生成排行榜、雷达图、Markdown/DOCX 球员报告。

## 技术栈

- **语言**: Python 3.14
- **数据**: pandas, numpy, PyYAML
- **可视化**: matplotlib（雷达图）
- **文档导出**: python-docx, openpyxl
- **数据源**: Kaggle（emrey3lmaz FBref + davidcariboo TM + jacksonjohannessen FIFA）
- **测试**: pytest（86 个测试）

## 项目结构

```
Project4Nathon/
├── main.py                    # 管线入口：python main.py [--skip-collect]
├── config/                    # YAML 配置文件
│   ├── config.yaml            # 全局参数
│   ├── field_mapping.yaml     # 外部列名→内部标准字段名
│   ├── league_mapping.yaml    # 联赛名归一化
│   ├── position_mapping.yaml  # Transfermarkt 位置→标准分组
│   ├── scoring_weights.yaml   # 分位置评分权重 + 风险扣分规则
│   └── league_strength_opta.yaml # Opta Power Rankings 联赛系数
├── src/
│   ├── config_loader.py       # YAML 加载
│   ├── collector.py           # 数据采集 + FBref↔TM↔FIFA 姓名匹配
│   ├── data_loader.py         # 数据读取 + 三级字段检查
│   ├── cleaner.py             # 清洗管线（年龄/分钟/去重/位置映射）
│   ├── position_mapper.py     # 位置映射（TM优先→FBref启发式兜底）
│   ├── feature_builder.py     # per90 指标计算（含欧洲小数格式修复）
│   ├── scorer.py              # 0-100 潜力评分（分位置百分位 + 风险扣分）
│   ├── league_correction.py   # Opta 联赛强度修正
│   ├── ranker.py              # 排行榜生成（CSV + Excel + MD）
│   ├── chart_builder.py       # 雷达图生成（matplotlib 极坐标）
│   └── report_generator.py    # 球员报告生成（MD + DOCX）
├── tests/                     # pytest 测试
├── data/
│   ├── raw/players.csv        # 原始数据（2854 球员，190+ 列）
│   └── processed/
│       ├── cleaned_players.csv   # 清洗后（508 U21球员）
│       └── scored_players.csv    # 评分后（186 人正式评分）
├── outputs/
│   ├── rankings/              # 排行榜（CSV/Excel/MD）
│   ├── charts/                # 雷达图 PNG
│   └── reports/
│       ├── reports_md/        # Markdown 报告
│       └── reports_docx/      # DOCX 报告
├── templates/
│   └── player_report.md       # 报告模板（10 章节）
└── docs/                      # 设计文档 + 分析文档
    ├── 00-总览与架构.md
    ├── 阶段0-9-*.md            # 各阶段设计文档
    ├── 01-当前进度与下一步计划.md  # 旧版进度
    ├── 02-Top50潜力榜分析.md
    ├── 03-改进建议.md
    └── 04-当前进度与下一步计划.md  # 最新进度（阶段0-8完成）
```

## 管线流程（8 个阶段）

```
阶段0 数据采集 → 阶段1 字段检查 → 阶段2 清洗+位置映射
→ 阶段3 特征计算(per90) → 阶段4 潜力评分(0-100)
→ 阶段5 联赛强度修正(Opta) → 阶段6 排行榜
→ 阶段7 雷达图 → 阶段8 报告生成
```

运行：`python main.py --skip-collect`（首次需去掉 `--skip-collect` 下载 Kaggle 数据集）

## 评分公式

```
total_score = 年龄优势×15% + 出场可靠性×15% + 同位置核心表现×45%
            + 行为风格×15% + 联赛强度(Opta)×10% - 风险扣分(0~-10)
```

- 同位置核心表现：分位置（Winger/AM/CM/DM）内部百分位排名
- 联赛强度：Opta Power Rankings（PL=100, Liga=94, SerieA=94, BL=93, L1=92）
- 风险扣分：数据完整度低(-2) + 黄牌多(-2) + 红牌(-3) + 样本不足(-3)

## 已知注意事项

1. **欧洲小数格式**：FBref 数据集 xg/xa 等列用逗号做小数点（`9,8`=9.8），`feature_builder.py` 的 `_safe_numeric()` 已处理
2. **TM 匹配用纯姓名**：Transfermarkt 俱乐部名为德语全名（如 "1. Fußball-Club Köln"），与 FBref 英文短名几乎无交集，`attach_transfermarkt_data()` 使用纯姓名模糊匹配（92% 匹配率）
3. **League 名需归一化**：Kaggle 数据集用 "ENG-Premier League" 格式，`league_mapping.yaml` + `stage2_clean` 中归一化为 "Premier League"
4. **Windows 编码**：`main.py` 设置了 `sys.stdout` 为 UTF-8，避免重音球员名打印报错
5. **GitHub Push**：数据集文件较大（2.4MB CSV），需 `git config http.postBuffer 524288000`

## 当前 Top 5（2024-25 赛季，186 人正式评分）

| # | 球员 | 位置 | 联赛 | 年龄 | 总分 |
|---|------|------|------|------|------|
| 1 | Lamine Yamal | Winger | La Liga | 17 | 91.7 |
| 2 | Florian Wirtz | AM | Bundesliga | 21 | 88.0 |
| 3 | Sávio | Winger | Premier League | 20 | 86.9 |
| 4 | Désiré Doué | Winger | Ligue 1 | 19 | 86.6 |
| 5 | Rayan Cherki | AM | Ligue 1 | 20 | 86.5 |
