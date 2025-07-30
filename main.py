"""
Aplicación Principal del Sistema BMS Demo - Módulo 1
===================================================

Este es el punto de entrada principal para probar el Módulo 1 del sistema BMS.
Incluye configuración, protocolo Modbus y modelos básicos.

Autor: Sistema BMS Demo
Versión: 1.0.2 - Corrección final
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes del sistema
from configuracion.configuracion_general import obtener_config, configuracion
from configuracion.configuracion_protocolos import configurador_protocolos
from configuracion.configuracion_base_datos import configurador_bd
from utilidades.logger import obtener_logger_sistema, configurar_nivel_logging
from protocolos.modbus.manejador_modbus import ManejadorModbus, ModoOperacionModbus
from modelos.dispositivo import Dispositivo, TipoDispositivo, EstadoDispositivo, ConfiguracionDispositivo, ProtocoloComunicacion
from modelos.sensor import crear_sensor_temperatura, crear_sensor_humedad, TipoSensor

class SistemaBMSDemo:
    """
    Clase principal del sistema BMS Demo para Módulo 1.
    Coordina todos los componentes y servicios.
    """
    
    def __init__(self):
        """Inicializar sistema BMS Demo."""
        self.logger = obtener_logger_sistema()
        self.config = obtener_config()
        self.activo = False
        self.manejador_modbus = None
        self.dispositivos_demo = []
        self.sensores_demo = []
        self.tiempo_inicio = datetime.now()
        
        # Control de señales
        signal.signal(signal.SIGINT, self._manejar_senal_salida)
        signal.signal(signal.SIGTERM, self._manejar_senal_salida)
        
        self.logger.info("Sistema BMS Demo inicializado")
        
    def inicializar(self) -> bool:
        """
        Inicializar todos los componentes del sistema.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("Iniciando inicialización del sistema BMS Demo...")
            
            # Mostrar configuración
            self._mostrar_configuracion_sistema()
            
            # Validar configuraciones
            if not self._validar_configuraciones():
                return False
                
            # Crear dispositivos y sensores de demostración
            self._crear_dispositivos_demo()
            
            # Inicializar protocolo Modbus
            if not self._inicializar_modbus():
                self.logger.warning("Modbus no se pudo inicializar, continuando sin él")
                
            # Configurar callbacks y eventos
            self._configurar_callbacks()
            
            self.activo = True
            self.logger.info("✓ Sistema BMS Demo inicializado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en inicialización: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    def _mostrar_configuracion_sistema(self):
        """Mostrar configuración actual del sistema."""
        self.logger.info("="*60)
        self.logger.info("CONFIGURACIÓN SISTEMA BMS DEMO - MÓDULO 1")
        self.logger.info("="*60)
        
        # Configuración general
        self.logger.info(f"Nombre: {self.config.NOMBRE_SISTEMA}")
        self.logger.info(f"Versión: {self.config.VERSION_SISTEMA}")
        self.logger.info(f"IP BMS: {self.config.IP_BMS}:{self.config.PUERTO_BMS}")
        self.logger.info(f"IP Genetec: {self.config.IP_GENETEC}:{self.config.PUERTO_GENETEC}")
        self.logger.info(f"Modo Debug: {self.config.DEBUG}")
        self.logger.info(f"Entorno: {self.config.ENTORNO}")
        
        # Protocolos habilitados
        try:
            protocolos = configurador_protocolos.obtener_protocolos_habilitados()
            self.logger.info(f"Protocolos habilitados: {[p.value for p in protocolos]}")
        except Exception as e:
            self.logger.warning(f"Error obteniendo protocolos: {e}")
        
        # Base de datos
        try:
            url_bd = configurador_bd.obtener_url_conexion()  # Método correcto
            self.logger.info(f"Base de datos: {url_bd}")
        except Exception as e:
            self.logger.warning(f"Error obteniendo configuración BD: {e}")
        
        self.logger.info("="*60)
        
    def _validar_configuraciones(self) -> bool:
        """Validar que todas las configuraciones sean correctas."""
        try:
            # Validar configuración general
            self.config.validar_configuracion()
            self.logger.info("✓ Configuración general válida")
            
            # Validar configuración de base de datos
            try:
                if not configurador_bd.validar_configuracion():
                    self.logger.error("✗ Configuración de base de datos inválida")
                    return False
                self.logger.info("✓ Configuración de base de datos válida")
            except Exception as e:
                self.logger.warning(f"Error validando BD (continuando): {e}")
            
            # Validar protocolos
            try:
                protocolos = configurador_protocolos.obtener_protocolos_habilitados()
                if not protocolos:
                    self.logger.warning("⚠ No hay protocolos habilitados")
                else:
                    self.logger.info(f"✓ Protocolos válidos: {len(protocolos)}")
            except Exception as e:
                self.logger.warning(f"Error validando protocolos: {e}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando configuraciones: {e}")
            return False
            
    def _crear_dispositivos_demo(self):
        """Crear dispositivos y sensores de demostración."""
        try:
            self.logger.info("Creando dispositivos de demostración...")
            
            # Dispositivo 1: Cámara IP
            config_camara = ConfiguracionDispositivo(
                ip="192.168.1.101",
                puerto=80,
                protocolo=ProtocoloComunicacion.HTTP,
                timeout=30,
                intervalo_polling=60
            )
            
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
                monitoreado=True
            )
            camara.configuracion = config_camara
            camara.agregar_etiqueta("seguridad")
            camara.agregar_etiqueta("laboratorio")
            self.dispositivos_demo.append(camara)
            
            # Dispositivo 2: Controlador de puerta
            config_controlador = ConfiguracionDispositivo(
                ip="192.168.1.102",
                puerto=4040,
                protocolo=ProtocoloComunicacion.TCP_IP,
                timeout=15,
                intervalo_polling=30
            )
            
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
                monitoreado=True
            )
            controlador.configuracion = config_controlador
            controlador.agregar_etiqueta("acceso")
            controlador.agregar_etiqueta("mercury")
            self.dispositivos_demo.append(controlador)
            
            # Dispositivo 3: UPS Mini
            config_ups = ConfiguracionDispositivo(
                ip="192.168.1.103",
                puerto=161,
                protocolo=ProtocoloComunicacion.SNMP,
                timeout=10,
                intervalo_polling=120
            )
            
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
                monitoreado=True
            )
            ups.configuracion = config_ups
            ups.agregar_etiqueta("energia")
            ups.agregar_etiqueta("critico")
            self.dispositivos_demo.append(ups)
            
            # Crear sensores asociados (con IDs ficticios)
            # Sensor de temperatura para el laboratorio
            sensor_temp = crear_sensor_temperatura(1, "Sensor Temperatura Lab")
            # Inicializar factor_correccion si es None
            if sensor_temp.factor_correccion is None:
                sensor_temp.factor_correccion = 1.0
            if sensor_temp.offset_correccion is None:
                sensor_temp.offset_correccion = 0.0
            self.sensores_demo.append(sensor_temp)
            
            # Sensor de humedad para el laboratorio  
            sensor_humedad = crear_sensor_humedad(1, "Sensor Humedad Lab")
            # Inicializar factor_correccion si es None
            if sensor_humedad.factor_correccion is None:
                sensor_humedad.factor_correccion = 1.0
            if sensor_humedad.offset_correccion is None:
                sensor_humedad.offset_correccion = 0.0
            self.sensores_demo.append(sensor_humedad)
            
            self.logger.info(f"✓ Creados {len(self.dispositivos_demo)} dispositivos demo")
            self.logger.info(f"✓ Creados {len(self.sensores_demo)} sensores demo")
            
        except Exception as e:
            self.logger.error(f"Error creando dispositivos demo: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
    def _inicializar_modbus(self) -> bool:
        """Inicializar manejador de protocolo Modbus."""
        try:
            self.logger.info("Inicializando protocolo Modbus...")
            
            # Crear manejador en modo servidor solamente (más estable)
            self.manejador_modbus = ManejadorModbus(ModoOperacionModbus.SOLO_SERVIDOR)
            
            # Intentar iniciar
            resultado = self.manejador_modbus.iniciar()
            
            if resultado.exitoso:
                self.logger.info(f"✓ Protocolo Modbus iniciado: {resultado.mensaje}")
                return True
            else:
                self.logger.warning(f"⚠ Error iniciando Modbus: {resultado.mensaje}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error inicializando Modbus: {e}")
            return False
            
    def _configurar_callbacks(self):
        """Configurar callbacks y eventos del sistema."""
        try:
            # Callback para datos Modbus
            if self.manejador_modbus:
                self.manejador_modbus.agregar_callback_datos(self._callback_datos_modbus)
                
            self.logger.info("✓ Callbacks configurados")
            
        except Exception as e:
            self.logger.error(f"Error configurando callbacks: {e}")
            
    def _callback_datos_modbus(self, datos: Dict[str, Any]):
        """
        Callback para datos recibidos vía Modbus.
        
        Args:
            datos: Datos recibidos del protocolo Modbus
        """
        self.logger.debug(f"Datos Modbus recibidos: {datos}")
        
        # Actualizar sensores con datos recibidos
        try:
            for sensor in self.sensores_demo:
                if sensor.tipo_sensor == TipoSensor.TEMPERATURA.value:
                    if 'temperatura' in datos:
                        temperatura = datos['temperatura'] / 10.0  # Convertir de x10
                        alertas = sensor.actualizar_valor(temperatura)
                        if alertas:
                            self.logger.warning(f"Alertas en sensor temperatura: {[a.value for a in alertas]}")
        except Exception as e:
            self.logger.error(f"Error procesando callback Modbus: {e}")
                        
    def ejecutar(self):
        """Ejecutar bucle principal del sistema."""
        try:
            self.logger.info("Iniciando bucle principal del sistema BMS Demo...")
            
            contador_ciclos = 0
            
            while self.activo:
                contador_ciclos += 1
                
                # Mostrar estado cada 30 segundos (6 ciclos de 5 segundos)
                if contador_ciclos % 6 == 0:
                    self._mostrar_estado_sistema()
                    
                # Simular lecturas de sensores cada 15 segundos (3 ciclos)
                if contador_ciclos % 3 == 0:
                    self._simular_lecturas_sensores()
                    
                # Verificar estado de dispositivos cada minuto (12 ciclos)
                if contador_ciclos % 12 == 0:
                    self._verificar_estado_dispositivos()
                    
                # Esperar 5 segundos
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.logger.info("Interrupción recibida, deteniendo sistema...")
        except Exception as e:
            self.logger.error(f"Error en bucle principal: {e}")
        finally:
            self.detener()
            
    def _mostrar_estado_sistema(self):
        """Mostrar estado actual del sistema."""
        try:
            self.logger.info("-" * 50)
            self.logger.info("ESTADO ACTUAL DEL SISTEMA BMS")
            self.logger.info("-" * 50)
            
            # Estado general
            tiempo_funcionamiento = datetime.now() - self.tiempo_inicio
            self.logger.info(f"Tiempo funcionamiento: {tiempo_funcionamiento}")
            
            # Estado dispositivos
            dispositivos_online = len([d for d in self.dispositivos_demo if d.esta_online()])
            self.logger.info(f"Dispositivos: {dispositivos_online}/{len(self.dispositivos_demo)} online")
            
            # Estado sensores
            sensores_alarma = len([s for s in self.sensores_demo if s.esta_en_alarma()])
            self.logger.info(f"Sensores: {len(self.sensores_demo)} total, {sensores_alarma} en alarma")
            
            # Estado Modbus
            if self.manejador_modbus:
                try:
                    estado_modbus = self.manejador_modbus.obtener_estado_completo()
                    self.logger.info(f"Modbus: {estado_modbus['modo_operacion']} - Activo: {estado_modbus['activo']}")
                    if 'estadisticas' in estado_modbus:
                        stats = estado_modbus['estadisticas']
                        self.logger.info(f"  Operaciones: {stats['total_operaciones']} (éxito: {stats['tasa_exito']}%)")
                except Exception as e:
                    self.logger.debug(f"Error obteniendo estado Modbus: {e}")
                    
            self.logger.info("-" * 50)
            
        except Exception as e:
            self.logger.error(f"Error mostrando estado: {e}")
            
    def _simular_lecturas_sensores(self):
        """Simular lecturas de sensores para demostración."""
        try:
            import random
            
            for sensor in self.sensores_demo:
                try:
                    if sensor.tipo_sensor == TipoSensor.TEMPERATURA.value:
                        # Simular temperatura entre 18-28°C con variación
                        temperatura = 23 + random.uniform(-5, 5)
                        alertas = sensor.actualizar_valor(temperatura)
                        
                        if alertas:
                            self.logger.warning(f"⚠ Alertas temperatura: {[a.value for a in alertas]} - Valor: {temperatura:.1f}°C")
                        else:
                            self.logger.debug(f"Temperatura actualizada: {temperatura:.1f}°C")
                            
                    elif sensor.tipo_sensor == TipoSensor.HUMEDAD.value:
                        # Simular humedad entre 40-70%
                        humedad = 55 + random.uniform(-15, 15)
                        alertas = sensor.actualizar_valor(humedad)
                        
                        if alertas:
                            self.logger.warning(f"⚠ Alertas humedad: {[a.value for a in alertas]} - Valor: {humedad:.0f}%")
                        else:
                            self.logger.debug(f"Humedad actualizada: {humedad:.0f}%")
                            
                except Exception as e:
                    self.logger.error(f"Error actualizando sensor {sensor.tipo_sensor}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error simulando lecturas: {e}")
            
    def _verificar_estado_dispositivos(self):
        """Verificar estado de todos los dispositivos."""
        try:
            for dispositivo in self.dispositivos_demo:
                # Simular verificación de conectividad
                import random
                if random.random() > 0.1:  # 90% probabilidad de estar online
                    if not dispositivo.esta_online():
                        dispositivo.actualizar_estado(EstadoDispositivo.ONLINE, random.uniform(0.1, 2.0))
                        self.logger.info(f"✓ Dispositivo {dispositivo.nombre} volvió online")
                else:
                    if dispositivo.esta_online():
                        dispositivo.actualizar_estado(EstadoDispositivo.OFFLINE)
                        self.logger.warning(f"⚠ Dispositivo {dispositivo.nombre} se desconectó")
                        
        except Exception as e:
            self.logger.error(f"Error verificando dispositivos: {e}")
            
    def _manejar_senal_salida(self, signum, frame):
        """Manejar señales de salida del sistema."""
        self.logger.info(f"Señal recibida: {signum}, iniciando parada del sistema...")
        self.activo = False
        
    def detener(self):
        """Detener sistema y limpiar recursos."""
        try:
            self.logger.info("Deteniendo sistema BMS Demo...")
            
            self.activo = False
            
            # Detener protocolo Modbus
            if self.manejador_modbus:
                try:
                    resultado = self.manejador_modbus.detener()
                    self.logger.info(f"Modbus detenido: {resultado.mensaje}")
                except Exception as e:
                    self.logger.error(f"Error deteniendo Modbus: {e}")
                
            # Limpiar recursos
            self.dispositivos_demo.clear()
            self.sensores_demo.clear()
            
            self.logger.info("✓ Sistema BMS Demo detenido completamente")
            
        except Exception as e:
            self.logger.error(f"Error deteniendo sistema: {e}")

def main():
    """Función principal del sistema BMS Demo."""
    print("="*60)
    print("SISTEMA BMS DEMO - MÓDULO 1")
    print("Configuración base + Protocolo Modbus + Modelos")
    print("="*60)
    
    # Crear e inicializar sistema
    sistema = SistemaBMSDemo()
    
    if sistema.inicializar():
        print("✓ Sistema inicializado correctamente")
        print("Presiona Ctrl+C para detener el sistema")
        print("-" * 60)
        
        # Ejecutar sistema
        sistema.ejecutar()
    else:
        print("✗ Error inicializando sistema")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)