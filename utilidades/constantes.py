"""
Constantes del Sistema BMS Demo
==============================

Este módulo define todas las constantes utilizadas en el sistema BMS,
incluyendo códigos de error, mensajes, límites y configuraciones predeterminadas.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

from enum import Enum

# =============================================================================
# INFORMACIÓN DEL SISTEMA
# =============================================================================
NOMBRE_SISTEMA = "Sistema BMS Demo"
VERSION_SISTEMA = "1.0.0"
AUTOR_SISTEMA = "Equipo BMS Demo"
COPYRIGHT = "© 2024 Sistema BMS Demo"

# =============================================================================
# CÓDIGOS DE RESPUESTA Y ESTADOS
# =============================================================================
class CodigoRespuesta(Enum):
    """Códigos de respuesta estándar del sistema."""
    EXITO = 200
    CREADO = 201
    ACEPTADO = 202
    SIN_CONTENIDO = 204
    BAD_REQUEST = 400
    NO_AUTORIZADO = 401
    NO_ENCONTRADO = 404
    CONFLICT = 409
    ERROR_INTERNO = 500
    SERVICIO_NO_DISPONIBLE = 503
    TIMEOUT = 504

class CodigoErrorModbus(Enum):
    """Códigos de error específicos de Modbus."""
    FUNCION_ILEGAL = 1
    DIRECCION_DATOS_ILEGAL = 2
    VALOR_DATOS_ILEGAL = 3
    FALLA_DISPOSITIVO_ESCLAVO = 4
    ACKNOWLEDGE = 5
    DISPOSITIVO_ESCLAVO_OCUPADO = 6
    FALLA_MEMORIA_PARIDAD = 8
    GATEWAY_PATH_NO_DISPONIBLE = 10
    GATEWAY_DISPOSITIVO_OBJETIVO_NO_RESPONDE = 11

# =============================================================================
# LÍMITES Y RANGOS DEL SISTEMA
# =============================================================================
class LimitesSistema:
    """Límites generales del sistema."""
    MAX_DISPOSITIVOS = 1000
    MAX_SENSORES_POR_DISPOSITIVO = 50
    MAX_EVENTOS_POR_DIA = 10000
    MAX_CONEXIONES_CONCURRENTES = 100
    MAX_TAMAÑO_LOG_MB = 50
    MAX_DIAS_RETENCION_EVENTOS = 90
    MAX_DIAS_RETENCION_LOGS = 30

class LimitesRed:
    """Límites de red y comunicación."""
    TIMEOUT_MINIMO = 1
    TIMEOUT_MAXIMO = 300
    REINTENTOS_MINIMO = 0
    REINTENTOS_MAXIMO = 10
    PUERTO_MINIMO = 1
    PUERTO_MAXIMO = 65535
    INTERVALO_POLLING_MINIMO = 1
    INTERVALO_POLLING_MAXIMO = 3600

class RangosSensores:
    """Rangos típicos para sensores."""
    TEMPERATURA_MIN = -50.0
    TEMPERATURA_MAX = 100.0
    HUMEDAD_MIN = 0.0
    HUMEDAD_MAX = 100.0
    PRESION_MIN = 800.0
    PRESION_MAX = 1200.0
    LUMINOSIDAD_MIN = 0.0
    LUMINOSIDAD_MAX = 100000.0
    VOLTAJE_MIN = 0.0
    VOLTAJE_MAX = 1000.0
    CORRIENTE_MIN = 0.0
    CORRIENTE_MAX = 1000.0

# =============================================================================
# CONFIGURACIÓN DE PROTOCOLOS
# =============================================================================
class ConfigModbus:
    """Configuración por defecto para Modbus."""
    PUERTO_TCP_DEFAULT = 502
    PUERTO_RTU_DEFAULT = "/dev/ttyUSB0"
    BAUDRATE_DEFAULT = 9600
    DATABITS_DEFAULT = 8
    PARITY_DEFAULT = "N"
    STOPBITS_DEFAULT = 1
    TIMEOUT_DEFAULT = 5
    REINTENTOS_DEFAULT = 3
    ID_ESCLAVO_DEFAULT = 1
    
    # Funciones Modbus
    LEER_COILS = 1
    LEER_DISCRETE_INPUTS = 2
    LEER_HOLDING_REGISTERS = 3
    LEER_INPUT_REGISTERS = 4
    ESCRIBIR_SINGLE_COIL = 5
    ESCRIBIR_SINGLE_REGISTER = 6
    ESCRIBIR_MULTIPLE_COILS = 15
    ESCRIBIR_MULTIPLE_REGISTERS = 16

class ConfigMQTT:
    """Configuración por defecto para MQTT."""
    PUERTO_DEFAULT = 1883
    PUERTO_SSL_DEFAULT = 8883
    KEEPALIVE_DEFAULT = 60
    QOS_DEFAULT = 1
    RETAIN_DEFAULT = False
    CLEAN_SESSION_DEFAULT = True

class ConfigBACnet:
    """Configuración por defecto para BACnet."""
    PUERTO_DEFAULT = 47808
    DEVICE_ID_DEFAULT = 1001
    MAX_APDU_LENGTH_DEFAULT = 1024
    SEGMENTATION_DEFAULT = "segmentedBoth"
    VENDOR_ID_DEFAULT = 999

class ConfigSNMP:
    """Configuración por defecto para SNMP."""
    PUERTO_DEFAULT = 161
    VERSION_DEFAULT = "2c"
    COMUNIDAD_DEFAULT = "public"
    TIMEOUT_DEFAULT = 5
    REINTENTOS_DEFAULT = 3

# =============================================================================
# MENSAJES DEL SISTEMA
# =============================================================================
class MensajesError:
    """Mensajes de error estándar."""
    CONEXION_FALLIDA = "Error al establecer conexión"
    TIMEOUT_CONEXION = "Timeout en conexión"
    DISPOSITIVO_NO_ENCONTRADO = "Dispositivo no encontrado"
    CONFIGURACION_INVALIDA = "Configuración inválida"
    DATOS_INVALIDOS = "Datos proporcionados son inválidos"
    PERMISO_DENEGADO = "Permiso denegado"
    SERVICIO_NO_DISPONIBLE = "Servicio no disponible"
    BASE_DATOS_ERROR = "Error en base de datos"
    PROTOCOLO_NO_SOPORTADO = "Protocolo no soportado"
    SENSOR_FUERA_RANGO = "Sensor fuera de rango"

class MensajesExito:
    """Mensajes de éxito estándar."""
    CONEXION_ESTABLECIDA = "Conexión establecida exitosamente"
    DISPOSITIVO_AGREGADO = "Dispositivo agregado correctamente"
    CONFIGURACION_GUARDADA = "Configuración guardada exitosamente"
    DATOS_ACTUALIZADOS = "Datos actualizados correctamente"
    OPERACION_COMPLETADA = "Operación completada exitosamente"
    SISTEMA_INICIADO = "Sistema iniciado correctamente"
    BACKUP_CREADO = "Backup creado exitosamente"

# =============================================================================
# CONFIGURACIÓN DE ALERTAS
# =============================================================================
class TipoAlerta(Enum):
    """Tipos de alertas del sistema."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class PrioridadAlerta(Enum):
    """Prioridades de alertas."""
    BAJA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4

