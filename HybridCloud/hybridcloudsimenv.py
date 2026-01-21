# hybridcloudsimenv.py

from HybridCloud import *
from HybridCloud.job_generator import JobGenerator
from HybridCloud.hybridcloud import HybridCloud

class HybridCloudSimEnv(simpy.Environment):
    def __init__(self, qpu_devices, cpu_devices, broker_class=HybridBroker, job_feed_method='generator', job_generation_model=None, file_path=None, printlog = False, cost_config=None):
        """
        Initialize the hybrid simulation environment.

        Parameters:
        - qpu_devices: List of quantum devices.
        - cpu_devices: List of classical CPU devices.
        - broker_class: Class of the broker to use for job handling.
        - job_feed_method: 'generator' or 'dispatcher'.
        - job_generation_model: Callable for job inter-arrival times.
        - file_path: Path to CSV if using dispatcher mode.
        """
        super().__init__()
        self.qpu_devices = qpu_devices
        self.cpu_devices = cpu_devices
        self.broker_class = broker_class
        self.job_feed_method = job_feed_method
        self.job_generation_model = job_generation_model
        self.file_path = file_path
        self.printlog = printlog
        self.event_bus = EventBus()
        # -------------------------------
        # Energy & cost configuration
        # -------------------------------
        self.cost_config = cost_config or {
            "energy": {
                # Electricity price ($/kWh)
                "electricity_price_per_kwh": 0.18,

                # -------------------------
                # QPU baseline power (kW)
                # -------------------------
                # Superconducting QPU often modeled as baseline-power dominated by cryogenics.
                "default_qpu_power_kw": 80.0,
                "qpu_power_kw": {},  # optional per-QPU overrides, e.g., {"QPU-1": 90.0}

                # -------------------------
                # CPU power model (CloudSim-style affine)
                # -------------------------
                # P = P_idle + (P_peak - P_idle) * u
                # u = min(1, cpu_units / capacity_units)
                "cpu_power_model": "affine",  # "affine" or "constant"

                # Defaults (kW and units)
                "default_cpu_idle_kw": 0.25,
                "default_cpu_peak_kw": 0.80,
                "default_cpu_capacity_units": 16,

                # Optional per-CPU overrides (by device name)
                "cpu_idle_kw": {},            # e.g., {"CPU-1": 0.25}
                "cpu_peak_kw": {},            # e.g., {"CPU-1": 0.80}
                "cpu_capacity_units": {},     # e.g., {"CPU-1": 32}

                # If you ever want constant-power CPU mode:
                "default_cpu_power_kw": 0.60,
                "cpu_power_kw": {},           # optional per-CPU overrides for constant mode
            }
        }
        
        # self.job_records_manager = JobRecordsManager(self.event_bus,
        #                                     cost_config=self.cost_config)

        self.job_records_manager = JobRecordsManager(
            self.event_bus,
            cost_config=self.cost_config
        )
        
        self.qcloud = HybridCloud(
            env=self,
            qpu_devices=self.qpu_devices,
            cpu_devices=self.cpu_devices,
            job_records_manager=self.job_records_manager
        )

        self.job_generator = None
        self._initialize_devices()
        self._initialize_job_generator()
        


        
    def _initialize_devices(self):

        for device in self.qpu_devices + self.cpu_devices:
            device.assign_env(self)
            device.job_records_manager = self.job_records_manager
            device.event_bus = self.event_bus
            # self.process(device.maintenance(False))

    def _initialize_job_generator(self):

        self.job_generator = JobGenerator(
            env=self,
            broker_class=self.broker_class,
            devices=self.qpu_devices + self.cpu_devices,  # pass all devices
            job_records_manager=self.job_records_manager,
            event_bus=self.event_bus,
            qcloud=self.qcloud,
            method=self.job_feed_method,
            job_generation_model=self.job_generation_model,
            file_path=self.file_path,
            printlog=self.printlog
        )

    def run(self, until=None):
        self.process(self.job_generator.run())
        print(f"{self.now:.2f}: SIMULATION STARTED")
        super().run(until=until if until is not None else None)
        # After run: print a summary of jobs seen vs finished
        try:
            recs = self.job_records_manager.get_job_records()  # or however you access them
            finished = [j for j, r in recs.items() if r.get("cpu_finish")]
            if self.printlog:
                print(f"Jobs processed: {finished}")
        except Exception:
            print(f"no job records found")
            pass
        finally: 
            print(f"{self.now:.2f}: SIMULATION ENDED")
            print(f"Number of jobs processed: {len(finished)}")