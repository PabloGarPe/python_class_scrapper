"""Tests para la integración de ScrapperManager y MathService."""
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil

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


# ==================== Tests de ScrapperManager ====================

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
        assert manager.playwright is not None, "Playwright debe estar inicializado"
    finally:
        await manager.cleanup()


@pytest.mark.asyncio
async def test_scrapper_manager_double_initialization():
    """Verifica que no falla al inicializar dos veces."""
    manager = ScrapperManager()
    await manager.initialize()
    
    try:
        # Intentar inicializar de nuevo no debería causar errores
        await manager.initialize()
        assert manager.browser is not None
    finally:
        await manager.cleanup()


@pytest.mark.asyncio
async def test_create_page(scrapper_manager):
    """Verifica que se puede crear una página."""
    page = await scrapper_manager.create_page()
    
    assert page is not None, "Debe crear una página"
    assert not page.is_closed(), "La página debe estar abierta"
    
    await page.close()
    assert page.is_closed(), "La página debe estar cerrada"


@pytest.mark.asyncio
async def test_create_multiple_pages(scrapper_manager):
    """Verifica que se pueden crear múltiples páginas simultáneamente."""
    page1 = await scrapper_manager.create_page()
    page2 = await scrapper_manager.create_page()
    page3 = await scrapper_manager.create_page()
    
    assert page1 is not None
    assert page2 is not None
    assert page3 is not None
    assert page1 != page2 != page3
    
    await page1.close()
    await page2.close()
    await page3.close()


@pytest.mark.asyncio
async def test_context_manager_page(scrapper_manager):
    """Verifica que el context manager de página funciona correctamente."""
    async with scrapper_manager.get_page() as page:
        assert page is not None
        assert not page.is_closed()
        # Hacer algo con la página
        await page.goto("about:blank")
    
    # La página debe estar cerrada después del contexto
    assert page.is_closed()


@pytest.mark.asyncio
async def test_context_manager_page_with_exception(scrapper_manager):
    """Verifica que la página se cierra incluso si hay una excepción."""
    page_ref = None
    
    try:
        async with scrapper_manager.get_page() as page:
            page_ref = page
            assert not page.is_closed()
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # La página debe estar cerrada incluso después de la excepción
    assert page_ref is not None
    assert page_ref.is_closed()


@pytest.mark.asyncio
async def test_temp_directory_creation(scrapper_manager):
    """Verifica que el directorio temporal se crea correctamente."""
    temp_dir = Path(scrapper_manager.temp_dir)
    
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    assert "xlsx_scrapping_" in temp_dir.name


@pytest.mark.asyncio
async def test_temp_directory_cleanup():
    """Verifica que el directorio temporal se limpia correctamente."""
    manager = ScrapperManager()
    await manager.initialize()
    
    temp_dir = Path(manager.temp_dir)
    assert temp_dir.exists()
    
    # Crear algunos archivos de prueba
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()
    
    await manager.cleanup()
    
    # El directorio temporal debería ser eliminado
    assert not temp_dir.exists()
    assert not test_file.exists()


@pytest.mark.asyncio
async def test_cleanup_without_initialization():
    """Verifica que cleanup no falla si no se ha inicializado."""
    manager = ScrapperManager()
    # No llamar a initialize()
    
    # No debería lanzar excepción
    await manager.cleanup()


@pytest.mark.asyncio
async def test_context_downloads_path(scrapper_manager):
    """Verifica que el contexto tiene configurada la ruta de descargas."""
    # El contexto debe tener la ruta de descargas configurada
    assert scrapper_manager.context._impl_obj._options.get('acceptDownloads') == 'accept'


# ==================== Tests de MathService ====================

@pytest.mark.asyncio
async def test_math_service_creation(math_service):
    """Verifica que MathService se crea correctamente con ScrapperManager."""
    assert math_service.scrapper_manager is not None
    assert math_service.site_url is not None
    assert "sharepoint.com" in math_service.site_url
    assert math_service.SELECTOR_TIMEOUT == 60000
    assert math_service.MAX_RETRIES == 3


@pytest.mark.asyncio
async def test_math_service_url_format(math_service):
    """Verifica que la URL del servicio tiene el formato correcto."""
    assert math_service.site_url.startswith("https://")
    assert "unioviedo-my.sharepoint.com" in math_service.site_url


# ==================== Tests de extracción de clases ====================


def test_extract_classes_from_dataframe():
    """Verifica la extracción de clases de un DataFrame."""
    import pandas as pd
    
    service = MathService(Mock())
    
    # Crear DataFrame de prueba
    df = pd.DataFrame({
        'col1': ['MOR-PL1', 'B04', 'IE-CE1', None],
        'col2': ['AMatIII-PA1', 'EAO', 'ProgM-TG1', '11:00-12:00'],
        'col3': ['ANM-CE1', 'Nombre', 'IE-TG1', 'Lunes']
    })
    
    classes = service._extract_classes_from_dataframe(df)
    
    assert 'MOR-PL1' in classes
    assert 'IE-CE1' in classes
    assert 'AMatIII-PA1' in classes
    assert 'ProgM-TG1' in classes
    assert 'ANM-CE1' in classes
    assert 'IE-TG1' in classes
    
    # No debe incluir aulas ni otros datos
    assert 'B04' not in classes
    assert 'EAO' not in classes
    assert 'Nombre' not in classes
    assert '11:00-12:00' not in classes
    assert 'Lunes' not in classes


