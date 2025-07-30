"""
Modelo de Dispositivo para Sistema BMS
=====================================

Este módulo define la clase base Dispositivo y modelos relacionados para
representar todos los tipos de dispositivos en el sistema BMS.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Base para modelos SQLAlchemy
Base = declarative_base()

class TipoDispositivo(Enum):
    """Tipos de dispositivos soportados por el sistema BMS."""
    CAMARA = "camara"
    CONTROLADOR = "controlador"
    SENSOR = "sensor"
    UPS = "ups"
    VENTILADOR = "ventilador"
    ALARMA = "alarma"
    GATEWAY = "gateway"
    SERVIDOR = "servidor"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"

class EstadoDispositivo(Enum):
    """Estados posibles de un dispositivo."""
    DESCONOCIDO = "desconocido"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MANTENIMIENTO = "mantenimiento"
    CONFIGURANDO = "configurando"
    ACTUALIZANDO = "actualizando"

class ProtocoloComunicacion(Enum):
    """Protocolos de comunicación soportados."""
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    MQTT = "mqtt"
    HTTP = "http"
    SNMP = "snmp"
    BACNET = "bacnet"
    TCP_IP = "tcp_ip"
    SERIAL = "serial"

@dataclass
class ConfiguracionDispositivo:
    """Configuración específica de un dispositivo."""
    ip: Optional[str] = None
    puerto: Optional[int] = None
    protocolo: Optional[ProtocoloComunicacion] = None
    usuario: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    reintentos: int = 3
    intervalo_polling: int = 60
    parametros_especificos: Dict[str, Any] = field(default_factory=dict)
    
    def validar(self) -> List[str]:
        """
        Validar configuración del dispositivo.
        
        Returns:
            Lista de errores de validación
        """
        errores = []
        
        if self.ip and not self._validar_ip(self.ip):
            errores.append(f"IP inválida: {self.ip}")
            
        if self.puerto and not (1 <= self.puerto <= 65535):
            errores.append(f"Puerto inválido: {self.puerto}")
            
        if self.timeout <= 0:
            errores.append("Timeout debe ser mayor a 0")
            
        if self.reintentos < 0:
            errores.append("Reintentos no puede ser negativo")
            
        if self.intervalo_polling <= 0:
            errores.append("Intervalo de polling debe ser mayor a 0")
            
        return errores
        
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

class Dispositivo(Base):
    """
    Modelo principal de dispositivo para el sistema BMS.
    Representa cualquier dispositivo físico o lógico del sistema.
    """
    
    __tablename__ = 'dispositivos'
    
    # Campos principales
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, index=True)
    descripcion = Column(Text)
    tipo = Column(String(50), nullable=False, index=True)
    marca = Column(String(50))
    modelo = Column(String(50))
    numero_serie = Column(String(100))
    
    # Ubicación y organización
    ubicacion_fisica = Column(String(200))
    zona = Column(String(50))
    edificio = Column(String(50))
    piso = Column(String(20))
    
    # Configuración de red
    direccion_ip = Column(String(15), index=True)
    puerto = Column(Integer)
    direccion_mac = Column(String(17))
    protocolo_comunicacion = Column(String(20))
    
    # Estado y monitoreo
    estado = Column(String(20), nullable=False, default='desconocido', index=True)
    estado_anterior = Column(String(20))
    ultima_comunicacion = Column(DateTime)
    tiempo_respuesta = Column(Float)
    
    # Configuración
    configuracion_json = Column(Text)  # JSON con configuración específica
    habilitado = Column(Boolean, default=True, nullable=False)
    monitoreado = Column(Boolean, default=True, nullable=False)
    
    # Metadatos
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    fecha_ultima_verificacion = Column(DateTime)
    
    # Relaciones y referencias
    dispositivo_padre_id = Column(Integer)  # Para dispositivos jerárquicos
    grupo_dispositivos = Column(String(50))
    etiquetas = Column(Text)  # Tags separados por comas
    
    def __init__(self, **kwargs):
        """Inicializar dispositivo con valores por defecto."""
        super().__init__(**kwargs)
        self._configuracion_obj = None
        
    @property
    def configuracion(self) -> ConfiguracionDispositivo:
        """Obtener configuración como objeto."""
        if self._configuracion_obj is None:
            import json
            if self.configuracion_json:
                try:
                    config_dict = json.loads(self.configuracion_json)
                    self._configuracion_obj = ConfiguracionDispositivo(**config_dict)
                except (json.JSONDecodeError, TypeError):
                    self._configuracion_obj = ConfiguracionDispositivo()
            else:
                self._configuracion_obj = ConfiguracionDispositivo()
        return self._configuracion_obj
        
    @configuracion.setter
    def configuracion(self, config: ConfiguracionDispositivo):
        """Establecer configuración desde objeto."""
        import json
        from dataclasses import asdict
        
        self._configuracion_obj = config
        # Convertir enum a string para JSON
        config_dict = asdict(config)
        if config_dict.get('protocolo'):
            config_dict['protocolo'] = config_dict['protocolo'].value
            
        self.configuracion_json = json.dumps(config_dict)
        
    def actualizar_estado(self, nuevo_estado: EstadoDispositivo, tiempo_respuesta: float = None):
        """
        Actualizar estado del dispositivo.
        
        Args:
            nuevo_estado: Nuevo estado del dispositivo
            tiempo_respuesta: Tiempo de respuesta en segundos
        """
        self.estado_anterior = self.estado
        self.estado = nuevo_estado.value
        self.ultima_comunicacion = datetime.now()
        if tiempo_respuesta is not None:
            self.tiempo_respuesta = tiempo_respuesta
        self.fecha_ultima_verificacion = datetime.now()
        
    def esta_online(self) -> bool:
        """Verificar si el dispositivo está online."""
        return self.estado == EstadoDispositivo.ONLINE.value
        
    def esta_disponible(self) -> bool:
        """Verificar si el dispositivo está disponible para comunicación."""
        estados_disponibles = [
            EstadoDispositivo.ONLINE.value,
            EstadoDispositivo.CONFIGURANDO.value
        ]
        return self.estado in estados_disponibles and self.habilitado
        
    def obtener_tiempo_sin_comunicacion(self) -> Optional[float]:
        """
        Obtener tiempo transcurrido desde la última comunicación.
        
        Returns:
            Tiempo en segundos o None si nunca se comunicó
        """
        if self.ultima_comunicacion:
            delta = datetime.now() - self.ultima_comunicacion
            return delta.total_seconds()
        return None
        
    def requiere_atencion(self) -> bool:
        """Verificar si el dispositivo requiere atención."""
        # Dispositivo en error
        if self.estado in [EstadoDispositivo.ERROR.value, EstadoDispositivo.OFFLINE.value]:
            return True
            
        # Sin comunicación por mucho tiempo
        tiempo_sin_comunicacion = self.obtener_tiempo_sin_comunicacion()
        if tiempo_sin_comunicacion and tiempo_sin_comunicacion > 300:  # 5 minutos
            return True
            
        # Tiempo de respuesta muy alto
        if self.tiempo_respuesta and self.tiempo_respuesta > 10:  # 10 segundos
            return True
            
        return False
        
    def obtener_etiquetas(self) -> List[str]:
        """Obtener lista de etiquetas del dispositivo."""
        if self.etiquetas:
            return [tag.strip() for tag in self.etiquetas.split(',') if tag.strip()]
        return []
        
    def agregar_etiqueta(self, etiqueta: str):
        """Agregar etiqueta al dispositivo."""
        etiquetas_actuales = self.obtener_etiquetas()
        if etiqueta not in etiquetas_actuales:
            etiquetas_actuales.append(etiqueta)
            self.etiquetas = ', '.join(etiquetas_actuales)
            
    def remover_etiqueta(self, etiqueta: str):
        """Remover etiqueta del dispositivo."""
        etiquetas_actuales = self.obtener_etiquetas()
        if etiqueta in etiquetas_actuales:
            etiquetas_actuales.remove(etiqueta)
            self.etiquetas = ', '.join(etiquetas_actuales)
            
    def validar_configuracion(self) -> List[str]:
        """
        Validar configuración del dispositivo.
        
        Returns:
            Lista de errores de validación
        """
        errores = []
        
        # Validaciones básicas
        if not self.nombre or not self.nombre.strip():
            errores.append("Nombre es requerido")
            
        if not self.tipo:
            errores.append("Tipo de dispositivo es requerido")
            
        # Validar tipo
        tipos_validos = [t.value for t in TipoDispositivo]
        if self.tipo not in tipos_validos:
            errores.append(f"Tipo de dispositivo inválido: {self.tipo}")
            
        # Validar estado
        estados_validos = [e.value for e in EstadoDispositivo]
        if self.estado not in estados_validos:
            errores.append(f"Estado inválido: {self.estado}")
            
        # Validar configuración específica
        if self.configuracion:
            errores.extend(self.configuracion.validar())
            
        return errores
        
    def to_dict(self, incluir_configuracion: bool = True) -> Dict[str, Any]:
        """
        Convertir dispositivo a diccionario.
        
        Args:
            incluir_configuracion: Si incluir configuración detallada
            
        Returns:
            Diccionario con datos del dispositivo
        """
        resultado = {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'marca': self.marca,
            'modelo': self.modelo,
            'numero_serie': self.numero_serie,
            'ubicacion_fisica': self.ubicacion_fisica,
            'zona': self.zona,
            'direccion_ip': self.direccion_ip,
            'puerto': self.puerto,
            'estado': self.estado,
            'estado_anterior': self.estado_anterior,
            'ultima_comunicacion': self.ultima_comunicacion.isoformat() if self.ultima_comunicacion else None,
            'tiempo_respuesta': self.tiempo_respuesta,
            'habilitado': self.habilitado,
            'monitoreado': self.monitoreado,
            'etiquetas': self.obtener_etiquetas(),
            'tiempo_sin_comunicacion': self.obtener_tiempo_sin_comunicacion(),
            'requiere_atencion': self.requiere_atencion(),
            'esta_online': self.esta_online()
        }
        
        if incluir_configuracion and self.configuracion:
            from dataclasses import asdict
            config_dict = asdict(self.configuracion)
            if config_dict.get('protocolo'):
                config_dict['protocolo'] = config_dict['protocolo'].value
            resultado['configuracion'] = config_dict
            
        return resultado
        
    def __repr__(self):
        """Representación string del dispositivo."""
        return f"<Dispositivo(id={self.id}, nombre='{self.nombre}', tipo='{self.tipo}', estado='{self.estado}')>"
        
    def __str__(self):
        """String descriptivo del dispositivo."""
        return f"{self.nombre} ({self.tipo}) - {self.estado}"

# Funciones de utilidad
def crear_dispositivo_desde_genetec(datos_genetec: Dict[str, Any]) -> Dispositivo:
    """
    Crear dispositivo desde datos de Genetec.
    
    Args:
        datos_genetec: Datos del dispositivo desde Genetec
        
    Returns:
        Instancia de Dispositivo configurada
    """
    # Mapear tipos de Genetec a nuestros tipos
    mapeo_tipos = {
        'camera': TipoDispositivo.CAMARA.value,
        'door_controller': TipoDispositivo.CONTROLADOR.value,
        'sensor': TipoDispositivo.SENSOR.value,
        'server': TipoDispositivo.SERVIDOR.value
    }
    
    tipo_dispositivo = mapeo_tipos.get(
        datos_genetec.get('type', '').lower(),
        TipoDispositivo.SENSOR.value
    )
    
    # Crear configuración
    config = ConfiguracionDispositivo(
        ip=datos_genetec.get('ip_address'),
        puerto=datos_genetec.get('port'),
        protocolo=ProtocoloComunicacion.TCP_IP,
        timeout=30,
        intervalo_polling=60,
        parametros_especificos=datos_genetec.get('specific_config', {})
    )
    
    # Crear dispositivo
    dispositivo = Dispositivo(
        nombre=datos_genetec.get('name', 'Dispositivo Sin Nombre'),
        descripcion=datos_genetec.get('description', ''),
        tipo=tipo_dispositivo,
        marca=datos_genetec.get('manufacturer', ''),
        modelo=datos_genetec.get('model', ''),
        numero_serie=datos_genetec.get('serial_number', ''),
        direccion_ip=datos_genetec.get('ip_address'),
        puerto=datos_genetec.get('port'),
        ubicacion_fisica=datos_genetec.get('location', ''),
        zona=datos_genetec.get('zone', ''),
        estado=EstadoDispositivo.DESCONOCIDO.value,
        habilitado=datos_genetec.get('enabled', True),
        monitoreado=datos_genetec.get('monitored', True)
    )
    
    dispositivo.configuracion = config
    
    return dispositivo

def buscar_dispositivos_por_tipo(dispositivos: List[Dispositivo], tipo: TipoDispositivo) -> List[Dispositivo]:
    """
    Buscar dispositivos por tipo.
    
    Args:
        dispositivos: Lista de dispositivos
        tipo: Tipo a buscar
        
    Returns:
        Lista de dispositivos del tipo especificado
    """
    return [d for d in dispositivos if d.tipo == tipo.value]

def obtener_dispositivos_online(dispositivos: List[Dispositivo]) -> List[Dispositivo]:
    """
    Obtener dispositivos que están online.
    
    Args:
        dispositivos: Lista de dispositivos
        
    Returns:
        Lista de dispositivos online
    """
    return [d for d in dispositivos if d.esta_online()]

def obtener_dispositivos_requieren_atencion(dispositivos: List[Dispositivo]) -> List[Dispositivo]:
    """
    Obtener dispositivos que requieren atención.
    
    Args:
        dispositivos: Lista de dispositivos
        
    Returns:
        Lista de dispositivos que requieren atención
    """
    return [d for d in dispositivos if d.requiere_atencion()]

if __name__ == "__main__":
    # Prueba del modelo de dispositivo
    print("Probando modelo de dispositivo...")
    
    # Crear dispositivo de prueba
    config = ConfiguracionDispositivo(
        ip="192.168.1.100",
        puerto=80,
        protocolo=ProtocoloComunicacion.HTTP,
        timeout=30
    )
    
    dispositivo = Dispositivo(
        nombre="Cámara Demo 01",
        descripcion="Cámara de prueba para laboratorio",
        tipo=TipoDispositivo.CAMARA.value,
        marca="Axis",
        modelo="P1455-LE",
        direccion_ip="192.168.1.100",
        puerto=80,
        ubicacion_fisica="Laboratorio - Entrada principal"
    )
    
    dispositivo.configuracion = config
    
    # Probar métodos
    print(f"Dispositivo: {dispositivo}")
    print(f"Está online: {dispositivo.esta_online()}")
    print(f"Requiere atención: {dispositivo.requiere_atencion()}")
    
    # Actualizar estado
    dispositivo.actualizar_estado(EstadoDispositivo.ONLINE, 0.5)
    print(f"Nuevo estado: {dispositivo.estado}")
    
    # Agregar etiquetas
    dispositivo.agregar_etiqueta("seguridad")
    dispositivo.agregar_etiqueta("laboratorio")
    print(f"Etiquetas: {dispositivo.obtener_etiquetas()}")
    
    # Validar
    errores = dispositivo.validar_configuracion()
    if errores:
        print(f"Errores de validación: {errores}")
    else:
        print("✓ Configuración válida")
        
    # Convertir a dict
    dict_dispositivo = dispositivo.to_dict()
    print(f"Como dict: {dict_dispositivo['nombre']} - {dict_dispositivo['estado']}")
    
    print("✓ Prueba de modelo de dispositivo completada")