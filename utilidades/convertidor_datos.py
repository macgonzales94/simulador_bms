"""
Convertidor de Datos para Sistema BMS
====================================

Este módulo proporciona funciones de conversión y transformación de datos
entre diferentes formatos, protocolos y unidades de medida utilizados en el sistema BMS.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import json
import struct
from typing import Any, Dict, List, Union, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import math

# Importar constantes
from utilidades.constantes import MAPEO_TIPOS_DISPOSITIVO, MAPEO_ESTADOS_DISPOSITIVO, FormatoDatos

class TipoConversion(Enum):
    """Tipos de conversión disponibles."""
    TEMPERATURA = "temperatura"
    PRESION = "presion"
    MODBUS_REGISTERS = "modbus_registers"
    TIMESTAMP = "timestamp"
    ESTADO_DISPOSITIVO = "estado_dispositivo"
    TIPO_DISPOSITIVO = "tipo_dispositivo"
    JSON_STRING = "json_string"
    BINARIO_DECIMAL = "binario_decimal"

class ConvertidorBMS:
    """
    Clase principal de conversión de datos para el sistema BMS.
    Proporciona métodos estáticos para convertir entre diferentes formatos.
    """
    
    @staticmethod
    def celsius_a_fahrenheit(celsius: float) -> float:
        """
        Convertir temperatura de Celsius a Fahrenheit.
        
        Args:
            celsius: Temperatura en Celsius
            
        Returns:
            Temperatura en Fahrenheit
        """
        return (celsius * 9/5) + 32
        
    @staticmethod
    def fahrenheit_a_celsius(fahrenheit: float) -> float:
        """
        Convertir temperatura de Fahrenheit a Celsius.
        
        Args:
            fahrenheit: Temperatura en Fahrenheit
            
        Returns:
            Temperatura en Celsius
        """
        return (fahrenheit - 32) * 5/9
        
    @staticmethod
    def celsius_a_kelvin(celsius: float) -> float:
        """
        Convertir temperatura de Celsius a Kelvin.
        
        Args:
            celsius: Temperatura en Celsius
            
        Returns:
            Temperatura en Kelvin
        """
        return celsius + 273.15
        
    @staticmethod
    def kelvin_a_celsius(kelvin: float) -> float:
        """
        Convertir temperatura de Kelvin a Celsius.
        
        Args:
            kelvin: Temperatura en Kelvin
            
        Returns:
            Temperatura en Celsius
        """
        return kelvin - 273.15
        
    @staticmethod
    def mbar_a_pascal(mbar: float) -> float:
        """
        Convertir presión de milibar a Pascal.
        
        Args:
            mbar: Presión en milibar
            
        Returns:
            Presión en Pascal
        """
        return mbar * 100
        
    @staticmethod
    def pascal_a_mbar(pascal: float) -> float:
        """
        Convertir presión de Pascal a milibar.
        
        Args:
            pascal: Presión en Pascal
            
        Returns:
            Presión en milibar
        """
        return pascal / 100
        
    @staticmethod
    def bar_a_pascal(bar: float) -> float:
        """
        Convertir presión de bar a Pascal.
        
        Args:
            bar: Presión en bar
            
        Returns:
            Presión en Pascal
        """
        return bar * 100000
        
    @staticmethod
    def pascal_a_bar(pascal: float) -> float:
        """
        Convertir presión de Pascal a bar.
        
        Args:
            pascal: Presión en Pascal
            
        Returns:
            Presión en bar
        """
        return pascal / 100000
        
    @staticmethod
    def registros_modbus_a_float(registro_alto: int, registro_bajo: int, orden_bytes: str = "big") -> float:
        """
        Convertir dos registros Modbus a un valor float de 32 bits.
        
        Args:
            registro_alto: Registro alto (16 bits)
            registro_bajo: Registro bajo (16 bits)
            orden_bytes: Orden de bytes ("big" o "little")
            
        Returns:
            Valor float de 32 bits
        """
        if orden_bytes == "big":
            valor_32bit = (registro_alto << 16) | registro_bajo
        else:
            valor_32bit = (registro_bajo << 16) | registro_alto
            
        # Convertir a float usando struct
        bytes_valor = struct.pack('>I', valor_32bit)
        return struct.unpack('>f', bytes_valor)[0]
        
    @staticmethod
    def float_a_registros_modbus(valor_float: float, orden_bytes: str = "big") -> Tuple[int, int]:
        """
        Convertir un valor float a dos registros Modbus de 16 bits.
        
        Args:
            valor_float: Valor float a convertir
            orden_bytes: Orden de bytes ("big" o "little")
            
        Returns:
            Tupla con (registro_alto, registro_bajo)
        """
        # Convertir float a bytes
        bytes_valor = struct.pack('>f', valor_float)
        valor_32bit = struct.unpack('>I', bytes_valor)[0]
        
        if orden_bytes == "big":
            registro_alto = (valor_32bit >> 16) & 0xFFFF
            registro_bajo = valor_32bit & 0xFFFF
        else:
            registro_bajo = (valor_32bit >> 16) & 0xFFFF
            registro_alto = valor_32bit & 0xFFFF
            
        return registro_alto, registro_bajo
        
    @staticmethod
    def int32_a_registros_modbus(valor_int: int) -> Tuple[int, int]:
        """
        Convertir un entero de 32 bits a dos registros Modbus de 16 bits.
        
        Args:
            valor_int: Valor entero de 32 bits
            
        Returns:
            Tupla con (registro_alto, registro_bajo)
        """
        registro_alto = (valor_int >> 16) & 0xFFFF
        registro_bajo = valor_int & 0xFFFF
        return registro_alto, registro_bajo
        
    @staticmethod
    def registros_modbus_a_int32(registro_alto: int, registro_bajo: int) -> int:
        """
        Convertir dos registros Modbus a un entero de 32 bits.
        
        Args:
            registro_alto: Registro alto (16 bits)
            registro_bajo: Registro bajo (16 bits)
            
        Returns:
            Valor entero de 32 bits
        """
        return (registro_alto << 16) | registro_bajo
        
    @staticmethod
    def datetime_a_timestamp_unix(fecha_hora: datetime) -> int:
        """
        Convertir datetime a timestamp Unix.
        
        Args:
            fecha_hora: Objeto datetime
            
        Returns:
            Timestamp Unix (segundos desde epoch)
        """
        return int(fecha_hora.timestamp())
        
    @staticmethod
    def timestamp_unix_a_datetime(timestamp: int) -> datetime:
        """
        Convertir timestamp Unix a datetime.
        
        Args:
            timestamp: Timestamp Unix
            
        Returns:
            Objeto datetime
        """
        return datetime.fromtimestamp(timestamp)
        
    @staticmethod
    def datetime_a_string(fecha_hora: datetime, formato: str = None) -> str:
        """
        Convertir datetime a string formateado.
        
        Args:
            fecha_hora: Objeto datetime
            formato: Formato de fecha (opcional)
            
        Returns:
            Fecha como string
        """
        if formato is None:
            formato = FormatoDatos.FECHA_HORA
        return fecha_hora.strftime(formato)
        
    @staticmethod
    def string_a_datetime(fecha_string: str, formato: str = None) -> datetime:
        """
        Convertir string a datetime.
        
        Args:
            fecha_string: Fecha como string
            formato: Formato de fecha (opcional)
            
        Returns:
            Objeto datetime
        """
        if formato is None:
            formato = FormatoDatos.FECHA_HORA
        return datetime.strptime(fecha_string, formato)
        
    @staticmethod
    def normalizar_tipo_dispositivo(tipo: str) -> str:
        """
        Normalizar tipo de dispositivo usando mapeo.
        
        Args:
            tipo: Tipo de dispositivo original
            
        Returns:
            Tipo normalizado
        """
        tipo_lower = tipo.lower()
        return MAPEO_TIPOS_DISPOSITIVO.get(tipo_lower, tipo_lower)
        
    @staticmethod
    def normalizar_estado_dispositivo(estado: str) -> str:
        """
        Normalizar estado de dispositivo usando mapeo.
        
        Args:
            estado: Estado original
            
        Returns:
            Estado normalizado
        """
        estado_lower = estado.lower()
        return MAPEO_ESTADOS_DISPOSITIVO.get(estado_lower, estado_lower)
        
    @staticmethod
    def diccionario_a_json(diccionario: Dict[str, Any], pretty: bool = False) -> str:
        """
        Convertir diccionario a JSON string.
        
        Args:
            diccionario: Diccionario a convertir
            pretty: Si formatear el JSON (sangría)
            
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(diccionario, indent=2, ensure_ascii=False, default=ConvertidorBMS._json_serializer)
        else:
            return json.dumps(diccionario, ensure_ascii=False, default=ConvertidorBMS._json_serializer)
            
    @staticmethod
    def json_a_diccionario(json_string: str) -> Dict[str, Any]:
        """
        Convertir JSON string a diccionario.
        
        Args:
            json_string: JSON como string
            
        Returns:
            Diccionario Python
        """
        return json.loads(json_string)
        
    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """
        Serializador personalizado para JSON.
        
        Args:
            obj: Objeto a serializar
            
        Returns:
            Objeto serializable
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
            
    @staticmethod
    def binario_a_decimal(binario: str) -> int:
        """
        Convertir string binario a decimal.
        
        Args:
            binario: String binario (ej: "1010")
            
        Returns:
            Valor decimal
        """
        return int(binario, 2)
        
    @staticmethod
    def decimal_a_binario(decimal: int, bits: int = 8) -> str:
        """
        Convertir decimal a string binario.
        
        Args:
            decimal: Valor decimal
            bits: Número de bits (padding)
            
        Returns:
            String binario
        """
        return format(decimal, f'0{bits}b')
        
    @staticmethod
    def hexadecimal_a_decimal(hexadecimal: str) -> int:
        """
        Convertir string hexadecimal a decimal.
        
        Args:
            hexadecimal: String hexadecimal (ej: "FF" o "0xFF")
            
        Returns:
            Valor decimal
        """
        # Remover prefijo "0x" si existe
        if hexadecimal.startswith('0x') or hexadecimal.startswith('0X'):
            hexadecimal = hexadecimal[2:]
        return int(hexadecimal, 16)
        
    @staticmethod
    def decimal_a_hexadecimal(decimal: int, mayusculas: bool = True) -> str:
        """
        Convertir decimal a string hexadecimal.
        
        Args:
            decimal: Valor decimal
            mayusculas: Si usar letras mayúsculas
            
        Returns:
            String hexadecimal (sin prefijo 0x)
        """
        hex_str = hex(decimal)[2:]  # Remover prefijo 0x
        return hex_str.upper() if mayusculas else hex_str
        
    @staticmethod
    def escalar_valor_sensor(valor: float, factor_escala: float, offset: float = 0.0) -> float:
        """
        Escalar valor de sensor aplicando factor y offset.
        
        Args:
            valor: Valor original
            factor_escala: Factor de escala
            offset: Offset a aplicar
            
        Returns:
            Valor escalado
        """
        return (valor * factor_escala) + offset
        
    @staticmethod
    def convertir_temperatura(valor: float, unidad_origen: str, unidad_destino: str) -> float:
        """
        Convertir temperatura entre diferentes unidades.
        
        Args:
            valor: Valor de temperatura
            unidad_origen: Unidad origen ("C", "F", "K")
            unidad_destino: Unidad destino ("C", "F", "K")
            
        Returns:
            Temperatura en unidad destino
        """
        # Normalizar unidades
        unidad_origen = unidad_origen.upper()
        unidad_destino = unidad_destino.upper()
        
        # Si son iguales, no convertir
        if unidad_origen == unidad_destino:
            return valor
            
        # Convertir a Celsius como unidad intermedia
        if unidad_origen == "F":
            celsius = ConvertidorBMS.fahrenheit_a_celsius(valor)
        elif unidad_origen == "K":
            celsius = ConvertidorBMS.kelvin_a_celsius(valor)
        else:  # "C"
            celsius = valor
            
        # Convertir de Celsius a unidad destino
        if unidad_destino == "F":
            return ConvertidorBMS.celsius_a_fahrenheit(celsius)
        elif unidad_destino == "K":
            return ConvertidorBMS.celsius_a_kelvin(celsius)
        else:  # "C"
            return celsius
            
    @staticmethod
    def convertir_presion(valor: float, unidad_origen: str, unidad_destino: str) -> float:
        """
        Convertir presión entre diferentes unidades.
        
        Args:
            valor: Valor de presión
            unidad_origen: Unidad origen ("Pa", "mbar", "bar")
            unidad_destino: Unidad destino ("Pa", "mbar", "bar")
            
        Returns:
            Presión en unidad destino
        """
        # Normalizar unidades
        unidad_origen = unidad_origen.lower()
        unidad_destino = unidad_destino.lower()
        
        # Si son iguales, no convertir
        if unidad_origen == unidad_destino:
            return valor
            
        # Convertir a Pascal como unidad intermedia
        if unidad_origen == "mbar":
            pascal = ConvertidorBMS.mbar_a_pascal(valor)
        elif unidad_origen == "bar":
            pascal = ConvertidorBMS.bar_a_pascal(valor)
        else:  # "pa"
            pascal = valor
            
        # Convertir de Pascal a unidad destino
        if unidad_destino == "mbar":
            return ConvertidorBMS.pascal_a_mbar(pascal)
        elif unidad_destino == "bar":
            return ConvertidorBMS.pascal_a_bar(pascal)
        else:  # "pa"
            return pascal
            
    @staticmethod
    def normalizar_mac_address(mac: str, separador: str = ":") -> str:
        """
        Normalizar dirección MAC con separador específico.
        
        Args:
            mac: Dirección MAC original
            separador: Separador a usar (":", "-", "")
            
        Returns:
            MAC normalizada
        """
        # Remover separadores existentes y convertir a mayúsculas
        mac_limpia = mac.replace(":", "").replace("-", "").replace(".", "").upper()
        
        # Validar longitud
        if len(mac_limpia) != 12:
            raise ValueError(f"MAC address inválida: {mac}")
            
        # Agregar separadores cada 2 caracteres
        if separador:
            mac_formateada = separador.join(mac_limpia[i:i+2] for i in range(0, 12, 2))
        else:
            mac_formateada = mac_limpia
            
        return mac_formateada
        
    @staticmethod
    def datos_genetec_a_bms(datos_genetec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir datos del formato Genetec al formato BMS interno.
        
        Args:
            datos_genetec: Datos en formato Genetec
            
        Returns:
            Datos en formato BMS
        """
        datos_bms = {}
        
        # Mapear campos comunes
        mapeo_campos = {
            "name": "nombre",
            "ip_address": "direccion_ip",
            "port": "puerto",
            "type": "tipo",
            "status": "estado",
            "location": "ubicacion_fisica",
            "zone": "zona",
            "manufacturer": "marca",
            "model": "modelo",
            "serial_number": "numero_serie",
            "mac_address": "direccion_mac"
        }
        
        for campo_genetec, campo_bms in mapeo_campos.items():
            if campo_genetec in datos_genetec:
                valor = datos_genetec[campo_genetec]
                
                # Aplicar conversiones específicas
                if campo_bms == "tipo":
                    valor = ConvertidorBMS.normalizar_tipo_dispositivo(valor)
                elif campo_bms == "estado":
                    valor = ConvertidorBMS.normalizar_estado_dispositivo(valor)
                elif campo_bms == "direccion_mac" and valor:
                    try:
                        valor = ConvertidorBMS.normalizar_mac_address(valor)
                    except ValueError:
                        valor = None
                        
                datos_bms[campo_bms] = valor
                
        # Agregar timestamp de conversión
        datos_bms["timestamp_conversion"] = datetime.now()
        
        return datos_bms
        
    @staticmethod
    def formatear_numero(numero: Union[int, float], decimales: int = 2) -> str:
        """
        Formatear número con decimales específicos.
        
        Args:
            numero: Número a formatear
            decimales: Número de decimales
            
        Returns:
            Número formateado como string
        """
        if isinstance(numero, int) and decimales == 0:
            return str(numero)
        else:
            return f"{numero:.{decimales}f}"

