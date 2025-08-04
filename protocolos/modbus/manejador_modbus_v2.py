"""
Manejador Modbus V2 con Servidor TCP Real
========================================

Versión actualizada que integra el servidor TCP real con el sistema existente.
Coordina las operaciones del servidor Modbus TCP real y proporciona interfaz
para el sistema BMS Demo.

Autor: Sistema BMS Demo
Versión: 2.0.0 - Con servidor TCP real
"""

import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

# Importar componentes actualizados
from protocolos.modbus.cliente_modbus import ClienteModbus
from protocolos.modbus.servidor_modbus_tcp_real import ServidorModbusTCPReal
from protocolos.protocolo_base import ResultadoOperacion, EstadoProtocolo, EventoProtocolo
from configuracion.configuracion_protocolos import obtener_config_modbus
from utilidades.logger import obtener_logger_protocolo

class ModoOperacionModbus(Enum):
    """Modos de operación del manejador Modbus."""
    SOLO_CLIENTE = "solo_cliente"
    SOLO_SERVIDOR = "solo_servidor"
    CLIENTE_SERVIDOR = "cliente_servidor"
    SOLO_SERVIDOR_TCP = "solo_servidor_tcp"  # Nuevo modo con servidor TCP real
    DESHABILITADO = "deshabilitado"

class EstadisticasModbusV2:
    """Estadísticas mejoradas para el manejador Modbus V2."""
    
    def __init__(self):
        """Inicializar estadísticas."""
        self.reset()
        
    def reset(self):
        """Resetear todas las estadísticas."""
        self.inicio_operacion = datetime.now()
        self.operaciones_exitosas = 0
        self.operaciones_fallidas = 0
        self.reconexiones = 0
        self.comandos_recibidos = 0
        self.dispositivos_monitoreados = set()
        self.ultima_actualizacion = None
        self.errores_por_tipo = {}
        
        # Estadísticas específicas del servidor TCP
        self.conexiones_cliente = 0
        self.lecturas_input_registers = 0
        self.lecturas_holding_registers = 0
        self.escrituras_holding_registers = 0
        
    def obtener_resumen(self) -> Dict[str, Any]:
        """Obtener resumen de estadísticas."""
        tiempo_operacion = datetime.now() - self.inicio_operacion
        total_operaciones = self.operaciones_exitosas + self.operaciones_fallidas
        
        tasa_exito = 0
        if total_operaciones > 0:
            tasa_exito = (self.operaciones_exitosas / total_operaciones) * 100
            
        return {
            'tiempo_operacion': str(tiempo_operacion),
            'total_operaciones': total_operaciones,
            'tasa_exito': round(tasa_exito, 2),
            'operaciones_exitosas': self.operaciones_exitosas,
            'operaciones_fallidas': self.operaciones_fallidas,
            'reconexiones': self.reconexiones,
            'comandos_recibidos': self.comandos_recibidos,
            'dispositivos_monitoreados': len(self.dispositivos_monitoreados),
            'ultima_actualizacion': str(self.ultima_actualizacion) if self.ultima_actualizacion else None,
            'errores_por_tipo': self.errores_por_tipo,
            'conexiones_cliente': self.conexiones_cliente,
            'lecturas_input_registers': self.lecturas_input_registers,
            'lecturas_holding_registers': self.lecturas_holding_registers,
            'escrituras_holding_registers': self.escrituras_holding_registers
        }

