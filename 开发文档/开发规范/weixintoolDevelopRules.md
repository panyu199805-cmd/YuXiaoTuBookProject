# 宇小兔读书 · 微信小程序开发规范

| 项目 | 说明 |
|------|------|
| 文档名称 | weixintoolDevelopRules.md |
| 文档版本 | v1.0 |
| 编写日期 | 2026-07-11 |
| 适用范围 | `yuxiaotubookWeixinTool` 及后续所有小程序功能开发 |
| 项目目录 | `E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\yuxiaotubookWeixinTool` |
| 存放路径 | `E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\开发文档\开发规范\weixintoolDevelopRules.md` |
| 关联文档 | [开发需求文档](../../yuxiaotubookWeixinTool/开发文档/开发需求文档.md) · [技术选型文档](../../yuxiaotubookWeixinTool/开发文档/技术选型文档.md) · [脚手架代码文档](../../yuxiaotubookWeixinTool/开发文档/脚手架代码文档.md) · [C 端 API 端点清单](../../yuxiaotubookWeixinTool/开发文档/C端API端点清单与OpenAPI对照表.md) |

---

## 一、规范定位与强制级别

### 1.1 文档目的

本文档是 **宇小兔读书微信小程序** 的唯一开发规范。所有新功能、重构、Bug 修复、联调与发版，均须遵循本文档；与 Web 用户端冲突时，以 **产品行为 → Dev PRD** 为准，以 **语言/API 归属 → 技术选型文档** 为准。

### 1.2 强制级别说明

| 标记 | 含义 |
|------|------|
| **【必须】** | 违反即视为不合规，Code Review 应拒绝合并 |
| **【推荐】** | 默认做法；特殊场景可偏离，但须在 PR 中说明理由 |
| **【禁止】** | 明确不允许的做法 |

### 1.3 核心原则（1 分钟读完）

1. **【必须】** 小程序与 Web 共用同一套 API、JWT、MySQL；**【禁止】** 在小程序仓库维护书籍/视频/每日等内容数据。
2. **【必须】** 业务逻辑走现有 Python（内容/用户）与 Java（订单/会员）服务；**【禁止】** 新建 BFF 或直连数据库。
3. **【必须】** 页面、Store、工具函数与 Web 保持 **同构**；Web 已有实现时优先对齐，而非另起炉灶。
4. **【必须】** 所有网络与媒体资源走 **HTTPS**；本地 HTTP 须通过 `SecureImage` / `secureMedia` 或 HTTPS 代理处理。
5. **【必须】** 发版仅影响 UI 与客户端逻辑；内容、价格、视频 URL 由 Admin + API 驱动，不依赖小程序发版。

---

## 二、技术栈与工程约束

### 2.1 定版技术栈

| 类别 | 选型 | 版本/说明 |
|------|------|-----------|
| 框架 | uni-app（Vue 3 模式） | 与 `package.json` 锁定版本一致 |
| 语言 | TypeScript | ≥ 4.9，新代码 **【必须】** 使用 TS |
| 构建 | Vite + `@dcloudio/vite-plugin-uni` | 编译目标 `mp-weixin` |
| 状态管理 | Pinia（Composition API 风格） | 与 Web stores 同构 |
| UI | uni-ui + 自定义组件 | 品牌主色 `#5b9aa0` |
| 样式 | SCSS + `variables.scss` | 单位使用 `rpx` |
| 包管理 | pnpm | **【推荐】** 与 monorepo 习惯一致 |
| HTTP | `uni.request` 封装于 `src/api/client.ts` | **【禁止】** 页面内直接 `uni.request` |

### 2.2 后端复用边界

| 服务 | 端口（本地） | 小程序调用方式 | 封装函数 |
|------|--------------|----------------|----------|
| Python FastAPI | 8000 | `API_BASE` | `get` / `post` / `put` / `del` |
| Java trade-service | 8081 | `TRADE_API_BASE` | `tradeGet` / `tradePost` |
| 生产 Nginx | 443 | 统一入口 `www.yuxiaotubook.com` | 生产环境 Python/Java 同域 |

