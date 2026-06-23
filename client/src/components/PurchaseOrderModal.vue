<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{
                mode === "create"
                  ? "Create Purchase Order"
                  : "Purchase Order Details"
              }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M15 5L5 15M5 5L15 15"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <!-- Create Mode -->
          <template v-if="mode === 'create'">
            <div class="modal-body">
              <div class="po-header">
                <div class="po-icon">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <rect
                      x="10"
                      y="6"
                      width="28"
                      height="36"
                      rx="3"
                      stroke="currentColor"
                      stroke-width="3"
                    />
                    <path
                      d="M17 16H31M17 24H31M17 32H25"
                      stroke="currentColor"
                      stroke-width="2.5"
                      stroke-linecap="round"
                    />
                  </svg>
                </div>
                <div class="po-title-section">
                  <h4 class="item-name">
                    {{ translateProductName(backlogItem.item_name) }}
                  </h4>
                  <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
                </div>
              </div>

              <div class="shortage-summary">
                <div class="summary-card info">
                  <div class="summary-label">Quantity Needed</div>
                  <div class="summary-value">
                    {{ backlogItem.quantity_needed }}
                  </div>
                </div>
                <div class="summary-card warning">
                  <div class="summary-label">Currently Available</div>
                  <div class="summary-value">
                    {{ backlogItem.quantity_available }}
                  </div>
                </div>
              </div>

              <form class="po-form" @submit.prevent="submitOrder">
                <div class="form-group">
                  <label class="form-label" for="supplier-name"
                    >Supplier Name</label
                  >
                  <input
                    id="supplier-name"
                    v-model="form.supplier_name"
                    type="text"
                    class="form-input"
                    placeholder="Enter supplier name"
                    required
                  />
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label" for="quantity">Quantity</label>
                    <input
                      id="quantity"
                      v-model.number="form.quantity"
                      type="number"
                      class="form-input"
                      :placeholder="String(shortage)"
                      min="1"
                      required
                    />
                  </div>
                  <div class="form-group">
                    <label class="form-label" for="unit-cost"
                      >Unit Cost ($)</label
                    >
                    <input
                      id="unit-cost"
                      v-model.number="form.unit_cost"
                      type="number"
                      class="form-input"
                      placeholder="0.00"
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="delivery-date"
                    >Expected Delivery Date</label
                  >
                  <input
                    id="delivery-date"
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="form-input"
                    required
                  />
                </div>

                <div class="form-group">
                  <label class="form-label" for="notes">Notes</label>
                  <textarea
                    id="notes"
                    v-model="form.notes"
                    class="form-input form-textarea"
                    placeholder="Additional notes (optional)"
                    rows="3"
                  ></textarea>
                </div>

                <div v-if="totalCost > 0" class="total-cost">
                  <span class="total-label">Estimated Total Cost</span>
                  <span class="total-value"
                    >${{
                      totalCost.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })
                    }}</span
                  >
                </div>
              </form>

              <div v-if="submitError" class="error-message">
                {{ submitError }}
              </div>
            </div>

            <div class="modal-footer">
              <button
                class="btn-secondary"
                @click="close"
                :disabled="submitting"
              >
                Cancel
              </button>
              <button
                class="btn-primary"
                @click="submitOrder"
                :disabled="submitting || !isFormValid"
              >
                {{ submitting ? "Creating..." : "Create Purchase Order" }}
              </button>
            </div>
          </template>

          <!-- View Mode -->
          <template v-else>
            <div class="modal-body">
              <div v-if="viewLoading" class="loading-state">
                Loading purchase order...
              </div>
              <div v-else-if="viewError" class="error-message">
                {{ viewError }}
              </div>
              <template v-else-if="purchaseOrder">
                <div class="po-header">
                  <div class="po-icon view-icon">
                    <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                      <rect
                        x="10"
                        y="6"
                        width="28"
                        height="36"
                        rx="3"
                        stroke="currentColor"
                        stroke-width="3"
                      />
                      <path
                        d="M17 16H31M17 24H31M17 32H25"
                        stroke="currentColor"
                        stroke-width="2.5"
                        stroke-linecap="round"
                      />
                    </svg>
                  </div>
                  <div class="po-title-section">
                    <h4 class="item-name">
                      {{ translateProductName(backlogItem.item_name) }}
                    </h4>
                    <div class="item-sku">PO #{{ purchaseOrder.id }}</div>
                  </div>
                  <span class="status-badge" :class="purchaseOrder.status">
                    {{ purchaseOrder.status }}
                  </span>
                </div>

                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">
                      {{ purchaseOrder.supplier_name }}
                    </div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">
                      {{ purchaseOrder.quantity }} units
                    </div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Unit Cost</div>
                    <div class="info-value">
                      ${{
                        Number(purchaseOrder.unit_cost).toLocaleString(
                          "en-US",
                          {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          },
                        )
                      }}
                    </div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Total Cost</div>
                    <div class="info-value total">
                      ${{
                        (
                          purchaseOrder.quantity * purchaseOrder.unit_cost
                        ).toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })
                      }}
                    </div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">
                      {{ formatDate(purchaseOrder.expected_delivery_date) }}
                    </div>
                  </div>

                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">
                      <span
                        class="status-badge inline"
                        :class="purchaseOrder.status"
                      >
                        {{ purchaseOrder.status }}
                      </span>
                    </div>
                  </div>
                </div>

                <div v-if="purchaseOrder.notes" class="notes-section">
                  <div class="info-label">Notes</div>
                  <div class="notes-content">{{ purchaseOrder.notes }}</div>
                </div>
              </template>
            </div>

            <div class="modal-footer">
              <button class="btn-secondary" @click="close">Close</button>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { api } from "../api";
