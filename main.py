from playwright.sync_api import Page, sync_playwright
import sys
import json

BASE_URL = "https://gobierno.ingenieriainformatica.uniovi.es/grado/gd/?y=25-26&t=s2" 
# To change year you must change 'y' parameter in the URL
# 't' parameter is for term: s1 = first term, s2 = second term

def get_element_by_uo(page: Page, uo_value: str):
    """
    Retrieve a web element using a custom 'uo' attribute.

    Args:
        page (Page): The Playwright page object.
        uo_value (str): The value of the 'uo' attribute to search for.

    Returns:
        ElementHandle: The located web element.
    """
    page.goto(BASE_URL)
    element = page.locator(f'a:has-text("{uo_value}")').first
    href = element.get_attribute("href")
    page.goto(href)
    return page

def getListClass(page: Page):
    """
    Extract a list of class names from the page.

    Args:
        page (Page): The Playwright page object.

    Returns:
        list: A list of class names.
    """
    class_elements = page.locator('h1 + p')
    class_elements = class_elements.all_text_contents()[0].split(": ")[1]
    class_list = class_elements.split("; ")
    return class_list


if __name__ == "__main__":    
    if len(sys.argv) >= 2:
        uo = sys.argv[1].capitalize()
    else:
        # Modo interactivo
        print("Ingresa el valor del UO:")
        uo = input().strip().capitalize()
        
        if not uo:
            print(json.dumps({"error": "Debes proporcionar un valor válido para UO"}))
            sys.exit(1)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page = get_element_by_uo(page, uo)
            class_list = getListClass(page)
            
            result = {
                "success": True,
                "uo": uo,
                "classes": class_list
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            browser.close()
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)