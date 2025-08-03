"""
Servidor Modbus TCP Real para Sistema BMS
=========================================

Implementación completa de servidor Modbus TCP usando pymodbus que:
- Expone input registers y holding registers reales
- Escucha en IP:puerto configurados (ej: 192.168.1.95:502)
- Maneja callbacks para escrituras
- Registra todas las operaciones
- Mantiene datastore sincronizado con estado real del sistema

Autor: Sistema BMS Demo
Versión: 2.0.0 - Servidor TCP Real
"""

import asyncio
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import socket

# PyModbus imports para servidor TCP
try:
    # PyModbus 3.x - Async server
    from pymodbus.server import StartAsyncTcpServer
    from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
    from pymodbus.datastore import ModbusSparseDataBlock
    from pymodbus.device import ModbusDeviceIdentification
    PYMODBUS_VERSION = "3.x"
except ImportError:
    try:
        # PyModbus 2.x - Sync server
        from pymodbus.server.sync import StartTcpServer
        from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
        from pymodbus.datastore import ModbusSparseDataBlock
        from pymodbus.device import ModbusDeviceIdentification
        PYMODBUS_VERSION = "2.x"
    except ImportError as e:
        print(f"Error: PyModbus no encontrado. Instalar con: pip install pymodbus==3.4.1")
        raise e

# Importar clases base del sistema
from protocolos.protocolo_base import ProtocoloBase, ResultadoOperacion, EstadoProtocolo
from configuracion.configuracion_protocolos import obtener_config_modbus
from utilidades.logger import obtener_logger_protocolo

