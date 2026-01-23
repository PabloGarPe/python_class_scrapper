"""Tests para la integración de ScrapperManager y MathService."""
import pytest
import pytest_asyncio
from pathlib import Path
from src.managers.scrapper_manager import ScrapperManager
from src.services.math_service import MathService


@pytest_asyncio.fixture
async def scrapper_manager():
    """Fixture que proporciona un ScrapperManager inicializado."""
    manager = ScrapperManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
def math_service(scrapper_manager):
    """Fixture que proporciona un MathService con ScrapperManager."""
    return MathService(scrapper_manager)


@pytest.mark.asyncio
async def test_scrapper_manager_initialization():
    """Verifica que el ScrapperManager se inicializa correctamente."""
    manager = ScrapperManager()
    await manager.initialize()
    
    try:
        assert manager.browser is not None, "El navegador debe estar inicializado"
        assert manager.context is not None, "El contexto debe estar inicializado"
        assert manager.temp_dir is not None, "El directorio temporal debe existir"
        assert Path(manager.temp_dir).exists(), "El directorio temporal debe existir en el sistema"
    finally:
        await manager.cleanup()


@pytest.mark.asyncio
async def test_create_page(scrapper_manager):
    """Verifica que se puede crear una página."""
    page = await scrapper_manager.create_page()
    
    assert page is not None, "Debe crear una página"
    await page.close()


@pytest.mark.asyncio
async def test_math_service_creation(math_service):
    """Verifica que MathService se crea correctamente con ScrapperManager."""
    assert math_service.scrapper_manager is not None
    assert math_service.site_url is not None
    assert "sharepoint.com" in math_service.site_url


@pytest.mark.asyncio
async def test_scrape_and_process_integration(math_service):
    """Prueba de integración completa (requiere UO real)."""
    test_uo = "uo301887"
    
    result = await math_service.scrape_and_process(test_uo)
    
    assert "success" in result
    assert "uo" in result
    assert "classes" in result
    assert isinstance(result["classes"], list)


@pytest.mark.asyncio
async def test_context_manager_page(scrapper_manager):
    """Verifica que el context manager de página funciona correctamente."""
    async with scrapper_manager.get_page() as page:
        assert page is not None
        # La página se cierra automáticamente al salir del contexto


@pytest.mark.asyncio
async def test_temp_directory_cleanup(scrapper_manager):
    """Verifica que el directorio temporal se limpia correctamente."""
    temp_dir = scrapper_manager.temp_dir
    assert Path(temp_dir).exists()
    
    await scrapper_manager.cleanup()
    
    # El directorio temporal debería ser eliminado
    assert not Path(temp_dir).exists()
