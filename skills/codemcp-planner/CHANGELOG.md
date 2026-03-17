# Changelog

All notable changes to the CodeMCP Planner Skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-17

### 🎉 增强版发布

#### 新增功能
- **项目记忆文件系统**: 每个项目自动创建 `memory.md` 记录完整历史
- **统一配置管理**: `.codemcp-config.json` 保管所有认证信息和设置
- **用户沟通批准机制**: 充分沟通后用户批准才执行计划
- **CodeMCP连接健康监控**: 实时检测服务器状态和连接可用性
- **流式管理与状态汇报**: CLI命令监控和实时状态汇报

#### 新增工具脚本
- `scripts/codemcp_planner_enhanced_fixed.sh` - 增强版工作流管理器
- `start_enhanced.sh` - 增强版启动脚本（包含依赖检查）
- `test_enhanced_features.sh` - 增强版功能测试脚本
- `ENHANCED_FEATURES_SUMMARY.md` - 增强版功能总结文档

#### 文档更新
- 更新 `SKILL.md` 包含完整增强版功能说明
- 更新 `README.md` 添加增强版使用指南
- 新增工作流程图和API参考文档
- 完善故障排除和最佳实践指南

#### 技术改进
- 改进错误处理和用户反馈
- 优化配置管理和类型安全
- 增强连接检测和自动修复
- 改进脚本性能和可靠性

#### 向后兼容性
- 完全兼容 v1.0.0 的标准版功能
- 增强版功能可选择性使用
- 配置文件自动迁移支持
- 所有现有脚本保持兼容

## [1.0.0] - 2026-03-16

### 🚀 初始发布

#### 核心功能
- **结构化计划管理**: 四层数据模型 (System → Block → Feature → Test)
- **AI协同工作流**: 任务分发、多Agent协调、状态监控
- **自动化流程**: 自动Git提交、进度报告生成、失败处理
- **开发者友好**: 简单CLI、问题报告、透明沟通

#### 工具脚本
- `scripts/codemcp_planner.sh` - 主工作流管理器
- `scripts/create_plan_template.sh` - 计划模板创建工具
- `scripts/monitor_tasks.sh` - 任务监控工具
- `scripts/auto_git_commit.sh` - 自动Git提交工具
- `scripts/generate_report.sh` - 进度报告生成工具
- `scripts/check_environment.sh` - 环境检查工具
- `scripts/start_services.sh` - 服务启动工具
- `scripts/problem_report.sh` - 问题报告工具

#### 文档结构
- `SKILL.md` - 主技能定义文档
- `README.md` - 项目说明文档
- `LICENSE` - MIT许可证
- `PACKAGE_SUMMARY.md` - 技能包总结
- 完整的使用示例和API参考

## 版本说明

### 版本命名规则
- **主版本号 (2.x.x)**: 不兼容的API变更或重大功能更新
- **次版本号 (x.1.x)**: 向后兼容的功能性新增
- **修订号 (x.x.1)**: 向后兼容的问题修正

### 升级指南
- **从 1.x.x 升级到 2.0.0**: 增强版功能需要重新初始化项目配置
- **配置迁移**: 旧版配置文件可自动迁移到新版格式
- **功能兼容**: 所有v1.0.0功能在v2.0.0中完全可用

### 支持周期
- **v2.0.0**: 长期支持版本 (LTS)，支持到2027-03-17
- **v1.0.0**: 维护版本，关键安全修复到2026-06-17

## 未来计划

### 短期目标 (v2.1.0)
- [ ] 完善用户沟通和批准流程
- [ ] 集成CodeMCP任务发送功能
- [ ] 添加更多配置模板和示例
- [ ] 优化错误处理和用户反馈

### 中期目标 (v3.0.0)
- [ ] 支持多项目并行管理
- [ ] 集成更多AI agent平台
- [ ] 提供Web管理界面
- [ ] 实现自动化测试和部署

### 长期愿景
- [ ] 完整的AI协同开发生态系统
- [ ] 跨平台支持和云集成
- [ ] 智能优化和预测分析
- [ ] 社区驱动的功能扩展

## 贡献者

感谢所有为这个项目做出贡献的人！

### 核心团队
- **OpenClaw AI** - 项目创建和维护
- **CodeMCP Team** - 技术支持和集成

### 特别感谢
- 所有测试用户和反馈提供者
- 开源社区的支持和贡献
- 技术文档的编写和维护者

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

*此变更日志文件遵循 [Keep a Changelog](https://keepachangelog.com/) 格式，使用 [Semantic Versioning](https://semver.org/) 进行版本控制。*