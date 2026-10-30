# 宇小兔读书 · 网站前台（C 端）开发规范

| 项目 | 说明 |
|------|------|
| 文档名称 | customerDevelopRules.md |
| 文档版本 | v1.0 |
| 编写日期 | 2026-07-06 |
| 适用范围 | `YuXiaotuBook/frontend` 中 **C 端用户前台** 全部页面与组件 |
| 项目目录 | `E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\YuXiaotuBook\frontend` |
| 存放路径 | `E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\开发文档\开发规范\customerDevelopRules.md` |
| 关联文档 | [技术选型定版](../开发需求文档/技术选型定版.md) · [技术选型（Python/Java 边界）](../开发需求文档/技术选型.md) · [小程序开发规范](./weixintoolDevelopRules.md) · [C 端 API 端点清单](../../yuxiaotubookWeixinTool/开发文档/C端API端点清单与OpenAPI对照表.md) |

---

## 一、规范定位与强制级别

### 1.1 文档目的

本文档是 **宇小兔读书网站用户前台（C 端）** 的唯一开发规范。所有新页面、组件、重构、Bug 修复与发版均须遵循本文档。

**适用范围说明：**

| 范围 | 路径前缀 | 是否适用本文档 |
|------|----------|----------------|
| **C 端用户前台** | `/`、`/books`、`/daily`、`/member`、`/login`、`/user/*` 等 | **是** |
| Admin 管理后台 | `/admin/*` | **否**（Admin 另有规范，本文档仅作仓库结构参考） |

与微信小程序冲突时，以 **产品行为 → Dev PRD** 为准；以 **语言/API 归属 → 技术选型文档** 为准；C 端与小程序应保持 **API、Store、工具函数同构**。

### 1.2 强制级别说明

| 标记 | 含义 |
|------|------|
| **【必须】** | 违反即视为不合规，Code Review 应拒绝合并 |
| **【推荐】** | 默认做法；特殊场景可偏离，但须在 PR 中说明理由 |
| **【禁止】** | 明确不允许的做法 |

### 1.3 核心原则（1 分钟读完）

1. **【必须】** C 端与小程序、Admin 共用同一套 API、JWT、MySQL；**【禁止】** 在前端维护书籍/视频/每日等内容数据。
2. **【必须】** 内容/用户接口走 Python（`:8000`），订单/会员走 Java（`:8081`）；**【禁止】** 前端直连数据库或自建 BFF。
3. **【必须】** 页面数据来自 API 实时拉取；Admin 改内容后，用户刷新即生效，不依赖前端发版。
4. **【必须】** 新增/变更 C 端能力时，同步评估小程序是否需要对齐（types、API、交互）。
5. **【必须】** C 端 UI 使用品牌 CSS 变量与原生组件为主；**【禁止】** 在 C 端页面滥用 Element Plus 破坏现有视觉气质。

---

## 二、技术栈与工程约束

### 2.1 定版技术栈

| 类别 | 选型 | 版本/说明 |
|------|------|-----------|
| 框架 | Vue 3 | 与 `package.json` 锁定版本一致 |
| 语言 | TypeScript | ~5.6，新代码 **【必须】** 使用 TS |
| 构建 | Vite | 开发端口 **5188**（`strictPort: true`） |
| 路由 | Vue Router 4 | History 模式 |
| 状态管理 | Pinia（Composition API 风格） | `user`、`site` 全局 Store |
| HTTP | Axios | 封装于 `src/api/client.ts` |
| 页面标题 | `@unhead/vue` | 各页 `useHead({ title })` |
| UI（C 端） | 原生 HTML + CSS 变量 | 见 `styles/variables.css`、`global.css` |
| UI（Admin） | Element Plus | 仅 `/admin/*` 使用，C 端 **【禁止】** 引入 |

### 2.2 后端与代理

本地开发通过 Vite 代理转发（`vite.config.ts`）：

| 路径 | 代理目标 | 后端 |
|------|----------|------|
| `/api/v1/orders`、`/api/v1/member` | `http://127.0.0.1:8081` | Java trade-service |
| `/api`、`/uploads`、`/media`、`/placeholders` | `http://127.0.0.1:8000` | Python FastAPI |

