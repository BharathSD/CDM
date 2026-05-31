import os

import reflex as rx
from reflex_base.plugins import SitemapPlugin
from reflex_components_radix.plugin import RadixThemesPlugin

config = rx.Config(
    app_name="cdm_reflex_portal",
    backend_port=8001,
    # When deployed to cloud, set REFLEX_API_URL to the public backend URL.
    # Falls back to localhost for local development.
    api_url=os.environ.get("REFLEX_API_URL", "http://localhost:8001"),
    disable_plugins=[SitemapPlugin],
    plugins=[RadixThemesPlugin()],
)