class ManejadorModbusV2:
    """
    Manejador Modbus V2 que integra servidor TCP real con el sistema existente.
    Proporciona interfaz unificada para manejo de protocolo Modbus con servidor real.
    """
    
    def __init__(self, modo_operacion: ModoOperacionModbus = ModoOperacionModbus.SOLO_SERVIDOR_TCP):
        """
        Inicializar manejador Modbus V2.
        
        Args:
            modo_operacion: Modo de operación del manejador
        """
        self.modo_operacion = modo_operacion
        self.config_modbus = obtener_config_modbus()
        self.logger = obtener_logger_protocolo("modbus_v2")
        
        # Componentes
        self.cliente = None
        self.servidor_tcp = None  # Servidor TCP real
        
        # Control de hilos
        self.hilo_polling = None
        self.hilo_actualizador_datos = None
        self.hilo_monitor_conexiones = None
        self.detener_hilos = threading.Event()
        self.activo = False
        
        # Estadísticas
        self.estadisticas = EstadisticasModbusV2()
        
        # Callbacks
        self.callbacks_datos_recibidos = []
        self.callbacks_estado_cambiado = []
        self.callbacks_comando_recibido = []
        
        # Cache de datos del sistema BMS
        self.datos_sistema = {
            'temperatura_lab': 25.0,
            'humedad_lab': 55.0,
            'presion_lab': 1013.2,
            'camaras_total': 8,
            'camaras_online': 8,
            'controladores_total': 4,
            'controladores_online': 4,
            'ups_total': 2,
            'ups_online': 2,
            'alarmas_activas': 0,
            'eventos_dia': 0,
            'calidad_aire': 85,
            'luminosidad': 60,
            'ruido_db': 42,
            'estado_comunicacion_genetec': True,
            'version_sistema': "2.0.0",
            'tiempo_funcionamiento_horas': 0
        }
        
        # Estado interno
        self.estado_conexion = EstadoProtocolo.DESCONECTADO
        self.ultima_actividad = datetime.now()
        
        self._inicializar_componentes()
        
    def _inicializar_componentes(self):
        """Inicializar componentes según el modo de operación."""
        try:
            if self.modo_operacion in [ModoOperacionModbus.SOLO_CLIENTE, ModoOperacionModbus.CLIENTE_SERVIDOR]:
                self.cliente = ClienteModbus()
                self.logger.info("🔌 Cliente Modbus inicializado")
                
            if self.modo_operacion in [
                ModoOperacionModbus.SOLO_SERVIDOR_TCP, 
                ModoOperacionModbus.CLIENTE_SERVIDOR
            ]:
                # Usar servidor TCP real
                self.servidor_tcp = ServidorModbusTCPReal()
                self._configurar_callbacks_servidor_tcp()
                self.logger.info("🚀 Servidor Modbus TCP real inicializado")
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando componentes Modbus: {e}")
            raise
            
    def _configurar_callbacks_servidor_tcp(self):
        """Configurar callbacks del servidor TCP real."""
        if self.servidor_tcp:
            # Callback para comando general
            self.servidor_tcp.agregar_callback_escritura(0, self._callback_comando_general)
            
            # Callback para reset de alarmas
            self.servidor_tcp.agregar_callback_escritura(1, self._callback_reset_alarmas)
            
            # Callback para backup forzado
            self.servidor_tcp.agregar_callback_escritura(2, self._callback_force_backup)
            
            # Callback para test del sistema
            self.servidor_tcp.agregar_callback_escritura(3, self._callback_test_sistema)
            
            self.logger.info("✅ Callbacks del servidor TCP configurados")
            
    def iniciar(self) -> ResultadoOperacion:
        """
        Iniciar el manejador Modbus V2.
        
        Returns:
            ResultadoOperacion con el resultado del inicio
        """
        try:
            self.logger.info(f"🚀 Iniciando manejador Modbus V2 en modo: {self.modo_operacion.value}")
            
            # Iniciar cliente si está configurado
            if self.cliente:
                resultado_cliente = self.cliente.conectar()
                if not resultado_cliente.exitoso:
                    self.logger.warning(f"⚠️ Cliente Modbus no pudo conectar: {resultado_cliente.mensaje}")
                else:
                    self.logger.info("✅ Cliente Modbus conectado")
            
            # Iniciar servidor TCP si está configurado
            if self.servidor_tcp:
                resultado_servidor = self.servidor_tcp.conectar()
                if not resultado_servidor.exitoso:
                    return ResultadoOperacion(
                        exitoso=False,
                        mensaje=f"Error iniciando servidor TCP: {resultado_servidor.mensaje}"
                    )
                else:
                    self.logger.info(f"✅ Servidor TCP iniciado: {resultado_servidor.mensaje}")
            
            # Iniciar hilos de trabajo
            self._iniciar_hilos()
            
            self.activo = True
            self.estado_conexion = EstadoProtocolo.CONECTADO
            self.estadisticas.inicio_operacion = datetime.now()
            
            self.logger.info("✅ Manejador Modbus V2 iniciado exitosamente")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Manejador Modbus V2 iniciado en modo {self.modo_operacion.value}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando manejador Modbus V2: {e}")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error iniciando manejador: {str(e)}"
            )
            
    def _iniciar_hilos(self):
        """Iniciar hilos de trabajo."""
        try:
            # Hilo actualizador de datos del sistema
            self.hilo_actualizador_datos = threading.Thread(
                target=self._bucle_actualizacion_datos,
                daemon=True,
                name="ModbusV2_DataUpdater"
            )
            self.hilo_actualizador_datos.start()
            
            # Hilo monitor de conexiones (si hay cliente)
            if self.cliente:
                self.hilo_monitor_conexiones = threading.Thread(
                    target=self._bucle_monitor_conexiones,
                    daemon=True,
                    name="ModbusV2_ConnectionMonitor"
                )
                self.hilo_monitor_conexiones.start()
                
            self.logger.info("✅ Hilos de trabajo iniciados")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando hilos: {e}")
            
    def _bucle_actualizacion_datos(self):
        """Bucle que actualiza datos del sistema periódicamente."""
        contador = 0
        tiempo_inicio = datetime.now()
        
        while self.activo and not self.detener_hilos.is_set():
            try:
                contador += 1
                
                # Actualizar tiempo de funcionamiento
                tiempo_funcionamiento = (datetime.now() - tiempo_inicio).total_seconds() / 3600
                self.datos_sistema['tiempo_funcionamiento_horas'] = round(tiempo_funcionamiento, 2)
                
                # Simular variaciones ligeras en sensores
                if contador % 12 == 0:  # Cada minuto aprox
                    import random
                    
                    # Variación de temperatura (±0.5°C)
                    self.datos_sistema['temperatura_lab'] += random.uniform(-0.5, 0.5)
                    self.datos_sistema['temperatura_lab'] = max(20.0, min(30.0, self.datos_sistema['temperatura_lab']))
                    
                    # Variación de humedad (±2%)
                    self.datos_sistema['humedad_lab'] += random.uniform(-2, 2)
                    self.datos_sistema['humedad_lab'] = max(40.0, min(70.0, self.datos_sistema['humedad_lab']))
                    
                    # Actualizar datos en el servidor TCP
                    if self.servidor_tcp:
                        self.servidor_tcp.actualizar_dato_sistema('temperatura_promedio', int(self.datos_sistema['temperatura_lab'] * 10))
                        self.servidor_tcp.actualizar_dato_sistema('humedad_promedio', int(self.datos_sistema['humedad_lab']))
                        self.servidor_tcp.actualizar_dato_sistema('camaras_online', self.datos_sistema['camaras_online'])
                        self.servidor_tcp.actualizar_dato_sistema('controladores_online', self.datos_sistema['controladores_online'])
                
                # Actualizar estadísticas
                self.estadisticas.ultima_actualizacion = datetime.now()
                self.estadisticas.operaciones_exitosas += 1
                
                # Dormir 5 segundos
                self.detener_hilos.wait(5)
                
            except Exception as e:
                self.logger.error(f"❌ Error en bucle de actualización: {e}")
                self.estadisticas.operaciones_fallidas += 1
                self.detener_hilos.wait(10)
                
    def _bucle_monitor_conexiones(self):
        """Monitorear conexiones del cliente."""
        while self.activo and not self.detener_hilos.is_set():
            try:
                if self.cliente:
                    if not self.cliente.verificar_conexion():
                        self.logger.warning("⚠️ Cliente Modbus desconectado, intentando reconectar...")
                        resultado = self.cliente.conectar()
                        if resultado.exitoso:
                            self.logger.info("✅ Cliente Modbus reconectado")
                            self.estadisticas.reconexiones += 1
                        else:
                            self.logger.error(f"❌ Error reconectando cliente: {resultado.mensaje}")
                            
                # Dormir 30 segundos
                self.detener_hilos.wait(30)
                
            except Exception as e:
                self.logger.error(f"❌ Error en monitor de conexiones: {e}")
                self.detener_hilos.wait(60)
                
    def detener(self) -> ResultadoOperacion:
        """
        Detener el manejador Modbus V2.
        
        Returns:
            ResultadoOperacion con el resultado de la parada
        """
        try:
            self.logger.info("🛑 Deteniendo manejador Modbus V2...")
            
            # Marcar como inactivo
            self.activo = False
            self.detener_hilos.set()
            
            # Detener servidor TCP
            if self.servidor_tcp:
                resultado_servidor = self.servidor_tcp.desconectar()
                if resultado_servidor.exitoso:
                    self.logger.info("✅ Servidor TCP detenido")
                else:
                    self.logger.warning(f"⚠️ Error deteniendo servidor TCP: {resultado_servidor.mensaje}")
            
            # Detener cliente
            if self.cliente:
                resultado_cliente = self.cliente.desconectar()
                if resultado_cliente.exitoso:
                    self.logger.info("✅ Cliente Modbus desconectado")
                else:
                    self.logger.warning(f"⚠️ Error desconectando cliente: {resultado_cliente.mensaje}")
            
            # Esperar que terminen los hilos
            hilos = [self.hilo_actualizador_datos, self.hilo_monitor_conexiones, self.hilo_polling]
            for hilo in hilos:
                if hilo and hilo.is_alive():
                    hilo.join(timeout=3)
                    
            self.estado_conexion = EstadoProtocolo.DESCONECTADO
            
            self.logger.info("✅ Manejador Modbus V2 detenido exitosamente")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje="Manejador Modbus V2 detenido exitosamente"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo manejador: {e}")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error deteniendo manejador: {str(e)}"
            )
            
    def obtener_estado_completo(self) -> Dict[str, Any]:
        """
        Obtener estado completo del manejador.
        
        Returns:
            Diccionario con estado completo del sistema
        """
        try:
            estado = {
                'modo_operacion': self.modo_operacion.value,
                'activo': self.activo,
                'estado_conexion': self.estado_conexion.value,
                'tiempo_actividad': str(datetime.now() - self.estadisticas.inicio_operacion),
                'estadisticas': self.estadisticas.obtener_resumen(),
                'datos_sistema': self.datos_sistema.copy(),
                'configuracion': {
                    'ip': self.config_modbus.ip,
                    'puerto': self.config_modbus.puerto,
                    'timeout': self.config_modbus.timeout,
                    'id_esclavo': self.config_modbus.id_esclavo
                }
            }
            
            # Estado del servidor TCP
            if self.servidor_tcp:
                estado['servidor_tcp'] = {
                    'activo': self.servidor_tcp.verificar_conexion(),
                    'estado': self.servidor_tcp.estado.value if hasattr(self.servidor_tcp, 'estado') else 'desconocido'
                }
            
            # Estado del cliente
            if self.cliente:
                estado['cliente'] = {
                    'activo': self.cliente.verificar_conexion() if hasattr(self.cliente, 'verificar_conexion') else False,
                    'estado': self.cliente.estado.value if hasattr(self.cliente, 'estado') else 'desconocido'
                }
                
            return estado
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estado: {e}")
            return {'error': f'Error obteniendo estado: {str(e)}'}
            
    # Métodos de callback para servidor TCP
    def _callback_comando_general(self, direccion: int, valor: int):
        """Callback para comando general del sistema."""
        try:
            comandos = {0: "Ninguno", 1: "Reiniciar", 2: "Apagar", 3: "Mantenimiento"}
            comando = comandos.get(valor, f"Desconocido({valor})")
            
            self.logger.info(f"🔧 Comando general recibido: {comando}")
            self.estadisticas.comandos_recibidos += 1
            
            # Ejecutar callbacks externos
            for callback in self.callbacks_comando_recibido:
                try:
                    callback({'tipo': 'comando_general', 'valor': valor, 'comando': comando})
                except Exception as e:
                    self.logger.error(f"❌ Error en callback comando: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error en callback comando general: {e}")
            
    def _callback_reset_alarmas(self, direccion: int, valor: int):
        """Callback para reset de alarmas."""
        if valor == 1:
            self.logger.info("🔧 Reset de alarmas solicitado")
            self.datos_sistema['alarmas_activas'] = 0
            self.estadisticas.comandos_recibidos += 1
            
            # Notificar callbacks externos
            for callback in self.callbacks_comando_recibido:
                try:
                    callback({'tipo': 'reset_alarmas', 'valor': valor})
                except Exception as e:
                    self.logger.error(f"❌ Error en callback reset alarmas: {e}")
                    
    def _callback_force_backup(self, direccion: int, valor: int):
        """Callback para backup forzado."""
        if valor == 1:
            self.logger.info("🔧 Backup forzado solicitado")
            self.estadisticas.comandos_recibidos += 1
            
            # Notificar callbacks externos
            for callback in self.callbacks_comando_recibido:
                try:
                    callback({'tipo': 'force_backup', 'valor': valor})
                except Exception as e:
                    self.logger.error(f"❌ Error en callback backup: {e}")
                    
    def _callback_test_sistema(self, direccion: int, valor: int):
        """Callback para test del sistema."""
        if valor == 1:
            self.logger.info("🔧 Test del sistema solicitado")
            self.estadisticas.comandos_recibidos += 1
            
            # Notificar callbacks externos
            for callback in self.callbacks_comando_recibido:
                try:
                    callback({'tipo': 'test_sistema', 'valor': valor})
                except Exception as e:
                    self.logger.error(f"❌ Error en callback test: {e}")
                    
    # Métodos públicos para agregar callbacks
    def agregar_callback_datos(self, callback: Callable[[Dict[str, Any]], None]):
        """Agregar callback para datos recibidos."""
        self.callbacks_datos_recibidos.append(callback)
        
    def agregar_callback_comando(self, callback: Callable[[Dict[str, Any]], None]):
        """Agregar callback para comandos recibidos."""
        self.callbacks_comando_recibido.append(callback)
        
    def agregar_callback_estado(self, callback: Callable[[EstadoProtocolo], None]):
        """Agregar callback para cambios de estado."""
        self.callbacks_estado_cambiado.append(callback)
        
    def simular_evento_sistema(self, tipo_evento: str, datos: Dict[str, Any] = None):
        """Simular eventos del sistema para pruebas."""
        try:
            if tipo_evento == "alarma_temperatura":
                self.datos_sistema['alarmas_activas'] += 1
                if datos and 'temperatura' in datos:
                    self.datos_sistema['temperatura_lab'] = datos['temperatura']
                self.logger.warning(f"🚨 Alarma de temperatura: {self.datos_sistema['temperatura_lab']}°C")
                
                # Actualizar servidor TCP
                if self.servidor_tcp:
                    self.servidor_tcp.actualizar_dato_sistema('numero_alarmas_activas', self.datos_sistema['alarmas_activas'])
                
            elif tipo_evento == "dispositivo_offline":
                dispositivo = datos.get('dispositivo', 'camara') if datos else 'camara'
                if dispositivo == 'camara':
                    self.datos_sistema['camaras_online'] = max(0, self.datos_sistema['camaras_online'] - 1)
                    if self.servidor_tcp:
                        self.servidor_tcp.actualizar_dato_sistema('camaras_online', self.datos_sistema['camaras_online'])
                elif dispositivo == 'controlador':
                    self.datos_sistema['controladores_online'] = max(0, self.datos_sistema['controladores_online'] - 1)
                    if self.servidor_tcp:
                        self.servidor_tcp.actualizar_dato_sistema('controladores_online', self.datos_sistema['controladores_online'])
                        
                self.logger.warning(f"📴 Dispositivo offline: {dispositivo}")
                
            elif tipo_evento == "reset_alarmas":
                self.datos_sistema['alarmas_activas'] = 0
                if self.servidor_tcp:
                    self.servidor_tcp.actualizar_dato_sistema('numero_alarmas_activas', 0)
                self.logger.info("✅ Alarmas reseteadas")
                
        except Exception as e:
            self.logger.error(f"❌ Error simulando evento: {e}")
            
    def leer_datos_sistema(self, nombre_dato: str) -> Any:
        """
        Leer un dato específico del sistema.
        
        Args:
            nombre_dato: Nombre del dato a leer
            
        Returns:
            Valor del dato o None si no existe
        """
        return self.datos_sistema.get(nombre_dato)
        
    def actualizar_dato_sistema(self, nombre_dato: str, valor: Any):
        """
        Actualizar un dato específico del sistema.
        
        Args:
            nombre_dato: Nombre del dato
            valor: Nuevo valor
        """
        try:
            if nombre_dato in self.datos_sistema:
                self.datos_sistema[nombre_dato] = valor
                self.logger.debug(f"📊 Dato actualizado: {nombre_dato} = {valor}")
                
                # Actualizar en servidor TCP si existe
                if self.servidor_tcp:
                    self.servidor_tcp.actualizar_dato_sistema(nombre_dato, valor)
            else:
                self.logger.warning(f"⚠️ Dato no encontrado: {nombre_dato}")
                
        except Exception as e:
            self.logger.error(f"❌ Error actualizando dato {nombre_dato}: {e}")