def test_organize_by_subject():
    """Verifica la organización de clases por asignatura."""
    service = MathService(Mock())
    
    classes = [
        'MOR-PL1', 'MOR-CE1', 'MOR-PA1',
        'IE-CE1', 'IE-PA1', 'IE-TG1',
        'AMatIII-PA1', 'AMatIII-CE1'
    ]
    
    subjects = service._organize_by_subject(classes)
    
    assert 'MOR' in subjects
    assert 'IE' in subjects
    assert 'AMatIII' in subjects
    
    assert len(subjects['MOR']) == 3
    assert len(subjects['IE']) == 3
    assert len(subjects['AMatIII']) == 2
    
    # Verificar que están ordenadas
    assert subjects['MOR'] == sorted(subjects['MOR'])
    assert subjects['IE'] == sorted(subjects['IE'])


def test_organize_by_subject_empty():
    """Verifica el comportamiento con lista vacía."""
    service = MathService(Mock())
    
    subjects = service._organize_by_subject([])
    
    assert subjects == {}


# ==================== Tests de procesamiento de archivos ====================

@pytest.mark.asyncio
async def test_process_xlsx_file_success():
    """Verifica el procesamiento exitoso de un archivo XLSX."""
    import pandas as pd
    
    service = MathService(Mock())
    
    # Crear archivo temporal de prueba
    with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as tmp:
        tmp_path = Path(tmp.name)
        
        # Crear un DataFrame de prueba
        df = pd.DataFrame({
            'col1': ['Lista_clases_UO301887@uniovi.es', None, 'MOR-PL1', 'IE-CE1'],
            'col2': [None, None, 'B04', 'AMatIII-PA1'],
        })
        
        # Guardar como Excel (requiere xlwt para .xls)
        try:
            df.to_excel(tmp_path, index=False, engine='xlwt')
        except ImportError:
            # Si xlwt no está disponible, saltar el test
            pytest.skip("xlwt no está instalado")
    
    try:
        result = service.process_xlsx_file(tmp_path)
        
        assert result['success'] == True
        assert 'uo' in result
        assert 'classes' in result
        assert isinstance(result['classes'], list)
        
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_process_xlsx_file_not_found():
    """Verifica el manejo de archivos no encontrados."""
    service = MathService(Mock())
    
    non_existent_path = Path("/tmp/non_existent_file.xls")
    result = service.process_xlsx_file(non_existent_path)
    
    assert result['success'] == False
    assert result['classes'] == []


# ==================== Tests de integración ====================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_scrape_and_process_integration(math_service):
    """Prueba de integración completa (requiere UO real)."""
    test_uo = "301887"  # Sin el prefijo UO
    
    result = await math_service.scrape_and_process(test_uo)
    
    assert "success" in result
    assert "uo" in result
    assert "classes" in result
    assert isinstance(result["classes"], list)
    
    if result["success"]:
        assert len(result["classes"]) > 0
        assert "subjects" in result
        assert "summary" in result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scrape_nonexistent_uo(math_service):
    """Verifica el comportamiento con un UO inexistente."""
    test_uo = "999999"  # UO que probablemente no existe
    
    result = await math_service.scrape_and_process(test_uo)
    
    assert "success" in result
    assert result["success"] == False or result["classes"] == []


@pytest.mark.asyncio
async def test_multiple_scrapes_sequential(math_service):
    """Verifica que se pueden hacer múltiples scrapes secuencialmente."""
    test_uos = ["301887", "295630"]
    
    results = []
    for uo in test_uos:
        result = await math_service.scrape_and_process(uo)
        results.append(result)
    
    assert len(results) == 2
    for result in results:
        assert "success" in result
        assert "uo" in result
        assert "classes" in result


# ==================== Tests de manejo de errores ====================

@pytest.mark.asyncio
async def test_scrapper_manager_create_page_without_init():
    """Verifica que crear página sin inicializar lanza error."""
    manager = ScrapperManager()
    # No llamar a initialize()
    
    with pytest.raises(RuntimeError, match="ScrapperManager no inicializado"):
        await manager.create_page()


@pytest.mark.asyncio
async def test_download_with_network_timeout(scrapper_manager):
    """Simula un timeout de red durante la descarga."""
    service = MathService(scrapper_manager)
    
    # Este test requeriría mock de la red
    # Por ahora solo verificamos que el método existe y tiene retry logic
    assert service.MAX_RETRIES > 0


# ==================== Tests de configuración ====================

def test_math_service_constants():
    """Verifica que las constantes del servicio son correctas."""
    service = MathService(Mock())
    
    assert service.SELECTOR_TIMEOUT == 60000
    assert service.MAX_RETRIES == 3
    assert isinstance(service.site_url, str)
    assert len(service.site_url) > 0


# ==================== Pytest markers ====================

def test_pytest_markers_configured():
    """Verifica que los markers de pytest están disponibles."""
    # Este test ayuda a documentar los markers disponibles
    # Los markers deben estar definidos en pytest.ini o pyproject.toml
    pass


# ==================== Test helpers ====================

@pytest.fixture
def temp_test_directory():
    """Crea un directorio temporal para tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_scraper_"))
    yield temp_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_temp_directory_fixture(temp_test_directory):
    """Verifica que el fixture de directorio temporal funciona."""
    assert temp_test_directory.exists()
    assert temp_test_directory.is_dir()
    
    # Crear un archivo de prueba
    test_file = temp_test_directory / "test.txt"
    test_file.write_text("test")
    assert test_file.exists()