# 工作流程图

## 整体工作流

```mermaid
graph TD
    A[用户需求] --> B[需求分析]
    B --> C[创建结构化计划]
    C --> D[用户审阅批准]
    D --> E[启动CodeMCP服务]
    E --> F[发送任务流]
    F --> G[Executor AI执行]
    G --> H{监控状态}
    H -->|任务完成| I[自动Git提交]
    H -->|任务失败| J[重新规划]
    I --> K[生成进度报告]
    J --> F
    K --> L[用户反馈]
    L --> M{继续开发?}
    M -->|是| G
    M -->|否| N[项目完成]
```

## 四层数据模型

```mermaid
graph TD
    A[System 系统] --> B[Block 模块]
    B --> C[Feature 功能]
    C --> D[Test 测试]
    
    A1[用户管理系统] --> B1[用户认证]
    A1 --> B2[用户管理]
    A1 --> B3[API接口]
    
    B1 --> C1[用户注册]
    B1 --> C2[用户登录]
    B1 --> C3[会话管理]
    
    C1 --> D1[pytest tests/test_registration.py]
    C2 --> D2[pytest tests/test_login.py]
    C3 --> D3[pytest tests/test_session.py]
```

## 任务执行流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant P as Planner
    participant C as CodeMCP
    participant E as Executor
    participant G as Git

    U->>P: 提供需求
    P->>P: 分析需求
    P->>P: 创建计划
    P->>U: 发送计划审阅
    U->>P: 批准计划
    
    P->>C: 启动服务
    P->>C: 发送任务流
    C->>E: 分配任务
    E->>E: 执行开发
    E->>C: 返回结果
    
    loop 监控循环
        P->>C: 查询状态
        C->>P: 返回状态
        P->>G: 检查代码变更
        alt 有变更
            P->>G: 自动提交
            P->>U: 发送进度报告
        end
    end
    
    E->>C: 任务完成
    C->>P: 通知完成
    P->>U: 项目完成报告
```

## 失败处理流程

```mermaid
graph TD
    A[任务执行] --> B{执行结果}
    B -->|成功| C[继续下一个任务]
    B -->|失败| D[记录失败信息]
    D --> E[分析失败原因]
    E --> F{失败类型}
    F -->|测试失败| G[修复测试]
    F -->|代码错误| H[修复代码]
    F -->|环境问题| I[修复环境]
    F -->|需求不明确| J[重新沟通需求]
    
    G --> K[重新规划任务]
    H --> K
    I --> K
    J --> L[与用户沟通]
    L --> M[更新需求]
    M --> K
    
    K --> N[细化任务颗粒度]
    N --> O[调整优先级]
    O --> P[重新发送任务]
    P --> A
```

## 自动Git提交流程

```mermaid
graph TD
    A[开始监控] --> B[检查Git状态]
    B --> C{有代码变更?}
    C -->|否| D[等待下次检查]
    C -->|是| E[分析变更类型]
    
    E --> F{变更类型}
    F -->|新功能| G[生成feat提交]
    F -->|Bug修复| H[生成fix提交]
    F -->|文档更新| I[生成docs提交]
    F -->|代码重构| J[生成refactor提交]
    F -->|其他| K[生成chore提交]
    
    G --> L[创建提交消息]
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M[执行Git提交]
    M --> N{有远程仓库?}
    N -->|是| O[推送到远程]
    N -->|否| P[仅本地提交]
    
    O --> Q[记录提交信息]
    P --> Q
    Q --> R[通知用户]
    R --> D
    
    D --> S[等待间隔时间]
    S --> B
```

## 进度报告生成流程

```mermaid
graph TD
    A[触发报告生成] --> B[收集数据]
    
    B --> C[系统状态]
    B --> D[任务进度]
    B --> E[代码统计]
    B --> F[问题记录]
    B --> G[用户反馈]
    
    C --> H[生成报告章节]
    D --> H
    E --> H
    F --> H
    G --> H
    
    H --> I[格式化报告]
    I --> J{输出格式}
    J -->|Markdown| K[生成.md文件]
    J -->|HTML| L[生成.html文件]
    J -->|JSON| M[生成.json文件]
    
    K --> N[保存报告]
    L --> N
    M --> N
    
    N --> O{发送通知?}
    O -->|是| P[发送通知]
    O -->|否| Q[仅保存]
    
    P --> R[用户接收报告]
    Q --> S[报告存档]
    
    R --> T[报告流程完成]
    S --> T
```

## 环境检查流程

```mermaid
graph TD
    A[开始检查] --> B[检查系统信息]
    B --> C[检查Git]
    C --> D[检查Python]
    D --> E[检查CodeMCP]
    E --> F[检查服务状态]
    F --> G[检查网络]
    G --> H[检查磁盘]
    H --> I[检查环境变量]
    
    I --> J[生成检查结果]
    J --> K{所有检查通过?}
    K -->|是| L[显示成功信息]
    K -->|否| M[显示失败信息]
    
    L --> N[建议下一步]
    M --> O[显示修复建议]
    
    N --> P[生成检查报告]
    O --> P
    
    P --> Q{保存报告?}
    Q -->|是| R[保存报告文件]
    Q -->|否| S[仅显示结果]
    
    R --> T[检查完成]
    S --> T
```

## 问题报告流程

```mermaid
graph TD
    A[发现问题] --> B[停止当前操作]
    B --> C[记录错误信息]
    C --> D[收集环境信息]
    D --> E[分析可能原因]
    E --> F[整理问题报告]
    
    F --> G[使用模板格式化]
    G --> H[生成问题报告]
    H --> I[保存报告文件]
    I --> J[发送给用户]
    
    J --> K[等待用户指示]
    K --> L{用户回复}
    L -->|提供解决方案| M[执行解决方案]
    L -->|要求更多信息| N[补充信息]
    L -->|忽略问题| O[记录并继续]
    
    M --> P[验证解决方案]
    P --> Q{解决成功?}
    Q -->|是| R[记录解决方案]
    Q -->|否| S[重新分析问题]
    
    R --> T[问题解决]
    N --> J
    S --> E
    O --> U[跳过问题]
    
    T --> V[继续工作流]
    U --> V
```

## 集成工作流

```mermaid
graph LR
    A[OpenClaw] --> B[CodeMCP Planner]
    B --> C[CodeMCP平台]
    C --> D[Executor AI]
    C --> E[Executor AI]
    C --> F[Executor AI]
    
    D --> G[Git仓库]
    E --> G
    F --> G
    
    B --> H[进度报告]
    B --> I[用户通知]
    
    G --> J[CI/CD流水线]
    J --> K[测试环境]
    J --> L[生产环境]
    
    H --> M[用户仪表板]
    I --> N[消息通知]
    
    M --> O[项目监控]
    N --> P[实时反馈]
    
    O --> Q[决策支持]
    P --> Q
```

这个文档提供了CodeMCP Planner Skill的完整工作流程图，包括：
1. 整体工作流
2. 四层数据模型
3. 任务执行流程
4. 失败处理流程
5. 自动Git提交流程
6. 进度报告生成流程
7. 环境检查流程
8. 问题报告流程
9. 集成工作流

所有图表都使用Mermaid语法，可以在支持Mermaid的Markdown查看器中正确显示。