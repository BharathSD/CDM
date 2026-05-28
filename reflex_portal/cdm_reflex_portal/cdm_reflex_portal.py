from __future__ import annotations

import reflex as rx
from sqlalchemy import or_

from .database import Company, SessionLocal, User, init_db, verify_password

init_db()


class PortalState(rx.State):
    is_authenticated: bool = False
    username: str = ""
    password: str = ""
    current_user: str = ""
    role: str = ""
    error_message: str = ""
    search_query: str = ""
    companies: list[dict] = []

    def handle_username_change(self, value: str):
        self.username = value

    def handle_password_change(self, value: str):
        self.password = value

    def handle_search_input(self, value: str):
        self.search_query = value

    def handle_login(self):
        with SessionLocal() as session:
            user = session.query(User).filter(User.username == self.username.strip()).first()
            if not user or not verify_password(self.password, user.password_hash):
                self.error_message = "Invalid username or password"
                return

            self.is_authenticated = True
            self.current_user = user.username
            self.role = user.role
            self.error_message = ""
            self.password = ""
            self.load_companies()

    def handle_logout(self):
        self.is_authenticated = False
        self.current_user = ""
        self.role = ""
        self.username = ""
        self.password = ""
        self.error_message = ""
        self.companies = []
        self.search_query = ""

    def load_companies(self):
        with SessionLocal() as session:
            query = session.query(Company)
            if self.search_query.strip():
                term = f"%{self.search_query.strip()}%"
                query = query.filter(or_(Company.cin.ilike(term), Company.name.ilike(term)))

            rows = query.order_by(Company.id.desc()).all()
            self.companies = [
                {
                    "id": str(item.id),
                    "cin": item.cin,
                    "name": item.name,
                    "type": item.company_type,
                    "class": item.company_class,
                    "status": item.status,
                    "city": item.city or "-",
                    "state": item.state or "-",
                }
                for item in rows
            ]


def login_page() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.vstack(
                rx.heading(
                    "Welcome to CDM Portal",
                    size="7",
                    color="white",
                    weight="bold",
                ),
                rx.text(
                    "Professional Income Tax Services Management",
                    size="4",
                    color="rgba(255,255,255,0.9)",
                    weight="medium",
                ),
                spacing="3",
            ),
            rx.vstack(
                rx.hstack(
                    rx.icon("check-circle", size=24, color="white"),
                    rx.text("Streamlined company registry", color="rgba(255,255,255,0.9)", size="3"),
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("check-circle", size=24, color="white"),
                    rx.text("Secure access control", color="rgba(255,255,255,0.9)", size="3"),
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("check-circle", size=24, color="white"),
                    rx.text("Real-time information tracking", color="rgba(255,255,255,0.9)", size="3"),
                    spacing="2",
                ),
                spacing="3",
                margin_top="3rem",
            ),
            spacing="6",
            padding="4rem 3rem",
            width="50%",
            height="100vh",
            justify="center",
            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        ),
        rx.vstack(
            rx.vstack(
                rx.heading("Sign In", size="6", color="#1a1a1a", weight="bold"),
                rx.text("Enter credentials to access", size="3", color="#666"),
                spacing="2",
                margin_bottom="2rem",
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Username", size="2", weight="bold", color="#333"),
                    rx.input(
                        placeholder="admin",
                        value=PortalState.username,
                        on_change=PortalState.handle_username_change,
                        width="100%",
                        padding="0.875rem 1rem",
                        border_radius="0.625rem",
                        border="2px solid #e0e0e0",
                        background="white",
                        font_size="1rem",
                        color="#1a1a1a",
                        font_weight="500",
                        _focus={"border_color": "#667eea", "box_shadow": "0 0 0 4px rgba(102,126,234,0.1)"},
                        _placeholder={"color": "#999"},
                    ),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Password", size="2", weight="bold", color="#333"),
                    rx.input(
                        placeholder="••••••••",
                        type="password",
                        value=PortalState.password,
                        on_change=PortalState.handle_password_change,
                        width="100%",
                        padding="0.875rem 1rem",
                        border_radius="0.625rem",
                        border="2px solid #e0e0e0",
                        background="white",
                        font_size="1rem",
                        color="#1a1a1a",
                        font_weight="500",
                        _focus={"border_color": "#667eea", "box_shadow": "0 0 0 4px rgba(102,126,234,0.1)"},
                        _placeholder={"color": "#999"},
                    ),
                    spacing="1",
                ),
                spacing="4",
                width="100%",
            ),
            rx.cond(
                PortalState.error_message != "",
                rx.box(
                    rx.hstack(
                        rx.icon("alert-circle", size=20, color="#dc2626"),
                        rx.text(PortalState.error_message, size="2", color="#dc2626"),
                        spacing="2",
                    ),
                    padding="1rem",
                    border_radius="0.625rem",
                    background="#fee2e2",
                    border_left="4px solid #dc2626",
                ),
            ),
            rx.button(
                rx.text("Sign In", size="4", weight="bold"),
                on_click=PortalState.handle_login,
                width="50%",
                align_self="left",
                padding="1rem",
                background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color="white",
                border_radius="0.625rem",
                font_weight="600",
                _hover={"box_shadow": "0 12px 24px rgba(102,126,234,0.3)", "transform": "translateY(-2px)"},
                box_shadow="0 4px 16px rgba(102,126,234,0.2)",
                transition="all 0.3s",
            ),
            spacing="5",
            padding="3rem 1.25rem",
            width="50%",
            height="100vh",
            justify="center",
            background="white",
        ),
        spacing="0",
        width="100%",
        height="100vh",
    )


