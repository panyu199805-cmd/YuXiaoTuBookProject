# 宇小兔读书 · 微信小程序

与 [宇小兔读书 Web 用户端](../YuXiaotuBook/frontend) 共用 API 与 Admin 后台。

## 文档

- [开发需求文档](./开发文档/开发需求文档.md)
- [技术选型文档](./开发文档/技术选型文档.md)
- [脚手架代码文档](./开发文档/脚手架代码文档.md)
- [C 端 API 端点清单](./开发文档/C端API端点清单与OpenAPI对照表.md)

## 微信开发者工具导入（二选一）

**方式 A（推荐）：** 直接导入编译产物目录

```text
E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\yuxiaotubookWeixinTool\dist\dev\mp-weixin
```

**方式 B：** 导入项目根目录 `yuxiaotubookWeixinTool`（需先有 `dist/dev/mp-weixin/app.json`，由 `project.config.json` 的 `miniprogramRoot` 指向）

若报错 **「未找到 app.json」**：说明还没编译，先执行下面命令生成 `dist/dev/mp-weixin`。

## 开发

```powershell
cd "E:\AI项目\YuXiaoTuAIGC\YuXiaoTuBook\yuxiaotubookWeixinTool"
# PowerShell:
.\scripts\dev-mp-weixin.ps1
# 或 CMD（避免中文编码问题）:
scripts\dev-mp-weixin.bat
# 或手动:
npx uni -p mp-weixin
```

编译完成后，微信工具导入 **`dist/dev/mp-weixin`**（开发 watch）或 **`dist/build/mp-weixin`**（仅 build 一次时）。

### 本地联调必读

1. 先启动本地后端：`开发文档/本地运行.ps1`
2. 小程序模拟器 **不能访问 `127.0.0.1`**，`.env.development` 已配置为本机局域网 IP（`192.168.3.14`）
3. 若 IP 变了：复制 `.env.development.local.example` 为 `.env.development.local` 并修改 IP
4. 微信开发者工具 → 详情 → 本地设置 → **勾选「不校验合法域名」**
5. 修改 env 后需 **重新运行** `npx uni -p mp-weixin`，再在开发者工具里 **重新编译**

### 页面未注册 / ERR_CACHE_MISS

| 现象 | 处理 |
|------|------|
| `Page "pages/xxx" has not been registered yet` | 完全关闭微信开发者工具 → 运行 `.\scripts\dev-mp-weixin.ps1` → 重新导入 `dist/dev/mp-weixin` |
| 编译时文件被占用 | 先关微信工具，再编译 |
| Tab 切换报错 | 微信工具 → **清除缓存（全部）** → 重新编译 |

### 图片不显示 / 「不再支持 HTTP 协议」

微信基础库 3.15+ 禁止 `<image>` 直接使用 `http://` 链接。

**已自动处理：** 书籍封面等图片通过 `SecureImage` 组件下载后展示。

**若需首页背景视频：**

1. 运行 `scripts/dev-https-proxy.ps1`（8443→8000，8444→8081）
2. 在 `.env.development` 切换到方案 B（HTTPS 8443）
3. 重新 `npx uni -p mp-weixin`，开发者工具勾选 **不校验 TLS 证书**

## 生产 API

`https://www.yuxiaotubook.com/api/v1`
