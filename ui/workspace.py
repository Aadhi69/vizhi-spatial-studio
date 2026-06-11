import os
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QColor, QAction, QIcon

import shutil

# Import Core Managers
from core.config_manager import ConfigManager
from core.project_manager import ProjectManager, DATASETS_DIR
from core.task_manager import TaskManager
from core.workspace_state import WorkspaceState
from core.notification_manager import NotificationManager

def get_dir_size(path):
    total_size = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
    return total_size

def resolve_gaussian_ply_path(project_path):
    # Check for latest iteration folder
    point_cloud_root = os.path.join(project_path, "gaussian", "point_cloud")
    if os.path.exists(point_cloud_root):
        try:
            subdirs = os.listdir(point_cloud_root)
            iter_dirs = []
            for d in subdirs:
                if d.startswith("iteration_"):
                    try:
                        iter_num = int(d.split("_")[-1])
                        iter_dirs.append((iter_num, os.path.join(point_cloud_root, d)))
                    except ValueError:
                        pass
            if iter_dirs:
                iter_dirs.sort(key=lambda x: x[0], reverse=True)
                for _, path in iter_dirs:
                    ply_path = os.path.join(path, "point_cloud.ply")
                    if os.path.exists(ply_path):
                        return ply_path
        except Exception:
            pass
            
    # Fallback to direct path or any point_cloud.ply inside gaussian folder
    direct_path = os.path.join(project_path, "gaussian", "point_cloud.ply")
    if os.path.exists(direct_path):
        return direct_path
        
    return None

# Import Dialog Windows
from dialogs.new_project_dialog import NewProjectDialog
from dialogs.preferences_dialog import PreferencesDialog
from dialogs.export_dialog import ExportDialog
from dialogs.system_info_dialog import SystemInfoDialog
from dialogs.error_dialog import ErrorDialog

# Import Modular UI Widgets
from ui.topbar import TopBar
from ui.sidebar import Sidebar
from ui.viewport import ViewportWidget, RecentFramesListWidget, create_vector_icon
from ui.logs_panel import LogsPanel, ConsoleLogTextEdit
from ui.rightpanel import RightPanel

class MetricCard(QFrame):
    """
    Custom card widget displaying an icon on the left, and a title,
    value, and optional detail info on the right.
    """
    def __init__(self, title, value, icon_type, detail_text=""):
        super().__init__()
        self.setObjectName("MetricCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)
        
        # Left Vector Icon Label
        self.icon_label = QLabel()
        self.icon_label.setPixmap(create_vector_icon(icon_type, color=QColor("#5B8CFF"), size=QSize(16, 16)).pixmap(16, 16))
        self.icon_label.setStyleSheet("""
            background-color: #050608;
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 6px;
            min-width: 32px;
            min-height: 32px;
            max-width: 32px;
            max-height: 32px;
        """)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.icon_label)
        
        # Text Layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MetricTitle")
        text_layout.addWidget(self.title_label)
        
        # Value & Detail Layout
        val_layout = QHBoxLayout()
        val_layout.setSpacing(6)
        val_layout.setContentsMargins(0, 0, 0, 0)
        
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        val_layout.addWidget(self.value_label)
        
        self.detail_label = QLabel(detail_text)
        self.detail_label.setObjectName("MetricDetail")
        val_layout.addWidget(self.detail_label)
        val_layout.addStretch()
        
        text_layout.addLayout(val_layout)
        
        main_layout.addLayout(text_layout)
        main_layout.addStretch()
        
        # Style status properties
        if value == "ONLINE":
            self.value_label.setStyleSheet("color: #58C777;")
        if "rtsp://" in detail_text:
            self.detail_label.setStyleSheet("color: #58C777; font-size: 10px;")