**【必须】** 订单（`/orders`）、会员（`/member`）走 Java；其余走 Python。新增接口前先查 [C 端 API 端点清单](../../yuxiaotubookWeixinTool/开发文档/C端API端点清单与OpenAPI对照表.md) 与 [技术选型.md](../开发需求文档/技术选型.md) 确认语言归属。

### 2.3 环境变量

**【必须】** 通过 `.env.development` / `.env.production` 配置，禁止在业务代码硬编码域名。

| 变量 | 开发示例 | 生产 |
|------|----------|------|
| `VITE_API_BASE` | `https://192.168.x.x:8443/api/v1` 或局域网 IP | `https://www.yuxiaotubook.com/api/v1` |
| `VITE_MEDIA_ORIGIN` | 与 API 同主机 | `https://www.yuxiaotubook.com` |
| `VITE_TRADE_API_BASE` | 可选；默认由 `env.ts` 推导 `:8444` 或 `:8081` | 与 `VITE_API_BASE` 同域 |

**【必须】** 修改 env 后重新执行 `pnpm dev:mp-weixin` 或 `build-mp-local.bat`，并在微信开发者工具中 **重新编译**。

**【禁止】** 将 `.env.production`、AppID、密钥提交到 Git；`.env.development.local` 用于个人局域网 IP 覆盖。

---

## 三、目录结构与文件归属

### 3.1 标准目录

```text
yuxiaotubookWeixinTool/
├── src/
│   ├── api/              # HTTP 封装与按域划分的 API 模块
│   ├── components/       # 可复用 UI 组件
│   ├── composables/      # 组合式函数（跨页面逻辑）
│   ├── config/           # env 等全局配置
│   ├── pages/            # 页面（按业务分子目录）
│   ├── static/           # 小体积本地静态资源（Tab 图标等）
│   ├── stores/           # Pinia Store
│   ├── styles/           # 全局 SCSS 变量与公共样式
│   ├── types/            # TypeScript 类型定义
│   └── utils/            # 纯函数工具（无 UI）
├── scripts/              # 构建、联调、检测脚本
├── 开发文档/              # 需求、选型、API 清单（子目录）
└── dist/dev|build/mp-weixin/   # 编译产物（不手改）
```

### 3.2 文件放置规则

| 内容 | 放置位置 | 说明 |
|------|----------|------|
| 页面级 UI 与交互 | `src/pages/{模块}/{页面}.vue` | 一个路由对应一个文件 |
| 跨页面复用组件 | `src/components/` | PascalCase 命名 |
| 接口请求 | `src/api/{域}.ts` | 如 `books.ts`、`trade.ts` |
| 响应/实体类型 | `src/types/{域}.ts` | 与 API 模块对应 |
| 全局状态 | `src/stores/` | 仅 `user`、`site` 等跨页状态 |
| 媒体/视频/存储工具 | `src/utils/` | 与 Web 同名模块保持逻辑一致 |

**【禁止】** 在 `pages/` 下新建 `api/`、`utils/` 副本；**【禁止】** 直接修改 `dist/` 下编译产物。

### 3.3 新增页面流程

1. 在 `src/pages/` 创建 `.vue` 文件；
2. 在 `src/pages.json` 注册路由（Tab 页须同步 `tabBar.list`）；
3. 若涉及新 API，在 `src/api/` + `src/types/` 补充；
4. 更新 [开发需求文档](../../yuxiaotubookWeixinTool/开发文档/开发需求文档.md) 页面清单（若为新功能）；
5. 本地走查 + 体验版验证。

---

## 四、命名规范

### 4.1 文件与目录

| 类型 | 规范 | 示例 |
|------|------|------|
| 页面目录 | 小写，业务语义 | `pages/books/list.vue` |
| 组件文件 | PascalCase | `BookCard.vue`、`SecureImage.vue` |
| API 模块 | 小写单数 | `books.ts`、`trade.ts` |
| Store | 小写单数 | `user.ts`、`site.ts` |
| 类型文件 | 小写单数 | `book.ts`、`api.ts` |
| 工具文件 | camelCase | `secureMedia.ts`、`storage.ts` |

