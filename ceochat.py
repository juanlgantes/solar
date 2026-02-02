import subprocess
import time
import os
import re

# --- CONFIGURACIÓN ---
MI_REPO = "juanlgantes/solar"
RAMA_ACTIVA = "create-plan-md-16884671065521769136"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def ejecutar_seguro(cmd_list):
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        return res.stdout.strip() + "\n" + res.stderr.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def esperar_respuesta(session_id):
    """Espera a que Jules termine de procesar el último mensaje."""
    log(f"👂 Escuchando a sesión {session_id}...")
    intentos = 0
    silencio = 0
    ultimo_msg = ""
    
    while intentos < 100:
        time.sleep(10) # Sondeo más rápido para chat
        res = ejecutar_seguro(['jules', 'remote', 'pull', '--session', session_id])
        res_limpia = res.strip()
        
        if "diff --git" in res and res_limpia != ultimo_msg:
            silencio = 0
            ultimo_msg = res_limpia
            log("   ⚡ Jules está escribiendo código...")
        else:
            silencio += 1
            
        # Si lleva 1 minuto callado después de actividad, o dice Completed
        if "Completed" in res or silencio > 6: # ~1 min de silencio
            log("✅ Jules ha terminado su turno.")
            return True
            
        intentos += 1
    return False

def main():
    log(f"💬 CEO CHAT V1 (EXPERIMENTAL): {MI_REPO}")
    
    # 1. ¿Nueva o Existente?
    session_id = input("¿Tienes un ID de sesión activa? (Pégalo o pulsa Enter para nueva): ").strip()
    
    if not session_id:
        prompt = input("Escribe el primer prompt para Jules: ")
        cmd = ['jules', 'remote', 'new', '--repo', MI_REPO, '--session', prompt]
        salida = ejecutar_seguro(cmd)
        match = re.search(r"ID:\s*(\d+)", salida)
        if match:
            session_id = match.group(1)
            log(f"✨ Nueva sesión iniciada: {session_id}")
        else:
            log("❌ Error creando sesión."); print(salida); return
    
    # 2. Bucle de Conversación Infinita
    while True:
        # A) Esperar a que Jules haga su trabajo
        esperar_respuesta(session_id)
        
        # B) Sincronizar (Bajamos lo que hizo)
        log("💾 Bajando cambios al disco...")
        ejecutar_seguro(['git', 'pull', 'origin', RAMA_ACTIVA]) # Por si acaso
        # Hacemos commit de lo recibido
        subprocess.run(['git', 'add', '.'], check=False)
        subprocess.run(['git', 'commit', '-m', "Chat: Avance recibido"], check=False)
        
        # C) Turno del Humano
        print("\n" + "="*40)
        print("🤖 JULES ESPERA TU ORDEN (Continuación del Chat)")
        print("Escribe 'exit' para salir.")
        print("="*40)
        nuevo_mensaje = input("Tú: ")
        
        if nuevo_mensaje.lower() in ['exit', 'salir']:
            break
            
        # D) ENVIAR RESPUESTA (EL EXPERIMENTO)
        # Probamos el comando hipotético 'send'. 
        # Si falla, el script te avisará.
        log(f"🚀 Enviando a Jules...")
        
        # --- AQUÍ ESTÁ LA PRUEBA DE FUEGO ---
        # Intentamos 'send'. Si no existe, prueba cambiarlo por 'reply' o 'input'
        cmd_chat = ['jules', 'remote', 'send', '--session', session_id, nuevo_mensaje]
        
        salida = ejecutar_seguro(cmd_chat)
        
        if "Error" in salida or "unknown command" in salida:
            log("❌ EL COMANDO 'send' NO EXISTE.")
            log("PRUEBA DE FALLO:")
            print(salida)
            log("💡 Tu misión: Ejecuta 'jules remote --help' en otra terminal y dime qué comandos salen.")
            break
        else:
            log("✅ ¡Mensaje enviado! Esperando respuesta...")

if __name__ == "__main__":
    main()