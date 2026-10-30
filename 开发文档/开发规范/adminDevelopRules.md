# 宇小兔读书 · 管理后台（Admin）开发规范

| 项目 | 说明 |
|------|------|
| 文档名称 | adminDevelopRules.md |
| 文档版本 | v1.0 |
| 编写日期 | 2026-07-06 |
| 适用范围 | `YuXiaotuBook/frontend` 中 **Admin 管理后台** 全部页面与组件 |
| 项目目录 | `E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\YuXiaotuBook\frontend` |
| 存放路径 | `E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\开发文档\开发规范\adminDevelopRules.md` |
| 关联文档 | [技术选型定版](../开发需求文档/技术选型定版.md) · [技术选型（Python/Java 边界）](../开发需求文档/技术选型.md) · [C 端开发规范](./customerDevelopRules.md) · [小程序开发规范](./weixintoolDevelopRules.md) |

---

## 一、规范定位与强制级别

### 1.1 文档目的

本文档是 **宇小兔读书内嵌管理后台（`/admin/*`）** 的唯一开发规范。所有新菜单、页面、组件、重构、Bug 修复与发版均须遵循本文档。

**适用范围说明：**

| 范围 | 路径前缀 | 是否适用本文档 |
|------|----------|----------------|
| **Admin 管理后台** | `/admin/*` | **是** |
| C 端用户前台 | `/`、`/books`、`/user/*` 等 | **否**（见 [customerDevelopRules.md](./customerDevelopRules.md)） |
| 微信小程序 | `yuxiaotubookWeixinTool` | **否** |

**与独立 ECMS 的关系：** 技术选型文档中 `Admin-YuXiaoTuBook` 为独立 ECMS 项目；**当前主链路 Admin 内嵌于 `YuXiaotuBook/frontend`**，调用 Python `/api/v1/admin/*`。本文档规范的是 **内嵌 Admin**；若未来拆分 ECMS，须以新仓库规范为准并同步 API 契约。

### 1.2 强制级别说明

| 标记 | 含义 |
|------|------|
| **【必须】** | 违反即视为不合规，Code Review 应拒绝合并 |
| **【推荐】** | 默认做法；特殊场景可偏离，但须在 PR 中说明理由 |
| **【禁止】** | 明确不允许的做法 |

### 1.3 核心原则（1 分钟读完）

1. **【必须】** Admin 是 **唯一内容运营入口**：书籍、视频、氛围、每日、会员套餐、订单履约均在此配置，C 端与小程序只读展示。
2. **【必须】** Admin API **永久走 Python**（`/api/v1/admin/*`）；**【禁止】** Admin 前端直连 MySQL 或调用未鉴权的 C 端写接口。
3. **【必须】** UI 统一使用 **Element Plus + admin-theme.css（ECMS 主题）**；**【禁止】** Admin 页面使用 C 端 `variables.css` / 原生按钮体系。
4. **【必须】** 菜单（`adminMenu.ts`）、路由（`router/index.ts`）、页面标题 meta **三处同步**。
5. **【必须】** 上传媒体走 `utils/adminUpload.ts` 与后端约定目录（`/uploads/homePage`、`/uploads/bookReview` 等）；C 端/小程序通过 API 即时生效。

---

## 二、技术栈与工程约束

### 2.1 定版技术栈

| 类别 | 选型 | 版本/说明 |
|------|------|-----------|
| 框架 | Vue 3 | 与 `package.json` 锁定版本一致 |
| 语言 | TypeScript | ~5.6，新代码 **【必须】** 使用 TS |
| 构建 | Vite | 开发端口 **5188**（与 C 端同仓同端口） |
| 路由 | Vue Router 4 | History 模式 |
| 状态管理 | Pinia | `user`（共用）、`adminTabs`（Admin 专用） |
| HTTP | Axios | `src/api/client.ts` 的 `request()` / `http` |
| UI 组件库 | Element Plus | **Admin 专用** |
| 图标 | `@element-plus/icons-vue` | 菜单与页面图标 |
| 主题 | `styles/admin-theme.css` | ECMS 变量 `--ecms-*` |

