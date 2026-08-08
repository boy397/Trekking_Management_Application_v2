<template>
  <div v-if="currentUser && currentUser.role === 'Admin'">
    <!-- ADMIN ACTION MENU TABS -->
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'dashboard'}" @click.prevent="currentTab = 'dashboard'; loadAdminDashboard()">Dashboard</a></li>
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'treks'}" @click.prevent="currentTab = 'treks'; loadAdminTreks()">Manage Treks</a></li>
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'users'}" @click.prevent="currentTab = 'users'; loadAdminUsers()">Manage Users & Staff</a></li>
      <li class="nav-item"><a class="nav-link" href="#" :class="{active: currentTab === 'reports'}" @click.prevent="currentTab = 'reports'; loadAdminReports()">Reports & Logs</a></li>
    </ul>

    <!-- TAB: ADMIN DASHBOARD STATS -->
    <div v-if="currentTab === 'dashboard'" class="row">
      <div class="col-md-3 mb-3"><div class="card p-3 shadow-sm border-0 bg-white"><h6>Total Treks</h6><h3>{{ adminStats.total_treks }}</h3></div></div>
      <div class="col-md-3 mb-3"><div class="card p-3 shadow-sm border-0 bg-white"><h6>Trekkers</h6><h3>{{ adminStats.total_users }}</h3></div></div>
      <div class="col-md-3 mb-3"><div class="card p-3 shadow-sm border-0 bg-white"><h6>Staff Members</h6><h3>{{ adminStats.total_staff }}</h3></div></div>
      <div class="col-md-3 mb-3"><div class="card p-3 shadow-sm border-0 bg-white"><h6>Bookings</h6><h3>{{ adminStats.total_bookings }}</h3></div></div>
    </div>

    <!-- TAB: ADMIN TREKS LIST & INLINE FORM -->
    <div v-else-if="currentTab === 'treks'">
      <div class="d-flex justify-content-between mb-3">
        <h5>Trek Routes</h5>
        <button class="btn btn-primary btn-sm" @click="showTrekForm = !showTrekForm; trekEditingId = null; resetTrekForm()">
          {{ showTrekForm ? 'Hide Form' : 'Create Trek' }}
        </button>
      </div>

      <!-- INLINE TREK FORM -->
      <div class="card p-3 mb-4 shadow-sm border-0" v-if="showTrekForm">
        <h6>{{ trekEditingId ? 'Edit Trek Route' : 'Create Trek Route' }}</h6>
        <form @submit.prevent="saveTrek" class="row g-2">
          <div class="col-md-4"><input type="text" class="form-control form-control-sm" placeholder="Trek Name" v-model="trekForm.trek_name" required></div>
          <div class="col-md-4"><input type="text" class="form-control form-control-sm" placeholder="Location" v-model="trekForm.location" required></div>
          <div class="col-md-4">
            <select class="form-select form-select-sm" v-model="trekForm.difficulty">
              <option value="Easy">Easy</option><option value="Moderate">Moderate</option><option value="Hard">Hard</option>
            </select>
          </div>
          <div class="col-md-3"><input type="number" class="form-control form-control-sm" placeholder="Slots" v-model="trekForm.slots" required></div>
          <div class="col-md-3"><input type="number" class="form-control form-control-sm" placeholder="Duration (Days)" v-model="trekForm.duration_days" required></div>
          <div class="col-md-3"><input type="date" class="form-control form-control-sm" v-model="trekForm.start_date"></div>
          <div class="col-md-3"><input type="date" class="form-control form-control-sm" v-model="trekForm.end_date"></div>
          <div class="col-md-6">
            <select class="form-select form-select-sm" v-model="trekForm.staff_id">
              <option :value="null">Unassigned Staff</option>
              <option v-for="staff in staffOptions" :key="staff.id" :value="staff.id">{{ staff.name }}</option>
            </select>
          </div>
          <div class="col-md-6"><input type="text" class="form-control form-control-sm" placeholder="Description" v-model="trekForm.description"></div>
          <div class="col-12"><button type="submit" class="btn btn-success btn-sm">Save Trek Route</button></div>
        </form>
      </div>

      <table class="table bg-white rounded shadow-sm table-striped small">
        <thead><tr><th>Name</th><th>Location</th><th>Difficulty</th><th>Slots</th><th>Status</th><th>Staff Assigned</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="t in treks" :key="t.id">
            <td>{{ t.trek_name }}</td><td>{{ t.location }}</td><td>{{ t.difficulty }}</td><td>{{ t.slots }}</td><td>{{ t.status }}</td><td>{{ t.staff_name }}</td>
            <td>
              <button class="btn btn-sm btn-link p-0 me-2" @click="editTrekInline(t)">Edit</button>
              <button class="btn btn-sm btn-link text-danger p-0" @click="deleteTrek(t.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB: ADMIN USERS & INLINE STAFF REGISTRATION -->
    <div v-else-if="currentTab === 'users'">
      <div class="d-flex justify-content-between mb-3">
        <h5>Manage Profiles</h5>
        <button class="btn btn-success btn-sm" @click="showStaffForm = !showStaffForm">
          {{ showStaffForm ? 'Hide Form' : 'Register Trek Staff' }}
        </button>
      </div>

      <!-- INLINE STAFF FORM -->
      <div class="card p-3 mb-4 shadow-sm border-0" v-if="showStaffForm">
        <h6>Register New Trek Staff</h6>
        <form @submit.prevent="createStaff" class="row g-2">
          <div class="col-md-3"><input type="text" class="form-control form-control-sm" placeholder="Staff Name" v-model="staffForm.name" required></div>
          <div class="col-md-3"><input type="email" class="form-control form-control-sm" placeholder="Email" v-model="staffForm.email" required></div>
          <div class="col-md-3"><input type="text" class="form-control form-control-sm" placeholder="Phone" v-model="staffForm.phone" required></div>
          <div class="col-md-3"><input type="password" class="form-control form-control-sm" placeholder="Password" v-model="staffForm.password" required></div>
          <div class="col-12"><button type="submit" class="btn btn-success btn-sm">Create Staff</button></div>
        </form>
      </div>

      <table class="table bg-white rounded shadow-sm table-striped small">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.name }}</td><td>{{ u.email }}</td><td>{{ u.phone }}</td><td>{{ u.role }}</td><td>{{ u.status }}</td>
            <td>
              <template v-if="u.role !== 'Admin'">
                <button class="btn btn-sm btn-link p-0 me-2 text-success" @click="updateUserStatus(u.id, 'Approved')">Approve</button>
                <button class="btn btn-sm btn-link p-0 me-2 text-warning" @click="updateUserStatus(u.id, 'Deactivated')">Block</button>
                <button class="btn btn-sm btn-link p-0 text-danger" @click="updateUserStatus(u.id, 'Blacklisted')">Blacklist</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB: ADMIN REPORTS AND MANUAL BACKGROUND LOGS -->
    <div v-else-if="currentTab === 'reports'">
      <div class="row">
        <div class="col-md-6 mb-4">
          <div class="card p-3 shadow-sm border-0">
            <h5>Statistical Breakdown</h5>
            <ul>
              <li>Total configured routes: {{ reportData.total_treks }}</li>
              <li>Completed routes: {{ reportData.completed_treks }}</li>
              <li>Booked Slots: {{ reportData.booked_bookings }}</li>
              <li>Cancelled bookings: {{ reportData.cancelled_bookings }}</li>
            </ul>
            <div class="btn-group mt-3">
              <button class="btn btn-outline-primary btn-sm" @click="triggerManualJob('reminders')">Run Daily Reminders</button>
              <button class="btn btn-outline-success btn-sm" @click="triggerManualJob('report')">Run Monthly Report</button>
            </div>
          </div>
        </div>
        <div class="col-md-6 mb-4">
          <div class="card p-3 shadow-sm border-0" style="max-height: 300px; overflow-y: auto;">
            <h5>Scheduler Background Logs</h5>
            <div v-for="l in logs" :key="l.id" class="border-bottom py-1 small">
              <span class="text-muted">[{{ l.timestamp }}]</span> <strong class="text-primary">{{ l.job }}</strong>: {{ l.message }}
            </div>
            <div v-if="logs.length === 0" class="text-muted text-center pt-5">No logs recorded.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import axios from 'axios'

