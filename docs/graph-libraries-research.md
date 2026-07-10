# 关系穿透台图谱轮子调研

调研时间：2026-07-11 · 调研方式：`ctx7`（Context7 官方文档检索）+ 本机环境实测
调研目的：`v_graph_nodes`/`v_graph_edges` + 递归 CTE BFS + 卡片式关系展示是纯手搓的（见
`sql/006_graph_review_stack.sql`、`app/graph_service.py`），本文调研业内常用的图谱/关系穿透
轮子，评估是否该、以及何时该替换手搓部分。

## 本机环境现状（先说清楚起点）

| 层 | 现状 |
|---|---|
| 前端 | `frontend/package.json` 只有 `vue` + `vue-router`，无任何图可视化库 |
| 后端 Python | 纯 stdlib，无 `pip` 依赖，无 `networkx` |
| PostgreSQL | 仅 `pgcrypto`/`plpgsql` 两个扩展，`pg_available_extensions` 里没有 Apache AGE |
| 图渲染 | 系统装了 `graphviz`（`/usr/bin/dot`），但代码里完全没用到，且它只是静态渲染工具，不能查询/遍历 |

也就是说，起点是**零轮子**，当前"关系穿透台"的节点/边模型、BFS 路径查询、卡片渲染全部是手写
SQL 视图 + Python 薄封装 + Vue 卡片组件。

## 候选轮子清单

按用途分两类：**前端图可视化**（把节点/边渲染成可交互的连线图，替换现在的卡片列表）、
**后端图查询/算法**（替换现在的手写递归 CTE，或者在 CTE 之外提供更复杂的图算法）。

### 前端可视化

| 库 | 定位 | 优点 | 缺点 | 对本项目的适配成本 |
|---|---|---|---|---|
| **Cytoscape.js** | 通用图论可视化库，生物/社交网络起家 | ① 功能最全：内置 `cose`/`grid`/`circle` 等多种布局算法，选择/过滤/事件系统完整；② `batch()` 批处理 API 专门优化大量增删节点场景；③ 660+ 代码示例，文档成熟，社区大（Cytoscape 桌面版生态延伸出来的） | ① API 是 jQuery 时代风格的链式调用，和 Vue 3 `<script setup>` 的响应式心智模型不太搭，需要自己包一层 ref↔cy 实例的桥接；② 默认 Canvas 渲染，节点数上千才需要关心性能，但本项目现在几十条边，用不上它的性能优势 | 中：需要写一个 `useCytoscape` composable 桥接响应式数据和命令式 `cy.add()/cy.remove()`，工作量比 vis-network 大一档 |
| **vis-network (vis.js)** | 物理引擎驱动的动态网络图 | ① 配置驱动（传一个 `options` 对象基本就能跑），学习曲线最平；② 内置层级布局（`hierarchicalRepulsion`），很适合"结构隶属"这类天然有层级的边；③ 502 星级项目，1000+ 代码片段，文档详尽 | ① Canvas 渲染，官方没给出明确的大规模性能承诺（几千节点会卡）；② 物理模拟（`barnesHut`/`forceAtlas2Based`）对小图有时会"抖来抖去"不稳定，需要调 `stabilization` 参数 | 低：`new vis.Network(container, {nodes, edges}, options)` 三行起步，最适合快速换掉卡片列表 |
| **Sigma.js** | WebGL 渲染的大图可视化库，构建在 `graphology`（图数据结构库）之上 | ① 专为大图设计，官方宣称"数千节点/边"级别，WebGL 渲染性能天花板最高；② 底层 `graphology` 是纯数据结构层，可以脱离渲染单独做图算法（度数、路径），复用性好 | ① 学习曲线最陡——WebGL renderer 需要理解 `NodeProgram`/`EdgeProgram` 这类底层渲染管线概念；②生态偏 React（`react-sigma` 成熟，Vue 绑定要自己写）；③ 对于本项目"几十条边"的体量，WebGL 的性能优势完全用不上，等于杀鸡用牛刀 | 高：性价比最低，除非未来关系数据涨到几千条边规模 |
| **D3-force 系（d3-force / react-force-graph / 3d-force-graph）** | 力导向图布局的事实标准，衍生出一整个生态（2D/3D/VR） | ① 最灵活、最可定制，业内"力导向图"约定俗成就是 D3 那套物理模型；② `react-force-graph`/`3d-force-graph` 这类封装库把 D3-force 的复杂度包掉了，开箱即用度接近 vis-network | ① 纯 D3（不用封装库）要自己管 SVG/Canvas 渲染循环，工作量最大；② 生态同样偏 React，Vue 版本要么自己包 D3，要么找社区维护度参差不齐的 `vue-d3` 系包 | 中到高：如果直接用 D3 原语，工作量最大；如果用 `react-force-graph` 得先跨框架桥接，不划算 |

### 后端图查询 / 算法