class CodigoAlerta:
    """Códigos de alertas específicas."""
    DISPOSITIVO_OFFLINE = "DEV_001"
    SENSOR_FUERA_RANGO = "SEN_001"
    COMUNICACION_PERDIDA = "COM_001"
    MEMORIA_INSUFICIENTE = "SYS_001"
    DISCO_LLENO = "SYS_002"
    TEMPERATURA_ALTA = "ENV_001"
    HUMEDAD_ALTA = "ENV_002"
    PRESION_ANORMAL = "ENV_003"
    UPS_BATERIA_BAJA = "PWR_001"
    UPS_EN_BATERIA = "PWR_002"

# =============================================================================
# CONFIGURACIÓN DE ARCHIVOS Y RUTAS
# =============================================================================
class RutasArchivos:
    """Rutas de archivos del sistema."""
    LOGS = "./logs/"
    BASE_DATOS = "./base_datos/"
    CONFIGURACION = "./configuracion/"
    BACKUPS = "./backups/"
    TEMP = "./temp/"
    REPORTES = "./reportes/"
    PLANTILLAS = "./interfaz_web/plantillas/"
    ESTATICOS = "./interfaz_web/estaticos/"

class NombresArchivos:
    """Nombres de archivos estándar."""
    LOG_SISTEMA = "sistema_bms.log"
    LOG_MODBUS = "protocolo_modbus.log"
    LOG_MQTT = "protocolo_mqtt.log"
    LOG_ERRORES = "errores.log"
    BD_SQLITE = "bms_demo.db"
    CONFIG_ENV = "configuracion.env"