const currentUser = inject('currentUser')
const showAlert = inject('showAlert')

const currentTab = ref('dashboard')
const adminStats = ref({ total_treks: 0, total_users: 0, total_staff: 0, total_bookings: 0 })
const treks = ref([])
const users = ref([])
const staffOptions = ref([])
const reportData = ref({ total_treks: 0, completed_treks: 0, open_treks: 0, total_bookings: 0, booked_bookings: 0, cancelled_bookings: 0, popular_treks: [] })
const logs = ref([])
const userSearchQuery = ref('')

const showTrekForm = ref(false)
const trekEditingId = ref(null)
const trekForm = ref({ trek_name: '', location: '', difficulty: 'Moderate', slots: 10, status: 'Open', duration_days: 1, staff_id: null, description: '', start_date: '', end_date: '' })

const showStaffForm = ref(false)
const staffForm = ref({ name: '', email: '', password: '', phone: '' })

onMounted(() => {
  if (currentUser.value?.role === 'Admin') {
    loadAdminDashboard()
  }
})

async function loadAdminDashboard() {
  try {
    const res = await axios.get('/api/admin/dashboard')
    adminStats.value = res.data
  } catch (e) { console.error(e) }
}

async function loadAdminTreks() {
  showTrekForm.value = false
  try {
    const res = await axios.get('/api/admin/treks')
    treks.value = res.data
    const usersRes = await axios.get('/api/admin/users-staff')
    staffOptions.value = usersRes.data.filter(u => u.role === 'Staff')
  } catch (e) { showAlert('Error fetching treks.', 'danger') }
}

