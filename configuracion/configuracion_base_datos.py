"""
Configuración de Base de Datos
=============================

Este módulo contiene la configuración para la base de datos del sistema BMS.
Maneja conexiones, configuraciones de SQLAlchemy y parámetros de base de datos.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
from enum import Enum
from dataclasses import dataclass

# Cargar variables de entorno
load_dotenv('configuracion.env')

class TipoBaseDatos(Enum):
    """Tipos de base de datos soportados."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"

@dataclass
class ConfiguracionBaseDatos:
    """Configuración principal de base de datos."""
    tipo: TipoBaseDatos
    nombre: str
    ruta: Path
    host: str = None
    puerto: int = None
    usuario: str = None
    password: str = None
    charset: str = 'utf8'
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    def obtener_url_conexion(self) -> str:
        """Obtener URL de conexión para SQLAlchemy."""
        if self.tipo == TipoBaseDatos.SQLITE:
            ruta_completa = self.ruta / f"{self.nombre}.db"
            return f"sqlite:///{ruta_completa}"
        elif self.tipo == TipoBaseDatos.POSTGRESQL:
            return f"postgresql://{self.usuario}:{self.password}@{self.host}:{self.puerto}/{self.nombre}"
        elif self.tipo == TipoBaseDatos.MYSQL:
            return f"mysql+pymysql://{self.usuario}:{self.password}@{self.host}:{self.puerto}/{self.nombre}?charset={self.charset}"
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {self.tipo}")

