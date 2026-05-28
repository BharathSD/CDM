import reflex as rx
from reflex_base.plugins import SitemapPlugin
from reflex_components_radix.plugin import RadixThemesPlugin

config = rx.Config(
    app_name="cdm_reflex_portal",
    backend_port=8001,
    api_url="http://localhost:8001",
    disable_plugins=[SitemapPlugin],
    plugins=[RadixThemesPlugin()],
)
