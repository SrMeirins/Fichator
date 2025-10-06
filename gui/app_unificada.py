# gui/app_unificada.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QDateEdit, QHBoxLayout, QDialog, QFormLayout,
    QDialogButtonBox, QTimeEdit, QComboBox, QMessageBox, QSpacerItem, 
    QSizePolicy, QGroupBox, QGridLayout, QHeaderView, QFrame, QProgressBar 
)
from PySide6.QtCore import QDate, QTime, Signal, Qt, QTimer
from PySide6.QtGui import QColor, QFont
# CORREGIDO: Se importan explícitamente date y time para resolver errores de tipado de Pylance
from datetime import datetime, timedelta, date, time 
from typing import List, Tuple, Dict, Any, Optional

# Model Imports - CORREGIDO: Nombres de funciones en inglés
from models.fichaje import (
    register_punch, get_daily_punches, calculate_worked_hours, 
    register_manual_punch, delete_punch_by_date_type, PUNCH_TYPES
)
from models.logica_contador import calculate_accumulated_time_and_state 

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from db import connect_db # CORREGIDO: conectar -> connect_db

# Base class for signal emission - CORREGIDO: Nombre de señal
class SignalEmitter(QWidget):
    """Base class to centralize the signal for punch changes across widgets."""
    punches_changed = Signal()  

