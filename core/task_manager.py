import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

class BackgroundTask(QObject):
    progress_updated = pyqtSignal(str, int)  # task_id, percentage
    status_updated = pyqtSignal(str, str)    # task_id, status
    log_added = pyqtSignal(str, str)         # task_id, log_line
    finished = pyqtSignal(str, bool)         # task_id, success

    def __init__(self, task_id, name, commands, cwd=None):
        super().__init__()
        self.task_id = task_id
        self.name = name
        self.commands = commands
        self.cwd = cwd
        self.status = "Queued"
        self.progress = 0
        self.start_time = 0
        self.elapsed_time = 0
        self.thread = None

class TaskManager(QObject):
    task_added = pyqtSignal(str)              # task_id
    queue_changed = pyqtSignal()
    active_task_changed = pyqtSignal(str)      # task_id

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TaskManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.tasks = {}
            cls._instance.queue = []
            cls._instance.active_task_id = None
            cls._instance.history = []
            
            # Start timer for elapsed time updates
            cls._instance.timer = QTimer()
            cls._instance.timer.timeout.connect(cls._instance.update_active_times)
            cls._instance.timer.start(1000)
        return cls._instance

    def add_task(self, name, commands, cwd=None):
        task_id = f"task_{int(time.time())}"
        task = BackgroundTask(task_id, name, commands, cwd)
        self.tasks[task_id] = task
        self.queue.append(task_id)
        
        task.status_updated.connect(self.on_task_status_changed)
        task.progress_updated.connect(self.on_task_progress_changed)
        
        self.task_added.emit(task_id)
        self.queue_changed.emit()
        self.process_queue()
        return task_id

    def process_queue(self):
        if self.active_task_id:
            return # A task is already running
        if not self.queue:
            return # No tasks in queue
            
        self.active_task_id = self.queue.pop(0)
        task = self.tasks[self.active_task_id]
        task.status = "Running"
        task.start_time = time.time()
        task.status_updated.emit(task.task_id, "Running")
        self.active_task_changed.emit(self.active_task_id)
        self.queue_changed.emit()
        
        # Start command thread execution (stub for UI, backend will hook into this)
        self.run_task_thread(task)

    def run_task_thread(self, task):
        # We define a simple dummy thread if backend hasn't overwritten it
        # Real backend commands will hook into this or start their own threads
        class DummyWorker(QThread):
            def run(self):
                for i in range(1, 11):
                    time.sleep(1)
                    if self.isInterruptionRequested():
                        break
                    task.progress = i * 10
                    task.progress_updated.emit(task.task_id, task.progress)
                    task.log_added.emit(task.task_id, f"Processing segment {i}/10...")
                task.finished.emit(task.task_id, True)

        task.thread = DummyWorker()
        task.thread.finished.connect(lambda: self.on_task_finished(task.task_id, True))
        task.thread.start()

    def cancel_task(self, task_id):
        if task_id in self.queue:
            self.queue.remove(task_id)
            task = self.tasks[task_id]
            task.status = "Cancelled"
            task.status_updated.emit(task_id, "Cancelled")
            self.history.append(task_id)
            self.queue_changed.emit()
        elif task_id == self.active_task_id:
            task = self.tasks[task_id]
            if task.thread:
                task.thread.requestInterruption()
                task.thread.wait()
            task.status = "Cancelled"
            task.status_updated.emit(task_id, "Cancelled")
            task.finished.emit(task_id, False)

    def on_task_status_changed(self, task_id, status):
        pass

    def on_task_progress_changed(self, task_id, progress):
        pass

    def on_task_finished(self, task_id, success):
        task = self.tasks[task_id]
        task.status = "Finished" if success else "Failed"
        task.status_updated.emit(task_id, task.status)
        self.history.append(task_id)
        
        if self.active_task_id == task_id:
            self.active_task_id = None
            self.active_task_changed.emit(None)
            
        self.process_queue()

    def update_active_times(self):
        if self.active_task_id:
            task = self.tasks[self.active_task_id]
            task.elapsed_time = int(time.time() - task.start_time)
            # Emit status change to force UI refresh
            task.status_updated.emit(task.task_id, "Running")