### 4.2 代码标识符

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件名 | PascalCase | `BookCard` |
| 变量/函数 | camelCase | `loadHomeData`、`isLoggedIn` |
| 常量 | UPPER_SNAKE_CASE | `TOKEN_KEY`、`MP_CLIENT_VERSION` |
| 类型/接口 | PascalCase | `BookListItem`、`ApiResponse` |
| Store | `use` + PascalCase | `useUserStore` |
| API 函数 | 动词开头 camelCase | `listBooks`、`getPlayAuth` |
| 事件处理 | `on` + 动作 或 `handle` + 动作 | `onCoverError`、`handleSubmit` |

### 4.3 API 与后端字段

**【必须】** 请求/响应 JSON 字段使用 **snake_case**，与后端一致（如 `book_id`、`package_id`、`is_vip`）。

**【禁止】** 在 `types/` 中把后端字段改成 camelCase 除非在 API 层做显式映射（当前项目 **不做** 自动转换）。

---

## 五、Vue 与 TypeScript 编码规范

### 5.1 组件写法

**【必须】** 新组件统一使用 `<script setup lang="ts">` + Composition API。

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { BookListItem } from '@/types/book'

const props = defineProps<{
  book: BookListItem
}>()

const emit = defineEmits<{
  select: [id: number]
}>()
</script>
```

**【禁止】** 新增 Options API 组件（除非改造遗留代码且范围可控）。

### 5.2 模板标签映射（相对 Web）

| Web | 小程序 | 说明 |
|-----|--------|------|
| `<div>` | `<view>` | 块级容器 |
| `<span>` / `<p>` | `<text>` | 文本 |
| `<img>` | `<image>` 或 `SecureImage` | 远程封面 **【必须】** 用 `SecureImage` |
| `<a>` / `<router-link>` | `uni.navigateTo` 等 | 见 §7.2 |
| `localStorage` | `uni.getStorageSync` | 封装在 `utils/storage.ts` |

### 5.3 类型

**【必须】** 所有 API 返回值、Store 状态、组件 props 声明 TypeScript 类型；**【禁止】** 滥用 `any`。

**【推荐】** 共用类型放 `src/types/`，页面内仅声明 UI 局部类型。

**【必须】** 从 `@/` 别名导入，路径与 Web 习惯一致：

```typescript
import { getFeatured } from '@/api/home'
import type { BookListItem } from '@/types/book'
```

### 5.4 异步与错误

**【必须】** 页面数据加载使用 `try/finally` 或 `Promise.allSettled`，避免未捕获 Promise rejection。

**【推荐】** 列表/首页并发请求不超过 4 个；部分失败时 `console.warn` 并展示已有数据，而非整页白屏。

```typescript
const results = await Promise.allSettled([getFeatured(), getHotBooks(1, 12)])
if (results[0].status === 'fulfilled') featured.value = results[0].value
```

**【禁止】** 在页面内重复实现 401 处理、Toast 提示；统一依赖 `api/client.ts`。

---

## 六、API 层规范

### 6.1 分层职责

| 层级 | 文件 | 职责 |
|------|------|------|
| 传输层 | `api/client.ts` | `uni.request`、401、错误 Toast、trade 路由 |
| 领域层 | `api/books.ts` 等 | 路径拼接、参数、`fetchData` 解包 |
| 类型层 | `types/*.ts` | 请求/响应结构 |

**【必须】** 页面与 Store **只调用** `api/{域}.ts` 导出函数，不直接调用 `request()`（除非扩展 client 本身）。

### 6.2 请求约定

```typescript
// 公开接口，无需登录
export function listBooks(params: BookQuery = {}) {
  return fetchData(get<PageResult<BookListItem>>(`/books?${qs}`, false))
}

// 需登录，401 不跳转（如试看权限探测）
export function getPlayAuth(id: number) {
  return fetchData(get<PlayAuth>(`/books/${id}/play-auth`, { auth: true, redirectOn401: false }))
}

// Java 交易
export function listOrders() {
  return fetchData(tradeGet<OrderInfo[]>('/orders', { redirectOn401: false }))
}
```

| 参数 | 含义 |
|------|------|
| `auth: false` | 不带 Token |
| `redirectOn401: false` | 401 时不跳转登录（用于可选登录场景） |
| `fetchData()` | 解包 `ApiResponse.data`，简化调用方 |

### 6.3 响应处理

**【必须】** 以 `code === 200`（或字符串 `'200'`）为成功；信封结构 `{ code, msg, data }`。

**【必须】** 401 时调用 `clearAuth()` 并按需跳转 `/pages/auth/login?redirect=...`。

### 6.4 新增接口 checklist

- [ ] 已在 C 端 API 清单或 OpenAPI 中确认路径与方法
- [ ] 确认 Python 或 Java 归属，选用正确的 `get/post` 或 `tradeGet/tradePost`
- [ ] 在 `types/` 补充类型
- [ ] 在对应 `api/*.ts` 导出函数
- [ ] Web 端若共用接口，字段变更需同步 Web `frontend`

---

## 七、路由与页面规范

### 7.1 页面注册

**【必须】** 所有页面在 `src/pages.json` 注册；Tab 页路径与 `tabBar.list` 一致。

| 页面 | 路径 | Tab | 下拉刷新 |
|------|------|-----|----------|
| 首页 | `pages/index/index` | 是 | 是 |
| 书单 | `pages/books/list` | 是 | 是 |
| 书籍详情 | `pages/books/detail` | 否 | — |
| 每日读书 | `pages/daily/index` | 是 | 是 |
| 会员中心 | `pages/member/index` | 否 | — |
| 登录/注册 | `pages/auth/login` · `register` | 否 | — |
| 个人中心 | `pages/user/center` | 是 | — |
| 订单/收藏/历史 | `pages/user/*` | 否 | 订单列表推荐开启 |

### 7.2 导航 API 选用

| 场景 | API | 示例 |
|------|-----|------|
| 切换 Tab | `uni.switchTab` | 首页 ↔ 书单 |
| 普通跳转 | `uni.navigateTo` | 详情、登录 |
| 替换当前页 | `uni.redirectTo` | 登录成功后 |
| 返回 Tab 并清栈 | `uni.reLaunch` | 登出回首页（慎用） |

**【必须】** Tab 页之间 **【禁止】** 使用 `navigateTo`；带参跳转 Tab 时 **【推荐】** 使用全局 Store 或 `eventChannel` 传递 keyword/category_id。

### 7.3 页面生命周期

| 场景 | 钩子 | 说明 |
|------|------|------|
| 每次展示刷新 | `onShow` | 首页、个人中心 VIP 状态 |
| 首次加载 | `onMounted` | 纯客户端初始化 |
| 下拉刷新 | `onPullDownRefresh` + `enablePullDownRefresh` | 结束时 `uni.stopPullDownRefresh()` |
| 分享 | `onShareAppMessage` | 详情、每日读书 **【推荐】** 实现 |

### 7.4 登录拦截

**【必须】** 需登录页面在 `onShow` 或操作前检查 `useUserStore().isLoggedIn`；未登录跳转：

```typescript
uni.navigateTo({
  url: `/pages/auth/login?redirect=${encodeURIComponent('/pages/user/orders')}`,
})
```

**【禁止】** 在多个页面复制不同的登录跳转逻辑；401 以 `client.ts` 为准，页面只做前置校验。

---

## 八、状态管理（Pinia）

### 8.1 Store 划分

| Store | 文件 | 职责 |
|-------|------|------|
| `useUserStore` | `stores/user.ts` | token、用户信息、登录/注册/登出 |
| `useSiteStore` | `stores/site.ts` | 站点氛围、背景视频、promo 文案 |

**【必须】** 页面级列表、表单状态用组件内 `ref`；**【禁止】** 把单次请求结果放入全局 Store（除非 Web 已同构且需跨 Tab 共享）。

### 8.2 Store 写法

**【必须】** 新 Store 使用 Composition API 风格（与现有 `user.ts` 一致）：

```typescript
export const useUserStore = defineStore('user', () => {
  const token = ref(getToken())
  const isLoggedIn = computed(() => !!token.value)
  async function login(username: string, password: string) { /* ... */ }
  return { token, isLoggedIn, login }
})
```

### 8.3 持久化

**【必须】** Token 与用户信息读写统一走 `utils/storage.ts`（`yxt_token`、`yxt_user`）。

**【禁止】** 页面直接 `uni.setStorageSync('token', ...)` 或使用与 Web 不一致的 key。

---

## 九、组件开发规范

### 9.1 组件分类

| 类型 | 示例 | 要求 |
|------|------|------|
| 业务组件 | `BookCard`、`EbookReader` | 对齐 Web 同名组件交互与文案 |
| 媒体组件 | `SecureImage`、`HeroVideoLayer` | 处理 HTTPS / 本地 HTTP 差异 |
| 反馈组件 | `EmptyState` | 空列表、加载失败统一视觉 |

### 9.2 组件约定

**【必须】** props 用 `defineProps` 并声明类型；事件用 `defineEmits` 声明。

**【必须】** 样式使用 `scoped` + `@import '@/styles/variables.scss'`。

**【推荐】** 单文件组件顺序：`<script setup>` → `<template>` → `<style lang="scss" scoped>`。

### 9.3 图片与视频

| 场景 | 规范 |
|------|------|
| 书籍封面 | **【必须】** `SecureImage` + `resolveMediaUrl` + `placeholderCover` 兜底 |
| 背景/轮播视频 | **【必须】** `protectVideoUrl`；本地仅 `MEDIA_ORIGIN` 为 HTTPS 时播放 |
| 详情页视频 | 原生 `<video>`；试看逻辑与 Web `VideoPlayer` 一致 |
| 远程 URL | **【必须】** 完整 HTTPS；**【禁止】** 相对路径给 `<image>` / `<video>` |

**【必须】** 本地 HTTP 媒体通过 `utils/secureMedia.ts` 的 `toMpSafeMediaUrl` 下载后展示，不得绕过。

---

## 十、样式与 UI 规范

### 10.1 设计基准

| 项 | 值 |
|----|-----|
| 设计稿宽度 | 750rpx |
| 主色 | `#5b9aa0`（`$color-primary`） |
| 页面背景 | `#f7f8fa`（`$color-bg`） |
| Tab 选中色 | `#5b9aa0` |
| 圆角 | 卡片 `$radius-card: 16rpx` |

