# app.py - Versión con debug avanzado
from flask import Flask, render_template, jsonify
import sys
import os

# Agregar el directorio padre para importar tu sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar tu sistema existente
try:
    from main import SistemaBMSDemo
    from base_datos.conexion_bd import obtener_sesion, verificar_bd_disponible
    from modelos.dispositivo import Dispositivo
    from modelos.sensor import Sensor
    print("✓ Importaciones exitosas")
except Exception as e:
    print(f"✗ Error en importaciones: {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-key-simple'

# Instancia global de tu sistema BMS
sistema_bms = None

@app.route('/')
def dashboard():
    """Dashboard principal simple."""
    return render_template('dashboard.html')

@app.route('/dispositivos')
def dispositivos():
    """Lista de dispositivos."""
    return render_template('dispositivos.html')

@app.route('/sensores')
def sensores():
    """Monitoreo de sensores."""
    return render_template('sensores.html')

@app.route('/modbus')
def modbus():
    """Estado Modbus."""
    return render_template('modbus.html')

# APIs con debug avanzado
@app.route('/api/dispositivos')
def api_dispositivos():
    """API: Lista dispositivos con debug."""
    debug_info = {
        'bd_disponible': False,
        'error': None,
        'datos': [],
        'count_bd': 0
    }
    
    try:
        # Verificar BD
        debug_info['bd_disponible'] = verificar_bd_disponible()
        print(f"BD disponible: {debug_info['bd_disponible']}")
        
        if not debug_info['bd_disponible']:
            debug_info['error'] = "Base de datos no disponible"
            return jsonify(debug_info)
        
        # Intentar consulta
        with obtener_sesion() as session:
            dispositivos = session.query(Dispositivo).all()
            debug_info['count_bd'] = len(dispositivos)
            print(f"Dispositivos encontrados en BD: {debug_info['count_bd']}")
            
            debug_info['datos'] = [{
                'id': d.id,
                'nombre': d.nombre,
                'tipo': d.tipo,
                'estado': d.estado,
                'ip': d.direccion_ip
            } for d in dispositivos]
            
        # Si no hay datos en BD, crear datos demo
        if debug_info['count_bd'] == 0:
            debug_info['datos'] = [
                {
                    'id': 1,
                    'nombre': 'Cámara Lab 01 (Demo)',
                    'tipo': 'camara',
                    'estado': 'online',
                    'ip': '192.168.1.101'
                },
                {
                    'id': 2,
                    'nombre': 'Controlador Puerta Lab (Demo)', 
                    'tipo': 'controlador',
                    'estado': 'online',
                    'ip': '192.168.1.102'
                },
                {
                    'id': 3,
                    'nombre': 'UPS Lab Mini (Demo)',
                    'tipo': 'ups', 
                    'estado': 'online',
                    'ip': '192.168.1.103'
                }
            ]
            debug_info['error'] = "Usando datos demo - BD vacía"
            
        return jsonify(debug_info['datos'])
        
    except Exception as e:
        debug_info['error'] = str(e)
        print(f"Error en api_dispositivos: {e}")
        
        # Datos de emergencia
        return jsonify([{
            'id': 999,
            'nombre': 'Error - Datos de prueba',
            'tipo': 'error',
            'estado': 'offline',
            'ip': 'N/A'
        }])

@app.route('/api/sensores')
def api_sensores():
    """API: Lista sensores con debug."""
    debug_info = {
        'bd_disponible': False,
        'error': None,
        'datos': [],
        'count_bd': 0
    }
    
    try:
        debug_info['bd_disponible'] = verificar_bd_disponible()
        
        if not debug_info['bd_disponible']:
            debug_info['error'] = "Base de datos no disponible"
            # Datos demo
            return jsonify([
                {
                    'id': 1,
                    'tipo': 'temperatura',
                    'valor': 23.5,
                    'unidad': '°C'
                },
                {
                    'id': 2,
                    'tipo': 'humedad',
                    'valor': 65,
                    'unidad': '%'
                }
            ])
        
        with obtener_sesion() as session:
            sensores = session.query(Sensor).all()
            debug_info['count_bd'] = len(sensores)
            print(f"Sensores encontrados en BD: {debug_info['count_bd']}")
            
            debug_info['datos'] = [{
                'id': s.id,
                'tipo': s.tipo_sensor,
                'valor': s.valor_actual,
                'unidad': s.unidad_medida
            } for s in sensores]
            
        # Si no hay datos, usar datos demo con simulación
        if debug_info['count_bd'] == 0:
            import random
            import time
            # Simular datos que cambien
            base_time = int(time.time()) % 100
            temp = 20 + (base_time % 20) + random.uniform(-2, 2)
            hum = 50 + (base_time % 30) + random.uniform(-5, 5)
            
            debug_info['datos'] = [
                {
                    'id': 1,
                    'tipo': 'temperatura',
                    'valor': round(temp, 1),
                    'unidad': '°C'
                },
                {
                    'id': 2,
                    'tipo': 'humedad',
                    'valor': round(hum, 0),
                    'unidad': '%'
                }
            ]
            debug_info['error'] = "Usando datos demo simulados - BD vacía"
            
        return jsonify(debug_info['datos'])
        
    except Exception as e:
        debug_info['error'] = str(e)
        print(f"Error en api_sensores: {e}")
        return jsonify([])

@app.route('/api/estado')
def api_estado():
    """API: Estado general del sistema."""
    try:
        estado_base = {
            'activo': True,
            'modo_operacion': 'solo_servidor',
            'tiempo_funcionamiento': 'Calculando...',
            'estadisticas': {
                'total_operaciones': 0,
                'tasa_exito': 100,
                'tiempo_operacion': '0:05:30'
            }
        }
        
        if sistema_bms and sistema_bms.manejador_modbus:
            estado_real = sistema_bms.manejador_modbus.obtener_estado_completo()
            print(f"Estado real del sistema: {estado_real}")
            return jsonify(estado_real)
        else:
            print("Sistema BMS no disponible, usando estado base")
            return jsonify(estado_base)
            
    except Exception as e:
        print(f"Error en api_estado: {e}")
        return jsonify({
            'error': str(e), 
            'activo': False,
            'modo_operacion': 'error'
        })

@app.route('/api/debug')
def api_debug():
    """API: Información de debug completa."""
    debug = {
        'sistema_bms_activo': sistema_bms is not None,
        'bd_disponible': False,
        'ruta_bd': 'desconocida',
        'tablas_bd': [],
        'count_dispositivos': 0,
        'count_sensores': 0,
        'error': None
    }
    
    try:
        # Verificar BD
        debug['bd_disponible'] = verificar_bd_disponible()
        
        if debug['bd_disponible']:
            from base_datos.conexion_bd import gestor_bd
            debug['ruta_bd'] = str(gestor_bd.config_bd.ruta / f"{gestor_bd.config_bd.nombre}.db")
            
            # Obtener info de salud
            salud = gestor_bd.verificar_salud_bd()
            debug['tablas_bd'] = salud.get('tablas_existentes', [])
            debug['count_dispositivos'] = salud.get('conteo_dispositivos', 0)
            debug['count_sensores'] = salud.get('conteo_sensores', 0)
            
    except Exception as e:
        debug['error'] = str(e)
        
    return jsonify(debug)

@app.route('/api/crear_datos_demo')
def api_crear_datos_demo():
    """API: Crear datos de demostración en la BD."""
    try:
        from base_datos.conexion_bd import crear_datos_demo
        crear_datos_demo()
        return jsonify({
            'success': True,
            'mensaje': 'Datos de demostración creados exitosamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def inicializar_sistema():
    """Función para inicializar el sistema BMS."""
    global sistema_bms
    print("Inicializando sistema BMS...")
    
    try:
        # Verificar BD primero
        bd_ok = verificar_bd_disponible()
        print(f"Base de datos disponible: {bd_ok}")
        
        if bd_ok:
            # Crear datos demo si la BD está vacía
            try:
                with obtener_sesion() as session:
                    count_dispositivos = session.query(Dispositivo).count()
                    if count_dispositivos == 0:
                        print("BD vacía, creando datos demo...")
                        from base_datos.conexion_bd import crear_datos_demo
                        crear_datos_demo()
                        print("✓ Datos demo creados")
            except Exception as e:
                print(f"Warning: No se pudieron crear datos demo: {e}")
        
        # Inicializar sistema BMS
        sistema_bms = SistemaBMSDemo()
        if sistema_bms.inicializar():
            print("✓ Sistema BMS iniciado correctamente")
            return True
        else:
            print("✗ Error inicializando sistema BMS")
            return False
    except Exception as e:
        print(f"✗ Excepción inicializando sistema BMS: {e}")
        return False

if __name__ == '__main__':
    print("=== INICIANDO APLICACIÓN WEB BMS ===")
    
    # Verificar dependencias
    try:
        print("Verificando dependencias...")
        bd_disponible = verificar_bd_disponible()
        print(f"✓ Base de datos: {'OK' if bd_disponible else 'ERROR'}")
        
        # Mostrar ruta de BD para debug
        try:
            from base_datos.conexion_bd import gestor_bd
            ruta_bd = gestor_bd.config_bd.ruta / f"{gestor_bd.config_bd.nombre}.db"
            print(f"✓ Ruta BD: {ruta_bd}")
            print(f"✓ BD existe: {ruta_bd.exists() if hasattr(ruta_bd, 'exists') else 'N/A'}")
        except Exception as e:
            print(f"Warning: No se pudo obtener info de BD: {e}")
            
    except Exception as e:
        print(f"Error verificando dependencias: {e}")
    
    # Inicializar el sistema BMS
    if inicializar_sistema():
        print("✓ Iniciando servidor web en http://localhost:5000")
        print("✓ Dashboard: http://localhost:5000")
        print("✓ Debug API: http://localhost:5000/api/debug")
        print("✓ Presiona Ctrl+C para detener")
        print("==========================================")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    else:
        print("✗ No se pudo inicializar el sistema BMS")
        print("✗ Iniciando solo el servidor web para debug...")
        print("✓ Debug API disponible en: http://localhost:5000/api/debug")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)