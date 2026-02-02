import subprocess
import time
import os
import re

# --- CONFIGURACIÓN SOLAR ---
MI_REPO = "juanlgantes/solar"
RAMA_ACTIVA = "create-plan-md-16884671065521769136"
ARCHIVO_BITACORA = "PLAN.md"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def ejecutar_seguro(cmd_list):
    try:
        # Ejecutamos el comando y capturamos todo
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        return res.stdout.strip() + "\n" + res.stderr.strip()
    except Exception as e:
        return f"ERROR CRITICO: {str(e)}"

def esperar_y_cosechar(session_id):
    log(f"⏳ Conectado a sesión {session_id}. Esperando entrega de código...")
    
    intentos = 0
    while intentos < 60: # 30 minutos máximo
        time.sleep(30)
        
        # Hacemos PULL (Traer cambios de la nube al disco)
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        
        # Limpiamos el mensaje para el log
        mensaje_corto = res.split('\n')[0][:120] 
        print(f"   [{intentos}] Respuesta: {mensaje_corto}...")

        # --- CRITERIOS DE ÉXITO V13 ---
        # 1. Si vemos "diff --git", significa que están llegando archivos nuevos. ¡ÉXITO!
        if "diff --git" in res:
            log(f"\n✅ ¡CÓDIGO RECIBIDO! (Cambios detectados en el disco)")
            return True
            
        # 2. Criterios estándar (por si acaso no hay diff visual pero sí descarga)
        if "Downloaded" in res or "Updated" in res or "up to date" in res or "up-to-date" in res:
            # Ignoramos si dice "not ready"
            if "not ready" not in res.lower() and "error" not in res.lower():
                log(f"\n✅ ¡Cosecha completada!")
                return True
        
        intentos += 1
        
    log("\n⚠️ Tiempo agotado. Jules no terminó a tiempo.")
    return False

def main():
    log(f"🧠 CEO V13 (DIFF AWARE): {MI_REPO}")
    
    # 1. Preparación Inicial
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    while True:
        # 2. Leer Tareas Pendientes
        if not os.path.exists(ARCHIVO_BITACORA):
            log("❌ Falta PLAN.md"); break
            
        with open(ARCHIVO_BITACORA, 'r') as f:
            contenido = f.read()
            
        tareas = [l.strip() for l in contenido.split('\n') 
                 if l.strip() and (l.strip().startswith('- ') or l.strip()[0].isdigit()) 
                 and not l.strip().startswith('- [x]')]
        
        if not tareas:
            log("🎉 SIN TAREAS PENDIENTES. PROYECTO FINALIZADO."); break

        tarea_actual = tareas[0]
        log(f"\n🔨 TAREA: {tarea_actual}")
        
        # 3. Lanzar Jules
        # Le pedimos explícitamente que espere en 'Ready' para que podamos hacer pull
        instrucciones = f"CONTEXTO: Repo {MI_REPO} Rama {RAMA_ACTIVA}. TAREA: {tarea_actual}. TU MISION: 1. Genera el código. 2. Modifica {ARCHIVO_BITACORA} marcando la tarea con [x]. 3. IMPORTANTE: No hagas PR, solo quédate esperando."
        
        log("🚀 Lanzando Jules...")
        salida_launch = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones])
        
        match = re.search(r"ID:\s*(\d+)", salida_launch)
        if not match:
            log("❌ ERROR AL LANZAR:"); print(salida_launch); break
            
        session_id = match.group(1)
        
        # 4. Cosechar (Pull)
        if esperar_y_cosechar(session_id):
            log("💾 Confirmando cambios en Git...")
            subprocess.run(['git', 'add', '.'], check=False)
            subprocess.run(['git', 'commit', '-m', f"Auto: {tarea_actual[:30]}"], check=False)
            subprocess.run(['git', 'push', 'origin', RAMA_ACTIVA], check=False)
            log("🚀 Sincronizado. Pasando a la siguiente tarea...")
        else:
            log("🛑 Detenido por timeout.")
            break

if __name__ == "__main__":
    main()