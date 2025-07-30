"""
Pruebas del Módulo 1 - Sistema BMS Demo
======================================

Script de pruebas para validar que todos los componentes del Módulo 1
estén funcionando correctamente tras la instalación.

Autor: Sistema BMS Demo
Versión: 1.0.0
"""

import sys
import os
import traceback
from datetime import datetime
from typing import Dict, List, Tuple

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestModulo1:
    """
    Clase principal para pruebas del Módulo 1.
    Valida configuración, protocolos, modelos y utilidades.
    """
    
    def __init__(self):
        """Inicializar tester."""
        self.resultados = {}
        self.errores = []
        self.inicio_tiempo = datetime.now()
        
    def ejecutar_todas_las_pruebas(self) -> bool:
        """
        Ejecutar todas las pruebas del Módulo 1.
        
        Returns:
            True si todas las pruebas pasaron
        """
        print("=" * 70)
        print("🧪 PRUEBAS DEL MÓDULO 1 - SISTEMA BMS DEMO")
        print("=" * 70)
        print(f"Inicio: {self.inicio_tiempo.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Lista de pruebas a ejecutar
        pruebas = [
            ("Configuración General", self.test_configuracion_general),
            ("Configuración Protocolos", self.test_configuracion_protocolos),
            ("Configuración Base Datos", self.test_configuracion_base_datos),
            ("Sistema de Logging", self.test_sistema_logging),
            ("Validador de Datos", self.test_validador),
            ("Convertidor de Datos", self.test_convertidor),
            ("Constantes del Sistema", self.test_constantes),
            ("Modelos de Dispositivo", self.test_modelo_dispositivo),
            ("Modelos de Sensor", self.test_modelo_sensor),
            ("Base de Datos", self.test_base_datos),
            ("Protocolo Base", self.test_protocolo_base),
            ("Cliente Modbus", self.test_cliente_modbus),
            ("Servidor Modbus", self.test_servidor_modbus),
            ("Manejador Modbus", self.test_manejador_modbus)
        ]
        
        # Ejecutar cada prueba
        total_pruebas = len(pruebas)
        pruebas_exitosas = 0
        
        for nombre_prueba, funcion_prueba in pruebas:
            print(f"🔍 Probando: {nombre_prueba}...")
            try:
                resultado = funcion_prueba()
                if resultado:
                    print(f"   ✅ {nombre_prueba}: OK")
                    pruebas_exitosas += 1
                    self.resultados[nombre_prueba] = "OK"
                else:
                    print(f"   ❌ {nombre_prueba}: FALLO")
                    self.resultados[nombre_prueba] = "FALLO"
            except Exception as e:
                print(f"   💥 {nombre_prueba}: ERROR - {str(e)}")
                self.resultados[nombre_prueba] = f"ERROR: {str(e)}"
                self.errores.append((nombre_prueba, str(e), traceback.format_exc()))
                
        # Mostrar resumen
        self.mostrar_resumen(total_pruebas, pruebas_exitosas)
        
        return pruebas_exitosas == total_pruebas
        
    def test_configuracion_general(self) -> bool:
        """Probar configuración general."""
        try:
            from configuracion.configuracion_general import obtener_config, es_modo_debug
            
            config = obtener_config()
            
            # Verificar atributos básicos
            assert hasattr(config, 'NOMBRE_SISTEMA')
            assert hasattr(config, 'VERSION_SISTEMA')
            assert hasattr(config, 'IP_BMS')
            assert hasattr(config, 'PUERTO_BMS')
            
            # Verificar funciones
            debug = es_modo_debug()
            assert isinstance(debug, bool)
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_configuracion_protocolos(self) -> bool:
        """Probar configuración de protocolos."""
        try:
            from configuracion.configuracion_protocolos import (
                obtener_config_modbus, obtener_protocolos_habilitados
            )
            
            # Verificar configuración Modbus
            config_modbus = obtener_config_modbus()
            assert hasattr(config_modbus, 'ip')
            assert hasattr(config_modbus, 'puerto')
            
            # Verificar protocolos habilitados
            protocolos = obtener_protocolos_habilitados()
            assert isinstance(protocolos, list)
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_configuracion_base_datos(self) -> bool:
        """Probar configuración de base de datos."""
        try:
            from configuracion.configuracion_base_datos import (
                obtener_config_bd, obtener_url_conexion_bd
            )
            
            config_bd = obtener_config_bd()
            assert hasattr(config_bd, 'tipo')
            assert hasattr(config_bd, 'nombre')
            
            url = obtener_url_conexion_bd()
            assert isinstance(url, str)
            assert len(url) > 0
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_sistema_logging(self) -> bool:
        """Probar sistema de logging."""
        try:
            from utilidades.logger import obtener_logger, obtener_logger_sistema
            
            # Crear logger
            logger = obtener_logger("test")
            assert logger is not None
            
            # Probar logger del sistema
            logger_sistema = obtener_logger_sistema()
            assert logger_sistema is not None
            
            # Probar escritura
            logger.info("Mensaje de prueba")
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_validador(self) -> bool:
        """Probar validador de datos."""
        try:
            from utilidades.validador import ValidadorBMS, es_ip_valida, es_puerto_valido
            
            # Probar validación de IP
            resultado_ip = ValidadorBMS.validar_ip_address("192.168.1.1")
            assert resultado_ip.es_valido
            
            resultado_ip_mala = ValidadorBMS.validar_ip_address("300.300.300.300")
            assert not resultado_ip_mala.es_valido
            
            # Probar validación de puerto
            resultado_puerto = ValidadorBMS.validar_puerto(80)
            assert resultado_puerto.es_valido
            
            # Probar funciones de conveniencia
            assert es_ip_valida("192.168.1.1")
            assert not es_ip_valida("invalid")
            assert es_puerto_valido(502)
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_convertidor(self) -> bool:
        """Probar convertidor de datos."""
        try:
            from utilidades.convertidor_datos import ConvertidorBMS
            
            # Probar conversión de temperatura
            fahrenheit = ConvertidorBMS.celsius_a_fahrenheit(25.0)
            assert abs(fahrenheit - 77.0) < 0.1
            
            # Probar conversión Modbus
            reg_alto, reg_bajo = ConvertidorBMS.float_a_registros_modbus(25.5)
            valor_recuperado = ConvertidorBMS.registros_modbus_a_float(reg_alto, reg_bajo)
            assert abs(valor_recuperado - 25.5) < 0.1
            
            # Probar normalización
            tipo_norm = ConvertidorBMS.normalizar_tipo_dispositivo("camera")
            assert tipo_norm == "camara"
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_constantes(self) -> bool:
        """Probar constantes del sistema."""
        try:
            from utilidades.constantes import (
                NOMBRE_SISTEMA, VERSION_SISTEMA, LimitesSistema,
                obtener_mensaje_error, validar_rango_sensor
            )
            
            # Verificar constantes básicas
            assert isinstance(NOMBRE_SISTEMA, str)
            assert isinstance(VERSION_SISTEMA, str)
            assert hasattr(LimitesSistema, 'MAX_DISPOSITIVOS')
            
            # Probar funciones
            mensaje = obtener_mensaje_error("DEV_001")
            assert isinstance(mensaje, str)
            
            valido = validar_rango_sensor("temperatura", 25.0)
            assert valido
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_modelo_dispositivo(self) -> bool:
        """Probar modelo de dispositivo."""
        try:
            from modelos.dispositivo import (
                Dispositivo, TipoDispositivo, EstadoDispositivo,
                ConfiguracionDispositivo, ProtocoloComunicacion
            )
            
            # Crear configuración
            config = ConfiguracionDispositivo(
                ip="192.168.1.100",
                puerto=80,
                protocolo=ProtocoloComunicacion.HTTP
            )
            
            # Crear dispositivo
            dispositivo = Dispositivo(
                nombre="Test Device",
                tipo=TipoDispositivo.CAMARA.value,
                direccion_ip="192.168.1.100",
                estado=EstadoDispositivo.ONLINE.value
            )
            
            dispositivo.configuracion = config
            
            # Verificar métodos
            assert dispositivo.esta_online()
            assert dispositivo.esta_disponible()
            
            # Verificar validación
            errores = dispositivo.validar_configuracion()
            assert isinstance(errores, list)
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_modelo_sensor(self) -> bool:
        """Probar modelo de sensor."""
        try:
            from modelos.sensor import (
                crear_sensor_temperatura, crear_sensor_humedad,
                TipoSensor, TipoAlerta
            )
            
            # Crear sensores
            sensor_temp = crear_sensor_temperatura(1)
            sensor_humedad = crear_sensor_humedad(1)
            
            # Verificar propiedades
            assert sensor_temp.tipo_sensor == TipoSensor.TEMPERATURA.value
            assert sensor_humedad.tipo_sensor == TipoSensor.HUMEDAD.value
            
            # Probar actualización de valores
            alertas = sensor_temp.actualizar_valor(25.5)
            assert isinstance(alertas, list)
            assert sensor_temp.valor_actual == 25.5
            
            # Probar estadísticas
            stats = sensor_temp.obtener_estadisticas()
            assert isinstance(stats, dict)
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_base_datos(self) -> bool:
        """Probar conexión a base de datos."""
        try:
            from base_datos.conexion_bd import (
                verificar_bd_disponible, obtener_salud_bd, gestor_bd
            )
            
            # Verificar disponibilidad
            disponible = verificar_bd_disponible()
            if not disponible:
                print("      Warning: BD no disponible, intentando conectar...")
                gestor_bd.conectar()
                
            # Verificar salud
            salud = obtener_salud_bd()
            assert isinstance(salud, dict)
            assert 'conectado' in salud
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_protocolo_base(self) -> bool:
        """Probar clase base de protocolos."""
        try:
            from protocolos.protocolo_base import (
                ProtocoloBase, EstadoProtocolo, ResultadoOperacion
            )
            
            # Crear resultado de operación
            resultado = ResultadoOperacion(True, "Test OK")
            assert resultado.exitoso
            assert resultado.mensaje == "Test OK"
            
            # Verificar enums
            assert hasattr(EstadoProtocolo, 'CONECTADO')
            assert hasattr(EstadoProtocolo, 'DESCONECTADO')
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_cliente_modbus(self) -> bool:
        """Probar cliente Modbus (sin conexión real)."""
        try:
            from protocolos.modbus.cliente_modbus import ClienteModbus
            
            # Crear cliente
            cliente = ClienteModbus()
            
            # Verificar propiedades
            assert hasattr(cliente, 'config_modbus')
            assert hasattr(cliente, 'registros_bms')
            
            # Verificar métodos (sin conectar)
            assert hasattr(cliente, 'conectar')
            assert hasattr(cliente, 'desconectar')
            assert hasattr(cliente, 'leer_datos')
            assert hasattr(cliente, 'escribir_datos')
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_servidor_modbus(self) -> bool:
        """Probar servidor Modbus (sin iniciar)."""
        try:
            from protocolos.modbus.servidor_modbus import ServidorModbus
            
            # Crear servidor
            servidor = ServidorModbus()
            
            # Verificar propiedades
            assert hasattr(servidor, 'config_modbus')
            assert hasattr(servidor, 'mapa_registros')
            
            # Verificar métodos
            assert hasattr(servidor, 'conectar')
            assert hasattr(servidor, 'desconectar')
            assert hasattr(servidor, 'leer_datos')
            assert hasattr(servidor, 'escribir_datos')
            
            # Probar actualización de datos
            servidor.actualizar_dato_sistema('temperatura_promedio', 250)
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def test_manejador_modbus(self) -> bool:
        """Probar manejador Modbus (sin conexión)."""
        try:
            from protocolos.modbus.manejador_modbus import (
                ManejadorModbus, ModoOperacionModbus
            )
            
            # Crear manejador
            manejador = ManejadorModbus(ModoOperacionModbus.SOLO_SERVIDOR)
            
            # Verificar propiedades
            assert hasattr(manejador, 'modo_operacion')
            assert hasattr(manejador, 'estadisticas')
            
            # Verificar métodos
            assert hasattr(manejador, 'iniciar')
            assert hasattr(manejador, 'detener')
            assert hasattr(manejador, 'obtener_estado_completo')
            
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
            
    def mostrar_resumen(self, total: int, exitosas: int):
        """Mostrar resumen de las pruebas."""
        fin_tiempo = datetime.now()
        duracion = fin_tiempo - self.inicio_tiempo
        
        print()
        print("=" * 70)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 70)
        print(f"Total de pruebas: {total}")
        print(f"Pruebas exitosas: {exitosas}")
        print(f"Pruebas fallidas: {total - exitosas}")
        print(f"Porcentaje éxito: {(exitosas/total)*100:.1f}%")
        print(f"Duración: {duracion.total_seconds():.2f} segundos")
        
        if exitosas == total:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! El Módulo 1 está funcionando correctamente.")
        else:
            print(f"\n⚠️  {total - exitosas} pruebas fallaron. Revisar la configuración.")
            
        # Mostrar errores si los hay
        if self.errores:
            print("\n❌ ERRORES DETALLADOS:")
            for nombre, error, traceback_str in self.errores:
                print(f"\n{nombre}:")
                print(f"  Error: {error}")
                if "--verbose" in sys.argv:
                    print(f"  Traceback:\n{traceback_str}")
                    
        print("\n" + "=" * 70)

def main():
    """Función principal para ejecutar las pruebas."""
    tester = TestModulo1()
    
    # Verificar argumentos
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Uso: python test_modulo1.py [--verbose]")
        print("  --verbose: Mostrar tracebacks completos de errores")
        return
        
    # Ejecutar pruebas
    resultado = tester.ejecutar_todas_las_pruebas()
    
    # Código de salida
    sys.exit(0 if resultado else 1)

if __name__ == "__main__":
    main()