def companies_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("CIN", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Company Name", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Type", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Class", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Status", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("City", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("State", font_weight="700", color="white", font_size="0.95rem"),
            ),
            background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
            padding="1rem",
        ),
        rx.table.body(
            rx.foreach(
                PortalState.companies,
                lambda item: rx.table.row(
                    rx.table.cell(rx.text(item["cin"], font_weight="600", color="#1a1a1a", size="3")),
                    rx.table.cell(rx.text(item["name"], font_weight="500", color="#333", size="3")),
                    rx.table.cell(rx.badge(item["type"], variant="outline", color_scheme="cyan")),
                    rx.table.cell(rx.badge(item["class"], variant="outline", color_scheme="indigo")),
                    rx.table.cell(
                        rx.cond(
                            item["status"] == "active",
                            rx.badge("✓ Active", color_scheme="green", variant="surface"),
                            rx.badge("○ Inactive", color_scheme="gray", variant="surface"),
                        )
                    ),
                    rx.table.cell(rx.text(item["city"], color="#555", size="2")),
                    rx.table.cell(rx.text(item["state"], color="#555", size="2")),
                    _hover={"background": "rgba(102,126,234,0.04)"},
                    border_bottom="1px solid #f0f0f0",
                    padding="1rem",
                ),
            )
        ),
        width="100%",
        size="3",
    )


def dashboard_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Premium Header
            rx.box(
                rx.hstack(
                    rx.hstack(
                        rx.icon("building-2", size=28, color="white"),
                        rx.vstack(
                            rx.heading("CDM Portal", size="6", color="white", weight="bold"),
                            rx.text("Company Management System", size="2", color="rgba(255,255,255,0.8)"),
                            spacing="0",
                        ),
                        spacing="3",
                        align_items="center",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.icon("user", size=18, color="white"),
                        rx.text(PortalState.current_user, size="2", color="white", weight="bold"),
                        rx.divider(orientation="vertical", margin_x="1rem"),
                        rx.badge(PortalState.role, color_scheme="amber", variant="solid", size="2"),
                        rx.button(
                            rx.hstack(
                                rx.icon("log-out", size=16),
                                rx.text("Logout"),
                                spacing="2",
                            ),
                            on_click=PortalState.handle_logout,
                            variant="outline",
                            color_scheme="red",
                            size="2",
                        ),
                        spacing="3",
                        align_items="center",
                    ),
                    width="100%",
                    padding="1.5rem 2rem",
                    align_items="center",
                ),
                background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                width="100%",
                box_shadow="0 4px 12px rgba(0,0,0,0.1)",
            ),
            # Main Content Area
            rx.vstack(
                # Search Section
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("search", size=20, color="#667eea"),
                            rx.vstack(
                                rx.text("Quick Search", size="2", weight="bold", color="#333"),
                                rx.text("Find companies by CIN or name", size="1", color="#999"),
                                spacing="1",
                            ),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.input(
                                placeholder="Enter CIN or company name...",
                                value=PortalState.search_query,
                                on_change=PortalState.handle_search_input,
                                width="100%",
                                padding="0.875rem 1rem",
                                border_radius="0.625rem",
                                border="2px solid #e0e0e0",
                                background="white",
                                font_size="1rem",
                                color="#1a1a1a",
                                font_weight="500",
                                _focus={"border_color": "#667eea", "box_shadow": "0 0 0 4px rgba(102,126,234,0.1)"},
                                _placeholder={"color": "#999"},
                            ),
                            rx.button(
                                rx.hstack(
                                    rx.icon("search", size=16),
                                    rx.text("Search"),
                                    spacing="2",
                                ),
                                on_click=PortalState.load_companies,
                                background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                color="white",
                                size="2",
                                _hover={"box_shadow": "0 8px 16px rgba(102,126,234,0.3)"},
                            ),
                            width="100%",
                            spacing="3",
                            align_items="center",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                    padding="1.5rem",
                    background="white",
                    border_radius="0.75rem",
                    box_shadow="0 2px 12px rgba(0,0,0,0.06)",
                ),
                # Error Message
                rx.cond(
                    PortalState.error_message != "",
                    rx.box(
                        rx.hstack(
                            rx.icon("alert-circle", size=20, color="#dc2626"),
                            rx.text(PortalState.error_message, size="2", color="#dc2626", weight="medium"),
                            spacing="2",
                            width="100%",
                        ),
                        padding="1rem",
                        border_radius="0.625rem",
                        background="#fee2e2",
                        border_left="4px solid #dc2626",
                        width="100%",
                    ),
                ),
                # Companies Table
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("database", size=22, color="#667eea"),
                            rx.vstack(
                                rx.heading("Company Registry", size="5", color="#1a1a1a"),
                                rx.text(f"{PortalState.companies.length()} companies", size="1", color="#999"),
                                spacing="1",
                            ),
                            width="100%",
                            align_items="flex-start",
                        ),
                        companies_table(),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                    padding="2rem",
                    background="white",
                    border_radius="0.75rem",
                    box_shadow="0 4px 16px rgba(0,0,0,0.08)",
                ),
                spacing="5",
                padding="2rem",
                width="100%",
            ),
            spacing="0",
            width="100%",
            height="100vh",
            on_mount=PortalState.load_companies,
        ),
        background="#f5f7fa",
        width="100%",
        padding="0",
    )


def index() -> rx.Component:
    return rx.cond(PortalState.is_authenticated, dashboard_page(), login_page())


app = rx.App()
app.add_page(index, title="CDM Portal")

