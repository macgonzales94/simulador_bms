"""
Sistema de Logging para BMS Demo
===============================

Este módulo proporciona funcionalidades centralizadas de logging para todo el sistema BMS.
Incluye rotación de archivos, niveles de log y formateo específico.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import colorlog
import sys
import os

# Importar configuración
from configuracion.configuracion_general import obtener_config

class GestorLogs:
    """
    Gestor centralizado de logs para el sistema BMS.
    Maneja múltiples handlers, rotación de archivos y formateo.
    """
    
    def __init__(self):
        """Inicializar gestor de logs."""
        self.config = obtener_config()
        self.loggers = {}
        self._configurar_logging_base()
        
    def _configurar_logging_base(self):
        """Configurar logging básico del sistema."""
        
        # Crear directorio de logs si no existe
        self.config.RUTA_LOGS.mkdir(parents=True, exist_ok=True)
        
        # Configurar nivel de logging global
        nivel_logging = getattr(logging, self.config.LOG_NIVEL.upper(), logging.INFO)
        logging.basicConfig(level=nivel_logging)
        
        # Deshabilitar logs de librerías externas muy verbosas
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('pymodbus').setLevel(logging.WARNING)
        
    def crear_logger(self, 
                    nombre: str, 
                    archivo_log: Optional[str] = None,
                    nivel: str = None,
                    incluir_consola: bool = True) -> logging.Logger:
        """
        Crear un logger específico para un módulo.
        
        Args:
            nombre: Nombre del logger
            archivo_log: Nombre del archivo de log (opcional)
            nivel: Nivel de logging (opcional)
            incluir_consola: Si incluir salida a consola
            
        Returns:
            Logger configurado
        """
        
        # Si ya existe el logger, devolverlo
        if nombre in self.loggers:
            return self.loggers[nombre]
            
        # Crear nuevo logger
        logger = logging.getLogger(nombre)
        
        # Configurar nivel
        nivel_log = nivel or self.config.LOG_NIVEL
        nivel_logging = getattr(logging, nivel_log.upper(), logging.INFO)
        logger.setLevel(nivel_logging)
        
        # Limpiar handlers existentes
        logger.handlers.clear()
        
        # Configurar formateo
        formato_archivo = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo
        if archivo_log:
            ruta_archivo = self.config.RUTA_LOGS / archivo_log
        else:
            ruta_archivo = self.config.RUTA_LOGS / f"{nombre.replace('.', '_')}.log"
            
        handler_archivo = logging.handlers.RotatingFileHandler(
            ruta_archivo,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handler_archivo.setFormatter(formato_archivo)
        handler_archivo.setLevel(nivel_logging)
        logger.addHandler(handler_archivo)
        
        # Handler para consola (con colores si está disponible)
        if incluir_consola:
            if colorlog and sys.stdout.isatty():
                formato_consola = colorlog.ColoredFormatter(
                    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            else:
                formato_consola = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
                
            handler_consola = logging.StreamHandler(sys.stdout)
            handler_consola.setFormatter(formato_consola)
            handler_consola.setLevel(nivel_logging)
            logger.addHandler(handler_consola)
            
        # Evitar propagación a logger raíz
        logger.propagate = False
        
        # Guardar referencia
        self.loggers[nombre] = logger
        
        return logger
        
    def obtener_logger(self, nombre: str) -> logging.Logger:
        """
        Obtener logger existente o crear uno nuevo.
        
        Args:
            nombre: Nombre del logger
            
        Returns:
            Logger configurado
        """
        if nombre not in self.loggers:
            return self.crear_logger(nombre)
        return self.loggers[nombre]
        
    def crear_logger_protocolo(self, protocolo: str) -> logging.Logger:
        """
        Crear logger específico para un protocolo de comunicación.
        
        Args:
            protocolo: Nombre del protocolo (modbus, mqtt, etc.)
            
        Returns:
            Logger configurado para el protocolo
        """
        nombre_logger = f"protocolo.{protocolo.lower()}"
        archivo_log = f"protocolo_{protocolo.lower()}.log"
        
        return self.crear_logger(
            nombre=nombre_logger,
            archivo_log=archivo_log,
            incluir_consola=True
        )
        
    def crear_logger_servicio(self, servicio: str) -> logging.Logger:
        """
        Crear logger específico para un servicio.
        
        Args:
            servicio: Nombre del servicio
            
        Returns:
            Logger configurado para el servicio
        """
        nombre_logger = f"servicio.{servicio.lower()}"
        archivo_log = f"servicio_{servicio.lower()}.log"
        
        return self.crear_logger(
            nombre=nombre_logger,
            archivo_log=archivo_log,
            incluir_consola=True
        )
        
    def crear_logger_sistema(self) -> logging.Logger:
        """
        Crear logger principal del sistema.
        
        Returns:
            Logger principal del sistema
        """
        return self.crear_logger(
            nombre="sistema_bms",
            archivo_log="sistema_bms.log",
            incluir_consola=True
        )
        
    def limpiar_logs_antiguos(self, dias_retencion: int = 30):
        """
        Limpiar archivos de log antiguos.
        
        Args:
            dias_retencion: Número de días a mantener
        """
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias_retencion)
            
            for archivo in self.config.RUTA_LOGS.glob("*.log*"):
                if archivo.stat().st_mtime < fecha_limite.timestamp():
                    archivo.unlink()
                    print(f"Eliminado log antiguo: {archivo.name}")
                    
        except Exception as e:
            print(f"Error limpiando logs antiguos: {e}")
            
    def obtener_estadisticas_logs(self) -> dict:
        """
        Obtener estadísticas de archivos de log.
        
        Returns:
            Diccionario con estadísticas
        """
        estadisticas = {
            'total_archivos': 0,
            'tamaño_total': 0,
            'archivos': []
        }
        
        try:
            for archivo in self.config.RUTA_LOGS.glob("*.log*"):
                info_archivo = archivo.stat()
                estadisticas['archivos'].append({
                    'nombre': archivo.name,
                    'tamaño': info_archivo.st_size,
                    'modificado': datetime.fromtimestamp(info_archivo.st_mtime)
                })
                estadisticas['total_archivos'] += 1
                estadisticas['tamaño_total'] += info_archivo.st_size
                
        except Exception as e:
            print(f"Error obteniendo estadísticas de logs: {e}")
            
        return estadisticas
        
    def configurar_nivel_global(self, nivel: str):
        """
        Cambiar nivel de logging para todos los loggers.
        
        Args:
            nivel: Nuevo nivel de logging
        """
        nivel_logging = getattr(logging, nivel.upper(), logging.INFO)
        
        for logger in self.loggers.values():
            logger.setLevel(nivel_logging)
            for handler in logger.handlers:
                handler.setLevel(nivel_logging)
                
        print(f"Nivel de logging cambiado a: {nivel.upper()}")

# Instancia global del gestor de logs
gestor_logs = GestorLogs()

# Funciones de acceso rápido
def obtener_logger(nombre: str) -> logging.Logger:
    """Obtener logger por nombre."""
    return gestor_logs.obtener_logger(nombre)

def obtener_logger_protocolo(protocolo: str) -> logging.Logger:
    """Obtener logger para protocolo específico."""
    return gestor_logs.crear_logger_protocolo(protocolo)

def obtener_logger_servicio(servicio: str) -> logging.Logger:
    """Obtener logger para servicio específico."""
    return gestor_logs.crear_logger_servicio(servicio)

def obtener_logger_sistema() -> logging.Logger:
    """Obtener logger principal del sistema."""
    return gestor_logs.crear_logger_sistema()

def configurar_nivel_logging(nivel: str):
    """Configurar nivel de logging global."""
    gestor_logs.configurar_nivel_global(nivel)

def limpiar_logs_antiguos(dias: int = 30):
    """Limpiar logs antiguos."""
    gestor_logs.limpiar_logs_antiguos(dias)

def obtener_estadisticas_logs() -> dict:
    """Obtener estadísticas de logs."""
    return gestor_logs.obtener_estadisticas_logs()

# Loggers predefinidos para uso común
logger_sistema = obtener_logger_sistema()
logger_modbus = obtener_logger_protocolo("modbus")
logger_mqtt = obtener_logger_protocolo("mqtt")
logger_bacnet = obtener_logger_protocolo("bacnet")
logger_snmp = obtener_logger_protocolo("snmp")
logger_http = obtener_logger_protocolo("http")

if __name__ == "__main__":
    # Prueba del sistema de logging
    print("Probando sistema de logging...")
    
    # Crear logger de prueba
    logger_prueba = obtener_logger("prueba")
    
    # Probar diferentes niveles
    logger_prueba.debug("Mensaje de debug")
    logger_prueba.info("Mensaje de información")
    logger_prueba.warning("Mensaje de advertencia")
    logger_prueba.error("Mensaje de error")
    
    # Mostrar estadísticas
    stats = obtener_estadisticas_logs()
    print(f"\nEstadísticas de logs:")
    print(f"Total archivos: {stats['total_archivos']}")
    print(f"Tamaño total: {stats['tamaño_total']} bytes")
    
    print("\n✓ Sistema de logging configurado correctamente")