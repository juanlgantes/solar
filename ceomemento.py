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
        log("🧹 Limpiando bloqueo de Git previo (index.lock)...")
        os.remove(".git/index.lock")

def leer_memoria_previa():
    if not os.path.exists(ARCHIVO_MEMORIA):
        return "INICIO DEL PROYECTO. Sin memoria previa."
    with open(ARCHIVO_MEMORIA, 'r') as f:
        lineas = f.readlines()
        return "".join(lineas[-15:]) 

def esperar_y_cosechar_inteligente(session_id):
    """
    V20: Cancelación de Eco. 
    Solo reinicia el contador si la respuesta es NUEVA y DIFERENTE a la anterior.
    """
    log(f"🧠 Conectado a sesión {session_id}. Esperando actividad...")
    
    intentos = 0
    racha_silencio = 0 
    ultimo_mensaje_recibido = "" # Memoria de corto plazo para detectar ecos
    
    while intentos < 200: # 100 min max
        time.sleep(30)
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        
        # Limpieza de output para comparación
        res_limpia = res.strip()
        mensaje_corto = res_limpia.split('\n')[0][:100] 
        
        # ¿Es esto nuevo o es un eco del pasado?
        es_nuevo = (res_limpia != ultimo_mensaje_recibido)
        hay_datos = "diff --git" in res or "Downloaded" in res or "Updated" in res

        # Actualizamos la memoria de corto plazo
        ultimo_mensaje_recibido = res_limpia

        if hay_datos and es_nuevo:
            racha_silencio = 0 
            log(f"   ⚡ [{intentos}] NUEVA Actividad detectada. Reiniciando reloj...")
        
        else:
            # Si no hay datos, O si los datos son idénticos a los de hace 30s (Eco)
            racha_silencio += 1
            minutos = racha_silencio * 0.5
            
            # Mensaje de estado
            estado = "Silencio" if not hay_datos else "Eco (Datos estáticos)"
            print(f"   [{intentos}] {estado}. Zona de Calma: {minutos} min / 5.0 min")
            
            # 5 MINUTOS de estabilidad (10 ciclos)
            if racha_silencio >= 10:
                log(f"\n✅ Cosecha finalizada (Estabilidad confirmada).")
                return True
            
            # Si Jules dice explícitamente que acabó
            if "Completed" in res and racha_silencio >= 2:
                return True

        intentos += 1
    
    log("🛑 Timeout.")
    return False

def verificar_autonomia_jules():
    estado = ejecutar_seguro(['git', 'status', '--porcelain'])
    modifico_plan = ARCHIVO_BITACORA in estado
    modifico_memoria = ARCHIVO_MEMORIA in estado
    return modifico_plan, modifico_memoria

def main():
    log(f"🦉 CEO V20 (ECHO CANCELLATION): {MI_REPO}")
    limpieza_inicial()
    
    # 1. Sync
    if not os.path.exists(".git"):
        subprocess.run(['git', 'clone', '--branch', RAMA_ACTIVA, '--single-branch', f'https://github.com/{MI_REPO}', '.'], check=True)
    subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)

    # Init Memoria
    if not os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, 'w') as f:
            f.write("# BITÁCORA DE INTELIGENCIA ARTIFICIAL\n\n")
        subprocess.run(['git', 'add', ARCHIVO_MEMORIA], check=False)
        subprocess.run(['git', 'commit', '-m', "Init: Memoria"], check=False)

    while True:
        # 2. Leer Plan
        subprocess.run(['git', 'pull', 'origin', RAMA_ACTIVA], check=False)
        memoria_txt = leer_memoria_previa()
        
        with open(ARCHIVO_BITACORA, 'r') as f:
            contenido = f.read()
        
        tareas = [l.strip() for l in contenido.split('\n') 
                 if l.strip() and (l.strip().startswith('- ') or l.strip()[0].isdigit()) 
                 and not l.strip().startswith('- [x]')]
        
        if not tareas:
            log("🎉 SIN TAREAS PENDIENTES."); break

        tarea_objetivo = tareas[0]
        log(f"\n🎯 OBJETIVO: {tarea_objetivo}")
        log(f"📜 Memoria:\n{memoria_txt.strip()}\n{'-'*20}")

        # 3. Prompt
        instrucciones = f"""
        MODO: AUTÓNOMO | REPO: {MI_REPO} | RAMA: {RAMA_ACTIVA}
        CONTEXTO PREVIO (Memoria): {memoria_txt}
        
        TU MISIÓN:
        1. Ejecuta: git fetch origin {RAMA_ACTIVA} && git checkout {RAMA_ACTIVA} && git pull
        2. Analiza '{ARCHIVO_BITACORA}'. Tu objetivo es: "{tarea_objetivo}".
        3. Realiza la tarea.
        4. OBLIGATORIO: Edita '{ARCHIVO_BITACORA}' ([x]).
        5. OBLIGATORIO: Escribe en '{ARCHIVO_MEMORIA}' (resumen técnico).
        6. Espera sin hacer PR.
        """
        instrucciones_linea = instrucciones.replace('\n', ' ').replace('  ', '')
        
        log("🚀 Lanzando Jules...")
        salida = ejecutar_seguro(['jules', 'remote', 'new', '--repo', MI_REPO, '--session', instrucciones_linea])
        
        match = re.search(r"ID:\s*(\d+)", salida)
        if not match:
            log("❌ Error lanzamiento"); print(salida); break
        session_id = match.group(1)
        
        # 4. Espera Inteligente
        if esperar_y_cosechar_inteligente(session_id):
            plan_ok, memoria_ok = verificar_autonomia_jules()
            
            if plan_ok and memoria_ok:
                log("✅ AUDITORÍA PASADA.")
                log("💾 Sincronizando...")
                subprocess.run(['git', 'add', '.'], check=False)
                subprocess.run(['git', 'commit', '-m', f"IA: {tarea_objetivo[:20]}"], check=False)
                subprocess.run(['git', 'push', 'origin', RAMA_ACTIVA], check=False)
            else:
                log("⚠️ ALERTA: Jules falló en la burocracia (Plan/Memoria).")
                # IMPORTANTE: Si falla la burocracia, forzamos parada para educar a la IA
                # Si quieres que siga igual, cambia 'break' por un tachado manual.
                break 
        else:
            break

if __name__ == "__main__":
    main()