import os
from typing import Optional


class NLPRunLogger:
    """Simple file logger focused on domain events (no HTTP noise).
    Writes compact one-line entries without timestamps.
    """

    def __init__(self, run_id: str, base_dir: str):
        self.run_id = run_id
        self.base_dir = base_dir
        self.logs_dir = os.path.join(base_dir, "run_logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.log_path = os.path.join(self.logs_dir, f"nlp4re_run_{run_id}.log")
        self._fh = open(self.log_path, "a", encoding="utf-8")
        self.log("run", "start", run_id=run_id)

    def log(self, section: str, message: str, **kwargs):
        parts = [f"[{section}]", message]
        if kwargs:
            kv = " ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
            parts.append(kv)
        line = " ".join(parts)
        self._fh.write(line + "\n")
        self._fh.flush()

    def divider(self, title: Optional[str] = None):
        # Visual divider line in logs to separate sections
        bar = "─" * 60
        if title:
            self.log("sep", f"{bar} {title} {bar}")
        else:
            self.log("sep", bar)

    def close(self):
        try:
            self.log("run", "end", run_id=self.run_id)
        except Exception:
            pass
        try:
            self._fh.close()
        except Exception:
            pass

    def set_instance_id(self, instance_id: str):
        """Rename the log file to include the created instance ID and continue logging."""
        try:
            # Close current file handle before renaming
            try:
                self._fh.flush()
                self._fh.close()
            except Exception:
                pass

            new_log_path = os.path.join(
                self.logs_dir, f"nlp4re_run_{self.run_id}_{instance_id}.log"
            )
            try:
                if os.path.exists(self.log_path):
                    os.rename(self.log_path, new_log_path)
            except Exception:
                # If rename fails for any reason, fallback to new path without renaming
                new_log_path = os.path.join(
                    self.logs_dir, f"nlp4re_run_{self.run_id}_{instance_id}.log"
                )

            self.log_path = new_log_path
            self._fh = open(self.log_path, "a", encoding="utf-8")
            self.log("run", "instance", run_id=self.run_id, instance_id=instance_id)
        except Exception:
            # As a last resort, try to reopen original path to not break logging
            try:
                if self._fh.closed:
                    self._fh = open(self.log_path, "a", encoding="utf-8")
            except Exception:
                pass