### 2.2 后端与 API 边界

| 域 | 路径前缀 | 后端 | 说明 |
|----|----------|------|------|
| Admin 全部 | `/api/v1/admin/*` | Python FastAPI `:8000` | **永久 Python** |
| 管理员登录 | `/api/v1/auth/login` | Python | 须 `user.role === 'admin'` |
| C 端订单支付 | `/api/v1/orders`、`/member` | Java `:8081` | Admin **只读/履约**，不在此创建支付 |

**【必须】** Admin 页面请求 Admin 接口时使用相对路径 `/admin/...`（Axios `baseURL` 已为 `/api/v1`）。

**【禁止】** 在 Admin 页面调用 C 端写接口（如 `POST /favorites`）代替 Admin API。

新增接口前先查 [技术选型.md §2.5](../开发需求文档/技术选型.md) 与 `backend/app/api/v1/admin.py`。

### 2.3 本地开发

```powershell
cd "E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\YuXiaotuBook\frontend"
pnpm dev
# 访问：http://127.0.0.1:5188/admin/login
```

**【必须】** 联调前启动 Python 后端（`:8000`）；订单列表/统计若涉及 Java 数据，须同时启动 `:8081`。

默认管理员账号见登录页提示（`admin` / `admin123456`，以实际 seed 为准）。

---

## 三、目录结构与文件归属

### 3.1 标准目录（Admin 相关）

```text
YuXiaotuBook/frontend/src/
├── api/
│   ├── client.ts                 # Axios 实例（C 端与 Admin 共用）
│   └── adminStats.ts             # 数据分析域 API 封装
├── components/admin/             # Admin 专用组件
│   ├── AuthBrandPanel.vue        # 登录页品牌区
│   └── BookReviewVideosUpload.vue
├── config/
│   └── adminMenu.ts              # 侧栏菜单定义（单一数据源）
├── layouts/
│   └── AdminLayout.vue           # 侧栏 + 顶栏 + Tab + 内容区
├── stores/
│   ├── user.ts                   # 登录态（与 C 端共用）
│   └── adminTabs.ts              # 已打开菜单 Tab
├── styles/
│   └── admin-theme.css           # ECMS 主题与 .page-card 等
├── utils/
│   ├── adminUpload.ts            # 上传/删除媒体
│   ├── datetime.ts               # formatBeijingTime
│   ├── media.ts                  # resolveMediaUrl（预览）
│   └── video.ts                  # protectVideoUrl（预览）
└── views/admin/                  # Admin 页面
    ├── Login.vue
    ├── AdminPlaceholder.vue      # 规划中页面占位
    ├── AnalyticsOverview.vue
    ├── AnalyticsReading.vue
    ├── AnalyticsOrders.vue
    ├── AnalyticsRegion.vue
    ├── AnalyticsSystem.vue
    ├── Books.vue
    ├── Categories.vue
    ├── Videos.vue
    ├── Daily.vue
    ├── SiteConfig.vue
    ├── MemberPackages.vue
    ├── Orders.vue
    └── Users.vue
```

### 3.2 文件放置规则

| 内容 | 放置位置 | 说明 |
|------|----------|------|
| Admin 页面 | `views/admin/*.vue` | 一个菜单页一个文件 |
| Admin 复用组件 | `components/admin/` | 如上传、表单块 |
| 菜单配置 | `config/adminMenu.ts` | **【必须】** 与路由同步 |
| 统计类 API | `api/admin*.ts` | 按域拆分，避免页面内拼 URL |
| 上传逻辑 | `utils/adminUpload.ts` | 统一 FormData 上传 |
| 占位页 | `AdminPlaceholder.vue` | 未上线模块 |

**【禁止】** 在 `views/admin/` 下新建独立 Axios 客户端；**【禁止】** Admin 组件放入 `components/` 根目录（与 C 端混放）。

### 3.3 新增 Admin 页面流程

