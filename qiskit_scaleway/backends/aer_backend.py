import randomname
import warnings

from typing import Union, List

from qiskit.providers import Options
from qiskit.circuit import QuantumCircuit
from qiskit.providers import convert_to_target
from qiskit.providers.models import QasmBackendConfiguration
from qiskit_aer.backends.aer_simulator import AerSimulator
from qiskit_aer.backends.aerbackend import NAME_MAPPING

from .aer_job import AerJob
from .scaleway_backend import ScalewayBackend
from ..utils import QaaSClient


class AerBackend(ScalewayBackend):
    def __init__(
        self,
        provider,
        client: QaaSClient,
        backend_id: str,
        name: str,
        availability: str,
        version: str,
        num_qubits: int,
        metadata: str,
    ):
        super().__init__(
            provider=provider,
            client=client,
            backend_id=backend_id,
            name=name,
            availability=availability,
            version=version,
        )

        self._options = self._default_options()

        # Create Target
        self._configuration = QasmBackendConfiguration.from_dict(
            AerSimulator._DEFAULT_CONFIGURATION
        )
        self._properties = None
        self._target = convert_to_target(
            self._configuration, self._properties, None, NAME_MAPPING
        )
        self._target.num_qubits = num_qubits

        # Set option validators
        self.options.set_validator("shots", (1, 1e6))
        self.options.set_validator("memory", bool)

    def __repr__(self) -> str:
        return f"<AerBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def target(self):
        return self._target

    @property
    def num_qubits(self) -> int:
        return self._target.num_qubits

    @property
    def max_circuits(self):
        return 1024

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **run_options
    ) -> AerJob:
        if not isinstance(circuits, list):
            circuits = [circuits]

        job_config = {key: value for key, value in self._options.items()}

        for kwarg in run_options:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = run_options[kwarg]

        job_name = f"qj-aer-{randomname.get_name()}"

        session_id = job_config.get("session_id", None)

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = AerJob(
            backend=self,
            client=self._client,
            circuits=circuits,
            config=job_config,
            name=job_name,
        )

        if session_id in ["auto", None]:
            session_id = self.start_session(name=f"auto-{self._options.session_name}")
            assert session_id is not None

        job.submit(session_id)

        return job

    @classmethod
    def _default_options(self):
        # https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html
        return Options(
            session_id="auto",
            session_name="aer-session-from-qiskit",
            session_deduplication_id="aer-session-from-qiskit",
            session_max_duration="20m",
            session_max_idle_duration="20m",
            shots=1000,
            memory=False,
            seed_simulator=None,
            method="automatic",
            precision="double",
            max_shot_size=None,
            enable_truncation=True,
            max_parallel_experiments=1,
            zero_threshold=1e-10,
            validation_threshold=1e-8,
            accept_distributed_results=None,
            runtime_parameter_bind_enable=False,
            statevector_parallel_threshold=14,
            statevector_sample_measure_opt=10,
            stabilizer_max_snapshot_probabilities=32,
            extended_stabilizer_sampling_method="resampled_metropolis",
            extended_stabilizer_metropolis_mixing_time=5000,
            extended_stabilizer_approximation_error=0.05,
            extended_stabilizer_norm_estimation_samples=100,
            extended_stabilizer_norm_estimation_repetitions=3,
            extended_stabilizer_parallel_threshold=100,
            extended_stabilizer_probabilities_snapshot_samples=3000,
            matrix_product_state_max_bond_dimension=None,
            matrix_product_state_truncation_threshold=1e-16,
            mps_sample_measure_algorithm="mps_apply_measure",
            mps_log_data=False,
            mps_swap_direction="mps_swap_left",
            chop_threshold=1e-8,
            mps_parallel_threshold=14,
            mps_omp_threads=1,
            tensor_network_num_sampling_qubits=10,
            use_cuTensorNet_autotuning=False,
            fusion_enable=True,
            fusion_verbose=False,
            fusion_max_qubit=None,
            fusion_threshold=None,
        )
