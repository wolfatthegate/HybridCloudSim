# job_records_manager.py

class JobRecordsManager:
    def __init__(self, event_bus, cost_config=None):
        """
        Initialize the JobRecordsManager with an EventBus instance.
        """
        self.event_bus = event_bus
        self.job_records = {}
        self.cost_config = cost_config or {}
        
    def log_job_event(self, job_id, event_type, timestamp):
        """
        Logs a job event with a timestamp.

        Parameters:
        - job_id: The ID of the job.
        - event_type: The type of event (e.g., 'arrival', 'start', 'finish', 'devc_start', 'devc_finish').
        - timestamp: The timestamp of the event.
        """
        if job_id not in self.job_records:
            self.job_records[job_id] = {}
        
        # Append the timestamp if the event_type already exists
        if job_id not in self.job_records:
            self.job_records[job_id] = {}

        if event_type not in self.job_records[job_id]:
            # First occurrence → create list
            self.job_records[job_id][event_type] = [timestamp]
        else:
            # Subsequent occurrences → append
            self.job_records[job_id][event_type].append(timestamp)

    # @property
    # def records(self):
    #     return self.job_records
    
    def get_job_records(self):
        """
        Returns all job records.
        """
        return self.job_records

    def finalize_job_energy_cost(self, job_id):
        if job_id not in self.job_records:
            return
        
        rec = self.job_records[job_id]
        energy_cfg = self.cost_config.get("energy", {})

        elec_price = energy_cfg.get("electricity_price_per_kwh", 0.0)
        default_qpu_kw = energy_cfg.get("default_qpu_power_kw", 0.0)
        default_cpu_kw = energy_cfg.get("default_cpu_power_kw", 0.0)
        qpu_kw_map = energy_cfg.get("qpu_power_kw", {})
        cpu_kw_map = energy_cfg.get("cpu_power_kw", {})

        qpu_start = rec.get("qpu_start", [])
        qpu_finish = rec.get("qpu_finish", [])
        cpu_start = rec.get("cpu_start", [])
        cpu_finish = rec.get("cpu_finish", [])
        devc_name = rec.get("devc_name", [])

        qpu_energy_kwh = 0.0
        cpu_energy_kwh = 0.0
        qpu_time_s = 0.0
        cpu_time_s = 0.0

        qpu_segments = []
        cpu_segments = []

        # QPU segments (even indices in devc_name)
        for i in range(len(qpu_start)):
            t = qpu_finish[i] - qpu_start[i]
            qpu_time_s += t

            dev = devc_name[2 * i] if 2 * i < len(devc_name) else "UNKNOWN_QPU"
            power_kw = qpu_kw_map.get(dev, default_qpu_kw)

            e = power_kw * (t / 3600.0)
            qpu_energy_kwh += e

            qpu_segments.append({
                "device": dev,
                "time_s": round(t, 4),
                "energy_kwh": round(e, 4),
                "power_kw": round(power_kw, 4)
            })

        # CPU segments (odd indices in devc_name)
        for i in range(len(cpu_start)):
            t = cpu_finish[i] - cpu_start[i]
            cpu_time_s += t

            dev = devc_name[2 * i + 1] if 2 * i + 1 < len(devc_name) else "UNKNOWN_CPU"
            power_kw = cpu_kw_map.get(dev, default_cpu_kw)

            e = power_kw * (t / 3600.0)
            cpu_energy_kwh += e

            cpu_segments.append({
                "device": dev,
                "time_s": round(t, 4),
                "energy_kwh": round(e, 4),
                "power_kw": round(power_kw, 4)
            })

        total_energy_kwh = qpu_energy_kwh + cpu_energy_kwh
        total_cost = total_energy_kwh * elec_price

        # Store results back into the job record
        rec["qpu_time_s"] = round(qpu_time_s, 4)
        rec["cpu_time_s"] = round(cpu_time_s, 4)
        rec["energy_qpu_kwh"] = round(qpu_energy_kwh, 4)
        rec["energy_cpu_kwh"] = round(cpu_energy_kwh, 4)
        rec["energy_total_kwh"] = round(total_energy_kwh, 4)
        rec["cost_energy_total"] = round(total_cost, 4)
        rec["qpu_segments"] = qpu_segments
        rec["cpu_segments"] = cpu_segments