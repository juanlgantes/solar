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
    """Marca la tarea como hecha localmente para asegurar el avance."""
    if not os.path.exists(ARCHIVO_BITACORA): return
    
    with open(ARCHIVO_BITACORA, 'r') as f:
        lineas = f.readlines()
    
    nueva_lista = []
    cambio_hecho = False
    texto_limpio = texto_tarea.replace("- [ ] ", "").replace("- ", "").strip()
    
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

def esperar_y_cosechar(session_id):
    log(f"⏳ Conectado a sesión {session_id}. Esperando código...")
    intentos = 0
    while intentos < 60: # 30 min
        time.sleep(30)
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        mensaje_corto = res.split('\n')[0][:100] 
        print(f"   [{intentos}] Jules: {mensaje_corto}...")

        # Si hay diff o descarga confirmada
        if "diff --git" in res or "Downloaded" in res or "Updated" in res or "up to date" in res:
             if "not ready" not in res.lower() and "error" not in res.lower():
                log(f"\n✅ ¡CÓDIGO RECIBIDO!")
                return True
        intentos += 1
    return False

def main():
    log(f"🔗 CEO V15 (CHAIN OF CUSTODY): {MI_REPO}")
    
    # 1. Asegurar estado local correcto
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    while True:
        # 2. Leer siguiente tarea
        if not os.path.exists(ARCHIVO_BITACORA):
            log("❌ Falta PLAN.md"); break
            
        with open(ARCHIVO_BITACORA, 'r') as f:
            contenido = f.read()
            
        tareas = [l.strip() for l in contenido.split('\n') 
                 if l.strip() and (l.strip().startswith('- ') or l.strip()[0].isdigit()) 
                 and not l.strip().startswith('- [x]')]
        
        if not tareas:
            log("🎉 ¡PROYECTO TERMINADO!"); break

        tarea_actual = tareas[0]
        log(f"\n🔨 TAREA: {tarea_actual}")
        
        # 3. LANZAMIENTO INTELIGENTE (AQUÍ ESTÁ LA CLAVE)
        # Le decimos explícitamente que cambie a la rama donde guardamos el trabajo anterior
        instrucciones = f"""
        REPO: {MI_REPO}
        RAMA OBJETIVO: {RAMA_ACTIVA}
        TAREA: {tarea_actual}
        
        INSTRUCCIONES CRÍTICAS:
        1. Ejecuta: git fetch origin {RAMA_ACTIVA}
        2. Ejecuta: git checkout {RAMA_ACTIVA} (IMPORTANTE: Debes construir sobre el trabajo previo).
        3. Realiza la tarea solicitada.
        4. Quédate esperando (NO hagas PR).
        """
        
        # Convertimos a una línea para evitar errores de shell
        instrucciones_linea = instrucciones.replace('\n', ' ').replace('  ', '')
        
        log("🚀 Lanzando Jules con instrucciones de continuidad...")
        salida_launch = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones_linea])
        
        match = re.search(r"ID:\s*(\d+)", salida_launch)
        if not match:
            log("❌ ERROR AL LANZAR:"); print(salida_launch); break
            
        session_id = match.group(1)
        
        # 4. Cosechar, Guardar, Repetir
        if esperar_y_cosechar(session_id):
            forzar_tachado_tarea(tarea_actual)
            
            log("💾 Guardando estado en la Nube (GitHub)...")
            subprocess.run(['git', 'add', '.'], check=False)
            subprocess.run(['git', 'commit', '-m', f"Auto: {tarea_actual[:20]}"], check=False)
            
            # EL PUSH ES VITAL: Es lo que permite que la siguiente sesión vea este trabajo
            res_push = ejecutar_seguro(['git', 'push', 'origin', RAMA_ACTIVA])
            
            if "error" in res_push.lower() and "fatal" in res_push.lower():
                log(f"⚠️ Error en Push: {res_push}")
                # Si falla el push, paramos, porque si no la siguiente tarea fallará
                break
                
            log("🚀 Sincronizado. La base está lista para la siguiente tarea.")
        else:
            log("🛑 Timeout."); break

if __name__ == "__main__":
    main()