class BMSDataStore(ModbusSparseDataBlock):
    """
    DataStore personalizado para el BMS que permite callbacks y logging.
    """
    
    def __init__(self, values=None, callbacks=None, logger=None):
        """
        Inicializar datastore del BMS.
        
        Args:
            values: Valores iniciales de registros
            callbacks: Diccionario de callbacks por dirección
            logger: Logger para registrar operaciones
        """
        super().__init__(values or {})
        self.callbacks = callbacks or {}
        self.logger = logger
        self.lecturas_count = 0
        self.escrituras_count = 0
        
    def setValues(self, address, values):
        """
        Sobrescribir setValues para agregar callbacks y logging.
        
        Args:
            address: Dirección inicial
            values: Lista de valores a escribir
        """
        if self.logger:
            self.logger.info(f"📝 Modbus WRITE: Dirección {address}, Valores {values}")
            
        # Llamar al método padre
        super().setValues(address, values)
        
        # Ejecutar callbacks para cada dirección escrita
        for i, valor in enumerate(values):
            direccion_actual = address + i
            if direccion_actual in self.callbacks:
                try:
                    self.callbacks[direccion_actual](direccion_actual, valor)
                    if self.logger:
                        self.logger.debug(f"✅ Callback ejecutado para dirección {direccion_actual}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"❌ Error en callback {direccion_actual}: {e}")
                        
        self.escrituras_count += len(values)
        
    def getValues(self, address, count=1):
        """
        Sobrescribir getValues para logging.
        
        Args:
            address: Dirección inicial
            count: Cantidad de registros a leer
            
        Returns:
            Lista de valores
        """
        valores = super().getValues(address, count)
        
        if self.logger:
            self.logger.debug(f"📖 Modbus READ: Dirección {address}, Count {count}, Valores {valores}")
            
        self.lecturas_count += count
        return valores

class ServidorModbusTCPReal(ProtocoloBase):
    """
    Servidor Modbus TCP real usando pymodbus que expone registros del BMS.
    """
    
    def __init__(self, configuracion: Dict[str, Any] = None):
        """
        Inicializar servidor Modbus TCP real.
        
        Args:
            configuracion: Configuración específica (opcional)
        """
        # Obtener configuración
        if configuracion is None:
            self.config_modbus = obtener_config_modbus()
        else:
            from types import SimpleNamespace
            self.config_modbus = SimpleNamespace(**configuracion)
            
        # Inicializar clase base
        super().__init__("modbus_servidor_tcp", self.config_modbus.__dict__)
        
        # Estado del servidor
        self.servidor_tcp = None
        self.servidor_activo = False
        self.hilo_servidor = None
        self.loop_asyncio = None
        
        # DataStores para diferentes tipos de registros
        self.input_registers_store = None
        self.holding_registers_store = None
        self.coils_store = None
        self.discrete_inputs_store = None
        
        # Callbacks por dirección
        self.callbacks_escritura = {}
        self.callbacks_lectura = {}
        
        # Datos del sistema BMS - Registros Input (solo lectura)
        self.datos_input_registers = {
            # Estados del sistema (0-9)
            0: 1,  # estado_general_sistema (0=Error, 1=OK, 2=Warning)
            1: 0,  # tiempo_funcionamiento_horas
            2: 3,  # numero_dispositivos_total
            3: 3,  # numero_dispositivos_online
            4: 0,  # numero_alarmas_activas
            5: 0,  # numero_eventos_dia
            6: 1,  # estado_comunicacion_genetec (0=Offline, 1=Online)
            7: 1,  # version_sistema_mayor
            8: 0,  # version_sistema_menor
            9: int(time.time()),  # timestamp_ultima_actualizacion
            
            # Sensores ambientales (10-19)
            10: 250,  # temperatura_promedio x10 (250 = 25.0°C)
            11: 55,   # humedad_promedio %
            12: 10132, # presion_atmosferica x10 mbar
            13: 85,   # calidad_aire (0-100)
            14: 60,   # luminosidad (0-100)
            15: 42,   # ruido_db
            
            # Estados de cámaras (20-29)
            20: 1,    # camaras_total
            21: 1,    # camaras_online
            22: 1,    # camaras_grabando
            23: 0,    # camaras_alarma
            24: 45,   # espacio_disco_usado %
            25: 150,  # bitrate_promedio_mbps x10
            
            # Estados de controladores (30-39)
            30: 1,    # controladores_total
            31: 1,    # controladores_online
            32: 1,    # puertas_total
            33: 0,    # puertas_abiertas
            34: 25,   # eventos_acceso_dia
            35: 150,  # tarjetas_activas
            
            # Gabinetes y UPS (40-49)
            40: 1,    # ups_total
            41: 1,    # ups_online
            42: 0,    # ups_en_bateria
            43: 85,   # carga_bateria_minima %
            44: 280,  # temperatura_gabinete_max x10 (28.0°C)
            45: 2,    # ventiladores_activos
        }
        
        # Datos Holding Registers (lectura/escritura)
        self.datos_holding_registers = {
            # Comandos y configuración (0-9)
            0: 0,  # comando_sistema (1=Restart, 2=Stop, 3=Reset)
            1: 2,  # nivel_log (1=DEBUG, 2=INFO, 3=WARNING, 4=ERROR)
            2: 5,  # intervalo_polling_segundos
            3: 30, # timeout_dispositivos_segundos
            4: 1,  # habilitar_alarmas (0=No, 1=Sí)
            5: 0,  # modo_debug (0=No, 1=Sí)
            
            # Setpoints y límites (10-19)
            10: 300,  # temperatura_limite_superior x10 (30.0°C)
            11: 150,  # temperatura_limite_inferior x10 (15.0°C)
            12: 70,   # humedad_limite_superior %
            13: 30,   # humedad_limite_inferior %
            14: 10200, # presion_limite_superior x10
            15: 10000, # presion_limite_inferior x10
            
            # Control de dispositivos (20-29)
            20: 0,  # forzar_actualizacion_camaras (1=Ejecutar)
            21: 0,  # forzar_actualizacion_controladores (1=Ejecutar)
            22: 0,  # reiniciar_comunicacion_genetec (1=Ejecutar)
            23: 1,  # habilitar_polling_continuo (0=No, 1=Sí)
        }
        
        # Hilo para actualizar datos del sistema
        self.hilo_actualizador = None
        self.detener_actualizador = threading.Event()
        
        self.logger.info("🚀 Servidor Modbus TCP real inicializado")
        
    def conectar(self) -> ResultadoOperacion:
        """
        Iniciar servidor Modbus TCP real.
        
        Returns:
            ResultadoOperacion con el resultado del inicio
        """
        try:
            self.cambiar_estado(EstadoProtocolo.CONECTANDO, "Iniciando servidor Modbus TCP")
            
            # Verificar que el puerto esté disponible
            if not self._verificar_puerto_disponible():
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=f"Puerto {self.config_modbus.puerto} no está disponible"
                )
            
            # Configurar callbacks por defecto
            self._configurar_callbacks_por_defecto()
            
            # Crear datastores
            self._crear_datastores()
            
            # Crear contexto del servidor
            context = self._crear_contexto_servidor()
            
            # Configurar identificación del dispositivo
            identity = self._crear_identificacion_dispositivo()
            
            # Iniciar servidor según versión de pymodbus
            if PYMODBUS_VERSION == "3.x":
                self._iniciar_servidor_async(context, identity)
            else:
                self._iniciar_servidor_sync(context, identity)
                
            # Iniciar hilo actualizador de datos
            self._iniciar_actualizador_datos()
            
            self.servidor_activo = True
            self.cambiar_estado(EstadoProtocolo.CONECTADO, "Servidor Modbus TCP iniciado")
            
            self.logger.info(f"✅ Servidor Modbus TCP iniciado en {self.config_modbus.ip}:{self.config_modbus.puerto}")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Servidor Modbus TCP iniciado en {self.config_modbus.ip}:{self.config_modbus.puerto}"
            )
            
        except Exception as e:
            self.cambiar_estado(EstadoProtocolo.ERROR, f"Error al iniciar servidor: {str(e)}")
            self.manejar_error(e, "conectar_servidor_tcp")
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error iniciando servidor Modbus TCP: {str(e)}"
            )
            
    def _verificar_puerto_disponible(self) -> bool:
        """Verificar si el puerto está disponible."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            resultado = sock.bind((self.config_modbus.ip, self.config_modbus.puerto))
            sock.close()
            return True
        except OSError as e:
            self.logger.warning(f"⚠️ Puerto {self.config_modbus.puerto} en uso: {e}")
            return False
            
    def _crear_datastores(self):
        """Crear datastores personalizados para cada tipo de registro."""
        
        # Input Registers (solo lectura)
        self.input_registers_store = BMSDataStore(
            values=self.datos_input_registers.copy(),
            callbacks={},  # Sin callbacks para input registers
            logger=self.logger
        )
        
        # Holding Registers (lectura/escritura)
        self.holding_registers_store = BMSDataStore(
            values=self.datos_holding_registers.copy(),
            callbacks=self.callbacks_escritura,
            logger=self.logger
        )
        
        # Coils y Discrete Inputs (básicos)
        self.coils_store = BMSDataStore(values={0: False}, logger=self.logger)
        self.discrete_inputs_store = BMSDataStore(values={0: True}, logger=self.logger)
        
    def _crear_contexto_servidor(self):
        """Crear contexto del servidor Modbus."""
        
        # Crear contexto de esclavo
        slave_context = ModbusSlaveContext(
            di=self.discrete_inputs_store,      # Discrete Inputs
            co=self.coils_store,                # Coils
            hr=self.holding_registers_store,    # Holding Registers
            ir=self.input_registers_store,      # Input Registers
            zero_mode=True                      # Direccionamiento basado en 0
        )
        
        # Crear contexto del servidor (puede manejar múltiples Unit IDs)
        context = ModbusServerContext(slaves={
            1: slave_context,  # Unit ID 1 (principal)
            # Pueden agregarse más Unit IDs si es necesario
            # 2: otro_slave_context,
        }, single=False)
        
        return context
        
    def _crear_identificacion_dispositivo(self):
        """Crear identificación del dispositivo Modbus."""
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'BMS Demo System'
        identity.ProductCode = 'BMS-TCP-01'
        identity.VendorUrl = 'http://localhost:5000'
        identity.ProductName = 'BMS Demo Modbus Server'
        identity.ModelName = 'BMS Demo TCP Server'
        identity.MajorMinorRevision = '2.0.0'
        
        return identity
        
    def _iniciar_servidor_async(self, context, identity):
        """Iniciar servidor usando PyModbus 3.x (async)."""
        def _run_async_server():
            self.loop_asyncio = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop_asyncio)
            
            try:
                # Iniciar servidor async
                self.loop_asyncio.run_until_complete(
                    StartAsyncTcpServer(
                        context=context,
                        identity=identity,
                        address=(self.config_modbus.ip, self.config_modbus.puerto),
                        allow_reuse_address=True,
                        defer_start=False
                    )
                )
            except Exception as e:
                self.logger.error(f"❌ Error en servidor async: {e}")
                self.servidor_activo = False
                
        self.hilo_servidor = threading.Thread(target=_run_async_server, daemon=True)
        self.hilo_servidor.start()
        
        # Esperar un poco para que inicie
        time.sleep(1)
        
    def _iniciar_servidor_sync(self, context, identity):
        """Iniciar servidor usando PyModbus 2.x (sync)."""
        def _run_sync_server():
            try:
                StartTcpServer(
                    context=context,
                    identity=identity,
                    address=(self.config_modbus.ip, self.config_modbus.puerto),
                    allow_reuse_address=True
                )
            except Exception as e:
                self.logger.error(f"❌ Error en servidor sync: {e}")
                self.servidor_activo = False
                
        self.hilo_servidor = threading.Thread(target=_run_sync_server, daemon=True)
        self.hilo_servidor.start()
        
        # Esperar un poco para que inicie
        time.sleep(1)
        
    def _configurar_callbacks_por_defecto(self):
        """Configurar callbacks por defecto para comandos del sistema."""
        
        # Callback para comando de sistema (registro 0)
        self.callbacks_escritura[0] = self._callback_comando_sistema
        
        # Callback para cambio de nivel de log (registro 1)
        self.callbacks_escritura[1] = self._callback_nivel_log
        
        # Callback para intervalo de polling (registro 2)
        self.callbacks_escritura[2] = self._callback_intervalo_polling
        
        # Callback para forzar actualización de cámaras (registro 20)
        self.callbacks_escritura[20] = self._callback_actualizar_camaras
        
        # Callback para forzar actualización de controladores (registro 21)
        self.callbacks_escritura[21] = self._callback_actualizar_controladores
        
        # Callback para reiniciar comunicación Genetec (registro 22)
        self.callbacks_escritura[22] = self._callback_reiniciar_genetec
        
    def _callback_comando_sistema(self, direccion: int, valor: int):
        """Callback para comandos de sistema."""
        self.logger.info(f"🔧 COMANDO SISTEMA recibido: {valor}")
        
        if valor == 1:
            self.logger.info("Comando: RESTART sistema")
        elif valor == 2:
            self.logger.info("Comando: STOP sistema")
        elif valor == 3:
            self.logger.info("Comando: RESET estadísticas")
                
    def _callback_nivel_log(self, direccion: int, valor: int):
        """Callback para cambio de nivel de logging."""
        niveles = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'ERROR'}
        if valor in niveles:
            nivel = niveles[valor]
            self.logger.info(f"🔧 CAMBIO NIVEL LOG a: {nivel}")
            
    def _callback_intervalo_polling(self, direccion: int, valor: int):
        """Callback para cambio de intervalo de polling."""
        if 1 <= valor <= 300:
            self.logger.info(f"🔧 CAMBIO INTERVALO POLLING a: {valor} segundos")
            
    def _callback_actualizar_camaras(self, direccion: int, valor: int):
        """Callback para forzar actualización de cámaras."""
        if valor == 1:
            self.logger.info("🔧 FORZAR ACTUALIZACIÓN CÁMARAS")
            
    def _callback_actualizar_controladores(self, direccion: int, valor: int):
        """Callback para forzar actualización de controladores."""
        if valor == 1:
            self.logger.info("🔧 FORZAR ACTUALIZACIÓN CONTROLADORES")
            
    def _callback_reiniciar_genetec(self, direccion: int, valor: int):
        """Callback para reiniciar comunicación con Genetec."""
        if valor == 1:
            self.logger.info("🔧 REINICIAR COMUNICACIÓN GENETEC")
            
    def _iniciar_actualizador_datos(self):
        """Iniciar hilo que actualiza datos del sistema periódicamente."""
        def _actualizar_datos_periodicamente():
            contador = 0
            tiempo_inicio = time.time()
            
            while self.servidor_activo and not self.detener_actualizador.is_set():
                try:
                    contador += 1
                    
                    # Actualizar timestamp
                    self.input_registers_store.setValues(9, [int(time.time())])
                    
                    # Actualizar tiempo de funcionamiento
                    horas_funcionamiento = int((time.time() - tiempo_inicio) / 3600)
                    self.input_registers_store.setValues(1, [horas_funcionamiento])
                    
                    # Simular variaciones en sensores cada 30 segundos
                    if contador % 6 == 0:
                        import random
                        
                        # Temperatura con variación
                        temp_actual = self.input_registers_store.getValues(10, 1)[0]
                        nueva_temp = max(200, min(350, temp_actual + random.randint(-10, 10)))
                        self.input_registers_store.setValues(10, [nueva_temp])
                        
                        # Humedad con variación
                        hum_actual = self.input_registers_store.getValues(11, 1)[0]
                        nueva_hum = max(30, min(80, hum_actual + random.randint(-5, 5)))
                        self.input_registers_store.setValues(11, [nueva_hum])
                        
                    # Dormir 5 segundos
                    self.detener_actualizador.wait(5)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error actualizando datos: {e}")
                    self.detener_actualizador.wait(5)
                    
        self.hilo_actualizador = threading.Thread(target=_actualizar_datos_periodicamente, daemon=True)
        self.hilo_actualizador.start()
        
    def desconectar(self) -> ResultadoOperacion:
        """Detener servidor Modbus TCP."""
        try:
            self.servidor_activo = False
            self.detener_actualizador.set()
            
            # Detener loop asyncio si existe
            if self.loop_asyncio and self.loop_asyncio.is_running():
                self.loop_asyncio.call_soon_threadsafe(self.loop_asyncio.stop)
                
            # Esperar que terminen los hilos
            if self.hilo_servidor and self.hilo_servidor.is_alive():
                self.hilo_servidor.join(timeout=3)
                
            if self.hilo_actualizador and self.hilo_actualizador.is_alive():
                self.hilo_actualizador.join(timeout=2)
                
            self.cambiar_estado(EstadoProtocolo.DESCONECTADO, "Servidor Modbus TCP detenido")
            self.logger.info("✅ Servidor Modbus TCP detenido")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje="Servidor Modbus TCP detenido exitosamente"
            )
            
        except Exception as e:
            self.manejar_error(e, "desconectar_servidor_tcp")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error deteniendo servidor: {str(e)}"
            )
            
    def verificar_conexion(self) -> bool:
        """Verificar si el servidor está activo."""
        return (self.servidor_activo and 
                self.hilo_servidor is not None and 
                self.hilo_servidor.is_alive())
                
    def actualizar_dato_sistema(self, nombre_dato: str, valor: Any):
        """
        Actualizar un dato específico del sistema en los registros.
        
        Args:
            nombre_dato: Nombre del dato
            valor: Nuevo valor
        """
        # Mapeo de nombres a direcciones de input registers
        mapeo_input = {
            'estado_general_sistema': 0,
            'tiempo_funcionamiento': 1,
            'numero_dispositivos_total': 2,
            'numero_dispositivos_online': 3,
            'numero_alarmas_activas': 4,
            'temperatura_promedio': 10,
            'humedad_promedio': 11,
            'estado_comunicacion_genetec': 6,
            'camaras_online': 21,
            'controladores_online': 31,
        }
        
        if nombre_dato in mapeo_input and self.input_registers_store:
            direccion = mapeo_input[nombre_dato]
            self.input_registers_store.setValues(direccion, [int(valor)])
            self.logger.debug(f"📊 Actualizado {nombre_dato} = {valor} en registro {direccion}")
            
    def agregar_callback_escritura(self, direccion: int, callback: Callable):
        """Agregar callback para escrituras en holding registers."""
        self.callbacks_escritura[direccion] = callback
        if self.holding_registers_store:
            self.holding_registers_store.callbacks[direccion] = callback
            
    def leer_datos(self, direccion: str, **kwargs) -> ResultadoOperacion:
        """Leer datos de los registros del servidor."""
        try:
            tipo = kwargs.get('tipo', 'input')
            direccion_int = int(direccion)
            
            if tipo == 'input' and self.input_registers_store:
                valor = self.input_registers_store.getValues(direccion_int, 1)[0]
            elif tipo == 'holding' and self.holding_registers_store:
                valor = self.holding_registers_store.getValues(direccion_int, 1)[0]
            else:
                return ResultadoOperacion(exitoso=False, mensaje=f"Tipo inválido: {tipo}")
                
            return ResultadoOperacion(exitoso=True, datos=valor)
            
        except Exception as e:
            return ResultadoOperacion(exitoso=False, mensaje=str(e))
            
    def escribir_datos(self, direccion: str, valor: Any, **kwargs) -> ResultadoOperacion:
        """Escribir datos en holding registers."""
        try:
            direccion_int = int(direccion)
            
            if self.holding_registers_store:
                self.holding_registers_store.setValues(direccion_int, [int(valor)])
                return ResultadoOperacion(exitoso=True, mensaje=f"Escrito {valor} en {direccion}")
            else:
                return ResultadoOperacion(exitoso=False, mensaje="Servidor no iniciado")
                
        except Exception as e:
            return ResultadoOperacion(exitoso=False, mensaje=str(e))

# Función de utilidad
def crear_servidor_modbus_tcp_real(configuracion: Dict[str, Any] = None) -> ServidorModbusTCPReal:
    """Crear servidor Modbus TCP real."""
    return ServidorModbusTCPReal(configuracion)

# Alias para compatibilidad
ServidorModbus = ServidorModbusTCPReal

if __name__ == "__main__":
    # Prueba del servidor TCP real
    print("=== PROBANDO SERVIDOR MODBUS TCP REAL ===")
    
    try:
        # Configuración de prueba
        config_prueba = {
            'ip': '127.0.0.1',  # Usar localhost para prueba
            'puerto': 5020,     # Puerto alternativo para prueba
            'timeout': 5,
            'id_esclavo': 1
        }
        
        servidor = crear_servidor_modbus_tcp_real(config_prueba)
        
        # Iniciar servidor
        resultado = servidor.conectar()
        print(f"✅ Servidor iniciado: {resultado.mensaje}")
        
        if resultado.exitoso:
            print("🔥 Servidor Modbus TCP escuchando en 127.0.0.1:5020")
            print("📡 Puedes conectarte con cualquier cliente Modbus")
            print("📊 Input Registers: 0-50 (datos del sistema)")
            print("⚙️  Holding Registers: 0-30 (comandos y configuración)")
            print("🔧 Escribe en registro 0 para enviar comandos")
            print("⏹️  Presiona Ctrl+C para detener")
            
            try:
                while True:
                    time.sleep(5)
                    # Mostrar algunas estadísticas
                    temp = servidor.leer_datos('10', tipo='input')
                    if temp.exitoso:
                        print(f"🌡️  Temperatura actual: {temp.datos/10.0}°C")
                        
            except KeyboardInterrupt:
                print("\n⏹️  Deteniendo servidor...")
                servidor.desconectar()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("✅ Prueba completada")