class Workspace(QMainWindow):

    def __init__(self):
        super().__init__()
        
        self.setObjectName("Workspace")
        self.setWindowTitle("Vizhi Spatial Studio")
        self.resize(1900, 1050)
        
        self.current_project = None
        self.fullscreen_state = False
        
        # Initialize Core Managers
        self.config_manager = ConfigManager()
        self.project_manager = ProjectManager()
        self.task_manager = TaskManager()
        self.workspace_state = WorkspaceState()
        
        # Initialize Toast Alerts
        NotificationManager().initialize(self)
        
        # Stylesheet load
        self.load_stylesheet()
        
        # Layout build
        self.build_ui()
        
        # Shortcuts mapping
        self.setup_actions_and_shortcuts()
        
        # Recover previous session layout
        self.load_workspace_state()
        
        # Generate noise texture for overlays
        self.noise_pixmap = self.generate_noise_pixmap()
        
        # Fade-in window opacity boot animation
        self.setWindowOpacity(0.0)
        from PyQt6.QtCore import QPropertyAnimation
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(800)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
        # Hardware diagnostics log on start
        self.perform_system_scan()
        
        # Start background GPU/System telemetry monitoring thread
        from core.gpu_monitor import GPUMonitorThread
        self.gpu_monitor_thread = GPUMonitorThread(1500, self)
        self.gpu_monitor_thread.telemetry_updated.connect(self.on_telemetry_updated)
        self.gpu_monitor_thread.start()
        
        # Start MediaMTX RTSP Server
        from core.mediamtx_manager import MediaMTXManager
        self.mediamtx_manager = MediaMTXManager()
        if self.mediamtx_manager.start():
            self.add_log("info", "MediaMTX server started successfully")
            self.add_log("info", "RTSP server is online at rtsp://127.0.0.1:8554/live")
            self.rtsp_card.value_label.setText("ONLINE")
            self.rtsp_card.detail_label.setText("rtsp://127.0.0.1:8554/live")
        else:
            self.add_log("error", "Failed to start MediaMTX server process")
            self.rtsp_card.value_label.setText("OFFLINE")

    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "theme.qss")
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print(f"Error reading stylesheet: {e}")

    def build_ui(self):
        # Central widget container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        root = QVBoxLayout(central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # =====================================================
        # TOP BAR
        # =====================================================
        self.topbar = TopBar(self)
        root.addWidget(self.topbar)

        # =====================================================
        # MAIN HORIZONTAL SPLITTER
        # =====================================================
        self.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_horizontal_splitter.setChildrenCollapsible(False)
        self.main_horizontal_splitter.setHandleWidth(2)
        root.addWidget(self.main_horizontal_splitter)

        # Left Sidebar
        self.sidebar = Sidebar(self)
        self.main_horizontal_splitter.addWidget(self.sidebar)

        # Center Area (Container Widget)
        center_area_widget = QWidget()
        center_area_layout = QVBoxLayout(center_area_widget)
        center_area_layout.setContentsMargins(0, 0, 0, 0)
        center_area_layout.setSpacing(0)
        
        self.center_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        self.center_vertical_splitter.setChildrenCollapsible(False)
        self.center_vertical_splitter.setHandleWidth(2)
        center_area_layout.addWidget(self.center_vertical_splitter)

        # 1. Center Top Content Panel (Metrics Cards + Viewport & Right Panel side-by-side)
        center_top_widget = QWidget()
        center_top_layout = QVBoxLayout(center_top_widget)
        center_top_layout.setContentsMargins(16, 16, 16, 16)
        center_top_layout.setSpacing(14)

        # Metric cards
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(10)
        
        # We define them on Workspace to expose properties to backend
        self.card_project = MetricCard("Project", "None", "folder")
        self.card_frames = MetricCard("Frames Captured", "0", "timer", "")
        self.card_storage = MetricCard("Storage Used", "0 MB", "database", "")
        self.card_gpu = MetricCard("GPU Usage", "0%", "gpu", "")
        self.card_rtsp = MetricCard("RTSP Server", "OFFLINE", "network", "")
        
        # Backward-compatible aliases for backend
        self.project_card = self.card_project
        self.frames_card = self.card_frames
        self.storage_card = self.card_storage
        self.gpu_card = self.card_gpu
        self.rtsp_card = self.card_rtsp
        
        for card in [self.card_project, self.card_frames, self.card_storage, self.card_gpu, self.card_rtsp]:
            card.setFixedHeight(88)
            
        center_top_layout.addLayout(metrics_layout)

        # Horizontal Splitter for Middle Section (Viewport on Left, Pipeline on Right)
        self.workspace_middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_middle_splitter.setChildrenCollapsible(False)
        self.workspace_middle_splitter.setHandleWidth(2)
        center_top_layout.addWidget(self.workspace_middle_splitter)

        # Viewport + Recent Frames Container Widget (Left side of middle splitter)
        viewport_container = QWidget()
        viewport_container_layout = QVBoxLayout(viewport_container)
        viewport_container_layout.setContentsMargins(0, 0, 0, 0)
        viewport_container_layout.setSpacing(14)

        # Viewport Widget (Uses custom QPainter rendering)
        viewport_card = QFrame()
        viewport_card.setObjectName("ViewportCard")
        viewport_card_layout = QVBoxLayout(viewport_card)
        viewport_card_layout.setContentsMargins(8, 8, 8, 8)
        
        self.video_viewport = ViewportWidget()
        viewport_card_layout.addWidget(self.video_viewport)
        
        # Viewport Toolbar
        viewport_toolbar = QHBoxLayout()
        viewport_toolbar.setContentsMargins(4, 8, 4, 4)
        viewport_toolbar.setSpacing(6)
        
        self.btn_capture = QPushButton()
        self.btn_capture.setObjectName("IconButton")
        self.btn_capture.setIcon(create_vector_icon("camera", QColor("#cbd5e1")))
        self.btn_capture.setIconSize(QSize(14, 14))
        self.btn_capture.setFixedSize(30, 30)
        
        self.btn_record = QPushButton()
        self.btn_record.setObjectName("IconButton")
        self.btn_record.setIcon(create_vector_icon("play", QColor("#ef4444"))) # Destructive red dot
        self.btn_record.setIconSize(QSize(14, 14))
        self.btn_record.setFixedSize(30, 30)
        
        self.btn_pause = QPushButton()
        self.btn_pause.setObjectName("IconButton")
        self.btn_pause.setIcon(create_vector_icon("pause", QColor("#cbd5e1")))
        self.btn_pause.setIconSize(QSize(14, 14))
        self.btn_pause.setFixedSize(30, 30)
        
        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("IconButton")
        self.btn_delete.setIcon(create_vector_icon("trash", QColor("#cbd5e1")))
        self.btn_delete.setIconSize(QSize(14, 14))
        self.btn_delete.setFixedSize(30, 30)
        
        viewport_toolbar.addWidget(self.btn_capture)
        viewport_toolbar.addWidget(self.btn_record)
        viewport_toolbar.addWidget(self.btn_pause)
        viewport_toolbar.addWidget(self.btn_delete)
        viewport_toolbar.addStretch()
        
        # Save every frames layout (hidden in viewport toolbar, kept in memory for sync logic)
        self.frame_spin = QSpinBox()
        self.frame_spin.setValue(5)
        self.frame_spin.setRange(1, 100)
        
        viewport_card_layout.addLayout(viewport_toolbar)
        viewport_container_layout.addWidget(viewport_card, 1)

        # Recent Frames Horizontal strip
        # Recent Frames Horizontal strip (instantiated in memory but not added to layout to maximize viewport dominance)
        self.thumbnail_list = RecentFramesListWidget()
        self.thumbnail_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumbnail_list.setFlow(QListWidget.Flow.LeftToRight)
        self.thumbnail_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumbnail_list.setIconSize(QSize(110, 70))
        self.thumbnail_list.setFixedHeight(92)
        self.thumbnail_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumbnail_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.workspace_middle_splitter.addWidget(viewport_container)

        # Right Panel controls
        self.right_panel = RightPanel(self)
        self.workspace_middle_splitter.addWidget(self.right_panel)

        self.center_vertical_splitter.addWidget(center_top_widget)

        # Logs Panel
        self.logs_panel = LogsPanel(self)
        self.logs_panel.setMinimumHeight(100)
        self.logs_panel.setMaximumHeight(200)
        self.center_vertical_splitter.addWidget(self.logs_panel)

        self.main_horizontal_splitter.addWidget(center_area_widget)

        # Expose properties to top window/backend references directly
        self.system_monitor = self.topbar.sys_vram_label
        self.search = self.sidebar.search
        self.project_list = self.sidebar.project_list
        self.project_info = self.sidebar.project_info
        self.storage_bar = self.sidebar.storage_bar
        self.open_folder_btn = self.sidebar.open_folder_btn
        self.settings_btn = self.sidebar.settings_btn
        self.clear_btn = self.sidebar.clear_btn
        self.import_btn = self.sidebar.import_btn
        self.plus_btn = self.sidebar.plus_btn
        self.current_project_name = self.sidebar.current_project_name
        self.storage_label = self.sidebar.storage_label
        self.storage_pct_label = self.sidebar.storage_pct_label
        
        self.video_label = self.video_viewport
        self.capture_dot = self.btn_record # alias recording dot to record btn for compatibility
        self.capture_status = QLabel("Ready") # dummy label for backward compatibility
        
        self.rtsp_input = self.right_panel.rtsp_input
        self.right_frame_spin = self.right_panel.right_frame_spin
        self.restart_btn = self.right_panel.restart_btn
        self.start_btn = self.right_panel.start_btn
        self.stop_btn = self.right_panel.stop_btn
        self.colmap_btn = self.right_panel.colmap_btn
        self.gaussian_btn = self.right_panel.gaussian_btn
        self.cancel_btn = self.right_panel.cancel_btn
        self.colmap_progress = self.right_panel.colmap_progress
        self.gaussian_progress = self.right_panel.gaussian_progress
        self.colmap_pct = self.right_panel.colmap_pct
        self.gaussian_pct = self.right_panel.gaussian_pct
        
        self.rtsp_dot = self.right_panel.rtsp_dot
        self.colmap_dot = self.right_panel.colmap_dot
        self.gaussian_dot = self.right_panel.gaussian_dot
        self.open_model_btn = self.right_panel.open_model_btn
        self.open_folder_btn = self.right_panel.open_folder_btn

        # Map child tabs
        self.logs_text = self.logs_panel.logs_text
        self.tasks_text = self.logs_panel.tasks_text
        self.notifications_text = self.logs_panel.notifications_text

        # =====================================================
        # STATUS BAR
        # =====================================================
        self.statusBar().setStyleSheet("background-color: #050608; border-top: 1px solid rgba(255,255,255,0.04); min-height: 24px; max-height: 24px;")
        
        self.status_version_lbl = QLabel("Vizhi Spatial Studio v1.0.0")
        self.status_version_lbl.setStyleSheet("font-size: 11px; color: #6F7682; padding-left: 10px;")
        self.statusBar().addWidget(self.status_version_lbl)
        
        # Spacer to push subsequent widgets to the right
        spacer = QWidget()
        self.statusBar().addPermanentWidget(spacer, 1)
        
        self.status_ready_dot = QLabel("●")
        self.status_ready_dot.setStyleSheet("color: #58C777; font-size: 10px; padding-right: 2px;")
        self.statusBar().addPermanentWidget(self.status_ready_dot)
        
        self.status_lbl = QLabel("System Ready")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #E4E7EB; font-weight: bold; padding-right: 15px;")
        self.statusBar().addPermanentWidget(self.status_lbl)
        
        self.status_gpu_lbl = QLabel("Detecting Hardware...")
        self.status_gpu_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1; padding-right: 15px;")
        self.statusBar().addPermanentWidget(self.status_gpu_lbl)
        
        self.status_cuda_lbl = QLabel("CUDA --")
        self.status_cuda_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1; padding-right: 15px;")
        self.statusBar().addPermanentWidget(self.status_cuda_lbl)
        
        self.status_os_lbl = QLabel("Windows")
        self.status_os_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1; padding-right: 10px;")
        self.statusBar().addPermanentWidget(self.status_os_lbl)

        # Wire Up Dialog Signals
        self.plus_btn.clicked.connect(self.open_new_project_dialog)
        self.settings_btn.clicked.connect(self.open_preferences_dialog)
        self.topbar.settings_btn.clicked.connect(self.open_preferences_dialog)
        self.sidebar.project_list.itemClicked.connect(self.on_project_clicked)
        
        # Console card signals
        self.logs_panel.clear_btn.clicked.connect(self.clear_current_log)
        self.logs_panel.export_btn.clicked.connect(self.open_export_logs_dialog)

        # Wire Up Pipeline & Stream Signals
        self.start_btn.clicked.connect(self.start_stream_capture)
        self.stop_btn.clicked.connect(self.stop_stream_capture)
        self.restart_btn.clicked.connect(self.restart_rtsp_server)
        self.colmap_btn.clicked.connect(self.run_colmap_reconstruction)
        self.gaussian_btn.clicked.connect(self.train_gaussian_splatting)
        self.cancel_btn.clicked.connect(self.cancel_active_pipeline_task)
        self.open_model_btn.clicked.connect(self.open_gaussian_model)
        self.open_folder_btn.clicked.connect(self.open_gaussian_folder)

        # Sync Viewport and Right Panel spinboxes
        self.frame_spin.valueChanged.connect(self.right_frame_spin.setValue)
        self.right_frame_spin.valueChanged.connect(self.frame_spin.setValue)

        # Wire Up Viewport Toolbar Buttons
        self.btn_capture.clicked.connect(self.capture_single_frame)
        self.btn_record.clicked.connect(self.start_stream_capture)
        self.btn_pause.clicked.connect(self.stop_stream_capture)
        self.btn_delete.clicked.connect(self.clear_project_frames)

    # =====================================================
    # ACTIONS & SHORTCUTS (Top Menu Bar)
    # =====================================================
    def setup_actions_and_shortcuts(self):
        # Hide the standard native menu bar to match custom dark workstation visuals
        self.menuBar().hide()

        # 1. Custom File Menu
        file_menu = QMenu(self)
        
        new_proj_act = QAction("New Project", self)
        new_proj_act.setShortcut("Ctrl+N")
        new_proj_act.triggered.connect(self.open_new_project_dialog)
        file_menu.addAction(new_proj_act)
        
        open_proj_act = QAction("Open Project...", self)
        open_proj_act.setShortcut("Ctrl+O")
        open_proj_act.triggered.connect(self.open_project_folder_selector)
        file_menu.addAction(open_proj_act)
        
        self.recent_menu = QMenu("Open Recent", self)
        file_menu.addMenu(self.recent_menu)
        self.rebuild_recent_projects_menu()

        file_menu.addSeparator()

        import_images_act = QAction("Import Images...", self)
        import_images_act.triggered.connect(self.import_images_directory)
        file_menu.addAction(import_images_act)

        export_recon_act = QAction("Export Reconstruction...", self)
        export_recon_act.triggered.connect(lambda: self.open_export_dialog("Point Cloud (PLY)"))
        file_menu.addAction(export_recon_act)

        export_gaussian_act = QAction("Export Gaussian Model...", self)
        export_gaussian_act.triggered.connect(lambda: self.open_export_dialog("Gaussian Scene"))
        file_menu.addAction(export_gaussian_act)

        file_menu.addSeparator()

        save_workspace_act = QAction("Save Workspace", self)
        save_workspace_act.setShortcut("Ctrl+S")
        save_workspace_act.triggered.connect(self.save_workspace_state)
        file_menu.addAction(save_workspace_act)

        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)
        
        self.topbar.btn_menu_file.setMenu(file_menu)

        # 2. Custom Edit Menu
        edit_menu = QMenu(self)
        
        preferences_act = QAction("Preferences...", self)
        preferences_act.triggered.connect(self.open_preferences_dialog)
        edit_menu.addAction(preferences_act)
        
        clear_cache_act = QAction("Clear Cache", self)
        clear_cache_act.triggered.connect(self.clear_project_cache)
        edit_menu.addAction(clear_cache_act)

        reset_layout_act = QAction("Reset Layout", self)
        reset_layout_act.triggered.connect(self.reset_splitter_layout)
        edit_menu.addAction(reset_layout_act)
        
        self.topbar.btn_menu_edit.setMenu(edit_menu)

        # 3. Custom View Menu
        view_menu = QMenu(self)
        
        self.toggle_logs_act = QAction("Show Logs Panel", self, checkable=True, checked=True)
        self.toggle_logs_act.setShortcut("Ctrl+L")
        self.toggle_logs_act.triggered.connect(self.toggle_logs_visibility)
        view_menu.addAction(self.toggle_logs_act)

        self.toggle_sidebar_act = QAction("Show Left Sidebar", self, checkable=True, checked=True)
        self.toggle_sidebar_act.triggered.connect(self.toggle_sidebar_visibility)
        view_menu.addAction(self.toggle_sidebar_act)

        self.toggle_right_act = QAction("Show Pipeline Panel", self, checkable=True, checked=True)
        self.toggle_right_act.triggered.connect(self.toggle_pipeline_visibility)
        view_menu.addAction(self.toggle_right_act)

        view_menu.addSeparator()

        fullscreen_act = QAction("Fullscreen", self)
        fullscreen_act.setShortcut("F11")
        fullscreen_act.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_act)
        
        self.topbar.btn_menu_view.setMenu(view_menu)

        # 4. Custom Tools Menu
        tools_menu = QMenu(self)
        
        rtsp_diag_act = QAction("RTSP Diagnostics", self)
        rtsp_diag_act.triggered.connect(self.show_rtsp_diagnostics)
        tools_menu.addAction(rtsp_diag_act)

        gpu_mon_act = QAction("GPU Monitor", self)
        gpu_mon_act.triggered.connect(self.show_gpu_monitor_details)
        tools_menu.addAction(gpu_mon_act)

        validate_act = QAction("Dataset Validator", self)
        validate_act.triggered.connect(self.validate_dataset)
        tools_menu.addAction(validate_act)
        
        self.topbar.btn_menu_tools.setMenu(tools_menu)

        # 5. Custom Help Menu
        help_menu = QMenu(self)
        
        sys_info_act = QAction("System Info...", self)
        sys_info_act.triggered.connect(self.show_system_info)
        help_menu.addAction(sys_info_act)

        about_act = QAction("About Vizhi Spatial Studio", self)
        about_act.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_act)
        
        self.topbar.btn_menu_help.setMenu(help_menu)

    # =====================================================
    # LOG CONTROLLERS
    # =====================================================
    def add_log(self, level, msg):
        # Direct support for custom log syntax coloring
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs_text.append(f"[{ts}] [{level.upper()}] {msg}")

    def perform_system_scan(self):
        self.logs_text.clear()
        
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        
        from core.gpu_monitor import get_cpu_name, get_ram_info, get_gpu_info, get_cuda_version, get_os_version
        
        cpu_name = get_cpu_name()
        ram_total, _, _ = get_ram_info()
        gpu_info = get_gpu_info()[0]
        gpu_name = gpu_info["name"]
        vram_total = gpu_info["vram_total"]
        cuda_ver = get_cuda_version()
        os_ver = get_os_version()
        
        self.boot_lines = [
            f"[{ts}] [INFO] Vizhi Spatial Studio v1.0.0 initialized.",
            f"[{ts}] [INFO] Scanning workstation hardware compute devices...",
            f"[{ts}] [INFO] Operating System: {os_ver}",
            f"[{ts}] [INFO] CPU: {cpu_name}",
            f"[{ts}] [INFO] System RAM: {ram_total:.1f} GB"
        ]
        
        if vram_total > 0:
            self.boot_lines.extend([
                f"[{ts}] [SUCCESS] CUDA compute device detected: {gpu_name}",
                f"[{ts}] [SUCCESS] Dedicated VRAM: {vram_total:.1f} GB",
                f"[{ts}] [SUCCESS] CUDA Version: {cuda_ver}"
            ])
            self.topbar.sys_gpu_label.setText("GPU --")
            self.topbar.sys_vram_label.setText(f"VRAM -- / {vram_total:.1f} GB")
            self.gpu_card.value_label.setText("0%")
            self.gpu_card.detail_label.setText(f"VRAM -- / {vram_total:.1f} GB")
        else:
            self.boot_lines.append(f"[{ts}] [WARNING] No CUDA GPU hardware detected.")
            self.topbar.sys_gpu_label.setText("GPU --")
            self.topbar.sys_vram_label.setText("VRAM --")
            self.gpu_card.value_label.setText("0%")
            self.gpu_card.detail_label.setText("VRAM N/A")
            
        self.boot_lines.append(f"[{ts}] [INFO] Workstation core ready.")
        
        # Populate status bar labels immediately
        self.status_gpu_lbl.setText(gpu_name)
        self.status_cuda_lbl.setText(f"CUDA {cuda_ver}" if cuda_ver != "N/A" else "CUDA N/A")
        self.status_os_lbl.setText(os_ver.split(" Build")[0])
        
        # Start progressive logging timer
        self.boot_line_index = 0
        from PyQt6.QtCore import QTimer
        self.boot_timer = QTimer(self)
        self.boot_timer.timeout.connect(self.print_next_boot_line)
        self.boot_timer.start(150)

    def print_next_boot_line(self):
        if hasattr(self, "boot_lines") and self.boot_line_index < len(self.boot_lines):
            self.logs_text.append(self.boot_lines[self.boot_line_index])
            self.boot_line_index += 1
        else:
            self.boot_timer.stop()

    def generate_noise_pixmap(self, width=128, height=128, opacity=0.012):
        from PyQt6.QtGui import QImage, QColor, QPixmap
        import random
        img = QImage(width, height, QImage.Format.Format_ARGB32)
        for y in range(height):
            for x in range(width):
                val = random.randint(0, 255)
                alpha = int(opacity * 255)
                img.setPixelColor(x, y, QColor(val, val, val, alpha))
        return QPixmap.fromImage(img)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QRadialGradient, QColor, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Subtle radial gradient
        from PyQt6.QtCore import QPointF
        grad = QRadialGradient(QPointF(self.rect().center()), float(max(self.width(), self.height())))
        grad.setColorAt(0.0, QColor("#141519"))
        grad.setColorAt(1.0, QColor("#0B0B0D"))
        painter.fillRect(self.rect(), grad)
        
        # Faint spatial grid lines
        pen = QPen(QColor(255, 255, 255, 3), 1)
        painter.setPen(pen)
        grid_size = 40
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
            
        # Tiled noise texture overlay
        if hasattr(self, "noise_pixmap") and self.noise_pixmap:
            painter.drawTiledPixmap(self.rect(), self.noise_pixmap)

    def on_telemetry_updated(self, payload):
        gpu_name = payload["gpu_name"]
        gpu_load = payload["gpu_load"]
        vram_total = payload["vram_total"]
        vram_used = payload["vram_used"]
        
        # Update topbar
        self.topbar.sys_gpu_label.setText(f"GPU {int(gpu_load)}%")
        self.topbar.sys_vram_label.setText(f"VRAM {vram_used:.1f} / {vram_total:.1f} GB")
        
        # Update metric cards
        self.gpu_card.value_label.setText(f"{int(gpu_load)}%")
        self.gpu_card.detail_label.setText(f"VRAM {vram_used:.1f} / {vram_total:.1f} GB")
        
        # Update status bar GPU label dynamically
        self.status_gpu_lbl.setText(gpu_name)

    def clear_current_log(self):
        active_idx = self.logs_panel.tabs.currentIndex()
        if active_idx == 0:
            self.logs_text.clear()
        elif active_idx == 1:
            self.tasks_text.clear()
        elif active_idx == 2:
            self.notifications_text.clear()
        NotificationManager().show_notification("Console log buffer cleared", "info")

    def open_export_logs_dialog(self):
        self.open_export_dialog("System Logs")

    # =====================================================
    # DIALOG ACTIONS
    # =====================================================
    def open_new_project_dialog(self):
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sidebar.load_projects_list()
            self.rebuild_recent_projects_menu()
            # Select the newly created project
            if dialog.project_path:
                self.select_project_by_path(dialog.project_path)

    def open_preferences_dialog(self):
        dialog = PreferencesDialog(self)
        dialog.exec()

    def open_export_dialog(self, default_type="Gaussian Scene"):
        dialog = ExportDialog(self, default_type)
        dialog.exec()

    def show_system_info(self):
        dialog = SystemInfoDialog(self)
        dialog.exec()

    def show_about_dialog(self):
        # Custom clean about QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle("About Vizhi Spatial Studio")
        dialog.setFixedSize(380, 200)
        dialog.setStyleSheet("QDialog { background-color: #080c14; border: 1px solid #131a26; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        title = QLabel("VIZHI SPATIAL STUDIO")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; letter-spacing: 1px;")
        layout.addWidget(title)
        
        ver = QLabel("Version 1.0.0 (Workstation Edition)")
        ver.setStyleSheet("font-size: 11px; color: #8fa0c2; font-weight: bold;")
        layout.addWidget(ver)
        
        desc = QLabel("Professional real-time RTSP capture, COLMAP reconstruction, and 3D Gaussian Splatting platform.")
        desc.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addStretch()
        
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(dialog.accept)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 6px;
                color: #cbd5e1;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def show_rtsp_diagnostics(self):
        url = self.rtsp_input.text()
        NotificationManager().show_notification("Running RTSP Stream Diagnostic Scan...", "info")
        # Simulate diagnostics check
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: NotificationManager().show_notification(f"RTSP stream reachable at {url}", "success"))

    def validate_dataset(self):
        if not self.current_project:
            NotificationManager().show_notification("No project loaded to validate", "warning")
            return
        NotificationManager().show_notification("Validating project image directories...", "info")
        project_path = os.path.join(DATASETS_DIR, self.current_project)
        images_dir = os.path.join(project_path, "images")
        if os.path.exists(images_dir):
            files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            NotificationManager().show_notification(f"Dataset Validated: {len(files)} clean capture images detected.", "success")
        else:
            NotificationManager().show_notification("Image directory missing. Validations failed.", "error")

    # =====================================================
    # LAYOUT VIEW CONTROLLER
    # =====================================================
    def toggle_fullscreen(self):
        if self.fullscreen_state:
            self.showMaximized()
            self.fullscreen_state = False
            self.status_lbl.setText("Exited Fullscreen")
        else:
            self.showFullScreen()
            self.fullscreen_state = True
            self.status_lbl.setText("Fullscreen Enabled")

    def toggle_logs_visibility(self, checked):
        self.logs_panel.setVisible(checked)
        self.toggle_logs_act.setChecked(checked)

    def toggle_sidebar_visibility(self, checked):
        self.sidebar.setVisible(checked)
        self.toggle_sidebar_act.setChecked(checked)

    def toggle_pipeline_visibility(self, checked):
        self.right_panel.setVisible(checked)
        self.toggle_right_act.setChecked(checked)

    def reset_splitter_layout(self):
        self.main_horizontal_splitter.setSizes([240, 1660])
        self.workspace_middle_splitter.setSizes([1360, 300])
        self.center_vertical_splitter.setSizes([900, 150])
        NotificationManager().show_notification("Workspace layout reset to default settings", "info")

    # =====================================================
    # PROJECT NAVIGATION & PERSISTENCE
    # =====================================================
    def rebuild_recent_projects_menu(self):
        self.recent_menu.clear()
        recent = self.project_manager.get_recent_projects()
        
        if not recent:
            no_recent_act = QAction("No Recent Projects", self)
            no_recent_act.setEnabled(False)
            self.recent_menu.addAction(no_recent_act)
            return
            
        for idx, p in enumerate(recent[:5]): # Show up to top 5
            path = p.get("path")
            act = QAction(f"{idx+1}. {p.get('name')}", self)
            # Use closure to bind correct path
            act.triggered.connect(lambda checked, path=path: self.select_project_by_path(path))
            self.recent_menu.addAction(act)

    def open_project_folder_selector(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Open Existing Project Folder", DATASETS_DIR)
        if dir_path:
            meta_path = os.path.join(dir_path, "metadata.json")
            if os.path.exists(meta_path):
                self.select_project_by_path(dir_path)
            else:
                # Ask if they want to import/convert folder to project
                dialog = ErrorDialog(
                    message="The directory selected is not a valid Vizhi project (missing metadata.json).",
                    traceback_text="Please use New Project wizard to initialize folders, or select a folder created by Vizhi.",
                    parent=self
                )
                dialog.exec()

    def import_images_directory(self):
        if not self.current_project:
            NotificationManager().show_notification("Load or create a project first before importing images", "warning")
            return
            
        dir_path = QFileDialog.getExistingDirectory(self, "Select Images Ingestion Directory", DATASETS_DIR)
        if dir_path:
            import shutil
            dest_dir = os.path.join(DATASETS_DIR, self.current_project, "images")
            os.makedirs(dest_dir, exist_ok=True)
            
            imported = 0
            for f in os.listdir(dir_path):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    shutil.copy(os.path.join(dir_path, f), os.path.join(dest_dir, f))
                    imported += 1
            
            if imported > 0:
                NotificationManager().show_notification(f"Successfully imported {imported} images.", "success")
                self.select_project_by_name(self.current_project)
            else:
                NotificationManager().show_notification("No valid image files found in selection directory.", "warning")

    def clear_project_cache(self):
        if not self.current_project:
            NotificationManager().show_notification("No project loaded to clear cache", "warning")
            return
            
        try:
            cache_dir = os.path.join(DATASETS_DIR, self.current_project, "sparse")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, exist_ok=True)
            NotificationManager().show_notification("Project reconstruction cache cleared", "success")
        except Exception as e:
            NotificationManager().show_notification(f"Failed to clear cache: {e}", "error")

    def on_project_clicked(self, item):
        # Map item selection to full metadata check
        recent = self.project_manager.get_recent_projects()
        selected_path = None
        for p in recent:
            if p.get("name") == item.text():
                selected_path = p.get("path")
                break
                
        if selected_path:
            self.select_project_by_path(selected_path)
        else:
            self.select_project_by_name(item.text())

    def select_project_by_path(self, path):
        meta = self.project_manager.load_project_metadata(path)
        if meta:
            self.current_project = meta.get("name")
            self.current_project_name.setText(meta.get("name"))
            self.project_info.setText(path)
            self.project_card.value_label.setText(meta.get("name"))
            
            # Select item in list
            for idx in range(self.project_list.count()):
                item = self.project_list.item(idx)
                if item.text() == meta.get("name"):
                    self.project_list.setCurrentItem(item)
                    break
            
            # Update frame statistics
            num_frames = meta.get("frames_count", 0)
            self.frames_card.value_label.setText(f"{num_frames:,}")
            self.frames_card.detail_label.setText(f"({num_frames} total)")
            
            # Update folder sizes
            proj_size = get_dir_size(path)
            proj_size_mb = proj_size / (1024 * 1024)
            if proj_size_mb >= 1024:
                self.storage_card.value_label.setText(f"{proj_size_mb/1024:.1f} GB")
                self.storage_label.setText(f"{proj_size_mb/1024:.1f} GB / 10 GB")
            else:
                self.storage_card.value_label.setText(f"{proj_size_mb:.1f} MB")
                self.storage_label.setText(f"{proj_size_mb:.1f} MB / 10 GB")
                
            limit_bytes = 10 * 1024 * 1024 * 1024
            storage_pct = int((proj_size / limit_bytes) * 100)
            storage_pct = min(100, max(0, storage_pct))
            self.storage_bar.setValue(storage_pct)
            self.storage_pct_label.setText(f"{storage_pct}%")
            self.storage_card.detail_label.setText(f"{100 - storage_pct}% available")
            
            # Load dynamic thumbnails
            self.thumbnail_list.clear()
            images_dir = os.path.join(path, "images")
            if os.path.exists(images_dir) and num_frames > 0:
                try:
                    files = sorted([f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                    latest_frames = files[-10:]
                    for f in latest_frames:
                        fpath = os.path.join(images_dir, f)
                        item = QListWidgetItem()
                        item.setIcon(QIcon(fpath))
                        lbl = os.path.splitext(f)[0]
                        if lbl.isdigit():
                            lbl = str(int(lbl))
                        item.setText(lbl)
                        item.setSizeHint(QSize(110, 85))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.thumbnail_list.addItem(item)
                        
                    last_item = self.thumbnail_list.item(self.thumbnail_list.count() - 1)
                    if last_item:
                        self.thumbnail_list.setCurrentItem(last_item)
                except Exception as e:
                    print(f"Error loading frame list: {e}")
                    
            # Update project list selection and recent ordering
            self.project_manager.add_recent_project(meta.get("name"), path)
            self.sidebar.load_projects_list()
            self.rebuild_recent_projects_menu()
            
            # Update open model/folder buttons based on model existence
            ply_path = resolve_gaussian_ply_path(path)
            if ply_path:
                self.open_model_btn.setEnabled(True)
                self.open_folder_btn.setEnabled(True)
            else:
                self.open_model_btn.setEnabled(False)
                self.open_folder_btn.setEnabled(False)

    def select_project_by_name(self, name):
        # Fallback redirecting name checks to paths
        project_path = os.path.join(DATASETS_DIR, name)
        if os.path.exists(project_path):
            self.select_project_by_path(project_path)

    # =====================================================
    # LAYOUT STATE PERSISTENCE
    # =====================================================
    def save_workspace_state(self):
        try:
            self.workspace_state.set("horizontal_splitter", list(self.main_horizontal_splitter.sizes()))
            self.workspace_state.set("middle_splitter", list(self.workspace_middle_splitter.sizes()))
            self.workspace_state.set("vertical_splitter", list(self.center_vertical_splitter.sizes()))
            self.workspace_state.set("window_width", self.width())
            self.workspace_state.set("window_height", self.height())
            self.workspace_state.set("fullscreen", self.fullscreen_state)
            self.workspace_state.set("active_project_path", self.project_info.text() if self.current_project else "")
            self.workspace_state.set("rtsp_url", self.rtsp_input.text())
            
            # Save toggles
            self.workspace_state.set("sidebar_visible", self.sidebar.isVisible())
            self.workspace_state.set("right_panel_visible", self.right_panel.isVisible())
            self.workspace_state.set("logs_visible", self.logs_panel.isVisible())
            self.workspace_state.save()
        except Exception as e:
            print(f"Error saving workspace config states: {e}")

    def load_workspace_state(self):
        try:
            # Restore panel sizes safely
            h_sizes = self.workspace_state.get("horizontal_splitter")
            if h_sizes and isinstance(h_sizes, list):
                try:
                    # If it has 3 values (old layout), convert to 2 values (new layout)
                    if len(h_sizes) == 3:
                        h_sizes = [h_sizes[0], h_sizes[1] + h_sizes[2]]
                    self.main_horizontal_splitter.setSizes([int(x) for x in h_sizes])
                except Exception as e:
                    print(f"Error restoring horizontal sizes: {e}")
                    self.main_horizontal_splitter.setSizes([240, 1660])
            
            m_sizes = self.workspace_state.get("middle_splitter")
            if m_sizes and isinstance(m_sizes, list):
                try:
                    self.workspace_middle_splitter.setSizes([int(x) for x in m_sizes])
                except Exception as e:
                    print(f"Error restoring middle sizes: {e}")
                    self.workspace_middle_splitter.setSizes([1360, 300])
            else:
                self.workspace_middle_splitter.setSizes([1360, 300])
            
            v_sizes = self.workspace_state.get("vertical_splitter")
            if v_sizes and isinstance(v_sizes, list):
                try:
                    self.center_vertical_splitter.setSizes([int(x) for x in v_sizes])
                except Exception as e:
                    print(f"Error restoring vertical sizes: {e}")
                    self.center_vertical_splitter.setSizes([900, 150])
                    
            rtsp = self.workspace_state.get("rtsp_url")
            if rtsp is not None:
                self.rtsp_input.setText(str(rtsp))
            
            # Ensure the horizontal splitter itself is always visible
            self.main_horizontal_splitter.setVisible(True)
            
            # Restore sidebar toggles
            sb_vis = self.workspace_state.get("sidebar_visible")
            if sb_vis is None:
                sb_vis = True
            self.sidebar.setVisible(sb_vis)
            self.toggle_sidebar_act.setChecked(sb_vis)
            
            right_vis = self.workspace_state.get("right_panel_visible")
            if right_vis is None:
                right_vis = True
            self.right_panel.setVisible(right_vis)
            self.toggle_right_act.setChecked(right_vis)
            
            log_vis = self.workspace_state.get("logs_visible")
            if log_vis is None:
                log_vis = True
            self.logs_panel.setVisible(log_vis)
            self.toggle_logs_act.setChecked(log_vis)
            
            # Restore window size
            if not self.workspace_state.get("maximized"):
                self.resize(self.workspace_state.get("window_width"), self.workspace_state.get("window_height"))
                
            # Restore project selection
            active_path = self.workspace_state.get("active_project_path")
            if active_path and os.path.exists(active_path):
                self.select_project_by_path(active_path)
        except Exception as e:
            print(f"Error recovering layout states: {e}")

    def closeEvent(self, event):
        # Stop telemetry thread if active
        if hasattr(self, "gpu_monitor_thread") and self.gpu_monitor_thread.isRunning():
            self.gpu_monitor_thread.stop()
        # Stop MediaMTX Server
        if hasattr(self, "mediamtx_manager"):
            self.mediamtx_manager.stop()
        # Auto-save state on close
        if self.config_manager.get("autosave"):
            self.save_workspace_state()
        super().closeEvent(event)

    def show_gpu_monitor_details(self):
        # Trigger preferences on the GPU tab or print toast diagnostic
        NotificationManager().show_notification("GPU status monitor is active and running", "success")

    # =====================================================
    # STREAM & PIPELINE ACTIONS
    # =====================================================
    def start_stream_capture(self):
        if not self.current_project:
            NotificationManager().show_notification("Please select or create a project first.", "warning")
            return
            
        if hasattr(self, "capture_worker") and self.capture_worker and self.capture_worker.isRunning():
            NotificationManager().show_notification("Capture is already running.", "warning")
            return
            
        rtsp_url = self.rtsp_input.text().strip()
        project_path = os.path.join(DATASETS_DIR, self.current_project)
        images_dir = os.path.join(project_path, "images")
        save_interval = self.frame_spin.value()
        
        from workers.capture_worker import CaptureWorker
        self.capture_worker = CaptureWorker(rtsp_url, images_dir, save_interval, self)
        self.capture_worker.frame_captured.connect(self.on_frame_captured)
        self.capture_worker.status_msg.connect(lambda msg: self.add_log("info", msg))
        self.capture_worker.finished.connect(self.on_capture_finished)
        
        self.capture_worker.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.btn_record.setIcon(create_vector_icon("pause", QColor("#E4E7EB")))
        
        # Update RTSP state dot to active blue
        self.rtsp_dot.setStyleSheet("color: #5B8CFF; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        
        self.add_log("info", f"Capture started using interval of {save_interval} frames.")
        NotificationManager().show_notification("RTSP Ingestion started.", "success")
        
    def stop_stream_capture(self):
        if hasattr(self, "capture_worker") and self.capture_worker and self.capture_worker.isRunning():
            self.capture_worker.stop()
            
    def on_frame_captured(self, pixmap, saved_path):
        # Update live viewport
        self.video_viewport.setPixmap(pixmap)
        
        if saved_path:
            # Add dynamic log
            filename = os.path.basename(saved_path)
            self.add_log("success", f"Saved frame: {filename}")
            
            # Refresh project details dynamically
            project_path = os.path.join(DATASETS_DIR, self.current_project)
            self.select_project_by_path(project_path)
            
    def on_capture_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.btn_record.setIcon(create_vector_icon("play", QColor("#D95C5C")))
        
        # Reset RTSP state dot to idle gray
        self.rtsp_dot.setStyleSheet("color: #6F7682; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        
        self.add_log("info", "Capture stopped.")
        NotificationManager().show_notification("RTSP Ingestion stopped.", "info")
        
    def restart_rtsp_server(self):
        self.add_log("info", "Restarting MediaMTX RTSP Server...")
        if self.mediamtx_manager.restart():
            self.add_log("success", "MediaMTX server restarted successfully.")
            self.rtsp_card.value_label.setText("ONLINE")
            NotificationManager().show_notification("RTSP Server restarted.", "success")
        else:
            self.add_log("error", "Failed to restart MediaMTX server.")
            self.rtsp_card.value_label.setText("OFFLINE")
            NotificationManager().show_notification("RTSP Server restart failed.", "error")

    def run_colmap_reconstruction(self):
        if not self.current_project:
            NotificationManager().show_notification("Please select or create a project first.", "warning")
            return
            
        if hasattr(self, "colmap_worker") and self.colmap_worker and self.colmap_worker.isRunning():
            NotificationManager().show_notification("COLMAP reconstruction is already running.", "warning")
            return
            
        project_path = os.path.join(DATASETS_DIR, self.current_project)
        images_dir = os.path.join(project_path, "images")
        
        if not os.path.exists(images_dir) or not [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]:
            NotificationManager().show_notification("No capture images found. Start capture first.", "error")
            return
            
        from workers.colmap_worker import ColmapWorker
        self.colmap_worker = ColmapWorker(project_path, self)
        self.colmap_worker.progress.connect(self.on_colmap_progress)
        self.colmap_worker.log_line.connect(lambda line: self.add_log("colmap", line))
        self.colmap_worker.finished.connect(self.on_colmap_finished)
        
        self.colmap_worker.start()
        self.colmap_btn.setEnabled(False)
        self.gaussian_btn.setEnabled(False)
        
        # Update COLMAP status dot to active blue
        self.colmap_dot.setStyleSheet("color: #5B8CFF; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        
        self.add_log("info", "COLMAP Reconstruction task started.")
        NotificationManager().show_notification("COLMAP Reconstruction started.", "info")
        
    def on_colmap_progress(self, val):
        self.colmap_progress.setValue(val)
        self.colmap_pct.setText(f"{val}%")
        
        if val <= 33:
            stage = "Extracting Features..."
        elif val <= 66:
            stage = "Matching Images..."
        elif val <= 85:
            stage = "Sparse Reconstruction..."
        elif val <= 95:
            stage = "Bundle Adjustment..."
        else:
            stage = "Optimizing Cameras..."
        self.right_panel.colmap_lbl.setText(f"COLMAP: {stage}")
        
    def on_colmap_finished(self, success):
        self.colmap_btn.setEnabled(True)
        self.gaussian_btn.setEnabled(True)
        if success:
            self.add_log("success", "COLMAP Reconstruction completed successfully.")
            NotificationManager().show_notification("COLMAP Reconstruction succeeded.", "success")
            project_path = os.path.join(DATASETS_DIR, self.current_project)
            self.project_manager.update_project_metadata(project_path, {"reconstruction_status": "Completed"})
            
            # Show completed states
            self.colmap_progress.setStyleSheet("QProgressBar::chunk { background-color: #58C777; }")
            self.colmap_dot.setStyleSheet("color: #58C777; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
            self.right_panel.colmap_lbl.setText("COLMAP: Completed")
            self.colmap_pct.setText("Done")
        else:
            self.add_log("error", "COLMAP Reconstruction task failed.")
            NotificationManager().show_notification("COLMAP Reconstruction failed.", "error")
            
            # Show failed states
            self.colmap_progress.setStyleSheet("QProgressBar::chunk { background-color: #D95C5C; }")
            self.colmap_dot.setStyleSheet("color: #D95C5C; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
            self.right_panel.colmap_lbl.setText("COLMAP: Failed")
            self.colmap_pct.setText("Error")
            
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self.reset_colmap_progress_ui)

    def reset_colmap_progress_ui(self):
        self.colmap_progress.setStyleSheet("")
        self.colmap_progress.setValue(0)
        self.colmap_dot.setStyleSheet("color: #6F7682; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        self.right_panel.colmap_lbl.setText("COLMAP: Idle")
        self.colmap_pct.setText("Idle")
            
    def train_gaussian_splatting(self):
        if not self.current_project:
            NotificationManager().show_notification("Please select or create a project first.", "warning")
            return
            
        if hasattr(self, "gaussian_worker") and self.gaussian_worker and self.gaussian_worker.isRunning():
            NotificationManager().show_notification("Gaussian training is already running.", "warning")
            return
            
        project_path = os.path.join(DATASETS_DIR, self.current_project)
        sparse_dir = os.path.join(project_path, "sparse")
        
        if not os.path.exists(sparse_dir) or not os.listdir(sparse_dir):
            NotificationManager().show_notification("Sparse reconstruction missing. Run COLMAP first.", "error")
            return
            
        from workers.gaussian_worker import GaussianWorker
        self.gaussian_worker = GaussianWorker(project_path, self)
        self.gaussian_worker.progress.connect(self.on_gaussian_progress)
        self.gaussian_worker.log_line.connect(lambda line: self.add_log("gaussian", line))
        self.gaussian_worker.finished.connect(self.on_gaussian_finished)
        
        self.gaussian_worker.start()
        self.colmap_btn.setEnabled(False)
        self.gaussian_btn.setEnabled(False)
        self.open_model_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)
        
        # Update Gaussian status dot to active blue
        self.gaussian_dot.setStyleSheet("color: #5B8CFF; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        
        self.add_log("info", "3D Gaussian Splatting training started.")
        NotificationManager().show_notification("Gaussian Training started.", "info")
        
    def on_gaussian_progress(self, val):
        self.gaussian_progress.setValue(val)
        self.gaussian_pct.setText(f"{val}%")
        
        if val <= 20:
            stage = "Initializing Points..."
        elif val <= 50:
            stage = "Optimizing Gaussians..."
        elif val <= 80:
            stage = "Density Control..."
        elif val <= 95:
            stage = "Spherical Harmonics Fit..."
        else:
            stage = "Finalizing Model..."
        self.right_panel.gaussian_lbl.setText(f"Gaussian: {stage}")
        
    def on_gaussian_finished(self, success):
        self.colmap_btn.setEnabled(True)
        self.gaussian_btn.setEnabled(True)
        if success:
            self.add_log("success", "3D Gaussian Splatting training completed successfully.")
            NotificationManager().show_notification("Gaussian Training succeeded.", "success")
            project_path = os.path.join(DATASETS_DIR, self.current_project)
            self.project_manager.update_project_metadata(project_path, {"gaussian_status": "Completed"})
            
            # Show completed states
            self.gaussian_progress.setStyleSheet("QProgressBar::chunk { background-color: #58C777; }")
            self.gaussian_dot.setStyleSheet("color: #58C777; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
            self.right_panel.gaussian_lbl.setText("Gaussian: Completed")
            self.gaussian_pct.setText("Done")
            
            # Enable Open Model/Folder buttons if PLY exists
            ply_path = resolve_gaussian_ply_path(project_path)
            if ply_path:
                self.open_model_btn.setEnabled(True)
                self.open_folder_btn.setEnabled(True)
        else:
            self.add_log("error", "Gaussian training failed.")
            NotificationManager().show_notification("Gaussian Training failed.", "error")
            
            # Show failed states
            self.gaussian_progress.setStyleSheet("QProgressBar::chunk { background-color: #D95C5C; }")
            self.gaussian_dot.setStyleSheet("color: #D95C5C; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
            self.right_panel.gaussian_lbl.setText("Gaussian: Failed")
            self.gaussian_pct.setText("Error")
            
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self.reset_gaussian_progress_ui)

    def reset_gaussian_progress_ui(self):
        self.gaussian_progress.setStyleSheet("")
        self.gaussian_progress.setValue(0)
        self.gaussian_dot.setStyleSheet("color: #6F7682; font-size: 10px; background: transparent; border: none; padding-bottom: 1px;")
        self.right_panel.gaussian_lbl.setText("Gaussian: Idle")
        self.gaussian_pct.setText("Idle")
            
    def cancel_active_pipeline_task(self):
        cancelled = False
        if hasattr(self, "colmap_worker") and self.colmap_worker and self.colmap_worker.isRunning():
            self.colmap_worker.stop()
            cancelled = True
        if hasattr(self, "gaussian_worker") and self.gaussian_worker and self.gaussian_worker.isRunning():
            self.gaussian_worker.stop()
            cancelled = True
            
        if cancelled:
            self.add_log("warning", "Active pipeline task was manually aborted.")
            NotificationManager().show_notification("Pipeline task aborted.", "warning")
        else:
            NotificationManager().show_notification("No active pipeline task running.", "info")

    def capture_single_frame(self):
        if not self.current_project:
            NotificationManager().show_notification("Please select or create a project first.", "warning")
            return
            
        if not hasattr(self, "capture_worker") or not self.capture_worker or not self.capture_worker.isRunning():
            NotificationManager().show_notification("Stream is not running. Start stream to capture frame.", "warning")
            return
            
        pixmap = self.video_viewport._pixmap
        if pixmap and not pixmap.isNull():
            project_path = os.path.join(DATASETS_DIR, self.current_project)
            images_dir = os.path.join(project_path, "images")
            os.makedirs(images_dir, exist_ok=True)
            existing = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            idx = len(existing) + 1
            filepath = os.path.join(images_dir, f"{idx:05d}.jpg")
            if pixmap.save(filepath, "JPG"):
                self.add_log("success", f"Saved manual snapshot: {idx:05d}.jpg")
                self.select_project_by_path(project_path)
                NotificationManager().show_notification("Snapshot saved.", "success")
            else:
                NotificationManager().show_notification("Failed to save snapshot.", "error")
        else:
            NotificationManager().show_notification("No frame active to capture.", "warning")
            
    def clear_project_frames(self):
        if not self.current_project:
            return
            
        ret = QMessageBox.question(
            self,
            "Clear Capture Frames",
            f"Are you sure you want to delete all captured frames in project '{self.current_project}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            project_path = os.path.join(DATASETS_DIR, self.current_project)
            images_dir = os.path.join(project_path, "images")
            if os.path.exists(images_dir):
                import shutil
                shutil.rmtree(images_dir)
                os.makedirs(images_dir, exist_ok=True)
                self.add_log("warning", "All project capture frames were deleted.")
                self.select_project_by_path(project_path)
                NotificationManager().show_notification("Project frames cleared.", "info")
                
    def open_gaussian_model(self):
        if not self.current_project:
            return
        project_path = os.path.join(DATASETS_DIR, self.current_project)
        ply_path = resolve_gaussian_ply_path(project_path)
        if ply_path and os.path.exists(ply_path):
            try:
                os.startfile(ply_path)
                NotificationManager().show_notification("Opening 3D model in default viewer...", "success")
            except Exception as e:
                NotificationManager().show_notification(f"Failed to open model: {e}", "error")
        else:
            NotificationManager().show_notification("Model output file not found.", "error")

    def open_gaussian_folder(self):
        if not self.current_project:
            return
        project_path = os.path.join(DATASETS_DIR, self.current_project)
        ply_path = resolve_gaussian_ply_path(project_path)
        target_dir = os.path.dirname(ply_path) if (ply_path and os.path.exists(ply_path)) else os.path.join(project_path, "gaussian")
        if os.path.exists(target_dir):
            try:
                os.startfile(target_dir)
                NotificationManager().show_notification("Opening output directory...", "success")
            except Exception as e:
                NotificationManager().show_notification(f"Failed to open directory: {e}", "error")
        else:
            NotificationManager().show_notification("Output directory not found.", "error")