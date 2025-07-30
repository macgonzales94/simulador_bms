"""
Configuración de Protocolos de Comunicación
==========================================

Este módulo contiene la configuración específica para todos los protocolos
de comunicación soportados por el sistema BMS: Modbus, MQTT, BACnet, SNMP, HTTP.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Cargar variables de entorno
load_dotenv('configuracion.env')

class TipoProtocolo(Enum):
    """Enumeración de tipos de protocolo soportados."""
    MODBUS = "modbus"
    MQTT = "mqtt"
    BACNET = "bacnet"
    SNMP = "snmp"
    HTTP = "http"

@dataclass
class ConfiguracionModbus:
    """Configuración específica para protocolo Modbus."""
    ip: str
    puerto: int
    timeout: int
    reintentos: int
    id_esclavo: int
    funcion_lectura: int
    funcion_escritura: int
    registro_inicio: int
    cantidad_registros: int
    intervalo_polling: int
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if not (1 <= self.puerto <= 65535):
            raise ValueError(f"Puerto Modbus inválido: {self.puerto}")
        if not (1 <= self.id_esclavo <= 247):
            raise ValueError(f"ID esclavo Modbus inválido: {self.id_esclavo}")

@dataclass
class ConfiguracionMQTT:
    """Configuración específica para protocolo MQTT."""
    broker: str
    puerto: int
    usuario: str
    password: str
    timeout: int
    keepalive: int
    qos: int
    retain: bool
    topico_base: str
    topico_comandos: str
    topico_eventos: str
    topico_estados: str
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if not (1 <= self.puerto <= 65535):
            raise ValueError(f"Puerto MQTT inválido: {self.puerto}")
        if not (0 <= self.qos <= 2):
            raise ValueError(f"QoS MQTT inválido: {self.qos}")

@dataclass
class ConfiguracionBACnet:
    """Configuración específica para protocolo BACnet."""
    ip: str
    puerto: int
    device_id: int
    network_number: int
    max_apdu_length: int
    segmentation: str
    vendor_id: int
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if not (1 <= self.puerto <= 65535):
            raise ValueError(f"Puerto BACnet inválido: {self.puerto}")
        if not (0 <= self.device_id <= 4194303):
            raise ValueError(f"Device ID BACnet inválido: {self.device_id}")

@dataclass
class ConfiguracionSNMP:
    """Configuración específica para protocolo SNMP."""
    ip: str
    puerto: int
    comunidad: str
    version: str
    timeout: int
    reintentos: int
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if not (1 <= self.puerto <= 65535):
            raise ValueError(f"Puerto SNMP inválido: {self.puerto}")
        if self.version not in ['1', '2c', '3']:
            raise ValueError(f"Versión SNMP inválida: {self.version}")

@dataclass
class ConfiguracionHTTP:
    """Configuración específica para protocolo HTTP."""
    ip: str
    puerto: int
    ssl: bool
    timeout: int
    auth_usuario: str
    auth_password: str
    headers: Dict[str, str]
    endpoints: Dict[str, str]
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if not (1 <= self.puerto <= 65535):
            raise ValueError(f"Puerto HTTP inválido: {self.puerto}")

class ConfiguradorProtocolos:
    """
    Clase principal para manejar configuración de todos los protocolos.
    """
    
    def __init__(self):
        """Inicializar configurador de protocolos."""
        self.cargar_configuraciones()
        
    def cargar_configuraciones(self):
        """Cargar configuraciones de todos los protocolos."""
        self.modbus = self._cargar_modbus()
        self.mqtt = self._cargar_mqtt()
        self.bacnet = self._cargar_bacnet()
        self.snmp = self._cargar_snmp()
        self.http = self._cargar_http()
        
    def _cargar_modbus(self) -> ConfiguracionModbus:
        """Cargar configuración Modbus desde variables de entorno."""
        return ConfiguracionModbus(
            ip=os.getenv('MODBUS_IP', '192.168.1.95'),
            puerto=int(os.getenv('MODBUS_PUERTO', 502)),
            timeout=int(os.getenv('MODBUS_TIMEOUT', 5)),
            reintentos=int(os.getenv('MODBUS_REINTENTOS', 3)),
            id_esclavo=int(os.getenv('MODBUS_ID_ESCLAVO', 1)),
            funcion_lectura=int(os.getenv('MODBUS_FUNCION_LECTURA', 3)),
            funcion_escritura=int(os.getenv('MODBUS_FUNCION_ESCRITURA', 16)),
            registro_inicio=int(os.getenv('MODBUS_REGISTRO_INICIO', 0)),
            cantidad_registros=int(os.getenv('MODBUS_CANTIDAD_REGISTROS', 10)),
            intervalo_polling=int(os.getenv('MODBUS_INTERVALO_POLLING', 5))
        )
        
    def _cargar_mqtt(self) -> ConfiguracionMQTT:
        """Cargar configuración MQTT desde variables de entorno."""
        return ConfiguracionMQTT(
            broker=os.getenv('MQTT_BROKER', '192.168.1.95'),
            puerto=int(os.getenv('MQTT_PUERTO', 1883)),
            usuario=os.getenv('MQTT_USUARIO', 'bms_user'),
            password=os.getenv('MQTT_PASSWORD', 'bms_demo'),
            timeout=int(os.getenv('MQTT_TIMEOUT', 60)),
            keepalive=int(os.getenv('MQTT_KEEPALIVE', 60)),
            qos=int(os.getenv('MQTT_QOS', 1)),
            retain=os.getenv('MQTT_RETAIN', 'False').lower() == 'true',
            topico_base=os.getenv('MQTT_TOPICO_BASE', 'bms/demo'),
            topico_comandos=os.getenv('MQTT_TOPICO_COMANDOS', 'bms/demo/comandos'),
            topico_eventos=os.getenv('MQTT_TOPICO_EVENTOS', 'bms/demo/eventos'),
            topico_estados=os.getenv('MQTT_TOPICO_ESTADOS', 'bms/demo/estados')
        )
        
    def _cargar_bacnet(self) -> ConfiguracionBACnet:
        """Cargar configuración BACnet desde variables de entorno."""
        return ConfiguracionBACnet(
            ip=os.getenv('BACNET_IP', '192.168.1.95'),
            puerto=int(os.getenv('BACNET_PUERTO', 47808)),
            device_id=int(os.getenv('BACNET_DEVICE_ID', 1001)),
            network_number=int(os.getenv('BACNET_NETWORK_NUMBER', 0)),
            max_apdu_length=int(os.getenv('BACNET_MAX_APDU_LENGTH', 1024)),
            segmentation=os.getenv('BACNET_SEGMENTATION', 'segmentedBoth'),
            vendor_id=int(os.getenv('BACNET_VENDOR_ID', 999))
        )
        
    def _cargar_snmp(self) -> ConfiguracionSNMP:
        """Cargar configuración SNMP desde variables de entorno."""
        return ConfiguracionSNMP(
            ip=os.getenv('SNMP_IP', '192.168.1.40'),
            puerto=int(os.getenv('SNMP_PUERTO', 161)),
            comunidad=os.getenv('SNMP_COMUNIDAD', 'public'),
            version=os.getenv('SNMP_VERSION', '2c'),
            timeout=int(os.getenv('SNMP_TIMEOUT', 5)),
            reintentos=int(os.getenv('SNMP_REINTENTOS', 3))
        )
        
    def _cargar_http(self) -> ConfiguracionHTTP:
        """Cargar configuración HTTP desde variables de entorno."""
        return ConfiguracionHTTP(
            ip=os.getenv('HTTP_IP', '192.168.1.40'),
            puerto=int(os.getenv('HTTP_PUERTO', 80)),
            ssl=os.getenv('HTTP_SSL', 'False').lower() == 'true',
            timeout=int(os.getenv('HTTP_TIMEOUT', 30)),
            auth_usuario=os.getenv('HTTP_AUTH_USUARIO', 'admin'),
            auth_password=os.getenv('HTTP_AUTH_PASSWORD', 'demo123'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'BMS-Demo/1.0'
            },
            endpoints={
                'dispositivos': '/api/dispositivos',
                'eventos': '/api/eventos',
                'estados': '/api/estados',
                'genetec_status': '/api/genetec/status'
            }
        )
        
    def obtener_configuracion(self, protocolo: TipoProtocolo):
        """Obtener configuración de un protocolo específico."""
        configuraciones = {
            TipoProtocolo.MODBUS: self.modbus,
            TipoProtocolo.MQTT: self.mqtt,
            TipoProtocolo.BACNET: self.bacnet,
            TipoProtocolo.SNMP: self.snmp,
            TipoProtocolo.HTTP: self.http
        }
        return configuraciones.get(protocolo)
        
    def obtener_configuraciones_todas(self) -> Dict[str, Any]:
        """Obtener diccionario con todas las configuraciones de protocolos."""
        return {
            'modbus': self.modbus.__dict__,
            'mqtt': self.mqtt.__dict__,
            'bacnet': self.bacnet.__dict__,
            'snmp': self.snmp.__dict__,
            'http': self.http.__dict__
        }
        
    def validar_protocolo_disponible(self, protocolo: TipoProtocolo) -> bool:
        """Validar si un protocolo está disponible y configurado correctamente."""
        try:
            config = self.obtener_configuracion(protocolo)
            return config is not None
        except Exception as e:
            print(f"Error validando protocolo {protocolo.value}: {e}")
            return False
            
    def obtener_protocolos_habilitados(self) -> List[TipoProtocolo]:
        """Obtener lista de protocolos habilitados y configurados."""
        protocolos_habilitados = []
        for protocolo in TipoProtocolo:
            if self.validar_protocolo_disponible(protocolo):
                protocolos_habilitados.append(protocolo)
        return protocolos_habilitados
        
    def mostrar_configuraciones(self):
        """Mostrar todas las configuraciones de protocolos."""
        print("\n" + "="*60)
        print("CONFIGURACIÓN DE PROTOCOLOS BMS")
        print("="*60)
        
        configuraciones = self.obtener_configuraciones_todas()
        
        for protocolo, config in configuraciones.items():
            print(f"\n[{protocolo.upper()}]")
            for clave, valor in config.items():
                # Ocultar passwords en la salida
                if 'password' in clave.lower():
                    valor = '*' * len(str(valor))
                print(f"  {clave}: {valor}")
        
        protocolos_habilitados = self.obtener_protocolos_habilitados()
        print(f"\nProtocolos habilitados: {[p.value for p in protocolos_habilitados]}")
        print("="*60)

# Instancia global de configuración de protocolos
configurador_protocolos = ConfiguradorProtocolos()

# Funciones de acceso rápido
def obtener_config_protocolo(protocolo: TipoProtocolo):
    """Obtener configuración de un protocolo específico."""
    return configurador_protocolos.obtener_configuracion(protocolo)

def obtener_config_modbus() -> ConfiguracionModbus:
    """Obtener configuración Modbus."""
    return configurador_protocolos.modbus

def obtener_config_mqtt() -> ConfiguracionMQTT:
    """Obtener configuración MQTT."""
    return configurador_protocolos.mqtt

def obtener_config_bacnet() -> ConfiguracionBACnet:
    """Obtener configuración BACnet."""
    return configurador_protocolos.bacnet

def obtener_config_snmp() -> ConfiguracionSNMP:
    """Obtener configuración SNMP."""
    return configurador_protocolos.snmp

def obtener_config_http() -> ConfiguracionHTTP:
    """Obtener configuración HTTP."""
    return configurador_protocolos.http

def obtener_protocolos_habilitados() -> List[TipoProtocolo]:
    """Obtener lista de protocolos habilitados."""
    return configurador_protocolos.obtener_protocolos_habilitados()

if __name__ == "__main__":
    # Prueba de configuración de protocolos
    print("Probando configuración de protocolos...")
    configurador_protocolos.mostrar_configuraciones()
    print("\n✓ Configuración de protocolos cargada correctamente")