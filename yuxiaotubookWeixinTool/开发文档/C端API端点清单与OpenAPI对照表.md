# 宇小兔读书 · C 端 API 端点清单与 OpenAPI 对照表

| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 编写日期 | 2026-07-10 |
| 适用范围 | **Web 用户端** 与 **微信小程序** 共用（Admin 不在此列） |
| Base URL（生产） | `https://www.yuxiaotubook.com/api/v1` |
| Base URL（本地） | `http://127.0.0.1:8000/api/v1`（Java 订单/会员经 Nginx 或 Vite 代理到 `:8081`） |

---

## 一、使用说明

### 1.1 这份文档是什么

- **端点清单**：Web C 端与微信小程序 **必须复用同一份接口**，禁止小程序单独建 BFF 或维护内容数据。
- **OpenAPI 对照**：Python FastAPI 端点可在本地 OpenAPI 文档中查看；Java 交易服务无独立 Swagger，以本文 + 源码为准。

### 1.2 通用约定

| 项 | 约定 |
|----|------|
| 认证 | `Authorization: Bearer {token}`（JWT，与 Web `localStorage.token` 相同） |
| 响应信封 | `{ "code": number, "msg": string, "data": T \| null }` |
| 成功 | `code === 200` |
| 登录返回 | `data.token` + `data.user`（**不是** `access_token`） |
| JSON 字段 | Python 与 Java 均使用 **snake_case**（Java 配置了 `SNAKE_CASE`） |
| 401 | 清除 token，跳转登录页 |

### 1.3 OpenAPI 文档地址