**【必须】** 颜色、间距优先使用 `styles/variables.scss` 变量；**【禁止】** 页面内大量硬编码色值。

### 10.2 单位

**【必须】** 布局尺寸使用 `rpx`；**【禁止】** 混用 `px`（除 1px 边框等特殊情况）。

换算参考：`1px ≈ 2rpx`（iPhone 6 基准）。

### 10.3 与 Web 对齐

**【必须】** 文案、信息架构、信任条、会员权益说明与 Web 用户端一致；Admin 改内容后小程序仅展示 API 返回，不写死文案（除固定 UI 标签如「搜索」「登录」）。

---

## 十一、媒体 URL 与安全

### 11.1 URL 解析

**【必须】** 使用统一工具，禁止页面内拼接：

| 用途 | 函数 | 文件 |
|------|------|------|
| 封面/静态图 | `resolveMediaUrl` | `utils/media.ts` |
| 视频 | `protectVideoUrl` | `utils/video.ts` |
| 占位图 | `placeholderCover` | `utils/media.ts` |

路径规则与 Web 一致：

```text
/uploads/...           → 封面
/placeholders/...      → 占位
/media/v/homePage/     → 首页背景视频
/media/v/bookReview/   → 书籍解读视频
```

### 11.2 安全清单

- **【必须】** 生产环境 HTTPS only
- **【必须】** Token 不打印到 console（生产包）；开发可用 `[YXT-MP]` + `MP_CLIENT_VERSION` 标识构建
- **【禁止】** 将 AppSecret、支付密钥写入前端
- **【禁止】** 用 `rich-text` 渲染不可信 HTML（电子书用 text 分段）
- **【必须】** 视频/图片 URL 来自 API 或 `resolveMediaUrl`，禁止拼接用户输入

