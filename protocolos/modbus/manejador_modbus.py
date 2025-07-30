"""
Manejador Principal de Protocolo Modbus
======================================

Este módulo coordina las operaciones de cliente y servidor Modbus para el sistema BMS.
Actúa como interfaz principal para todas las operaciones Modbus del sistema.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import threading
import time
import schedule
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

# Importar componentes Modbus
from protocolos.modbus.cliente_modbus import ClienteModbus
from protocolos.modbus.servidor_modbus import ServidorModbus
from protocolos.protocolo_base import ResultadoOperacion, EstadoProtocolo, EventoProtocolo
from configuracion.configuracion_protocolos import obtener_config_modbus
from utilidades.logger import obtener_logger_protocolo

class ModoOperacionModbus(Enum):
    """Modos de operación del manejador Modbus."""
    SOLO_CLIENTE = "solo_cliente"
    SOLO_SERVIDOR = "solo_servidor"
    CLIENTE_SERVIDOR = "cliente_servidor"
    DESHABILITADO = "deshabilitado"

class EstadisticasModbus:
    """Clase para manejar estadísticas del protocolo Modbus."""
    
    def __init__(self):
        """Inicializar estadísticas."""
        self.reset()
        
    def reset(self):
        """Resetear todas las estadísticas."""
        self.inicio_operacion = datetime.now()
        self.lecturas_exitosas = 0
        self.lecturas_fallidas = 0
        self.escrituras_exitosas = 0
        self.escrituras_fallidas = 0
        self.reconexiones = 0
        self.tiempo_total_conectado = timedelta()
        self.tiempo_ultima_conexion = None
        self.errores_por_tipo = {}
        self.dispositivos_monitoreados = set()
        self.registro_mas_leido = {}
        
    def incrementar_lectura(self, exitosa: bool):
        """Incrementar contador de lecturas."""
        if exitosa:
            self.lecturas_exitosas += 1
        else:
            self.lecturas_fallidas += 1
            
    def incrementar_escritura(self, exitosa: bool):
        """Incrementar contador de escrituras."""
        if exitosa:
            self.escrituras_exitosas += 1
        else:
            self.escrituras_fallidas += 1
            
    def registrar_error(self, tipo_error: str):
        """Registrar un error por tipo."""
        if tipo_error not in self.errores_por_tipo:
            self.errores_por_tipo[tipo_error] = 0
        self.errores_por_tipo[tipo_error] += 1
        
    def obtener_resumen(self) -> Dict[str, Any]:
        """Obtener resumen de estadísticas."""
        tiempo_operacion = datetime.now() - self.inicio_operacion
        total_operaciones = (self.lecturas_exitosas + self.lecturas_fallidas + 
                           self.escrituras_exitosas + self.escrituras_fallidas)
        
        tasa_exito = 0
        if total_operaciones > 0:
            operaciones_exitosas = self.lecturas_exitosas + self.escrituras_exitosas
            tasa_exito = (operaciones_exitosas / total_operaciones) * 100
            
        return {
            'tiempo_operacion': str(tiempo_operacion),
            'total_operaciones': total_operaciones,
            'tasa_exito': round(tasa_exito, 2),
            'lecturas_exitosas': self.lecturas_exitosas,
            'lecturas_fallidas': self.lecturas_fallidas,
            'escrituras_exitosas': self.escrituras_exitosas,
            'escrituras_fallidas': self.escrituras_fallidas,
            'reconexiones': self.reconexiones,
            'dispositivos_monitoreados': len(self.dispositivos_monitoreados),
            'errores_por_tipo': self.errores_por_tipo
        }

class ManejadorModbus:
    """
    Manejador principal del protocolo Modbus para el sistema BMS.
    Coordina cliente y servidor Modbus y proporciona interfaz unificada.
    """
    
    def __init__(self, modo_operacion: ModoOperacionModbus = ModoOperacionModbus.CLIENTE_SERVIDOR):
        """
        Inicializar manejador Modbus.
        
        Args:
            modo_operacion: Modo de operación del manejador
        """
        self.modo_operacion = modo_operacion
        self.config_modbus = obtener_config_modbus()
        self.logger = obtener_logger_protocolo("modbus")
        
        # Componentes
        self.cliente = None
        self.servidor = None
        
        # Control de hilos
        self.hilo_polling = None
        self.hilo_servidor_datos = None
        self.detener_hilos = threading.Event()
        self.activo = False
        
        # Estadísticas
        self.estadisticas = EstadisticasModbus()
        
        # Callbacks
        self.callbacks_datos_recibidos = []
        self.callbacks_estado_cambiado = []
        self.callbacks_error = []
        
        # Cache de datos del sistema
        self.datos_sistema_cache = {}
        self.ultima_actualizacion_cache = datetime.now()
        
        # Configuración de polling
        self.dispositivos_polling = []
        self.intervalo_polling = self.config_modbus.intervalo_polling
        self.registros_monitoreados = [
            'estado_sistema', 'temperatura', 'humedad', 
            'estado_camaras', 'estado_controladores'
        ]
        
        self._inicializar_componentes()
        
    def _inicializar_componentes(self):
        """Inicializar componentes según el modo de operación."""
        try:
            if self.modo_operacion in [ModoOperacionModbus.SOLO_CLIENTE, ModoOperacionModbus.CLIENTE_SERVIDOR]:
                self.cliente = ClienteModbus()
                self.cliente.agregar_callback_evento(self._manejar_evento_cliente)
                self.cliente.agregar_callback_error(self._manejar_error_cliente)
                self.logger.info("Cliente Modbus inicializado")
                
            if self.modo_operacion in [ModoOperacionModbus.SOLO_SERVIDOR, ModoOperacionModbus.CLIENTE_SERVIDOR]:
                self.servidor = ServidorModbus()
                self.servidor.agregar_callback_evento(self._manejar_evento_servidor)
                self.servidor.agregar_callback_error(self._manejar_error_servidor)
                self._configurar_callbacks_servidor()
                self.logger.info("Servidor Modbus inicializado")
                
        except Exception as e:
            self.logger.error(f"Error inicializando componentes Modbus: {e}")
            raise
            
    def _configurar_callbacks_servidor(self):
        """Configurar callbacks del servidor para manejar escrituras."""
        if self.servidor:
            # Callback para comando de sistema
            self.servidor.agregar_callback_escritura(0, self._manejar_comando_sistema)
            
            # Callback para cambios de configuración
            self.servidor.agregar_callback_escritura(1, self._manejar_cambio_nivel_log)
            self.servidor.agregar_callback_escritura(2, self._manejar_cambio_intervalo_polling)
            
            # Callbacks para forzar actualizaciones
            self.servidor.agregar_callback_escritura(20, self._manejar_forzar_actualizacion_camaras)
            self.servidor.agregar_callback_escritura(21, self._manejar_forzar_actualizacion_controladores)
            self.servidor.agregar_callback_escritura(22, self._manejar_reiniciar_comunicacion_genetec)
            
    def iniciar(self) -> ResultadoOperacion:
        """
        Iniciar el manejador Modbus.
        
        Returns:
            ResultadoOperacion con el resultado del inicio
        """
        try:
            self.logger.info(f"Iniciando manejador Modbus en modo: {self.modo_operacion.value}")
            
            resultados = []
            
            # Iniciar cliente si está configurado
            if self.cliente:
                resultado_cliente = self.cliente.conectar()
                resultados.append(f"Cliente: {resultado_cliente.mensaje}")
                if not resultado_cliente.exitoso:
                    self.logger.warning(f"Cliente Modbus no pudo conectar: {resultado_cliente.mensaje}")
                else:
                    self.estadisticas.dispositivos_monitoreados.add("genetec_servidor")
                    
            # Iniciar servidor si está configurado
            if self.servidor:
                resultado_servidor = self.servidor.conectar()
                resultados.append(f"Servidor: {resultado_servidor.mensaje}")
                if not resultado_servidor.exitoso:
                    self.logger.error(f"Servidor Modbus no pudo iniciar: {resultado_servidor.mensaje}")
                    return resultado_servidor
                    
            # Iniciar hilos de trabajo
            self.activo = True
            self.detener_hilos.clear()
            
            if self.cliente:
                self._iniciar_polling_datos()
                
            if self.servidor:
                self._iniciar_actualizacion_servidor()
                
            self.logger.info("Manejador Modbus iniciado exitosamente")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Manejador Modbus iniciado: {'; '.join(resultados)}",
                datos={'modo': self.modo_operacion.value}
            )
            
        except Exception as e:
            self.logger.error(f"Error iniciando manejador Modbus: {e}")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error iniciando manejador: {str(e)}"
            )
            
    def detener(self) -> ResultadoOperacion:
        """
        Detener el manejador Modbus.
        
        Returns:
            ResultadoOperacion con el resultado de la parada
        """
        try:
            self.logger.info("Deteniendo manejador Modbus...")
            
            # Detener hilos
            self.activo = False
            self.detener_hilos.set()
            
            if self.hilo_polling and self.hilo_polling.is_alive():
                self.hilo_polling.join(timeout=5)
                
            if self.hilo_servidor_datos and self.hilo_servidor_datos.is_alive():
                self.hilo_servidor_datos.join(timeout=5)
                
            # Detener componentes
            resultados = []
            
            if self.cliente:
                resultado_cliente = self.cliente.desconectar()
                resultados.append(f"Cliente: {resultado_cliente.mensaje}")
                
            if self.servidor:
                resultado_servidor = self.servidor.desconectar()
                resultados.append(f"Servidor: {resultado_servidor.mensaje}")
                
            self.logger.info("Manejador Modbus detenido")
            
            return ResultadoOperacion(
                exitoso=True,
                mensaje=f"Manejador Modbus detenido: {'; '.join(resultados)}"
            )
            
        except Exception as e:
            self.logger.error(f"Error deteniendo manejador Modbus: {e}")
            return ResultadoOperacion(
                exitoso=False,
                mensaje=f"Error deteniendo manejador: {str(e)}"
            )
            
    def _iniciar_polling_datos(self):
        """Iniciar hilo de polling de datos desde Genetec."""
        if self.cliente:
            self.hilo_polling = threading.Thread(
                target=self._bucle_polling_datos,
                name="ModbusPolling",
                daemon=True
            )
            self.hilo_polling.start()
            self.logger.info(f"Polling de datos iniciado (intervalo: {self.intervalo_polling}s)")
            
    def _iniciar_actualizacion_servidor(self):
        """Iniciar hilo de actualización del servidor."""
        if self.servidor:
            self.hilo_servidor_datos = threading.Thread(
                target=self._bucle_actualizacion_servidor,
                name="ModbusServerUpdate",
                daemon=True
            )
            self.hilo_servidor_datos.start()
            self.logger.info("Actualización de servidor iniciada")
            
    def _bucle_polling_datos(self):
        """Bucle principal de polling de datos."""
        while self.activo and not self.detener_hilos.is_set():
            try:
                if self.cliente and self.cliente.verificar_conexion():
                    # Leer estado general del sistema BMS
                    resultado = self.cliente.leer_estado_sistema_bms()
                    
                    if resultado.exitoso:
                        self.estadisticas.incrementar_lectura(True)
                        self._procesar_datos_recibidos(resultado.datos)
                        self._notificar_datos_recibidos(resultado.datos)
                    else:
                        self.estadisticas.incrementar_lectura(False)
                        self.estadisticas.registrar_error("lectura_estado_sistema")
                        self.logger.warning(f"Error en polling: {resultado.mensaje}")
                        
                    # Leer registros específicos monitoreados
                    for registro in self.registros_monitoreados:
                        if self.detener_hilos.is_set():
                            break
                            
                        resultado_reg = self.cliente.leer_datos(registro)
                        if resultado_reg.exitoso:
                            self.estadisticas.incrementar_lectura(True)
                            # Actualizar cache
                            self.datos_sistema_cache[registro] = {
                                'valor': resultado_reg.datos,
                                'timestamp': datetime.now()
                            }
                        else:
                            self.estadisticas.incrementar_lectura(False)
                            
                else:
                    # Intentar reconectar
                    self.logger.info("Intentando reconectar cliente Modbus...")
                    if self.cliente:
                        resultado_reconexion = self.cliente.conectar()
                        if resultado_reconexion.exitoso:
                            self.estadisticas.reconexiones += 1
                            self.logger.info("Reconexión exitosa")
                        else:
                            self.logger.warning("Falló reconexión")
                            
            except Exception as e:
                self.logger.error(f"Error en bucle de polling: {e}")
                self.estadisticas.registrar_error("polling_general")
                
            # Esperar intervalo o señal de parada
            self.detener_hilos.wait(self.intervalo_polling)
            
    def _bucle_actualizacion_servidor(self):
        """Bucle de actualización del servidor con datos del sistema."""
        while self.activo and not self.detener_hilos.is_set():
            try:
                if self.servidor and self.servidor.verificar_conexion():
                    # Actualizar timestamp
                    self.servidor.actualizar_dato_sistema(
                        'timestamp_ultima_actualizacion', 
                        int(datetime.now().timestamp())
                    )
                    
                    # Actualizar tiempo de funcionamiento
                    tiempo_funcionamiento = (datetime.now() - self.estadisticas.inicio_operacion).total_seconds() / 3600
                    self.servidor.actualizar_dato_sistema(
                        'tiempo_funcionamiento',
                        int(tiempo_funcionamiento)
                    )
                    
                    # Actualizar datos desde cache
                    for nombre_dato, info in self.datos_sistema_cache.items():
                        if isinstance(info.get('valor'), (int, float)):
                            self.servidor.actualizar_dato_sistema(nombre_dato, int(info['valor']))
                            
                    # Actualizar estadísticas de comunicación
                    if self.cliente and self.cliente.verificar_conexion():
                        self.servidor.actualizar_dato_sistema('estado_comunicacion_genetec', 1)
                    else:
                        self.servidor.actualizar_dato_sistema('estado_comunicacion_genetec', 0)
                        
                    # Actualizar contadores de dispositivos
                    self.servidor.actualizar_dato_sistema(
                        'numero_dispositivos_total',
                        len(self.estadisticas.dispositivos_monitoreados)
                    )
                    
            except Exception as e:
                self.logger.error(f"Error actualizando servidor: {e}")
                
            # Actualizar cada 10 segundos
            self.detener_hilos.wait(10)
            
    def _procesar_datos_recibidos(self, datos: Dict[str, Any]):
        """
        Procesar datos recibidos del cliente.
        
        Args:
            datos: Datos recibidos
        """
        try:
            # Actualizar cache local
            for clave, valor in datos.items():
                self.datos_sistema_cache[clave] = {
                    'valor': valor,
                    'timestamp': datetime.now()
                }
                
            self.ultima_actualizacion_cache = datetime.now()
            
            # Si tenemos servidor, actualizar sus datos
            if self.servidor:
                for clave, valor in datos.items():
                    if isinstance(valor, (int, float)):
                        self.servidor.actualizar_dato_sistema(clave, valor)
                        
        except Exception as e:
            self.logger.error(f"Error procesando datos recibidos: {e}")
            
    def _manejar_evento_cliente(self, evento: EventoProtocolo):
        """Manejar eventos del cliente Modbus."""
        self.logger.debug(f"Evento cliente: {evento.tipo} - {evento.mensaje}")
        
    def _manejar_evento_servidor(self, evento: EventoProtocolo):
        """Manejar eventos del servidor Modbus."""
        self.logger.debug(f"Evento servidor: {evento.tipo} - {evento.mensaje}")
        
    def _manejar_error_cliente(self, contexto: str, error: Exception):
        """Manejar errores del cliente."""
        self.logger.error(f"Error cliente Modbus ({contexto}): {error}")
        self.estadisticas.registrar_error(f"cliente_{contexto}")
        
    def _manejar_error_servidor(self, contexto: str, error: Exception):
        """Manejar errores del servidor."""
        self.logger.error(f"Error servidor Modbus ({contexto}): {error}")
        self.estadisticas.registrar_error(f"servidor_{contexto}")
        
    def _manejar_comando_sistema(self, direccion: int, valor: int):
        """Manejar comando de sistema desde cliente Modbus."""
        self.logger.info(f"Comando sistema recibido: {valor}")
        
        if valor == 1:  # Restart
            self.logger.info("Comando RESTART recibido")
            # Implementar restart del sistema
        elif valor == 2:  # Stop
            self.logger.info("Comando STOP recibido")
            self.detener()
        elif valor == 3:  # Reset
            self.logger.info("Comando RESET recibido")
            self.estadisticas.reset()
            
    def _manejar_cambio_nivel_log(self, direccion: int, valor: int):
        """Manejar cambio de nivel de logging."""
        niveles = {1: 'DEBUG', 2: 'INFO', 3: 'WARNING', 4: 'ERROR'}
        if valor in niveles:
            nivel = niveles[valor]
            self.logger.info(f"Cambiando nivel de log a: {nivel}")
            # Implementar cambio de nivel
            
    def _manejar_cambio_intervalo_polling(self, direccion: int, valor: int):
        """Manejar cambio de intervalo de polling."""
        if 1 <= valor <= 300:  # Entre 1 segundo y 5 minutos
            self.intervalo_polling = valor
            self.logger.info(f"Intervalo de polling cambiado a: {valor} segundos")
            
    def _manejar_forzar_actualizacion_camaras(self, direccion: int, valor: int):
        """Manejar comando de forzar actualización de cámaras."""
        if valor == 1:
            self.logger.info("Forzando actualización de cámaras...")
            # Implementar actualización forzada
            
    def _manejar_forzar_actualizacion_controladores(self, direccion: int, valor: int):
        """Manejar comando de forzar actualización de controladores."""
        if valor == 1:
            self.logger.info("Forzando actualización de controladores...")
            # Implementar actualización forzada
            
    def _manejar_reiniciar_comunicacion_genetec(self, direccion: int, valor: int):
        """Manejar comando de reiniciar comunicación con Genetec."""
        if valor == 1:
            self.logger.info("Reiniciando comunicación con Genetec...")
            if self.cliente:
                self.cliente.reiniciar()
                
    def _notificar_datos_recibidos(self, datos: Dict[str, Any]):
        """Notificar a callbacks sobre datos recibidos."""
        for callback in self.callbacks_datos_recibidos:
            try:
                callback(datos)
            except Exception as e:
                self.logger.error(f"Error en callback de datos: {e}")
                
    def obtener_estado_completo(self) -> Dict[str, Any]:
        """
        Obtener estado completo del manejador Modbus.
        
        Returns:
            Diccionario con estado completo
        """
        estado = {
            'modo_operacion': self.modo_operacion.value,
            'activo': self.activo,
            'estadisticas': self.estadisticas.obtener_resumen(),
            'cache_datos': len(self.datos_sistema_cache),
            'ultima_actualizacion': str(self.ultima_actualizacion_cache)
        }
        
        if self.cliente:
            estado['cliente'] = {
                'conectado': self.cliente.verificar_conexion(),
                'estado': self.cliente.estado.value,
                'estadisticas': self.cliente.obtener_estadisticas()
            }
            
        if self.servidor:
            estado['servidor'] = {
                'activo': self.servidor.verificar_conexion(),
                'estado': self.servidor.estado.value,
                'estadisticas': self.servidor.obtener_estadisticas()
            }
            
        return estado
        
    def agregar_callback_datos(self, callback: Callable[[Dict[str, Any]], None]):
        """Agregar callback para datos recibidos."""
        self.callbacks_datos_recibidos.append(callback)
        
    def remover_callback_datos(self, callback: Callable[[Dict[str, Any]], None]):
        """Remover callback de datos recibidos."""
        if callback in self.callbacks_datos_recibidos:
            self.callbacks_datos_recibidos.remove(callback)

# Función de utilidad para crear manejador
def crear_manejador_modbus(modo: ModoOperacionModbus = ModoOperacionModbus.CLIENTE_SERVIDOR) -> ManejadorModbus:
    """
    Crear manejador Modbus con el modo especificado.
    
    Args:
        modo: Modo de operación del manejador
        
    Returns:
        Manejador Modbus configurado
    """
    return ManejadorModbus(modo)

if __name__ == "__main__":
    # Prueba del manejador Modbus
    print("Probando manejador Modbus...")
    
    manejador = crear_manejador_modbus(ModoOperacionModbus.CLIENTE_SERVIDOR)
    
    # Iniciar manejador
    resultado = manejador.iniciar()
    print(f"Manejador iniciado: {resultado.exitoso} - {resultado.mensaje}")
    
    if resultado.exitoso:
        try:
            print("Manejador Modbus ejecutándose...")
            print("Presiona Ctrl+C para detener")
            
            while True:
                time.sleep(10)
                estado = manejador.obtener_estado_completo()
                print(f"Estadísticas: {estado['estadisticas']}")
                
        except KeyboardInterrupt:
            print("\nDeteniendo manejador...")
            manejador.detener()
            
    print("✓ Prueba de manejador Modbus completada")