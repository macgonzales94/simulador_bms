"""
Servidor Modbus para Sistema BMS - Versión Final Simplificada
============================================================

Versión completamente simplificada que evita problemas de asyncio
y se enfoca en proporcionar datos simulados de forma estable.

Autor: Sistema BMS Demo
Versión: 1.0.3 - Final simplificado
"""

import threading
import time
import socket
from typing import Dict, Any, List, Optional
from datetime import datetime

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

class ServidorModbusSimple(ProtocoloBase):
    """
    Servidor Modbus TCP completamente simplificado para exponer datos del BMS.
    Esta versión evita PyModbus y solo simula la funcionalidad.
    """
    
    def __init__(self, configuracion: Dict[str, Any] = None):
        """
        Inicializar servidor Modbus simplificado.
        
        Args:
            configuracion: Configuración específica (opcional)
        """
        # Obtener configuración
        if configuracion is None:
            self.config_modbus = obtener_config_modbus()
        else:
            self.config_modbus = configuracion
            
        # Inicializar clase base
        super().__init__("modbus_servidor_simple", self.config_modbus.__dict__)
        
        # Mapa de registros
        self.mapa_registros = MapaRegistrosModbus()
        
        # Estado del servidor
        self.servidor_activo = False
        self.hilo_simulacion = None
        self.socket_servidor = None
        
        # Datos del servidor - solo mantenemos los registros en memoria
        self.input_registers_data = {}
        self.holding_registers_data = {}
        self.callbacks_escritura = {}
        
        # Inicializar datos por defecto
        self._inicializar_datos_por_defecto()
        
        self.logger.info("Servidor Modbus simplificado inicializado")
        
    def _inicializar_datos_por_defecto(self):
        """Inicializar datos por defecto en los registros."""
        
        # Input Registers (solo lectura)
        self.input_registers_data = {
            0: 1,  # Estado general OK
            1: 0,  # Tiempo funcionamiento
            2: 3,  # Total dispositivos
            3: 3,  # Dispositivos online
            4: 0,  # Alarmas activas
            5: 0,  # Eventos día
            6: 1,  # Estado Genetec online
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
            20: 1, 21: 1, 22: 1, 23: 0, 24: 45, 25: 150,
            
            # Controladores por defecto
            30: 1, 31: 1, 32: 1, 33: 0, 34: 15, 35: 50,
            
            # UPS por defecto
            40: 1, 41: 1, 42: 0, 43: 85, 44: 280, 45: 2
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
        
    def conectar(self) -> ResultadoOperacion:
        """
        Iniciar servidor Modbus simulado (solo verifica puerto).
        
        Returns:
            ResultadoOperacion con el resultado del inicio
        """
        try:
            self.cambiar_estado(EstadoProtocolo.CONECTANDO, "Iniciando servidor Modbus simulado")
            
            # Verificar que el puerto esté disponible
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_socket.bind((self.config_modbus.ip, self.config_modbus.puerto))
                test_socket.close()
                puerto_disponible = True
            except OSError:
                puerto_disponible = False
                
            if not puerto_disponible:
                self.logger.warning(f"Puerto {self.config_modbus.puerto} en uso, continuando en modo simulado")
            
            # Iniciar hilo de simulación
            self.servidor_activo = True
            self.hilo_simulacion = threading.Thread(
                target=self._bucle_simulacion,
                daemon=True,
                name="ServidorModbusSimple"
            )
            self.hilo_simulacion.start()
            
            # Simular un pequeño delay de inicio
            time.sleep(0.5)
            
            self.cambiar_estado(EstadoProtocolo.CONECTADO, "Servidor Modbus simulado iniciado")
            self.logger.info(f"Servidor Modbus simulado iniciado en puerto {self.config_modbus.puerto}")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Servidor Modbus simulado iniciado en puerto {self.config_modbus.puerto}"
            )
                
        except Exception as e:
            self.cambiar_estado(EstadoProtocolo.ERROR, f"Error al iniciar servidor: {str(e)}")
            self.manejar_error(e, "conectar_servidor")
            
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error iniciando servidor Modbus: {str(e)}"
            )
            
    def _bucle_simulacion(self):
        """Bucle principal de simulación del servidor."""
        contador = 0
        inicio_tiempo = time.time()
        
        while self.servidor_activo:
            try:
                contador += 1
                
                # Actualizar timestamp cada ciclo
                self.input_registers_data[9] = int(time.time())
                
                # Actualizar tiempo de funcionamiento en horas
                tiempo_funcionamiento = (time.time() - inicio_tiempo) / 3600
                self.input_registers_data[1] = int(tiempo_funcionamiento)
                
                # Simular cambios en datos cada 30 segundos
                if contador % 6 == 0:  # 6 ciclos * 5 segundos = 30 segundos
                    import random
                    
                    # Simular variaciones en temperatura
                    temp_base = 250  # 25.0°C
                    variacion = random.randint(-20, 20)  # ±2.0°C
                    self.input_registers_data[10] = max(150, min(350, temp_base + variacion))
                    
                    # Simular variaciones en humedad
                    hum_base = 50
                    variacion_hum = random.randint(-10, 10)
                    self.input_registers_data[11] = max(20, min(80, hum_base + variacion_hum))
                    
                    # Simular variaciones en presión
                    presion_base = 10132
                    variacion_presion = random.randint(-50, 50)
                    self.input_registers_data[12] = max(9800, min(10500, presion_base + variacion_presion))
                    
                # Actualizar otros valores ocasionalmente
                if contador % 12 == 0:  # Cada minuto
                    import random
                    # Simular eventos del día
                    self.input_registers_data[5] += random.randint(0, 2)
                    
                    # Simular uso de disco
                    self.input_registers_data[24] = min(95, self.input_registers_data[24] + random.randint(0, 1))
                    
                    # Simular eventos de acceso
                    self.input_registers_data[34] += random.randint(0, 3)
                
                # Dormir 5 segundos
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error en bucle de simulación: {e}")
                time.sleep(5)
                
    def desconectar(self) -> ResultadoOperacion:
        """
        Detener servidor Modbus simulado.
        
        Returns:
            ResultadoOperacion con el resultado de la parada
        """
        try:
            self.servidor_activo = False
            
            if self.socket_servidor:
                try:
                    self.socket_servidor.close()
                except:
                    pass
            
            if self.hilo_simulacion and self.hilo_simulacion.is_alive():
                self.hilo_simulacion.join(timeout=2)
                
            self.cambiar_estado(EstadoProtocolo.DESCONECTADO, "Servidor Modbus simulado detenido")
            self.logger.info("Servidor Modbus simulado detenido")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje="Servidor Modbus simulado detenido exitosamente"
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
        return (self.servidor_activo and 
                self.hilo_simulacion is not None and 
                self.hilo_simulacion.is_alive() and
                self.estado == EstadoProtocolo.CONECTADO)
                
    def leer_datos(self, direccion: str, **kwargs) -> ResultadoOperacion:
        """
        Leer datos de los registros del servidor.
        
        Args:
            direccion: Dirección del registro
            **kwargs: tipo_registro ('input', 'holding')
            
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
            **kwargs: tipo_registro ('holding')
            
        Returns:
            ResultadoOperacion con el resultado de la escritura
        """
        try:
            tipo_registro = kwargs.get('tipo_registro', 'holding')
            direccion_int = int(direccion)
            
            if tipo_registro == 'holding':
                self.holding_registers_data[direccion_int] = int(valor)
                
                # Ejecutar callback si existe
                if direccion_int in self.callbacks_escritura:
                    try:
                        self.callbacks_escritura[direccion_int](direccion_int, valor)
                    except Exception as e:
                        self.logger.error(f"Error en callback escritura: {e}")
                        
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
                    self.input_registers_data[direccion] = int(valor)
                    self.logger.debug(f"Actualizado {nombre_dato} = {valor}")
                    return
                    
        except Exception as e:
            self.logger.error(f"Error actualizando dato {nombre_dato}: {e}")
            
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
            'datos_actuales': {
                'input_registers': dict(self.input_registers_data),
                'holding_registers': dict(self.holding_registers_data)
            }
        }