---

## 十二、条件编译与平台差异

### 12.1 使用场景

**【推荐】** 仅在必要时使用 uni-app 条件编译：

```javascript
// #ifdef MP-WEIXIN
onShareAppMessage(() => ({ title: '...', path: '...' }))
// #endif
```

| 能力 | 平台 API |
|------|----------|
| 微信登录（二期） | `wx.login` |
| 微信支付（二期） | `wx.requestPayment` |
| 客服 | `button open-type="contact"` |
| 分享 | `onShareAppMessage` |

### 12.2 微信基础库

**【必须】** 最低基础库 ≥ 2.25.0；关注 3.15+ 对 HTTP 媒体的限制（见 README）。

---

## 十三、本地开发与联调规范

### 13.1 启动顺序

1. 启动后端：`开发文档/本地运行.ps1`（Python :8000，Java :8081）
2. 小程序：`.\start-mp-simulator.bat` 或 `pnpm dev:mp-weixin`
3. 微信开发者工具导入 **`dist/dev/mp-weixin`**
4. 勾选 **不校验合法域名**；HTTPS 本地代理时勾选 **不校验 TLS 证书**

### 13.2 模拟器 vs 真机

| 环境 | 要求 |
|------|------|
| PC 模拟器 | 可用 `127.0.0.1` 或 HTTPS 8443 |
| 真机 | **【必须】** 局域网 IP + HTTPS 代理（`dev-https-proxy.bat`）或 mkcert |
| 修改 env | **【必须】** 重新编译 + 开发者工具重新编译 |

