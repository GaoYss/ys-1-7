<template>
  <section>
    <PageHeader eyebrow="Quotes" :title="editingQuoteId ? '编辑报价' : '供应商比价'">
      <button class="primary-btn" @click="submitQuote">
        {{ editingQuoteId ? '更新报价' : '登记报价' }}
      </button>
      <button v-if="editingQuoteId" class="secondary-btn" @click="resetForm">取消编辑</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          原料
          <select v-model.number="form.ingredientId">
            <option disabled :value="null">选择原料</option>
            <option v-for="item in ingredients" :key="item.id" :value="item.id">
              {{ item.name }} / {{ item.unit }}
            </option>
          </select>
        </label>
        <label>
          供应商
          <select v-model.number="form.supplierId">
            <option disabled :value="null">选择供应商</option>
            <option v-for="s in suppliers" :key="s.id" :value="s.id">
              {{ s.name }}（{{ '★'.repeat(s.rating) }}）
            </option>
          </select>
        </label>
        <label>
          单价（元）
          <input v-model.number="form.unitPrice" type="number" min="0" step="0.01" />
        </label>
        <label>
          交付周期（天）
          <input v-model.number="form.deliveryDays" type="number" min="1" />
        </label>
        <label>
          状态
          <select v-model="form.status">
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </label>
      </div>
      <p v-if="errorText" class="error-text" style="margin-top:10px;">{{ errorText }}</p>
    </section>

    <div class="toolbar">
      <select v-model="filterIngredientId" @change="loadQuotes">
        <option :value="null">全部原料</option>
        <option v-for="item in ingredients" :key="item.id" :value="item.id">
          {{ item.name }}
        </option>
      </select>
      <select v-model="filterSupplierId" @change="loadQuotes">
        <option :value="null">全部供应商</option>
        <option v-for="s in allSuppliers" :key="s.id" :value="s.id">
          {{ s.name }}
        </option>
      </select>
      <button class="secondary-btn" @click="loadRecommendations">
        {{ recommendations.length ? '刷新推荐' : '查看推荐' }}
      </button>
    </div>

    <DataTable :columns="quoteColumns" :rows="filteredQuotes">
      <template #unitPrice="{ row }">¥{{ row.unitPrice.toFixed(2) }}</template>
      <template #supplierRating="{ row }">
        {{ '★'.repeat(row.supplierRating || 0) }}{{ '☆'.repeat(5 - (row.supplierRating || 0)) }}
      </template>
      <template #deliveryDays="{ row }">{{ row.deliveryDays }}天</template>
      <template #status="{ row }">
        <div style="display:flex;flex-direction:column;gap:4px;">
          <StatusBadge
            :label="row.status === 'active' ? '报价启用' : '报价停用'"
            :variant="row.status === 'active' ? 'success' : 'neutral'"
          />
          <StatusBadge
            v-if="row.supplierStatus"
            :label="row.supplierStatus === 'active' ? '供应商合作中' : '供应商停用'"
            :variant="row.supplierStatus === 'active' ? 'approved' : 'cancelled'"
          />
        </div>
      </template>
      <template #actions="{ row }">
        <button class="secondary-btn" @click="editQuote(row)">编辑</button>
        <button class="secondary-btn" @click="toggleQuoteStatus(row)">
          {{ row.status === 'active' ? '停用报价' : '启用报价' }}
        </button>
        <button class="secondary-btn danger-btn" @click="removeQuote(row)">删除</button>
      </template>
    </DataTable>

    <section v-if="recommendations.length" class="panel recommend-panel">
      <div class="recommend-title-bar">
        <h2 style="margin:0;">采购推荐</h2>
        <div class="legend">
          <span class="legend-item"><span class="dot price-dot"></span>价格权重 50%</span>
          <span class="legend-item"><span class="dot rating-dot"></span>评级权重 30%</span>
          <span class="legend-item"><span class="dot delivery-dot"></span>交付权重 20%</span>
        </div>
      </div>
      <div class="recommend-grid">
        <div v-for="rec in recommendations" :key="rec.ingredientId" class="recommend-card">
          <div class="recommend-header">
            <div>
              <strong>{{ rec.ingredientName }}</strong>
              <small style="color:#6b786f;margin-left:6px;">（{{ rec.quoteCount }} 家报价）</small>
            </div>
            <span class="badge success">推荐</span>
          </div>

          <ul v-if="rec.summaryReasons.length" class="summary-reasons">
            <li v-for="(r, i) in rec.summaryReasons" :key="i">{{ r }}</li>
          </ul>

          <div v-if="rec.recommended" class="recommend-body">
            <div class="recommend-row">
              <span>推荐供应商</span>
              <strong>{{ rec.recommended.supplierName }}</strong>
            </div>
            <div class="recommend-row">
              <span>单价</span>
              <strong class="price">¥{{ rec.recommended.unitPrice.toFixed(2) }} / {{ rec.ingredientUnit }}</strong>
            </div>
            <div class="recommend-row">
              <span>评级</span>
              <span>{{ '★'.repeat(rec.recommended.supplierRating || 0) }}{{ '☆'.repeat(5 - (rec.recommended.supplierRating || 0)) }}</span>
            </div>
            <div class="recommend-row">
              <span>交付周期</span>
              <span>{{ rec.recommended.deliveryDays }}天</span>
            </div>
            <div class="recommend-row">
              <span>综合评分</span>
              <strong class="score">{{ rec.recommended.score }}</strong>
            </div>

            <div class="score-breakdown">
              <div class="breakdown-row">
                <span class="breakdown-label"><span class="dot price-dot"></span>价格分</span>
                <div class="bar-wrap">
                  <div class="bar price-bar" :style="{ width: (rec.recommended.scoreBreakdown.price * 100) + '%' }"></div>
                </div>
                <span class="breakdown-value">{{ rec.recommended.scoreBreakdown.price }}</span>
              </div>
              <div class="breakdown-row">
                <span class="breakdown-label"><span class="dot rating-dot"></span>评级分</span>
                <div class="bar-wrap">
                  <div class="bar rating-bar" :style="{ width: (rec.recommended.scoreBreakdown.rating * 100) + '%' }"></div>
                </div>
                <span class="breakdown-value">{{ rec.recommended.scoreBreakdown.rating }}</span>
              </div>
              <div class="breakdown-row">
                <span class="breakdown-label"><span class="dot delivery-dot"></span>交付分</span>
                <div class="bar-wrap">
                  <div class="bar delivery-bar" :style="{ width: (rec.recommended.scoreBreakdown.delivery * 100) + '%' }"></div>
                </div>
                <span class="breakdown-value">{{ rec.recommended.scoreBreakdown.delivery }}</span>
              </div>
            </div>

            <ul class="reason-tags">
              <li v-for="(reason, i) in rec.recommended.reasons" :key="i" class="reason-tag">{{ reason }}</li>
            </ul>
          </div>
          <div v-else class="recommend-empty">暂无启用报价</div>

          <details v-if="rec.quotes.length > 1" class="compare-details">
            <summary>查看全部 {{ rec.quotes.length }} 家报价对比</summary>
            <table class="compare-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>供应商</th>
                  <th>单价</th>
                  <th>评级</th>
                  <th>交付</th>
                  <th>评分</th>
                  <th>分析</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(q, idx) in rec.quotes" :key="q.id" :class="{ 'is-best': idx === 0 }">
                  <td><strong v-if="idx === 0" class="rank-best">第1</strong><span v-else>第{{ idx + 1 }}</span></td>
                  <td>{{ q.supplierName }}</td>
                  <td>¥{{ q.unitPrice.toFixed(2) }}</td>
                  <td>{{ '★'.repeat(q.supplierRating || 0) }}</td>
                  <td>{{ q.deliveryDays }}天</td>
                  <td><strong>{{ q.score }}</strong></td>
                  <td style="font-size:12px;white-space:normal;max-width:220px;">
                    <span v-for="(r, i) in q.reasons" :key="i" class="mini-tag">{{ r }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </details>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'

import { quotesApi } from '../api/quotes'
import { suppliersApi } from '../api/suppliers'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const quotes = ref([])
const ingredients = ref([])
const suppliers = ref([])
const allSuppliers = ref([])
const recommendations = ref([])
const filterIngredientId = ref(null)
const filterSupplierId = ref(null)
const editingQuoteId = ref(null)
const errorText = ref('')

const form = reactive({
  ingredientId: null,
  supplierId: null,
  unitPrice: 0,
  deliveryDays: 3,
  status: 'active'
})

const quoteColumns = [
  { key: 'ingredientName', label: '原料' },
  { key: 'supplierName', label: '供应商' },
  { key: 'unitPrice', label: '单价' },
  { key: 'supplierRating', label: '评级' },
  { key: 'deliveryDays', label: '交付周期' },
  { key: 'status', label: '状态' },
  { key: 'actions', label: '操作' }
]

const filteredQuotes = computed(() => {
  let list = quotes.value
  if (filterIngredientId.value) list = list.filter((q) => q.ingredientId === filterIngredientId.value)
  if (filterSupplierId.value) list = list.filter((q) => q.supplierId === filterSupplierId.value)
  return list
})

function resetForm() {
  editingQuoteId.value = null
  errorText.value = ''
  Object.assign(form, {
    ingredientId: null,
    supplierId: null,
    unitPrice: 0,
    deliveryDays: 3,
    status: 'active'
  })
}

async function loadOptions() {
  const res = await quotesApi.options()
  ingredients.value = res.data.ingredients
  suppliers.value = res.data.suppliers
  const allRes = await suppliersApi.list()
  allSuppliers.value = allRes.data
}

async function loadQuotes() {
  const params = {}
  if (filterIngredientId.value) params.ingredientId = filterIngredientId.value
  if (filterSupplierId.value) params.supplierId = filterSupplierId.value
  const res = await quotesApi.list(params)
  quotes.value = res.data
}

async function submitQuote() {
  errorText.value = ''
  if (!form.ingredientId || !form.supplierId || !form.unitPrice) {
    errorText.value = '请选择原料、供应商并填写单价'
    return
  }
  try {
    if (editingQuoteId.value) {
      await quotesApi.update(editingQuoteId.value, { ...form })
    } else {
      await quotesApi.create({ ...form })
    }
    resetForm()
    await loadQuotes()
    if (recommendations.value.length) await loadRecommendations()
  } catch (e) {
    errorText.value = e?.response?.data?.error || '操作失败，请检查输入'
  }
}

function editQuote(row) {
  editingQuoteId.value = row.id
  Object.assign(form, {
    ingredientId: row.ingredientId,
    supplierId: row.supplierId,
    unitPrice: row.unitPrice,
    deliveryDays: row.deliveryDays,
    status: row.status
  })
  errorText.value = ''
}

async function toggleQuoteStatus(row) {
  errorText.value = ''
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  try {
    await quotesApi.update(row.id, { ...row, status: newStatus })
    await loadQuotes()
    if (recommendations.value.length) await loadRecommendations()
  } catch (e) {
    errorText.value = e?.response?.data?.error || '状态切换失败'
  }
}

async function removeQuote(row) {
  errorText.value = ''
  if (!confirm(`确认删除该报价？\n${row.ingredientName} - ${row.supplierName} ¥${row.unitPrice.toFixed(2)}`)) return
  try {
    await quotesApi.remove(row.id)
    if (editingQuoteId.value === row.id) resetForm()
    await loadQuotes()
    if (recommendations.value.length) await loadRecommendations()
  } catch (e) {
    errorText.value = e?.response?.data?.error || '删除失败'
  }
}

async function loadRecommendations() {
  const params = {}
  if (filterIngredientId.value) params.ingredientId = filterIngredientId.value
  const res = await quotesApi.recommend(params)
  recommendations.value = res.data
}

onMounted(async () => {
  await Promise.all([loadOptions(), loadQuotes()])
})
</script>

<style scoped>
.danger-btn {
  background: #ffe4e2;
  color: #a72f25;
}

.recommend-title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #6b786f;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.price-dot { background: #256f4a; }
.rating-dot { background: #b58900; }
.delivery-dot { background: #268bd2; }

.summary-reasons {
  margin: 0 0 12px;
  padding: 10px 12px 10px 28px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 13px;
  color: #815a00;
}

.summary-reasons li { margin: 2px 0; }

.score-breakdown {
  margin-top: 10px;
  padding: 10px 12px;
  background: #f6f8f4;
  border-radius: 6px;
  display: grid;
  gap: 6px;
}

.breakdown-row {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.breakdown-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #526057;
}

.bar-wrap {
  height: 8px;
  background: #dde5dc;
  border-radius: 4px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 4px;
  transition: width .3s;
}

.price-bar { background: #256f4a; }
.rating-bar { background: #d4a72c; }
.delivery-bar { background: #3a8fd6; }

.breakdown-value {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}

.reason-tags {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.reason-tag {
  background: #e7eee8;
  color: #223029;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.rank-best {
  color: #256f4a;
}

.mini-tag {
  display: inline-block;
  background: #eef3ef;
  padding: 2px 6px;
  border-radius: 4px;
  margin: 2px;
  color: #526057;
}
</style>
