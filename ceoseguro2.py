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
    texto_limpio = texto_tarea.replace("- [ ] ", "").replace("- ", "").replace("[x]", "").strip()
    
    for linea in lineas:
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
        log("✅ (Local) Plan actualizado correctamente.")

def esperar_y_cosechar_con_calma_profunda(session_id):
    log(f"⏳ Conectado a sesión {session_id}. Esperando actividad...")
    
    intentos = 0
    cambios_detectados = False
    racha_silencio = 0 
    
    # LIMITES DE TIEMPO (AJUSTADOS A TU PETICIÓN)
    # 200 intentos * 30s = 100 minutos máx de sesión total
    # racha_silencio >= 10 * 30s = 5 MINUTOS de silencio para confirmar fin
    
    while intentos < 200: 
        time.sleep(30)
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        mensaje_corto = res.split('\n')[0][:100] 
        
        # Filtramos mensajes vacíos
        if "No diff found" in mensaje_corto:
            print(f"   [{intentos}] ... (Sin novedades)")
        else:
            print(f"   [{intentos}] Jules: {mensaje_corto}...")

        hay_actividad = "diff --git" in res or "Downloaded" in res or "Updated" in res

        if hay_actividad:
            cambios_detectados = True
            racha_silencio = 0 # Reiniciamos el reloj si hay movimiento
            log("   ⚡ ¡Datos recibidos! Reiniciando cuenta atrás de seguridad...")
        
        elif cambios_detectados and not hay_actividad:
            # Ya bajamos cosas, ahora estamos esperando a ver si acabó de verdad
            racha_silencio += 1
            minutos_silencio = racha_silencio * 0.5
            print(f"   (Zona de Calma: {minutos_silencio} min / 5.0 min requeridos)")
            
            # 10 rachas de 30s = 5 MINUTOS de silencio absoluto
            if racha_silencio >= 10:
                log(f"\n✅ Cosecha finalizada (5 minutos sin cambios).")
                return True
        
        if "Completed" in res:
            # Si Jules dice explícitamente "Completed", esperamos un ciclo más por seguridad y salimos
            if racha_silencio >= 2: 
                return True

        intentos += 1
        
    return False

def main():
    log(f"🧘 CEO V17 (DEEP CALM - FULL DAY WORKER): {MI_REPO}")
    
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    while True:
        if not os.path.exists(ARCHIVO_BITACORA):
            log("❌ Falta PLAN.md"); break
            
        with open(ARCHIVO_BITACORA, 'r') as f:
            contenido = f.read()
            
        tareas = []
        for l in contenido.split('\n'):
            l_strip = l.strip()
            if l_strip and (l_strip.startswith('- ') or l_strip[0].isdigit()):
                if "- [x]" not in l_strip and "[x]" not in l_strip:
                    tareas.append(l_strip)
        
        if not tareas:
            log("🎉 ¡PROYECTO TERMINADO! (A disfrutar del día)"); break

        tarea_actual = tareas[0]
        log(f"\n🔨 TAREA: {tarea_actual}")
        
        # INSTRUCCIONES DE CONTINUIDAD
        instrucciones = f"""
        REPO: {MI_REPO}
        RAMA: {RAMA_ACTIVA}
        TAREA: {tarea_actual}
        CONTEXTO OBLIGATORIO:
        1. git fetch origin {RAMA_ACTIVA}
        2. git checkout {RAMA_ACTIVA}
        3. git pull origin {RAMA_ACTIVA}
        4. Realiza la tarea completa. Tómate tu tiempo.
        """
        instrucciones_linea = instrucciones.replace('\n', ' ').replace('  ', '')
        
        log("🚀 Lanzando Jules...")
        salida_launch = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones_linea])
        
        match = re.search(r"ID:\s*(\d+)", salida_launch)
        if not match:
            log("❌ ERROR AL LANZAR:"); print(salida_launch); break
        session_id = match.group(1)
        
        # MODO DEEP CALM
        if esperar_y_cosechar_con_calma_profunda(session_id):
            forzar_tachado_tarea(tarea_actual)
            
            log("💾 Guardando en GitHub...")
            subprocess.run(['git', 'add', '.'], check=False)
            subprocess.run(['git', 'commit', '-m', f"Auto: {tarea_actual[:20]}"], check=False)
            
            res_push = ejecutar_seguro(['git', 'push', 'origin', RAMA_ACTIVA])
            if "error" in res_push.lower() and "fatal" in res_push.lower():
                log(f"⚠️ Error Push: {res_push}"); break
                
            log("🚀 Sincronizado. Todo seguro.")
        else:
            log("🛑 Timeout extremo."); break

if __name__ == "__main__":
    main()