生产环境经 Nginx 统一入口：`https://www.yuxiaotubook.com`。

**【必须】** Axios `baseURL` 为 `/api/v1`（相对路径），**【禁止】** 在 C 端代码硬编码 `127.0.0.1` 或生产域名。

### 2.3 npm scripts

```powershell
cd "E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\YuXiaotuBook\frontend"
pnpm install
pnpm dev          # 开发 :5188
pnpm build        # vue-tsc + vite build
pnpm preview      # 预览生产构建
```

**【必须】** 提交前执行 `pnpm build` 确保类型检查与构建通过。

---

## 三、目录结构与文件归属

### 3.1 标准目录（C 端相关）

```text
YuXiaotuBook/frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # Axios 实例与 request 封装
│   ├── components/               # C 端公共组件
│   │   ├── AppHeader.vue
│   │   ├── AppFooter.vue
│   │   ├── BookCard.vue
│   │   ├── VideoPlayer.vue
│   │   ├── EbookReader.vue
│   │   ├── HeroSearchBox.vue
│   │   ├── FloatSupportButton.vue
│   │   └── BookSearchSuggestList.vue
│   ├── composables/              # 组合式函数
│   │   └── useBookSearchSuggest.ts
│   ├── layouts/
│   │   └── UserLayout.vue        # C 端统一布局
│   ├── stores/
│   │   ├── user.ts               # 登录态、VIP
│   │   └── site.ts               # 站点氛围配置
│   ├── styles/
│   │   ├── variables.css         # 品牌 CSS 变量
│   │   └── global.css            # C 端全局样式
│   ├── utils/
│   │   ├── media.ts              # 封面/头像 URL 解析
│   │   ├── video.ts              # 视频 URL 保护
│   │   └── datetime.ts           # 日期格式化
│   ├── views/                    # C 端页面
│   │   ├── Home.vue
│   │   ├── Books.vue
│   │   ├── BookDetail.vue
│   │   ├── Daily.vue
│   │   ├── Login.vue
│   │   ├── Register.vue
│   │   ├── member/MemberCenter.vue
│   │   └── user/                 # Orders / Favorites / History / Center
│   ├── router/index.ts           # 路由与守卫
│   ├── App.vue
│   └── main.ts
├── vite.config.ts
└── package.json
```

**说明：** 同仓库内 `views/admin/`、`layouts/AdminLayout.vue`、`styles/admin-theme.css` 属于管理后台，**不在本文档规范范围内**。

### 3.2 文件放置规则

| 内容 | 放置位置 | 说明 |
|------|----------|------|
| C 端页面 | `src/views/` 或 `src/views/user/`、`member/` | 与路由一一对应 |
| 跨页面组件 | `src/components/`（非 `admin/` 子目录） | PascalCase 命名 |
| 跨页面逻辑 | `src/composables/` | `useXxx` 命名 |
| HTTP 封装 | `src/api/client.ts` | 统一 Axios 实例 |
| 实体类型 | 优先在 Store 或独立 `types/`（逐步补齐） | 与 API 字段 snake_case 一致 |
| 媒体/视频工具 | `src/utils/media.ts`、`video.ts` | 小程序同构复制源 |

**【禁止】** 在 `views/` 单页内复制 `media.ts` / `video.ts` 逻辑；**【禁止】** C 端引用 `components/admin/` 下组件。

### 3.3 新增 C 端页面流程

1. 在 `src/views/` 创建 `.vue` 文件；
2. 在 `src/router/index.ts` 的 `UserLayout` 子路由中注册；
3. 需登录页面设置 `meta: { login: true }`；
4. 使用 `useHead` 设置页面标题；
5. 若涉及新 API，确认 [C 端 API 端点清单](../../yuxiaotubookWeixinTool/开发文档/C端API端点清单与OpenAPI对照表.md)；
6. 同步评估小程序 `types` + `api` + 页面是否需要对齐；
7. 本地 `:5188` 走查 + 移动端宽度抽查。

---

## 四、命名规范

### 4.1 文件与目录

| 类型 | 规范 | 示例 |
|------|------|------|
| 页面文件 | PascalCase | `BookDetail.vue`、`MemberCenter.vue` |
| 组件文件 | PascalCase | `VideoPlayer.vue`、`BookCard.vue` |
| Composable | camelCase，`use` 前缀 | `useBookSearchSuggest.ts` |
| 工具文件 | camelCase | `media.ts`、`datetime.ts` |
| Store | 小写单数 | `user.ts`、`site.ts` |

