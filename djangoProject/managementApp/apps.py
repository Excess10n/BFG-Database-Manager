from django.apps import AppConfig
import logging


class ManagementappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'managementApp'

    def ready(self):
        try:
            import pypandoc
            try:
                pypandoc.get_pandoc_path()
            except OSError:
                pypandoc.download_pandoc()
        except ImportError:
            logging.warning(
                "pypandoc is not installed; report export will fail until pypandoc is installed."
            )
        except Exception as exc:
            logging.error("Failed to download pandoc at startup: %s", exc)
