const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('pages/Index.vue')
      },
      {
        path: 'bank',
        component: () => import('pages/Bank.vue')
      },
      {
        path: 'teams',
        component: () => import('pages/Teams.vue')
      },
      {
        path: 'players',
        component: () => import('pages/Players.vue')
      },
    ]
  },



  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/Error404.vue')
  }
]

export default routes
