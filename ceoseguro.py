import subprocess
import time
import os
import re

# --- CONFIGURACIÓN ---
MI_REPO = "juanlgantes/solar"
RAMA_ACTIVA = "create-plan-md-16884671065521769136"
ARCHIVO_BITACORA = "PLAN.md"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def ejecutar_seguro(cmd_list):
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        return res.stdout.strip() + "\n" + res.stderr.strip()
    except Exception as e:
        return f"ERROR CRITICO: {str(e)}"

def forzar_tachado_tarea(texto_tarea):
    if not os.path.exists(ARCHIVO_BITACORA): return
    with open(ARCHIVO_BITACORA, 'r') as f:
        lineas = f.readlines()
    nueva_lista = []
    cambio_hecho = False
    texto_limpio = texto_tarea.replace("- [ ] ", "").replace("- ", "").replace("[x]", "").strip() # Limpieza extra
    
    for linea in lineas:
        # Buscamos coincidencias flexibles
        if texto_limpio in linea and "- [x]" not in linea:
            if linea.strip().startswith("- "):
                nueva_linea = linea.replace("- ", "- [x] ", 1)
            elif linea.strip()[0].isdigit():
                nueva_linea = linea.replace(". ", ". [x] ", 1)
            else:
                nueva_linea = f"- [x] {linea.strip()}\n"
            nueva_lista.append(nueva_linea)
            cambio_hecho = True
        else:
            nueva_lista.append(linea)     
    if cambio_hecho:
        with open(ARCHIVO_BITACORA, 'w') as f:
            f.writelines(nueva_lista)

def esperar_y_cosechar_con_calma(session_id):
    log(f"⏳ Conectado a sesión {session_id}. Esperando actividad...")
    
    intentos = 0
    cambios_detectados = False
    racha_silencio = 0 # Cuántas veces seguidas Jules no ha enviado nada nuevo tras empezar
    
    while intentos < 80: # 40 min max
        time.sleep(30)
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        mensaje_corto = res.split('\n')[0][:100] 
        print(f"   [{intentos}] Jules: {mensaje_corto}...")

        # Detección de Actividad
        hay_actividad = "diff --git" in res or "Downloaded" in res or "Updated" in res

        if hay_actividad:
            cambios_detectados = True
            racha_silencio = 0 # Reiniciamos contador porque sigue trabajando
            log("   ⚡ Actividad detectada. Dejando que termine...")
        
        elif cambios_detectados and not hay_actividad:
            # Si ya habíamos visto cambios antes, pero ahora hay silencio...
            racha_silencio += 1
            print(f"   (Silencio post-actividad: {racha_silencio}/3)")
            
            # Si lleva 3 intentos (1.5 min) sin enviar nada nuevo DESPUÉS de haber empezado, asumimos fin.
            if racha_silencio >= 3:
                log(f"\n✅ Cosecha finalizada (Jules dejó de escribir).")
                return True
        
        # Criterio de respaldo: Si dice explícitamente que terminó (raro en CLI pero posible)
        if "Completed" in res:
            return True

        intentos += 1
        
    return False

def main():
    log(f"🐢 CEO V16 (PACIENTE & CONTEXTUAL): {MI_REPO}")
    
    # 1. Sync Inicial
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    while True:
        # 2. Leer siguiente tarea
        if not os.path.exists(ARCHIVO_BITACORA):
            log("❌ Falta PLAN.md"); break
            
        with open(ARCHIVO_BITACORA, 'r') as f:
            contenido = f.read()
            
        # Filtro mejorado para ignorar tareas ya tachadas o subtareas completadas
        tareas = []
        for l in contenido.split('\n'):
            l_strip = l.strip()
            if l_strip and (l_strip.startswith('- ') or l_strip[0].isdigit()):
                if "- [x]" not in l_strip and "[x]" not in l_strip:
                    tareas.append(l_strip)
        
        if not tareas:
            log("🎉 ¡PROYECTO TERMINADO! (Ojo: Revisa si quedan subtareas)"); break

        tarea_actual = tareas[0]
        log(f"\n🔨 TAREA: {tarea_actual}")
        
        # 3. LANZAMIENTO CONTEXTUAL V2
        # Añadimos 'git pull' explícito dentro de la sesión de Jules para forzar la actualización
        instrucciones = f"""
        REPO: {MI_REPO}
        RAMA: {RAMA_ACTIVA}
        TAREA: {tarea_actual}
        CONTEXTO OBLIGATORIO:
        1. git fetch origin {RAMA_ACTIVA}
        2. git checkout {RAMA_ACTIVA}
        3. git pull origin {RAMA_ACTIVA} (Asegúrate de tener el código de la tarea anterior).
        4. Realiza la tarea. NO hagas PR.
        """
        instrucciones_linea = instrucciones.replace('\n', ' ').replace('  ', '')
        
        log("🚀 Lanzando Jules (Modo Continuidad)...")
        salida_launch = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones_linea])
        
        match = re.search(r"ID:\s*(\d+)", salida_launch)
        if not match:
            log("❌ ERROR AL LANZAR:"); print(salida_launch); break
        session_id = match.group(1)
        
        # 4. Cosecha Paciente
        if esperar_y_cosechar_con_calma(session_id):
            forzar_tachado_tarea(tarea_actual)
            
            log("💾 Guardando en GitHub (Creando punto de control)...")
            subprocess.run(['git', 'add', '.'], check=False)
            subprocess.run(['git', 'commit', '-m', f"Auto: {tarea_actual[:20]}"], check=False)
            
            # Subida crítica para la siguiente tarea
            res_push = ejecutar_seguro(['git', 'push', 'origin', RAMA_ACTIVA])
            if "error" in res_push.lower() and "fatal" in res_push.lower():
                log(f"⚠️ Error Push: {res_push}"); break
                
            log("🚀 Sincronizado. Contexto actualizado para la siguiente tarea.")
        else:
            log("🛑 Timeout o error."); break

if __name__ == "__main__":
    main()