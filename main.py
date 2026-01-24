"""
Main script to coordinate InfoService and MathService scrapers.
Retrieves class schedules from both sources and combines the results.
"""
import asyncio
import sys
import json

from src.managers.scrapper_manager import ScrapperManager
from src.services.info_service import InfoService
from src.services.math_service import MathService


async def scrape_all(uo_value: str) -> dict:
    """
    Coordinate both scrapers to get complete class information.
    
    Args:
        uo_value: The UO identifier (e.g., "Uo301887" or "301887")
    
    Returns:
        dict: Combined results from both services
    """
    # Initialize scrapper manager
    scrapper_manager = ScrapperManager()
    await scrapper_manager.initialize()
    
    try:
        # Create service instances
        info_service = InfoService(scrapper_manager)
        math_service = MathService(scrapper_manager)
        
        # Normalize UO format
        uo_formatted = uo_value if uo_value.lower().startswith("uo") else f"uo{uo_value}"
        
        # Try InfoService (gobierno.ingenieriainformatica)
        info_result = await info_service.scrape_and_process(uo_formatted)
        
        # Try MathService (SharePoint) in parallel
        math_result = await math_service.scrape_and_process(uo_formatted)
        
        # Combine results
        all_classes = []
        success = False
        
        if info_result.get("success"):
            all_classes.extend(info_result.get("classes", []))
            success = True
        
        if math_result.get("success"):
            all_classes.extend(math_result.get("classes", []))
            success = True
        
        # Remove duplicates while preserving order
        seen = set()
        unique_classes = []
        for cls in all_classes:
            if cls not in seen:
                seen.add(cls)
                unique_classes.append(cls)
        
        result = {
            "success": success,
            "uo": uo_formatted,
            "classes": unique_classes,
            "sources": {
                "gobierno": info_result.get("success", False),
                "sharepoint": math_result.get("success", False)
            }
        }
        
        return result
        
    finally:
        await scrapper_manager.cleanup()


async def main_async():
    """Main async function."""
    # Get UO from command line or interactive input
    if len(sys.argv) >= 2:
        uo = sys.argv[1].strip()
    else:
        # Interactive mode
        print("Ingresa el valor del UO:", file=sys.stderr)
        uo = input().strip()
        
        if not uo:
            result = {
                "success": False,
                "error": "Debes proporcionar un valor válido para UO"
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
    
    # Normalize UO format
    if not uo.lower().startswith("uo"):
        uo = f"Uo{uo}"
    else:
        # Capitalize first letters
        uo = uo[:2].capitalize() + uo[2:]
    
    try:
        # Run the scraper
        result = await scrape_all(uo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if not result["success"]:
            sys.exit(1)
            
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main_async())