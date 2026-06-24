import { createRouter, createWebHistory } from 'vue-router'
import PublicLayout from './views/PublicLayout.vue'
import Home from './views/Home.vue'

const routes = [
  {
    path: '/',
    component: PublicLayout,
    children: [
      { path: '', component: Home, name: 'home' },
      {
        path: 'score-rank',
        component: () => import('./views/ScoreRank.vue'),
        name: 'score-rank',
      },
    ],
  },
  {
    path: '/admin/login',
    component: () => import('./views/admin/Login.vue'),
    name: 'admin-login',
  },
  {
    path: '/admin',
    component: () => import('./views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/admin/import' },
      { path: 'import', component: () => import('./views/admin/Import.vue'), name: 'admin-import' },
      { path: 'schools', component: () => import('./views/admin/Schools.vue'), name: 'admin-schools' },
      { path: 'config', component: () => import('./views/admin/Config.vue'), name: 'admin-config' },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Guard admin routes: require a token.
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('admin_token')) {
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
})

export default router
