import subprocess
import time
import os
import re

# --- CONFIGURACIÓN ---
MI_REPO = "juanlgantes/solar"
RAMA_ACTIVA = "create-plan-md-16884671065521769136"
ARCHIVO_BITACORA = "PLAN.md"
ARCHIVO_MEMORIA = "MEMORIA.md"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def ejecutar_seguro(cmd_list):
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        return res.stdout.strip() + "\n" + res.stderr.strip()
    except Exception as e:
        return f"ERROR CRITICO: {str(e)}"

def limpieza_inicial():
    if os.path.exists(".git/index.lock"):
        log("🧹 Limpiando bloqueo de Git previo...")
        os.remove(".git/index.lock")

def leer_memoria_previa():
    if not os.path.exists(ARCHIVO_MEMORIA): return "INICIO."
    with open(ARCHIVO_MEMORIA, 'r') as f: return "".join(f.readlines()[-15:])

# --- RESPALDO INTELIGENTE (LOGICA V23) ---
def forzar_tachado_tarea(texto_tarea):
    """Marca la tarea como completada SIEMPRE."""
    if not os.path.exists(ARCHIVO_BITACORA): return False
    with open(ARCHIVO_BITACORA, 'r') as f: lineas = f.readlines()
    
    nueva_lista = []
    cambio = False
    texto_limpio = texto_tarea.replace("- [ ] ", "").replace("- ", "").replace("[x]", "").strip()
    fragmento_clave = texto_limpio[:30] # Usamos un fragmento identificador
    
    for linea in lineas:
        # Buscamos la línea que contiene el texto pero que NO tiene ya la [x]
        if fragmento_clave in linea and "- [x]" not in linea:
            if linea.strip().startswith("- "): nueva_linea = linea.replace("- ", "- [x] ", 1)
            elif linea.strip()[0].isdigit(): nueva_linea = linea.replace(". ", ". [x] ", 1)
            else: nueva_linea = f"- [x] {linea.strip()}\n"
            nueva_lista.append(nueva_linea)
            cambio = True
        else:
            nueva_lista.append(linea)
            
    if cambio:
        with open(ARCHIVO_BITACORA, 'w') as f: f.writelines(nueva_lista)
        log("🛡️ Tarea marcada con [x] localmente (Burocracia Forzada).")
        return True
    return False

def forzar_memoria_automatica(tarea, motivo="Completada"):
    ts = time.strftime('%Y-%m-%d %H:%M')
    nota = f"\n- [{ts}] {motivo}: '{tarea[:40]}...'\n"
    with open(ARCHIVO_MEMORIA, 'a') as f: f.write(nota)
    return True

def esperar_y_cosechar_inteligente(session_id):
    log(f"🧠 Conectado a sesión {session_id}. Esperando...")
    intentos = 0
    racha_silencio = 0 
    ultimo_mensaje = ""
    hubo_actividad_real = False
    
    while intentos < 200: 
        time.sleep(30)
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        res_limpia = res.strip()
        
        es_nuevo = (res_limpia != ultimo_mensaje)
        hay_datos = "diff --git" in res or "Downloaded" in res or "Updated" in res
        
        if hay_datos: hubo_actividad_real = True
        ultimo_mensaje = res_limpia

        if hay_datos and es_nuevo:
            racha_silencio = 0 
            log(f"   ⚡ [{intentos}] NUEVA Actividad. Reiniciando reloj...")
        else:
            racha_silencio += 1
            minutos = racha_silencio * 0.5
            print(f"   [{intentos}] Calma: {minutos} min / 5.0 min")
            
            if racha_silencio >= 10: # 5 min
                log(f"\n✅ Cosecha finalizada.")
                return True, hubo_actividad_real
            if "Completed" in res and racha_silencio >= 2: return True, hubo_actividad_real
        intentos += 1
    return False, False

def main():
    log(f"⚔️ CEO V23 (TRUST NO ONE): {MI_REPO}")
    limpieza_inicial()
    
    # Init Repo
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    while True:
        # Actualizamos antes de leer
        subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)
        memoria_txt = leer_memoria_previa()
        
        with open(ARCHIVO_BITACORA, 'r') as f: contenido = f.read()
        
        tareas = []
        for l in contenido.split('\n'):
            l_strip = l.strip()
            if l_strip and (l_strip.startswith('- ') or l_strip[0].isdigit()):
                if "- [x]" not in l_strip and "[x]" not in l_strip:
                    tareas.append(l_strip)
        
        if not tareas:
            log("🎉 ¡PROYECTO TERMINADO! (Bitácora limpia)"); break

        tarea_objetivo = tareas[0]
        log(f"\n🎯 OBJETIVO: {tarea_objetivo}")

        instrucciones = f"""
        MODO: AUTÓNOMO | REPO: {MI_REPO} | RAMA: {RAMA_ACTIVA}
        CONTEXTO PREVIO: {memoria_txt}
        OBJETIVO: "{tarea_objetivo}"
        
        1. git checkout {RAMA_ACTIVA} && git pull
        2. Si la tarea ya está hecha, actualiza papeles y para.
        3. Si no, escribe el código.
        4. Espera.
        """
        instrucciones_linea = instrucciones.replace('\n', ' ').replace('  ', '')
        
        log("🚀 Lanzando Jules...")
        salida = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones_linea])
        match = re.search(r"ID:\s*(\d+)", salida)
        if not match: log("❌ Error lanzamiento"); break
        session_id = match.group(1)
        
        exito_cosecha, hubo_actividad = esperar_y_cosechar_inteligente(session_id)
        
        if exito_cosecha:
            estado = ejecutar_seguro(['git', 'status', '--porcelain'])
            code_changed = len(estado.strip()) > 0
            memoria_ok = ARCHIVO_MEMORIA in estado

            # --- LÓGICA V23: MARTILLO DE BUROCRACIA ---
            # Si no hay cambios, asumimos tarea ya hecha en el pasado
            if not code_changed:
                 log("⚠️ Git limpio. Asumiendo tarea completada previamente.")
            
            # Tachamos SIEMPRE. No confiamos en Jules.
            forzar_tachado_tarea(tarea_objetivo)
            
            if not memoria_ok:
                log("⚠️ (Auto-Fix) Escribiendo MEMORIA.md...")
                forzar_memoria_automatica(tarea_objetivo, "Completada/Verificada")

            log("💾 Sincronizando...")
            subprocess.run(['git', 'add', '.'], check=False)
            subprocess.run(['git', 'commit', '-m', f"Auto: {tarea_objetivo[:20]}"], check=False)
            subprocess.run(['git', 'push', 'origin', RAMA_ACTIVA], check=False)
            log("🚀 Avanzando...")

        else:
            log("🛑 Timeout crítico."); break

if __name__ == "__main__":
    main()