# Funciones de conveniencia
def convertir_temp_modbus_a_celsius(registro_modbus: int) -> float:
    """
    Convertir registro Modbus (temperatura x10) a Celsius.
    
    Args:
        registro_modbus: Valor del registro Modbus
        
    Returns:
        Temperatura en Celsius
    """
    return registro_modbus / 10.0

def convertir_celsius_a_temp_modbus(temperatura_celsius: float) -> int:
    """
    Convertir temperatura Celsius a registro Modbus (x10).
    
    Args:
        temperatura_celsius: Temperatura en Celsius
        
    Returns:
        Valor para registro Modbus
    """
    return int(temperatura_celsius * 10)

def convertir_humedad_modbus_a_porcentaje(registro_modbus: int) -> float:
    """
    Convertir registro Modbus de humedad a porcentaje.
    
    Args:
        registro_modbus: Valor del registro Modbus
        
    Returns:
        Humedad en porcentaje
    """
    return float(registro_modbus)

def convertir_presion_modbus_a_mbar(registro_modbus: int) -> float:
    """
    Convertir registro Modbus (presión x10) a mbar.
    
    Args:
        registro_modbus: Valor del registro Modbus
        
    Returns:
        Presión en mbar
    """
    return registro_modbus / 10.0

if __name__ == "__main__":
    # Prueba del convertidor
    print("Probando convertidor BMS...")
    
    # Probar conversiones de temperatura
    celsius = 25.0
    fahrenheit = ConvertidorBMS.celsius_a_fahrenheit(celsius)
    kelvin = ConvertidorBMS.celsius_a_kelvin(celsius)
    print(f"Temperatura: {celsius}°C = {fahrenheit:.1f}°F = {kelvin:.1f}K")
    
    # Probar conversiones de presión
    mbar = 1013.25
    pascal = ConvertidorBMS.mbar_a_pascal(mbar)
    bar = ConvertidorBMS.pascal_a_bar(pascal)
    print(f"Presión: {mbar} mbar = {pascal:.0f} Pa = {bar:.5f} bar")
    
    # Probar conversión Modbus
    valor_float = 25.75
    reg_alto, reg_bajo = ConvertidorBMS.float_a_registros_modbus(valor_float)
    valor_recuperado = ConvertidorBMS.registros_modbus_a_float(reg_alto, reg_bajo)
    print(f"Modbus: {valor_float} -> registros({reg_alto}, {reg_bajo}) -> {valor_recuperado}")
    
    # Probar conversión de timestamp
    ahora = datetime.now()
    timestamp = ConvertidorBMS.datetime_a_timestamp_unix(ahora)
    fecha_recuperada = ConvertidorBMS.timestamp_unix_a_datetime(timestamp)
    print(f"Timestamp: {ahora} -> {timestamp} -> {fecha_recuperada}")
    
    # Probar normalización
    tipo_original = "camera"
    tipo_normalizado = ConvertidorBMS.normalizar_tipo_dispositivo(tipo_original)
    print(f"Tipo: {tipo_original} -> {tipo_normalizado}")
    
    # Probar MAC address
    mac_original = "aa-bb-cc-dd-ee-ff"
    mac_normalizada = ConvertidorBMS.normalizar_mac_address(mac_original, ":")
    print(f"MAC: {mac_original} -> {mac_normalizada}")
    
    # Probar datos Genetec
    datos_genetec = {
        "name": "Camera 01",
        "type": "camera",
        "ip_address": "192.168.1.100",
        "status": "up",
        "location": "Main entrance"
    }
    
    datos_bms = ConvertidorBMS.datos_genetec_a_bms(datos_genetec)
    print(f"\nConversión Genetec -> BMS:")
    for clave, valor in datos_bms.items():
        if clave != "timestamp_conversion":
            print(f"  {clave}: {valor}")
            
    print("✓ Prueba de convertidor completada")