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

def esperar_y_cosechar(session_id):
    log(f"⏳ Conectado a sesión {session_id}. Intentando cosecha...")
    
    intentos = 0
    while intentos < 60: # 30 mins
        time.sleep(30)
        
        # Ejecutamos pull
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        
        # MODO VERBOSE: Imprimimos lo que dice Jules para no estar ciegos
        mensaje_limpio = res.replace('\n', ' ').strip()[:100] # Solo los primeros 100 caracteres
        print(f"   [{intentos}] Jules dice: {mensaje_limpio}")

        # CRITERIOS DE ÉXITO AMPLIADOS
        # Si descargó, si actualizó, o si ya estaba actualizado (significa que ya bajó)
        if "Downloaded" in res or "Updated" in res or "up to date" in res or "up-to-date" in res:
            if "not ready" not in res.lower() and "error" not in res.lower():
                log(f"\n✅ ¡Cosecha exitosa!")
                return True
        
        intentos += 1
        
    log("\n⚠️ Tiempo agotado. Revisa el mensaje de arriba para ver por qué.")
    return False

def main():
    log(f"👁️ CEO V12 (VERBOSE MODE): {MI_REPO}")
    
    # 1. Init
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    while True:
        # 2. Buscar Tareas
        if not os.path.exists(ARCHIVO_BITACORA):
            log("❌ Falta PLAN.md"); break
            
        with open(ARCHIVO_BITACORA, 'r') as f:
            contenido = f.read()
            
        tareas = [l.strip() for l in contenido.split('\n') 
                 if l.strip() and (l.strip().startswith('- ') or l.strip()[0].isdigit()) 
                 and not l.strip().startswith('- [x]')]
        
        if not tareas:
            log("🎉 SIN TAREAS PENDIENTES."); break

        tarea_actual = tareas[0]
        log(f"\n🔨 TAREA: {tarea_actual}")
        
        # 3. Lanzar
        instrucciones = f"CONTEXTO: Repo {MI_REPO} Rama {RAMA_ACTIVA}. TAREA: {tarea_actual}. TU MISION: 1. Genera el código. 2. Modifica {ARCHIVO_BITACORA} marcando la tarea con [x]. 3. IMPORTANTE: Quédate esperando en estado 'Ready'."
        
        log("🚀 Lanzando Jules...")
        salida_launch = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones])
        
        match = re.search(r"ID:\s*(\d+)", salida_launch)
        if not match:
            log("❌ ERROR AL LANZAR:"); print(salida_launch); break
            
        session_id = match.group(1)
        
        # 4. Cosechar
        if esperar_y_cosechar(session_id):
            log("💾 Guardando...")
            subprocess.run(['git', 'add', '.'], check=False)
            subprocess.run(['git', 'commit', '-m', f"Auto: {tarea_actual[:20]}"], check=False)
            subprocess.run(['git', 'push', 'origin', RAMA_ACTIVA], check=False)
            log("🚀 Hecho. Siguiente...")
        else:
            break

if __name__ == "__main__":
    main()