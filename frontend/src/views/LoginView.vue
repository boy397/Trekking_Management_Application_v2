<template>
  <div class="row justify-content-center">
    <div class="col-md-5">
      <div class="card shadow-sm border-0 mt-5">
        <div class="card-body p-4">
          <h4 class="text-center mb-4">Login to TrekSync</h4>
          <form @submit.prevent="handleLogin">
            <div class="mb-3">
              <label class="form-label text-muted small">Email Address</label>
              <input type="email" class="form-control" v-model="email" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small">Password</label>
              <input type="password" class="form-control" v-model="password" required>
            </div>
            <button type="submit" class="btn btn-primary w-100 mb-3">Sign In</button>
            <div class="text-center small">
              Don't have an account? <router-link to="/register">Register here</router-link>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const email = ref('')
const password = ref('')
const router = useRouter()
const currentUser = inject('currentUser')
const showAlert = inject('showAlert')

async function handleLogin() {
  try {
    const res = await axios.post('/api/auth/login', { email: email.value, password: password.value })
    currentUser.value = res.data.user
    showAlert('Login successful!')
    
    if (currentUser.value.role === 'Admin') router.push('/admin')
    else if (currentUser.value.role === 'Staff') router.push('/staff')
    else router.push('/user')
  } catch (e) {
    showAlert(e.response?.data?.error || 'Login failed.', 'danger')
  }
}
</script>
