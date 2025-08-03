"""
Servidor Modbus TCP Real para Sistema BMS
========================================

Servidor Modbus TCP real usando pymodbus que expone datos del BMS
y permite comunicación bidireccional con Genetec u otros sistemas.

Autor: Sistema BMS Demo  
Versión: 2.0.0 - Servidor TCP Real
"""

import threading
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# PyModbus imports
try:
    from pymodbus.server.sync import StartTcpServer
    from pymodbus.device import ModbusDeviceIdentification
    from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
    from pymodbus.transaction import ModbusRtuFramer, ModbusSocketFramer
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
except ImportError as e:
    print(f"Error: pymodbus no está instalado: {e}")
    print("Instalar con: pip install pymodbus==3.4.1")
    raise

# Importar clases base del proyecto
from protocolos.protocolo_base import ProtocoloBase, ResultadoOperacion, EstadoProtocolo
from configuracion.configuracion_protocolos import obtener_config_modbus
from utilidades.logger import obtener_logger_protocolo

class MapaRegistrosBMSReal:
    """
    Mapa de registros Modbus real para el BMS.
    Define exactamente qué datos se exponen vía Modbus TCP.
    """
    
    def __init__(self):
        """Inicializar mapa de registros."""
        
        # Input Registers (Función 04) - Solo lectura
        self.input_registers = {
            # Estados del sistema (0-9)
            0: {'nombre': 'estado_general_sistema', 'descripcion': 'Estado general (0=Error, 1=OK, 2=Warning)', 'valor_inicial': 1},
            1: {'nombre': 'tiempo_funcionamiento', 'descripcion': 'Tiempo funcionamiento en horas', 'valor_inicial': 0},
            2: {'nombre': 'numero_dispositivos_total', 'descripcion': 'Total dispositivos configurados', 'valor_inicial': 3},
            3: {'nombre': 'numero_dispositivos_online', 'descripcion': 'Dispositivos online', 'valor_inicial': 3},
            4: {'nombre': 'numero_alarmas_activas', 'descripcion': 'Alarmas activas', 'valor_inicial': 0},
            5: {'nombre': 'numero_eventos_dia', 'descripcion': 'Eventos del día', 'valor_inicial': 0},
            6: {'nombre': 'estado_comunicacion_genetec', 'descripcion': 'Estado conexión Genetec (0=Offline, 1=Online)', 'valor_inicial': 1},
            7: {'nombre': 'version_sistema_mayor', 'descripcion': 'Versión mayor del sistema', 'valor_inicial': 1},
            8: {'nombre': 'version_sistema_menor', 'descripcion': 'Versión menor del sistema', 'valor_inicial': 0},
            9: {'nombre': 'timestamp_ultima_actualizacion', 'descripcion': 'Timestamp última actualización', 'valor_inicial': 0},
            
            # Sensores ambientales (10-19)
            10: {'nombre': 'temperatura_promedio', 'descripcion': 'Temperatura promedio x10 (ej: 235 = 23.5°C)', 'valor_inicial': 250},
            11: {'nombre': 'humedad_promedio', 'descripcion': 'Humedad relativa promedio %', 'valor_inicial': 50},
            12: {'nombre': 'presion_atmosferica', 'descripcion': 'Presión atmosférica x10 mbar', 'valor_inicial': 10132},
            13: {'nombre': 'calidad_aire', 'descripcion': 'Índice calidad aire (0-100)', 'valor_inicial': 80},
            14: {'nombre': 'luminosidad', 'descripcion': 'Nivel luminosidad (0-100)', 'valor_inicial': 50},
            15: {'nombre': 'ruido_db', 'descripcion': 'Nivel ruido en dB', 'valor_inicial': 40},
            
            # Estados de cámaras (20-29)
            20: {'nombre': 'camaras_total', 'descripcion': 'Total cámaras configuradas', 'valor_inicial': 1},
            21: {'nombre': 'camaras_online', 'descripcion': 'Cámaras online', 'valor_inicial': 1},
            22: {'nombre': 'camaras_grabando', 'descripcion': 'Cámaras grabando', 'valor_inicial': 1},
            23: {'nombre': 'camaras_alarma', 'descripcion': 'Cámaras en alarma', 'valor_inicial': 0},
            24: {'nombre': 'espacio_disco_usado', 'descripcion': 'Espacio disco usado %', 'valor_inicial': 45},
            25: {'nombre': 'bitrate_promedio', 'descripcion': 'Bitrate promedio Mbps x10', 'valor_inicial': 150},
            
            # Estados de controladores (30-39)
            30: {'nombre': 'controladores_total', 'descripcion': 'Total controladores configurados', 'valor_inicial': 1},
            31: {'nombre': 'controladores_online', 'descripcion': 'Controladores online', 'valor_inicial': 1},
            32: {'nombre': 'puertas_total', 'descripcion': 'Total puertas configuradas', 'valor_inicial': 1},
            33: {'nombre': 'puertas_abiertas', 'descripcion': 'Puertas actualmente abiertas', 'valor_inicial': 0},
            34: {'nombre': 'eventos_acceso_dia', 'descripcion': 'Eventos de acceso del día', 'valor_inicial': 15},
            35: {'nombre': 'tarjetas_activas', 'descripcion': 'Tarjetas de acceso activas', 'valor_inicial': 50},
            
            # Gabinetes y UPS (40-49)
            40: {'nombre': 'ups_total', 'descripcion': 'Total UPS configurados', 'valor_inicial': 1},
            41: {'nombre': 'ups_online', 'descripcion': 'UPS online', 'valor_inicial': 1},
            42: {'nombre': 'ups_en_bateria', 'descripcion': 'UPS funcionando con batería', 'valor_inicial': 0},
            43: {'nombre': 'carga_bateria_minima', 'descripcion': 'Carga batería mínima %', 'valor_inicial': 85},
            44: {'nombre': 'temperatura_gabinete_max', 'descripcion': 'Temperatura máxima gabinetes x10', 'valor_inicial': 280},
            45: {'nombre': 'ventiladores_activos', 'descripcion': 'Ventiladores activos', 'valor_inicial': 2},
        }
        
        # Holding Registers (Función 03/16) - Lectura/Escritura
        self.holding_registers = {
            # Comandos y configuración (0-9)
            0: {'nombre': 'comando_sistema', 'descripcion': 'Comando sistema (1=Restart, 2=Stop, 3=Reset)', 'valor_inicial': 0},
            1: {'nombre': 'nivel_log', 'descripcion': 'Nivel logging (1=DEBUG, 2=INFO, 3=WARNING, 4=ERROR)', 'valor_inicial': 2},
            2: {'nombre': 'intervalo_polling', 'descripcion': 'Intervalo polling segundos', 'valor_inicial': 5},
            3: {'nombre': 'timeout_dispositivos', 'descripcion': 'Timeout dispositivos segundos', 'valor_inicial': 30},
            4: {'nombre': 'habilitar_alarmas', 'descripcion': 'Habilitar alarmas (0=No, 1=Sí)', 'valor_inicial': 1},
            5: {'nombre': 'modo_debug', 'descripcion': 'Modo debug (0=No, 1=Sí)', 'valor_inicial': 0},
            
            # Setpoints y límites (10-19)  
            10: {'nombre': 'temperatura_limite_superior', 'descripcion': 'Límite superior temperatura x10', 'valor_inicial': 300},
            11: {'nombre': 'temperatura_limite_inferior', 'descripcion': 'Límite inferior temperatura x10', 'valor_inicial': 150},
            12: {'nombre': 'humedad_limite_superior', 'descripcion': 'Límite superior humedad %', 'valor_inicial': 70},
            13: {'nombre': 'humedad_limite_inferior', 'descripcion': 'Límite inferior humedad %', 'valor_inicial': 30},
            14: {'nombre': 'presion_limite_superior', 'descripcion': 'Límite superior presión x10', 'valor_inicial': 10200},
            15: {'nombre': 'presion_limite_inferior', 'descripcion': 'Límite inferior presión x10', 'valor_inicial': 10000},
            
            # Control de dispositivos (20-29)
            20: {'nombre': 'forzar_actualizacion_camaras', 'descripcion': 'Forzar actualización cámaras (1=Ejecutar)', 'valor_inicial': 0},
            21: {'nombre': 'forzar_actualizacion_controladores', 'descripcion': 'Forzar actualización controladores (1=Ejecutar)', 'valor_inicial': 0},
            22: {'nombre': 'reiniciar_comunicacion_genetec', 'descripcion': 'Reiniciar comunicación Genetec (1=Ejecutar)', 'valor_inicial': 0},
            23: {'nombre': 'habilitar_polling_continuo', 'descripcion': 'Polling continuo (0=No, 1=Sí)', 'valor_inicial': 1},
        }

