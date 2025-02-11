import randomname
import warnings

from typing import Union, List

from qiskit.providers import Options
from qiskit.circuit import QuantumCircuit

from .qsim_job import QsimJob
from .scaleway_backend import ScalewayBackend
from ..utils import QaaSClient


class QsimBackend(ScalewayBackend):
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

        # Set option validators
        self.options.set_validator("shots", (1, 100000000))

        self._max_qubits = num_qubits

    def __repr__(self) -> str:
        return f"<QsimBackend(name={self.name},num_qubits={self.num_qubits},platform_id={self.id})>"

    @property
    def target(self):
        return None

    @property
    def num_qubits(self) -> int:
        return self._max_qubits

    @property
    def max_circuits(self):
        return 1

    def run(
        self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], **kwargs
    ) -> QsimJob:
        if not isinstance(circuits, list):
            circuits = [circuits]

        job_config = {key: value for key, value in self._options.items()}

        for kwarg in kwargs:
            if not hasattr(self.options, kwarg):
                warnings.warn(
                    f"Option {kwarg} is not used by this backend",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                job_config[kwarg] = kwargs[kwarg]

        job_name = f"qj-qsim-{randomname.get_name()}"

        session_id = job_config.get("session_id", None)

        job_config.pop("session_id")
        job_config.pop("session_name")
        job_config.pop("session_deduplication_id")
        job_config.pop("session_max_duration")
        job_config.pop("session_max_idle_duration")

        job = QsimJob(
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
        return Options(
            session_id="auto",
            session_name="qsim-session-from-qiskit",
            session_deduplication_id="qsim-session-from-qiskit",
            session_max_duration="20m",
            session_max_idle_duration="20m",
            shots=1000,
            circuit_memoization_size=0,
            max_fused_gate_size=2,
            ev_noisy_repetitions=1,
            denormals_are_zeros=False,
        )
