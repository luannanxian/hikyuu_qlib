# 文档重组计划

**审计日期**: 2025-11-20
**总文档数**: 67 个 Markdown 文件
**审计目标**: 识别重复、过时、需要合并的文档

---

## 文档审计结果

### 📊 文档分布统计

| 位置 | 数量 | 说明 |
|------|------|------|
| 根目录 | 9 | 快速入门和参考文档 |
| docs/ | 10 | 核心文档 |
| docs/guides/ | 6 | 使用指南 |
| docs/integration/ | 8 | 集成文档 |
| docs/adapters/ | 1 | 适配器文档 |
| docs/archive/ | 32 | 历史归档文档 |
| docs/hikyuu-manual/ | 1 | Hikyuu API 参考 |

---

## 🔴 需要删除的文档 (过时/重复)

### 1. 根目录重复文档 (4 个)

#### ❌ IMPLEMENTATION_SUMMARY.md
**原因**: 与 `docs/IMPLEMENTATION_SUMMARY.md` 重复
**行动**: 删除,使用 docs/ 版本

#### ❌ PERFORMANCE_OPTIMIZATION.md
**原因**: 与 `docs/PERFORMANCE_OPTIMIZATION.md` 完全重复
**行动**: 删除根目录版本

#### ❌ BACKTEST_WORKFLOW.md
**原因**: 内容已被 `docs/WORKFLOW_GUIDE.md` 完全覆盖
**行动**: 删除

#### ❌ CLI_ENHANCEMENTS_SUMMARY.md
**原因**: CLI 增强已完成,内容过时
**行动**: 移至 `docs/archive/`

### 2. docs/ 下过时文档 (3 个)

#### ❌ docs/BUG_FIXES.md
**原因**: 历史 bug 修复记录,当前无参考价值
**行动**: 移至 `docs/archive/`

#### ❌ docs/predict_batch_implementation_summary.md
**原因**: 实现总结已过时,功能已稳定
**行动**: 移至 `docs/archive/`

#### ❌ docs/predict_batch_usage_example.md
**原因**: 示例已整合到 `WORKFLOW_GUIDE.md`
**行动**: 移至 `docs/archive/`

### 3. docs/integration/ 重复文档 (2 个)

#### ❌ docs/integration/EXECUTIVE_SUMMARY.md
**原因**: 内容已被 `QLIB_ENGINE_COMPLETE_STATUS.md` 覆盖
**行动**: 删除

#### ❌ docs/integration/VISUAL_SUMMARY.md
**原因**: 可视化总结已过时
**行动**: 移至 `docs/archive/`

---

## 🟡 需要合并的文档

### 1. 快速开始文档合并

**目标**: 统一快速开始体验

**需要合并的文档**:
- `QUICK_START.md` (根目录,14K,454行)
- `RUN.md` (根目录,3.5K,简化版)
- `QUICK_REFERENCE.md` (根目录,1.2K,命令参考)

**合并方案**:
```
新文档: docs/GETTING_STARTED.md
├─ 第1部分: 环境准备 (from QUICK_START)
├─ 第2部分: 快速开始 (from RUN.md)
├─ 第3部分: 命令参考 (from QUICK_REFERENCE)
└─ 第4部分: 下一步指引
```

**保留**: 根目录保留一个简化的 `QUICK_START.md` (300行内)作为快速入口

### 2. 实现总结文档合并

**目标**: 统一项目状态文档

**需要合并的文档**:
- `docs/IMPLEMENTATION_SUMMARY.md` (指数训练功能总结,362行)
- `docs/QLIB_ENGINE_COMPLETE_STATUS.md` (Qlib 引擎完整状态,443行)
- `docs/CLEANUP_FINAL_REPORT.md` (清理最终报告,282行)

**合并方案**:
```
新文档: docs/PROJECT_STATUS.md
├─ 第1部分: 项目概览
├─ 第2部分: 核心功能状态
│   ├─ Qlib 引擎状态
│   ├─ 指数训练功能
│   └─ 回测集成状态
├─ 第3部分: 代码质量
│   ├─ 源代码审计结果
│   └─ 清理总结
└─ 第4部分: 待办事项
```

### 3. 性能优化文档合并

**目标**: 统一性能优化指南

