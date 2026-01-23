"""Ejemplo de uso integrado de ScrapperManager y MathService en main.py."""
import asyncio
import sys
from src.managers.scrapper_manager import ScrapperManager
from src.services.math_service import MathService


async def main_async():
    """Función principal asíncrona."""
    
    if len(sys.argv) >= 2:
        uo = sys.argv[1].strip()
    else:
        print("Ingresa el valor del UO:")
        uo = input().strip()
        
        if not uo:
            print("❌ Error: Debes ingresar un UO válido")
            return
    
    # Inicializar el scrapper manager
    scrapper_manager = ScrapperManager()
    await scrapper_manager.initialize()
    
    try:
        # Crear instancia del servicio de matemáticas
        math_service = MathService(scrapper_manager)
        
        print(f"\n🔍 Buscando horarios para: {uo}")
        print("⏳ Esto puede tardar algunos minutos...\n")
        
        # Ejecutar el scraping y procesamiento
        result = await math_service.scrape_and_process(uo)
        
        # Mostrar resultados
        print("\n" + "="*50)
        print("📊 RESULTADOS")
        print("="*50)
        
        if result["success"]:
            print(f"✅ Éxito: Se encontró información para {result['uo']}")
            print(f"\n📚 Total de clases: {len(result['classes'])}")
            
            if result['classes']:
                print("\nLista de clases:")
                for i, clase in enumerate(result['classes'], 1):
                    print(f"  {i}. {clase}")
        else:
            print(f"❌ No se pudo obtener información para {result['uo']}")
            print("   Verifica que el UO sea correcto y tenga archivos disponibles.")
        
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        
    finally:
        # Limpiar recursos
        print("\n🧹 Limpiando recursos...")
        await scrapper_manager.cleanup()
        print("✅ Completado")


if __name__ == "__main__":
    asyncio.run(main_async())
