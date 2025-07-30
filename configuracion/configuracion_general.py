"""
Configuración General del Sistema BMS Demo
==========================================

Este módulo contiene toda la configuración general del sistema BMS.
Maneja variables de entorno, configuraciones de red, rutas y parámetros generales.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
import logging

# Cargar variables de entorno
load_dotenv('configuracion.env')

class ConfiguracionGeneral:
    """
    Clase principal para manejar toda la configuración del sistema BMS.
    Centraliza el acceso a variables de entorno y configuraciones.
    """
    
    def __init__(self):
        """Inicializar configuración general del sistema."""
        self.cargar_configuracion()
        self.validar_configuracion()
        
    def cargar_configuracion(self):
        """Cargar todas las configuraciones desde variables de entorno."""
        
        # Configuración General del BMS
        self.NOMBRE_SISTEMA = os.getenv('BMS_NOMBRE', 'Sistema BMS Demo')
        self.VERSION_SISTEMA = os.getenv('BMS_VERSION', '1.0.0')
        self.IP_BMS = os.getenv('BMS_IP', '192.168.1.95')
        self.PUERTO_BMS = int(os.getenv('BMS_PUERTO', 5000))
        
        # Configuración de Genetec
        self.IP_GENETEC = os.getenv('GENETEC_IP', '192.168.1.40')
        self.PUERTO_GENETEC = int(os.getenv('GENETEC_PUERTO', 80))
        self.USUARIO_GENETEC = os.getenv('GENETEC_USUARIO', 'admin')
        self.PASSWORD_GENETEC = os.getenv('GENETEC_PASSWORD', 'demo123')
        
        # Rutas del Sistema
        self.RUTA_BASE = Path(__file__).parent.parent
        self.RUTA_LOGS = self.RUTA_BASE / 'logs'
        self.RUTA_BD = self.RUTA_BASE / 'base_datos'
        self.RUTA_TEMPORAL = self.RUTA_BASE / 'temp'
        
        # Crear directorios si no existen
        self._crear_directorios()
        
        # Configuración de Desarrollo
        self.DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
        self.TESTING = os.getenv('TESTING', 'False').lower() == 'true'
        self.ENTORNO = 'desarrollo' if self.DEBUG else 'produccion'
        
        # Configuración de Logging
        self.LOG_NIVEL = os.getenv('LOG_NIVEL', 'INFO')
        self.LOG_ARCHIVO = self.RUTA_LOGS / 'bms_sistema.log'
        self.LOG_FORMATO = os.getenv(
            'LOG_FORMATO', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configuración de Red
        self.TIMEOUT_CONEXION = int(os.getenv('TIMEOUT_CONEXION', 30))
        self.REINTENTOS_MAXIMOS = int(os.getenv('REINTENTOS_MAXIMOS', 3))
        self.INTERVALO_HEARTBEAT = int(os.getenv('INTERVALO_HEARTBEAT', 60))
        
    def _crear_directorios(self):
        """Crear directorios necesarios si no existen."""
        directorios = [
            self.RUTA_LOGS,
            self.RUTA_BD,
            self.RUTA_TEMPORAL
        ]
        
        for directorio in directorios:
            directorio.mkdir(parents=True, exist_ok=True)
            
    def validar_configuracion(self):
        """Validar que la configuración sea correcta."""
        errores = []
        
        # Validar IPs
        if not self._validar_ip(self.IP_BMS):
            errores.append(f"IP BMS inválida: {self.IP_BMS}")
            
        if not self._validar_ip(self.IP_GENETEC):
            errores.append(f"IP Genetec inválida: {self.IP_GENETEC}")
            
        # Validar puertos
        if not (1 <= self.PUERTO_BMS <= 65535):
            errores.append(f"Puerto BMS inválido: {self.PUERTO_BMS}")
            
        if not (1 <= self.PUERTO_GENETEC <= 65535):
            errores.append(f"Puerto Genetec inválido: {self.PUERTO_GENETEC}")
            
        if errores:
            raise ValueError("Errores en configuración: " + "; ".join(errores))
            
    def _validar_ip(self, ip: str) -> bool:
        """Validar formato de dirección IP."""
        try:
            partes = ip.split('.')
            if len(partes) != 4:
                return False
            for parte in partes:
                if not (0 <= int(parte) <= 255):
                    return False
            return True
        except (ValueError, AttributeError):
            return False
            
    def obtener_configuracion_completa(self) -> Dict[str, Any]:
        """Obtener diccionario con toda la configuración."""
        return {
            'sistema': {
                'nombre': self.NOMBRE_SISTEMA,
                'version': self.VERSION_SISTEMA,
                'entorno': self.ENTORNO,
                'debug': self.DEBUG
            },
            'red': {
                'ip_bms': self.IP_BMS,
                'puerto_bms': self.PUERTO_BMS,
                'ip_genetec': self.IP_GENETEC,
                'puerto_genetec': self.PUERTO_GENETEC,
                'timeout': self.TIMEOUT_CONEXION,
                'reintentos': self.REINTENTOS_MAXIMOS
            },
            'rutas': {
                'base': str(self.RUTA_BASE),
                'logs': str(self.RUTA_LOGS),
                'base_datos': str(self.RUTA_BD),
                'temporal': str(self.RUTA_TEMPORAL)
            },
            'logging': {
                'nivel': self.LOG_NIVEL,
                'archivo': str(self.LOG_ARCHIVO),
                'formato': self.LOG_FORMATO
            }
        }
        
    def mostrar_configuracion(self):
        """Mostrar configuración actual en consola."""
        config = self.obtener_configuracion_completa()
        print("\n" + "="*60)
        print(f"CONFIGURACIÓN SISTEMA BMS - {self.NOMBRE_SISTEMA}")
        print("="*60)
        
        for seccion, valores in config.items():
            print(f"\n[{seccion.upper()}]")
            for clave, valor in valores.items():
                print(f"  {clave}: {valor}")
        print("\n" + "="*60)

# Instancia global de configuración
configuracion = ConfiguracionGeneral()

# Funciones de acceso rápido
def obtener_config() -> ConfiguracionGeneral:
    """Obtener instancia de configuración global."""
    return configuracion

def obtener_ip_bms() -> str:
    """Obtener IP del BMS."""
    return configuracion.IP_BMS

def obtener_puerto_bms() -> int:
    """Obtener puerto del BMS."""
    return configuracion.PUERTO_BMS

def obtener_ip_genetec() -> str:
    """Obtener IP de Genetec."""
    return configuracion.IP_GENETEC

def obtener_puerto_genetec() -> int:
    """Obtener puerto de Genetec."""
    return configuracion.PUERTO_GENETEC

def es_modo_debug() -> bool:
    """Verificar si está en modo debug."""
    return configuracion.DEBUG

def obtener_ruta_logs() -> Path:
    """Obtener ruta de logs."""
    return configuracion.RUTA_LOGS

def obtener_ruta_bd() -> Path:
    """Obtener ruta de base de datos."""
    return configuracion.RUTA_BD

if __name__ == "__main__":
    # Prueba de configuración
    print("Probando configuración general...")
    config = obtener_config()
    config.mostrar_configuracion()
    print("✓ Configuración cargada correctamente")