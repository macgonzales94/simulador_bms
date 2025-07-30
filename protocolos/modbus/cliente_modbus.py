"""
Cliente Modbus para Sistema BMS
==============================

Este módulo implementa el cliente Modbus TCP/RTU para comunicación con dispositivos
que soporten el protocolo Modbus. Se conecta principalmente con el servidor Genetec
que ya tiene configurados los dispositivos físicos.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

from typing import Dict, Any, List, Optional, Union
import time
from datetime import datetime

# Importar librerías Modbus
from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException, ConnectionException
from pymodbus.pdu import ExceptionResponse

# Importar clases base
from protocolos.protocolo_base import ProtocoloBase, ResultadoOperacion, EstadoProtocolo
from configuracion.configuracion_protocolos import obtener_config_modbus
from utilidades.logger import obtener_logger_protocolo

class TipoFuncionModbus:
    """Constantes para funciones Modbus."""
    LEER_COILS = 1                      # 0x01
    LEER_DISCRETE_INPUTS = 2            # 0x02  
    LEER_HOLDING_REGISTERS = 3          # 0x03
    LEER_INPUT_REGISTERS = 4            # 0x04
    ESCRIBIR_SINGLE_COIL = 5            # 0x05
    ESCRIBIR_SINGLE_REGISTER = 6        # 0x06
    ESCRIBIR_MULTIPLE_COILS = 15        # 0x0F
    ESCRIBIR_MULTIPLE_REGISTERS = 16    # 0x10

class ClienteModbus(ProtocoloBase):
    """
    Cliente Modbus TCP/RTU para comunicación con dispositivos BMS.
    Extiende ProtocoloBase con funcionalidades específicas de Modbus.
    """
    
    def __init__(self, configuracion: Dict[str, Any] = None):
        """
        Inicializar cliente Modbus.
        
        Args:
            configuracion: Configuración específica (opcional, usa la global por defecto)
        """
        # Obtener configuración
        if configuracion is None:
            self.config_modbus = obtener_config_modbus()
        else:
            self.config_modbus = configuracion
            
        # Inicializar clase base
        super().__init__("modbus", self.config_modbus.__dict__)
        
        # Cliente Modbus
        self.cliente = None
        self.tipo_conexion = "tcp"  # tcp o rtu
        
        # Cache de datos
        self.cache_datos = {}
        self.tiempo_cache = {}
        self.duracion_cache = 5  # segundos
        
        # Registros específicos para BMS
        self.registros_bms = {
            'estado_sistema': 0,
            'temperatura': 1,
            'humedad': 2,
            'presion': 3,
            'estado_camaras': 10,
            'estado_controladores': 20,
            'alarmas_activas': 30,
            'eventos_recientes': 40
        }
        
        self.logger.info("Cliente Modbus inicializado")
        
    def conectar(self) -> ResultadoOperacion:
        """
        Conectar al servidor Modbus (Genetec o dispositivo directo).
        
        Returns:
            ResultadoOperacion con el resultado de la conexión
        """
        inicio_tiempo = time.time()
        
        try:
            self.cambiar_estado(EstadoProtocolo.CONECTANDO, "Iniciando conexión Modbus")
            
            # Crear cliente TCP por defecto
            self.cliente = ModbusTcpClient(
                host=self.config_modbus.ip,
                port=self.config_modbus.puerto,
                timeout=self.config_modbus.timeout
            )
            
            # Intentar conexión
            conectado = self.cliente.connect()
            
            if conectado:
                self.cambiar_estado(EstadoProtocolo.CONECTADO, "Conexión Modbus establecida")
                self.estadisticas['tiempo_conexion'] = datetime.now()
                
                # Verificar comunicación con lectura de test
                resultado_test = self._probar_comunicacion()
                if not resultado_test.exitoso:
                    self.logger.warning(f"Advertencia en prueba de comunicación: {resultado_test.mensaje}")
                
                tiempo_respuesta = time.time() - inicio_tiempo
                self.actualizar_estadisticas(True, tiempo_respuesta)
                
                self.logger.info(f"Conectado a Modbus TCP {self.config_modbus.ip}:{self.config_modbus.puerto}")
                
                return ResultadoOperacion(
                    exitoso=True,
                    mensaje="Conexión Modbus establecida exitosamente",
                    tiempo_respuesta=tiempo_respuesta
                )
            else:
                self.cambiar_estado(EstadoProtocolo.ERROR, "Error al conectar Modbus")
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=f"No se pudo conectar a {self.config_modbus.ip}:{self.config_modbus.puerto}"
                )
                
        except Exception as e:
            self.cambiar_estado(EstadoProtocolo.ERROR, f"Excepción en conexión: {str(e)}")
            self.manejar_error(e, "conectar")
            
            tiempo_respuesta = time.time() - inicio_tiempo
            self.actualizar_estadisticas(False, tiempo_respuesta)
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error de conexión Modbus: {str(e)}",
                tiempo_respuesta=tiempo_respuesta
            )
            
    def desconectar(self) -> ResultadoOperacion:
        """
        Desconectar del servidor Modbus.
        
        Returns:
            ResultadoOperacion con el resultado de la desconexión
        """
        try:
            if self.cliente and self.cliente.is_socket_open():
                self.cliente.close()
                
            self.cambiar_estado(EstadoProtocolo.DESCONECTADO, "Desconectado de Modbus")
            self.logger.info("Desconectado de servidor Modbus")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje="Desconectado exitosamente"
            )
            
        except Exception as e:
            self.manejar_error(e, "desconectar")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error al desconectar: {str(e)}"
            )
            
    def verificar_conexion(self) -> bool:
        """
        Verificar si la conexión Modbus está activa.
        
        Returns:
            True si está conectado, False en caso contrario
        """
        try:
            if not self.cliente:
                return False
                
            # Verificar socket
            if not self.cliente.is_socket_open():
                return False
                
            # Hacer lectura rápida de test
            resultado = self.leer_holding_registers(0, 1)
            return resultado.exitoso
            
        except Exception:
            return False
            
    def _probar_comunicacion(self) -> ResultadoOperacion:
        """
        Probar comunicación básica con el servidor.
        
        Returns:
            ResultadoOperacion con el resultado de la prueba
        """
        try:
            # Intentar leer el primer registro de estado
            resultado = self.leer_holding_registers(0, 1)
            
            if resultado.exitoso:
                self.logger.debug("Prueba de comunicación exitosa")
                return ResultadoOperacion(
                    exitoso=True,
                    mensaje="Comunicación verificada",
                    datos=resultado.datos
                )
            else:
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje="No se pudo verificar comunicación"
                )
                
        except Exception as e:
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error en prueba de comunicación: {str(e)}"
            )
            
    def leer_datos(self, direccion: str, **kwargs) -> ResultadoOperacion:
        """
        Leer datos usando nombre lógico o dirección numérica.
        
        Args:
            direccion: Nombre del registro o dirección numérica
            **kwargs: cantidad, tipo_registro, id_esclavo
            
        Returns:
            ResultadoOperacion con los datos leídos
        """
        # Convertir nombre lógico a dirección numérica
        if direccion in self.registros_bms:
            direccion_numerica = self.registros_bms[direccion]
        else:
            try:
                direccion_numerica = int(direccion)
            except ValueError:
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=f"Dirección inválida: {direccion}"
                )
        
        # Leer holding registers por defecto
        return self.leer_holding_registers(
            direccion_numerica,
            kwargs.get('cantidad', 1),
            kwargs.get('id_esclavo', self.config_modbus.id_esclavo)
        )
        
    def escribir_datos(self, direccion: str, valor: Any, **kwargs) -> ResultadoOperacion:
        """
        Escribir datos usando nombre lógico o dirección numérica.
        
        Args:
            direccion: Nombre del registro o dirección numérica
            valor: Valor a escribir
            **kwargs: id_esclavo, tipo_registro
            
        Returns:
            ResultadoOperacion con el resultado de la escritura
        """
        # Convertir nombre lógico a dirección numérica
        if direccion in self.registros_bms:
            direccion_numerica = self.registros_bms[direccion]
        else:
            try:
                direccion_numerica = int(direccion)
            except ValueError:
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=f"Dirección inválida: {direccion}"
                )
        
        # Escribir holding register por defecto
        return self.escribir_holding_register(
            direccion_numerica,
            valor,
            kwargs.get('id_esclavo', self.config_modbus.id_esclavo)
        )
        
    def leer_holding_registers(self, direccion: int, cantidad: int = 1, id_esclavo: int = None) -> ResultadoOperacion:
        """
        Leer registros de retención (Holding Registers).
        
        Args:
            direccion: Dirección inicial del registro
            cantidad: Cantidad de registros a leer
            id_esclavo: ID del dispositivo esclavo
            
        Returns:
            ResultadoOperacion con los valores leídos
        """
        inicio_tiempo = time.time()
        id_esclavo = id_esclavo or self.config_modbus.id_esclavo
        
        # Verificar cache
        clave_cache = f"holding_{direccion}_{cantidad}_{id_esclavo}"
        if self._datos_en_cache(clave_cache):
            return self.cache_datos[clave_cache]
        
        try:
            if not self.verificar_conexion():
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje="No hay conexión Modbus activa"
                )
            
            # Realizar lectura
            respuesta = self.cliente.read_holding_registers(
                address=direccion,
                count=cantidad,
                unit=id_esclavo
            )
            
            tiempo_respuesta = time.time() - inicio_tiempo
            
            if respuesta.isError():
                error_msg = f"Error Modbus: {respuesta}"
                self.logger.error(error_msg)
                self.actualizar_estadisticas(False, tiempo_respuesta)
                
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=error_msg,
                    tiempo_respuesta=tiempo_respuesta
                )
            else:
                # Procesar datos exitosos
                valores = respuesta.registers
                self.actualizar_estadisticas(True, tiempo_respuesta)
                
                resultado = ResultadoOperacion(
                    exitoso=True,
                    datos=valores,
                    mensaje=f"Leídos {cantidad} registros desde {direccion}",
                    tiempo_respuesta=tiempo_respuesta
                )
                
                # Guardar en cache
                self._guardar_en_cache(clave_cache, resultado)
                
                self.logger.debug(f"Holding registers leídos: {direccion}={valores}")
                
                # Emitir evento
                self.emitir_evento(
                    "lectura_exitosa",
                    f"esclavo_{id_esclavo}",
                    f"Lectura exitosa de {cantidad} registros",
                    {
                        'direccion': direccion,
                        'cantidad': cantidad,
                        'valores': valores,
                        'tiempo_respuesta': tiempo_respuesta
                    }
                )
                
                return resultado
                
        except Exception as e:
            tiempo_respuesta = time.time() - inicio_tiempo
            self.manejar_error(e, f"leer_holding_registers({direccion}, {cantidad})")
            self.actualizar_estadisticas(False, tiempo_respuesta)
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Excepción en lectura: {str(e)}",
                tiempo_respuesta=tiempo_respuesta
            )
            
    def escribir_holding_register(self, direccion: int, valor: int, id_esclavo: int = None) -> ResultadoOperacion:
        """
        Escribir un registro de retención.
        
        Args:
            direccion: Dirección del registro
            valor: Valor a escribir
            id_esclavo: ID del dispositivo esclavo
            
        Returns:
            ResultadoOperacion con el resultado de la escritura
        """
        inicio_tiempo = time.time()
        id_esclavo = id_esclavo or self.config_modbus.id_esclavo
        
        try:
            if not self.verificar_conexion():
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje="No hay conexión Modbus activa"
                )
            
            # Realizar escritura
            respuesta = self.cliente.write_register(
                address=direccion,
                value=valor,
                unit=id_esclavo
            )
            
            tiempo_respuesta = time.time() - inicio_tiempo
            
            if respuesta.isError():
                error_msg = f"Error en escritura Modbus: {respuesta}"
                self.logger.error(error_msg)
                self.actualizar_estadisticas(False, tiempo_respuesta)
                
                return ResultadoOperacion(
                    exitoso=False,
                    mensaje=error_msg,
                    tiempo_respuesta=tiempo_respuesta
                )
            else:
                self.actualizar_estadisticas(True, tiempo_respuesta)
                
                self.logger.debug(f"Registro escrito: {direccion}={valor}")
                
                # Emitir evento
                self.emitir_evento(
                    "escritura_exitosa",
                    f"esclavo_{id_esclavo}",
                    f"Escritura exitosa en registro {direccion}",
                    {
                        'direccion': direccion,
                        'valor': valor,
                        'tiempo_respuesta': tiempo_respuesta
                    }
                )
                
                # Limpiar cache relacionado
                self._limpiar_cache_direccion(direccion)
                
                return ResultadoOperacion(
                    exitoso=True,
                    mensaje=f"Registro {direccion} escrito con valor {valor}",
                    tiempo_respuesta=tiempo_respuesta
                )
                
        except Exception as e:
            tiempo_respuesta = time.time() - inicio_tiempo
            self.manejar_error(e, f"escribir_holding_register({direccion}, {valor})")
            self.actualizar_estadisticas(False, tiempo_respuesta)
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Excepción en escritura: {str(e)}",
                tiempo_respuesta=tiempo_respuesta
            )
            
    def leer_estado_sistema_bms(self) -> ResultadoOperacion:
        """
        Leer estado general del sistema BMS desde Genetec.
        
        Returns:
            ResultadoOperacion con el estado del sistema
        """
        try:
            # Leer registros principales del BMS
            resultado_estado = self.leer_holding_registers(
                self.registros_bms['estado_sistema'], 
                10  # Leer bloque de estado
            )
            
            if resultado_estado.exitoso:
                valores = resultado_estado.datos
                
                # Interpretar datos según protocolo BMS
                estado_sistema = {
                    'estado_general': valores[0] if len(valores) > 0 else 0,
                    'temperatura': valores[1] / 10.0 if len(valores) > 1 else 0,  # Dividir por 10 para decimales
                    'humedad': valores[2] if len(valores) > 2 else 0,
                    'presion': valores[3] if len(valores) > 3 else 0,
                    'camaras_online': valores[4] if len(valores) > 4 else 0,
                    'controladores_online': valores[5] if len(valores) > 5 else 0,
                    'alarmas_activas': valores[6] if len(valores) > 6 else 0,
                    'timestamp': datetime.now()
                }
                
                return ResultadoOperacion(
                    exitoso=True,
                    datos=estado_sistema,
                    mensaje="Estado del sistema BMS obtenido exitosamente"
                )
            else:
                return resultado_estado
                
        except Exception as e:
            self.manejar_error(e, "leer_estado_sistema_bms")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error leyendo estado del sistema: {str(e)}"
            )
            
    def _datos_en_cache(self, clave: str) -> bool:
        """Verificar si los datos están en cache y son válidos."""
        if clave not in self.cache_datos:
            return False
            
        tiempo_cache = self.tiempo_cache.get(clave, datetime.min)
        tiempo_actual = datetime.now()
        
        return (tiempo_actual - tiempo_cache).total_seconds() < self.duracion_cache
        
    def _guardar_en_cache(self, clave: str, resultado: ResultadoOperacion):
        """Guardar resultado en cache."""
        self.cache_datos[clave] = resultado
        self.tiempo_cache[clave] = datetime.now()
        
    def _limpiar_cache_direccion(self, direccion: int):
        """Limpiar cache relacionado con una dirección."""
        claves_a_eliminar = []
        for clave in self.cache_datos.keys():
            if f"_{direccion}_" in clave:
                claves_a_eliminar.append(clave)
                
        for clave in claves_a_eliminar:
            del self.cache_datos[clave]
            del self.tiempo_cache[clave]

# Función de utilidad para crear cliente
def crear_cliente_modbus(configuracion: Dict[str, Any] = None) -> ClienteModbus:
    """
    Crear y configurar cliente Modbus.
    
    Args:
        configuracion: Configuración personalizada (opcional)
        
    Returns:
        Cliente Modbus configurado
    """
    return ClienteModbus(configuracion)

if __name__ == "__main__":
    # Prueba del cliente Modbus
    print("Probando cliente Modbus...")
    
    cliente = crear_cliente_modbus()
    
    # Probar conexión
    resultado_conexion = cliente.conectar()
    print(f"Conexión: {resultado_conexion.exitoso} - {resultado_conexion.mensaje}")
    
    if resultado_conexion.exitoso:
        # Probar lectura
        resultado_lectura = cliente.leer_estado_sistema_bms()
        print(f"Lectura: {resultado_lectura.exitoso} - {resultado_lectura.mensaje}")
        
        if resultado_lectura.exitoso:
            print(f"Datos: {resultado_lectura.datos}")
            
        # Desconectar
        cliente.desconectar()
        
    print("✓ Prueba de cliente Modbus completada")