import { useI18n } from "../composables/useI18n";

const { translateProductName } = useI18n();

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  backlogItem: {
    type: Object,
    default: null,
  },
  mode: {
    type: String,
    default: "create",
    validator: (value) => ["create", "view"].includes(value),
  },
});

const emit = defineEmits(["close", "po-created"]);

// Create mode state
const form = ref({
  supplier_name: "",
  quantity: null,
  unit_cost: null,
  expected_delivery_date: "",
  notes: "",
});
const submitting = ref(false);
const submitError = ref(null);

// View mode state
const purchaseOrder = ref(null);
const viewLoading = ref(false);
const viewError = ref(null);

const shortage = computed(() => {
  if (!props.backlogItem) return 0;
  return (
    props.backlogItem.quantity_needed - props.backlogItem.quantity_available
  );
});

const totalCost = computed(() => {
  const qty = form.value.quantity || 0;
  const cost = form.value.unit_cost || 0;
  return qty * cost;
});

const isFormValid = computed(() => {
  return (
    form.value.supplier_name.trim() !== "" &&
    form.value.quantity > 0 &&
    form.value.unit_cost >= 0 &&
    form.value.expected_delivery_date !== ""
  );
});

const resetForm = () => {
  form.value = {
    supplier_name: "",
    quantity: null,
    unit_cost: null,
    expected_delivery_date: "",
    notes: "",
  };
  submitting.value = false;
  submitError.value = null;
};

const close = () => {
  emit("close");
};

const submitOrder = async () => {
  if (!isFormValid.value || submitting.value) return;

  submitting.value = true;
  submitError.value = null;

  try {
    const payload = {
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name.trim(),
      quantity: form.value.quantity,
      unit_cost: form.value.unit_cost,
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes.trim(),
    };

    const response = await api.createPurchaseOrder(payload);
    emit("po-created", response);
    resetForm();
  } catch (err) {
    submitError.value = "Failed to create purchase order. Please try again.";
    console.error("PO creation error:", err);
  } finally {
    submitting.value = false;
  }
};

const loadPurchaseOrder = async () => {
  if (!props.backlogItem) return;

  viewLoading.value = true;
  viewError.value = null;

  try {
    const response = await api.getPurchaseOrderByBacklogItem(
      props.backlogItem.id,
    );
    purchaseOrder.value = response;
  } catch (err) {
    viewError.value = "Failed to load purchase order details.";
    console.error("PO load error:", err);
  } finally {
    viewLoading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "N/A";
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

// Watch for modal open to reset form or load PO
watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      if (props.mode === "create") {
        resetForm();
        // Pre-fill quantity with shortage amount
        if (shortage.value > 0) {
          form.value.quantity = shortage.value;
        }
      } else if (props.mode === "view") {
        loadPurchaseOrder();
      }
    } else {
      // Reset on close
      purchaseOrder.value = null;
      viewError.value = null;
      resetForm();
    }
  },
);
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.po-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.po-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.po-icon.view-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.po-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.5rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: "Monaco", "Courier New", monospace;
}

.shortage-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  padding: 1.25rem;
  border-radius: 10px;
  border: 2px solid;
}

.summary-card.info {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.summary-card.warning {
  border-color: #fed7aa;
  background: #fffbeb;
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-card.info .summary-value {
  color: #2563eb;
}

.summary-card.warning .summary-value {
  color: #f59e0b;
}

/* Form styles */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-input {
  padding: 0.625rem 0.875rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: #94a3b8;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.total-cost {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  margin-top: 0.5rem;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

/* View mode styles */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.total {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.status-badge.inline {
  padding: 0.25rem 0.75rem;
  font-size: 0.813rem;
}

.status-badge.pending {
  background: #fed7aa;
  color: #92400e;
}

.status-badge.approved {
  background: #bbf7d0;
  color: #166534;
}

.status-badge.ordered {
  background: #bfdbfe;
  color: #1e40af;
}

.status-badge.received {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.cancelled {
  background: #fecaca;
  color: #991b1b;
}

.notes-section {
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.notes-content {
  margin-top: 0.5rem;
  font-size: 0.938rem;
  color: #334155;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* Loading and error states */
.loading-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error-message {
  padding: 0.875rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 1rem;
}

/* Footer buttons */
.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #3b82f6;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover {
  background: #2563eb;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