### 13.3 构建标识

**【必须】** 每次发版或排查缓存问题时，递增 `src/config/env.ts` 中的 `MP_CLIENT_VERSION`；Console 出现 `[YXT-MP]` 表示已加载对应构建。

### 13.4 常用脚本

| 脚本 | 用途 |
|------|------|
| `start-mp-simulator.bat` | 模拟器一键联调 |
| `start-mp-real-device.bat` | 真机调试 |
| `build-mp-local.bat` | 本地 env 构建 |
| `check-mp-api.bat` | 检测并修正 API IP |
| `dev-https-proxy.bat` | HTTPS 代理 8443/8444 |

---

## 十四、Git 与协作流程

### 14.1 仓库位置

小程序代码位于 monorepo：

```text
YuXiaoTuBook/yuxiaotubookWeixinTool/
```

**【必须】** 与 Web、后端同仓管理；独立 `package.json`，构建产物不入库（已在 `.gitignore`）。

### 14.2 分支与提交

**【推荐】** 功能分支命名：`feat/mp-{简述}`、`fix/mp-{简述}`。

**【推荐】** 提交信息格式：

```text
feat(mp): 书籍详情页增加分享
fix(mp): 修复订单列表 401 重复跳转
```

### 14.3 与 Web / Admin 协同

```text
Admin 改内容 → Web 验证 → 小程序同 API 验证
API 字段变更 → 先后端 + Admin → Web frontend → 小程序 types + api + 页面
```

**【禁止】** 仅改小程序而不更新 types/API 层；**【禁止】** 小程序单独加字段 mock 数据上线。

---

## 十五、Code Review 检查项

提交 PR 或合并前，审查人 **【必须】** 核对：

### 15.1 架构

- [ ] 无硬编码内容数据、无直连 MySQL
- [ ] 新 API 已按 Python/Java 边界调用
- [ ] 类型定义完整，无新增 `any`

### 15.2 代码质量

- [ ] 使用 `<script setup lang="ts">`
- [ ] 网络请求经 `api/` 层
- [ ] 401/错误提示未在页面重复实现
- [ ] 远程图片使用 `SecureImage`

### 15.3 体验

- [ ] Tab 跳转使用 `switchTab`
- [ ] 需登录功能有拦截或依赖 client 401
- [ ] 空态、加载态有处理
- [ ] 文案与 Web 一致

### 15.4 发版

- [ ] `MP_CLIENT_VERSION` 已更新（若有 client/env 变更）
- [ ] 生产 env 指向 `www.yuxiaotubook.com`
- [ ] 微信公众平台合法域名已配置（生产）

---

## 十六、测试与验收

### 16.1 开发自测（最低要求）

