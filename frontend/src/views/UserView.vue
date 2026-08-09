<template>
  <div v-if="currentUser && currentUser.role === 'User'">
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'dashboard'}" @click.prevent="currentTab = 'dashboard'; loadUserTreks()">Find Treks</a></li>
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'history'}" @click.prevent="currentTab = 'history'; loadUserBookings()">My Bookings & Export</a></li>
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'profile'}" @click.prevent="currentTab = 'profile'; loadUserProfile()">Profile Settings</a></li>
    </ul>

    <!-- TAB: USER DISCOVERY -->
    <div v-if="currentTab === 'dashboard'">
      <div class="row g-2 mb-4">
        <div class="col-md-3"><input type="text" class="form-control form-control-sm" placeholder="Search route..." v-model="filterSearch" @input="loadUserTreks"></div>
        <div class="col-md-3">
          <select class="form-select form-select-sm" v-model="filterDifficulty" @change="loadUserTreks">
            <option value="">All Difficulties</option><option value="Easy">Easy</option><option value="Moderate">Moderate</option><option value="Hard">Hard</option>
          </select>
        </div>
        <div class="col-md-3"><input type="text" class="form-control form-control-sm" placeholder="Filter Location..." v-model="filterLocation" @input="loadUserTreks"></div>
        <div class="col-md-3"><input type="number" class="form-control form-control-sm" placeholder="Max Days..." v-model="filterDuration" @input="loadUserTreks"></div>
      </div>

      <div class="row">
        <div class="col-md-4 mb-3" v-for="t in userTreks" :key="t.id">
          <div class="card p-3 border-0 shadow-sm h-100">
            <h5>{{ t.trek_name }} <span class="badge bg-info text-dark float-end small">{{ t.difficulty }}</span></h5>
            <p class="text-muted small">📍 {{ t.location }}</p>
            <p class="small mb-1">{{ t.description }}</p>
            <p class="small mb-3 text-muted">Guide: {{ t.staff_name }} | Days: {{ t.duration_days }} | Slots left: {{ t.slots }}</p>
            <button class="btn btn-primary btn-sm w-100" @click="bookTrek(t.id)" :disabled="t.slots <= 0">Book Now</button>
          </div>
        </div>
        <div v-if="userTreks.length === 0" class="col-12 text-center text-muted">No open treks match.</div>
      </div>
    </div>

    <!-- TAB: USER BOOKING HISTORY & CSV EXPORTS -->
    <div v-else-if="currentTab === 'history'">
      <div class="d-flex justify-content-between mb-3 align-items-center">
        <h5>Booking History</h5>
        <button class="btn btn-secondary btn-sm" @click="exportHistory" :disabled="exportInfo.status === 'Pending'">
          {{ exportInfo.status === 'Pending' ? 'Processing CSV...' : 'Export History (CSV)' }}
        </button>
      </div>

      <div v-if="exportInfo.status === 'Ready'" class="alert alert-success d-flex justify-content-between align-items-center border-0 p-2 shadow-sm mb-3 small">
        <span>CSV Export finished!</span>
        <a :href="'http://localhost:8085/api/users/download-export/' + exportInfo.filename + '?token=' + getToken()" class="btn btn-success btn-sm py-0">Download CSV</a>
      </div>

      <table class="table bg-white rounded shadow-sm table-striped small">
        <thead><tr><th>Booking #</th><th>Trek Name</th><th>Location</th><th>Start Date</th><th>Date Reserved</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="b in userBookings" :key="b.booking_id">
            <td>#{{ b.booking_id }}</td><td>{{ b.trek_name }}</td><td>{{ b.location }}</td><td>{{ b.start_date }}</td><td>{{ b.booking_date }}</td><td>{{ b.status }}</td>
            <td>
              <button class="btn btn-sm btn-link text-danger p-0" v-if="b.status === 'Booked'" @click="cancelBooking(b.booking_id)">Cancel</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB: USER PROFILE EDIT -->
    <div v-else-if="currentTab === 'profile'">
      <div class="card p-4 border-0 shadow-sm col-md-6">
        <h5>Modify Profile Settings</h5>
        <form @submit.prevent="updateUserProfile">
          <div class="mb-3"><label class="form-label small text-muted">Full Name</label><input type="text" class="form-control" v-model="profileName" required></div>
          <div class="mb-3"><label class="form-label small text-muted">Phone Number</label><input type="text" class="form-control" v-model="profilePhone" required></div>
          <button type="submit" class="btn btn-primary btn-sm">Save Profile Details</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

const currentUser = inject('currentUser')
const showAlert = inject('showAlert')

const currentTab = ref('dashboard')
const userTreks = ref([])
const userBookings = ref([])

const filterSearch = ref('')
const filterDifficulty = ref('')
const filterLocation = ref('')
const filterDuration = ref('')

const profileName = ref('')
const profilePhone = ref('')

const exportInfo = ref({ status: 'None', filename: '' })
let pollInterval = null

const getToken = () => localStorage.getItem('token')

onMounted(() => {
  if (currentUser.value?.role === 'User') {
    loadUserTreks()
  }
})

onBeforeUnmount(() => {
  if (pollInterval) clearInterval(pollInterval)
})

async function loadUserTreks() {
  try {
    const res = await axios.get('/api/users/treks', {
      params: { search: filterSearch.value, difficulty: filterDifficulty.value, location: filterLocation.value, duration: filterDuration.value }
    })
    userTreks.value = res.data
  } catch (e) { showAlert('Error loading treks.', 'danger') }
}

async function bookTrek(trekId) {
  try {
    const res = await axios.post('/api/users/bookings', { trek_id: trekId })
    showAlert(res.data.message)
    loadUserTreks()
  } catch (e) { showAlert(e.response?.data?.error || 'Failed to book slot.', 'danger') }
}

async function loadUserBookings() {
  try {
    const res = await axios.get('/api/users/bookings')
    userBookings.value = res.data
    checkExportStatus()
  } catch (e) { showAlert('Error loading booking list.', 'danger') }
}

async function cancelBooking(bookingId) {
  if (confirm('Cancel reservation?')) {
    try {
      const res = await axios.post(`/api/users/bookings/${bookingId}/cancel`)
      showAlert(res.data.message)
      loadUserBookings()
    } catch (e) { showAlert('Cancellation failed.', 'danger') }
  }
}

function loadUserProfile() {
  profileName.value = currentUser.value.name
  profilePhone.value = currentUser.value.phone
}

async function updateUserProfile() {
  try {
    const res = await axios.put('/api/users/profile', { name: profileName.value, phone: profilePhone.value })
    currentUser.value = res.data.user
    showAlert('Profile settings saved.')
  } catch (e) { showAlert('Update failed.', 'danger') }
}

async function exportHistory() {
  try {
    const res = await axios.post('/api/users/export-history')
    showAlert(res.data.message, 'info')
    exportInfo.value.status = 'Pending'
    pollInterval = setInterval(checkExportStatus, 1000)
  } catch (e) { showAlert('Export failed.', 'danger') }
}

async function checkExportStatus() {
  try {
    const res = await axios.get('/api/users/export-status')
    exportInfo.value = res.data
    if (exportInfo.value.status === 'Ready') {
      clearInterval(pollInterval)
    }
  } catch (e) { clearInterval(pollInterval) }
}
</script>
