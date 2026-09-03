import getpass
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import subprocess
import yaml

def main():
    print("="*60)
    print("🚀 ASISTENTE AUTOMÁTICO DE CONFIGURACIÓN DE BASE DE DATOS")
    print("="*60)
    print("\nEste script conectará con tu PostgreSQL local, creará la base de datos,")
    print("construirá las tablas, generará los datos de prueba y actualizará tu configuración.\n")
    
    password = getpass.getpass("🔑 Ingresa la contraseña de tu usuario 'postgres' local (no se mostrará): ")
    
    try:
        # 1. Conectar a PostgreSQL (BD por defecto)
        print("\n[1/5] Conectando a PostgreSQL...")
        conn = psycopg2.connect(dbname="postgres", user="postgres", password=password, host="localhost")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # 2. Crear BD
        print("[2/5] Verificando existencia de la base de datos...")
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'predictive_maintenance_db'")
        exists = cur.fetchone()
        if not exists:
            print("      🛠️ Creando base de datos 'predictive_maintenance_db'...")
            cur.execute("CREATE DATABASE predictive_maintenance_db;")
        else:
            print("      ⚠️ La base de datos ya existe. Reutilizando...")
            
        cur.close()
        conn.close()
        
        # 3. Actualizar config.yaml
        print("[3/5] Actualizando tu archivo config.yaml con la contraseña...")
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            config['database']['password'] = password
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f)
        
        # 4. Conectar a la nueva BD y ejecutar tablas
        print("[4/5] Creando el esquema de tablas (schema.sql)...")
        conn = psycopg2.connect(dbname="predictive_maintenance_db", user="postgres", password=password, host="localhost")
        cur = conn.cursor()
        
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            cur.execute(f.read())
            
        # 5. Generar e insertar datos
        print("[5/5] Generando e insertando miles de datos sintéticos...")
        print("      ⏳ (Ejecutando database/generate_sql.py...)")
        
        # Activar el entorno virtual para este subproceso si es necesario, o usar el ejecutable actual
        import sys
        subprocess.run([sys.executable, "database/generate_sql.py"], check=True)
        
        print("      💾 Insertando los datos en las tablas (esto puede tardar unos segundos)...")
        with open('database/seed_data.sql', 'r', encoding='utf-8') as f:
            cur.execute(f.read())
            
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n" + "="*60)
        print("🎉 ¡TODO LISTO! La base de datos está instalada y conectada.")
        print("="*60)
        print("Siguientes pasos:")
        print("1. Ejecutar las fases de IA (Fase 1 a 5).")
        print("2. Iniciar la aplicación web con: streamlit run app/main.py")
        
    except psycopg2.OperationalError:
        print("\n❌ Error de Conexión: La contraseña es incorrecta o PostgreSQL no está encendido en tu computadora.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
