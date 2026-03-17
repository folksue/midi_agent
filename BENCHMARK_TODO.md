# Benchmark TODO (Music Reasoning, 8 Tasks, 3 Tokenizers)

## 0. 目标与边界
- 目标: 构建可复现 benchmark，覆盖 8 个音乐推理任务。
- 使用方式: **zero-shot 评测为主**，不做 train/dev/test 训练划分。
- 同一题目内容导出为 3 种 token 视图:
  - `note_level` (基准表示，沿用现有 note 表达)
  - `midilike`
  - `remilike`
- 题目语义与答案保持一致，仅音符表示方式替换。
- Ground truth 采用 rule-based 生成，保证可自动验证。

## 1. 任务集合 (V1)
- Task 1: Interval Identification
- Task 2: Chord Identification
- Task 3: Harmonic Function Classification
- Task 4: Transposition
- Task 5: Melodic Inversion
- Task 6: Retrograde
- Task 7: Rhythmic Augmentation / Diminution
- Task 8: Voice-Leading Violation Detection (`parallel_fifths`, `voice_crossing`)

### 1.1 任务分组（按输出类型）

#### A. Label Classification（输出不需要 notes 序列）
- Task 1: Interval Identification
- Task 2: Chord Identification
- Task 3: Harmonic Function Classification
- Task 8: Voice-Leading Violation Detection

建议输出字段:
- `prediction_label`（字符串）

#### B. Note Sequence Transformation（输出需要 notes 序列）
- Task 4: Transposition
- Task 5: Melodic Inversion
- Task 6: Retrograde
- Task 7: Rhythmic Augmentation / Diminution

建议输出字段:
- `prediction_notes`（与 tokenizer 视图一致的音符序列表示）
- 可选 `prediction_structured`（反解后的结构化 notes，便于评测）

## 2. 数据规范
- 新建目录: `benchmark/`
- 计划结构:
  - `benchmark/specs/` 任务定义与标签空间
  - `benchmark/core/` 规则引擎与音乐基础工具
  - `benchmark/tokenizers/` 三种 tokenizer 实现
  - `benchmark/data/raw_note_level/` note-level 原始样本
  - `benchmark/data/views/{note_level,midilike,remilike}/` 导出视图
  - `benchmark/eval/` 指标与评测器
  - `benchmark/scripts/` 生成/导出/评测 CLI
- 样本格式 (JSONL):
  - 通用字段: `id`, `task`, `input`, `target`, `meta`
  - `input` 内包含音乐对象 (note/chord/melody/key/pivot/factor 等)
  - `target` 为该任务标准答案

## 3. Rule-Based Ground Truth 引擎
- 音名/音高转换: note name <-> midi pitch <-> pitch class
- Interval 判定: 半音差 + 字母距离 -> 标准音程名
- Chord 模板匹配: major/minor/dim/aug/dom7
- Harmonic function: 大调 3 类映射 (tonic/predominant/dominant)
- Melody 变换:
  - Transposition
  - Inversion (2c - p)
  - Retrograde
  - Rhythm scale (augment/diminish)
- Voice-leading 检测:
  - parallel fifths
  - voice crossing

## 4. Tokenizer 视图转换
- 基准: `note_level` (保留现有表达)
- `midilike` 转换规则 (rule-based)
- `remilike` 转换规则 (rule-based)
- 约束:
  - 三视图 `id/task/target` 一致
  - 仅 `input` 音符字段的字符串表示不同
- 校验脚本:
  - `id` 对齐
  - 反解后音乐语义一致 (pitch/duration/onset)

## 5. 评测指标
- Task 1/2/3/6: exact match accuracy
- Task 2 可选: root accuracy / quality accuracy
- Task 3: macro F1
- Task 4: pitch accuracy, sequence exact match, interval preservation, rhythm preservation
- Task 5: pitch accuracy, exact sequence match
- Task 7: duration accuracy, exact sequence match, bar-validity rate
- Task 8: exact match accuracy, macro F1
- 输出:
  - 总表 (`overall.json`)
  - 分任务 (`by_task.json`)
  - 分 tokenizer (`by_tokenizer.json`)

## 6. CLI 脚本计划
- `benchmark/scripts/gen_note_level.py`
  - 生成 8 任务 note-level 原始数据
- `benchmark/scripts/export_views.py`
  - 从 note-level 导出 `midilike/remilike`
- `benchmark/scripts/validate_views.py`
  - 三视图一致性检查
- `benchmark/scripts/eval_predictions.py`
  - 对模型输出做评测，产出指标

## 7. 首版数据规模建议
- 每任务样本量 (可调整):
  - eval: 200
- 首版优先保证规则正确与可重复，规模第二步放大。

## 8. 里程碑
- M1: 核心规则引擎 + Task 1/2/4 可生成可评测
- M2: 8 任务全部可生成 + note-level 全链路
- M3: midilike/remilike 导出 + 视图一致性校验
- M4: 全任务评测脚本 + 报表

## 9. 验收清单
- [ ] 8 任务均可自动生成 `note_level` 数据
- [ ] 三 tokenizer 视图成功导出且通过一致性校验
- [ ] 评测脚本可对任意任务/全任务输出指标
- [ ] 提供最小可运行示例命令
- [ ] 文档包含字段定义、标签定义、指标定义

## 10. 待你确认的设计点
- [ ] `midilike` 与 `remilike` 的具体 token 语法最终版
- [ ] 每任务样本规模
- [ ] 是否先只做大调语境 (Task 3)
- [ ] Voice-leading 是否先限定两声部再扩到 SATB
