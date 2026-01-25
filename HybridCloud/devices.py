# devices.py

import simpy, random

class CPU:
    def __init__(self, name, env=None, cpu_capacity=100, mem_bw_capacity=200):
        """
        cpu_capacity:    total CPU units (integer)
        mem_bw_capacity: total memory bandwidth units (e.g., MB/s 'units') (integer)
        """
        self.name = name
        self.type = "CPU"
        self.env = None
        self.queue = None
        self.container = None           # CPU units
        self.mem_bw = None              # memory bandwidth units
        self.resource = None
        self.cpu_capacity = int(cpu_capacity)
        self.mem_bw_capacity = int(mem_bw_capacity)
        if env is not None:
            self.assign_env(env)

    def assign_env(self, env):
        self.env = env
        self.queue = simpy.Resource(env, capacity=1)
        self.container = simpy.Container(env=env, capacity=self.cpu_capacity, init=self.cpu_capacity)
        self.mem_bw   = simpy.Container(env=env, capacity=self.mem_bw_capacity, init=self.mem_bw_capacity) 
        self.resource = simpy.PriorityResource(env=env, capacity=1)

    def maintenance(self, _):
        return self.env.timeout(0)  
            
    def process_job(self, job, wait_time_start):
        job_id = job.job_id
        duration = random.uniform(1, 3)
        cpu_units = random.randint(4, 10)
        mem_bw    = int(getattr(job, "mem_bw",  20))
        
        self.job_records_manager.log_job_event(job_id, 'devc_name', self.name)
        # phase arrival
        self.job_records_manager.log_job_event(job_id, 'cpu_arrive', round(self.env.now, 4))
        self.job_records_manager.log_job_event(job.job_id, 'cpu_units', cpu_units)
        self.job_records_manager.log_job_event(job_id, 'cpu_mem_bw', mem_bw)
        
        yield self.container.get(cpu_units)
        try:
            yield self.mem_bw.get(mem_bw)
        except:
            # If mem_bw get fails for some reason, give CPU units back and re-raise
            yield self.container.put(cpu_units)
            raise
            
        # service start
        # self.job_records_manager.log_job_event(job_id, 'cpu_start', round(self.env.now, 4))
        
        # print(f"{self.env.now:.2f}: Job {job_id} running on {self.name} for {duration:.1f} (cpu_units={cpu_units}, mem_bw={mem_bw})")

        yield self.env.timeout(duration)

        # service finish
        # self.job_records_manager.log_job_event(job_id, 'cpu_finish', round(self.env.now, 4))
        
        # print(f"{self.env.now:.2f}: Job {job.job_id} finished running on {self.name} for {duration:.1f}")

        # Publish a 'device_finish' event
        self.event_bus.publish("device_finish", {
            "device": self.name,
            "job_id": job_id,
            "timestamp": round(self.env.now, 2),
        })
        
        # always return capacity
        try:
            yield self.container.put(cpu_units)
            yield self.mem_bw.put(mem_bw)
        except Exception as e:
            print(f"{self.env.now:.2f}: ERROR while returning units for Job {job.job_id} on {self.name}: {e}")            
            


class AMDRyzen(CPU):
    """
    Drop-in CPU-compatible AMD Ryzen model.
    IMPORTANT: keep .type == "CPU" so broker filters still match.
    """

    def __init__(
        self,
        name,
        env=None,
        cores=8,
        threads=16,
        base_ghz=3.8,
        boost_ghz=5.0,
        ipc_factor=1.10,
        mem_bw_gbps=51.2,
        cpu_units_per_thread=8,
        mem_bw_units_per_gbps=4,
        printlog=False,
        **kwargs,
    ):
        self.cores = int(cores)
        self.threads = int(threads)
        self.base_ghz = float(base_ghz)
        self.boost_ghz = float(boost_ghz)
        self.ipc_factor = float(ipc_factor)
        self.mem_bw_gbps = float(mem_bw_gbps)
        self.cpu_units_per_thread = int(cpu_units_per_thread)
        self.mem_bw_units_per_gbps = float(mem_bw_units_per_gbps)
        self.printlog = printlog

        cpu_capacity = self.threads * self.cpu_units_per_thread
        mem_bw_capacity = int(round(self.mem_bw_gbps * self.mem_bw_units_per_gbps))

        super().__init__(
            name=name,
            env=env,
            cpu_capacity=cpu_capacity,
            mem_bw_capacity=mem_bw_capacity,
        )

        # Keep compatibility with broker code that checks dev.type == "CPU"
        self.type = "CPU"
        # Keep a separate label for identification/logging
        self.model = "AMD_Ryzen"

    @property
    def effective_perf(self) -> float:
        avg_ghz = 0.5 * (self.base_ghz + self.boost_ghz)
        return avg_ghz * self.ipc_factor

    def assign_env(self, env):
        """
        Ensure we always end up with container/mem_bw/resource exactly like CPU.
        """
        super().assign_env(env)

        # Optional safety assertions (helpful during debugging)
        assert self.container is not None, "AMDRyzen.container was not initialized"
        assert self.mem_bw is not None, "AMDRyzen.mem_bw was not initialized"

    def process_job(self, job, wait_time_start):
        job_id = job.job_id

        cpu_units = int(getattr(job, "cpu_units", random.randint(4, max(10, self.threads))))
        mem_bw = int(getattr(job, "mem_bw", 20))

        work = float(getattr(job, "cpu_work", 0.0))
        if work > 0:
            parallel_eff = (cpu_units ** 0.85)
            duration = work / (max(self.effective_perf, 1e-6) * parallel_eff)
        else:
            base_duration = random.uniform(1, 3)
            duration = base_duration / max(self.effective_perf, 1e-6)

        self.job_records_manager.log_job_event(job_id, 'devc_name', self.name)
        self.job_records_manager.log_job_event(job_id, 'cpu_arrive', round(self.env.now, 4))
        self.job_records_manager.log_job_event(job_id, 'cpu_units', cpu_units)
        self.job_records_manager.log_job_event(job_id, 'cpu_mem_bw', mem_bw)

        # use model tag instead of type
        self.job_records_manager.log_job_event(job_id, 'cpu_model', getattr(self, "model", "CPU"))
        self.job_records_manager.log_job_event(job_id, 'cpu_cores', self.cores)
        self.job_records_manager.log_job_event(job_id, 'cpu_threads', self.threads)
        self.job_records_manager.log_job_event(job_id, 'cpu_eff_perf', round(self.effective_perf, 4))

        # identical resource semantics to CPU
        yield self.container.get(cpu_units)
        try:
            yield self.mem_bw.get(mem_bw)
        except:
            yield self.container.put(cpu_units)
            raise

        yield self.env.timeout(duration)

        self.event_bus.publish("device_finish", {
            "device": self.name,
            "job_id": job_id,
            "timestamp": round(self.env.now, 2),
        })

        try:
            yield self.container.put(cpu_units)
            yield self.mem_bw.put(mem_bw)
        except Exception as e:
            print(f"{self.env.now:.2f}: ERROR while returning units for Job {job.job_id} on {self.name}: {e}")