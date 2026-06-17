<template>
  <section>
    <PageHeader eyebrow="Dashboard" title="采购与库存工作台" />

    <div class="metrics-grid">
      <article class="metric">
        <span>原料种类</span>
        <strong>{{ summary.ingredientCount }}</strong>
      </article>
      <article class="metric">
        <span>预警原料</span>
        <strong>{{ summary.warningCount }}</strong>
      </article>
      <article class="metric">
        <span>供应商</span>
        <strong>{{ suppliers.length }}</strong>
      </article>
      <article class="metric">
        <span>采购订单</span>
        <strong>{{ orders.length }}</strong>
      </article>
    </div>

    <div class="content-grid">
      <section class="panel">
        <h2>库存预警</h2>
        <DataTable :columns="warningColumns" :rows="warningItems">
          <template #stock="{ row }">
            {{ row.stock }} {{ row.unit }}
          </template>
          <template #warningThreshold="{ row }">
            {{ row.warningThreshold }} {{ row.unit }}
          </template>
        </DataTable>
      </section>
      <section class="panel">
        <h2>近期采购订单</h2>
        <DataTable :columns="orderColumns" :rows="orders.slice(0, 5)">
          <template #status="{ row }">
            <StatusBadge :label="statusText(row.status)" :variant="row.status" />
          </template>
          <template #totalAmount="{ row }">¥{{ row.totalAmount.toFixed(2) }}</template>
        </DataTable>
      </section>
    </div>

    <section class="panel" style="margin-top:18px;">
      <div class="recommend-title-bar">
        <h2 style="margin:0;">原料比价推荐摘要</h2>
        <router-link to="/quotes" class="secondary-btn" style="text-decoration:none;">查看完整比价 →</router-link>
      </div>
      <div v-if="!recommendations.length" class="recommend-empty">
        正在加载推荐数据，或前往「供应商比价」查看详细信息。
      </div>
      <div v-else class="dash-rec-grid">
        <article v-for="rec in recommendations" :key="rec.ingredientId" class="dash-rec-card" @click="goQuotes">
          <div class="dash-rec-head">
            <strong>{{ rec.ingredientName }}</strong>
            <span class="badge success">推荐</span>
          </div>
          <div v-if="rec.recommended" class="dash-rec-body">
            <div class="dash-rec-row">
              <span>{{ rec.recommended.supplierName }}</span>
              <strong class="dash-price">¥{{ rec.recommended.unitPrice.toFixed(2) }}</strong>
            </div>
            <div class="dash-rec-row dash-meta">
              <span>{{ '★'.repeat(rec.recommended.supplierRating || 0) }}</span>
              <span>{{ rec.recommended.deliveryDays }}天交付</span>
              <span>评分 {{ rec.recommended.score }}</span>
            </div>
            <ul v-if="rec.summaryReasons.length" class="dash-reasons">
              <li v-for="(r, i) in rec.summaryReasons.slice(0, 2)" :key="i">{{ r }}</li>
            </ul>
            <p v-if="rec.quoteCount > 1" class="dash-count">{{ quoteCountText(rec) }}</p>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { inventoryApi } from '../api/inventory'
import { ordersApi } from '../api/orders'
import { suppliersApi } from '../api/suppliers'
import { quotesApi } from '../api/quotes'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { statusText } from '../utils/format'

const router = useRouter()
const summary = ref({ ingredientCount: 0, warningCount: 0, totalStock: 0 })
const inventory = ref([])
const orders = ref([])
const suppliers = ref([])
const recommendations = ref([])

const warningItems = computed(() => inventory.value.filter((item) => item.warning))
const warningColumns = [
  { key: 'name', label: '原料' },
  { key: 'stock', label: '当前库存' },
  { key: 'warningThreshold', label: '预警线' }
]
const orderColumns = [
  { key: 'orderNo', label: '订单号' },
  { key: 'supplierName', label: '供应商' },
  { key: 'status', label: '状态' },
  { key: 'totalAmount', label: '金额' }
]

function goQuotes() {
  router.push('/quotes')
}

function quoteCountText(rec) {
  if (!rec.totalQuoteCount || rec.quoteCount === rec.totalQuoteCount) {
    return `${rec.quoteCount} 家报价对比`
  }
  return `${rec.quoteCount} 家参与推荐对比 / 共 ${rec.totalQuoteCount} 条报价`
}

onMounted(async () => {
  const [summaryRes, inventoryRes, ordersRes, suppliersRes, recRes] = await Promise.all([
    inventoryApi.summary(),
    inventoryApi.list(),
    ordersApi.list(),
    suppliersApi.list(),
    quotesApi.recommend().catch(() => ({ data: [] }))
  ])
  summary.value = summaryRes.data
  inventory.value = inventoryRes.data
  orders.value = ordersRes.data
  suppliers.value = suppliersRes.data
  recommendations.value = recRes.data || []
})
</script>

<style scoped>
.recommend-title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.dash-rec-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.dash-rec-card {
  border: 1px solid #dde5dc;
  border-radius: 8px;
  background: #fff;
  padding: 14px;
  cursor: pointer;
  transition: transform .15s, box-shadow .15s;
}

.dash-rec-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(22, 54, 37, .08);
}

.dash-rec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.dash-rec-body { display: grid; gap: 6px; }

.dash-rec-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.dash-price {
  color: #256f4a;
  font-size: 16px;
}

.dash-meta {
  color: #6b786f;
  font-size: 12px;
}

.dash-reasons {
  margin: 6px 0 0;
  padding: 8px 10px 8px 24px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 12px;
  color: #815a00;
}

.dash-reasons li { margin: 1px 0; }

.dash-count {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b786f;
}

.recommend-empty {
  padding: 20px;
  color: #7d8981;
  text-align: center;
  background: #f6f8f4;
  border-radius: 8px;
}
</style>
