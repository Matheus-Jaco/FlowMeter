from django.apps import AppConfig
import sys
import os

class FluxoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fluxo'

    def ready(self):
        import fluxo.signals  # Importa os signals
        if 'runserver' in sys.argv:
            if os.environ.get('RUN_MAIN') == 'true':
                self.limpar_fluxo_agua()

    def limpar_fluxo_agua(self):
        from .models import FluxoAgua
        from django.db import connections
        from django.db.utils import OperationalError

        try:
            num_deleted, _ = FluxoAgua.objects.all().delete()
            print(f"FluxoAgua zerado. Registros excluídos: {num_deleted}")
        except OperationalError:
            pass