# =============================================================================
# CONFIGURACIÓN DE INTERFAZ WEB
# =============================================================================
class ConfigWeb:
    """Configuración de la interfaz web."""
    PUERTO_DEFAULT = 5000
    HOST_DEFAULT = "0.0.0.0"
    DEBUG_DEFAULT = True
    TIMEOUT_SESSION = 3600
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class RutasAPI:
    """Rutas de la API REST."""
    BASE = "/api/v1"
    DISPOSITIVOS = "/dispositivos"
    SENSORES = "/sensores"
    EVENTOS = "/eventos"
    ESTADO = "/estado"
    CONFIGURACION = "/configuracion"
    ALERTAS = "/alertas"

# =============================================================================
# CONFIGURACIÓN DE FORMATO DE DATOS
# =============================================================================
class FormatoDatos:
    """Formatos de datos estándar."""
    FECHA_HORA = "%Y-%m-%d %H:%M:%S"
    FECHA = "%Y-%m-%d"
    HORA = "%H:%M:%S"
    TIMESTAMP = "%Y%m%d_%H%M%S"
    
class PrecisionDecimal:
    """Precisión decimal para diferentes tipos de datos."""
    TEMPERATURA = 1
    HUMEDAD = 0
    PRESION = 1
    VOLTAJE = 2
    CORRIENTE = 3
    ENERGIA = 2

# =============================================================================
# CONFIGURACIÓN DE SIMULACIÓN (PARA DESARROLLO)
# =============================================================================
class ConfigSimulacion:
    """Configuración para modo de simulación."""
    INTERVALO_ACTUALIZACION = 5  # segundos
    VARIACION_TEMPERATURA = 2.0  # grados
    VARIACION_HUMEDAD = 5.0  # porcentaje
    VARIACION_PRESION = 10.0  # mbar
    PROBABILIDAD_ERROR = 0.05  # 5%
    PROBABILIDAD_OFFLINE = 0.02  # 2%

# =============================================================================
# PATRONES DE VALIDACIÓN
# =============================================================================
class PatronesValidacion:
    """Patrones regex para validación."""
    IP_ADDRESS = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    MAC_ADDRESS = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    NUMERO_SERIE = r"^[A-Z0-9]{8,20}$"
    VERSION = r"^\d+\.\d+\.\d+$"

# =============================================================================
# CONFIGURACIÓN DE MONITOREO
# =============================================================================
class ConfigMonitoreo:
    """Configuración de monitoreo del sistema."""
    INTERVALO_HEARTBEAT = 60  # segundos
    INTERVALO_VERIFICACION_DISPOSITIVOS = 120  # segundos
    INTERVALO_LIMPIEZA_LOGS = 86400  # 24 horas en segundos
    INTERVALO_BACKUP = 604800  # 7 días en segundos
    UMBRAL_MEMORIA = 80  # porcentaje
    UMBRAL_DISCO = 90  # porcentaje
    UMBRAL_CPU = 85  # porcentaje

# =============================================================================
# DICCIONARIOS DE MAPEO
# =============================================================================
MAPEO_TIPOS_DISPOSITIVO = {
    "camera": "camara",
    "door_controller": "controlador",
    "sensor": "sensor",
    "ups": "ups",
    "server": "servidor",
    "switch": "switch",
    "access_point": "access_point"
}

MAPEO_ESTADOS_DISPOSITIVO = {
    "up": "online",
    "down": "offline",
    "unknown": "desconocido",
    "maintenance": "mantenimiento",
    "error": "error"
}