| 库 | 定位 | 优点 | 缺点 | 对本项目的适配成本 |
|---|---|---|---|---|
| **NetworkX (Python)** | 图论算法库（最短路径、社群发现、中心度等） | ① API 简单，`nx.shortest_path()` 一行顶现在几十行递归 CTE；② 算法覆盖面远超手写 SQL 能做到的范围（中心度、社群发现这类图谱页 README 里提到的"下一步"需求） | ① 需要引入 `pip` 依赖——而这个项目目前明确是"纯 stdlib，无 `requirements.txt`"（见 `CLAUDE.md`），加它意味着打破这个约定，需要先决定要不要上虚拟环境/依赖管理；② 数据要从 Postgres 搬到内存图对象，对于会持续增长的关系数据，需要设计好"何时重建内存图"的策略，不是查询即用 | 中：技术上简单，但和现有"零依赖"哲学冲突，是项目基调层面的决定，不只是技术选型 |
| **Apache AGE** | PostgreSQL 图数据库扩展，openCypher 查询语法 | ① 图查询能直接下推到数据库层，不用倒腾内存图对象；② 支持"SQL JOIN + Cypher MATCH 混用"（关系表拉数据喂给图遍历），和现有 `legal_relations` 关系表模型能共存；③ 官方在线文档成熟（550 代码片段） | ① **本机环境目前没有这个扩展**（`pg_available_extensions` 查不到），需要自己编译/安装 `age.so` 或者换用打包好该扩展的 Postgres 镜像，属于基础设施变更，不是加个包那么简单；② 查询结果是 `agtype` 编码类型，从 `psql` CLI 里拿到的是这种特殊格式，而现在 `db_access.py` 的 `psql_json` 依赖 Postgres 原生 `jsonb`/`jsonb_agg` 输出，两者对不上，接入层要单独适配 | 高：目前环境不具备，且和"纯 psql CLI 查询 jsonb"的现有架构有摩擦，短期不现实 |

## 综合结论

**现在不用换。** 理由很直接：
- 关系数据体量是几十条边（截至最近一次批量抽取后，`legal_relations` 才 30 来行），远没到手写递归
  CTE（4 跳深度封顶）会喊卡的规模，Cytoscape/Sigma 的性能优势和 NetworkX/AGE 的算法优势现在都用
  不上
- 换轮子的成本不是"装个包"，而是打破两条已经写进 `CLAUDE.md` 的项目基调：后端"纯 stdlib 无依赖"、
  数据链路"psql CLI 直出 jsonb"——引入 NetworkX 或 AGE 都会破坏这两条

**但前端"卡片列表 ≠ 真图谱"这件事，是值得换的**，因为这不是性能问题，是体验问题——用户想直观看到
节点连线，卡片列表再怎么分组也不是同一种认知方式。这块建议：

| 选择 | 推荐度 | 理由 |
|---|---|---|
| **vis-network** | ★★★★★ 首选 | 配置驱动，接入成本最低，`hierarchicalRepulsion` 天然适合"结构隶属"边和"制度关系"边分层展示，和现有 `RelationBoard.vue` 的分组逻辑（`grouped_relations`）可以直接映射成 vis 的 `group` 字段 |
| Cytoscape.js | ★★★☆☆ 次选 | 功能更全，但接入工作量更大，只有当未来需要"按图论算法过滤/高亮"（比如"高亮所有制度联动路径"）这类超出 vis-network 配置能力的需求时才值得换 |
| Sigma.js / D3-force | ★☆☆☆☆ 不推荐（现阶段） | 性能天花板用不上，接入成本还最高，等关系数据涨到成百上千条边再考虑 |

后端维持现有递归 CTE 不动；等 `legal_relations` 数据量或查询复杂度（比如要做"最短路径解释链"
之外的社群发现/中心度分析）真正超出手写 SQL 能力范围时，再重新评估 NetworkX（先解决要不要引入
`pip` 依赖这个基调问题）或 Apache AGE（先解决扩展是否能装进本机环境这个基础设施问题）。

## 后续行动（如果要动手）

1. `frontend`: `npm install vis-network`（无需 `vis-data`，直接用 `DataSet`/`Network` 核心 API 即可）
2. 新增 `frontend/src/components/RelationGraphCanvas.vue`：接收 `workspace_service.graph_view()`
   已经吐出来的 `structural_neighbors` + `grouped_relations` + `neighbors`，映射成
   `{nodes: [...], edges: [...]}` 喂给 `vis.Network`；`contains` 边用 `hierarchicalRepulsion`
   物理模式，其余关系边用默认 `barnesHut`
3. 保留现有 `RelationBoard.vue` 卡片视图作为"列表模式"，图谱页做成 `连线图 / 列表` 两个 tab 切换，
   不是相互替代（列表模式在证据密集查看、可访问性上仍有优势）
4. 不动后端：`workspace_service.graph_view()` 的 JSON 契约不需要改，前端组件层面适配即可