class CallbackHandler:
    """
    Manejador de callbacks para escrituras en Holding Registers.
    Se ejecuta cuando Genetec u otros clientes escriben datos.
    """
    
    def __init__(self, servidor_bms):
        """Inicializar handler."""
        self.servidor_bms = servidor_bms
        self.logger = servidor_bms.logger
        
    def manejar_escritura(self, address: int, values: List[int]):
        """
        Callback ejecutado cuando se escribe en holding registers.
        
        Args:
            address: Dirección del registro escrito
            values: Lista de valores escritos
        """
        try:
            self.logger.info(f"📝 Escritura Modbus - Dirección: {address}, Valores: {values}")
            
            # Obtener información del registro
            registro_info = self.servidor_bms.mapa_registros.holding_registers.get(address, {})
            nombre_registro = registro_info.get('nombre', f'registro_{address}')
            
            self.logger.info(f"📝 Registro: {nombre_registro} - Descripción: {registro_info.get('descripcion', 'N/A')}")
            
            # Procesar comandos específicos
            if address == 0:  # comando_sistema
                self._procesar_comando_sistema(values[0])
            elif address == 1:  # nivel_log
                self._procesar_cambio_log(values[0])
            elif address == 2:  # intervalo_polling
                self._procesar_cambio_polling(values[0])
            elif address == 20:  # forzar_actualizacion_camaras
                if values[0] == 1:
                    self._forzar_actualizacion_camaras()
            elif address == 21:  # forzar_actualizacion_controladores
                if values[0] == 1:
                    self._forzar_actualizacion_controladores()
            elif address == 22:  # reiniciar_comunicacion_genetec
                if values[0] == 1:
                    self._reiniciar_comunicacion_genetec()
                    
        except Exception as e:
            self.logger.error(f"Error en callback escritura: {e}")
            
    def _procesar_comando_sistema(self, comando: int):
        """Procesar comando de sistema."""
        comandos = {1: 'RESTART', 2: 'STOP', 3: 'RESET'}
        nombre_comando = comandos.get(comando, f'DESCONOCIDO({comando})')
        
        self.logger.warning(f"🚨 COMANDO SISTEMA RECIBIDO: {nombre_comando}")
        
        if comando == 1:  # Restart
            self.logger.info("🔄 Comando RESTART - Reiniciando sistema...")
            # Aquí podrías implementar restart real
        elif comando == 2:  # Stop
            self.logger.info("🛑 Comando STOP - Deteniendo sistema...")
            # Aquí podrías implementar stop real
        elif comando == 3:  # Reset
            self.logger.info("🔄 Comando RESET - Reseteando estadísticas...")
            # Aquí podrías implementar reset de estadísticas
            
    def _procesar_cambio_log(self, nivel: int):
        """Procesar cambio de nivel de logging."""
        niveles = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'ERROR'}
        nombre_nivel = niveles.get(nivel, 'DESCONOCIDO')
        self.logger.info(f"📊 Cambio nivel logging a: {nombre_nivel}")
        
    def _procesar_cambio_polling(self, intervalo: int):
        """Procesar cambio de intervalo de polling."""
        if 1 <= intervalo <= 300:
            self.logger.info(f"⏱️  Cambio intervalo polling a: {intervalo} segundos")
            self.servidor_bms.intervalo_actualizacion = intervalo
        else:
            self.logger.warning(f"⚠️  Intervalo polling inválido: {intervalo}")
            
    def _forzar_actualizacion_camaras(self):
        """Forzar actualización de cámaras."""
        self.logger.info("📹 Forzando actualización de cámaras...")
        # Aquí podrías implementar actualización real de cámaras
        
    def _forzar_actualizacion_controladores(self):
        """Forzar actualización de controladores."""
        self.logger.info("🚪 Forzando actualización de controladores...")
        # Aquí podrías implementar actualización real de controladores
        
    def _reiniciar_comunicacion_genetec(self):
        """Reiniciar comunicación con Genetec."""
        self.logger.info("🔄 Reiniciando comunicación con Genetec...")
        # Aquí podrías implementar reinicio real de comunicación