1. 在 `config/adminMenu.ts` 增加菜单项（含 `path`、`title`、`icon`）；
2. 在 `router/index.ts` 的 `/admin` 子路由注册，设置 `meta.title`、`meta.parentTitle`、`meta.group`；
3. 创建 `views/admin/Xxx.vue` 页面；
4. 若为新 API，在后端 `admin.py` 增加路由并更新技术选型文档；
5. 若为规划中功能，路由指向 `AdminPlaceholder` 并设置 `meta.placeholderDesc`；
6. 本地登录 Admin → 菜单可见 → Tab 可打开 → 接口联调；
7. 在 C 端 `:5188` 验证配置是否生效。

---

## 四、命名规范

### 4.1 文件与目录

| 类型 | 规范 | 示例 |
|------|------|------|
| Admin 页面 | PascalCase | `SiteConfig.vue`、`MemberPackages.vue` |
| Admin 组件 | PascalCase，放 `components/admin/` | `BookReviewVideosUpload.vue` |
| API 模块 | camelCase，`admin` 前缀 | `adminStats.ts` |
| 菜单 group key | 小写英文 | `analytics`、`book`、`content` |
| 路由 path | `/admin/{域}/{动作}` | `/admin/content/video` |

### 4.2 路由与菜单 path 约定

```text
/admin/analytics/*     数据分析
/admin/book/*          书籍管理
/admin/content/*       内容管理
/admin/atmosphere/*    氛围配置
/admin/member/*        会员管理
/admin/order/*         订单管理
/admin/permission/*    权限管理
```

**【必须】** 新 path 遵循 `{域}/{动作}` 两级结构；**【禁止】** 与旧路由冲突（旧路径已在 router 中做 redirect 兼容）。

### 4.3 API 字段

**【必须】** 与后端一致使用 **snake_case**（`book_id`、`ship_tracking_no`、`bg_videos` 等）。

---

## 五、Vue 与 TypeScript 编码规范

### 5.1 组件写法

**【必须】** 使用 `<script setup lang="ts">` + Composition API + Element Plus。

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { request } from '@/api/client'

const loading = ref(false)
const list = ref<BookRow[]>([])