| 步骤 | 预期 |
|------|------|
| 编译 | `pnpm dev:mp-weixin` 无报错 |
| 首页 | promo、daily_sentence、热门书展示 |
| 书单 | 分页、分类、搜索 |
| 详情 | 封面、试看/全片、电子书 |
| 登录 | token 写入，个人中心显示用户 |
| Admin 改标题 | 小程序刷新后文案更新 |
| 订单/会员 | mock-pay 后列表可见 |

完整验收标准见 [开发需求文档 §七](../../yuxiaotubookWeixinTool/开发文档/开发需求文档.md)。

### 16.2 类型检查

**【推荐】** 提交前执行：

```powershell
pnpm type-check
```

---

## 十七、性能与包体

| 项 | 规范 |
|----|------|
| 主包体积 | **【推荐】** ≤ 1.5MB |
| 列表分页 | 每页 12 条，与 Web 一致 |
| 首页并发 | `Promise.allSettled` ≤ 4 个请求 |
| 图片 | 远程 lazy-load；**【禁止】** 打包大体积图片/视频 |
| 视频 | 首页同时解码 ≤ 1 路；详情点击后再加载 |
| 分包 | 主包接近 2MB 时将详情/电子书迁入 `subPackages`（见脚手架文档 §十） |

---

## 十八、发版与上线

### 18.1 构建生产包

```powershell
pnpm build:mp-weixin
# 产物：dist/build/mp-weixin
```

### 18.2 上线前 checklist

- [ ] `manifest.json` → `mp-weixin.appid` 正确
- [ ] `.env.production` 域名正确
- [ ] 微信公众平台 request/upload/download 合法域名已配置
- [ ] 体验版全页面走查（iOS + Android）
- [ ] 支付：内测可用 mock-pay；正式上线 **【必须】** 接微信支付
- [ ] 用户协议、隐私政策可访问（WebView 或原生页）

### 18.3 审核注意

- 图书解读类目需资质说明
- 一期 mock-pay 仅内测；正式版禁止误导性「假支付」文案

---

## 十九、文档维护

| 变更类型 | 须同步更新的文档 |
|----------|------------------|
| 新页面/功能 | 开发需求文档、本文档（若涉及新规范） |
| 技术栈/架构 | 技术选型文档、脚手架代码文档 |
| API 增删改 | C 端 API 端点清单、types、api 模块 |
| 目录/脚本变更 | 脚手架代码文档、README |
| 开发流程变更 | **本文档** |

**【必须】** 本文档随项目演进修订；每次重大规范变更递增文档版本号并填写修订记录。

---

## 二十、附录

### A. Web → 小程序文件对照（维护同构时参考）

| Web | 小程序 |
|-----|--------|
| `frontend/src/api/client.ts` | `src/api/client.ts` |
| `frontend/src/stores/user.ts` | `src/stores/user.ts` |
| `frontend/src/stores/site.ts` | `src/stores/site.ts` |
| `frontend/src/utils/video.ts` | `src/utils/video.ts` |
| `frontend/src/utils/media.ts` | `src/utils/media.ts` |
| `frontend/src/components/BookCard.vue` | `src/components/BookCard.vue` |
| `frontend/src/views/Home.vue` | `src/pages/index/index.vue` |
| `frontend/src/views/BookDetail.vue` | `src/pages/books/detail.vue` |

### B. 禁止事项汇总

1. 在小程序仓库维护书籍/视频/每日等内容 JSON 或静态 CMS
2. 新建 BFF 或直连 MySQL
3. 页面内直接 `uni.request`
4. 硬编码生产 API 域名或密钥
5. 相对路径作为 `<image>` / `<video>` 的 src
6. 使用 `rich-text` 渲染不可信 HTML
7. 修改 `dist/` 编译产物
8. Tab 页使用 `navigateTo` 跳转
9. 与 Web 不一致的 Storage key 或 JWT 处理方式
10. 未经 API 清单确认擅自调用未文档化接口

### C. 参考链接

- [uni-app Vue3 文档](https://uniapp.dcloud.net.cn/)
- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [项目 README](../../yuxiaotubookWeixinTool/README.md)

---

**修订记录**

| 版本 | 日期 | 说明 | 作者 |
|------|------|------|------|
| v1.0 | 2026-07-11 | 初版：基于现有 yuxiaotubookWeixinTool 工程与配套文档定稿 | — |
