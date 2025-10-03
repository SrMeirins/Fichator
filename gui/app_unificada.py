# gui/app_unificada.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QDateEdit, QHBoxLayout, QDialog, QFormLayout,
    QDialogButtonBox, QTimeEdit, QComboBox, QMessageBox, QSpacerItem, 
    QSizePolicy, QGroupBox, QGridLayout, QHeaderView, QFrame, QProgressBar 
)
from PySide6.QtCore import QDate, QTime, Signal, Qt, QTimer
from PySide6.QtGui import QColor, QFont
from datetime import datetime, timedelta

from models.fichaje import (
    registrar_fichaje, obtener_fichajes_del_dia, calcular_horas_trabajadas, 
    registrar_fichaje_manual, TIPOS_FICHAJE
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Clase base para la señal
class SignalEmitter(QWidget):
    fichajes_cambiados = Signal()  

class AppUnificada(SignalEmitter):
    OBJETIVO_SEMANAL = 37.5 

    def __init__(self):
        super().__init__()
        
        # Inicialización del contador
        self.tiempo_trabajado_segundos = 0
        self.ultimo_fichaje_hora = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_contador)
        
        self.layout_principal = QVBoxLayout(self)

        # 1. Sección de Fichaje y Resumen Diario (Tarjetas)
        self._crear_seccion_fichaje_rapido()
        self.layout_principal.addLayout(self.fichaje_rapido_layout)
        self.layout_principal.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)) 
        
        # 2. Sección de Resumen Semanal (Barra de progreso)
        self._crear_seccion_resumen_semanal()
        self.layout_principal.addLayout(self.resumen_semanal_layout)
        self.layout_principal.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)) 

        # 3. Historial y Edición Manual
        self._crear_seccion_historial()
        self.layout_principal.addWidget(self.historial_group)
        
        # 4. Gráfico
        self._crear_seccion_grafico()
        self.layout_principal.addWidget(self.canvas)

        # Inicialización de datos
        self.actualizar_tabla()
        self.actualizar_historial_rapido()
        self.actualizar_estado_botones()
        self.actualizar_resumen_semanal() 
        self._inicializar_contador_estado() 

    def _crear_seccion_fichaje_rapido(self):
        """Crea los botones y etiquetas de estado con diseño de tarjetas."""
        self.fichaje_rapido_layout = QGridLayout()
        
        # A) Tarjeta de Info del Día (Horas Trabajadas Hoy)
        info_frame = QFrame()
        info_frame.setObjectName("InfoCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        self.label_fecha = QLabel(f"Hoy: {QDate.currentDate().toString('yyyy-MM-dd')}")
        self.label_fecha.setObjectName("LabelFecha")
        self.label_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_fecha.setStyleSheet("font-weight: bold; margin-bottom: 5px; font-size: 14pt;")
        
        self.label_horas_title = QLabel("Horas trabajadas hoy:")
        self.label_horas_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_horas_title.setStyleSheet("font-size: 12pt; margin-top: 5px;")
        self.label_horas = QLabel("0.00 h")
        self.label_horas.setObjectName("LabelHoras") 
        self.label_horas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_layout.addWidget(self.label_fecha)
        info_layout.addWidget(self.label_horas_title)
        info_layout.addWidget(self.label_horas)
        
        self.fichaje_rapido_layout.addWidget(info_frame, 0, 0, 1, 1) 
        
        # B) Botones de Fichaje 
        botones_frame = QFrame()
        botones_frame.setObjectName("InfoCard")
        botones_layout = QVBoxLayout(botones_frame)
        botones_layout.setContentsMargins(5, 5, 5, 5) 
        
        self.botones = {}
        boton_names = {
            "Entrada": "EntradaBtn",
            "Ir a comer": "IrAComerBtn",
            "Salida comida": "SalidaComidaBtn",
            "Fin jornada": "FinJornadaBtn"
        }
        
        for tipo in TIPOS_FICHAJE: 
            btn = QPushButton(tipo)
            btn.setObjectName(boton_names.get(tipo, "GenericBtn")) 
            btn.clicked.connect(lambda checked, t=tipo: self.fichar(t))
            self.botones[tipo] = btn
            botones_layout.addWidget(btn)
        
        self.fichaje_rapido_layout.addWidget(botones_frame, 0, 1, 1, 1)
        
        # C) Tarjeta de Historial del Día 
        historial_frame = QFrame()
        historial_frame.setObjectName("InfoCard")
        historial_layout = QVBoxLayout(historial_frame)
        
        self.label_historial_title = QLabel("Fichajes del día:")
        self.label_historial_title.setStyleSheet("font-weight: bold; margin-bottom: 5px; font-size: 12pt;")
        
        self.label_historial_content = QLabel("No hay fichajes todavía.")
        self.label_historial_content.setObjectName("LabelHistorialContent") 
        
        historial_layout.addWidget(self.label_historial_title)
        historial_layout.addWidget(self.label_historial_content)
        
        self.fichaje_rapido_layout.addWidget(historial_frame, 0, 2, 1, 1)
        
        self.fichaje_rapido_layout.setColumnStretch(0, 3) 
        self.fichaje_rapido_layout.setColumnStretch(1, 2) 
        self.fichaje_rapido_layout.setColumnStretch(2, 5) 


    def _crear_seccion_resumen_semanal(self):
        """Crea la barra de progreso semanal."""
        self.resumen_semanal_layout = QVBoxLayout()
        
        self.label_resumen_semanal = QLabel("")
        self.label_resumen_semanal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_resumen_semanal.setStyleSheet("font-size: 12pt; font-weight: bold; color: #ecf0f1; margin-bottom: 5px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, int(self.OBJETIVO_SEMANAL * 100)) 
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.resumen_semanal_layout.addWidget(self.label_resumen_semanal)
        self.resumen_semanal_layout.addWidget(self.progress_bar)


    def _crear_seccion_historial(self):
        """Crea los controles de fecha y la tabla."""
        self.historial_group = QGroupBox("Historial y Edición Manual")
        
        vbox = QVBoxLayout(self.historial_group)

        # Controles de fecha y botones de acción
        control_layout = QHBoxLayout()
        
        label = QLabel("Fecha de la semana:")
        self.date_selector = QDateEdit(QDate.currentDate())
        self.date_selector.setCalendarPopup(True)
        self.date_selector.dateChanged.connect(self.actualizar_tabla)
        
        self.btn_manual = QPushButton("Entrada manual")
        self.btn_manual.clicked.connect(self.entrada_manual_dialog)

        self.btn_eliminar = QPushButton("Eliminar fichaje")
        self.btn_eliminar.clicked.connect(self.eliminar_fichaje)
        
        control_layout.addWidget(label)
        control_layout.addWidget(self.date_selector)
        control_layout.addStretch() 
        control_layout.addWidget(self.btn_manual)
        control_layout.addWidget(self.btn_eliminar)
        vbox.addLayout(control_layout)

        # Tabla de fichajes 
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2 + len(TIPOS_FICHAJE)) 
        self.tabla.setHorizontalHeaderLabels(["Día Sem", "Día"] + TIPOS_FICHAJE) 
        self.tabla.itemChanged.connect(self.editar_fichaje_desde_tabla)
        self.tabla.setAlternatingRowColors(True)
        
        # Aumentamos la prioridad de crecimiento vertical de la tabla para darle más espacio
        self.tabla.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        
        self.tabla.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        vbox.addWidget(self.tabla)
        
        
    def _crear_seccion_grafico(self):
        """Crea el gráfico de Matplotlib."""
        self.figure = Figure(facecolor="#2c3e50") 
        self.canvas = FigureCanvas(self.figure)
        
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumHeight(200) # Reducimos la altura mínima para darle más a la tabla


    # ----------------------------------------
    # --- Lógica del Contador en Tiempo Real ---
    # ----------------------------------------

    def _inicializar_contador_estado(self):
        """
        Calcula el tiempo trabajado al inicio y define si el contador debe estar activo.
        """
        hoy = QDate.currentDate().toString("yyyy-MM-dd")
        fichajes = obtener_fichajes_del_dia(hoy)
        
        if not fichajes:
            self.tiempo_trabajado_segundos = 0
            self.timer.stop()
            self._actualizar_label_horas(0)
            return

        try:
            from models.logica_contador import calcular_tiempo_acumulado_y_estado 
            
            total_segundos, esta_activo, ultimo_fichaje_dt = calcular_tiempo_acumulado_y_estado(fichajes)
            
            self.tiempo_trabajado_segundos = total_segundos
            self.ultimo_fichaje_hora = ultimo_fichaje_dt
            self._actualizar_label_horas(total_segundos)

            if esta_activo:
                self.timer.start(1000)
            else:
                self.timer.stop()
                
        except ImportError:
            # Fallback si no se encuentra models.logica_contador
            horas = calcular_horas_trabajadas(hoy)
            self.tiempo_trabajado_segundos = int(horas * 3600)
            self._actualizar_label_horas(self.tiempo_trabajado_segundos)
            self.timer.stop()
            
        except Exception:
            # Fallback en caso de otro error
            horas = calcular_horas_trabajadas(hoy)
            self.tiempo_trabajado_segundos = int(horas * 3600)
            self._actualizar_label_horas(self.tiempo_trabajado_segundos)
            self.timer.stop()


    def _actualizar_contador(self):
        """Aumenta el contador cada segundo y actualiza el label."""
        if self.timer.isActive():
            self.tiempo_trabajado_segundos += 1
            self._actualizar_label_horas(self.tiempo_trabajado_segundos)


    def _actualizar_label_horas(self, segundos):
        """Formatea y actualiza el label de horas."""
        horas_float = segundos / 3600
        horas_str = f"{horas_float:.2f} h"
        self.label_horas.setText(horas_str)


    # ----------------------------------------
    # --- Métodos de Lógica Central ---
    # ----------------------------------------
    
    def fichar(self, tipo):
        try:
            registrar_fichaje(tipo)
            
            self._inicializar_contador_estado() 
            self.actualizar_tabla()
            self.actualizar_historial_rapido()
            self.actualizar_estado_botones() 
            self.actualizar_resumen_semanal() 
            self.fichajes_cambiados.emit() 
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Fichaje", str(e))

    def actualizar_historial_rapido(self):
        hoy = QDate.currentDate().toString("yyyy-MM-dd")
        fichajes = obtener_fichajes_del_dia(hoy)
        
        if fichajes:
            texto = "\n".join([f"  • {tipo}: {hora[:5]}" for tipo, hora in fichajes]) 
        else:
            texto = "No hay fichajes todavía."
        self.label_historial_content.setText(texto) 

    def actualizar_estado_botones(self):
        """Controla qué botones de fichaje deben estar habilitados/deshabilitados."""
        hoy = QDate.currentDate().toString("yyyy-MM-dd")
        fichajes = [tipo for tipo, _ in obtener_fichajes_del_dia(hoy)]
        fichados = {f: True for f in fichajes}

        # 1. Deshabilitar TODOS los botones primero (aplica el estilo grisáceo)
        for btn in self.botones.values():
            btn.setEnabled(False)

        # 2. Aplicar la lógica de habilitación
        
        # A. Fichaje de Entrada:
        if not fichados.get("Entrada"):
            self.botones["Entrada"].setEnabled(True)
            return

        # B. Jornada Finalizada:
        if fichados.get("Fin jornada"):
            # Si hay "Fin jornada", todos permanecen DESACTIVADOS.
            return 
        
        # C. Jornada Activa (Tras Entrada y antes de Fin jornada):
        
        # C1. ¿Estamos en Pausa para comer? (Ir a comer SÍ, Salida comida NO)
        if fichados.get("Ir a comer") and not fichados.get("Salida comida"):
            # Solo se puede fichar la vuelta de comer
            self.botones["Salida comida"].setEnabled(True)
        
        # C2. ¿Estamos trabajando? (Ir a comer NO, o Salida comida SÍ)
        elif (not fichados.get("Ir a comer")) or (fichados.get("Salida comida")):
            # Se puede salir a comer O terminar la jornada
            self.botones["Ir a comer"].setEnabled(True)
            self.botones["Fin jornada"].setEnabled(True)
            
    
    # --- Métodos de la Tabla y Edición ---

    def actualizar_tabla(self):
        """
        Actualiza la tabla con los fichajes de la semana (Lun-Vie), con fuente pequeña para las horas.
        """
        qdate = self.date_selector.date()
        fecha = datetime(qdate.year(), qdate.month(), qdate.day()).date()
        inicio_semana = fecha - timedelta(days=fecha.weekday()) 
        
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(5) 

        self.horas_dia = []
        
        dias_semana_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie"]

        # Ajuste de tamaño de fuente para que las horas quepan mejor
        font_data = QFont()
        font_data.setPointSize(14) 
        
        font_day_name = QFont()
        font_day_name.setBold(True)

        for i in range(5): 
            dia = inicio_semana + timedelta(days=i)
            dia_str = dia.strftime("%Y-%m-%d")
            fichajes = obtener_fichajes_del_dia(dia_str)
            fich_dict = {tipo: hora for tipo, hora in fichajes}

            # Columna 0: Día de la semana
            item_dia_sem = QTableWidgetItem(dias_semana_nombres[i])
            item_dia_sem.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
            item_dia_sem.setFont(font_day_name) 
            self.tabla.setItem(i, 0, item_dia_sem)
            
            # Columna 1: Fecha (Día)
            item_dia = QTableWidgetItem(dia_str)
            item_dia.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
            self.tabla.setItem(i, 1, item_dia)

            # Columnas 2 en adelante: Fichajes (Horas)
            for j, tipo in enumerate(TIPOS_FICHAJE):
                hora_str = fich_dict.get(tipo, "")
                if hora_str and len(hora_str) > 5:
                    hora_str = hora_str[:5]
                    
                item = QTableWidgetItem(hora_str)
                item.setForeground(QColor("#ecf0f1"))
                
                item.setFont(font_data) 
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
                
                self.tabla.setItem(i, j+2, item)

            horas_trabajo = calcular_horas_trabajadas(dia_str)
            self.horas_dia.append(horas_trabajo)

        # Ajuste de cabecera
        self.tabla.resizeColumnsToContents() 
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        
        for i in range(2, self.tabla.columnCount()):
            self.tabla.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch) 
            
        self.tabla.blockSignals(False)
        self.actualizar_grafico()
        self.actualizar_resumen_semanal() 
        
    def actualizar_resumen_semanal(self):
        """Calcula las horas semanales trabajadas y actualiza la barra de progreso."""
        qdate = self.date_selector.date()
        fecha = datetime(qdate.year(), qdate.month(), qdate.day()).date()
        inicio_semana = fecha - timedelta(days=fecha.weekday()) 
        
        total_horas = 0
        for i in range(5):
            dia = inicio_semana + timedelta(days=i)
            dia_str = dia.strftime("%Y-%m-%d")
            total_horas += calcular_horas_trabajadas(dia_str)
            
        valor_progreso = int(total_horas * 100) 
        self.progress_bar.setValue(valor_progreso)
        
        horas_restantes = max(0, self.OBJETIVO_SEMANAL - total_horas)
        porcentaje = (total_horas / self.OBJETIVO_SEMANAL) * 100 if self.OBJETIVO_SEMANAL > 0 else 0
        
        texto_progreso = f"Progreso: {total_horas:.2f} h de {self.OBJETIVO_SEMANAL:.1f} h ({porcentaje:.0f}%)"
        
        if horas_restantes > 0 and porcentaje < 100:
            texto_restante = f"Te quedan {horas_restantes:.2f} horas hasta el objetivo."
        elif total_horas == 0:
            texto_restante = f"Debes alcanzar {self.OBJETIVO_SEMANAL:.1f} horas esta semana."
        else:
            texto_restante = "¡Objetivo semanal completado! 🎉"
            
        self.progress_bar.setFormat(texto_progreso)
        self.label_resumen_semanal.setText(texto_restante)

    def actualizar_grafico(self):
        """Genera gráfico semanal estético, solo para los 5 días laborales."""
        self.figure.clear()
        
        ax = self.figure.add_subplot(111, facecolor="#34495e") 

        dias_etiquetas = []
        for i in range(self.tabla.rowCount()): 
            item = self.tabla.item(i, 0) 
            if item:
                dias_etiquetas.append(item.text()) 

        colores = []
        objetivo_diario = self.OBJETIVO_SEMANAL / 5 
        
        for i, h in enumerate(self.horas_dia): 
            target = objetivo_diario 
            
            if target > 0:
                pct = h / target
                if pct >= 1.0:
                    colores.append("#2ecc71")
                elif pct >= 0.8:
                    colores.append("#f1c40f")
                else:
                    colores.append("#e74c3c")
            else:
                colores.append("#4e6d8a") 

        ax.bar(dias_etiquetas, self.horas_dia, color=colores, edgecolor="#ecf0f1", linewidth=0.5)

        ax.axhline(objetivo_diario, color="#1abc9c", linestyle="-.", alpha=0.9, 
                   label=f"Obj. diario ({objetivo_diario:.1f} h)")

        total_semanal = sum(self.horas_dia)
        pct_total = (total_semanal / self.OBJETIVO_SEMANAL) * 100
        
        title_text = f"Horas trabajadas (Lun-Vie) | Total: {total_semanal:.2f} h ({pct_total:.0f}%)"
        ax.set_title(title_text, color="#ecf0f1", fontsize=14, pad=15) 

        ax.set_ylabel("Horas", color="#ecf0f1")
        ax.set_xlabel("Día", color="#ecf0f1")
        ax.tick_params(colors="#ecf0f1", labelsize=9)
        ax.set_facecolor("#34495e") 
        for spine in ax.spines.values():
            spine.set_color("#ecf0f1")
            
        ax.grid(axis='y', linestyle=':', alpha=0.4, color="#7f8c8d")
        ax.set_axisbelow(True)
        
        self.figure.tight_layout(pad=3.0) 
        self.figure.autofmt_xdate(rotation=45) 

        ax.legend(facecolor="#34495e", edgecolor="#ecf0f1", labelcolor="#ecf0f1", fontsize=9)
        self.canvas.draw()
        
    def entrada_manual_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Entrada manual")
        layout = QFormLayout(dialog)

        combo_dia = QComboBox()
        for i in range(self.tabla.rowCount()): 
            item_fecha = self.tabla.item(i, 1)
            if item_fecha:
                combo_dia.addItem(item_fecha.text())
        layout.addRow("Día:", combo_dia)

        combo_tipo = QComboBox()
        for tipo in TIPOS_FICHAJE:
            combo_tipo.addItem(tipo)
        layout.addRow("Tipo de fichaje:", combo_tipo)

        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        hora_actual = QTime.currentTime()
        time_edit.setTime(QTime(hora_actual.hour(), hora_actual.minute()))
        layout.addRow("Hora:", time_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            dia_seleccionado = combo_dia.currentText()
            tipo_seleccionado = combo_tipo.currentText()
            hora_seleccionada = time_edit.time().toString("HH:mm")
            self.guardar_fichaje_manual(dia_seleccionado, tipo_seleccionado, hora_seleccionada)

    def guardar_fichaje_manual(self, fecha, tipo, hora):
        try:
            registrar_fichaje_manual(fecha, tipo, hora)
            self.actualizar_tabla()
            self.actualizar_historial_rapido() 
            self._inicializar_contador_estado()
            self.actualizar_resumen_semanal()
            self.actualizar_estado_botones() 
            self.fichajes_cambiados.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error de Fichaje Manual", str(e))
            return

    def editar_fichaje_desde_tabla(self, item):
        if item is None or item.column() < 2: 
            return 
            
        self.tabla.blockSignals(True) 
        
        item_fecha = self.tabla.item(item.row(), 1) 
        if item_fecha is None:
            self.tabla.blockSignals(False)
            return
            
        fecha = item_fecha.text()
        tipo = TIPOS_FICHAJE[item.column()-2] 
        hora = item.text().strip() or "" 

        if not hora:
             self.eliminar_fichaje_logico(fecha, tipo)
        else:
            try:
                datetime.strptime(hora, "%H:%M") 
                registrar_fichaje_manual(fecha, tipo, hora)
                self.actualizar_tabla()
                self.actualizar_historial_rapido()
                self._inicializar_contador_estado()
                self.actualizar_resumen_semanal()
                self.actualizar_estado_botones() 
                self.fichajes_cambiados.emit()
            except ValueError:
                QMessageBox.warning(self, "Formato Inválido", "La hora debe tener el formato HH:MM.")
                self.actualizar_tabla() 
            except Exception as e:
                QMessageBox.warning(self, "Error de Actualización", str(e))
                self.actualizar_tabla()

        self.tabla.blockSignals(False)

    def eliminar_fichaje_logico(self, fecha, tipo):
        from db import conectar 
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fichajes WHERE fecha=? AND tipo=?", (fecha, tipo))
                conn.commit()
            self.actualizar_tabla()
            self.actualizar_historial_rapido()
            self._inicializar_contador_estado()
            self.actualizar_resumen_semanal()
            self.actualizar_estado_botones() 
            self.fichajes_cambiados.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error de DB", f"No se pudo eliminar el fichaje: {e}")

    def eliminar_fichaje(self):
        item = self.tabla.currentItem()
        if not item or item.column() < 2 or not item.text(): 
            QMessageBox.warning(self, "Eliminar fichaje", "Selecciona una hora válida para eliminar.")
            return
            
        item_fecha = self.tabla.item(item.row(), 1) 
        if not item_fecha:
            return
            
        fecha = item_fecha.text()
        tipo = TIPOS_FICHAJE[item.column()-2] 

        reply = QMessageBox.question(self, "Confirmar eliminación", f"¿Eliminar {tipo} del {fecha}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.eliminar_fichaje_logico(fecha, tipo)