# CORREGIDO: Nombre de clase
class UnifiedPunchApp(SignalEmitter):
    """
    Main widget combining punch control, weekly table, summary, and chart.
    Manages the application state and UI updates.
    """
    WEEKLY_GOAL_HOURS: float = 37.5 

    def __init__(self):
        super().__init__()
        
        # State Initialization - CORREGIDO: Nombres de atributos
        self.worked_time_seconds: float = 0.0
        self.last_punch_time: Optional[datetime] = None
        
        # Timer Configuration (1-second interval)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_counter)
        
        self.main_layout = QVBoxLayout(self)

        # 1. UI Construction - CORREGIDO: Nombres de métodos
        self._create_quick_punch_section()
        self.main_layout.addLayout(self.quick_punch_layout)
        self.main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)) 
        
        self._create_weekly_summary_section()
        self.main_layout.addLayout(self.weekly_summary_layout)
        self.main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)) 

        self._create_history_section()
        self.main_layout.addWidget(self.history_group)
        
        self._create_chart_section()
        self.main_layout.addWidget(self.canvas)

        # 2. Initial Data Load - CORREGIDO: Nombres de métodos
        self._load_initial_counter_state() 
        self.update_table()
        self.update_quick_history()
        self.update_button_state()
        self.update_weekly_summary() 

    # ----------------------------------------
    # --- UI Creation Methods ---
    # ----------------------------------------

    def _create_quick_punch_section(self):
        """Creates the quick punch buttons and daily status cards."""
        self.quick_punch_layout = QGridLayout()
        
        # A) Daily Info Card (Worked Hours)
        info_frame = QFrame()
        info_frame.setObjectName("InfoCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        self.date_label = QLabel(f"Today: {QDate.currentDate().toString('yyyy-MM-dd')}")
        self.date_label.setObjectName("LabelDate")
        
        self.hours_title_label = QLabel("Hours worked today:")
        self.hours_label = QLabel("0.00 h")
        self.hours_label.setObjectName("LabelHours") 
        
        info_layout.addWidget(self.date_label, alignment=Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.hours_title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.hours_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.quick_punch_layout.addWidget(info_frame, 0, 0, 1, 1) 
        
        # B) Punch Buttons Card
        buttons_frame = QFrame()
        buttons_frame.setObjectName("InfoCard")
        buttons_layout = QVBoxLayout(buttons_frame)
        
        self.punch_buttons: Dict[str, QPushButton] = {}
        for punch_type in PUNCH_TYPES: 
            btn = QPushButton(punch_type)
            # CORREGIDO: Llamada al método renombrado
            btn.clicked.connect(lambda checked, t=punch_type: self._execute_punch(t))
            # Set object name for QSS styling
            btn.setObjectName(f"{punch_type.replace(' ', '')}Btn") 
            self.punch_buttons[punch_type] = btn
            buttons_layout.addWidget(btn)
        
        self.quick_punch_layout.addWidget(buttons_frame, 0, 1, 1, 1)
        
        # C) Daily History Card 
        history_frame = QFrame()
        history_frame.setObjectName("InfoCard")
        history_layout = QVBoxLayout(history_frame)
        
        self.history_title_label = QLabel("Today's Punches:")
        self.history_title_label.setObjectName("LabelHistoryTitle")
        
        self.history_content_label = QLabel("No punches yet.")
        self.history_content_label.setObjectName("LabelHistoryContent") 
        
        history_layout.addWidget(self.history_title_label)
        history_layout.addWidget(self.history_content_label)
        
        self.quick_punch_layout.addWidget(history_frame, 0, 2, 1, 1)
        
        # Column stretch configuration
        self.quick_punch_layout.setColumnStretch(0, 3) 
        self.quick_punch_layout.setColumnStretch(1, 2) 
        self.quick_punch_layout.setColumnStretch(2, 5) 


    def _create_weekly_summary_section(self):
        """Creates the weekly progress bar."""
        self.weekly_summary_layout = QVBoxLayout()
        
        self.weekly_summary_label = QLabel("")
        self.weekly_summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        # Set progress range based on weekly goal in "tenths of an hour" for precision
        self.progress_bar.setRange(0, int(self.WEEKLY_GOAL_HOURS * 100)) 
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.weekly_summary_layout.addWidget(self.weekly_summary_label)
        self.weekly_summary_layout.addWidget(self.progress_bar)


    def _create_history_section(self):
        """Creates the date controls and the weekly punch table."""
        self.history_group = QGroupBox("Weekly History and Manual Edit")
        
        vbox = QVBoxLayout(self.history_group)

        # Date controls and action buttons
        control_layout = QHBoxLayout()
        
        date_label = QLabel("Week starting:")
        self.date_selector = QDateEdit(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        # CORREGIDO: Llamada al método renombrado
        self.date_selector.dateChanged.connect(self.update_table)
        
        # CORREGIDO: Nombres de botones y llamadas a métodos
        self.manual_punch_btn = QPushButton("Manual Punch")
        self.manual_punch_btn.clicked.connect(self._show_manual_punch_dialog)

        self.delete_punch_btn = QPushButton("Delete Punch")
        self.delete_punch_btn.clicked.connect(self._delete_selected_punch)
        
        control_layout.addWidget(date_label)
        control_layout.addWidget(self.date_selector)
        control_layout.addStretch() 
        control_layout.addWidget(self.manual_punch_btn)
        control_layout.addWidget(self.delete_punch_btn)
        vbox.addLayout(control_layout)

        # Punch Table 
        self.punch_table = QTableWidget()
        self.punch_table.setColumnCount(2 + len(PUNCH_TYPES)) 
        self.punch_table.setHorizontalHeaderLabels(["Day", "Date"] + PUNCH_TYPES) 
        # Connect itemChanged for manual inline editing
        # CORREGIDO: Llamada al método renombrado
        self.punch_table.itemChanged.connect(self._edit_punch_from_table)
        
        # Configuration for table appearance and sizing
        self.punch_table.setAlternatingRowColors(True)
        self.punch_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        self.punch_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        vbox.addWidget(self.punch_table)
        
        
    def _create_chart_section(self):
        """Creates the Matplotlib chart canvas."""
        self.figure = Figure(facecolor="#2c3e50") 
        self.canvas = FigureCanvas(self.figure)
        
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumHeight(200)


    # ----------------------------------------
    # --- Real-Time Counter Logic ---
    # ----------------------------------------

    def _load_initial_counter_state(self):
        """
        Calculates initial worked time using logica_contador and starts/stops the QTimer.
        """
        today_str: str = QDate.currentDate().toString("yyyy-MM-dd")
        # CORREGIDO: Nombre de función
        daily_punches: List[Tuple[str, str]] = get_daily_punches(today_str)
        
        # CORREGIDO: Nombre de función
        try:
            total_seconds, is_active, start_time_dt = calculate_accumulated_time_and_state(daily_punches)
            
            self.worked_time_seconds = total_seconds
            self.last_punch_time = start_time_dt
            self._update_hours_label(total_seconds)

            if is_active:
                self.timer.start(1000)
            else:
                self.timer.stop()
                
        except Exception as e:
            # Fallback for errors in counter logic or DB read
            print(f"Error initializing counter state: {e}")
            # El modelo calculate_worked_hours toma la lista de fichajes y devuelve un timedelta
            hours_td = calculate_worked_hours(daily_punches)
            self.worked_time_seconds = hours_td.total_seconds()
            self._update_hours_label(self.worked_time_seconds)
            self.timer.stop()


    def _update_counter(self):
        """Timer slot: increments the counter and updates the UI label."""
        # Se recalcula cada segundo para mantener la precisión y sincronización con el reloj del sistema
        if self.last_punch_time:
            punches = get_daily_punches(datetime.now().strftime("%Y-%m-%d"))
            total_seconds, is_active, start_dt = calculate_accumulated_time_and_state(punches)
            
            self.worked_time_seconds = total_seconds
            self._update_hours_label(self.worked_time_seconds)
            
        else:
            self._update_hours_label(self.worked_time_seconds)
            self.timer.stop()
            
        # Actualizar fecha y hora en el label de fecha
        self.date_label.setText(datetime.now().strftime("%A, %d %B %Y | %H:%M:%S")) 


    def _update_hours_label(self, seconds: float):
        """Formats and updates the daily worked hours label."""
        total_time = timedelta(seconds=int(seconds))
        hours_str: str = str(total_time).split('.')[0] # Formato HH:MM:SS
        self.hours_label.setText(hours_str)


    # ----------------------------------------
    # --- Core Application Logic Methods ---
    # ----------------------------------------
    
    def _execute_punch(self, punch_type: str):
        """Handles the quick punch button actions."""
        try:
            # CORREGIDO: Nombre de función
            register_punch(punch_type)
            
            # Refresh all UI elements - CORREGIDO: Nombres de métodos y señales
            self._load_initial_counter_state() 
            self.update_table()
            self.update_quick_history()
            self.update_button_state() 
            self.update_weekly_summary() 
            self.punches_changed.emit() 
            
        except Exception as e:
            QMessageBox.critical(self, "Punch Error", str(e))

    def update_quick_history(self):
        """Updates the label showing today's punches."""
        today_str: str = QDate.currentDate().toString("yyyy-MM-dd")
        # CORREGIDO: Nombre de función
        punches: List[Tuple[str, str]] = get_daily_punches(today_str)
        
        if punches:
            # Format time to HH:MM for cleaner display
            text = "\n".join([f"  • {punch_type}: {time_str[:5]}" for punch_type, time_str in punches]) 
        else:
            text = "No punches yet."
        self.history_content_label.setText(text) 

    def update_button_state(self):
        """Controls which quick punch buttons are enabled/disabled based on flow logic."""
        today_str: str = QDate.currentDate().toString("yyyy-MM-dd")
        # CORREGIDO: Nombre de función
        punches_list: List[str] = [punch_type for punch_type, _ in get_daily_punches(today_str)]
        punched: Dict[str, bool] = {p: True for p in punches_list}

        # 1. Disable all buttons first
        for btn in self.punch_buttons.values():
            btn.setEnabled(False)

        # 2. Apply enablement logic based on sequence
        
        # A. Start Shift
        if not punched.get("Entrada"):
            self.punch_buttons["Entrada"].setEnabled(True)
            return

        # B. Shift Ended
        if punched.get("Fin jornada"):
            return # All remain disabled
        
        # C. Active Shift
        
        # C1. Currently on Lunch Break? ('Ir a comer' YES, 'Salida comida' NO)
        if punched.get("Ir a comer") and not punched.get("Salida comida"):
            # Only 'Salida comida' is allowed
            self.punch_buttons["Salida comida"].setEnabled(True)
        
        # C2. Currently Working? (No break or break ended)
        elif (not punched.get("Ir a comer")) or (punched.get("Salida comida")):
            # 'Ir a comer' OR 'Fin jornada' are allowed
            self.punch_buttons["Ir a comer"].setEnabled(True)
            self.punch_buttons["Fin jornada"].setEnabled(True)
            
    
    # --- Table and Editing Methods ---

    def update_table(self):
        """Updates the table with weekly punches (Mon-Fri) and recalculates totals."""
        qdate: QDate = self.date_selector.date()
        date_obj: date = datetime(qdate.year(), qdate.month(), qdate.day()).date()
        # Calculate the start of the week (Monday)
        start_of_week: date = date_obj - timedelta(days=date_obj.weekday()) 
        
        self.punch_table.blockSignals(True)
        self.punch_table.setRowCount(5) 

        self.daily_hours: List[float] = []
        day_names: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri"]

        # Font configuration for table data
        font_data = QFont()
        font_data.setPointSize(10)
        font_day_name = QFont()
        font_day_name.setBold(True)

        for i in range(5): # Iterate Monday to Friday
            day: date = start_of_week + timedelta(days=i)
            day_str: str = day.strftime("%Y-%m-%d")
            # CORREGIDO: Nombre de función
            punches: List[Tuple[str, str]] = get_daily_punches(day_str)
            punch_dict: Dict[str, str] = {punch_type: time_str for punch_type, time_str in punches}

            # Column 0: Day of the week
            item_day_name = QTableWidgetItem(day_names[i])
            item_day_name.setFont(font_day_name) 
            self.punch_table.setItem(i, 0, item_day_name)
            
            # Column 1: Date
            item_date = QTableWidgetItem(day_str)
            self.punch_table.setItem(i, 1, item_date)

            # Columns 2 onwards: Punches (Hours)
            for j, punch_type in enumerate(PUNCH_TYPES):
                hour_str: str = punch_dict.get(punch_type, "")
                if hour_str and len(hour_str) > 5:
                    hour_str = hour_str[:5] # Use HH:MM format
                    
                item = QTableWidgetItem(hour_str)
                item.setFont(font_data) 
                
                # Apply alignment and QSS colors
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
                self.punch_table.setItem(i, j+2, item)

            # CORREGIDO: calculate_worked_hours toma la lista de fichajes y devuelve un float
            worked_hours_td: timedelta = calculate_worked_hours(punches)
            worked_hours: float = worked_hours_td.total_seconds() / 3600
            self.daily_hours.append(worked_hours)

        # Final table layout adjustments
        self.punch_table.resizeColumnsToContents() 
        self.punch_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        self.punch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        
        for i in range(2, self.punch_table.columnCount()):
            self.punch_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch) 
            
        self.punch_table.blockSignals(False)
        # CORREGIDO: Nombre de métodos
        self.update_chart()
        self.update_weekly_summary() 
        
    def update_weekly_summary(self):
        """Calculates weekly hours and updates the progress bar."""
        qdate: QDate = self.date_selector.date()
        date_obj: date = datetime(qdate.year(), qdate.month(), qdate.day()).date()
        start_of_week: date = date_obj - timedelta(days=date_obj.weekday()) 
        
        total_hours: float = 0.0
        # Recalculate based on current table week selection
        for i in range(5):
            day: date = start_of_week + timedelta(days=i)
            day_str: str = day.strftime("%Y-%m-%d")
            # CORREGIDO: calculate_worked_hours toma la lista de fichajes
            punches: List[Tuple[str, str]] = get_daily_punches(day_str)
            total_hours += calculate_worked_hours(punches).total_seconds() / 3600
            
        # Value for progress bar (multiplied by 100 for range set previously)
        progress_value: int = int(total_hours * 100) 
        self.progress_bar.setValue(progress_value)
        
        hours_remaining: float = max(0, self.WEEKLY_GOAL_HOURS - total_hours)
        percentage: float = (total_hours / self.WEEKLY_GOAL_HOURS) * 100 if self.WEEKLY_GOAL_HOURS > 0 else 0.0
        
        progress_text: str = f"Progress: {total_hours:.2f} h of {self.WEEKLY_GOAL_HOURS:.1f} h ({percentage:.0f}%)"
        
        # Update summary text
        if hours_remaining > 0 and percentage < 100:
            remaining_text: str = f"{hours_remaining:.2f} hours remaining until goal."
        elif total_hours == 0:
            remaining_text: str = f"Must reach {self.WEEKLY_GOAL_HOURS:.1f} hours this week."
        else:
            remaining_text: str = "Weekly goal completed! 🎉"
            
        self.progress_bar.setFormat(progress_text)
        self.weekly_summary_label.setText(remaining_text)

    def update_chart(self):
        """Generates the aesthetic weekly bar chart for the 5 working days."""
        self.figure.clear()
        
        # Set subplot background color to match QGroupBox/Card background
        ax = self.figure.add_subplot(111, facecolor="#34495e") 

        day_labels: List[str] = []
        for i in range(self.punch_table.rowCount()):
            item = self.punch_table.item(i, 0)
            # CORREGIDO: Comprobación explícita para evitar Error 8 de Pylance
            if item:
                 day_labels.append(item.text())
        
        # Color coding logic for bars based on daily goal
        daily_goal: float = self.WEEKLY_GOAL_HOURS / 5 
        colors: List[str] = []
        for h in self.daily_hours: 
            if daily_goal > 0:
                pct: float = h / daily_goal
                if pct >= 1.0:
                    colors.append("#2ecc71") # Green (Goal reached)
                elif pct >= 0.8:
                    colors.append("#f1c40f") # Yellow (Close to goal)
                else:
                    colors.append("#e74c3c") # Red (Below goal)
            else:
                colors.append("#4e6d8a") # Default gray

        ax.bar(day_labels, self.daily_hours, color=colors, edgecolor="#ecf0f1", linewidth=0.5)

        # Add horizontal goal line
        ax.axhline(daily_goal, color="#1abc9c", linestyle="-.", alpha=0.9, 
                   label=f"Daily Goal ({daily_goal:.1f} h)")

        total_weekly: float = sum(self.daily_hours)
        pct_total: float = (total_weekly / self.WEEKLY_GOAL_HOURS) * 100 if self.WEEKLY_GOAL_HOURS > 0 else 0.0
        
        title_text: str = f"Worked Hours (Mon-Fri) | Total: {total_weekly:.2f} h ({pct_total:.0f}%)"
        ax.set_title(title_text, color="#ecf0f1", fontsize=14, pad=15) 

        # Configure axis appearance for dark theme
        ax.set_ylabel("Hours", color="#ecf0f1")
        ax.set_xlabel("Day", color="#ecf0f1")
        ax.tick_params(colors="#ecf0f1", labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#ecf0f1")
            
        ax.grid(axis='y', linestyle=':', alpha=0.4, color="#7f8c8d")
        ax.set_axisbelow(True)
        
        self.figure.tight_layout(pad=3.0) 
        self.figure.autofmt_xdate(rotation=45) 

        ax.legend(facecolor="#34495e", edgecolor="#ecf0f1", labelcolor="#ecf0f1", fontsize=9)
        self.canvas.draw()
        
    def _show_manual_punch_dialog(self):
        """Displays the dialog for manual punch entry/update."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manual Punch Entry")
        layout = QFormLayout(dialog)

        # 1. Day selection (based on the current week displayed in the table)
        day_combo = QComboBox()
        for i in range(self.punch_table.rowCount()): 
            item_date = self.punch_table.item(i, 1)
            if item_date:
                day_combo.addItem(item_date.text())
        layout.addRow("Date:", day_combo)

        # 2. Punch type selection
        type_combo = QComboBox()
        for punch_type in PUNCH_TYPES:
            type_combo.addItem(punch_type)
        layout.addRow("Punch Type:", type_combo)

        # 3. Time selection (HH:MM)
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(QTime.currentTime())
        layout.addRow("Time:", time_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            selected_date: str = day_combo.currentText()
            selected_type: str = type_combo.currentText()
            selected_time: str = time_edit.time().toString("HH:mm")
            # CORREGIDO: Nombre de método
            self._save_manual_punch(selected_date, selected_type, selected_time)

    def _save_manual_punch(self, date_str: str, punch_type: str, time_str_hhmm: str):
        """Registers a manual punch and refreshes the UI."""
        try:
            # CORREGIDO: Nombre de función
            register_manual_punch(date_str, punch_type, time_str_hhmm)
            
            # Full UI refresh after successful DB operation - CORREGIDO: Nombres de métodos y señales
            self.update_table()
            self.update_quick_history() 
            self._load_initial_counter_state()
            self.update_weekly_summary()
            self.update_button_state() 
            self.punches_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Manual Punch Error", str(e))
            return

    def _edit_punch_from_table(self, item: QTableWidgetItem):
        """Handles manual inline editing in the table cells."""
        # Only process changes in punch columns (index >= 2)
        if item is None or item.column() < 2: 
            return 
            
        self.punch_table.blockSignals(True) # Prevent recursion
        
        item_date: Optional[QTableWidgetItem] = self.punch_table.item(item.row(), 1) 
        if item_date is None:
            self.punch_table.blockSignals(False)
            return
            
        date_str: str = item_date.text()
        # Map column index to punch type
        punch_type: str = PUNCH_TYPES[item.column() - 2] 
        hour_str: str = item.text().strip() 

        if not hour_str:
             # If the user deletes the text, perform a logical deletion
             # CORREGIDO: Nombre de método
             self._delete_punch_logical(date_str, punch_type)
        else:
            try:
                # Validate HH:MM format
                datetime.strptime(hour_str, "%H:%M") 
                # CORREGIDO: Nombre de función
                register_manual_punch(date_str, punch_type, hour_str)
                
                # Full UI refresh after successful DB operation - CORREGIDO: Nombres de métodos y señales
                self.update_table() 
                self.update_quick_history()
                self._load_initial_counter_state()
                self.update_weekly_summary()
                self.update_button_state() 
                self.punches_changed.emit()
                
            except ValueError:
                QMessageBox.warning(self, "Invalid Format", "Time must be in HH:MM format.")
                self.update_table() # Revert table content on error
            except Exception as e:
                QMessageBox.warning(self, "Update Error", str(e))
                self.update_table() # Revert table content on error

        self.punch_table.blockSignals(False)

    def _delete_punch_logical(self, date_str: str, punch_type: str):
        """Executes the DB deletion and refreshes UI components."""
        try:
            # CORREGIDO: Usa la función del modelo delete_punch_by_date_type
            delete_punch_by_date_type(date_str, punch_type)
            
            # Full UI refresh after successful DB operation - CORREGIDO: Nombres de métodos y señales
            self.update_table()
            self.update_quick_history()
            self._load_initial_counter_state()
            self.update_weekly_summary()
            self.update_button_state() 
            self.punches_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Could not delete punch: {e}")

    def _delete_selected_punch(self):
        """Handles the 'Delete Punch' button action based on cell selection."""
        item: Optional[QTableWidgetItem] = self.punch_table.currentItem()
        # Check if an item is selected and it's a punch column (index >= 2) with content
        if not item or item.column() < 2 or not item.text(): 
            QMessageBox.warning(self, "Delete Punch", "Select a valid time cell to delete.")
            return
            
        item_date: Optional[QTableWidgetItem] = self.punch_table.item(item.row(), 1) 
        if not item_date:
            return
            
        date_str: str = item_date.text()
        punch_type: str = PUNCH_TYPES[item.column() - 2] 

        reply = QMessageBox.question(self, "Confirm Deletion", f"Confirm deletion of {punch_type} on {date_str}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # CORREGIDO: Nombre de método
            self._delete_punch_logical(date_str, punch_type)