# Alias para mantener compatibilidad
ServidorModbus = ServidorModbusSimple

# Función de utilidad para crear servidor
def crear_servidor_modbus(configuracion: Dict[str, Any] = None) -> ServidorModbusSimple:
    """
    Crear y configurar servidor Modbus.
    
    Args:
        configuracion: Configuración personalizada (opcional)
        
    Returns:
        Servidor Modbus configurado
    """
    return ServidorModbusSimple(configuracion)

if __name__ == "__main__":
    # Prueba del servidor Modbus
    print("Probando servidor Modbus simplificado...")
    
    try:
        servidor = crear_servidor_modbus()
        
        # Iniciar servidor
        resultado = servidor.conectar()
        print(f"Servidor iniciado: {resultado.exitoso} - {resultado.mensaje}")
        
        if resultado.exitoso:
            print("Servidor Modbus ejecutándose...")
            print("Presiona Ctrl+C para detener")
            
            try:
                # Mostrar algunos datos
                contador = 0
                while True:
                    time.sleep(10)
                    contador += 1
                    
                    # Leer algunos registros
                    temp = servidor.leer_datos('10')
                    humedad = servidor.leer_datos('11')
                    
                    print(f"Ciclo {contador}: Temp={temp.datos/10.0}°C, Humedad={humedad.datos}%")
                    
            except KeyboardInterrupt:
                print("\nDeteniendo servidor...")
                servidor.desconectar()
                
    except Exception as e:
        print(f"Error en prueba: {e}")
        
    print("✓ Prueba de servidor Modbus completada")