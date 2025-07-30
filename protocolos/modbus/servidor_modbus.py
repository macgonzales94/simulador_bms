"""
Servidor Modbus para Sistema BMS
===============================

Este módulo implementa un servidor Modbus TCP que permite a otros sistemas
conectarse al BMS para leer/escribir datos. Actúa como interfaz de datos
del sistema BMS hacia el exterior.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Importar librerías Modbus
from pymodbus.server.sync import StartTcpServer, StopServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

# Importar clases base
from protocolos.protocolo_base import ProtocoloBase, ResultadoOperacion, EstadoProtocolo
from configuracion.configuracion_protocolos import obtener_config_modbus
from utilidades.logger import obtener_logger_protocolo

class MapaRegistrosModbus:
    """
    Clase para manejar el mapeo de registros Modbus del BMS.
    Define la estructura de datos que se expondrá vía Modbus.
    """
    
    def __init__(self):
        """Inicializar mapa de registros."""
        
        # Registros de solo lectura (Input Registers) - Función 04
        self.input_registers = {
            # Estados del sistema (0-9)
            0: {'nombre': 'estado_general_sistema', 'descripcion': 'Estado general (0=Error, 1=OK, 2=Warning)'},
            1: {'nombre': 'tiempo_funcionamiento', 'descripcion': 'Tiempo funcionamiento en horas'},
            2: {'nombre': 'numero_dispositivos_total', 'descripcion': 'Total dispositivos configurados'},
            3: {'nombre': 'numero_dispositivos_online', 'descripcion': 'Dispositivos online'},
            4: {'nombre': 'numero_alarmas_activas', 'descripcion': 'Alarmas activas'},
            5: {'nombre': 'numero_eventos_dia', 'descripcion': 'Eventos del día'},
            6: {'nombre': 'estado_comunicacion_genetec', 'descripcion': 'Estado conexión Genetec (0=Offline, 1=Online)'},
            7: {'nombre': 'version_sistema_mayor', 'descripcion': 'Versión mayor del sistema'},
            8: {'nombre': 'version_sistema_menor', 'descripcion': 'Versión menor del sistema'},
            9: {'nombre': 'timestamp_ultima_actualizacion', 'descripcion': 'Timestamp última actualización'},
            
            # Sensores ambientales (10-19)
            10: {'nombre': 'temperatura_promedio', 'descripcion': 'Temperatura promedio x10 (ej: 235 = 23.5°C)'},
            11: {'nombre': 'humedad_promedio', 'descripcion': 'Humedad relativa promedio %'},
            12: {'nombre': 'presion_atmosferica', 'descripcion': 'Presión atmosférica x10 mbar'},
            13: {'nombre': 'calidad_aire', 'descripcion': 'Índice calidad aire (0-100)'},
            14: {'nombre': 'luminosidad', 'descripcion': 'Nivel luminosidad (0-100)'},
            15: {'nombre': 'ruido_db', 'descripcion': 'Nivel ruido en dB'},
            
            # Estados de cámaras (20-29)
            20: {'nombre': 'camaras_total', 'descripcion': 'Total cámaras configuradas'},
            21: {'nombre': 'camaras_online', 'descripcion': 'Cámaras online'},
            22: {'nombre': 'camaras_grabando', 'descripcion': 'Cámaras grabando'},
            23: {'nombre': 'camaras_alarma', 'descripcion': 'Cámaras en alarma'},
            24: {'nombre': 'espacio_disco_usado', 'descripcion': 'Espacio disco usado %'},
            25: {'nombre': 'bitrate_promedio', 'descripcion': 'Bitrate promedio Mbps x10'},
            
            # Estados de controladores (30-39)
            30: {'nombre': 'controladores_total', 'descripcion': 'Total controladores configurados'},
            31: {'nombre': 'controladores_online', 'descripcion': 'Controladores online'},
            32: {'nombre': 'puertas_total', 'descripcion': 'Total puertas configuradas'},
            33: {'nombre': 'puertas_abiertas', 'descripcion': 'Puertas actualmente abiertas'},
            34: {'nombre': 'eventos_acceso_dia', 'descripcion': 'Eventos de acceso del día'},
            35: {'nombre': 'tarjetas_activas', 'descripcion': 'Tarjetas de acceso activas'},
            
            # Gabinetes y UPS (40-49)
            40: {'nombre': 'ups_total', 'descripcion': 'Total UPS configurados'},
            41: {'nombre': 'ups_online', 'descripcion': 'UPS online'},
            42: {'nombre': 'ups_en_bateria', 'descripcion': 'UPS funcionando con batería'},
            43: {'nombre': 'carga_bateria_minima', 'descripcion': 'Carga batería mínima %'},
            44: {'nombre': 'temperatura_gabinete_max', 'descripcion': 'Temperatura máxima gabinetes x10'},
            45: {'nombre': 'ventiladores_activos', 'descripcion': 'Ventiladores activos'},
        }
        
        # Registros de lectura/escritura (Holding Registers) - Función 03/16
        self.holding_registers = {
            # Comandos y configuración (0-9)
            0: {'nombre': 'comando_sistema', 'descripcion': 'Comando sistema (1=Restart, 2=Stop, 3=Reset)'},
            1: {'nombre': 'nivel_log', 'descripcion': 'Nivel logging (1=DEBUG, 2=INFO, 3=WARNING, 4=ERROR)'},
            2: {'nombre': 'intervalo_polling', 'descripcion': 'Intervalo polling segundos'},
            3: {'nombre': 'timeout_dispositivos', 'descripcion': 'Timeout dispositivos segundos'},
            4: {'nombre': 'habilitar_alarmas', 'descripcion': 'Habilitar alarmas (0=No, 1=Sí)'},
            5: {'nombre': 'modo_debug', 'descripcion': 'Modo debug (0=No, 1=Sí)'},
            
            # Setpoints y límites (10-19)  
            10: {'nombre': 'temperatura_limite_superior', 'descripcion': 'Límite superior temperatura x10'},
            11: {'nombre': 'temperatura_limite_inferior', 'descripcion': 'Límite inferior temperatura x10'},
            12: {'nombre': 'humedad_limite_superior', 'descripcion': 'Límite superior humedad %'},
            13: {'nombre': 'humedad_limite_inferior', 'descripcion': 'Límite inferior humedad %'},
            14: {'nombre': 'presion_limite_superior', 'descripcion': 'Límite superior presión x10'},
            15: {'nombre': 'presion_limite_inferior', 'descripcion': 'Límite inferior presión x10'},
            
            # Control de dispositivos (20-29)
            20: {'nombre': 'forzar_actualizacion_camaras', 'descripcion': 'Forzar actualización cámaras (1=Ejecutar)'},
            21: {'nombre': 'forzar_actualizacion_controladores', 'descripcion': 'Forzar actualización controladores (1=Ejecutar)'},
            22: {'nombre': 'reiniciar_comunicacion_genetec', 'descripcion': 'Reiniciar comunicación Genetec (1=Ejecutar)'},
            23: {'nombre': 'habilitar_polling_continuo', 'descripcion': 'Polling continuo (0=No, 1=Sí)'},
        }
        
        # Coils (salidas digitales) - Función 01/05
        self.coils = {
            0: {'nombre': 'alarma_general', 'descripcion': 'Alarma general del sistema'},
            1: {'nombre': 'alarma_temperatura', 'descripcion': 'Alarma temperatura'},
            2: {'nombre': 'alarma_humedad', 'descripcion': 'Alarma humedad'},
            3: {'nombre': 'alarma_comunicacion', 'descripcion': 'Alarma comunicación'},
            4: {'nombre': 'alarma_dispositivos', 'descripcion': 'Alarma dispositivos offline'},
            5: {'nombre': 'modo_mantenimiento', 'descripcion': 'Modo mantenimiento activo'},
            6: {'nombre': 'backup_en_progreso', 'descripcion': 'Backup en progreso'},
        }
        
        # Discrete Inputs (entradas digitales) - Función 02
        self.discrete_inputs = {
            0: {'nombre': 'sistema_inicializado', 'descripcion': 'Sistema inicializado correctamente'},
            1: {'nombre': 'genetec_conectado', 'descripcion': 'Genetec conectado'},
            2: {'nombre': 'base_datos_disponible', 'descripcion': 'Base datos disponible'},
            3: {'nombre': 'interfaz_web_activa', 'descripcion': 'Interfaz web activa'},
            4: {'nombre': 'mqtt_broker_activo', 'descripcion': 'MQTT broker activo'},
            5: {'nombre': 'todas_camaras_ok', 'descripcion': 'Todas cámaras funcionando'},
            6: {'nombre': 'todos_controladores_ok', 'descripcion': 'Todos controladores funcionando'},
        }

class ServidorModbus(ProtocoloBase):
    """
    Servidor Modbus TCP para exponer datos del BMS.
    Permite que sistemas externos se conecten para leer/escribir datos.
    """
    
    def __init__(self, configuracion: Dict[str, Any] = None):
        """
        Inicializar servidor Modbus.
        
        Args:
            configuracion: Configuración específica (opcional)
        """
        # Obtener configuración
        if configuracion is None:
            self.config_modbus = obtener_config_modbus()
        else:
            self.config_modbus = configuracion
            
        # Inicializar clase base
        super().__init__("modbus_servidor", self.config_modbus.__dict__)
        
        # Mapa de registros
        self.mapa_registros = MapaRegistrosModbus()
        
        # Servidor y contexto
        self.servidor = None
        self.contexto_servidor = None
        self.hilo_servidor = None
        
        # Datos del servidor
        self.datos_sistema = {}
        self.callbacks_escritura = {}
        
        # Inicializar datos por defecto
        self._inicializar_datos_por_defecto()
        
        self.logger.info("Servidor Modbus inicializado")
        
    def _inicializar_datos_por_defecto(self):
        """Inicializar datos por defecto en los registros."""
        
        # Input Registers (solo lectura)
        self.input_registers_data = {
            0: 1,  # Estado general OK
            1: 0,  # Tiempo funcionamiento
            2: 0,  # Total dispositivos
            3: 0,  # Dispositivos online
            4: 0,  # Alarmas activas
            5: 0,  # Eventos día
            6: 0,  # Estado Genetec
            7: 1,  # Versión mayor
            8: 0,  # Versión menor
            9: int(time.time()),  # Timestamp
            
            # Sensores por defecto
            10: 250,  # 25.0°C
            11: 50,   # 50% humedad
            12: 10132, # 1013.2 mbar
            13: 80,   # Calidad aire
            14: 50,   # Luminosidad
            15: 40,   # Ruido dB
            
            # Cámaras por defecto
            20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0,
            
            # Controladores por defecto
            30: 0, 31: 0, 32: 0, 33: 0, 34: 0, 35: 0,
            
            # UPS por defecto
            40: 0, 41: 0, 42: 0, 43: 100, 44: 250, 45: 0
        }
        
        # Holding Registers (lectura/escritura)
        self.holding_registers_data = {
            0: 0,  # Sin comandos
            1: 2,  # Nivel INFO
            2: 5,  # Polling 5 segundos
            3: 30, # Timeout 30 segundos
            4: 1,  # Alarmas habilitadas
            5: 0,  # Debug deshabilitado
            
            # Setpoints por defecto
            10: 300,  # 30.0°C max
            11: 150,  # 15.0°C min
            12: 70,   # 70% humedad max
            13: 30,   # 30% humedad min
            14: 10200, # 1020.0 mbar max
            15: 10000, # 1000.0 mbar min
            
            # Control por defecto
            20: 0, 21: 0, 22: 0, 23: 1  # Polling continuo habilitado
        }
        
        # Coils (salidas digitales)
        self.coils_data = {
            0: False,  # Sin alarma general
            1: False,  # Sin alarma temperatura
            2: False,  # Sin alarma humedad  
            3: False,  # Sin alarma comunicación
            4: False,  # Sin alarma dispositivos
            5: False,  # Sin modo mantenimiento
            6: False   # Sin backup
        }
        
        # Discrete Inputs (entradas digitales)
        self.discrete_inputs_data = {
            0: True,   # Sistema inicializado
            1: False,  # Genetec no conectado
            2: True,   # BD disponible
            3: False,  # Web no activa
            4: False,  # MQTT no activo
            5: False,  # No todas cámaras OK
            6: False   # No todos controladores OK
        }
        
    def conectar(self) -> ResultadoOperacion:
        """
        Iniciar servidor Modbus TCP.
        
        Returns:
            ResultadoOperacion con el resultado del inicio
        """
        try:
            self.cambiar_estado(EstadoProtocolo.CONECTANDO, "Iniciando servidor Modbus")
            
            # Crear bloques de datos
            store = ModbusSlaveContext(
                di=ModbusSequentialDataBlock(0, [self.discrete_inputs_data.get(i, False) for i in range(100)]),
                co=ModbusSequentialDataBlock(0, [self.coils_data.get(i, False) for i in range(100)]),
                hr=ModbusSequentialDataBlock(0, [self.holding_registers_data.get(i, 0) for i in range(100)]),
                ir=ModbusSequentialDataBlock(0, [self.input_registers_data.get(i, 0) for i in range(100)]),
                zero_mode=True
            )
            
            # Contexto del servidor
            self.contexto_servidor = ModbusServerContext(slaves=store, single=True)
            
            # Información del dispositivo
            identidad = ModbusDeviceIdentification()
            identidad.VendorName = 'BMS Demo'
            identidad.ProductCode = 'BMS-001'
            identidad.VendorUrl = 'http://bms-demo.local'
            identidad.ProductName = 'Sistema BMS Demo'
            identidad.ModelName = 'BMS Demo v1.0'
            identidad.MajorMinorRevision = '1.0.0'
            
            # Iniciar servidor en hilo separado
            self.hilo_servidor = threading.Thread(
                target=self._ejecutar_servidor,
                args=(identidad,),
                daemon=True,
                name="ServidorModbus"
            )
            
            self.hilo_servidor.start()
            
            # Esperar un poco para verificar que inició
            time.sleep(1)
            
            if self.hilo_servidor.is_alive():
                self.cambiar_estado(EstadoProtocolo.CONECTADO, "Servidor Modbus iniciado")
                self.logger.info(f"Servidor Modbus iniciado en {self.config_modbus.ip}:{self.config_modbus.puerto}")
                
                return ResultadoOperacion(
                    exitoso=True,
                    mensaje=f"Servidor Modbus iniciado en puerto {self.config_modbus.puerto}"
                )
            else:
                self.cambiar_estado(EstadoProtocolo.ERROR, "Error al iniciar servidor")
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje="Error al iniciar servidor Modbus"
                )
                
        except Exception as e:
            self.cambiar_estado(EstadoProtocolo.ERROR, f"Excepción al iniciar: {str(e)}")
            self.manejar_error(e, "conectar_servidor")
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error iniciando servidor Modbus: {str(e)}"
            )
            
    def _ejecutar_servidor(self, identidad):
        """
        Ejecutar servidor Modbus en hilo separado.
        
        Args:
            identidad: Información de identificación del dispositivo
        """
        try:
            StartTcpServer(
                context=self.contexto_servidor,
                identity=identidad,
                address=(self.config_modbus.ip, self.config_modbus.puerto),
                defer_reactor_run=True
            )
        except Exception as e:
            self.logger.error(f"Error en servidor Modbus: {e}")
            self.cambiar_estado(EstadoProtocolo.ERROR, f"Error en servidor: {str(e)}")
            
    def desconectar(self) -> ResultadoOperacion:
        """
        Detener servidor Modbus.
        
        Returns:
            ResultadoOperacion con el resultado de la parada
        """
        try:
            if self.hilo_servidor and self.hilo_servidor.is_alive():
                # Detener servidor
                StopServer()
                
                # Esperar que termine el hilo
                self.hilo_servidor.join(timeout=5)
                
            self.cambiar_estado(EstadoProtocolo.DESCONECTADO, "Servidor Modbus detenido")
            self.logger.info("Servidor Modbus detenido")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje="Servidor Modbus detenido exitosamente"
            )
            
        except Exception as e:
            self.manejar_error(e, "desconectar_servidor")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error deteniendo servidor: {str(e)}"
            )
            
    def verificar_conexion(self) -> bool:
        """
        Verificar si el servidor está activo.
        
        Returns:
            True si está activo, False en caso contrario
        """
        return (self.hilo_servidor is not None and 
                self.hilo_servidor.is_alive() and 
                self.estado == EstadoProtocolo.CONECTADO)
                
    def leer_datos(self, direccion: str, **kwargs) -> ResultadoOperacion:
        """
        Leer datos de los registros del servidor.
        
        Args:
            direccion: Dirección del registro
            **kwargs: tipo_registro ('input', 'holding', 'coil', 'discrete')
            
        Returns:
            ResultadoOperacion con el valor leído
        """
        try:
            tipo_registro = kwargs.get('tipo_registro', 'input')
            direccion_int = int(direccion)
            
            if tipo_registro == 'input':
                valor = self.input_registers_data.get(direccion_int, 0)
            elif tipo_registro == 'holding':
                valor = self.holding_registers_data.get(direccion_int, 0)
            elif tipo_registro == 'coil':
                valor = self.coils_data.get(direccion_int, False)
            elif tipo_registro == 'discrete':
                valor = self.discrete_inputs_data.get(direccion_int, False)
            else:
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=f"Tipo de registro inválido: {tipo_registro}"
                )
                
            return ResultadoOperacion(
                exitoso=True,
                datos=valor,
                mensaje=f"Valor leído del registro {direccion}: {valor}"
            )
            
        except Exception as e:
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error leyendo registro {direccion}: {str(e)}"
            )
            
    def escribir_datos(self, direccion: str, valor: Any, **kwargs) -> ResultadoOperacion:
        """
        Escribir datos en los registros del servidor.
        
        Args:
            direccion: Dirección del registro
            valor: Valor a escribir
            **kwargs: tipo_registro ('holding', 'coil')
            
        Returns:
            ResultadoOperacion con el resultado de la escritura
        """
        try:
            tipo_registro = kwargs.get('tipo_registro', 'holding')
            direccion_int = int(direccion)
            
            if tipo_registro == 'holding':
                self.holding_registers_data[direccion_int] = int(valor)
                self._actualizar_contexto_servidor()
                
                # Ejecutar callback si existe
                if direccion_int in self.callbacks_escritura:
                    self.callbacks_escritura[direccion_int](direccion_int, valor)
                    
            elif tipo_registro == 'coil':
                self.coils_data[direccion_int] = bool(valor)
                self._actualizar_contexto_servidor()
                
            else:
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=f"Tipo de registro no escribible: {tipo_registro}"
                )
                
            self.logger.debug(f"Registro {direccion} ({tipo_registro}) escrito con valor {valor}")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Registro {direccion} escrito con valor {valor}"
            )
            
        except Exception as e:
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error escribiendo registro {direccion}: {str(e)}"
            )
            
    def actualizar_dato_sistema(self, nombre_dato: str, valor: Any):
        """
        Actualizar un dato específico del sistema.
        
        Args:
            nombre_dato: Nombre del dato a actualizar
            valor: Nuevo valor
        """
        try:
            # Buscar en qué registro está el dato
            for direccion, info in self.mapa_registros.input_registers.items():
                if info['nombre'] == nombre_dato:
                    self.input_registers_data[direccion] = valor
                    self._actualizar_contexto_servidor()
                    self.logger.debug(f"Actualizado {nombre_dato} = {valor}")
                    return
                    
            # Si no se encontró, guardarlo para uso futuro
            self.datos_sistema[nombre_dato] = valor
            
        except Exception as e:
            self.logger.error(f"Error actualizando dato {nombre_dato}: {e}")
            
    def _actualizar_contexto_servidor(self):
        """Actualizar contexto del servidor con los datos actuales."""
        if self.contexto_servidor:
            try:
                # Actualizar input registers
                for direccion, valor in self.input_registers_data.items():
                    self.contexto_servidor[0].setValues(4, direccion, [valor])
                    
                # Actualizar holding registers
                for direccion, valor in self.holding_registers_data.items():
                    self.contexto_servidor[0].setValues(3, direccion, [valor])
                    
                # Actualizar coils
                for direccion, valor in self.coils_data.items():
                    self.contexto_servidor[0].setValues(1, direccion, [valor])
                    
                # Actualizar discrete inputs
                for direccion, valor in self.discrete_inputs_data.items():
                    self.contexto_servidor[0].setValues(2, direccion, [valor])
                    
            except Exception as e:
                self.logger.error(f"Error actualizando contexto servidor: {e}")
                
    def agregar_callback_escritura(self, direccion: int, callback: callable):
        """
        Agregar callback para cuando se escriba en un registro.
        
        Args:
            direccion: Dirección del registro
            callback: Función a llamar (direccion, valor)
        """
        self.callbacks_escritura[direccion] = callback
        
    def obtener_mapa_registros(self) -> Dict[str, Any]:
        """
        Obtener información completa del mapa de registros.
        
        Returns:
            Diccionario con información de todos los registros
        """
        return {
            'input_registers': self.mapa_registros.input_registers,
            'holding_registers': self.mapa_registros.holding_registers,
            'coils': self.mapa_registros.coils,
            'discrete_inputs': self.mapa_registros.discrete_inputs
        }

# Función de utilidad para crear servidor
def crear_servidor_modbus(configuracion: Dict[str, Any] = None) -> ServidorModbus:
    """
    Crear y configurar servidor Modbus.
    
    Args:
        configuracion: Configuración personalizada (opcional)
        
    Returns:
        Servidor Modbus configurado
    """
    return ServidorModbus(configuracion)

if __name__ == "__main__":
    # Prueba del servidor Modbus
    print("Probando servidor Modbus...")
    
    servidor = crear_servidor_modbus()
    
    # Iniciar servidor
    resultado = servidor.conectar()
    print(f"Servidor iniciado: {resultado.exitoso} - {resultado.mensaje}")
    
    if resultado.exitoso:
        print("Servidor Modbus ejecutándose...")
        print("Presiona Ctrl+C para detener")
        
        try:
            # Simular actualización de datos
            import random
            contador = 0
            while True:
                time.sleep(5)
                contador += 1
                
                # Actualizar algunos datos de ejemplo
                servidor.actualizar_dato_sistema('temperatura_promedio', 200 + random.randint(-50, 50))
                servidor.actualizar_dato_sistema('numero_dispositivos_online', random.randint(0, 10))
                servidor.actualizar_dato_sistema('tiempo_funcionamiento', contador)
                
                print(f"Datos actualizados... ({contador})")
                
        except KeyboardInterrupt:
            print("\nDeteniendo servidor...")
            servidor.desconectar()
            
    print("✓ Prueba de servidor Modbus completada")