async function load() {
  loading.value = true
  try {
    const res = await request<BookRow[]>({ url: '/admin/books' })
    if (res.code === 200) list.value = res.data || []
    else ElMessage.error(res.msg || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
```

### 5.2 用户反馈

**【必须】** 操作结果使用 Element Plus 反馈组件：

| 场景 | 组件 |
|------|------|
| 成功/失败提示 | `ElMessage.success` / `ElMessage.error` |
| 需确认的操作 | `ElMessageBox.confirm` 或 `confirm()`（逐步统一） |
| 表单校验 | `el-form` + `FormRules` |
| 加载态 | `v-loading` 或 `:loading` on 按钮 |

**【禁止】** 新页面使用 `alert()`（遗留代码改造时替换为 `ElMessage`）。

### 5.3 类型

**【推荐】** 统计类类型放在 `api/adminStats.ts`；页面局部类型可写在 `.vue` 内。

**【必须】** 新代码减少 `any`；表格行、表单、API 响应应声明 interface。

---

## 六、API 层规范

### 6.1 请求方式

**【必须】** 业务页面使用 `request()`：

```typescript
const res = await request<VideoGroupRow[]>({ url: '/admin/videos' })
if (res.code === 200) { /* res.data */ }
```

**【必须】** 文件上传使用 `utils/adminUpload.ts` 或 `http.post` + `FormData`（与 `adminUpload` 保持一致）：

```typescript
import { uploadBookReviewVideo } from '@/utils/adminUpload'

const data = await uploadBookReviewVideo(file)
// data.url → 写入表单，提交 PUT /admin/videos/by-book/{id}
```

### 6.2 Admin API 域划分

| 域 | 典型路径 | 页面 |
|----|----------|------|
| 上传 | `POST /admin/upload`、`/admin/home-page-videos/*`、`/admin/book-review-videos/*` | 氛围、视频 |
| 书籍 | `GET/POST/PUT/DELETE /admin/books` | 书籍列表 |
| 视频 | `GET /admin/videos`、`PUT /admin/videos/by-book/{id}` | 解读视频管理 |
| 分类 | `GET/POST/DELETE /admin/categories` | 书籍分类 |
| 订单 | `GET /admin/orders`、`PUT .../ship`、`PUT .../status` | 全部订单 |
| 氛围 | `GET/PUT /admin/site-config` | 首页氛围配置 |
| 每日 | `GET/POST/PUT/DELETE /admin/daily` | 每日读书专栏 |
| 会员 | `GET/POST/PUT/DELETE /admin/member/packages` | 会员套餐 |
| 用户 | `GET /admin/users/tree`、`GET/PUT /admin/users/{id}` | 用户管理 |
| 统计 | `GET /admin/stats/overview` 等 | 数据分析各页 |

完整列表以 `backend/app/api/v1/admin.py` 为准。

### 6.3 鉴权

**【必须】** Admin 接口依赖 Bearer Token；Axios 请求拦截器自动附加 `localStorage.token`。

**【必须】** 登录页校验 `res.data.user.role === 'admin'`，非管理员 **【禁止】** 进入 `/admin/*`。

**【必须】** 路由守卫（`router.beforeEach`）对 `meta.admin` 校验 `store.isLoggedIn && store.isAdmin`。

### 6.4 响应处理

与 C 端一致：`{ code: 200, msg, data }`；失败时展示 `res.msg`。

---

## 七、路由、菜单与布局

### 7.1 路由注册规范

每个 Admin 页面路由 **【必须】** 包含 meta：

```typescript
{
  path: 'content/video',
  meta: {
    title: '解读视频管理',           // Tab 与面包屑标题
    parentTitle: '内容管理',         // 面包屑上级
    group: 'content',               // 与 adminMenu group.key 一致
    placeholderDesc: '...',          // 可选：占位页说明
  },
  component: () => import('@/views/admin/Videos.vue'),
}
```

### 7.2 菜单配置（`adminMenu.ts`）

**【必须】** 侧栏菜单以 `adminMenuGroups` 为单一数据源；`AdminLayout` 通过 `filterAdminMenu` 渲染。

新增菜单项 checklist：

- [ ] `adminMenu.ts` 增加 `AdminMenuItem`（`path`、`title`、`icon`）
- [ ] `router/index.ts` 注册同名 `path`
- [ ] `meta.title` 与菜单 `title` 一致
- [ ] 需 `matchPrefix: true` 时（如书籍编辑子页）在菜单项上声明

### 7.3 AdminLayout 行为

| 能力 | 实现 |
|------|------|
| 侧栏折叠 | `collapsed` + 折叠态 Popover 飞菜单 |
| 面包屑 | `parentTitle` + `title` |
| 菜单搜索 | 顶栏 `el-autocomplete` → `searchMenuOptions` |
| 多 Tab | `useAdminTabsStore` 随路由 `addTab` |
| 退出 | 清空 tabs + `logout` → `/admin/login` |

**【禁止】** 在单页内重复实现侧栏/顶栏；**【必须】** 业务页只渲染 `.content` 区域内内容。

### 7.4 占位页（规划中模块）

**【必须】** 未实现业务的路由使用 `AdminPlaceholder.vue`：

```typescript
component: placeholder,
meta: {
  title: '图书素材库',
  parentTitle: '书籍管理',
  group: 'book',
  placeholderDesc: '统一管理图书高清封面、内页插图等素材...',
},
```

**【禁止】** 占位路由指向空白页或不注册路由。

---

## 八、状态管理（Pinia）

### 8.1 Store 划分

| Store | 文件 | 职责 |
|-------|------|------|
| `useUserStore` | `stores/user.ts` | token、用户、**isAdmin**、登录/登出 |
| `useAdminTabsStore` | `stores/adminTabs.ts` | 已打开菜单 Tab 列表 |

**【必须】** Admin 业务数据（列表、表单）放页面内 `ref`，**【禁止】** 放入全局 Store（除非跨 Tab 明确需要共享）。

### 8.2 Admin Tabs

**【必须】** 由 `AdminLayout` 在路由变化时 `tabsStore.addTab(route)`。

**【必须】** 关闭 Tab 时 `removeTab` 返回下一跳转 path；清空记录调用 `clearTabs()`。

---

## 九、UI 与样式规范

### 9.1 主题变量（ECMS）

定义于 `styles/admin-theme.css`，Admin 根节点 `data-admin-theme="light"`：

| 变量 | 值 | 用途 |
|------|-----|------|
| `--ecms-primary` | `#5d87ff` | 主色（与 C 端 `#5b9aa0` 区分） |
| `--ecms-bg` | `#f4f7fe` | 内容区背景 |
| `--ecms-text` | `#1d2129` | 主文字 |
| `--ecms-border` | `#e5e6eb` | 边框 |
| `--ecms-radius` | `8px` | 圆角 |

**【必须】** Admin 页面样式使用 `--ecms-*`；**【禁止】** 使用 C 端 `--color-primary` 作为主色。

### 9.2 页面结构模板

**【推荐】** 标准列表/表单页结构：

```vue
<template>
  <div class="page-card">
    <div class="page-header">
      <h2>页面标题</h2>
      <el-button type="primary" @click="openCreate">新增</el-button>
    </div>
    <el-table v-loading="loading" :data="list" ... />
    <!-- 或 el-form -->
  </div>
</template>
```

全局类（`admin-theme.css`）：

- `.page-card` — 白底卡片容器
- `.page-header` — 标题 + 操作区

### 9.3 Element Plus 使用约定

| 场景 | 组件 |
|------|------|
| 数据表格 | `el-table` + `el-pagination` |
| 弹窗表单 | `el-dialog` + `el-form` |
| 筛选 | `el-form` inline + `el-select` / `el-date-picker` |
| 状态标签 | `el-tag`（订单状态等） |
| 上传 | `el-upload` + `:http-request` 自定义上传 |

**【必须】** 表格分页、筛选参数与后端约定一致（如 `page`、`page_size`、snake_case 查询字段）。

### 9.4 登录页

**【必须】** 使用 `AuthBrandPanel` + 右侧 `el-form` 双栏布局（`views/admin/Login.vue`）。

**【必须】** 登录成功跳转默认工作台：`/admin/analytics/overview`。

---

## 十、上传与媒体管理

### 10.1 上传工具（`adminUpload.ts`）

| 函数 | 用途 | 后端路径 |
|------|------|----------|
| `uploadAdminFile` | 通用图片/小视频 | `POST /admin/upload` |
| `uploadHomePageVideo` | 首页背景视频 | `POST /admin/home-page-videos/upload` |
| `deleteHomePageVideo` | 删除背景视频 | `DELETE /admin/home-page-videos` |
| `uploadBookReviewVideo` | 解读视频 | `POST /admin/book-review-videos/upload` |
| `deleteBookReviewVideo` | 删除解读视频 | `DELETE /admin/book-review-videos` |

### 10.2 限制（与后端一致）

| 类型 | 限制 |
|------|------|
| 图片 | jpg/png/webp，≤ 5MB |
| 通用视频 | mp4/webm，≤ 50MB |
| 首页/解读视频 | mp4/webm，≤ 100MB |
| 解读视频数量 | 每书最多 20 个（前后端一致） |

**【必须】** 上传前在组件内 `beforeUpload` 校验类型与大小（参考 `BookReviewVideosUpload.vue`）。

**【必须】** 保存书籍视频时 URL 使用后端返回的 `/uploads/bookReview/...` 路径；预览时使用 `resolveMediaUrl` + `protectVideoUrl`。

### 10.3 与 C 端 / 小程序联动

```text
Admin 上传/配置 → Python 写库/写文件 → C 端 / 小程序 GET API 展示
```

**【必须】** 氛围配置（`site-config`）保存后，C 端 `siteStore`、小程序 `siteStore` 下次请求即更新。

**【禁止】** 在前端写死 CDN URL 替代 Admin 配置的 `bg_videos` / 封面字段。

---

## 十一、业务模块规范

### 11.1 数据分析

| 页面 | 路由 | API |
|------|------|-----|
| 全站总览 | `/admin/analytics/overview` | `GET /admin/stats/overview` |
| 阅读行为 | `/admin/analytics/reading` | `GET /admin/stats/reading` |
| 订单统计 | `/admin/analytics/orders` | `GET /admin/stats/orders` |
| 地域分布 | `/admin/analytics/region` | `GET /admin/stats/region` |
| 系统监控 | `/admin/analytics/system` | `GET /admin/stats/system` |

**【必须】** 统计 API 封装在 `api/adminStats.ts`；时间展示使用 `formatBeijingTime`。

### 11.2 书籍与内容

| 模块 | 要点 |
|------|------|
| 书籍列表 | CRUD `/admin/books`；含库存 `stock`（运营改库存走 Admin，支付扣减走 Java） |
| 书籍分类 | `/admin/categories` |
| 解读视频 | 按书聚合；`BookReviewVideosUpload` 组件；`PUT /admin/videos/by-book/{id}` |
| 每日读书 | `/admin/daily` CRUD；发布后 C 端/小程序 `/daily/*` 可见 |

### 11.3 氛围配置

**【必须】** 首页氛围走 `GET/PUT /admin/site-config`：`promo_title`、`daily_sentence`、`bg_videos`、`featured_book_id` 等。

**【必须】** 背景视频列表与 `uploads/homePage` 目录通过后端 `merge_bg_videos_with_folder` 合并，Admin 保存时需理解该逻辑。

### 11.4 订单履约

**【必须】** 列表 `GET /admin/orders`（Python，只读/履约）。

**【必须】** 发货 `PUT /admin/orders/{id}/ship`（物流公司 + 运单号）。

**【必须】** 状态变更 `PUT /admin/orders/{id}/status`（含 Admin 取消）；涉及库存回滚须与 Java trade 策略一致（见技术选型文档）。

**【禁止】** 在 Admin 前端模拟 C 端 `mock-pay` 代替用户支付流程（测试支付在 C 端/小程序进行）。

### 11.5 会员与用户

| 模块 | API |
|------|-----|
| 会员套餐 CRUD | `/admin/member/packages` |
| 用户地区树 | `GET /admin/users/tree` |
| 用户详情/编辑 | `GET/PUT /admin/users/{id}` |

套餐 **配置** 在 Python Admin；用户 **订阅/支付** 在 Java trade。

---

## 十二、安全与权限

### 12.1 认证

- **【必须】** 仅 `role === 'admin'` 可进入 Admin
- **【必须】** Token 存 `localStorage`（与 C 端相同 key，但 Admin 登录入口独立）
- **【禁止】** 在前端硬编码 Admin 密码或 JWT 密钥

### 12.2 操作安全

- **【必须】** 删除、清空、取消订单等操作需二次确认
- **【必须】** 上传文件校验 MIME/扩展名与大小
- **【推荐】** 敏感操作日志留后端（`permission/audit` 占位页规划）

### 12.3 数据展示

- **【禁止】** 在控制台打印完整 Token 或用户隐私
- **【必须】** 用户手机号等敏感信息按产品要求脱敏展示

---

## 十三、Git 与协作流程

### 13.1 与 C 端同仓协作

```text
YuXiaotuBook/frontend/
├── views/           C 端
├── views/admin/     Admin  ← 本文档
├── components/      C 端
├── components/admin/ Admin
```

**【必须】** Admin PR 避免无关 C 端大改；共用文件（`api/client.ts`、`stores/user.ts`）变更须评估 C 端影响。

### 13.2 分支与提交

**【推荐】** 分支：`feat/admin-{简述}`、`fix/admin-{简述}`。

**【推荐】** 提交：

```text
feat(admin): 订单列表增加发货弹窗
fix(admin): 修复解读视频上传后未刷新素材库
```

### 13.3 变更传播

| Admin 变更 | 须验证 |
|------------|--------|
| 书籍/分类 | C 端书单、小程序书单 |
| 解读视频 | C 端/小程序详情页播放 |
| 氛围配置 | C 端/小程序首页 |
| 每日读书 | C 端/小程序每日 Tab |
| 会员套餐 | C 端/小程序会员中心 |
| 订单发货 | C 端/小程序个人中心收发货 |

---

## 十四、Code Review 检查项

### 14.1 架构

- [ ] 新接口走 `/admin/*` Python API
- [ ] 菜单、路由、meta.title 三处一致
- [ ] 未引用 C 端组件/样式作为主 UI

### 14.2 代码质量

- [ ] `<script setup lang="ts">`
- [ ] 使用 `request()` / `adminUpload`
- [ ] 操作反馈用 `ElMessage` 等，非 `alert`
- [ ] 列表有 loading、空态

### 14.3 UI

- [ ] 使用 `.page-card` / `--ecms-*`
- [ ] Element Plus 组件用法一致
- [ ] 上传限制与后端一致

### 14.4 联调

- [ ] Admin 保存后 C 端可见（抽样）
- [ ] `pnpm build` 通过

---

## 十五、测试与验收

### 15.1 Admin 自测（最低要求）

| 步骤 | 预期 |
|------|------|
| 登录 | 非 admin 账号被拒绝 |
| 菜单 | 侧栏、搜索、Tab 正常 |
| 书籍 CRUD | 列表增删改后 C 端可见 |
| 视频管理 | 上传 + 绑定书籍 + 详情页可播 |
| 氛围配置 | 首页标题/背景视频更新 |
| 每日读书 | 发布后 C 端/小程序可见 |
| 订单 | 发货后用户端物流可见 |
| 会员套餐 | C 端/小程序套餐列表一致 |

### 15.2 构建

```powershell
pnpm build
```

---

## 十六、发版与部署

Admin 与 C 端 **同一 Vite 构建产物** `dist/`，由 Nginx 统一托管。Admin 路由为 SPA 前端路由，需配置 fallback 到 `index.html`。

**上线前 checklist：**

- [ ] `pnpm build` 通过
- [ ] 生产环境 Admin 登录可用
- [ ] HTTPS
- [ ] 上传目录 `/uploads` 可写且 Nginx 可访问

---

## 十七、文档维护

| 变更类型 | 须同步更新 |
|----------|------------|
| 新菜单/页面 | `adminMenu.ts`、`router`、本文档 §7/§11 |
| 新 Admin API | `admin.py`、技术选型 §2.5 |
| 上传策略变更 | `adminUpload.ts`、本文档 §10 |
| 主题/布局变更 | `admin-theme.css`、`AdminLayout.vue` |
| 占位页转正式 | 替换 component、删除 placeholder meta |

---

## 十八、附录

### A. 菜单与页面对照（当前）

| 分组 | 菜单 | 路由 | 状态 |
|------|------|------|------|
| 数据分析 | 全站总览仪表盘 | `/admin/analytics/overview` | 已实现 |
| 数据分析 | 用户阅读行为分析 | `/admin/analytics/reading` | 已实现 |
| 数据分析 | 交易订单数据统计 | `/admin/analytics/orders` | 已实现 |
| 数据分析 | 用户地域分布分析 | `/admin/analytics/region` | 已实现 |
| 数据分析 | 系统性能监控面板 | `/admin/analytics/system` | 已实现 |
| 书籍管理 | 书籍列表 | `/admin/book/list` | 已实现 |
| 书籍管理 | 书籍分类 | `/admin/book/category` | 已实现 |
| 书籍管理 | 图书素材库 | `/admin/book/assets` | 占位 |
| 书籍管理 | 书单管理 | `/admin/book/collections` | 占位 |
| 内容管理 | 解读视频管理 | `/admin/content/video` | 已实现 |
| 内容管理 | 每日读书专栏 | `/admin/content/daily` | 已实现 |
| 内容管理 | AI 内容生成 | `/admin/content/ai` | 已实现 |
| 内容管理 | 内容审核 | `/admin/content/review` | 占位 |
| 氛围配置 | 首页氛围配置 | `/admin/atmosphere/home` | 已实现 |
| 氛围配置 | 音噪素材管理 | `/admin/atmosphere/audio` | 占位 |
| 氛围配置 | 页面全局设置 | `/admin/atmosphere/global` | 占位 |
| 会员管理 | 会员套餐配置 | `/admin/member/package` | 已实现 |
| 会员管理 | 用户会员列表 | `/admin/member/users` | 占位 |
| 会员管理 | 会员权益统计 | `/admin/member/stats` | 占位 |
| 会员管理 | 会员订单流水 | `/admin/member/orders` | 占位 |
| 订单管理 | 全部订单列表 | `/admin/order/all` | 已实现 |
| 订单管理 | 售后订单管理 | `/admin/order/aftersale` | 占位 |
| 订单管理 | 销量数据统计 | `/admin/order/stats` | 占位 |
| 订单管理 | 物流配置 | `/admin/order/logistics` | 占位 |
| 权限管理 | 用户管理 | `/admin/permission/user` | 已实现 |
| 权限管理 | 角色权限配置 | `/admin/permission/role` | 占位 |
| 权限管理 | 操作审计日志 | `/admin/permission/audit` | 占位 |
| 权限管理 | 系统安全配置 | `/admin/permission/security` | 占位 |

### B. Admin API 速查（Python）

前缀：`/api/v1/admin`（前端写 `/admin/...`）

| 模块 | 方法 | 路径 |
|------|------|------|
| 上传 | POST | `/upload` |
| 首页视频 | POST/DELETE/GET | `/home-page-videos/*` |
| 解读视频文件 | POST/DELETE/GET | `/book-review-videos/*` |
| 书籍 | GET/POST/PUT/DELETE | `/books`、`/books/{id}` |
| 视频绑定 | GET/PUT | `/videos`、`/videos/by-book/{id}` |
| 分类 | GET/POST/DELETE | `/categories`、`/categories/{id}` |
| 订单 | GET/PUT | `/orders`、`/orders/{id}/ship`、`/orders/{id}/status` |
| 氛围 | GET/PUT | `/site-config` |
| 每日 | GET/POST/PUT/DELETE | `/daily`、`/daily/{id}` |
| 会员套餐 | GET/POST/PUT/DELETE | `/member/packages`、`/member/packages/{id}` |
| 用户 | GET/PUT | `/users/tree`、`/users/{id}` |
| 统计 | GET | `/stats/overview`、`/stats/reading`、`/stats/orders`、`/stats/region`、`/stats/system` |
| AI 内容 | GET/POST/PUT | `/ai/config`、`/ai/generate`、`/ai/tasks`、`/ai/items/{id}`、accept/discard |

### C. 禁止事项汇总

1. Admin 前端直连 MySQL 或使用 C 端写接口代替 Admin API
2. 菜单、路由、标题 meta 不同步
3. Admin 页面使用 C 端 `--color-primary` / 原生 `.btn` 作为主 UI
4. C 端组件（`AppHeader`、`BookCard` 等）嵌入 Admin 业务页
5. 页面内新建 Axios 实例
6. 上传不校验类型/大小
7. 硬编码生产域名或密钥
8. 非 admin 角色进入后台
9. 仅改 Admin 不验证 C 端/小程序展示
10. 占位页不说明 `placeholderDesc` 即上线空路由

### D. 参考链接

- [Element Plus 文档](https://element-plus.org/)
- [C 端开发规范](./customerDevelopRules.md)
- [小程序开发规范](./weixintoolDevelopRules.md)
- [技术选型 Admin §2.5](../开发需求文档/技术选型.md)
- 后端源码：`YuXiaotuBook/backend/app/api/v1/admin.py`

---

**修订记录**

| 版本 | 日期 | 说明 | 作者 |
|------|------|------|------|
| v1.0 | 2026-07-11 | 初版：基于 YuXiaotuBook/frontend 内嵌 Admin 工程定稿 | — |
