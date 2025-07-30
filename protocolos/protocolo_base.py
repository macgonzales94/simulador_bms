"""
Clase Base para Protocolos de Comunicación
==========================================

Este módulo define la interfaz base que deben implementar todos los protocolos
de comunicación del sistema BMS (Modbus, MQTT, BACnet, SNMP, HTTP).

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading
import time
from dataclasses import dataclass

# Importar utilidades
from utilidades.logger import obtener_logger

class EstadoProtocolo(Enum):
    """Estados posibles de un protocolo de comunicación."""
    DESCONECTADO = "desconectado"
    CONECTANDO = "conectando"
    CONECTADO = "conectado"
    ERROR = "error"
    DETENIDO = "detenido"

class TipoOperacion(Enum):
    """Tipos de operación soportados por los protocolos."""
    LECTURA = "lectura"
    ESCRITURA = "escritura"
    SUSCRIPCION = "suscripcion"
    PUBLICACION = "publicacion"
    DESCUBRIMIENTO = "descubrimiento"

@dataclass
class ResultadoOperacion:
    """Resultado de una operación de protocolo."""
    exitoso: bool
    datos: Any = None
    mensaje: str = ""
    timestamp: datetime = None
    tiempo_respuesta: float = 0.0
    codigo_error: Optional[int] = None
    
    def __post_init__(self):
        """Inicializar timestamp si no se proporciona."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class EventoProtocolo:
    """Evento generado por un protocolo."""
    tipo: str
    protocolo: str
    dispositivo: str
    mensaje: str
    datos: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        """Inicializar timestamp si no se proporciona."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ProtocoloBase(ABC):
    """
    Clase base abstracta para todos los protocolos de comunicación.
    Define la interfaz común que deben implementar todos los protocolos.
    """
    
    def __init__(self, nombre_protocolo: str, configuracion: Dict[str, Any]):
        """
        Inicializar protocolo base.
        
        Args:
            nombre_protocolo: Nombre del protocolo (modbus, mqtt, etc.)
            configuracion: Diccionario con configuración específica
        """
        self.nombre_protocolo = nombre_protocolo
        self.configuracion = configuracion
        self.estado = EstadoProtocolo.DESCONECTADO
        self.logger = obtener_logger(f"protocolo.{nombre_protocolo}")
        
        # Control de hilos
        self.hilo_principal = None
        self.detener_evento = threading.Event()
        self.activo = False
        
        # Callbacks y eventos
        self.callbacks_eventos = []
        self.callbacks_errores = []
        self.callbacks_conexion = []
        
        # Estadísticas
        self.estadisticas = {
            'operaciones_exitosas': 0,
            'operaciones_fallidas': 0,
            'tiempo_conexion': None,
            'ultima_operacion': None,
            'errores_consecutivos': 0
        }
        
        # Bloqueo para operaciones thread-safe
        self.bloqueo = threading.Lock()
        
        self.logger.info(f"Protocolo {nombre_protocolo} inicializado")
        
    @abstractmethod
    def conectar(self) -> ResultadoOperacion:
        """
        Conectar al dispositivo/servidor del protocolo.
        
        Returns:
            ResultadoOperacion con el resultado de la conexión
        """
        pass
        
    @abstractmethod
    def desconectar(self) -> ResultadoOperacion:
        """
        Desconectar del dispositivo/servidor del protocolo.
        
        Returns:
            ResultadoOperacion con el resultado de la desconexión
        """
        pass
        
    @abstractmethod
    def leer_datos(self, direccion: str, **kwargs) -> ResultadoOperacion:
        """
        Leer datos del protocolo.
        
        Args:
            direccion: Dirección o identificador del dato a leer
            **kwargs: Parámetros adicionales específicos del protocolo
            
        Returns:
            ResultadoOperacion con los datos leídos
        """
        pass
        
    @abstractmethod
    def escribir_datos(self, direccion: str, valor: Any, **kwargs) -> ResultadoOperacion:
        """
        Escribir datos usando el protocolo.
        
        Args:
            direccion: Dirección o identificador donde escribir
            valor: Valor a escribir
            **kwargs: Parámetros adicionales específicos del protocolo
            
        Returns:
            ResultadoOperacion con el resultado de la escritura
        """
        pass
        
    @abstractmethod
    def verificar_conexion(self) -> bool:
        """
        Verificar si la conexión está activa.
        
        Returns:
            True si está conectado, False en caso contrario
        """
        pass
        
    def cambiar_estado(self, nuevo_estado: EstadoProtocolo, mensaje: str = ""):
        """
        Cambiar estado del protocolo y notificar callbacks.
        
        Args:
            nuevo_estado: Nuevo estado del protocolo
            mensaje: Mensaje descriptivo del cambio
        """
        estado_anterior = self.estado
        self.estado = nuevo_estado
        
        self.logger.info(f"Cambio de estado: {estado_anterior.value} -> {nuevo_estado.value}")
        
        if mensaje:
            self.logger.info(f"Mensaje: {mensaje}")
            
        # Notificar callbacks de conexión
        for callback in self.callbacks_conexion:
            try:
                callback(self.nombre_protocolo, estado_anterior, nuevo_estado, mensaje)
            except Exception as e:
                self.logger.error(f"Error en callback de conexión: {e}")
                
    def agregar_callback_evento(self, callback: Callable[[EventoProtocolo], None]):
        """
        Agregar callback para eventos del protocolo.
        
        Args:
            callback: Función a llamar cuando ocurra un evento
        """
        self.callbacks_eventos.append(callback)
        
    def agregar_callback_error(self, callback: Callable[[str, Exception], None]):
        """
        Agregar callback para errores del protocolo.
        
        Args:
            callback: Función a llamar cuando ocurra un error
        """
        self.callbacks_errores.append(callback)
        
    def agregar_callback_conexion(self, callback: Callable[[str, EstadoProtocolo, EstadoProtocolo, str], None]):
        """
        Agregar callback para cambios de estado de conexión.
        
        Args:
            callback: Función a llamar cuando cambie el estado
        """
        self.callbacks_conexion.append(callback)
        
    def emitir_evento(self, tipo_evento: str, dispositivo: str, mensaje: str, datos: Dict[str, Any] = None):
        """
        Emitir un evento del protocolo.
        
        Args:
            tipo_evento: Tipo de evento
            dispositivo: Dispositivo relacionado
            mensaje: Mensaje del evento
            datos: Datos adicionales del evento
        """
        evento = EventoProtocolo(
            tipo=tipo_evento,
            protocolo=self.nombre_protocolo,
            dispositivo=dispositivo,
            mensaje=mensaje,
            datos=datos or {}
        )
        
        self.logger.debug(f"Evento emitido: {tipo_evento} - {mensaje}")
        
        # Notificar callbacks
        for callback in self.callbacks_eventos:
            try:
                callback(evento)
            except Exception as e:
                self.logger.error(f"Error en callback de evento: {e}")
                
    def manejar_error(self, error: Exception, contexto: str = ""):
        """
        Manejar error del protocolo.
        
        Args:
            error: Excepción ocurrida
            contexto: Contexto donde ocurrió el error
        """
        with self.bloqueo:
            self.estadisticas['errores_consecutivos'] += 1
            
        mensaje_error = f"Error en {self.nombre_protocolo}"
        if contexto:
            mensaje_error += f" ({contexto})"
        mensaje_error += f": {str(error)}"
        
        self.logger.error(mensaje_error)
        
        # Notificar callbacks de error
        for callback in self.callbacks_errores:
            try:
                callback(contexto, error)
            except Exception as e:
                self.logger.error(f"Error en callback de error: {e}")
                
        # Cambiar estado si hay muchos errores consecutivos
        if self.estadisticas['errores_consecutivos'] >= 3:
            self.cambiar_estado(EstadoProtocolo.ERROR, "Múltiples errores consecutivos")
            
    def actualizar_estadisticas(self, operacion_exitosa: bool, tiempo_respuesta: float = 0.0):
        """
        Actualizar estadísticas del protocolo.
        
        Args:
            operacion_exitosa: Si la operación fue exitosa
            tiempo_respuesta: Tiempo de respuesta en segundos
        """
        with self.bloqueo:
            if operacion_exitosa:
                self.estadisticas['operaciones_exitosas'] += 1
                self.estadisticas['errores_consecutivos'] = 0
            else:
                self.estadisticas['operaciones_fallidas'] += 1
                
            self.estadisticas['ultima_operacion'] = datetime.now()
            
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del protocolo.
        
        Returns:
            Diccionario con estadísticas actuales
        """
        with self.bloqueo:
            estadisticas = self.estadisticas.copy()
            
        # Agregar información de estado
        estadisticas.update({
            'protocolo': self.nombre_protocolo,
            'estado': self.estado.value,
            'activo': self.activo,
            'configuracion': self.configuracion.copy()
        })
        
        return estadisticas
        
    def iniciar_monitoreo(self, intervalo: int = 30):
        """
        Iniciar monitoreo automático del protocolo.
        
        Args:
            intervalo: Intervalo de monitoreo en segundos
        """
        if self.hilo_principal and self.hilo_principal.is_alive():
            self.logger.warning("Monitoreo ya está activo")
            return
            
        self.activo = True
        self.detener_evento.clear()
        
        self.hilo_principal = threading.Thread(
            target=self._bucle_monitoreo,
            args=(intervalo,),
            name=f"Monitor-{self.nombre_protocolo}",
            daemon=True
        )
        self.hilo_principal.start()
        
        self.logger.info(f"Monitoreo iniciado con intervalo de {intervalo} segundos")
        
    def detener_monitoreo(self):
        """Detener monitoreo automático del protocolo."""
        if not self.activo:
            return
            
        self.activo = False
        self.detener_evento.set()
        
        if self.hilo_principal and self.hilo_principal.is_alive():
            self.hilo_principal.join(timeout=5)
            
        self.logger.info("Monitoreo detenido")
        
    def _bucle_monitoreo(self, intervalo: int):
        """
        Bucle principal de monitoreo.
        
        Args:
            intervalo: Intervalo de verificación en segundos
        """
        while self.activo and not self.detener_evento.is_set():
            try:
                # Verificar conexión
                if not self.verificar_conexion():
                    self.logger.warning("Conexión perdida, intentando reconectar...")
                    self.cambiar_estado(EstadoProtocolo.CONECTANDO, "Reconectando...")
                    
                    resultado = self.conectar()
                    if resultado.exitoso:
                        self.logger.info("Reconexión exitosa")
                    else:
                        self.logger.error(f"Error en reconexión: {resultado.mensaje}")
                        
                # Emitir evento de heartbeat
                self.emitir_evento(
                    "heartbeat",
                    self.nombre_protocolo,
                    "Verificación periódica",
                    {"estado": self.estado.value}
                )
                
            except Exception as e:
                self.manejar_error(e, "monitoreo")
                
            # Esperar intervalo o evento de parada
            self.detener_evento.wait(intervalo)
            
    def reiniciar(self) -> ResultadoOperacion:
        """
        Reiniciar protocolo (desconectar y conectar).
        
        Returns:
            ResultadoOperacion con el resultado del reinicio
        """
        self.logger.info("Reiniciando protocolo...")
        
        # Desconectar
        resultado_desc = self.desconectar()
        if not resultado_desc.exitoso:
            self.logger.warning(f"Error al desconectar: {resultado_desc.mensaje}")
            
        # Esperar un poco
        time.sleep(1)
        
        # Conectar
        resultado_conn = self.conectar()
        
        if resultado_conn.exitoso:
            self.logger.info("Protocolo reiniciado exitosamente")
        else:
            self.logger.error(f"Error al reiniciar: {resultado_conn.mensaje}")
            
        return resultado_conn
        
    def __del__(self):
        """Destructor para limpiar recursos."""
        try:
            self.detener_monitoreo()
            self.desconectar()
        except:
            pass