| 服务 | 文档 URL | 说明 |
|------|----------|------|
| Python FastAPI | `http://127.0.0.1:8000/docs` | 仅 `DEBUG=true` 时开启 |
| Python OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` | 可导入 Postman / Apifox |
| Java trade-service | 无 Swagger | 见本文 §三 |

**OpenAPI 覆盖范围：** 仅 Python 侧 C 端 + Admin 路由。Java `/orders`、`/member` **不在** FastAPI OpenAPI 中，需按本文 §三 实现。

---

## 二、端点总览（25 个 JSON + 3 类静态资源）

### 2.1 按后端划分

| 后端 | 端口 | 路径前缀 | 端点数 |
|------|------|----------|--------|
| Python FastAPI | 8000 | 除 orders/member 外 | 18 |
| Java trade-service | 8081 | `/orders`、`/member` | 7 |
| Nginx / 静态 | — | `/uploads`、`/media/v`、`/placeholders` | 3 类 |

### 2.2 按 Web / 小程序页面划分

| 页面 | 路由/路径 | 端点 |
|------|-----------|------|
| 全局 | App 启动 | `GET /site/config`、`GET /auth/me` |
| 首页 | `/` / `pages/index` | `GET /home/featured`、`GET /home/hot-books`、`GET /categories` |
| 书单 | `/books` / `pages/books/list` | `GET /books`、`GET /categories` |
| 书籍详情 | `/books/:id` / `pages/books/detail` | `GET /books/{id}`、`GET /books/{id}/play-auth`、`GET /books/{id}/similar`、`POST /favorites`、`POST /orders`、`POST /orders/{id}/mock-pay` |
| 每日读书 | `/daily` / `pages/daily` | `GET /daily/today`、`GET /daily/list`、`POST /daily/{id}/like` |
| 会员中心 | `/member` / `pages/member` | `GET /member/packages`、`GET /member/status`、`POST /member/subscribe`、`POST /member/orders/{id}/mock-pay` |
| 登录 | `/login` | `POST /auth/login` |
| 注册 | `/register` | `POST /auth/register` |
| 我的订单 | `/user/orders` | `GET /orders` |
| 我的收藏 | `/user/favorites` | `GET /favorites` |
| 浏览记录 | `/user/history` | `GET /history` |
| 个人中心 | `/user/center` | `GET /auth/me`、`GET /categories`、`GET /user/preferences`、`PUT /user/preferences`、`GET /user/orders/shipping`、`GET /member/status` |

---

## 三、Python FastAPI 端点明细（含 OpenAPI 对照）

> OpenAPI Tag 来自 `backend/app/core/openapi.py`  
> 源码路径：`YuXiaotuBook/backend/app/api/v1/`

### 3.1 站点与首页

#### `GET /site/config`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `站点` |
| 认证 | 否 |
| Web 引用 | `stores/site.ts` |
| 小程序 | `stores/site.ts` |

**响应 `data` 字段：**

```json
{
  "bg_type": "image | video",
  "bg_url": "/uploads/...",
  "bg_videos": ["/uploads/homePage/xxx.mp4"],
  "bg_music": "string | null",
  "white_noise": "string | null",
  "music_enabled": true,
  "bg_enabled": true,
  "promo_title": "string",
  "daily_sentence": "string"
}
```

**小程序注意：** 视频 URL 需 `protectVideoUrl()` 转为 `/media/v/homePage/{basename}` 完整 HTTPS。

---

#### `GET /categories`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `站点` |
| 认证 | 否 |

**响应 `data`：** `[{ "id": 1, "name": "心理学", "slug": "psychology" }]`

---

#### `GET /home/featured`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `首页` |
| 认证 | 否 |

**响应 `data`：** 书籍对象或 `null`（见 §3.3 书籍列表项结构）。

---

#### `GET /home/hot-books`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `首页` |
| 认证 | 否 |
| Query | `page=1`, `page_size=12` |

**响应 `data`：**

```json
{
  "list": [ /* BookListItem[] */ ],
  "total": 100,
  "page": 1,
  "page_size": 12
}
```

---

### 3.2 认证

#### `POST /auth/register`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `用户-认证` |
| 认证 | 否 |

**请求 body：**

```json
{
  "username": "abc123",
  "password": "12345678",
  "nickname": "可选",
  "province": "可选",
  "city": "可选"
}
```

**响应 `data`：**

```json
{
  "token": "eyJ...",
  "user": { "id": 1, "username": "abc123", "nickname": "昵称", "role": "user" }
}
```

---

#### `POST /auth/login`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `Admin-认证`（与用户共用） |
| 认证 | 否 |

**请求 body：** `{ "username": "...", "password": "..." }`  
**响应 `data`：** 同注册。

---

#### `GET /auth/me`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `Admin-认证` |
| 认证 | **是** |

**响应 `data`：**

```json
{
  "id": 1,
  "username": "abc123",
  "nickname": "昵称",
  "avatar": "/uploads/...",
  "role": "user",
  "is_vip": false,
  "vip_expire_time": "2026-12-31T23:59:59"
}
```

---

### 3.3 书籍

#### `GET /books`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `书籍` |
| 认证 | 否 |
| Query | `page`, `page_size`, `sort=hot|new`, `keyword`, `category_id` |

**响应 `data`：** `{ list, total, page, page_size }`

**BookListItem 结构：**

```json
{
  "id": 1,
  "title": "书名",
  "author": "作者",
  "cover": "/uploads/...",
  "highlight": "一句话亮点",
  "category": { "id": 1, "name": "心理学" },
  "price": 39.9,
  "has_video": true,
  "view_count": 100
}
```

---

#### `GET /books/{book_id}`

| 项 | 值 |
|----|-----|
| 认证 | 可选（已登录时 **自动写入浏览记录** collect_type=2） |

**响应 `data` 额外字段（在 BookListItem 基础上）：**

```json
{
  "stock": 100,
  "summary": "摘要",
  "target_audience": "适读人群",
  "status": "published",
  "video": { "duration": 600, "cover": "...", "intro": "..." },
  "ebook_title": "电子书标题",
  "ebook_content": "电子书正文"
}
```

---

#### `GET /books/{book_id}/play-auth`

| 项 | 值 |
|----|-----|
| 认证 | 可选 |

**响应 `data`：**

```json
{
  "video_url": "/media/v/bookReview/xxx",
  "poster": "/uploads/...",
  "duration": 600,
  "full_access": false,
  "max_duration": 180,
  "is_vip": false
}
```

| 场景 | full_access | max_duration |
|------|-------------|--------------|
| 未登录 | false | 180（可配置 `GUEST_VIDEO_PREVIEW_SECONDS`） |
| 已登录 | true | null |

---

#### `GET /books/{book_id}/similar`

| 项 | 值 |
|----|-----|
| 认证 | 否 |
| 响应 | `BookListItem[]` |

---

#### `POST /books/{book_id}/play-report`

| 项 | 值 |
|----|-----|
| 认证 | 否 |
| Web 现状 | **未调用** |
| 小程序 | Phase 2 可选 |

**请求 body：** `{ "position": 30 }`（播放 ≥30 秒上报一次）

---

### 3.4 每日读书

#### `GET /daily/today`

| 项 | 值 |
|----|-----|
| OpenAPI Tag | `每日读书` |
| 认证 | 否 |

**响应 `data`（DailyItem 或 null）：**

```json
{
  "id": 1,
  "book_id": 3,
  "daily_sentence": "今日金句",
  "daily_intro": "导读",
  "publish_date": "2026-07-10",
  "is_top": false,
  "like_count": 12,
  "book": { /* BookListItem */ }
}
```

---

#### `GET /daily/list`

| Query | `page=1`, `page_size=10` |
| 响应 | `{ list: DailyItem[], total, page, page_size }` |

---

#### `POST /daily/{daily_id}/like`

| 认证 | 否 |
| 响应 `data` | `{ "like_count": 13 }` |

---

### 3.5 收藏与浏览记录

#### `POST /favorites`

| 认证 | **是** |
| Body | `{ "book_id": 1 }` |

#### `GET /favorites`

| 认证 | **是** |
| 响应 | `BookListItem[]` |

#### `DELETE /favorites/{book_id}`

| 认证 | **是** |
| Web 现状 | **未调用** |
| 小程序 | Phase 2 建议接入 |

#### `GET /history`

| 认证 | **是** |
| 响应 | `BookListItem[]`（collect_type=2） |
| 写入方式 | 已登录用户访问 `GET /books/{id}` 时后端自动写入，**无需单独 POST** |

---

### 3.6 用户个人中心

#### `GET /user/preferences`

| OpenAPI Tag | `用户-个人中心` |
| 认证 | **是** |

**响应 `data`：**

```json
{
  "category_ids": [1, 2],
  "scene_tags": ["commute", "before_sleep"],
  "bio": "个人简介"
}
```

`scene_tags` 允许值：`commute` | `before_sleep` | `weekend` | `career`

---

#### `PUT /user/preferences`

| Body | 同 GET 响应结构 |
| 认证 | **是** |

---

#### `GET /user/orders/shipping`

| 认证 | **是** |
| 说明 | Python 读 Order 表，含物流字段；与 Java `GET /orders` 互补 |

**响应 `data`：** Order 对象数组（含 `ship_company`, `ship_tracking_no`, `shipped_at`, `status_label`, `items` 等）

---

## 四、Java trade-service 端点明细（无 OpenAPI）

> 源码：`yuxiaotu-trade-service/src/main/java/com/yuxiaotu/trade/controller/`  
> JSON 命名：**snake_case**（`spring.jackson.property-naming-strategy: SNAKE_CASE`）

### 4.1 购书订单

#### `POST /orders`

| 认证 | **是** |

**请求 body：**

```json
{
  "book_id": 1,
  "quantity": 1,
  "receiver_name": "张三",
  "receiver_phone": "13800138000",
  "receiver_address": "详细地址"
}
```

**响应 `data`（OrderVO）：** 含 `id`, `order_no`, `status`, `total_amount`, `items` 等。

---

#### `GET /orders`

| 认证 | **是** |
| 响应 | `OrderVO[]` |

**Web 使用字段：** `order_no`, `status`, `items[].book_title`, `items[].quantity`, `total_amount`

---

#### `POST /orders/{order_id}/mock-pay`

| 认证 | **是** |
| 说明 | 一期模拟支付，内测/开发用 |

---

#### `GET /orders/{order_id}`、`POST /orders/{order_id}/cancel`

| Web 现状 | **未调用** |
| 小程序 | 可选扩展 |

---

### 4.2 会员

#### `GET /member/packages`

| 认证 | 否 |

**响应 `data`：**

```json
[
  {
    "id": 1,
    "package_name": "月度会员",
    "price": 19.9,
    "valid_day": 30,
    "rights": ["权益1", "权益2"]
  }
]
```

---

#### `GET /member/status`

| 认证 | **是** |

**响应 `data`：**

```json
{
  "is_vip": true,
  "expire_time": "2026-08-10T00:00:00",
  "package_id": 1,
  "package_name": "月度会员"
}
```

---

#### `POST /member/subscribe`

| 认证 | **是** |
| Body | `{ "package_id": 1 }` |
| 响应 `data` | 含 `id`（会员订单 ID，用于 mock-pay） |

---

#### `POST /member/orders/{order_id}/mock-pay`

| 认证 | **是** |

---

#### `POST /member/orders/{order_id}/pay`

| 状态 | 返回 501「真实支付尚未配置」 |
| 小程序 Phase 3 | 对接微信支付 |

---

## 五、静态资源（非 JSON API）

| 路径 | 用途 | Web | 小程序 |
|------|------|-----|--------|
| `/uploads/**` | 封面、原视频 | 相对路径 | **完整 HTTPS URL** |
| `/media/v/homePage/{name}` | 首页背景视频 | `protectVideoUrl` | 同上 |
| `/media/v/bookReview/{name}` | 解读视频 | play-auth 返回 | 同上 |
| `/placeholders/books/*.svg` | 封面占位 | `resolveMediaUrl` | 同上 |

**生产示例：**

```text
https://www.yuxiaotubook.com/uploads/covers/xxx.jpg
https://www.yuxiaotubook.com/media/v/bookReview/abc123
https://www.yuxiaotubook.com/placeholders/books/bei-tao-yan-de-yong-qi.svg
```

---

## 六、OpenAPI Tag 与 C 端端点对照表

| OpenAPI Tag | 路径 | 方法 | C端/Web | 小程序 |
|-------------|------|------|---------|--------|
| 站点 | `/site/config` | GET | ✅ | ✅ |
| 站点 | `/categories` | GET | ✅ | ✅ |
| 首页 | `/home/featured` | GET | ✅ | ✅ |
| 首页 | `/home/hot-books` | GET | ✅ | ✅ |
| 用户-认证 | `/auth/register` | POST | ✅ | ✅ |
| Admin-认证 | `/auth/login` | POST | ✅ | ✅ |
| Admin-认证 | `/auth/me` | GET | ✅ | ✅ |
| 书籍 | `/books` | GET | ✅ | ✅ |
| 书籍 | `/books/{book_id}` | GET | ✅ | ✅ |
| 书籍 | `/books/{book_id}/play-auth` | GET | ✅ | ✅ |
| 书籍 | `/books/{book_id}/similar` | GET | ✅ | ✅ |
| 书籍 | `/books/{book_id}/play-report` | POST | ❌ | Phase 2 |
| 每日读书 | `/daily/today` | GET | ✅ | ✅ |
| 每日读书 | `/daily/list` | GET | ✅ | ✅ |
| 每日读书 | `/daily/{daily_id}/like` | POST | ✅ | ✅ |
| 收藏 | `/favorites` | POST/GET | ✅ | ✅ |
| 收藏 | `/favorites/{book_id}` | DELETE | ❌ | Phase 2 |
| 收藏 | `/history` | GET | ✅ | ✅ |
| 用户-个人中心 | `/user/preferences` | GET/PUT | ✅ | ✅ |
| 用户-个人中心 | `/user/orders/shipping` | GET | ✅ | ✅ |
| *(Java)* | `/orders` | POST/GET | ✅ | ✅ |
| *(Java)* | `/orders/{id}/mock-pay` | POST | ✅ | ✅ |
| *(Java)* | `/member/packages` | GET | ✅ | ✅ |
| *(Java)* | `/member/status` | GET | ✅ | ✅ |
| *(Java)* | `/member/subscribe` | POST | ✅ | ✅ |
| *(Java)* | `/member/orders/{id}/mock-pay` | POST | ✅ | ✅ |

**图例：** ✅ 一期必须对齐 Web；❌ 后端有但 Web 未用。

---

## 七、小程序 `api/` 模块映射（建议）

与 Web 内联 `request()` 不同，小程序建议按模块拆分，**路径与 Web 完全一致**：

| 文件 | 导出函数 | 对应端点 |
|------|----------|----------|
| `api/client.ts` | `get/post/put/del` | 通用封装 |
| `api/auth.ts` | `login`, `register`, `fetchMe` | `/auth/*` |
| `api/site.ts` | `getSiteConfig`, `getCategories` | `/site/config`, `/categories` |
| `api/home.ts` | `getFeatured`, `getHotBooks` | `/home/*` |
| `api/books.ts` | `listBooks`, `getBook`, `getPlayAuth`, `getSimilar`, `reportPlay` | `/books/*` |
| `api/daily.ts` | `getToday`, `listDaily`, `likeDaily` | `/daily/*` |
| `api/favorites.ts` | `add`, `list`, `remove` | `/favorites`, `/history` |
| `api/user.ts` | `getPreferences`, `savePreferences`, `getShippingOrders` | `/user/*` |
| `api/trade.ts` | `createOrder`, `listOrders`, `mockPayOrder`, `getPackages`, `getMemberStatus`, `subscribe`, `mockPayMember` | `/orders`, `/member` |

---

## 八、数据联动验证清单

| # | Admin 操作 | 验证接口 | Web | 小程序 |
|---|------------|----------|-----|--------|
| 1 | 改首页宣传标题 | `GET /site/config` | ✅ | ✅ |
| 2 | 上传 homePage 视频 | `GET /site/config` → bg_videos | ✅ | ✅ |
| 3 | 改书籍价格/上下架 | `GET /books/{id}` | ✅ | ✅ |
| 4 | 发布每日读书 | `GET /daily/today` | ✅ | ✅ |
| 5 | 改会员套餐 | `GET /member/packages` | ✅ | ✅ |
| 6 | Web 注册 → 小程序登录 | `POST /auth/login` | — | 同一 users 表 |
| 7 | Web 收藏 → 小程序查看 | `GET /favorites` | ✅ | ✅ |

---

## 九、Apifox / Postman 导入步骤

1. 本地启动 Python API（`DEBUG=true`）
2. 访问 `http://127.0.0.1:8000/openapi.json` 导出
3. 导入 Apifox 集合，Base URL 设为 `{{host}}/api/v1`
4. **手动补充** §四 Java 7 个端点（OpenAPI 不包含）
5. 环境变量：
   - `host_dev` = `http://127.0.0.1:8000`
   - `host_prod` = `https://www.yuxiaotubook.com`
   - `token` = 登录后 `data.token`

---

## 十、相关文档

| 文档 | 路径 |
|------|------|
| 小程序开发需求 | `./开发需求文档.md` |
| 小程序技术选型 | `./技术选型文档.md` |
| 小程序脚手架 | `./脚手架代码文档.md` |
| Web 技术选型定版 | `../../开发文档/开发需求文档/技术选型定版.md` |
| Python OpenAPI 配置 | `../../YuXiaotuBook/backend/app/core/openapi.py` |

---

**维护规则：** 后端新增/变更 C 端接口时，同步更新本文档、Web 前端与小程序 `api/` 模块。