class ConfiguradorBaseDatos:
    """
    Clase para manejar toda la configuración de base de datos del sistema BMS.
    """
    
    def __init__(self):
        """Inicializar configurador de base de datos."""
        self.cargar_configuracion()
        
    def cargar_configuracion(self):
        """Cargar configuración de base de datos desde variables de entorno."""
        
        # Obtener tipo de base de datos
        tipo_bd_str = os.getenv('BD_TIPO', 'sqlite').lower()
        try:
            tipo_bd = TipoBaseDatos(tipo_bd_str)
        except ValueError:
            print(f"Tipo de BD inválido: {tipo_bd_str}, usando SQLite")
            tipo_bd = TipoBaseDatos.SQLITE
            
        # Configuración básica
        nombre_bd = os.getenv('BD_NOMBRE', 'bms_demo')
        ruta_bd = Path(os.getenv('BD_RUTA', './base_datos/'))
        
        # Asegurar que el directorio existe
        ruta_bd.mkdir(parents=True, exist_ok=True)
        
        # Configuración según el tipo de BD
        if tipo_bd == TipoBaseDatos.SQLITE:
            self.configuracion = ConfiguracionBaseDatos(
                tipo=tipo_bd,
                nombre=nombre_bd,
                ruta=ruta_bd,
                echo=os.getenv('BD_ECHO', 'False').lower() == 'true'
            )
        else:
            # Para PostgreSQL o MySQL
            self.configuracion = ConfiguracionBaseDatos(
                tipo=tipo_bd,
                nombre=nombre_bd,
                ruta=ruta_bd,
                host=os.getenv('BD_HOST', 'localhost'),
                puerto=int(os.getenv('BD_PUERTO', 5432 if tipo_bd == TipoBaseDatos.POSTGRESQL else 3306)),
                usuario=os.getenv('BD_USUARIO', 'bms_user'),
                password=os.getenv('BD_PASSWORD', 'bms_password'),
                charset=os.getenv('BD_CHARSET', 'utf8'),
                pool_size=int(os.getenv('BD_POOL_SIZE', 5)),
                max_overflow=int(os.getenv('BD_MAX_OVERFLOW', 10)),
                pool_timeout=int(os.getenv('BD_POOL_TIMEOUT', 30)),
                pool_recycle=int(os.getenv('BD_POOL_RECYCLE', 3600)),
                echo=os.getenv('BD_ECHO', 'False').lower() == 'true'
            )
            
        # Configuraciones adicionales para tablas
        self.configuracion_tablas = {
            'dispositivos': {
                'nombre_tabla': 'dispositivos',
                'campos_obligatorios': ['id', 'nombre', 'tipo', 'ip', 'estado'],
                'indices': ['ip', 'tipo', 'estado'],
                'eliminar_automatico': False
            },
            'eventos': {
                'nombre_tabla': 'eventos',
                'campos_obligatorios': ['id', 'timestamp', 'tipo', 'dispositivo_id', 'mensaje'],
                'indices': ['timestamp', 'tipo', 'dispositivo_id'],
                'eliminar_automatico': True,
                'dias_retencion': 30
            },
            'sensores': {
                'nombre_tabla': 'sensores',
                'campos_obligatorios': ['id', 'nombre', 'tipo', 'dispositivo_id', 'valor'],
                'indices': ['dispositivo_id', 'tipo'],
                'eliminar_automatico': False
            },
            'controladores': {
                'nombre_tabla': 'controladores',
                'campos_obligatorios': ['id', 'nombre', 'tipo', 'ip', 'puerto'],
                'indices': ['ip', 'tipo'],
                'eliminar_automatico': False
            },
            'camaras': {
                'nombre_tabla': 'camaras',
                'campos_obligatorios': ['id', 'nombre', 'ip', 'puerto', 'canal'],
                'indices': ['ip'],
                'eliminar_automatico': False
            },
            'lecturas_modbus': {
                'nombre_tabla': 'lecturas_modbus',
                'campos_obligatorios': ['id', 'timestamp', 'dispositivo_id', 'registro', 'valor'],
                'indices': ['timestamp', 'dispositivo_id', 'registro'],
                'eliminar_automatico': True,
                'dias_retencion': 7
            }
        }
        
    def obtener_configuracion(self) -> ConfiguracionBaseDatos:
        """Obtener configuración de base de datos."""
        return self.configuracion
        
    def obtener_url_conexion(self) -> str:
        """Obtener URL de conexión SQLAlchemy."""
        return self.configuracion.obtener_url_conexion()
        
    def obtener_configuracion_tabla(self, nombre_tabla: str) -> Dict[str, Any]:
        """Obtener configuración específica de una tabla."""
        return self.configuracion_tablas.get(nombre_tabla, {})
        
    def obtener_configuracion_sqlalchemy(self) -> Dict[str, Any]:
        """Obtener configuración para SQLAlchemy engine."""
        config = {
            'echo': self.configuracion.echo,
            'future': True
        }
        
        # Solo agregar configuración de pool para bases de datos remotas
        if self.configuracion.tipo != TipoBaseDatos.SQLITE:
            config.update({
                'pool_size': self.configuracion.pool_size,
                'max_overflow': self.configuracion.max_overflow,
                'pool_timeout': self.configuracion.pool_timeout,
                'pool_recycle': self.configuracion.pool_recycle
            })
            
        return config
        
    def validar_configuracion(self) -> bool:
        """Validar que la configuración de BD sea correcta."""
        try:
            # Verificar que la URL se puede generar
            url = self.obtener_url_conexion()
            
            # Para SQLite, verificar que el directorio existe
            if self.configuracion.tipo == TipoBaseDatos.SQLITE:
                if not self.configuracion.ruta.exists():
                    self.configuracion.ruta.mkdir(parents=True, exist_ok=True)
                    
            return True
        except Exception as e:
            print(f"Error validando configuración de BD: {e}")
            return False
            
    def obtener_configuracion_completa(self) -> Dict[str, Any]:
        """Obtener diccionario completo con toda la configuración."""
        config = self.configuracion.__dict__.copy()
        
        # Convertir Path a string para serialización
        config['ruta'] = str(config['ruta'])
        
        # Convertir enum a string
        config['tipo'] = config['tipo'].value
        
        # Ocultar password en la salida
        if config.get('password'):
            config['password'] = '*' * len(config['password'])
            
        return {
            'configuracion_principal': config,
            'url_conexion': self.obtener_url_conexion().replace(
                self.configuracion.password or '', 
                '*' * len(self.configuracion.password or '')
            ),
            'configuracion_tablas': self.configuracion_tablas,
            'configuracion_sqlalchemy': self.obtener_configuracion_sqlalchemy()
        }
        
    def mostrar_configuracion(self):
        """Mostrar configuración actual de base de datos."""
        config = self.obtener_configuracion_completa()
        
        print("\n" + "="*60)
        print("CONFIGURACIÓN BASE DE DATOS BMS")
        print("="*60)
        
        print(f"\n[CONFIGURACIÓN PRINCIPAL]")
        for clave, valor in config['configuracion_principal'].items():
            print(f"  {clave}: {valor}")
            
        print(f"\n[URL CONEXIÓN]")
        print(f"  {config['url_conexion']}")
        
        print(f"\n[CONFIGURACIÓN SQLALCHEMY]")
        for clave, valor in config['configuracion_sqlalchemy'].items():
            print(f"  {clave}: {valor}")
            
        print(f"\n[TABLAS CONFIGURADAS]")
        for tabla, conf in config['configuracion_tablas'].items():
            print(f"  {tabla}: {conf['nombre_tabla']}")
            
        print("="*60)

# Instancia global de configuración de base de datos
configurador_bd = ConfiguradorBaseDatos()

# Funciones de acceso rápido
def obtener_config_bd() -> ConfiguracionBaseDatos:
    """Obtener configuración de base de datos."""
    return configurador_bd.obtener_configuracion()

def obtener_url_conexion_bd() -> str:
    """Obtener URL de conexión de base de datos."""
    return configurador_bd.obtener_url_conexion()

def obtener_config_sqlalchemy() -> Dict[str, Any]:
    """Obtener configuración para SQLAlchemy."""
    return configurador_bd.obtener_configuracion_sqlalchemy()

def obtener_config_tabla(nombre_tabla: str) -> Dict[str, Any]:
    """Obtener configuración de una tabla específica."""
    return configurador_bd.obtener_configuracion_tabla(nombre_tabla)

def validar_bd_disponible() -> bool:
    """Validar que la base de datos esté disponible."""
    return configurador_bd.validar_configuracion()

if __name__ == "__main__":
    # Prueba de configuración de base de datos
    print("Probando configuración de base de datos...")
    configurador_bd.mostrar_configuracion()
    
    if validar_bd_disponible():
        print("\n✓ Configuración de base de datos válida")
    else:
        print("\n✗ Error en configuración de base de datos")