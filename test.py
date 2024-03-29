import os
import qiskit

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

provider = ScalewayProvider(
    project_id=os.environ["TEST_USER_PROJECT_ID"],
    secret_key=os.environ["TEST_USER_TOKEN"],
    url="http://localhost:5044/qaas/v1alpha1",
)

# The backends() method lists all available computing backends. Printing it
# renders it as a table that shows each backend's containing workspace.
print(provider.backends())

# Retrieve a backend by providing search criteria. The search must have a single match
backend = provider.get_backend("aer_simulation_local")

# Define a quantum circuit that produces a 4-qubit GHZ state.
qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)
qc.cx(0, 3)
qc.measure_all()

# # Transpile for the target backend
# # useless for now, could return the same circuit (later could be useful for Perceval to Qiskit)
qc = qiskit.transpile(qc, backend)

# Execute on the target backend
# Send job in QASM format
# Every params from backend + job are send to the session
result = backend.run(qc, shots=1000).result()

# TODO
if result.success:
    print(result.get_counts())
else:
    print(result.to_dict()["error"])