class ServidorModbusTCPReal(ProtocoloBase):
    """
    Servidor Modbus TCP REAL usando pymodbus.
    Escucha en puerto TCP y responde a clientes Modbus reales.
    """
    
    def __init__(self, configuracion: Dict[str, Any] = None):
        """Inicializar servidor Modbus TCP real."""
        
        # Obtener configuración
        if configuracion is None:
            self.config_modbus = obtener_config_modbus()
        else:
            self.config_modbus = configuracion
            
        # Inicializar clase base
        super().__init__("modbus_tcp_servidor", self.config_modbus.__dict__)
        
        # Mapa de registros y datos
        self.mapa_registros = MapaRegistrosBMSReal()
        self.callback_handler = CallbackHandler(self)
        
        # Estado del servidor
        self.servidor_tcp = None
        self.servidor_activo = False
        self.hilo_servidor = None
        self.hilo_actualizacion = None
        self.intervalo_actualizacion = 5  # segundos
        
        # Datastore de pymodbus
        self.datastore = None
        self.context = None
        
        # Estadísticas
        self.estadisticas_modbus = {
            'lecturas_totales': 0,
            'escrituras_totales': 0,
            'errores_total': 0,
            'ultima_operacion': None,
            'clientes_conectados': 0
        }
        
        self._inicializar_datastore()
        
        self.logger.info("Servidor Modbus TCP real inicializado")
        
    def _inicializar_datastore(self):
        """Inicializar datastore de pymodbus con valores iniciales."""
        try:
            # Crear bloques de datos para Input Registers
            input_registers_valores = [0] * 100  # 100 registros
            for direccion, info in self.mapa_registros.input_registers.items():
                if direccion < 100:
                    input_registers_valores[direccion] = info['valor_inicial']
                    
            # Crear bloques de datos para Holding Registers  
            holding_registers_valores = [0] * 50  # 50 registros
            for direccion, info in self.mapa_registros.holding_registers.items():
                if direccion < 50:
                    holding_registers_valores[direccion] = info['valor_inicial']
            
            # Crear bloques de datos
            input_block = ModbusSequentialDataBlock(0, input_registers_valores)
            holding_block = ModbusSequentialDataBlock(0, holding_registers_valores)
            
            # Crear datastore
            self.datastore = ModbusSlaveContext(
                di=input_block,    # Discrete Inputs
                co=None,           # Coils 
                hr=holding_block,  # Holding Registers
                ir=input_block     # Input Registers
            )
            
            # Crear contexto del servidor
            self.context = ModbusServerContext(slaves=self.datastore, single=True)
            
            self.logger.info("✓ Datastore Modbus inicializado con valores por defecto")
            
        except Exception as e:
            self.logger.error(f"Error inicializando datastore: {e}")
            raise
            
    def conectar(self) -> ResultadoOperacion:
        """Iniciar servidor Modbus TCP real."""
        try:
            self.cambiar_estado(EstadoProtocolo.CONECTANDO, "Iniciando servidor Modbus TCP real")
            
            # Configurar identificación del dispositivo
            identity = ModbusDeviceIdentification()
            identity.VendorName = 'Sistema BMS Demo'
            identity.ProductCode = 'BMS'
            identity.VendorUrl = 'https://github.com/tu-usuario/sistema-bms-demo'
            identity.ProductName = 'BMS Demo Modbus Server'
            identity.ModelName = 'BMS-DEMO-V1'
            identity.MajorMinorRevision = '1.0.0'
            
            # Iniciar servidor TCP en hilo separado
            self.hilo_servidor = threading.Thread(
                target=self._ejecutar_servidor_tcp,
                args=(identity,),
                daemon=True,
                name="ModbusTCPServer"
            )
            
            self.servidor_activo = True
            self.hilo_servidor.start()
            
            # Esperar un poco para que el servidor se inicie
            time.sleep(1)
            
            # Iniciar hilo de actualización de datos
            self.hilo_actualizacion = threading.Thread(
                target=self._bucle_actualizacion_datos,
                daemon=True,
                name="ModbusDataUpdater"
            )
            self.hilo_actualizacion.start()
            
            self.cambiar_estado(EstadoProtocolo.CONECTADO, "Servidor Modbus TCP iniciado")
            
            self.logger.info(f"✓ Servidor Modbus TCP escuchando en {self.config_modbus.ip}:{self.config_modbus.puerto}")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Servidor Modbus TCP iniciado en {self.config_modbus.ip}:{self.config_modbus.puerto}"
            )
            
        except Exception as e:
            self.cambiar_estado(EstadoProtocolo.ERROR, f"Error iniciando servidor TCP: {str(e)}")
            self.manejar_error(e, "conectar_servidor_tcp")
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error iniciando servidor Modbus TCP: {str(e)}"
            )
            
    def _ejecutar_servidor_tcp(self, identity):
        """Ejecutar servidor TCP de pymodbus."""
        try:
            self.logger.info(f"🚀 Iniciando servidor TCP en {self.config_modbus.ip}:{self.config_modbus.puerto}")
            
            # Configurar callback para escrituras
            original_setValues = self.context[0].setValues
            
            def callback_escritura(fx, address, values):
                """Callback personalizado para escrituras."""
                try:
                    # Ejecutar escritura original
                    resultado = original_setValues(fx, address, values)
                    
                    # Si es holding register (fx=3), ejecutar callback
                    if fx == 3:  # Holding registers
                        self.callback_handler.manejar_escritura(address, values)
                        self.estadisticas_modbus['escrituras_totales'] += 1
                        self.estadisticas_modbus['ultima_operacion'] = datetime.now()
                        
                    return resultado
                    
                except Exception as e:
                    self.logger.error(f"Error en callback escritura: {e}")
                    self.estadisticas_modbus['errores_total'] += 1
                    raise
                    
            # Reemplazar método setValues con callback
            self.context[0].setValues = callback_escritura
            
            # Iniciar servidor TCP
            StartTcpServer(
                context=self.context,
                identity=identity,
                address=(self.config_modbus.ip, self.config_modbus.puerto),
                framer=ModbusSocketFramer,
                ignore_missing_slaves=True
            )
            
        except Exception as e:
            self.logger.error(f"Error en servidor TCP: {e}")
            self.servidor_activo = False
            
    def _bucle_actualizacion_datos(self):
        """Bucle que actualiza datos en tiempo real."""
        contador = 0
        inicio_tiempo = time.time()
        
        while self.servidor_activo:
            try:
                contador += 1
                
                # Actualizar timestamp
                timestamp_actual = int(time.time())
                self._actualizar_input_register(9, timestamp_actual)
                
                # Actualizar tiempo de funcionamiento
                tiempo_funcionamiento = int((time.time() - inicio_tiempo) / 3600)
                self._actualizar_input_register(1, tiempo_funcionamiento)
                
                # Simular cambios en sensores cada 30 segundos
                if contador % 6 == 0:  # 6 * 5 segundos = 30 segundos
                    import random
                    
                    # Temperatura con variación
                    temp_base = 250  # 25.0°C
                    variacion = random.randint(-20, 20)  # ±2.0°C
                    nueva_temp = max(150, min(350, temp_base + variacion))
                    self._actualizar_input_register(10, nueva_temp)
                    
                    # Humedad con variación
                    hum_base = 50
                    variacion_hum = random.randint(-10, 10)
                    nueva_hum = max(20, min(80, hum_base + variacion_hum))
                    self._actualizar_input_register(11, nueva_hum)
                    
                    # Presión con variación
                    presion_base = 10132
                    variacion_presion = random.randint(-50, 50)
                    nueva_presion = max(9800, min(10500, presion_base + variacion_presion))
                    self._actualizar_input_register(12, nueva_presion)
                    
                # Actualizar otros valores ocasionalmente
                if contador % 12 == 0:  # Cada minuto
                    import random
                    
                    # Eventos del día
                    eventos_actuales = self._leer_input_register(5)
                    self._actualizar_input_register(5, eventos_actuales + random.randint(0, 2))
                    
                    # Uso de disco
                    disco_actual = self._leer_input_register(24)
                    self._actualizar_input_register(24, min(95, disco_actual + random.randint(0, 1)))
                    
                    # Eventos de acceso
                    accesos_actuales = self._leer_input_register(34)
                    self._actualizar_input_register(34, accesos_actuales + random.randint(0, 3))
                
                # Dormir según intervalo configurado
                time.sleep(self.intervalo_actualizacion)
                
            except Exception as e:
                self.logger.error(f"Error en bucle actualización: {e}")
                time.sleep(5)
                
    def _actualizar_input_register(self, direccion: int, valor: int):
        """Actualizar valor en Input Register."""
        try:
            if self.datastore:
                self.datastore.setValues(4, direccion, [valor])  # fx=4 = Input Registers
                self.estadisticas_modbus['lecturas_totales'] += 1
        except Exception as e:
            self.logger.error(f"Error actualizando input register {direccion}: {e}")
            
    def _leer_input_register(self, direccion: int) -> int:
        """Leer valor de Input Register."""
        try:
            if self.datastore:
                valores = self.datastore.getValues(4, direccion, 1)  # fx=4 = Input Registers
                return valores[0] if valores else 0
            return 0
        except Exception as e:
            self.logger.error(f"Error leyendo input register {direccion}: {e}")
            return 0
            
    def actualizar_dato_sistema(self, nombre_dato: str, valor: Any):
        """Actualizar dato del sistema por nombre."""
        try:
            # Buscar en input registers
            for direccion, info in self.mapa_registros.input_registers.items():
                if info['nombre'] == nombre_dato:
                    self._actualizar_input_register(direccion, int(valor))
                    self.logger.debug(f"✓ Actualizado {nombre_dato} = {valor}")
                    return
                    
            self.logger.warning(f"⚠️  Dato no encontrado: {nombre_dato}")
            
        except Exception as e:
            self.logger.error(f"Error actualizando dato {nombre_dato}: {e}")
            
    def desconectar(self) -> ResultadoOperacion:
        """Detener servidor Modbus TCP."""
        try:
            self.servidor_activo = False
            
            # Dar tiempo para que los hilos terminen
            if self.hilo_actualizacion and self.hilo_actualizacion.is_alive():
                self.hilo_actualizacion.join(timeout=2)
                
            if self.hilo_servidor and self.hilo_servidor.is_alive():
                self.hilo_servidor.join(timeout=2)
                
            self.cambiar_estado(EstadoProtocolo.DESCONECTADO, "Servidor Modbus TCP detenido")
            self.logger.info("✓ Servidor Modbus TCP detenido")
            
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
                self.hilo_servidor.is_alive() and
                self.estado == EstadoProtocolo.CONECTADO)
                
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas del servidor."""
        stats = super().obtener_estadisticas()
        stats.update(self.estadisticas_modbus)
        return stats
        
    def obtener_mapa_registros(self) -> Dict[str, Any]:
        """Obtener mapa completo de registros."""
        return {
            'input_registers': self.mapa_registros.input_registers,
            'holding_registers': self.mapa_registros.holding_registers,
            'estadisticas': self.obtener_estadisticas()
        }

# Alias para compatibilidad
ServidorModbus = ServidorModbusTCPReal

def crear_servidor_modbus_real(configuracion: Dict[str, Any] = None) -> ServidorModbusTCPReal:
    """Crear servidor Modbus TCP real."""
    return ServidorModbusTCPReal(configuracion)

if __name__ == "__main__":
    # Prueba del servidor Modbus TCP real
    print("🚀 Probando Servidor Modbus TCP Real...")
    
    try:
        # Crear servidor
        servidor = crear_servidor_modbus_real()
        
        # Iniciar servidor
        resultado = servidor.conectar()
        print(f"Servidor iniciado: {resultado.exitoso} - {resultado.mensaje}")
        
        if resultado.exitoso:
            print("✓ Servidor Modbus TCP ejecutándose...")
            print(f"✓ Escuchando en {servidor.config_modbus.ip}:{servidor.config_modbus.puerto}")
            print("✓ Presiona Ctrl+C para detener")
            print("✓ Puedes conectar con cualquier cliente Modbus TCP")
            print()
            print("📋 Registros disponibles:")
            print("   - Input Registers (Función 04): 0-45 (solo lectura)")
            print("   - Holding Registers (Función 03/16): 0-23 (lectura/escritura)")
            print()
            
            try:
                contador = 0
                while True:
                    time.sleep(10)
                    contador += 1
                    
                    # Mostrar algunas estadísticas
                    stats = servidor.obtener_estadisticas()
                    print(f"Ciclo {contador}:")
                    print(f"  ├─ Lecturas: {stats.get('lecturas_totales', 0)}")
                    print(f"  ├─ Escrituras: {stats.get('escrituras_totales', 0)}")
                    print(f"  ├─ Errores: {stats.get('errores_total', 0)}")
                    
                    # Mostrar algunos valores actuales
                    temp = servidor._leer_input_register(10)
                    humedad = servidor._leer_input_register(11)
                    print(f"  ├─ Temperatura: {temp/10.0}°C")
                    print(f"  └─ Humedad: {humedad}%")
                    print()
                    
            except KeyboardInterrupt:
                print("\n🛑 Deteniendo servidor...")
                resultado_stop = servidor.desconectar()
                print(f"Servidor detenido: {resultado_stop.mensaje}")
                
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
        
    print("✓ Prueba completada")