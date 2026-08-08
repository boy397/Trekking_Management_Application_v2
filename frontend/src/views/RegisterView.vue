<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <div class="card shadow-sm border-0 mt-5">
        <div class="card-body p-4">
          <h4 class="text-center mb-4">Create an Account</h4>
          <form @submit.prevent="handleRegister">
            <div class="mb-3">
              <label class="form-label text-muted small">Full Name</label>
              <input type="text" class="form-control" v-model="name" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small">Email Address</label>
              <input type="email" class="form-control" v-model="email" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small">Phone Number</label>
              <input type="text" class="form-control" v-model="phone" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small">Password</label>
              <input type="password" class="form-control" v-model="password" required>
            </div>
            <button type="submit" class="btn btn-success w-100 mb-3">Register Now</button>
            <div class="text-center small">
              Already have an account? <router-link to="/login">Login here</router-link>
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

const name = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const router = useRouter()
const showAlert = inject('showAlert')

async function handleRegister() {
  try {
    await axios.post('/api/auth/register', {
      name: name.value, email: email.value, phone: phone.value, password: password.value
    })
    showAlert('Registration successful! Please log in.')
    router.push('/login')
  } catch (e) {
    showAlert(e.response?.data?.error || 'Registration failed.', 'danger')
  }
}
</script>
