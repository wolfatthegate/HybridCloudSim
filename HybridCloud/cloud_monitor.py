class CloudMonitor:
    def __init__(self, sim_env):
        self.env = sim_env
        
        # Track live utilization state variables
        self.current_qpu_allocated = 0
        self.current_cpu_allocated = 0
        self.current_mem_allocated = 0
        
        # Time-integrated totals
        self.accumulated_qpu_time = 0.0
        self.accumulated_cpu_time = 0.0
        self.accumulated_mem_time = 0.0
        
        self.last_update_time = 0.0
        self.utilization_history = []

        # Hook into the EventBus
        if hasattr(sim_env, "event_bus") and sim_env.event_bus:
            sim_env.event_bus.subscribe("device_start", self.on_device_event)
            sim_env.event_bus.subscribe("device_finish", self.on_device_event)

    # ------------------------------------------------------------
    # LAZY CAPACITY LOOKUPS (Ensures environment is fully built)
    # ------------------------------------------------------------
    @property
    def qpu_devices(self):
        return getattr(self.env, "qpu_devices", [])

    @property
    def cpu_devices(self):
        return getattr(self.env, "cpu_devices", [])

    @property
    def qpu_cap(self):
        return sum(getattr(d, "capacity", getattr(getattr(d, "container", None), "capacity", 0)) for d in self.qpu_devices)

    @property
    def cpu_cap(self):
        return sum(getattr(d, "capacity", getattr(getattr(d, "container", None), "capacity", 0)) for d in self.cpu_devices)

    @property
    def mem_cap(self):
        return sum(getattr(d, "mem_bw_capacity", getattr(getattr(d, "mem_bw", None), "capacity", 0)) for d in self.cpu_devices)

    def _update_integrals(self):
        now = self.env.now
        dt = now - self.last_update_time
        if dt > 0:
            self.accumulated_qpu_time += self.current_qpu_allocated * dt
            self.accumulated_cpu_time += self.current_cpu_allocated * dt
            self.accumulated_mem_time += self.current_mem_allocated * dt
        self.last_update_time = now

    def _query_live_allocations(self):
        live_qpu = 0
        for d in self.qpu_devices:
            container = getattr(d, "container", None)
            if container:
                live_qpu += (container.capacity - container.level)

        live_cpu = 0
        live_mem = 0
        for d in self.cpu_devices:
            cpu_cont = getattr(d, "container", None)
            if cpu_cont:
                live_cpu += (cpu_cont.capacity - cpu_cont.level)
            
            mem_cont = getattr(d, "mem_bw", None)
            if mem_cont:
                live_mem += (mem_cont.capacity - mem_cont.level)

        return live_qpu, live_cpu, live_mem

    def on_device_event(self, data):
        self._update_integrals()
        
        live_qpu, live_cpu, live_mem = self._query_live_allocations()
        
        self.current_qpu_allocated = live_qpu
        self.current_cpu_allocated = live_cpu
        self.current_mem_allocated = live_mem
        
        T = max(1e-12, self.env.now)
        
        # Now these dynamically fetch the true, initialized capacities!
        qpu_den = self.qpu_cap * T if self.qpu_cap else 1e-12
        cpu_den = self.cpu_cap * T if self.cpu_cap else 1e-12
        mem_den = self.mem_cap * T if self.mem_cap else 1e-12
        
        individual_qpu_status = {
            getattr(d, "name", f"QPU-{i}"): {
                "capacity": getattr(d, "capacity", getattr(getattr(d, "container", None), "capacity", 0)),
                "current_usage": getattr(getattr(d, "container", None), "level", 0) if getattr(d, "container", None) else 0
            } for i, d in enumerate(self.qpu_devices)
        }
        
        individual_cpu_status = {
            getattr(d, "name", f"CPU-{i}"): {
                "capacity": getattr(d, "capacity", getattr(getattr(d, "container", None), "capacity", 0)),
                "current_usage": getattr(getattr(d, "container", None), "level", 0) if getattr(d, "container", None) else 0
            } for i, d in enumerate(self.cpu_devices)
        }
        
        snapshot = {
            "time": round(T, 2),
            "global_qpu_util_percent": round(100.0 * self.accumulated_qpu_time / qpu_den, 2),
            "global_cpu_util_percent": round(100.0 * self.accumulated_cpu_time / cpu_den, 2),
            "global_mem_bw_util_percent": round(100.0 * self.accumulated_mem_time / mem_den, 2),
            "qpu_devices": individual_qpu_status,
            "cpu_devices": individual_cpu_status
        }
        self.utilization_history.append(snapshot)
        
        if self.env.printlog:
        # if True:
            # Added live print tracker per your request
            print(f"[STEP LOG - Time {snapshot['time']:.2f}] "
                  f"QPU: {snapshot['global_qpu_util_percent']}% | "
                  f"CPU: {snapshot['global_cpu_util_percent']}% | "
                  f"Mem BW: {snapshot['global_mem_bw_util_percent']}%")