# Función de utilidad actualizada
def crear_manejador_modbus_v2(modo: ModoOperacionModbus = ModoOperacionModbus.SOLO_SERVIDOR_TCP) -> ManejadorModbusV2:
    """Crear manejador Modbus V2 con servidor TCP real."""
    return ManejadorModbusV2(modo)

# Alias para compatibilidad con código existente
ManejadorModbus = ManejadorModbusV2

if __name__ == "__main__":
    # Prueba del manejador V2 con servidor TCP real
    print("=== PROBANDO MANEJADOR MODBUS V2 CON SERVIDOR TCP REAL ===")
    
    try:
        manejador = crear_manejador_modbus_v2(ModoOperacionModbus.SOLO_SERVIDOR_TCP)
        
        # Iniciar manejador
        resultado = manejador.iniciar()
        print(f"✅ Manejador iniciado: {resultado.mensaje}")
        
        if resultado.exitoso:
            print("🔥 Servidor Modbus TCP activo - Conecta desde un cliente Modbus")
            print(f"📡 IP: {manejador.config_modbus.ip}:{manejador.config_modbus.puerto}")
            print("📊 Input Registers: 0-49 (datos del sistema)")
            print("⚙️ Holding Registers: 0-49 (comandos)")
            print("⏹️ Presiona Ctrl+C para detener")
            
            try:
                contador = 0
                while True:
                    time.sleep(10)
                    contador += 1
                    
                    estado = manejador.obtener_estado_completo()
                    print(f"\n📊 Ciclo {contador} - Estado del sistema:")
                    print(f"   Temperatura: {estado['datos_sistema']['temperatura_lab']:.1f}°C")
                    print(f"   Dispositivos online: C:{estado['datos_sistema']['camaras_online']}/CT:{estado['datos_sistema']['controladores_online']}")
                    print(f"   Comandos recibidos: {estado['estadisticas']['comandos_recibidos']}")
                    print(f"   Servidor TCP activo: {estado.get('servidor_tcp', {}).get('activo', False)}")
                    
                    # Simular eventos ocasionalmente
                    if contador % 5 == 0:
                        print("🎭 Simulando evento de prueba...")
                        manejador.simular_evento_sistema("alarma_temperatura", {"temperatura": 32.0})
                    
            except KeyboardInterrupt:
                print("\n⏹️ Deteniendo manejador...")
                manejador.detener()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("✅ Prueba completada")