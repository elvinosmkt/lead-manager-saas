"""
Arquivo de configuração para o scraper
"""

CONFIG = {
    # Delay entre scrolls (segundos)
    "DELAY_BETWEEN_SCROLLS": 2,
    
    # Delay entre processar cada empresa (segundos)
    "DELAY_BETWEEN_BUSINESSES": 1,
    
    # Número máximo de empresas a processar (aumentado para 200)
    "MAX_BUSINESSES": 200,
    
    # Modo headless (False = mostra navegador, True = oculto)
    "HEADLESS": True,
    
    # Diretório de saída
    "OUTPUT_DIR": "resultados"
}
