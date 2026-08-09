<template>
  <div id="app" class="container-fluid p-0">
    <!-- NAVIGATION NAVBAR -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3 shadow-sm">
      <a class="navbar-brand fw-bold" href="#" @click.prevent="goHome">
        TrekSync
      </a>
      <div class="collapse navbar-collapse justify-content-end">
        <ul class="navbar-nav align-items-center" v-if="currentUser">
          <li class="nav-item me-3">
            <span class="navbar-text text-light">Welcome, <strong>{{ currentUser.name }}</strong> ({{ currentUser.role }})</span>
          </li>
          <li class="nav-item">
            <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Logout</button>
          </li>
        </ul>
        <ul class="navbar-nav" v-else>
          <li class="nav-item"><router-link class="nav-link" to="/login">Login</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/register">Register</router-link></li>
        </ul>
      </div>
    </nav>

    <!-- ALERTS AND NOTIFICATIONS -->
    <div class="container mt-3" v-if="alertMsg">
      <div class="alert alert-dismissible fade show" :class="'alert-' + alertType" role="alert">
        {{ alertMsg }}
        <button type="button" class="btn-close" @click="alertMsg = ''"></button>
      </div>
    </div>

    <!-- MAIN LAYOUT -->
    <div class="container py-4">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

axios.defaults.baseURL = 'http://localhost:8085'
axios.defaults.withCredentials = true

axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

const router = useRouter()
const currentUser = ref(null)
const alertMsg = ref('')
const alertType = ref('success')

// Provide globally so child views can show alerts
provide('currentUser', currentUser)
provide('showAlert', showAlert)

function showAlert(msg, type = 'success') {
  alertMsg.value = msg
  alertType.value = type
  setTimeout(() => { alertMsg.value = '' }, 5000)
}

onMounted(() => {
  checkSession()
})

async function checkSession() {
  try {
    const res = await axios.get('/api/auth/me')
    currentUser.value = res.data.user
    redirectUser()
  } catch (e) {
    currentUser.value = null
    if (router.currentRoute.value.path !== '/login' && router.currentRoute.value.path !== '/register') {
      router.push('/login')
    }
  }
}

async function handleLogout() {
  try {
    await axios.post('/api/auth/logout')
    currentUser.value = null
    localStorage.removeItem('token')
    showAlert('Logged out successfully.')
    router.push('/login')
  } catch (e) {
    showAlert('Logout failed.', 'danger')
  }
}

function goHome() {
  redirectUser()
}

function redirectUser() {
  if (!currentUser.value) return router.push('/login')
  if (currentUser.value.role === 'Admin') router.push('/admin')
  else if (currentUser.value.role === 'Staff') router.push('/staff')
  else router.push('/user')
}
</script>
