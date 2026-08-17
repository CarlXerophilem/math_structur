import Std

theorem retrieval_order_preserves_records
    {α : Type} (before after : List α) (h : before.Perm after) (x : α) :
    x ∈ before ↔ x ∈ after := by
  exact h.mem_iff
