import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminView from '../views/AdminView.vue'
import StaffView from '../views/StaffView.vue'
import UserView from '../views/UserView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/admin', name: 'admin', component: AdminView },
  { path: '/staff', name: 'staff', component: StaffView },
  { path: '/user', name: 'user', component: UserView }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
