# Bio Pharma Suite（生物医药 · 食药检验检疫 合规套件）

基于 ERPNext v16 质量模块的 **GMP 扩展补充层**。零侵入：不改官方代码，全部经
doc_events 钩子、fixtures 字段注入、Custom Sidebar 导航增量实现。

## 一、快速指引（按角色）

### QC 检验员（日常）
1. 收样：Quality 模块 → 生物医药套件 → 实验室样品 新建
   - 扫码字段自动生成（条码=样品号，二维码=表单链接）
   - 提交门禁：必须至少一行检验项目；引用的检验方法必须"生效中"
2. 检测：在"检验项目"子表填方法/仪器/结果/结论
3. 流转交接：表单内"流转记录"子表逐次登记；移动端可用
   bio_pharma_suite.lims.api.log_custody_handover 扫码交接
4. 标签打印：Lab Sample Label 打印格式（含二维码）

### QA 专员（体系运行）
- 受控文件：SOP/规程全生命周期（起草→审核→批准→生效→作废），版本受控
- 主配方 + 主配方版本：工艺文件版本管理；工单强制引用受控配方
- 批生产记录：从工单/工卡/质检自动汇编
- 温区/温度日志/温度越限：冷链监控；越限自动冻结批次

### 质量受权人 QP（放行）
- 批次放行双签（制备人 + QP 电子签名）
- 放行前自动核验：全部检验合格 + 无未闭环偏差 + 法规证照有效 + 无未处置越限

### 系统管理员
- 数据完整性设置：电子签名开关、复核规则
- 原因代码：放行否决/偏差分类/让步处置的标准化用语
- 法规库 + 法规条款：条款以子表挂在法规库下维护（不在侧边栏单独入口）

## 二、文档体系对照表

| 套件 DocType | GMP 文件类别 | 说明 |
|---|---|---|
| Controlled Document | 质量手册/程序文件/SOP/记录模板 | document_tier 四级分层 |
| Master Formula (+Version) | 工艺规程/主配方 | 版本受控，工单强制引用 |
| Batch Production Record | 批生产记录 | 自动汇编 |
| Regulation Library (+Clause) | 法规/标准原文条款库 | Controlled Document 可引用 |
| Test Method | 检验方法 | QI 引用生效版本 |
| Reason Code | 记录用语标准化（ALCOA+） | — |

## 三、体系差距分析（诚实清单）

本套件是扩展层，不是完整 QMS。

### 已覆盖
文件受控、工艺配方版本、批生产记录、样品全生命周期（含条码）、
冷链温控与越限冻结、批放行双签门禁、法规条款库、电子签名标记、审计追踪（框架级）

### 部分覆盖（官方有基础，需深化）
- 偏差/CAPA/OOS：官方 Non Conformance / Quality Action 有基础，
  缺 GMP 级根因分析(RCA)向导、CAPA 有效性检查计划
- 培训管理：官方 HRMS 有培训模块；文件分发与培训确认未打通
- 供应商审计：官方有 Supplier Scorecard；缺 GMP 审计计划/报告模板

### 未覆盖（路线图）
- 实验室安全体系（ISO/IEC 17025 / GB 19489 生物安全）：危废台账、
  试剂 MSDS 关联、生物风险评估、实验室事故上报——建议 Phase 4，
  可复用官方 Incident/Asset 模块扩展
- 稳定性研究自动化（ICH Q1A）：方案/时间点矩阵/OOT 统计（已预留设计）
- 验证主计划 VMP：设备/工艺/清洁验证生命周期管理
- 数据完整性技术控制（ALCOA+）：当前电子签名为 Check+审计追踪，
  距 21 CFR Part 11 完整合规（独立签名实体、签名含义绑定）尚有距离

## 四、多语言
translations/zh.csv（215 词条）。守卫消息待改为 _() 包裹后补词条。

## 五、开发约定
- 零侵入：禁改 frappe/erpnext 源码；扩展一律走 hooks/fixtures/patch
- 类名规则：Frappe 按去空格字面推导（Chain of Custody → ChainofCustody）
- 导航：v16 工作区放 <module>/workspace/<name>/；侧边栏用 Custom Sidebar fixtures
