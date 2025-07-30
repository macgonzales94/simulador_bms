"""
Conexión y Gestión de Base de Datos
==================================

Este módulo maneja la conexión a la base de datos SQLAlchemy y proporciona
funciones para gestionar la base de datos del sistema BMS.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.pool import StaticPool

# Importar configuración y modelos
from configuracion.configuracion_base_datos import obtener_config_bd, obtener_url_conexion_bd, obtener_config_sqlalchemy
from modelos.dispositivo import Base, Dispositivo
from modelos.sensor import Sensor, LecturaSensor
from utilidades.logger import obtener_logger

class GestorBaseDatos:
    """
    Gestor principal de la base de datos del sistema BMS.
    Maneja conexiones, sesiones y operaciones de base de datos.
    """
    
    def __init__(self):
        """Inicializar gestor de base de datos."""
        self.logger = obtener_logger("base_datos")
        self.config_bd = obtener_config_bd()
        self.engine = None
        self.SessionLocal = None
        self.conectado = False
        
        # Intentar conectar automáticamente
        self.conectar()
        
    def conectar(self) -> bool:
        """
        Establecer conexión con la base de datos.
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            url_conexion = obtener_url_conexion_bd()
            config_sqlalchemy = obtener_config_sqlalchemy()
            
            self.logger.info(f"Conectando a base de datos: {self.config_bd.tipo.value}")
            
            # Configuración especial para SQLite
            if self.config_bd.tipo.value == "sqlite":
                config_sqlalchemy.update({
                    'poolclass': StaticPool,
                    'connect_args': {
                        'check_same_thread': False,
                        'timeout': 20
                    }
                })
                
            # Crear engine
            self.engine = create_engine(url_conexion, **config_sqlalchemy)
            
            # Crear sessionmaker
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Probar conexión
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            self.conectado = True
            self.logger.info("✓ Conexión a base de datos establecida")
            
            # Crear tablas si no existen
            self.crear_tablas()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error conectando a base de datos: {e}")
            self.conectado = False
            return False
            
    def desconectar(self):
        """Cerrar conexión con la base de datos."""
        try:
            if self.engine:
                self.engine.dispose()
                self.conectado = False
                self.logger.info("Conexión a base de datos cerrada")
        except Exception as e:
            self.logger.error(f"Error cerrando conexión: {e}")
            
    def crear_tablas(self):
        """Crear todas las tablas definidas en los modelos."""
        try:
            if not self.engine:
                raise RuntimeError("No hay conexión a base de datos")
                
            self.logger.info("Creando tablas de base de datos...")
            
            # Crear todas las tablas
            Base.metadata.create_all(bind=self.engine)
            
            # Verificar que las tablas se crearon
            inspector = inspect(self.engine)
            tablas_existentes = inspector.get_table_names()
            
            tablas_esperadas = ['dispositivos', 'sensores', 'lecturas_sensores']
            tablas_creadas = [t for t in tablas_esperadas if t in tablas_existentes]
            
            self.logger.info(f"✓ Tablas creadas: {tablas_creadas}")
            
            if len(tablas_creadas) != len(tablas_esperadas):
                tablas_faltantes = set(tablas_esperadas) - set(tablas_creadas)
                self.logger.warning(f"⚠ Tablas faltantes: {tablas_faltantes}")
                
        except Exception as e:
            self.logger.error(f"Error creando tablas: {e}")
            
    def eliminar_tablas(self):
        """Eliminar todas las tablas (¡CUIDADO! Elimina todos los datos)."""
        try:
            if not self.engine:
                raise RuntimeError("No hay conexión a base de datos")
                
            self.logger.warning("⚠ ELIMINANDO TODAS LAS TABLAS")
            Base.metadata.drop_all(bind=self.engine)
            self.logger.info("✓ Todas las tablas eliminadas")
            
        except Exception as e:
            self.logger.error(f"Error eliminando tablas: {e}")
            
    @contextmanager
    def obtener_sesion(self):
        """
        Context manager para obtener sesión de base de datos.
        Maneja automáticamente commit/rollback.
        
        Yields:
            Session: Sesión de SQLAlchemy
        """
        if not self.conectado or not self.SessionLocal:
            raise RuntimeError("No hay conexión a base de datos")
            
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error en sesión de base de datos: {e}")
            raise
        finally:
            session.close()
            
    def verificar_salud_bd(self) -> Dict[str, Any]:
        """
        Verificar salud de la base de datos.
        
        Returns:
            Diccionario con información de salud
        """
        resultado = {
            'conectado': False,
            'tablas_existentes': [],
            'version_esquema': None,
            'tamaño_bd': None,
            'ultimo_error': None
        }
        
        try:
            if not self.conectado:
                resultado['ultimo_error'] = "No conectado"
                return resultado
                
            # Verificar conexión
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                resultado['conectado'] = True
                
            # Obtener tablas existentes
            inspector = inspect(self.engine)
            resultado['tablas_existentes'] = inspector.get_table_names()
            
            # Para SQLite, obtener tamaño del archivo
            if self.config_bd.tipo.value == "sqlite":
                ruta_bd = self.config_bd.ruta / f"{self.config_bd.nombre}.db"
                if ruta_bd.exists():
                    resultado['tamaño_bd'] = ruta_bd.stat().st_size
                    
            # Contar registros por tabla
            with self.obtener_sesion() as session:
                resultado['conteo_dispositivos'] = session.query(Dispositivo).count()
                resultado['conteo_sensores'] = session.query(Sensor).count()
                resultado['conteo_lecturas'] = session.query(LecturaSensor).count()
                
        except Exception as e:
            resultado['ultimo_error'] = str(e)
            self.logger.error(f"Error verificando salud de BD: {e}")
            
        return resultado
        
    def limpiar_datos_antiguos(self, dias_retencion: int = 30):
        """
        Limpiar datos antiguos de la base de datos.
        
        Args:
            dias_retencion: Días de retención de datos
        """
        try:
            fecha_limite = datetime.now() - timedelta(days=dias_retencion)
            
            with self.obtener_sesion() as session:
                # Limpiar lecturas de sensores antiguas
                lecturas_eliminadas = session.query(LecturaSensor).filter(
                    LecturaSensor.timestamp < fecha_limite
                ).delete()
                
                if lecturas_eliminadas > 0:
                    self.logger.info(f"✓ Eliminadas {lecturas_eliminadas} lecturas antiguas")
                    
        except Exception as e:
            self.logger.error(f"Error limpiando datos antiguos: {e}")
            
    def hacer_backup(self, ruta_backup: str = None) -> bool:
        """
        Hacer backup de la base de datos.
        
        Args:
            ruta_backup: Ruta donde guardar el backup
            
        Returns:
            True si el backup fue exitoso
        """
        try:
            if self.config_bd.tipo.value != "sqlite":
                self.logger.warning("Backup automático solo soportado para SQLite")
                return False
                
            if not ruta_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_backup = f"backup_bms_{timestamp}.db"
                
            ruta_bd_origen = self.config_bd.ruta / f"{self.config_bd.nombre}.db"
            
            if not ruta_bd_origen.exists():
                self.logger.error("Archivo de base de datos no existe")
                return False
                
            import shutil
            shutil.copy2(ruta_bd_origen, ruta_backup)
            
            self.logger.info(f"✓ Backup creado: {ruta_backup}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return False
            
    def ejecutar_mantenimiento(self):
        """Ejecutar tareas de mantenimiento de la base de datos."""
        try:
            self.logger.info("Ejecutando mantenimiento de base de datos...")
            
            # Para SQLite, ejecutar VACUUM para optimizar
            if self.config_bd.tipo.value == "sqlite":
                with self.engine.connect() as conn:
                    conn.execute(text("VACUUM"))
                    conn.execute(text("ANALYZE"))
                    
            # Limpiar datos antiguos
            self.limpiar_datos_antiguos()
            
            # Hacer backup automático
            self.hacer_backup()
            
            self.logger.info("✓ Mantenimiento de base de datos completado")
            
        except Exception as e:
            self.logger.error(f"Error en mantenimiento: {e}")

# Instancia global del gestor
gestor_bd = GestorBaseDatos()

# Funciones de acceso rápido
def obtener_sesion():
    """Obtener sesión de base de datos usando context manager."""
    return gestor_bd.obtener_sesion()

def verificar_bd_disponible() -> bool:
    """Verificar si la base de datos está disponible."""
    return gestor_bd.conectado

def obtener_salud_bd() -> Dict[str, Any]:
    """Obtener información de salud de la base de datos."""
    return gestor_bd.verificar_salud_bd()

def inicializar_bd():
    """Inicializar base de datos y crear tablas."""
    if not gestor_bd.conectado:
        gestor_bd.conectar()
    gestor_bd.crear_tablas()

def limpiar_bd():
    """Limpiar datos antiguos de la base de datos."""
    gestor_bd.limpiar_datos_antiguos()

def hacer_backup_bd(ruta: str = None) -> bool:
    """Hacer backup de la base de datos."""
    return gestor_bd.hacer_backup(ruta)

def ejecutar_mantenimiento_bd():
    """Ejecutar mantenimiento de la base de datos."""
    gestor_bd.ejecutar_mantenimiento()

# Funciones para popular base de datos con datos demo
def crear_datos_demo():
    """Crear datos de demostración en la base de datos."""
    try:
        from modelos.dispositivo import TipoDispositivo, EstadoDispositivo, ConfiguracionDispositivo, ProtocoloComunicacion
        from modelos.sensor import crear_sensor_temperatura, crear_sensor_humedad
        
        with obtener_sesion() as session:
            # Verificar si ya hay datos
            count_dispositivos = session.query(Dispositivo).count()
            if count_dispositivos > 0:
                gestor_bd.logger.info("Ya existen datos en la base de datos")
                return
                
            gestor_bd.logger.info("Creando datos de demostración...")
            
            # Dispositivo 1: Cámara
            camara = Dispositivo(
                nombre="Cámara Lab 01",
                descripcion="Cámara IP en laboratorio - entrada principal",
                tipo=TipoDispositivo.CAMARA.value,
                marca="Axis",
                modelo="P1455-LE",
                direccion_ip="192.168.1.101",
                puerto=80,
                ubicacion_fisica="Laboratorio - Entrada principal",
                zona="Lab-A",
                estado=EstadoDispositivo.ONLINE.value,
                habilitado=True,
                monitoreado=True,
                etiquetas="seguridad, laboratorio"
            )
            session.add(camara)
            session.flush()  # Para obtener el ID
            
            # Dispositivo 2: Controlador
            controlador = Dispositivo(
                nombre="Controlador Puerta Lab",
                descripcion="Controlador Mercury LP1502 - puerta laboratorio",
                tipo=TipoDispositivo.CONTROLADOR.value,
                marca="Mercury",
                modelo="LP1502",
                numero_serie="MC123456789",
                direccion_ip="192.168.1.102",
                puerto=4040,
                ubicacion_fisica="Laboratorio - Puerta principal",
                zona="Lab-A",
                estado=EstadoDispositivo.ONLINE.value,
                habilitado=True,
                monitoreado=True,
                etiquetas="acceso, mercury"
            )
            session.add(controlador)
            session.flush()
            
            # Dispositivo 3: UPS
            ups = Dispositivo(
                nombre="UPS Lab Mini",
                descripcion="UPS para equipos críticos del laboratorio",
                tipo=TipoDispositivo.UPS.value,
                marca="APC",
                modelo="Smart-UPS 750",
                direccion_ip="192.168.1.103",
                puerto=161,
                ubicacion_fisica="Laboratorio - Rack principal",
                zona="Lab-A",
                estado=EstadoDispositivo.ONLINE.value,
                habilitado=True,
                monitoreado=True,
                etiquetas="energia, critico"
            )
            session.add(ups)
            session.flush()
            
            # Sensores
            sensor_temp = crear_sensor_temperatura(camara.id)
            sensor_humedad = crear_sensor_humedad(camara.id)
            
            session.add(sensor_temp)
            session.add(sensor_humedad)
            
            gestor_bd.logger.info("✓ Datos de demostración creados")
            
    except Exception as e:
        gestor_bd.logger.error(f"Error creando datos demo: {e}")

if __name__ == "__main__":
    # Prueba del gestor de base de datos
    print("Probando gestor de base de datos...")
    
    # Verificar salud
    salud = obtener_salud_bd()
    print(f"Estado BD: {salud}")
    
    if verificar_bd_disponible():
        print("✓ Base de datos disponible")
        
        # Crear datos demo
        crear_datos_demo()
        
        # Verificar datos
        with obtener_sesion() as session:
            dispositivos = session.query(Dispositivo).all()
            sensores = session.query(Sensor).all()
            
            print(f"Dispositivos en BD: {len(dispositivos)}")
            for disp in dispositivos:
                print(f"  - {disp.nombre} ({disp.tipo}) - {disp.estado}")
                
            print(f"Sensores en BD: {len(sensores)}")
            for sensor in sensores:
                print(f"  - {sensor.tipo_sensor} - Dispositivo {sensor.dispositivo_id}")
                
    else:
        print("✗ Base de datos no disponible")
        
    print("✓ Prueba de gestor BD completada")