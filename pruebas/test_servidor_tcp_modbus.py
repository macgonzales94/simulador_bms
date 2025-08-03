"""
Script de Prueba para Servidor Modbus TCP Real
==============================================

Este script verifica que el servidor Modbus TCP real funcione correctamente
y se pueda conectar desde un cliente externo.

Autor: Sistema BMS Demo
Versión: 2.0.0
"""

import sys
import os
import time
import threading
from typing import Dict, Any

# Agregar path del sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar componentes del sistema
from protocolos.modbus.servidor_modbus_tcp_real import ServidorModbusTCPReal
from protocolos.modbus.cliente_modbus import ClienteModbus

class ProbadorServidorTCP:
    """
    Clase para probar el servidor Modbus TCP de forma integral.
    """
    
    def __init__(self):
        """Inicializar probador."""
        self.servidor = None
        self.cliente_prueba = None
        self.resultados_pruebas = {}
        
    def ejecutar_todas_las_pruebas(self) -> bool:
        """
        Ejecutar todas las pruebas del servidor TCP.
        
        Returns:
            True si todas las pruebas pasaron
        """
        print("=" * 70)
        print("🧪 PRUEBAS DEL SERVIDOR MODBUS TCP REAL")
        print("=" * 70)
        
        pruebas = [
            ("Inicialización del servidor", self._test_inicializacion_servidor),
            ("Arranque del servidor TCP", self._test_arranque_servidor),
            ("Verificación de puerto", self._test_verificacion_puerto),
            ("Conexión de cliente", self._test_conexion_cliente),
            ("Lectura de Input Registers", self._test_lectura_input_registers),
            ("Lectura de Holding Registers", self._test_lectura_holding_registers),
            ("Escritura de Holding Registers", self._test_escritura_holding_registers),
            ("Callbacks de escritura", self._test_callbacks_escritura),
            ("Actualización de datos", self._test_actualizacion_datos),
            ("Parada del servidor", self._test_parada_servidor)
        ]
        
        total_pruebas = len(pruebas)
        pruebas_exitosas = 0
        
        for nombre, funcion_prueba in pruebas:
            print(f"\n🔍 Ejecutando: {nombre}...")
            try:
                resultado = funcion_prueba()
                if resultado:
                    print(f"   ✅ {nombre}: EXITOSA")
                    pruebas_exitosas += 1
                    self.resultados_pruebas[nombre] = "EXITOSA"
                else:
                    print(f"   ❌ {nombre}: FALLIDA")
                    self.resultados_pruebas[nombre] = "FALLIDA"
            except Exception as e:
                print(f"   💥 {nombre}: ERROR - {str(e)}")
                self.resultados_pruebas[nombre] = f"ERROR: {str(e)}"
                
        # Mostrar resumen
        self._mostrar_resumen(total_pruebas, pruebas_exitosas)
        
        return pruebas_exitosas == total_pruebas
        
    def _test_inicializacion_servidor(self) -> bool:
        """Probar inicialización del servidor."""
        try:
            # Configuración de prueba en puerto alternativo
            config_prueba = {
                'ip': '127.0.0.1',
                'puerto': 5502,  # Puerto alternativo para no interferir
                'timeout': 5,
                'id_esclavo': 1
            }
            
            self.servidor = ServidorModbusTCPReal(config_prueba)
            print(f"      ✓ Servidor inicializado en {config_prueba['ip']}:{config_prueba['puerto']}")
            return True
            
        except Exception as e:
            print(f"      ✗ Error inicializando servidor: {e}")
            return False
            
    def _test_arranque_servidor(self) -> bool:
        """Probar arranque del servidor TCP."""
        try:
            if not self.servidor:
                return False
                
            resultado = self.servidor.conectar()
            
            if resultado.exitoso:
                print(f"      ✓ Servidor TCP iniciado: {resultado.mensaje}")
                # Esperar un momento para que el servidor se estabilice
                time.sleep(2)
                return True
            else:
                print(f"      ✗ Error iniciando servidor: {resultado.mensaje}")
                return False
                
        except Exception as e:
            print(f"      ✗ Excepción iniciando servidor: {e}")
            return False
            
    def _test_verificacion_puerto(self) -> bool:
        """Verificar que el puerto esté escuchando."""
        try:
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Intentar conectar al puerto
            resultado = sock.connect_ex(('127.0.0.1', 5502))
            sock.close()
            
            if resultado == 0:
                print(f"      ✓ Puerto 5502 está escuchando")
                return True
            else:
                print(f"      ✗ Puerto 5502 no está disponible (código: {resultado})")
                return False
                
        except Exception as e:
            print(f"      ✗ Error verificando puerto: {e}")
            return False
            
    def _test_conexion_cliente(self) -> bool:
        """Probar conexión de cliente Modbus."""
        try:
            from pymodbus.client import ModbusTcpClient
            
            # Crear cliente de prueba
            self.cliente_prueba = ModbusTcpClient(
                host='127.0.0.1',
                port=5502,
                timeout=5
            )
            
            # Intentar conectar
            conectado = self.cliente_prueba.connect()
            
            if conectado:
                print(f"      ✓ Cliente conectado exitosamente")
                return True
            else:
                print(f"      ✗ Cliente no pudo conectar")
                return False
                
        except Exception as e:
            print(f"      ✗ Error conectando cliente: {e}")
            return False
            
    def _test_lectura_input_registers(self) -> bool:
        """Probar lectura de Input Registers."""
        try:
            if not self.cliente_prueba:
                return False
                
            # Leer primeros 10 input registers
            respuesta = self.cliente_prueba.read_input_registers(
                address=0,
                count=10,
                slave=1
            )
            
            if hasattr(respuesta, 'registers') and respuesta.registers:
                valores = respuesta.registers
                print(f"      ✓ Input Registers leídos: {valores[:5]}... (mostrando 5 primeros)")
                
                # Verificar que hay datos sensatos
                if len(valores) == 10 and any(v > 0 for v in valores):
                    return True
                else:
                    print(f"      ✗ Datos de Input Registers no válidos")
                    return False
            else:
                print(f"      ✗ Error leyendo Input Registers: {respuesta}")
                return False
                
        except Exception as e:
            print(f"      ✗ Excepción leyendo Input Registers: {e}")
            return False
            
    def _test_lectura_holding_registers(self) -> bool:
        """Probar lectura de Holding Registers."""
        try:
            if not self.cliente_prueba:
                return False
                
            # Leer primeros 10 holding registers
            respuesta = self.cliente_prueba.read_holding_registers(
                address=0,
                count=10,
                slave=1
            )
            
            if hasattr(respuesta, 'registers') and respuesta.registers:
                valores = respuesta.registers
                print(f"      ✓ Holding Registers leídos: {valores[:5]}... (mostrando 5 primeros)")
                
                if len(valores) == 10:
                    return True
                else:
                    print(f"      ✗ Cantidad incorrecta de Holding Registers")
                    return False
            else:
                print(f"      ✗ Error leyendo Holding Registers: {respuesta}")
                return False
                
        except Exception as e:
            print(f"      ✗ Excepción leyendo Holding Registers: {e}")
            return False
            
    def _test_escritura_holding_registers(self) -> bool:
        """Probar escritura de Holding Registers."""
        try:
            if not self.cliente_prueba:
                return False
                
            # Escribir en registro de prueba (registro 5 - modo_debug)
            valor_prueba = 1
            respuesta = self.cliente_prueba.write_register(
                address=5,
                value=valor_prueba,
                slave=1
            )
            
            if not (hasattr(respuesta, 'isError') and respuesta.isError()):
                print(f"      ✓ Escritura exitosa en registro 5 con valor {valor_prueba}")
                
                # Verificar que se escribió correctamente
                respuesta_lectura = self.cliente_prueba.read_holding_registers(
                    address=5,
                    count=1,
                    slave=1
                )
                
                if hasattr(respuesta_lectura, 'registers') and respuesta_lectura.registers:
                    valor_leido = respuesta_lectura.registers[0]
                    if valor_leido == valor_prueba:
                        print(f"      ✓ Verificación exitosa: valor leído = {valor_leido}")
                        return True
                    else:
                        print(f"      ✗ Valor leído ({valor_leido}) no coincide con escrito ({valor_prueba})")
                        return False
                else:
                    print(f"      ✗ Error verificando escritura")
                    return False
            else:
                print(f"      ✗ Error en escritura: {respuesta}")
                return False
                
        except Exception as e:
            print(f"      ✗ Excepción en escritura: {e}")
            return False
            
    def _test_callbacks_escritura(self) -> bool:
        """Probar que los callbacks de escritura funcionan."""
        try:
            if not self.cliente_prueba or not self.servidor:
                return False
                
            # Variable para capturar callback
            callback_ejecutado = {'valor': False, 'direccion': None, 'valor_escrito': None}
            
            def callback_prueba(direccion, valor):
                callback_ejecutado['valor'] = True
                callback_ejecutado['direccion'] = direccion
                callback_ejecutado['valor_escrito'] = valor
                print(f"      ✓ Callback ejecutado: registro {direccion} = {valor}")
                
            # Agregar callback temporal
            self.servidor.agregar_callback_escritura(99, callback_prueba)
            
            # Escribir en registro que debe disparar callback
            valor_callback = 123
            respuesta = self.cliente_prueba.write_register(
                address=99,
                value=valor_callback,
                slave=1
            )
            
            # Esperar un momento para que se ejecute el callback
            time.sleep(1)
            
            if callback_ejecutado['valor']:
                if (callback_ejecutado['direccion'] == 99 and 
                    callback_ejecutado['valor_escrito'] == valor_callback):
                    print(f"      ✓ Callback funcionó correctamente")
                    return True
                else:
                    print(f"      ✗ Callback con datos incorrectos")
                    return False
            else:
                print(f"      ✗ Callback no se ejecutó")
                return False
                
        except Exception as e:
            print(f"      ✗ Excepción probando callback: {e}")
            return False
            
    def _test_actualizacion_datos(self) -> bool:
        """Probar actualización dinámica de datos."""
        try:
            if not self.cliente_prueba or not self.servidor:
                return False
                
            # Leer valor inicial de temperatura (registro 10)
            respuesta_inicial = self.cliente_prueba.read_input_registers(
                address=10,
                count=1,
                slave=1
            )
            
            if hasattr(respuesta_inicial, 'registers'):
                valor_inicial = respuesta_inicial.registers[0]
                print(f"      ✓ Valor inicial temperatura: {valor_inicial}")
                
                # Actualizar dato en el servidor
                nuevo_valor = 275  # 27.5°C
                self.servidor.actualizar_dato_sistema('temperatura_promedio', nuevo_valor)
                
                # Esperar un momento
                time.sleep(1)
                
                # Leer valor actualizado
                respuesta_final = self.cliente_prueba.read_input_registers(
                    address=10,
                    count=1,
                    slave=1
                )
                
                if hasattr(respuesta_final, 'registers'):
                    valor_final = respuesta_final.registers[0]
                    print(f"      ✓ Valor final temperatura: {valor_final}")
                    
                    if valor_final == nuevo_valor:
                        print(f"      ✓ Actualización de datos funcionó correctamente")
                        return True
                    else:
                        print(f"      ✗ Valor no se actualizó correctamente")
                        return False
                else:
                    print(f"      ✗ Error leyendo valor final")
                    return False
            else:
                print(f"      ✗ Error leyendo valor inicial")
                return False
                
        except Exception as e:
            print(f"      ✗ Excepción probando actualización: {e}")
            return False
            
    def _test_parada_servidor(self) -> bool:
        """Probar parada correcta del servidor."""
        try:
            # Cerrar cliente primero
            if self.cliente_prueba:
                self.cliente_prueba.close()
                print(f"      ✓ Cliente desconectado")
                
            # Parar servidor
            if self.servidor:
                resultado = self.servidor.desconectar()
                
                if resultado.exitoso:
                    print(f"      ✓ Servidor detenido: {resultado.mensaje}")
                    return True
                else:
                    print(f"      ✗ Error deteniendo servidor: {resultado.mensaje}")
                    return False
            else:
                return True
                
        except Exception as e:
            print(f"      ✗ Excepción deteniendo servidor: {e}")
            return False
            
    def _mostrar_resumen(self, total: int, exitosas: int):
        """Mostrar resumen de las pruebas."""
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE PRUEBAS DEL SERVIDOR MODBUS TCP")
        print("=" * 70)
        print(f"Total de pruebas: {total}")
        print(f"Pruebas exitosas: {exitosas}")
        print(f"Pruebas fallidas: {total - exitosas}")
        print(f"Porcentaje éxito: {(exitosas/total)*100:.1f}%")
        
        if exitosas == total:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("✅ El servidor Modbus TCP está funcionando correctamente")
        else:
            print(f"\n⚠️ {total - exitosas} pruebas fallaron")
            print("❌ Revisar la configuración del servidor")
            
        print("\n📋 Resultados detallados:")
        for nombre, resultado in self.resultados_pruebas.items():
            estado = "✅" if resultado == "EXITOSA" else "❌"
            print(f"   {estado} {nombre}: {resultado}")
            
        print("\n" + "=" * 70)

def main():
    """Función principal para ejecutar las pruebas."""
    print("Iniciando pruebas del servidor Modbus TCP real...")
    
    probador = ProbadorServidorTCP()
    
    try:
        # Ejecutar todas las pruebas
        resultado = probador.ejecutar_todas_las_pruebas()
        
        if resultado:
            print("\n🎯 CONCLUSIÓN: Servidor Modbus TCP listo para uso en producción")
            print("📡 Puedes conectar cualquier cliente Modbus a la IP configurada")
            return 0
        else:
            print("\n🚨 CONCLUSIÓN: Servidor Modbus TCP tiene problemas")
            print("🔧 Revisar configuración y dependencias")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
        return 1
    except Exception as e:
        print(f"\n💥 Error fatal en pruebas: {e}")
        return 1
    finally:
        # Limpiar recursos
        if probador.cliente_prueba:
            try:
                probador.cliente_prueba.close()
            except:
                pass
        if probador.servidor:
            try:
                probador.servidor.desconectar()
            except:
                pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)