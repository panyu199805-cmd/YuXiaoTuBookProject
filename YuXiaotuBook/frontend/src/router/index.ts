import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const placeholder = () => import('@/views/admin/AdminPlaceholder.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/UserLayout.vue'),
      children: [
        { path: '', name: 'Home', component: () => import('@/views/Home.vue') },
        { path: 'books', name: 'Books', component: () => import('@/views/Books.vue') },
        { path: 'books/:id', name: 'BookDetail', component: () => import('@/views/BookDetail.vue') },
        { path: 'daily', name: 'Daily', component: () => import('@/views/Daily.vue') },
        { path: 'member', name: 'Member', component: () => import('@/views/member/MemberCenter.vue') },
        { path: 'login', name: 'Login', component: () => import('@/views/Login.vue') },
        { path: 'register', name: 'Register', component: () => import('@/views/Register.vue') },
        {
          path: 'user/orders',
          name: 'UserOrders',
          meta: { login: true },
          component: () => import('@/views/user/Orders.vue'),
        },
        {
          path: 'user/favorites',
          name: 'UserFavorites',
          meta: { login: true },
          component: () => import('@/views/user/Favorites.vue'),
        },
        {
          path: 'user/history',
          name: 'UserHistory',
          meta: { login: true },
          component: () => import('@/views/user/History.vue'),
        },
        {
          path: 'user/center',
          name: 'UserCenter',
          meta: { login: true },
          component: () => import('@/views/user/UserCenter.vue'),
        },
      ],
    },
    {
      path: '/admin/login',
      name: 'AdminLogin',
      component: () => import('@/views/admin/Login.vue'),
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { admin: true },
      children: [
        { path: '', redirect: '/admin/analytics/overview' },

        // 数据分析
        {
          path: 'analytics/overview',
          meta: {
            title: '全站总览仪表盘',
            parentTitle: '数据分析',
            group: 'analytics',
          },
          component: () => import('@/views/admin/AnalyticsOverview.vue'),
        },
        {
          path: 'analytics/reading',
          meta: {
            title: '用户阅读行为分析',
            parentTitle: '数据分析',
            group: 'analytics',
          },
          component: () => import('@/views/admin/AnalyticsReading.vue'),
        },
        {
          path: 'analytics/orders',
          meta: {
            title: '交易订单数据统计',
            parentTitle: '数据分析',
            group: 'analytics',
          },
          component: () => import('@/views/admin/AnalyticsOrders.vue'),
        },
        {
          path: 'analytics/region',
          meta: {
            title: '用户地域分布分析',
            parentTitle: '数据分析',
            group: 'analytics',
          },
          component: () => import('@/views/admin/AnalyticsRegion.vue'),
        },
        {
          path: 'analytics/system',
          meta: {
            title: '系统性能监控面板',
            parentTitle: '数据分析',
            group: 'analytics',
          },
          component: () => import('@/views/admin/AnalyticsSystem.vue'),
        },

        // 书籍管理
        {
          path: 'book/list',
          meta: { title: '书籍列表', parentTitle: '书籍管理', group: 'book' },
          component: () => import('@/views/admin/Books.vue'),
        },
        {
          path: 'book/category',
          meta: { title: '书籍分类', parentTitle: '书籍管理', group: 'book' },
          component: () => import('@/views/admin/Categories.vue'),
        },
        {
          path: 'book/assets',
          meta: {
            title: '图书素材库',
            parentTitle: '书籍管理',
            group: 'book',
            placeholderDesc: '统一管理图书高清封面、内页插图等素材，支持复用与批量上传。',
          },
          component: placeholder,
        },
        {
          path: 'book/collections',
          meta: {
            title: '书单管理',
            parentTitle: '书籍管理',
            group: 'book',
            placeholderDesc: '创建推荐书单、绑定多本图书，并配置首页热门推荐展示。',
          },
          component: placeholder,
        },

        // 内容管理
        {
          path: 'content/video',
          meta: { title: '解读视频管理', parentTitle: '内容管理', group: 'content' },
          component: () => import('@/views/admin/Videos.vue'),
        },
        {
          path: 'content/daily',
          meta: { title: '每日读书专栏', parentTitle: '内容管理', group: 'content' },
          component: () => import('@/views/admin/Daily.vue'),
        },
        {
          path: 'content/ai',
          meta: { title: 'AI 内容生成', parentTitle: '内容管理', group: 'content' },
          component: () => import('@/views/admin/AiContent.vue'),
        },
        {
          path: 'content/review',
          meta: {
            title: '内容审核',
            parentTitle: '内容管理',
            group: 'content',
            placeholderDesc: '视频与文字内容敏感词预审、违规拦截与审核日志查询。',
          },
          component: placeholder,
        },

        // 氛围配置
        {
          path: 'atmosphere/home',
          meta: { title: '首页氛围配置', parentTitle: '氛围配置', group: 'atmosphere' },
          component: () => import('@/views/admin/SiteConfig.vue'),
        },
        {
          path: 'atmosphere/audio',
          meta: {
            title: '音噪素材管理',
            parentTitle: '氛围配置',
            group: 'atmosphere',
            placeholderDesc: '背景音乐、白噪音素材上传，音量默认值与上下架管理。',
          },
          component: placeholder,
        },
        {
          path: 'atmosphere/global',
          meta: {
            title: '页面全局设置',
            parentTitle: '氛围配置',
            group: 'atmosphere',
            placeholderDesc: '网站基础文案、页脚导航、SEO 关键词等全局配置。',
          },
          component: placeholder,
        },

        // 会员管理
        {
          path: 'member/package',
          meta: { title: '会员套餐配置', parentTitle: '会员管理', group: 'member' },
          component: () => import('@/views/admin/MemberPackages.vue'),
        },
        {
          path: 'member/users',
          meta: {
            title: '用户会员列表',
            parentTitle: '会员管理',
            group: 'member',
            placeholderDesc: '查询开通会员用户、查看有效期，支持手动续费与停用操作。',
          },
          component: placeholder,
        },
        {
          path: 'member/stats',
          meta: {
            title: '会员权益统计',
            parentTitle: '会员管理',
            group: 'member',
            placeholderDesc: '会员视频观看、笔记下载、购书折扣使用数据看板。',
          },
          component: placeholder,
        },
        {
          path: 'member/orders',
          meta: {
            title: '会员订单流水',
            parentTitle: '会员管理',
            group: 'member',
            placeholderDesc: '会员充值与续费订单查询、退款处理与财务对账。',
          },
          component: placeholder,
        },

        // 订单管理
        {
          path: 'order/all',
          meta: { title: '全部订单列表', parentTitle: '订单管理', group: 'order' },
          component: () => import('@/views/admin/Orders.vue'),
        },
        {
          path: 'order/aftersale',
          meta: {
            title: '售后订单管理',
            parentTitle: '订单管理',
            group: 'order',
            placeholderDesc: '图书退货换货申请处理、退款审核与售后原因记录。',
          },
          component: placeholder,
        },
        {
          path: 'order/stats',
          meta: {
            title: '销量数据统计',
            parentTitle: '订单管理',
            group: 'order',
            placeholderDesc: '图书销量排行、日月销售额图表与销售报表导出。',
          },
          component: placeholder,
        },
        {
          path: 'order/logistics',
          meta: {
            title: '物流配置',
            parentTitle: '订单管理',
            group: 'order',
            placeholderDesc: '快递公司模板、运费规则与发货地址配置。',
          },
          component: placeholder,
        },

        // 权限管理
        {
          path: 'permission/user',
          meta: { title: '用户管理', parentTitle: '权限管理', group: 'permission' },
          component: () => import('@/views/admin/Users.vue'),
        },
        {
          path: 'permission/role',
          meta: {
            title: '角色权限配置',
            parentTitle: '权限管理',
            group: 'permission',
            placeholderDesc: '新建角色并勾选二级菜单访问权限，区分编辑、财务与超级管理员。',
          },
          component: placeholder,
        },
        {
          path: 'permission/audit',
          meta: {
            title: '操作审计日志',
            parentTitle: '权限管理',
            group: 'permission',
            placeholderDesc: '后台账号操作记录查询，书籍、订单与配置变更溯源。',
          },
          component: placeholder,
        },
        {
          path: 'permission/security',
          meta: {
            title: '系统安全配置',
            parentTitle: '权限管理',
            group: 'permission',
            placeholderDesc: 'API 密钥、AI 渠道密钥、登录验证码与超时策略配置。',
          },
          component: placeholder,
        },

        // 旧路由兼容重定向
        { path: 'books', redirect: '/admin/book/list' },
        { path: 'categories', redirect: '/admin/book/category' },
        { path: 'videos', redirect: '/admin/content/video' },
        { path: 'daily', redirect: '/admin/content/daily' },
        { path: 'site-config', redirect: '/admin/atmosphere/home' },
        { path: 'member', redirect: '/admin/member/package' },
        { path: 'orders', redirect: '/admin/order/all' },
        { path: 'users', redirect: '/admin/permission/user' },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const store = useUserStore()
  if (to.meta.login && !store.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  if (to.meta.admin || to.path.startsWith('/admin')) {
    if (to.name === 'AdminLogin') {
      next()
      return
    }
    if (!store.isLoggedIn || !store.isAdmin) {
      next({ name: 'AdminLogin' })
      return
    }
  }
  next()
})

export default router