async function loadAdminUsers() {
  showStaffForm.value = false
  try {
    const res = await axios.get('/api/admin/users-staff', { params: { search: userSearchQuery.value } })
    users.value = res.data
  } catch (e) { showAlert('Error fetching directory.', 'danger') }
}

async function updateUserStatus(userId, action) {
  try {
    const res = await axios.post('/api/admin/deactivate-blacklist', { user_id: userId, action: action })
    showAlert(res.data.message)
    loadAdminUsers()
  } catch (e) { showAlert(e.response?.data?.error || 'Action failed.', 'danger') }
}

async function createStaff() {
  try {
    const res = await axios.post('/api/admin/staff', staffForm.value)
    showAlert(res.data.message)
    showStaffForm.value = false
    loadAdminUsers()
    staffForm.value = { name: '', email: '', password: '', phone: '' }
  } catch (e) { showAlert(e.response?.data?.error || 'Failed to create guide.', 'danger') }
}

function resetTrekForm() {
  trekForm.value = { trek_name: '', location: '', difficulty: 'Moderate', slots: 10, status: 'Open', duration_days: 1, staff_id: null, description: '', start_date: '', end_date: '' }
}

function editTrekInline(t) {
  trekEditingId.value = t.id
  trekForm.value = { ...t }
  showTrekForm.value = true
}

async function saveTrek() {
  try {
    if (trekEditingId.value) {
      await axios.put(`/api/admin/treks/${trekEditingId.value}`, trekForm.value)
      showAlert('Trek successfully updated.')
    } else {
      await axios.post('/api/admin/treks', trekForm.value)
      showAlert('Trek successfully created.')
    }
    showTrekForm.value = false
    loadAdminTreks()
  } catch (e) { showAlert(e.response?.data?.error || 'Save failed.', 'danger') }
}

async function deleteTrek(trekId) {
  if (confirm('Delete this trek?')) {
    try {
      const res = await axios.delete(`/api/admin/treks/${trekId}`)
      showAlert(res.data.message)
      loadAdminTreks()
    } catch (e) { showAlert('Deletion failed.', 'danger') }
  }
}

async function loadAdminReports() {
  try {
    const res = await axios.get('/api/admin/reports')
    reportData.value = res.data
    const logsRes = await axios.get('/api/logs')
    logs.value = logsRes.data
  } catch (e) { showAlert('Error loading reports.', 'danger') }
}

async function triggerManualJob(jobType) {
  try {
    const res = await axios.post('/api/admin/trigger-job', { job_type: jobType })
    showAlert(res.data.message)
    loadAdminReports()
  } catch (e) { showAlert('Job execution failed.', 'danger') }
}
</script>
