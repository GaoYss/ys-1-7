<template>
  <section>
    <PageHeader eyebrow="Suppliers" :title="editingId ? '编辑供应商' : '供应商管理'">
      <button class="primary-btn" @click="submitSupplier">
        {{ editingId ? '更新供应商' : '保存供应商' }}
      </button>
      <button v-if="editingId" class="secondary-btn" @click="resetForm">取消编辑</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          供应商名称
          <input v-model="form.name" placeholder="如：香叶原料供应链" />
        </label>
        <label>
          联系人
          <input v-model="form.contact" placeholder="如：林经理" />
        </label>
        <label>
          电话
          <input v-model="form.phone" placeholder="如：13800010001" />
        </label>
        <label>
          评级（1-5星）
          <input v-model.number="form.rating" type="number" min="1" max="5" />
        </label>
        <label>
          状态
          <select v-model="form.status">
            <option value="active">合作中</option>
            <option value="inactive">已停用</option>
          </select>
        </label>
        <label class="span-2">
          地址
          <input v-model="form.address" placeholder="选填" />
        </label>
      </div>
    </section>

    <DataTable :columns="columns" :rows="suppliers">
      <template #rating="{ row }">{{ '★'.repeat(row.rating) }}{{ '☆'.repeat(5 - row.rating) }}</template>
      <template #status="{ row }">
        <StatusBadge
          :label="row.status === 'active' ? '合作中' : '已停用'"
          :variant="row.status === 'active' ? 'success' : 'neutral'"
        />
      </template>
      <template #actions="{ row }">
        <button class="secondary-btn" @click="editSupplier(row)">编辑</button>
        <button class="secondary-btn" @click="toggleSupplierStatus(row)">
          {{ row.status === 'active' ? '停用' : '启用' }}
        </button>
        <button class="secondary-btn danger-btn" @click="removeSupplier(row)">删除</button>
      </template>
    </DataTable>

    <p v-if="errorText" class="error-text">{{ errorText }}</p>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { suppliersApi } from '../api/suppliers'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const suppliers = ref([])
const editingId = ref(null)
const errorText = ref('')
const form = reactive({
  name: '',
  contact: '',
  phone: '',
  address: '',
  rating: 5,
  status: 'active'
})
const columns = [
  { key: 'name', label: '供应商' },
  { key: 'contact', label: '联系人' },
  { key: 'phone', label: '电话' },
  { key: 'rating', label: '评级' },
  { key: 'status', label: '状态' },
  { key: 'actions', label: '操作' }
]

function resetForm() {
  editingId.value = null
  errorText.value = ''
  Object.assign(form, {
    name: '',
    contact: '',
    phone: '',
    address: '',
    rating: 5,
    status: 'active'
  })
}

async function loadSuppliers() {
  const res = await suppliersApi.list()
  suppliers.value = res.data
}

async function submitSupplier() {
  errorText.value = ''
  if (!form.name || !form.contact || !form.phone) {
    errorText.value = '请填写供应商名称、联系人、电话'
    return
  }
  try {
    if (editingId.value) {
      await suppliersApi.update(editingId.value, { ...form })
    } else {
      await suppliersApi.create({ ...form })
    }
    resetForm()
    await loadSuppliers()
  } catch (e) {
    errorText.value = e?.response?.data?.error || '操作失败，请检查输入'
  }
}

function editSupplier(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    contact: row.contact,
    phone: row.phone,
    address: row.address || '',
    rating: row.rating,
    status: row.status
  })
  errorText.value = ''
}

async function toggleSupplierStatus(row) {
  errorText.value = ''
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  try {
    await suppliersApi.update(row.id, { ...row, status: newStatus })
    await loadSuppliers()
  } catch (e) {
    errorText.value = e?.response?.data?.error || '状态切换失败'
  }
}

async function removeSupplier(row) {
  errorText.value = ''
  if (!confirm(`确认删除供应商「${row.name}」？该供应商若存在报价或订单则不可删除。`)) return
  try {
    await suppliersApi.remove(row.id)
    if (editingId.value === row.id) resetForm()
    await loadSuppliers()
  } catch (e) {
    errorText.value = e?.response?.data?.error || '删除失败'
  }
}

onMounted(loadSuppliers)
</script>

<style scoped>
.danger-btn {
  background: #ffe4e2;
  color: #a72f25;
}
</style>