**需要合并的文档**:
- `docs/PERFORMANCE_OPTIMIZATION.md` (346行)
- `docs/archive/PERFORMANCE_ANALYSIS.md` (历史分析)

**合并方案**:
```
新文档: docs/PERFORMANCE_GUIDE.md
├─ 当前性能指标
├─ 优化建议
├─ 实施步骤
└─ 性能测试方法
```

### 4. 集成文档合并

**目标**: 简化集成文档结构

**需要合并的文档**:
- `docs/integration/HIKYUU_BACKTEST_INTEGRATION.md`
- `docs/integration/SIGNAL_CONVERSION_SOLUTION.md`
- `docs/adapters/CUSTOM_SG_QLIB_FACTOR.md`

**合并方案**:
```
新文档: docs/INTEGRATION_GUIDE.md
├─ Hikyuu 数据集成
├─ Qlib 训练集成
├─ Hikyuu 回测集成
├─ 信号转换方案
└─ CustomSG_QlibFactor 使用
```

---

## 🟢 需要更新的文档

### 1. README.md (根目录)

**当前问题**:
- 文档链接指向已删除/移动的文件
- 缺少最新功能说明

**更新内容**:
```markdown
# 更新文档链接
- ❌ 链接到已删除的文档
- ✅ 更新到重组后的文档

# 添加最新功能
- ✅ 指数成分股训练
- ✅ Hikyuu 真实回测集成
- ✅ 完整工作流支持

# 简化快速开始
- 3 步快速开始 (不超过 50 行)
- 链接到详细的 GETTING_STARTED.md
```

### 2. docs/README.md

**当前问题**:
- 作为文档索引,但未更新最新结构

**更新内容**:
```markdown
# 重新组织文档索引
## 快速开始
- 环境准备
- 安装指南
- 第一次运行

## 核心功能
- 工作流指南
- 指数训练指南
- 回测集成

## 高级主题
- 性能优化
- 架构设计
- API 参考

## 开发文档
- 贡献指南
- 测试指南
```

### 3. docs/WORKFLOW_GUIDE.md

**当前问题**:
- Troubleshooting 部分包含已修复的历史错误

**更新内容**:
```markdown
# 移除已修复的错误说明
- ❌ 删除 Error 1-5 (已修复)
- ✅ 保留常见问题 FAQ
- ✅ 更新为当前工作流状态
```

### 4. docs/INDEX_TRAINING_GUIDE.md

**当前问题**:
- 完整且最新,但需要添加更多示例

**更新内容**:
```markdown
# 添加实际案例
- 沪深300 全量训练案例
- 行业板块训练案例
- 自选股训练案例

# 添加性能对比
- 不同股票数量的训练时间
- 模型效果对比
```

---

## 📁 重组后的文档结构

```
project_root/
├── README.md                    ✅ 项目主页 (简化,<100行)
├── QUICK_START.md               ✅ 快速开始 (简化,<300行)
└── docs/
    ├── README.md                ✅ 文档索引
    ├── GETTING_STARTED.md       🆕 详细入门指南 (合并3个文档)
    ├── PROJECT_STATUS.md        🆕 项目状态 (合并3个文档)
    ├── INTEGRATION_GUIDE.md     🆕 集成指南 (合并3个文档)
    ├── PERFORMANCE_GUIDE.md     🆕 性能优化指南
    ├── WORKFLOW_GUIDE.md        ✅ 工作流指南 (更新)
    ├── INDEX_TRAINING_GUIDE.md  ✅ 指数训练指南 (更新)
    ├── SOURCE_CODE_AUDIT.md     ✅ 源代码审计
    ├── CLEANUP_SUMMARY.md       ✅ 清理总结
    ├── design.md                ✅ 架构设计
    ├── prd.md                   ✅ 产品需求
    ├── requirements.md          ✅ 技术需求
    ├── backtest_guide.md        ✅ 回测指南
    ├── guides/                  📁 使用指南
    │   ├── BATCH_TRAINING_GUIDE.md
    │   ├── CLI_USER_GUIDE.md
    │   ├── COMPLETE_USER_GUIDE.md
    │   ├── INDEX_CONSTITUENTS_GUIDE.md
    │   └── MODEL_TRAINING_DATA_LOADING_GUIDE.md
    ├── integration/             📁 集成技术文档
    │   ├── ARCHITECTURE_VALIDATION_REPORT.md
    │   ├── IMPLEMENTATION_PRIORITY_MATRIX.md
    │   ├── SIGNAL_ADAPTER_DESIGN.md
    │   └── README.md
    ├── adapters/                📁 适配器文档 (保留)
    ├── hikyuu-manual/           📁 Hikyuu API 参考 (保留)
    └── archive/                 📁 历史归档 (32+7 个文档)
        ├── [所有历史文档]
        ├── BUG_FIXES.md         🔄 移入
        ├── CLI_ENHANCEMENTS_SUMMARY.md 🔄 移入
        └── ...
```

