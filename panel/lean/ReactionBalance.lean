def carbonReactants : Nat := 2 * 1
def carbonProducts : Nat := 1 * 2 + 3 * 0

def hydrogenReactants : Nat := 6 * 2
def hydrogenProducts : Nat := 1 * 6 + 3 * 2

def oxygenReactants : Nat := 2 * 2
def oxygenProducts : Nat := 1 * 1 + 3 * 1

theorem carbon_conserved : carbonReactants = carbonProducts := by decide
theorem hydrogen_conserved : hydrogenReactants = hydrogenProducts := by decide
theorem oxygen_conserved : oxygenReactants = oxygenProducts := by decide
