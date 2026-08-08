<template>
  <div v-if="currentUser && currentUser.role === 'Staff'">
    <div class="d-flex justify-content-between mb-4">
      <h3>Guide Dashboard - Assigned Treks</h3>
      <button class="btn btn-outline-secondary btn-sm" v-if="currentView === 'participants'" @click="currentView = 'dashboard'">Back to Treks</button>
    </div>

    <!-- SUB-VIEW: PARTICIPANTS LIST -->
    <div v-if="currentView === 'participants'" class="card p-3 border-0 shadow-sm">
      <h5>Registered Trekkers</h5>
      <table class="table table-sm table-striped small">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="p in participantList" :key="p.id">
            <td>{{ p.name }}</td><td>{{ p.email }}</td><td>{{ p.phone }}</td><td>{{ p.booking_status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- SUB-VIEW: TREKS LIST -->
    <div v-else class="row">
      <div class="col-md-6 mb-3" v-for="t in staffTreks" :key="t.id">
        <div class="card p-3 border-0 shadow-sm">
          <h5>{{ t.trek_name }} <span class="badge bg-secondary float-end">{{ t.difficulty }}</span></h5>
          <p class="text-muted small mb-2"><i class="fa-solid fa-location-dot"></i> {{ t.location }}</p>
          <p class="small mb-1">Status: <strong>{{ t.status }}</strong> | Slots left: <strong>{{ t.slots }}</strong></p>
          <p class="small mb-2">Registered Attendees: <strong>{{ t.registered_users_count }}</strong></p>
          
          <!-- INLINE UPDATE CONTROLS -->
          <div class="d-flex gap-2 mb-2">
            <input type="number" class="form-control form-control-sm w-50" placeholder="Slots count" v-model="t.slots">
            <select class="form-select form-select-sm w-50" v-model="t.status">
              <option value="Open">Open</option><option value="Closed">Closed</option><option value="Completed">Completed</option>
            </select>
          </div>
          
          <div class="d-flex justify-content-between mt-2">
            <button class="btn btn-primary btn-sm" @click="saveStaffTrekUpdates(t)">Save Updates</button>
            <button class="btn btn-outline-dark btn-sm" @click="loadTrekParticipants(t.id)">Attendee List</button>
          </div>
        </div>
      </div>
      <div v-if="staffTreks.length === 0" class="col-12 text-center text-muted py-5">You are not assigned to any treks.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import axios from 'axios'

const currentUser = inject('currentUser')
const showAlert = inject('showAlert')

const currentView = ref('dashboard')
const staffTreks = ref([])
const participantList = ref([])

onMounted(() => {
  if (currentUser.value?.role === 'Staff') {
    loadStaffTreks()
  }
})

async function loadStaffTreks() {
  currentView.value = 'dashboard'
  try {
    const res = await axios.get('/api/staff/treks')
    staffTreks.value = res.data
  } catch (e) { showAlert('Error loading assigned treks.', 'danger') }
}

async function loadTrekParticipants(trekId) {
  try {
    const res = await axios.get(`/api/staff/treks/${trekId}/users`)
    participantList.value = res.data
    currentView.value = 'participants'
  } catch (e) { showAlert('Error fetching participants list.', 'danger') }
}

async function saveStaffTrekUpdates(t) {
  try {
    await axios.put(`/api/staff/treks/${t.id}`, { slots: t.slots, status: t.status })
    showAlert('Trek details updated!')
    loadStaffTreks()
  } catch (e) { showAlert(e.response?.data?.error || 'Failed to update details.', 'danger') }
}
</script>