---

## 执行计划

### Phase 1: 删除重复文档 (立即执行)

```bash
# 删除根目录重复文档
rm BACKTEST_WORKFLOW.md
rm IMPLEMENTATION_SUMMARY.md
rm PERFORMANCE_OPTIMIZATION.md

# 移动过时文档到归档
mv CLI_ENHANCEMENTS_SUMMARY.md docs/archive/
mv docs/BUG_FIXES.md docs/archive/
mv docs/predict_batch_implementation_summary.md docs/archive/
mv docs/predict_batch_usage_example.md docs/archive/

# 删除集成文档重复
rm docs/integration/EXECUTIVE_SUMMARY.md
mv docs/integration/VISUAL_SUMMARY.md docs/archive/
```

**减少文档数**: 67 → 59 (-8 个)

### Phase 2: 合并文档 (需要编辑)

**优先级 P0 (核心文档)**:
1. 合并快速开始文档 → `docs/GETTING_STARTED.md`
2. 合并项目状态文档 → `docs/PROJECT_STATUS.md`

**优先级 P1 (重要但不紧急)**:
3. 合并性能文档 → `docs/PERFORMANCE_GUIDE.md`
4. 合并集成文档 → `docs/INTEGRATION_GUIDE.md`

### Phase 3: 更新文档 (需要编辑)

**优先级 P0**:
1. 更新 `README.md` - 修复链接,简化内容
2. 更新 `QUICK_START.md` - 简化为快速入口 (<300行)

**优先级 P1**:
3. 更新 `docs/README.md` - 重新组织文档索引
4. 更新 `docs/WORKFLOW_GUIDE.md` - 移除历史错误

**优先级 P2**:
5. 更新 `docs/INDEX_TRAINING_GUIDE.md` - 添加案例

---

## 预期效果

### 文档数量优化

| 阶段 | 文档数 | 变化 |
|------|--------|------|
| 当前 | 67 | - |
| Phase 1 完成 | 59 | -8 (删除/归档) |
| Phase 2 完成 | 51 | -8 (合并) |
| 最终 | 51 | -16 总计 |

### 文档质量提升

✅ **结构优化**:
- 清晰的文档层次
- 明确的入口点
- 逻辑的组织方式

✅ **用户体验**:
- 快速找到所需文档
- 避免重复和混淆
- 最新准确的内容

✅ **维护性**:
- 减少重复维护
- 集中更新点
- 历史文档归档

---

## 立即执行建议

基于当前状态,建议**立即执行 Phase 1**:

```bash
cd /Users/zhenkunliu/project/hikyuu_qlib

# 删除根目录重复文档
rm BACKTEST_WORKFLOW.md IMPLEMENTATION_SUMMARY.md PERFORMANCE_OPTIMIZATION.md

# 移动过时文档
mv CLI_ENHANCEMENTS_SUMMARY.md docs/archive/
mv docs/BUG_FIXES.md docs/archive/
mv docs/predict_batch_implementation_summary.md docs/archive/
mv docs/predict_batch_usage_example.md docs/archive/

# 删除集成文档重复
rm docs/integration/EXECUTIVE_SUMMARY.md
mv docs/integration/VISUAL_SUMMARY.md docs/archive/

# 验证
echo "剩余文档数:"
find docs/ -name "*.md" | wc -l
find . -maxdepth 1 -name "*.md" | wc -l
```

**Phase 2-3** 需要内容编辑,建议逐步执行。

---

**审计完成**: 识别出 16 个需要处理的文档,建议分 3 个阶段执行