### 4.2 代码标识符

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件名 | PascalCase | `BookCard` |
| 变量/函数 | camelCase | `loadHomeData`、`isLoggedIn` |
| 路由 name | PascalCase | `BookDetail`、`UserOrders` |
| 常量 | UPPER_SNAKE_CASE | `PLAYBACK_RATES` |
| 路由 path | kebab-case 或小写 | `/books/:id`、`/user/center` |

### 4.3 API 与后端字段

**【必须】** 请求/响应 JSON 使用 **snake_case**（如 `book_id`、`package_id`、`is_vip`、`category_ids`）。

**【禁止】** 未经 API 层映射擅自将后端字段改为 camelCase。

---

## 五、Vue 与 TypeScript 编码规范

### 5.1 组件写法

**【必须】** 新组件统一使用 `<script setup lang="ts">` + Composition API。

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHead } from '@unhead/vue'
import { request } from '@/api/client'

useHead({ title: '书单 - 宇小兔每日读书' })

const books = ref<BookListItem[]>([])
</script>
```

**【禁止】** 新增 Options API 组件。

### 5.2 页面标题（SEO）

**【必须】** 每个 C 端页面设置 `useHead`：

```typescript
useHead({ title: '书籍详情 - 宇小兔每日读书' })
// 动态标题（详情页）
useHead({ title: `${book.title} - 宇小兔每日读书` })
```

### 5.3 类型

**【必须】** 新代码优先补全 TypeScript 类型；逐步替换现有 `ref<any>`。

**【推荐】** 共用类型集中到 `src/types/`（与小程序 `types/` 字段保持一致）。

**【必须】** 使用 `@/` 路径别名导入：

```typescript
import { request } from '@/api/client'
import { useUserStore } from '@/stores/user'
import { resolveMediaUrl } from '@/utils/media'
```

### 5.4 异步与错误

**【必须】** 检查 API 响应 `res.code === 200` 后再使用 `res.data`。

**【推荐】** 并发请求使用 `Promise.all` / `Promise.allSettled`；用户可见错误用页面内 `error` 状态或 `alert`（后续可统一为 Toast 组件）。

**【禁止】** 在页面内新建 Axios 实例；**【禁止】** 绕过 `request()` 重复实现 401 逻辑（除 Store 刷新外）。

---

## 六、API 层规范

### 6.1 HTTP 客户端

统一使用 `src/api/client.ts`：

```typescript
import { request } from '@/api/client'

// GET
const res = await request<BookListResult>({
  url: '/books',
  params: { page: 1, page_size: 12, sort: 'hot' },
})

// POST
const res = await request<{ token: string; user: UserInfo }>({
  url: '/auth/login',
  method: 'POST',
  data: { username, password },
})

