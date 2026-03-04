# 湖南生元律师事务所管理系统 /Hunan Shengyuan Law Firm Management System

![Vue3](https://img.shields.io/badge/Frontend-Vue%203-brightgreen) ![FastAPI](https://img.shields.io/badge/Backend-FastAPI-blue) ![MySQL](https://img.shields.io/badge/Database-MySQL-orange) ![License](https://img.shields.io/badge/License-Proprietary-red)

##  项目简介 / Project Overview

本项目为**湖南生元律师事务所**定制的综合性数字化管理系统。系统致力于实现律所业务流程的全面线上化，涵盖案件的全生命周期管理、律师人事管理、财务开票、电子卷宗归档、党建工作记录以及电子用印审批等核心业务场景。通过引入数据可视化大盘，显著提升了律所的协同办公效率与数字化运营水平。

This project is a customized comprehensive digital management system for **Hunan Shengyuan Law Firm**. It digitizes core business processes including case lifecycle management, personnel, finance, archiving, and seal approvals, enhancing collaborative efficiency through data visualization.

---

##  技术栈 / Tech Stack

### 前端 / Frontend
- **核心框架**: Vue 3 + Vite
- **状态管理与路由**: Pinia + Vue Router
- **UI 组件库**: Element-Plus
- **网络请求**: Axios

### 后端 / Backend
- **核心框架**: Python + FastAPI
- **ORM 与数据校验**: SQLAlchemy + Pydantic

### 基础设施 / Infrastructure
- **数据库**: MySQL
- **部署方案**: 腾讯云服务器 (Tencent Cloud Server)

---

##  核心功能 / Key Features

### 1. 案件与进度管理 (Case Management)
* **多类型案件登记**: 支持常规民事/刑事案件、专项银行案件的独立登记与表单流转。
    * *Multi-type Registration: Supports regular cases and specialized bank cases.*
* **案件审批流**: 完善的案件合规审查与审批流程（立案、结案审批）。
    * *Approval Flow: Compliance review for case filing and closing.*
* **事件提醒**: 案件关键节点、庭审日程的智能提醒。
    * *Event Reminders: Smart notifications for milestones and court schedules.*

### 2. 电子卷宗与档案 (Electronic Volumes)
* **卷宗归档**: 案件结案后的电子卷宗一键生成与分类管理。
    * *File Archiving: One-click generation and management post-closure.*
* **卷宗面板**: 可视化的卷宗目录树与在线调阅功能。
    * *File Dashboard: Visual directory tree and online access.*

### 3. 财务与发票管理 (Finance Management)
* **收支登记**: 代理费、办案费等各项费用的登记与审核。
    * *Income/Expense: Registration and review of attorney and case fees.*
* **开票申请**: 律师在线提交发票申请，财务端统一处理与统计。
    * *Invoice Application: Online requests with centralized financial processing.*

### 4. 电子用印与文书 (E-Seal & Documents)
* **在线用印**: 所函、介绍信、委托书等文件的电子盖章申请与审批。
    * *Online Seal: E-seal requests for firm letters and powers of attorney.*
* **文书模板**: 常用法律文书模板的统一管理、在线预览与下载。
    * *Document Templates: Centralized management and preview of legal templates.*

### 5. 党建工作管理 (Party Building)
* **材料与活动管理**: 党建学习材料上传、党支部活动记录与详情展示。
    * *Activity Management: Learning materials upload and activity records.*

### 6. 律师与行政管理 (Lawyer & System Management)
* **律师管理**: 律师个人档案、执业信息及系统账户权限管理。
    * *Lawyer Management: Profiles, practice info, and RBAC.*
* **个人中心**: 律师个人数据面板及基础资料修改。
    * *Personal Center: Personal data dashboard and profile editing.*
* **系统设置**: 律所全局参数、审批流节点及系统字典配置。
    * *System Settings: Global parameters and workflow configurations.*