MAPEO_UNIDADES_MEDIDA = {
    "celsius": "°C",
    "fahrenheit": "°F",
    "kelvin": "K",
    "percent": "%",
    "pascal": "Pa",
    "bar": "bar",
    "millibar": "mbar",
    "lux": "lux",
    "volt": "V",
    "ampere": "A",
    "watt": "W",
    "kilowatt": "kW"
}

# =============================================================================
# FUNCIONES DE UTILIDAD PARA CONSTANTES
# =============================================================================
def obtener_mensaje_error(codigo: str) -> str:
    """
    Obtener mensaje de error por código.
    
    Args:
        codigo: Código de error
        
    Returns:
        Mensaje de error correspondiente
    """
    mensajes = {
        "DEV_001": "Dispositivo fuera de línea",
        "SEN_001": "Sensor fuera de rango",
        "COM_001": "Comunicación perdida",
        "SYS_001": "Memoria insuficiente",
        "SYS_002": "Disco lleno",
        "ENV_001": "Temperatura alta",
        "ENV_002": "Humedad alta",
        "ENV_003": "Presión anormal",
        "PWR_001": "Batería UPS baja",
        "PWR_002": "UPS funcionando con batería"
    }
    return mensajes.get(codigo, "Error desconocido")

def validar_rango_sensor(tipo_sensor: str, valor: float) -> bool:
    """
    Validar si un valor está en el rango típico para el tipo de sensor.
    
    Args:
        tipo_sensor: Tipo de sensor
        valor: Valor a validar
        
    Returns:
        True si está en rango, False si no
    """
    rangos = {
        "temperatura": (RangosSensores.TEMPERATURA_MIN, RangosSensores.TEMPERATURA_MAX),
        "humedad": (RangosSensores.HUMEDAD_MIN, RangosSensores.HUMEDAD_MAX),
        "presion": (RangosSensores.PRESION_MIN, RangosSensores.PRESION_MAX),
        "luminosidad": (RangosSensores.LUMINOSIDAD_MIN, RangosSensores.LUMINOSIDAD_MAX),
        "voltaje": (RangosSensores.VOLTAJE_MIN, RangosSensores.VOLTAJE_MAX),
        "corriente": (RangosSensores.CORRIENTE_MIN, RangosSensores.CORRIENTE_MAX)
    }
    
    if tipo_sensor in rangos:
        min_val, max_val = rangos[tipo_sensor]
        return min_val <= valor <= max_val
    
    return True  # Si no conocemos el tipo, asumimos que es válido

def obtener_precision_decimal(tipo_sensor: str) -> int:
    """
    Obtener precisión decimal recomendada para un tipo de sensor.
    
    Args:
        tipo_sensor: Tipo de sensor
        
    Returns:
        Número de decimales recomendado
    """
    precisiones = {
        "temperatura": PrecisionDecimal.TEMPERATURA,
        "humedad": PrecisionDecimal.HUMEDAD,
        "presion": PrecisionDecimal.PRESION,
        "voltaje": PrecisionDecimal.VOLTAJE,
        "corriente": PrecisionDecimal.CORRIENTE,
        "energia": PrecisionDecimal.ENERGIA
    }
    
    return precisiones.get(tipo_sensor, 2)  # 2 decimales por defecto

if __name__ == "__main__":
    # Prueba de constantes
    print("Probando constantes del sistema...")
    
    print(f"Sistema: {NOMBRE_SISTEMA} v{VERSION_SISTEMA}")
    print(f"Límite máximo de dispositivos: {LimitesSistema.MAX_DISPOSITIVOS}")
    print(f"Puerto Modbus por defecto: {ConfigModbus.PUERTO_TCP_DEFAULT}")
    
    # Probar validación
    print(f"Temperatura 25°C válida: {validar_rango_sensor('temperatura', 25.0)}")
    print(f"Temperatura 150°C válida: {validar_rango_sensor('temperatura', 150.0)}")
    
    # Probar mensajes
    print(f"Mensaje error DEV_001: {obtener_mensaje_error('DEV_001')}")
    
    # Probar precisión
    print(f"Precisión temperatura: {obtener_precision_decimal('temperatura')} decimales")
    
    print("✓ Prueba de constantes completada")