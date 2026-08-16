/-
Optional Lean 4 export sketch.

This file was generated to show how a Content-MathML/FunctionContract
representation could become proof obligations. It was NOT compiled in the
current run because Lean is not installed on the machine.
-/

def ClosedUnder {α : Type} (D : α → Prop) (g : α → α) : Prop :=
  ∀ x, D x → D (g x)

def IsIterativeSquareRoot {α : Type} (D : α → Prop)
    (f g : α → α) : Prop :=
  ClosedUnder D g ∧ ∀ x, D x → g (g x) = f x

theorem identity_is_its_own_square_root {α : Type} (D : α → Prop) :
    IsIterativeSquareRoot D (fun x => x) (fun x => x) := by
  constructor
  · intro x hx
    exact hx
  · intro x hx
    rfl

