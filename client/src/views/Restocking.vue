<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Success notification -->
      <div v-if="orderSuccess" class="success-banner">
        {{ t('restocking.orderPlaced') }}
      </div>

      <!-- Budget slider card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <div class="budget-display">{{ formatMoney(budget) }}</div>
        </div>
        <div class="slider-container">
          <input
            type="range"
            min="1000"
            max="50000"
            step="500"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="slider-labels">
            <span>{{ formatMoney(1000) }}</span>
            <span>{{ formatMoney(50000) }}</span>
          </div>
        </div>
        <div class="budget-remaining" :class="{ 'over-budget': remainingBudget < 0 }">
          <span v-if="remainingBudget >= 0">
            {{ t('restocking.remaining') }}: {{ formatMoney(remainingBudget) }}
          </span>
          <span v-else>
            {{ t('restocking.overBudget') }}: {{ formatMoney(Math.abs(remainingBudget)) }}
          </span>
        </div>
      </div>

      <!-- Summary stats row -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsToRestock') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.estimatedTotal') }}</div>
          <div class="stat-value">{{ formatMoney(totalEstimatedCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.withinBudget') }}</div>
          <div class="stat-value">{{ selectedCount }}</div>
        </div>
      </div>

      <!-- Recommendations table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <span class="selected-count">{{ t('restocking.selectedItems') }}: {{ selectedCount }}</span>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          <p>{{ t('restocking.noRecommendations') }}</p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.include') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.shortage') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.estimatedCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in tableRows" :key="item.item_sku" :class="{ 'row-selected': item.included }">
                <td>
                  <input
                    type="checkbox"
                    :checked="item.included"
                    @change="toggleItem(item.item_sku)"
                    class="row-checkbox"
                  />
                </td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.shortage }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ formatMoney(item.unit_cost) }}</td>
                <td>
                  <input
                    type="number"
                    :value="item.quantity"
                    @input="updateQuantity(item.item_sku, $event)"
                    min="0"
                    :max="item.shortage"
                    class="quantity-input"
                    :disabled="!item.included"
                  />
                </td>
                <td>
                  <strong>{{ formatMoney(item.rowCost) }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Order summary bar -->
      <div class="order-summary-bar">
        <div class="summary-info">
          <span class="summary-item">
            {{ t('restocking.selectedItems') }}: <strong>{{ selectedCount }}</strong>
          </span>
          <span class="summary-item">
            {{ t('restocking.totalCost') }}: <strong :class="{ 'over-budget-text': remainingBudget < 0 }">{{ formatMoney(totalSelectedCost) }}</strong>
          </span>
          <span class="summary-item">
            {{ t('restocking.remaining') }}: <strong :class="remainingBudget >= 0 ? 'within-budget-text' : 'over-budget-text'">{{ formatMoney(remainingBudget) }}</strong>
          </span>
        </div>
        <button
          class="place-order-btn"
          :disabled="selectedCount === 0 || totalSelectedCost > budget || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref([])
    const budget = ref(10000)
    const selections = ref({})
    const submitting = ref(false)
    const orderSuccess = ref(false)

    // Currency formatting helper
    const formatMoney = (value) => {
      if (value == null || isNaN(value)) return '$0.00'
      const currency = currentCurrency.value || 'USD'
      const locale = currency === 'JPY' ? 'ja-JP' : 'en-US'
      return value.toLocaleString(locale, {
        style: 'currency',
        currency: currency
      })
    }

    // Computed: build table rows from recommendations + selections
    const tableRows = computed(() => {
      return recommendations.value.map(rec => {
        const sel = selections.value[rec.item_sku]
        const included = sel ? sel.included : false
        const quantity = sel ? sel.quantity : 0
        return {
          ...rec,
          included,
          quantity,
          rowCost: included ? quantity * rec.unit_cost : 0
        }
      })
    })

    const selectedItems = computed(() => {
      return tableRows.value.filter(row => row.included && row.quantity > 0)
    })

    const selectedCount = computed(() => selectedItems.value.length)

    const totalSelectedCost = computed(() => {
      return selectedItems.value.reduce((sum, row) => sum + row.rowCost, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - totalSelectedCost.value
    })

    const totalEstimatedCost = computed(() => {
      return recommendations.value.reduce((sum, rec) => sum + rec.estimated_cost, 0)
    })

    // Auto-fill logic: greedily select items within budget
    const autoFill = () => {
      const newSelections = {}
      let remaining = budget.value

      for (const rec of recommendations.value) {
        const fullCost = rec.recommended_quantity * rec.unit_cost
        if (fullCost <= remaining) {
          newSelections[rec.item_sku] = {
            included: true,
            quantity: rec.recommended_quantity
          }
          remaining -= fullCost
        } else {
          const partialQty = Math.floor(remaining / rec.unit_cost)
          if (partialQty > 0) {
            newSelections[rec.item_sku] = {
              included: true,
              quantity: partialQty
            }
            remaining -= partialQty * rec.unit_cost
          } else {
            newSelections[rec.item_sku] = {
              included: false,
              quantity: rec.recommended_quantity
            }
          }
        }
      }

      selections.value = newSelections
    }

    // Toggle include/exclude for a row
    const toggleItem = (sku) => {
      const sel = selections.value[sku]
      if (sel) {
        selections.value = {
          ...selections.value,
          [sku]: { ...sel, included: !sel.included }
        }
      }
    }

    // Update quantity for a row
    const updateQuantity = (sku, event) => {
      const val = parseInt(event.target.value, 10)
      const sel = selections.value[sku]
      if (sel) {
        const rec = recommendations.value.find(r => r.item_sku === sku)
        const maxQty = rec ? rec.shortage : Infinity
        const quantity = isNaN(val) ? 0 : Math.max(0, Math.min(val, maxQty))
        selections.value = {
          ...selections.value,
          [sku]: { ...sel, quantity }
        }
      }
    }

    // Load recommendations from API
    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const data = await api.getRestockingRecommendations({
          warehouse: filters.warehouse,
          category: filters.category
        })
        recommendations.value = data
        autoFill()
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Place order
    const placeOrder = async () => {
      if (selectedCount.value === 0 || totalSelectedCost.value > budget.value) return

      submitting.value = true
      try {
        const items = selectedItems.value.map(row => ({
          sku: row.item_sku,
          name: row.item_name,
          quantity: row.quantity,
          unit_cost: row.unit_cost,
          warehouse: row.warehouse,
          category: row.category
        }))

        await api.submitRestockingOrder({
          items,
          budget: budget.value
        })

        orderSuccess.value = true
        setTimeout(() => { orderSuccess.value = false }, 3000)

        // Reload recommendations after order
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    // Watch budget changes to re-run auto-fill
    watch(budget, () => {
      autoFill()
    })

    // Watch filter changes to reload data
    watch([selectedLocation, selectedCategory], () => {
      loadRecommendations()
    })

    onMounted(loadRecommendations)

    return {
      t,
      loading,
      error,
      recommendations,
      budget,
      tableRows,
      selectedCount,
      totalSelectedCost,
      totalEstimatedCost,
      remainingBudget,
      orderSuccess,
      submitting,
      formatMoney,
      toggleItem,
      updateQuantity,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
}

.slider-container {
  padding: 0.5rem 0 0.25rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.budget-remaining {
  margin-top: 0.75rem;
  padding: 0.625rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  background: #f0fdf4;
  color: #16a34a;
}

.budget-remaining.over-budget {
  background: #fef2f2;
  color: #dc2626;
}

.selected-count {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.row-checkbox {
  width: 18px;
  height: 18px;
  accent-color: #2563eb;
  cursor: pointer;
}

.row-selected {
  background: #f0f9ff;
}

.quantity-input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  text-align: center;
  color: #334155;
  background: #ffffff;
  outline: none;
  transition: border-color 0.2s;
}

.quantity-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}

.quantity-input:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.order-summary-bar {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  position: sticky;
  bottom: 1rem;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
}

.summary-info {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.summary-item {
  font-size: 0.875rem;
  color: #64748b;
}

.summary-item strong {
  color: #0f172a;
}

.within-budget-text {
  color: #16a34a !important;
}

.over-budget-text {
  color: #dc2626 !important;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-weight: 600;
  font-size: 0.938rem;
  text-align: center;
}
</style>
