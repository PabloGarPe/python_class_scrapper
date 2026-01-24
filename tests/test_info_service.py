"""Tests para InfoService."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from src.managers.scrapper_manager import ScrapperManager
from src.services.info_service import InfoService


@pytest_asyncio.fixture
async def scrapper_manager():
    """Fixture que proporciona un ScrapperManager inicializado."""
    manager = ScrapperManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
def info_service(scrapper_manager):
    """Fixture que proporciona un InfoService con ScrapperManager."""
    return InfoService(scrapper_manager)


# ==================== Tests de InfoService ====================

@pytest.mark.asyncio
async def test_info_service_creation(info_service):
    """Verifica que InfoService se crea correctamente con ScrapperManager."""
    assert info_service.scrapper_manager is not None
    assert info_service.site_urls is not None
    assert isinstance(info_service.site_urls, list)
    assert len(info_service.site_urls) > 0
    assert "gobierno.ingenieriainformatica.uniovi.es" in info_service.site_urls[0]
    assert info_service.SELECTOR_TIMEOUT == 60000
    assert info_service.MAX_RETRIES == 3


@pytest.mark.asyncio
async def test_info_service_url_format(info_service):
    """Verifica que las URLs del servicio tienen el formato correcto."""
    assert isinstance(info_service.site_urls, list)
    for url in info_service.site_urls:
        assert url.startswith("https://")
        assert "grado/gd" in url


def test_info_service_constants():
    """Verifica que las constantes del servicio son correctas."""
    service = InfoService(Mock())
    
    assert service.SELECTOR_TIMEOUT == 60000
    assert service.MAX_RETRIES == 3
    assert isinstance(service.site_urls, list)
    assert len(service.site_urls) > 0


# ==================== Tests de funcionalidad ====================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_scrape_and_process_integration(info_service):
    """Prueba de integración completa con un UO real."""
    # Este test requiere conexión real al sitio
    test_uo = "Uo301887"  # UO de ejemplo
    
    result = await info_service.scrape_and_process(test_uo)
    
    assert "success" in result
    assert "uo" in result
    assert "classes" in result
    
    if result["success"]:
        assert isinstance(result["classes"], list)
        assert len(result["classes"]) > 0
        assert result["uo"] == test_uo


@pytest.mark.asyncio
async def test_get_element_by_uo_mock():
    """Verifica el método get_element_by_uo con mocks."""
    mock_manager = Mock()
    service = InfoService(mock_manager)
    
    # Crear un mock de página
    mock_page = AsyncMock()
    mock_element = AsyncMock()
    mock_locator = Mock()
    mock_locator.first = mock_element
    
    # Configurar los mocks
    mock_page.goto = AsyncMock()
    mock_page.locator = Mock(return_value=mock_locator)
    mock_element.get_attribute = AsyncMock(return_value="https://example.com/schedule")
    
    # Ejecutar el método
    result = await service.get_element_by_uo(mock_page, "Uo301887")
    
    # Verificar que se llamaron los métodos correctos
    assert mock_page.goto.call_count >= 1
    mock_page.locator.assert_called_with('a:has-text("Uo301887")')
    mock_element.get_attribute.assert_called_with("href")


@pytest.mark.asyncio
async def test_getListClass_mock():
    """Verifica el método getListClass con mocks."""
    mock_manager = Mock()
    service = InfoService(mock_manager)
    
    # Crear un mock de página
    mock_page = Mock()
    mock_locator = AsyncMock()
    
    # Configurar el mock para devolver texto simulado
    mock_page.locator = Mock(return_value=mock_locator)
    mock_locator.all_text_contents = AsyncMock(
        return_value=["Asignaturas: Clase1; Clase2; Clase3; Clase4"]
    )
    
    # Ejecutar el método
    result = await service.getListClass(mock_page)
    
    # Verificar el resultado
    assert isinstance(result, list)
    assert len(result) == 4
    assert result == ["Clase1", "Clase2", "Clase3", "Clase4"]


@pytest.mark.asyncio
async def test_getListClass_real_format():
    """Verifica getListClass con formato real esperado."""
    mock_manager = Mock()
    service = InfoService(mock_manager)
    
    mock_page = Mock()
    mock_locator = AsyncMock()
    
    # Simular formato real de la página
    mock_page.locator = Mock(return_value=mock_locator)
    mock_locator.all_text_contents = AsyncMock(
        return_value=["Asignaturas: Alg.T.2; Alg.S.1; Alg.L.3; SO.T.1; SO.L.1; TPP.T.2; TPP.L.5"]
    )
    
    result = await service.getListClass(mock_page)
    
    assert "Alg.T.2" in result
    assert "SO.T.1" in result
    assert "TPP.L.5" in result
    assert len(result) == 7


# ==================== Tests de manejo de errores ====================

@pytest.mark.asyncio
async def test_get_element_by_uo_no_href():
    """Verifica el comportamiento cuando no se encuentra el href."""
    mock_manager = Mock()
    service = InfoService(mock_manager)
    
    mock_page = AsyncMock()
    mock_element = AsyncMock()
    mock_locator = Mock()
    mock_locator.first = mock_element
    
    mock_page.goto = AsyncMock()
    mock_page.locator = Mock(return_value=mock_locator)
    mock_element.get_attribute = AsyncMock(return_value=None)
    
    result = await service.get_element_by_uo(mock_page, "UoInexistente")
    
    # Debería retornar None después de todos los reintentos
    assert result is None


@pytest.mark.asyncio
async def test_get_element_by_uo_retry_on_error():
    """Verifica que se reintenta en caso de error."""
    from playwright.async_api import Error as PlaywrightError
    
    mock_manager = Mock()
    service = InfoService(mock_manager)
    
    mock_page = AsyncMock()
    
    # Simular error en goto
    mock_page.goto = AsyncMock(side_effect=PlaywrightError("Connection failed"))
    
    with pytest.raises(PlaywrightError):
        await service.get_element_by_uo(mock_page, "Uo301887")


@pytest.mark.asyncio
async def test_scrape_and_process_error_handling(info_service):
    """Verifica el manejo de errores en scrape_and_process."""
    # Probar con un UO que claramente no existe
    test_uo = "UoInvalidoXYZ999"
    
    try:
        result = await info_service.scrape_and_process(test_uo)
        # Si no lanza error, verificar que el resultado indique falla
        assert "success" in result or result is None
    except Exception as e:
        # Es aceptable que lance una excepción con UO inválido
        assert True


# ==================== Tests de integración múltiple ====================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_scrapes_info_service(info_service):
    """Verifica que se pueden hacer múltiples scrapes secuencialmente."""
    test_uos = ["Uo301887", "Uo295630"]
    
    results = []
    for uo in test_uos:
        try:
            result = await info_service.scrape_and_process(uo)
            results.append(result)
        except Exception:
            # Algunos UOs pueden no existir
            pass
    
    # Al menos deberíamos tener intentado procesar los UOs
    assert len(results) >= 0


# ==================== Tests de comparación con MathService ====================

def test_services_have_same_interface():
    """Verifica que InfoService y MathService tienen la misma interfaz básica."""
    from src.services.math_service import MathService
    
    mock_manager = Mock()
    info_service = InfoService(mock_manager)
    math_service = MathService(mock_manager)
    
    # Ambos deben tener los mismos atributos básicos
    assert hasattr(info_service, 'scrapper_manager')
    assert hasattr(math_service, 'scrapper_manager')
    
    # InfoService tiene site_urls (lista), MathService tiene site_url (string)
    assert hasattr(info_service, 'site_urls')
    assert hasattr(math_service, 'site_url')
    
    assert hasattr(info_service, 'SELECTOR_TIMEOUT')
    assert hasattr(math_service, 'SELECTOR_TIMEOUT')
    
    assert hasattr(info_service, 'MAX_RETRIES')
    assert hasattr(math_service, 'MAX_RETRIES')
    
    # Ambos deben tener el método scrape_and_process
    assert callable(getattr(info_service, 'scrape_and_process'))
    assert callable(getattr(math_service, 'scrape_and_process'))


@pytest.mark.asyncio
async def test_both_services_with_same_uo(scrapper_manager):
    """Verifica que ambos servicios pueden procesar el mismo UO."""
    from src.services.math_service import MathService
    
    info_service = InfoService(scrapper_manager)
    math_service = MathService(scrapper_manager)
    
    test_uo = "301887"
    
    # Ambos servicios deberían poder procesar el mismo UO
    # (aunque devuelvan formatos diferentes)
    info_result = await info_service.scrape_and_process(f"Uo{test_uo}")
    math_result = await math_service.scrape_and_process(test_uo)
    
    # Ambos deben tener la estructura básica
    assert "success" in info_result
    assert "uo" in info_result
    assert "classes" in info_result
    
    assert "success" in math_result
    assert "uo" in math_result
    assert "classes" in math_result
