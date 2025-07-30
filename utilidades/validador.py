"""
Validador de Datos para Sistema BMS
==================================

Este módulo proporciona funciones de validación para todos los tipos de datos
utilizados en el sistema BMS, incluyendo IPs, puertos, rangos de sensores, etc.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import re
import ipaddress
from typing import Any, List, Dict, Union, Tuple, Optional
from datetime import datetime, date
from enum import Enum

# Importar constantes
from utilidades.constantes import (
    LimitesRed, RangosSensores, PatronesValidacion,
    MAPEO_TIPOS_DISPOSITIVO, MAPEO_ESTADOS_DISPOSITIVO
)

class TipoValidacion(Enum):
    """Tipos de validación disponibles."""
    IP_ADDRESS = "ip_address"
    PUERTO = "puerto"
    EMAIL = "email"
    MAC_ADDRESS = "mac_address"
    NUMERO_SERIE = "numero_serie"
    VERSION = "version"
    RANGO_NUMERICO = "rango_numerico"
    LONGITUD_CADENA = "longitud_cadena"
    FECHA = "fecha"
    TIMESTAMP = "timestamp"

class ResultadoValidacion:
    """Resultado de una validación."""
    
    def __init__(self, es_valido: bool, mensaje: str = "", codigo_error: str = ""):
        """
        Inicializar resultado de validación.
        
        Args:
            es_valido: Si la validación fue exitosa
            mensaje: Mensaje descriptivo del resultado
            codigo_error: Código de error específico
        """
        self.es_valido = es_valido
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        
    def __bool__(self):
        """Permitir uso en contextos booleanos."""
        return self.es_valido
        
    def __str__(self):
        """Representación string del resultado."""
        return f"{'✓' if self.es_valido else '✗'} {self.mensaje}"

class ValidadorBMS:
    """
    Clase principal de validación para el sistema BMS.
    Proporciona métodos estáticos para validar diferentes tipos de datos.
    """
    
    @staticmethod
    def validar_ip_address(ip: str) -> ResultadoValidacion:
        """
        Validar dirección IP v4.
        
        Args:
            ip: Dirección IP a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        if not ip or not isinstance(ip, str):
            return ResultadoValidacion(False, "IP no puede estar vacía", "IP_EMPTY")
            
        try:
            # Usar ipaddress para validación robusta
            ip_obj = ipaddress.IPv4Address(ip)
            
            # Verificar que no sea dirección especial
            if ip_obj.is_multicast:
                return ResultadoValidacion(False, "IP multicast no permitida", "IP_MULTICAST")
            if ip_obj.is_loopback and ip != "127.0.0.1":
                return ResultadoValidacion(False, "IP loopback no permitida", "IP_LOOPBACK")
            if ip_obj.is_reserved:
                return ResultadoValidacion(False, "IP reservada no permitida", "IP_RESERVED")
                
            return ResultadoValidacion(True, f"IP válida: {ip}")
            
        except ipaddress.AddressValueError:
            return ResultadoValidacion(False, f"Formato de IP inválido: {ip}", "IP_FORMAT")
        except Exception as e:
            return ResultadoValidacion(False, f"Error validando IP: {str(e)}", "IP_ERROR")
            
    @staticmethod
    def validar_puerto(puerto: Union[int, str]) -> ResultadoValidacion:
        """
        Validar número de puerto.
        
        Args:
            puerto: Puerto a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        try:
            puerto_int = int(puerto)
            
            if not (LimitesRed.PUERTO_MINIMO <= puerto_int <= LimitesRed.PUERTO_MAXIMO):
                return ResultadoValidacion(
                    False, 
                    f"Puerto fuera de rango ({LimitesRed.PUERTO_MINIMO}-{LimitesRed.PUERTO_MAXIMO}): {puerto_int}",
                    "PUERTO_RANGO"
                )
                
            # Verificar puertos bien conocidos (opcional warning)
            if puerto_int < 1024:
                return ResultadoValidacion(
                    True, 
                    f"Puerto válido (privilegiado): {puerto_int}",
                    "PUERTO_PRIVILEGIADO"
                )
                
            return ResultadoValidacion(True, f"Puerto válido: {puerto_int}")
            
        except (ValueError, TypeError):
            return ResultadoValidacion(False, f"Puerto debe ser numérico: {puerto}", "PUERTO_FORMAT")
            
    @staticmethod
    def validar_email(email: str) -> ResultadoValidacion:
        """
        Validar dirección de email.
        
        Args:
            email: Email a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        if not email or not isinstance(email, str):
            return ResultadoValidacion(False, "Email no puede estar vacío", "EMAIL_EMPTY")
            
        if len(email) > 254:  # RFC 5321
            return ResultadoValidacion(False, "Email demasiado largo", "EMAIL_LENGTH")
            
        if not re.match(PatronesValidacion.EMAIL, email):
            return ResultadoValidacion(False, f"Formato de email inválido: {email}", "EMAIL_FORMAT")
            
        return ResultadoValidacion(True, f"Email válido: {email}")
        
    @staticmethod
    def validar_mac_address(mac: str) -> ResultadoValidacion:
        """
        Validar dirección MAC.
        
        Args:
            mac: Dirección MAC a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        if not mac or not isinstance(mac, str):
            return ResultadoValidacion(False, "MAC no puede estar vacía", "MAC_EMPTY")
            
        # Normalizar separadores
        mac_normalizada = mac.replace("-", ":").upper()
        
        if not re.match(PatronesValidacion.MAC_ADDRESS, mac_normalizada):
            return ResultadoValidacion(False, f"Formato de MAC inválido: {mac}", "MAC_FORMAT")
            
        return ResultadoValidacion(True, f"MAC válida: {mac_normalizada}")
        
    @staticmethod
    def validar_numero_serie(numero_serie: str) -> ResultadoValidacion:
        """
        Validar número de serie.
        
        Args:
            numero_serie: Número de serie a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        if not numero_serie or not isinstance(numero_serie, str):
            return ResultadoValidacion(False, "Número de serie no puede estar vacío", "SERIAL_EMPTY")
            
        numero_serie = numero_serie.strip().upper()
        
        if len(numero_serie) < 4:
            return ResultadoValidacion(False, "Número de serie muy corto (mínimo 4 caracteres)", "SERIAL_SHORT")
            
        if len(numero_serie) > 50:
            return ResultadoValidacion(False, "Número de serie muy largo (máximo 50 caracteres)", "SERIAL_LONG")
            
        # Permitir letras, números, guiones y espacios
        if not re.match(r"^[A-Z0-9\-\s]+$", numero_serie):
            return ResultadoValidacion(False, "Número de serie contiene caracteres inválidos", "SERIAL_CHARS")
            
        return ResultadoValidacion(True, f"Número de serie válido: {numero_serie}")
        
    @staticmethod
    def validar_rango_sensor(valor: Union[int, float], tipo_sensor: str) -> ResultadoValidacion:
        """
        Validar que un valor esté en el rango típico para un tipo de sensor.
        
        Args:
            valor: Valor a validar
            tipo_sensor: Tipo de sensor
            
        Returns:
            ResultadoValidacion con el resultado
        """
        try:
            valor_float = float(valor)
        except (ValueError, TypeError):
            return ResultadoValidacion(False, f"Valor debe ser numérico: {valor}", "SENSOR_VALUE_FORMAT")
            
        # Definir rangos por tipo de sensor
        rangos = {
            "temperatura": (RangosSensores.TEMPERATURA_MIN, RangosSensores.TEMPERATURA_MAX),
            "humedad": (RangosSensores.HUMEDAD_MIN, RangosSensores.HUMEDAD_MAX),
            "presion": (RangosSensores.PRESION_MIN, RangosSensores.PRESION_MAX),
            "luminosidad": (RangosSensores.LUMINOSIDAD_MIN, RangosSensores.LUMINOSIDAD_MAX),
            "voltaje": (RangosSensores.VOLTAJE_MIN, RangosSensores.VOLTAJE_MAX),
            "corriente": (RangosSensores.CORRIENTE_MIN, RangosSensores.CORRIENTE_MAX)
        }
        
        if tipo_sensor.lower() not in rangos:
            return ResultadoValidacion(True, f"Tipo de sensor desconocido, no se valida rango: {tipo_sensor}")
            
        min_val, max_val = rangos[tipo_sensor.lower()]
        
        if not (min_val <= valor_float <= max_val):
            return ResultadoValidacion(
                False,
                f"Valor fuera de rango para {tipo_sensor} ({min_val}-{max_val}): {valor_float}",
                "SENSOR_OUT_OF_RANGE"
            )
            
        return ResultadoValidacion(True, f"Valor válido para {tipo_sensor}: {valor_float}")
        
    @staticmethod
    def validar_timeout(timeout: Union[int, float]) -> ResultadoValidacion:
        """
        Validar valor de timeout.
        
        Args:
            timeout: Timeout en segundos
            
        Returns:
            ResultadoValidacion con el resultado
        """
        try:
            timeout_float = float(timeout)
        except (ValueError, TypeError):
            return ResultadoValidacion(False, f"Timeout debe ser numérico: {timeout}", "TIMEOUT_FORMAT")
            
        if not (LimitesRed.TIMEOUT_MINIMO <= timeout_float <= LimitesRed.TIMEOUT_MAXIMO):
            return ResultadoValidacion(
                False,
                f"Timeout fuera de rango ({LimitesRed.TIMEOUT_MINIMO}-{LimitesRed.TIMEOUT_MAXIMO}): {timeout_float}",
                "TIMEOUT_RANGE"
            )
            
        return ResultadoValidacion(True, f"Timeout válido: {timeout_float}s")
        
    @staticmethod
    def validar_intervalo_polling(intervalo: Union[int, float]) -> ResultadoValidacion:
        """
        Validar intervalo de polling.
        
        Args:
            intervalo: Intervalo en segundos
            
        Returns:
            ResultadoValidacion con el resultado
        """
        try:
            intervalo_float = float(intervalo)
        except (ValueError, TypeError):
            return ResultadoValidacion(False, f"Intervalo debe ser numérico: {intervalo}", "INTERVAL_FORMAT")
            
        if not (LimitesRed.INTERVALO_POLLING_MINIMO <= intervalo_float <= LimitesRed.INTERVALO_POLLING_MAXIMO):
            return ResultadoValidacion(
                False,
                f"Intervalo fuera de rango ({LimitesRed.INTERVALO_POLLING_MINIMO}-{LimitesRed.INTERVALO_POLLING_MAXIMO}): {intervalo_float}",
                "INTERVAL_RANGE"
            )
            
        return ResultadoValidacion(True, f"Intervalo válido: {intervalo_float}s")
        
    @staticmethod
    def validar_nombre_dispositivo(nombre: str) -> ResultadoValidacion:
        """
        Validar nombre de dispositivo.
        
        Args:
            nombre: Nombre a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        if not nombre or not isinstance(nombre, str):
            return ResultadoValidacion(False, "Nombre no puede estar vacío", "NAME_EMPTY")
            
        nombre = nombre.strip()
        
        if len(nombre) < 2:
            return ResultadoValidacion(False, "Nombre muy corto (mínimo 2 caracteres)", "NAME_SHORT")
            
        if len(nombre) > 100:
            return ResultadoValidacion(False, "Nombre muy largo (máximo 100 caracteres)", "NAME_LONG")
            
        # Permitir letras, números, espacios, guiones y guiones bajos
        if not re.match(r"^[A-Za-z0-9\s\-_]+$", nombre):
            return ResultadoValidacion(False, "Nombre contiene caracteres inválidos", "NAME_CHARS")
            
        return ResultadoValidacion(True, f"Nombre válido: {nombre}")
        
    @staticmethod
    def validar_fecha(fecha: Union[str, datetime, date]) -> ResultadoValidacion:
        """
        Validar fecha.
        
        Args:
            fecha: Fecha a validar
            
        Returns:
            ResultadoValidacion con el resultado
        """
        if fecha is None:
            return ResultadoValidacion(False, "Fecha no puede ser None", "DATE_NONE")
            
        if isinstance(fecha, (datetime, date)):
            return ResultadoValidacion(True, f"Fecha válida: {fecha}")
            
        if isinstance(fecha, str):
            # Intentar parsear diferentes formatos
            formatos = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d"
            ]
            
            for formato in formatos:
                try:
                    fecha_parseada = datetime.strptime(fecha, formato)
                    return ResultadoValidacion(True, f"Fecha válida: {fecha_parseada}")
                except ValueError:
                    continue
                    
            return ResultadoValidacion(False, f"Formato de fecha inválido: {fecha}", "DATE_FORMAT")
            
        return ResultadoValidacion(False, f"Tipo de fecha inválido: {type(fecha)}", "DATE_TYPE")
        
    @staticmethod
    def validar_configuracion_dispositivo(config: Dict[str, Any]) -> List[ResultadoValidacion]:
        """
        Validar configuración completa de dispositivo.
        
        Args:
            config: Diccionario con configuración
            
        Returns:
            Lista de ResultadoValidacion
        """
        resultados = []
        
        # Validar campos requeridos
        campos_requeridos = ["nombre", "tipo", "ip"]
        for campo in campos_requeridos:
            if campo not in config or not config[campo]:
                resultados.append(ResultadoValidacion(False, f"Campo requerido faltante: {campo}", f"{campo.upper()}_REQUIRED"))
                
        # Validar IP si existe
        if "ip" in config:
            resultados.append(ValidadorBMS.validar_ip_address(config["ip"]))
            
        # Validar puerto si existe
        if "puerto" in config:
            resultados.append(ValidadorBMS.validar_puerto(config["puerto"]))
            
        # Validar nombre si existe
        if "nombre" in config:
            resultados.append(ValidadorBMS.validar_nombre_dispositivo(config["nombre"]))
            
        # Validar tipo de dispositivo
        if "tipo" in config:
            tipos_validos = list(MAPEO_TIPOS_DISPOSITIVO.values()) + list(MAPEO_TIPOS_DISPOSITIVO.keys())
            if config["tipo"] not in tipos_validos:
                resultados.append(ResultadoValidacion(False, f"Tipo de dispositivo inválido: {config['tipo']}", "TYPE_INVALID"))
            else:
                resultados.append(ResultadoValidacion(True, f"Tipo de dispositivo válido: {config['tipo']}"))
                
        # Validar timeout si existe
        if "timeout" in config:
            resultados.append(ValidadorBMS.validar_timeout(config["timeout"]))
            
        # Validar intervalo de polling si existe
        if "intervalo_polling" in config:
            resultados.append(ValidadorBMS.validar_intervalo_polling(config["intervalo_polling"]))
            
        return resultados
        
    @staticmethod
    def validar_multiples_campos(datos: Dict[str, Any], validaciones: Dict[str, TipoValidacion]) -> Dict[str, ResultadoValidacion]:
        """
        Validar múltiples campos usando diferentes tipos de validación.
        
        Args:
            datos: Diccionario con datos a validar
            validaciones: Diccionario campo -> tipo de validación
            
        Returns:
            Diccionario con resultados de validación por campo
        """
        resultados = {}
        
        for campo, tipo_validacion in validaciones.items():
            valor = datos.get(campo)
            
            if tipo_validacion == TipoValidacion.IP_ADDRESS:
                resultados[campo] = ValidadorBMS.validar_ip_address(valor)
            elif tipo_validacion == TipoValidacion.PUERTO:
                resultados[campo] = ValidadorBMS.validar_puerto(valor)
            elif tipo_validacion == TipoValidacion.EMAIL:
                resultados[campo] = ValidadorBMS.validar_email(valor)
            elif tipo_validacion == TipoValidacion.MAC_ADDRESS:
                resultados[campo] = ValidadorBMS.validar_mac_address(valor)
            elif tipo_validacion == TipoValidacion.NUMERO_SERIE:
                resultados[campo] = ValidadorBMS.validar_numero_serie(valor)
            elif tipo_validacion == TipoValidacion.FECHA:
                resultados[campo] = ValidadorBMS.validar_fecha(valor)
            else:
                resultados[campo] = ResultadoValidacion(False, f"Tipo de validación no soportado: {tipo_validacion}", "VALIDATION_TYPE")
                
        return resultados

# Funciones de conveniencia
def es_ip_valida(ip: str) -> bool:
    """Verificar si una IP es válida (función de conveniencia)."""
    return ValidadorBMS.validar_ip_address(ip).es_valido

def es_puerto_valido(puerto: Union[int, str]) -> bool:
    """Verificar si un puerto es válido (función de conveniencia)."""
    return ValidadorBMS.validar_puerto(puerto).es_valido

def es_email_valido(email: str) -> bool:
    """Verificar si un email es válido (función de conveniencia)."""
    return ValidadorBMS.validar_email(email).es_valido

def validar_configuracion_modbus(config: Dict[str, Any]) -> List[str]:
    """
    Validar configuración específica de Modbus.
    
    Args:
        config: Configuración de Modbus
        
    Returns:
        Lista de errores encontrados
    """
    errores = []
    
    # Validar IP
    if "ip" in config:
        resultado = ValidadorBMS.validar_ip_address(config["ip"])
        if not resultado.es_valido:
            errores.append(f"IP Modbus: {resultado.mensaje}")
            
    # Validar puerto
    if "puerto" in config:
        resultado = ValidadorBMS.validar_puerto(config["puerto"])
        if not resultado.es_valido:
            errores.append(f"Puerto Modbus: {resultado.mensaje}")
            
    # Validar timeout
    if "timeout" in config:
        resultado = ValidadorBMS.validar_timeout(config["timeout"])
        if not resultado.es_valido:
            errores.append(f"Timeout Modbus: {resultado.mensaje}")
            
    # Validar ID esclavo
    if "id_esclavo" in config:
        id_esclavo = config["id_esclavo"]
        try:
            id_int = int(id_esclavo)
            if not (1 <= id_int <= 247):
                errores.append(f"ID esclavo Modbus fuera de rango (1-247): {id_int}")
        except (ValueError, TypeError):
            errores.append(f"ID esclavo Modbus debe ser numérico: {id_esclavo}")
            
    return errores

if __name__ == "__main__":
    # Prueba del validador
    print("Probando validador BMS...")
    
    # Probar validación de IP
    ips_prueba = ["192.168.1.1", "300.300.300.300", "192.168.1", "invalid"]
    for ip in ips_prueba:
        resultado = ValidadorBMS.validar_ip_address(ip)
        print(f"IP {ip}: {resultado}")
        
    # Probar validación de puerto
    puertos_prueba = [80, 502, 0, 65536, "abc"]
    for puerto in puertos_prueba:
        resultado = ValidadorBMS.validar_puerto(puerto)
        print(f"Puerto {puerto}: {resultado}")
        
    # Probar validación de sensor
    resultado_sensor = ValidadorBMS.validar_rango_sensor(25.5, "temperatura")
    print(f"Sensor temperatura 25.5°C: {resultado_sensor}")
    
    resultado_sensor2 = ValidadorBMS.validar_rango_sensor(150, "temperatura")
    print(f"Sensor temperatura 150°C: {resultado_sensor2}")
    
    # Probar validación de configuración
    config_prueba = {
        "nombre": "Dispositivo Test",
        "tipo": "camara",
        "ip": "192.168.1.100",
        "puerto": 80,
        "timeout": 30
    }
    
    resultados_config = ValidadorBMS.validar_configuracion_dispositivo(config_prueba)
    print(f"\nValidación de configuración:")
    for resultado in resultados_config:
        print(f"  {resultado}")
        
    print("✓ Prueba de validador completada")