if (res.code === 200) {
  // 使用 res.data
} else {
  // 使用 res.msg
}
```

### 6.2 响应约定

| 项 | 约定 |
|----|------|
| 成功 | `code === 200` |
| 信封 | `{ code, msg, data }` |
| 认证 | Header `Authorization: Bearer {token}`（Axios 拦截器自动附加） |
| 登录返回 | `data.token` + `data.user`（**不是** `access_token`） |
| 401 | 拦截器清除 `localStorage` 中 `token`、`user` |

### 6.3 Python / Java 边界

| 域 | 示例路径 | 说明 |
|----|----------|------|
| Python | `/auth/*`、`/books/*`、`/daily/*`、`/favorites`、`/history`、`/site/config` | 内容与用户 |
| Java | `/orders/*`、`/member/*` | 订单与会员支付 |

**【必须】** 新增接口前先查 [技术选型.md](../开发需求文档/技术选型.md) 确认实现语言；前端仅通过统一 `/api/v1` 调用，由 Vite/Nginx 分流。

### 6.4 新增接口 checklist

- [ ] 路径已在 C 端 API 清单或 OpenAPI 中确认
- [ ] 确认 Python 或 Java 归属
- [ ] 补充 TypeScript 类型
- [ ] 同步小程序 `api/` + `types/`（若 C 端与小程序共用）
- [ ] 本地 `:5188` 联调通过

---

## 七、路由与页面规范

### 7.1 C 端路由清单

| 路由 | name | 组件 | 需登录 | 说明 |
|------|------|------|--------|------|
| `/` | Home | `Home.vue` | 否 | 首页 Hero、主推、热门 |
| `/books` | Books | `Books.vue` | 否 | 书单、搜索、分类 |
| `/books/:id` | BookDetail | `BookDetail.vue` | 否* | 详情、视频、电子书、下单 |
| `/daily` | Daily | `Daily.vue` | 否 | 每日读书 |
| `/member` | Member | `MemberCenter.vue` | 否* | 会员套餐 |
| `/login` | Login | `Login.vue` | 否 | 登录 |
| `/register` | Register | `Register.vue` | 否 | 注册 |
| `/user/center` | UserCenter | `user/UserCenter.vue` | 是 | 个人中心 |
| `/user/orders` | UserOrders | `user/Orders.vue` | 是 | 我的订单 |
| `/user/favorites` | UserFavorites | `user/Favorites.vue` | 是 | 我的收藏 |
| `/user/history` | UserHistory | `user/History.vue` | 是 | 浏览记录 |

\* 未登录可浏览；收藏、下单、开通会员需登录。

### 7.2 布局与导航

**【必须】** 所有 C 端页面挂在 `UserLayout` 下，包含：

- `AppHeader` — 顶栏导航（首页 Hero 透明态）
- `<main>` + `<router-view>`
- `AppFooter` — 页脚
- `FloatSupportButton` — 客服浮窗

**【推荐】** 首页使用 `keep-alive` 缓存（已在 `UserLayout` 配置 `include="Home"`）。

### 7.3 路由守卫

**【必须】** 需登录路由设置 `meta.login: true`，由全局 `beforeEach` 统一拦截：

```typescript
if (to.meta.login && !store.isLoggedIn) {
  next({ name: 'Login', query: { redirect: to.fullPath } })
}
```

**【必须】** 登录成功后跳转 `route.query.redirect` 或 `/`。

**【禁止】** 各页面自行实现不一致的登录跳转逻辑。

### 7.4 导航方式

| 场景 | 方式 |
|------|------|
| 站内链接 | `<router-link>` |
| 编程式跳转 | `router.push({ name: 'BookDetail', params: { id } })` |
| 带查询参数 | `router.push({ path: '/books', query: { keyword, category_id } })` |
| 登录 redirect | `query: { redirect: route.fullPath }` |

---

## 八、状态管理（Pinia）

### 8.1 Store 划分

| Store | 文件 | 职责 |
|-------|------|------|
| `useUserStore` | `stores/user.ts` | token、用户信息、VIP、登录/登出、`fetchMe` |
| `useSiteStore` | `stores/site.ts` | 站点氛围、`bg_videos`、首页背景 |

**【必须】** 页面级列表、表单、弹窗状态用组件内 `ref`；**【禁止】** 把单次页面数据放入全局 Store。

### 8.2 User Store 约定

**【必须】** 认证信息持久化 key：

| Key | 说明 |
|-----|------|
| `token` | JWT |
| `user` | 用户信息 JSON |

**【必须】** 登录/注册成功后调用 `store.setAuth(token, user)`；登出调用 `store.logout()`。

**【推荐】** VIP 相关操作后调用 `store.fetchMe()` 刷新状态。

### 8.3 Site Store 约定

**【必须】** 应用启动时 `main.ts` 调用 `useSiteStore().fetchConfig()`。

**【必须】** 背景视频 URL 经 `resolveMediaUrl` + `protectVideoUrl` 处理（见 `site.ts` getters）。

---

## 九、组件开发规范

### 9.1 C 端核心组件

| 组件 | 职责 | 要点 |
|------|------|------|
| `AppHeader` | 顶栏、Hero 透明态、移动端菜单 | 滚动过 Hero 后切换样式 |
| `BookCard` | 书籍卡片 | `resolveMediaUrl` + 封面 error 兜底 |
| `VideoPlayer` | 解读视频播放 | 试看 `maxDuration`、`protectVideoUrl` |
| `EbookReader` | 电子书阅读 | 纯文本/简单 Markdown，**【禁止】** `v-html` 渲染不可信内容 |
| `HeroSearchBox` | 首页搜索 | 跳转书单或联想 |
| `FloatSupportButton` | 客服入口 | 与小程序客服策略一致 |

### 9.2 组件约定

**【必须】** props / emits 声明类型；样式 `scoped`，颜色使用 CSS 变量。

**【推荐】** 单文件顺序：`<script setup>` → `<template>` → `<style scoped>`。

**【禁止】** C 端组件依赖 Element Plus 组件（`<el-button>` 等）；Admin 与 C 端 UI 分离。

### 9.3 图片与视频

| 场景 | 规范 |
|------|------|
| 书籍封面 | `resolveMediaUrl(url, id)` → error 时 `placeholderCover` → `inlineCoverFallback` |
| 用户头像 | `resolveAvatarUrl` / `defaultAvatarImage` |
| 解读视频 | `protectVideoUrl` → `/media/v/bookReview/{name}` |
| 首页背景视频 | `siteStore.bgVideos`（经 `protectVideoUrl`） |
| 远程资源 | 开发期走 Vite 代理；生产使用相对路径或 HTTPS 绝对路径 |

---

## 十、样式与 UI 规范

### 10.1 设计基准

定义于 `src/styles/variables.css`：

| 变量 | 值 | 用途 |
|------|-----|------|
| `--color-primary` | `#5b9aa0` | 主色、按钮、链接强调 |
| `--color-bg` | `#fafafa` | 页面背景 |
| `--color-surface` | `#ffffff` | 卡片/表单背景 |
| `--color-text` | `#1a1a1a` | 主文字 |
| `--color-text-secondary` | `#6b7280` | 次要文字 |
| `--max-width` | `1200px` | 内容区最大宽度 |
| `--radius-card` | `8px` | 卡片圆角 |
| `--bp-tablet` | `1023px` | 平板断点 |
| `--bp-mobile` | `767px` | 手机断点 |

**【必须】** 新样式优先使用 CSS 变量；**【禁止】** 大量硬编码 `#5b9aa0` 以外的主色。

### 10.2 布局与响应式

**【必须】** 内容区使用 `.container`（`max-width` + 左右 padding）。

**【必须】** C 端页面兼顾 **桌面 + 移动端**；`AppHeader` 已实现汉堡菜单，新页面须在 `--bp-mobile` 下验证。

**【推荐】** 使用 `global.css` 已有 `.btn`、`.btn-primary`、`.btn-outline` 按钮样式。

### 10.3 与小程序对齐

| 维度 | C 端 | 小程序 |
|------|------|--------|
| 主色 | `#5b9aa0` | `#5b9aa0` |
| 单位 | `px` / `rem` | `rpx` |
| 变量文件 | `variables.css` | `variables.scss` |
| 文案/信息架构 | **【必须】** 一致 | **【必须】** 一致 |

---

## 十一、媒体 URL 与安全

### 11.1 URL 工具（同构源）

| 用途 | 函数 | 文件 |
|------|------|------|
| 封面/静态图 | `resolveMediaUrl`、`placeholderCover` | `utils/media.ts` |
| 视频保护 | `protectVideoUrl` | `utils/video.ts` |
| 最终兜底封面 | `inlineCoverFallback` | `utils/media.ts` |

路径规则：

```text
/uploads/...           → 封面上传
/placeholders/books/   → 占位 SVG
/media/v/homePage/     → 首页背景视频
/media/v/bookReview/   → 书籍解读视频
```

**【必须】** 修改 `media.ts` / `video.ts` 后，同步检查小程序同名文件是否需要复制更新。

### 11.2 安全清单

- **【必须】** 生产 HTTPS；Token 存 `localStorage`，不写进 URL
- **【禁止】** 在前端代码存放 AppSecret、支付密钥
- **【禁止】** 使用 `v-html` / `innerHTML` 渲染 API 返回的不可信 HTML
- **【必须】** 用户输入展示前做 XSS 意识处理（电子书内容仅 text 渲染）
- **【必须】** 视频/图片 URL 来自 API 或工具函数，禁止拼接未校验的用户输入

---

## 十二、本地开发与联调

### 12.1 启动顺序

1. 启动后端（项目根 `开发文档/本地运行.ps1` 或等价脚本）  
   - Python API：`http://127.0.0.1:8000`  
   - Java Trade：`http://127.0.0.1:8081`
2. 启动前端：`pnpm dev` → `http://127.0.0.1:5188`
3. 浏览器访问 C 端页面验证

### 12.2 联调要点

| 项 | 说明 |
|----|------|
| API | 浏览器请求 `/api/v1/*`，由 Vite 代理到后端 |
| 静态媒体 | `/uploads`、`/media`、`/placeholders` 同样代理 |
| 订单/会员 | 必须启动 Java `:8081`，否则 `/member`、`/orders` 404 |
| Admin 改内容 | 刷新 C 端页面即可看到更新 |

### 12.3 与小程序联调协同

```text
1. Admin 配置内容 → C 端 :5188 验证
2. 同一 API 在小程序验证（无需改 Admin）
3. API/字段变更 → 后端 → C 端 → 小程序 types/api 同步
4. utils/media.ts、video.ts 变更 → 评估小程序复制同步
```

---

## 十三、Git 与协作流程

### 13.1 仓库位置

```text
YuXiaoTuBook/
└── YuXiaotuBook/
    └── frontend/          ← 本文档适用范围（C 端 + Admin 同仓）
```

**【必须】** C 端与 Admin 同仓但 **路由与样式隔离**；C 端 PR 避免无关 Admin 大改。

### 13.2 分支与提交

**【推荐】** 分支命名：`feat/web-{简述}`、`fix/web-{简述}`。

**【推荐】** 提交信息：

```text
feat(web): 书单页增加搜索联想
fix(web): 修复详情页试看结束后未引导登录
```

### 13.3 变更传播

| 变更类型 | 须同步 |
|----------|--------|
| API 字段 | 后端 → C 端 → 小程序 types |
| `media.ts` / `video.ts` | C 端 → 小程序 utils |
| 新 C 端页面 | Dev PRD → 小程序页面（若产品要求对齐） |
| Store 语义变更 | `stores/user.ts`、`site.ts` → 小程序 stores |

---

## 十四、Code Review 检查项

### 14.1 架构

- [ ] 无硬编码书籍/内容数据
- [ ] 新 API 按 Python/Java 边界调用
- [ ] 未在 C 端引用 Admin 组件或 `admin-theme.css`

### 14.2 代码质量

- [ ] `<script setup lang="ts">`
- [ ] 使用 `request()` 而非裸 Axios
- [ ] 检查 `res.code === 200`
- [ ] 封面/视频走 `media.ts` / `video.ts`

### 14.3 体验

- [ ] `useHead` 设置标题
- [ ] 需登录路由有 `meta.login`
- [ ] 移动端宽度可用
- [ ] 空态、加载态有基本处理

### 14.4 构建

- [ ] `pnpm build` 通过
- [ ] 无新增 `any`（或已说明）
- [ ] 小程序同构文件已评估同步

---

## 十五、测试与验收

### 15.1 开发自测（最低要求）

| 步骤 | 预期 |
|------|------|
| 编译 | `pnpm dev` / `pnpm build` 无报错 |
| 首页 | 氛围文案、主推、热门书、背景视频/图 |
| 书单 | 分页 12 条、分类、keyword 搜索 |
| 详情 | 封面、试看/全片、电子书、相似推荐 |
| 登录 | token 写入，Header 显示用户入口 |
| Admin 改标题 | 刷新首页可见新文案 |
| 会员/订单 | mock-pay 后状态更新 |
| 移动端 | Header 汉堡菜单、布局不溢出 |

### 15.2 与小程序对照验收

**【推荐】** 重大功能上线前，对照 [小程序开发规范](./weixintoolDevelopRules.md) 做 AC 项抽查，确保同一账号收藏/订单/VIP 状态一致。

---

## 十六、性能与体验

| 项 | 规范 |
|----|------|
| 列表分页 | 每页 **12** 条（与 API 默认一致） |
| 首页视频 | 同时播放 ≤ 1 路背景视频 |
| 详情视频 | 点击/进入视口后再加载（`VideoPlayer` IntersectionObserver） |
| 路由 | 页面组件 **【推荐】** 懒加载 `() => import(...)` |
| 图片 | `loading="lazy"`（**【推荐】**）；封面 error 兜底 |
| keep-alive | 仅首页等必要时缓存，避免滥用 |

---

## 十七、发版与部署

### 17.1 构建

```powershell
pnpm build
# 产物：dist/
```

### 17.2 部署

生产静态资源由 Nginx/CDN 托管，API 反代至 Python/Java。构建产物部署后 **无需** 重启后端即可更新 UI。

### 17.3 上线前 checklist

- [ ] `pnpm build` 通过
- [ ] 生产 API 域名与 Nginx 配置正确
- [ ] 核心 C 端页面桌面 + 手机走查
- [ ] 登录/注册/订单/会员/mock-pay 流程可用
- [ ] 与小程序共用 API 的字段无 breaking change（或已同步小程序）

---

## 十八、文档维护

| 变更类型 | 须同步更新 |
|----------|------------|
| 新 C 端页面/功能 | Dev PRD、本文档（若涉及新规范） |
| API 增删改 | C 端 API 清单、技术选型.md |
| 同构 utils/stores 变更 | 小程序对应文件 |
| 路由/布局变更 | 本文档 §七 |
| 品牌/UI 变量变更 | `variables.css` + 小程序 `variables.scss` |

**【必须】** 本文档随项目演进修订；重大规范变更递增版本号并填写修订记录。

---

## 十九、附录

### A. C 端 ↔ 小程序文件对照

| C 端（frontend） | 小程序（yuxiaotubookWeixinTool） |
|------------------|----------------------------------|
| `src/api/client.ts` | `src/api/client.ts` |
| `src/stores/user.ts` | `src/stores/user.ts` |
| `src/stores/site.ts` | `src/stores/site.ts` |
| `src/utils/media.ts` | `src/utils/media.ts` |
| `src/utils/video.ts` | `src/utils/video.ts` |
| `src/views/Home.vue` | `src/pages/index/index.vue` |
| `src/views/Books.vue` | `src/pages/books/list.vue` |
| `src/views/BookDetail.vue` | `src/pages/books/detail.vue` |
| `src/components/BookCard.vue` | `src/components/BookCard.vue` |
| `src/components/VideoPlayer.vue` | 小程序原生 `<video>` + 试看逻辑 |

### B. C 端页面 ↔ 路由对照

| 页面文件 | 路由 |
|----------|------|
| `Home.vue` | `/` |
| `Books.vue` | `/books` |
| `BookDetail.vue` | `/books/:id` |
| `Daily.vue` | `/daily` |
| `member/MemberCenter.vue` | `/member` |
| `Login.vue` | `/login` |
| `Register.vue` | `/register` |
| `user/UserCenter.vue` | `/user/center` |
| `user/Orders.vue` | `/user/orders` |
| `user/Favorites.vue` | `/user/favorites` |
| `user/History.vue` | `/user/history` |

### C. 禁止事项汇总

1. 在前端维护书籍/视频/每日等内容 JSON 或静态 CMS
2. 直连数据库或新建 BFF
3. 页面内创建独立 Axios 实例或直接 `fetch` 业务 API
4. 硬编码生产 API 域名
5. C 端页面使用 Element Plus 组件破坏现有 UI 体系
6. C 端引用 `components/admin/` 下组件
7. 使用 `v-html` 渲染不可信 API 内容
8. 与小程序不一致的 Token/Storage 语义（key 均为 `token`、`user`）
9. 未经 API 清单确认调用未文档化接口
10. 仅改 C 端不同步评估小程序 types/api（共用接口时）

### D. 参考链接

- [Vue 3 文档](https://vuejs.org/)
- [Vite 文档](https://vite.dev/)
- [Vue Router 文档](https://router.vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [小程序开发规范](./weixintoolDevelopRules.md)
- [C 端 API 端点清单](../../yuxiaotubookWeixinTool/开发文档/C端API端点清单与OpenAPI对照表.md)

---

**修订记录**

| 版本 | 日期 | 说明 | 作者 |
|------|------|------|------|
| v1.0 | 2026-07-11 | 初版：基于 YuXiaotuBook/frontend C 端工程与配套文档定稿 | — |
