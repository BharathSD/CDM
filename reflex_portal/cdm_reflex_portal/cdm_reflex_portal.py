from __future__ import annotations

import reflex as rx
from sqlalchemy import or_

from .database import Company, SessionLocal, User, hash_password, init_db, verify_password

init_db()


class PortalState(rx.State):
    # ── Auth ──────────────────────────────────────────────────────────────────
    is_authenticated: bool = False
    username: str = ""
    password: str = ""
    current_user: str = ""
    role: str = ""
    error_message: str = ""

    # ── Companies ─────────────────────────────────────────────────────────────
    search_query: str = ""
    companies: list[dict] = []

    # ── Add-company form ──────────────────────────────────────────────────────
    show_add_form: bool = False
    is_saving: bool = False
    form_cin: str = ""
    form_name: str = ""
    form_class: str = ""
    form_category: str = ""
    form_sub_category: str = ""
    form_error: str = ""

    # ── Edit-company form ─────────────────────────────────────────────────────
    show_edit_company_form: bool = False
    edit_company_id: str = ""
    edit_form_cin: str = ""
    edit_form_name: str = ""
    edit_form_class: str = ""
    edit_form_category: str = ""
    edit_form_sub_category: str = ""
    edit_form_error: str = ""

    # ── User management (admin only) ──────────────────────────────────────────
    active_tab: str = "companies"
    users: list[dict] = []
    show_add_user_form: bool = False
    user_form_username: str = ""
    user_form_password: str = ""
    user_form_role: str = ""
    user_form_error: str = ""
    # Edit user form
    show_edit_user_form: bool = False
    edit_user_id: str = ""
    edit_user_form_username: str = ""
    edit_user_form_password: str = ""
    edit_user_form_error: str = ""

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clear_form(self) -> None:
        """Reset every company-form var to its default."""
        self.show_add_form = False
        self.is_saving = False
        self.form_cin = ""
        self.form_name = ""
        self.form_class = ""
        self.form_category = ""
        self.form_sub_category = ""
        self.form_error = ""

    def _clear_edit_company_form(self) -> None:
        """Reset every edit-company-form var to its default."""
        self.show_edit_company_form = False
        self.edit_company_id = ""
        self.edit_form_cin = ""
        self.edit_form_name = ""
        self.edit_form_class = ""
        self.edit_form_category = ""
        self.edit_form_sub_category = ""
        self.edit_form_error = ""

    def _clear_user_form(self) -> None:
        """Reset every user-form var to its default."""
        self.show_add_user_form = False
        self.user_form_username = ""
        self.user_form_password = ""
        self.user_form_role = ""
        self.user_form_error = ""

    def _clear_edit_user_form(self) -> None:
        """Reset every edit-user-form var to its default."""
        self.show_edit_user_form = False
        self.edit_user_id = ""
        self.edit_user_form_username = ""
        self.edit_user_form_password = ""
        self.edit_user_form_error = ""

    # ── Page lifecycle ────────────────────────────────────────────────────────

    def on_page_load(self):
        """Registered via on_load so it runs on every page load AND on every
        WebSocket reconnect (Reflex re-fires on_load_internal after reconnect).
        Guarantees transient form state is never restored from stale disk state."""
        self._clear_form()
        self._clear_edit_company_form()
        self._clear_user_form()
        self._clear_edit_user_form()
        if self.is_authenticated:
            self.load_companies()
            if self.active_tab == "admin" and self.role == "ADMIN":
                self.load_users()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def handle_username_change(self, value: str):
        self.username = value

    def handle_password_change(self, value: str):
        self.password = value

    def handle_key_down(self, key: str):
        if key == "Enter":
            return PortalState.handle_login

    def handle_login(self):
        with SessionLocal() as session:
            user = (
                session.query(User)
                .filter(User.username == self.username.strip())
                .first()
            )
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
        self._clear_form()
        self._clear_user_form()
        self.active_tab = "companies"
        self.is_authenticated = False
        self.current_user = ""
        self.role = ""
        self.username = ""
        self.password = ""
        self.error_message = ""
        self.companies = []
        self.users = []
        self.search_query = ""
        self._clear_edit_company_form()
        self._clear_edit_user_form()

    def clear_error(self):
        self.error_message = ""

    # ── Companies ─────────────────────────────────────────────────────────────

    def handle_search_input(self, value: str):
        self.search_query = value

    def load_companies(self):
        with SessionLocal() as session:
            query = session.query(Company)
            if self.search_query.strip():
                term = f"%{self.search_query.strip()}%"
                query = query.filter(
                    or_(Company.cin.ilike(term), Company.name.ilike(term))
                )
            rows = query.order_by(Company.id.desc()).all()
            self.companies = [
                {
                    "id": str(r.id),
                    "cin": r.cin,
                    "name": r.name,
                    "class": r.company_class or "-",
                    "category": r.company_type or "-",
                    "sub_category": r.sub_category or "-",
                }
                for r in rows
            ]

    def confirm_delete(self, company_id: str):
        if self.role not in ("ADMIN", "EDITOR"):
            self.error_message = "You do not have permission to delete companies."
            return
        try:
            cid = int(company_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid company ID '{company_id}'."
            return
        with SessionLocal() as session:
            company = session.query(Company).filter(Company.id == cid).first()
            if company:
                session.delete(company)
                session.commit()
        self.load_companies()

    # ── Add-company form handlers ─────────────────────────────────────────────

    def handle_form_cin_change(self, value: str):
        if self.show_add_form:
            self.form_cin = value

    def handle_form_name_change(self, value: str):
        if self.show_add_form:
            self.form_name = value

    def handle_form_class_change(self, value: str):
        if self.show_add_form:
            self.form_class = value

    def handle_form_category_change(self, value: str):
        if self.show_add_form:
            self.form_category = value

    def handle_form_sub_category_change(self, value: str):
        if self.show_add_form:
            self.form_sub_category = value

    def open_add_form(self):
        self._clear_form()
        self.show_add_form = True

    def close_add_form(self):
        self._clear_form()

    def open_edit_company_form(self, company_id: str):
        self._clear_edit_company_form()
        self.edit_company_id = company_id
        for c in self.companies:
            if c["id"] == company_id:
                self.edit_form_cin = c["cin"]
                self.edit_form_name = c["name"]
                self.edit_form_class = c["class"] if c["class"] != "-" else ""
                self.edit_form_category = c["category"] if c["category"] != "-" else ""
                self.edit_form_sub_category = c["sub_category"] if c["sub_category"] != "-" else ""
                break
        self.show_edit_company_form = True

    def close_edit_company_form(self):
        self._clear_edit_company_form()

    def handle_edit_form_cin_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_cin = value

    def handle_edit_form_name_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_name = value

    def handle_edit_form_class_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_class = value

    def handle_edit_form_category_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_category = value

    def handle_edit_form_sub_category_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_sub_category = value

    def save_edit_company(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.edit_form_error = "You do not have permission to edit companies."
            return
        cin = self.edit_form_cin.strip()
        name = self.edit_form_name.strip()
        company_class = self.edit_form_class.strip()
        company_category = self.edit_form_category.strip()
        company_sub_category = self.edit_form_sub_category.strip()
        if not cin or not name or not company_class or not company_category or not company_sub_category:
            self.edit_form_error = "All fields are required."
            return
        cid = self.edit_company_id
        self._clear_edit_company_form()
        self.is_saving = True
        return PortalState.commit_edit_company(cid, cin, name, company_class, company_category, company_sub_category)

    def commit_edit_company(
        self,
        company_id: str,
        cin: str,
        name: str,
        company_class: str,
        company_category: str,
        company_sub_category: str,
    ):
        try:
            cid = int(company_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid company ID '{company_id}'."
            self.is_saving = False
            return
        with SessionLocal() as session:
            existing = session.query(Company).filter(Company.cin == cin, Company.id != cid).first()
            if existing:
                self.error_message = f"Another company with CIN '{cin}' already exists."
                self.is_saving = False
                return
            company = session.query(Company).filter(Company.id == cid).first()
            if company:
                company.cin = cin
                company.name = name
                company.company_class = company_class
                company.company_type = company_category
                company.sub_category = company_sub_category
                session.commit()
        self.is_saving = False
        self.load_companies()

    # ── Save – two-hop sequential (no generators / yield) ────────────────────
    #
    # save_company  → validates, closes form, sets is_saving=True,
    #                 then chains to _commit_save.
    # _commit_save  → performs the DB insert and refreshes the table.
    #
    # Splitting into two events lets the frontend render the loading overlay
    # between hops without using any async generator.

    def save_company(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.form_error = "You do not have permission to add companies."
            return

        cin = self.form_cin.strip()
        name = self.form_name.strip()
        company_class = self.form_class.strip()
        company_category = self.form_category.strip()
        company_sub_category = self.form_sub_category.strip()

        if not cin or not name or not company_class or not company_category or not company_sub_category:
            self.form_error = "All fields are required."
            return

        # Close the form immediately and clear all fields so that any disk
        # write captured between the two hops has show_add_form=False.
        self._clear_form()
        self.is_saving = True
        # Chain to the DB work.  The frontend renders the loading overlay
        # while this second event is in flight.
        return PortalState.commit_save(
            cin, name, company_class, company_category, company_sub_category
        )

    def commit_save(
        self,
        cin: str,
        name: str,
        company_class: str,
        company_category: str,
        company_sub_category: str,
    ):
        """Second hop: DB insert + table refresh."""
        with SessionLocal() as session:
            if session.query(Company).filter(Company.cin == cin).first():
                self.error_message = f"A company with CIN '{cin}' already exists."
                self.is_saving = False
                return
            session.add(
                Company(
                    cin=cin,
                    name=name,
                    company_class=company_class,
                    company_type=company_category,
                    sub_category=company_sub_category,
                )
            )
            session.commit()
        self.is_saving = False
        self.load_companies()

    # ── User management ───────────────────────────────────────────────────────

    def switch_tab(self, tab: str):
        self.active_tab = tab
        self.error_message = ""
        if tab == "admin" and self.role == "ADMIN":
            self.load_users()

    def load_users(self):
        with SessionLocal() as session:
            rows = session.query(User).order_by(User.id).all()
            self.users = [
                {"id": str(u.id), "username": u.username, "role": u.role}
                for u in rows
            ]

    def open_add_user_form(self):
        self._clear_user_form()
        self.show_add_user_form = True

    def close_add_user_form(self):
        self._clear_user_form()

    def handle_user_form_username_change(self, value: str):
        if self.show_add_user_form:
            self.user_form_username = value

    def handle_user_form_password_change(self, value: str):
        if self.show_add_user_form:
            self.user_form_password = value

    def handle_user_form_role_change(self, value: str):
        if self.show_add_user_form:
            self.user_form_role = value

    def save_user(self):
        if self.role != "ADMIN":
            self.user_form_error = "Only admins can add users."
            return
        uname = self.user_form_username.strip()
        pwd = self.user_form_password.strip()
        user_role = self.user_form_role.strip()
        if not uname or not pwd or not user_role:
            self.user_form_error = "All fields are required."
            return
        if len(pwd) < 6:
            self.user_form_error = "Password must be at least 6 characters."
            return
        self._clear_user_form()
        self.is_saving = True
        return PortalState.commit_add_user(uname, pwd, user_role)

    def commit_add_user(self, username: str, password: str, user_role: str):
        with SessionLocal() as session:
            if session.query(User).filter(User.username == username).first():
                self.error_message = f"Username '{username}' already exists."
                self.is_saving = False
                return
            session.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                    role=user_role,
                )
            )
            session.commit()
        self.is_saving = False
        self.load_users()

    def delete_user(self, user_id: str):
        if self.role != "ADMIN":
            self.error_message = "Only admins can delete users."
            return
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid user ID '{user_id}'."
            return
        with SessionLocal() as session:
            user = session.query(User).filter(User.id == uid).first()
            if user:
                if user.username == self.current_user:
                    self.error_message = "You cannot delete your own account."
                    return
                session.delete(user)
                session.commit()
        self.load_users()

    def change_user_role(self, user_id: str, new_role: str):
        if self.role != "ADMIN":
            self.error_message = "Only admins can change roles."
            return
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid user ID '{user_id}'."
            return
        with SessionLocal() as session:
            user = session.query(User).filter(User.id == uid).first()
            if user:
                user.role = new_role
                session.commit()
                if user.username == self.current_user:
                    self.role = new_role
        self.load_users()

    # ── Edit-user form handlers ───────────────────────────────────────────────

    def open_edit_user_form(self, user_id: str):
        self._clear_edit_user_form()
        self.edit_user_id = user_id
        for u in self.users:
            if u["id"] == user_id:
                self.edit_user_form_username = u["username"]
                break
        self.show_edit_user_form = True

    def close_edit_user_form(self):
        self._clear_edit_user_form()

    def handle_edit_user_form_username_change(self, value: str):
        if self.show_edit_user_form:
            self.edit_user_form_username = value

    def handle_edit_user_form_password_change(self, value: str):
        if self.show_edit_user_form:
            self.edit_user_form_password = value

    def save_edit_user(self):
        if self.role != "ADMIN":
            self.edit_user_form_error = "Only admins can edit users."
            return
        uname = self.edit_user_form_username.strip()
        pwd = self.edit_user_form_password.strip()
        if not uname:
            self.edit_user_form_error = "Username is required."
            return
        if pwd and len(pwd) < 6:
            self.edit_user_form_error = "Password must be at least 6 characters."
            return
        uid = self.edit_user_id
        self._clear_edit_user_form()
        self.is_saving = True
        return PortalState.commit_edit_user(uid, uname, pwd)

    def commit_edit_user(self, user_id: str, username: str, password: str):
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid user ID '{user_id}'."
            self.is_saving = False
            return
        with SessionLocal() as session:
            existing = session.query(User).filter(User.username == username, User.id != uid).first()
            if existing:
                self.error_message = f"Username '{username}' is already taken."
                self.is_saving = False
                return
            user = session.query(User).filter(User.id == uid).first()
            if user:
                old_username = user.username
                user.username = username
                if password:
                    user.password_hash = hash_password(password)
                session.commit()
                if old_username == self.current_user:
                    self.current_user = username
        self.is_saving = False
        self.load_users()


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
                    rx.icon("circle-check", size=24, color="white"),
                    rx.text("Streamlined company registry", color="rgba(255,255,255,0.9)", size="3"),
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("circle-check", size=24, color="white"),
                    rx.text("Secure access control", color="rgba(255,255,255,0.9)", size="3"),
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("circle-check", size=24, color="white"),
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
                    rx.el.input(
                        placeholder="admin",
                        value=PortalState.username,
                        on_change=PortalState.handle_username_change,
                        on_key_down=PortalState.handle_key_down,
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "0.875rem 1rem",
                            "border_radius": "0.625rem",
                            "border": "2px solid #999",
                            "background_color": "white",
                            "font_size": "1rem",
                            "font_weight": "500",
                            "color": "black",
                            "outline": "none",
                            "box_sizing": "border-box",
                        },
                    ),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Password", size="2", weight="bold", color="#333"),
                    rx.el.input(
                        placeholder="Password",
                        value=PortalState.password,
                        on_change=PortalState.handle_password_change,
                        on_key_down=PortalState.handle_key_down,
                        type="password",
                        style={
                            "width": "100%",
                            "padding": "0.875rem 1rem",
                            "border_radius": "0.625rem",
                            "border": "2px solid #999",
                            "background_color": "white",
                            "font_size": "1rem",
                            "font_weight": "500",
                            "color": "black",
                            "outline": "none",
                            "box_sizing": "border-box",
                        },
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
                        rx.icon("circle-alert", size=20, color="#dc2626"),
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


def _form_input(label: str, placeholder: str, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold", color="#333"),
        rx.el.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            type="text",
            style={
                "width": "100%",
                "padding": "0.625rem 0.875rem",
                "border_radius": "0.5rem",
                "border": "2px solid #d0d0d0",
                "background_color": "white",
                "font_size": "0.95rem",
                "color": "black",
                "outline": "none",
                "box_sizing": "border-box",
            },
        ),
        spacing="1",
        width="100%",
    )


def _form_select(label: str, options: list, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold", color="#333"),
        rx.el.select(
            rx.el.option("-- Select --", value="", disabled=True),
            *[rx.el.option(o, value=o) for o in options],
            value=value,
            on_change=on_change,
            style={
                "width": "100%",
                "padding": "0.625rem 0.875rem",
                "border_radius": "0.5rem",
                "border": "2px solid #d0d0d0",
                "background_color": "white",
                "font_size": "0.95rem",
                "color": "#111111",
                "outline": "none",
                "box_sizing": "border-box",
                "cursor": "pointer",
                "appearance": "auto",
            },
        ),
        spacing="1",
        width="100%",
    )


def add_company_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_add_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("building-2", size=22, color="#667eea"),
                        rx.heading("Add Company", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_add_form,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    _form_input("CIN", "e.g. U74999MH2021PTC123456", PortalState.form_cin, PortalState.handle_form_cin_change),
                    _form_input("Company Name", "Enter company name", PortalState.form_name, PortalState.handle_form_name_change),
                    _form_select("Class", ["PUBLIC", "PRIVATE"], PortalState.form_class, PortalState.handle_form_class_change),
                    _form_select("Category", ["Company limited by Shares"], PortalState.form_category, PortalState.handle_form_category_change),
                    _form_select(
                        "Sub Category",
                        [
                            "Non-government company",
                            "State government company",
                            "Union government company",
                            "Subsidiary of company incorporated outside India",
                        ],
                        PortalState.form_sub_category,
                        PortalState.handle_form_sub_category_change,
                    ),
                    rx.cond(
                        PortalState.form_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.form_error, size="2", color="#dc2626"),
                                spacing="2",
                            ),
                            padding="0.75rem",
                            border_radius="0.5rem",
                            background="#fee2e2",
                            border_left="4px solid #dc2626",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=PortalState.close_add_form,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save Company"), spacing="2"),
                            on_click=PortalState.save_company,
                            loading=PortalState.is_saving,
                            disabled=PortalState.is_saving,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="500px",
                width="90%",
                box_shadow="0 20px 60px rgba(0,0,0,0.3)",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background="rgba(0,0,0,0.5)",
            z_index="1000",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def edit_company_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_edit_company_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("pencil", size=22, color="#667eea"),
                        rx.heading("Edit Company", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_edit_company_form,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    _form_input("CIN", "e.g. U74999MH2021PTC123456", PortalState.edit_form_cin, PortalState.handle_edit_form_cin_change),
                    _form_input("Company Name", "Enter company name", PortalState.edit_form_name, PortalState.handle_edit_form_name_change),
                    _form_select("Class", ["PUBLIC", "PRIVATE"], PortalState.edit_form_class, PortalState.handle_edit_form_class_change),
                    _form_select("Category", ["Company limited by Shares"], PortalState.edit_form_category, PortalState.handle_edit_form_category_change),
                    _form_select(
                        "Sub Category",
                        [
                            "Non-government company",
                            "State government company",
                            "Union government company",
                            "Subsidiary of company incorporated outside India",
                        ],
                        PortalState.edit_form_sub_category,
                        PortalState.handle_edit_form_sub_category_change,
                    ),
                    rx.cond(
                        PortalState.edit_form_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.edit_form_error, size="2", color="#dc2626"),
                                spacing="2",
                            ),
                            padding="0.75rem",
                            border_radius="0.5rem",
                            background="#fee2e2",
                            border_left="4px solid #dc2626",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=PortalState.close_edit_company_form,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save Changes"), spacing="2"),
                            on_click=PortalState.save_edit_company,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="500px",
                width="90%",
                box_shadow="0 20px 60px rgba(0,0,0,0.3)",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background="rgba(0,0,0,0.5)",
            z_index="1000",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def companies_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("CIN", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Company Name", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Class", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Category", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Sub Category", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Actions", font_weight="700", color="white", font_size="0.95rem"),
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
                    rx.table.cell(rx.badge(item["class"], variant="outline", color_scheme="violet")),
                    rx.table.cell(rx.badge(item["category"], variant="outline", color_scheme="cyan")),
                    rx.table.cell(rx.text(item["sub_category"], color="#555", size="2")),
                    rx.table.cell(
                        rx.cond(
                            (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                            rx.hstack(
                                rx.button(
                                    rx.icon("pencil", size=14),
                                    on_click=PortalState.open_edit_company_form(item["id"]),
                                    color_scheme="blue",
                                    variant="ghost",
                                    size="1",
                                ),
                                rx.dialog.root(
                                    rx.dialog.trigger(
                                        rx.button(
                                            rx.icon("trash-2", size=14),
                                            color_scheme="red",
                                            variant="ghost",
                                            size="1",
                                        ),
                                    ),
                                    rx.dialog.content(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.icon("triangle-alert", size=22, color="#dc2626"),
                                                rx.dialog.title(
                                                    "Delete Company",
                                                    size="5",
                                                    weight="bold",
                                                    color="#1a1a1a",
                                                ),
                                                spacing="2",
                                                align_items="center",
                                            ),
                                            rx.divider(),
                                            rx.dialog.description(
                                                rx.text(
                                                    "Are you sure you want to permanently delete ",
                                                    rx.text.strong(item["name"]),
                                                    "? This action cannot be undone.",
                                                    size="3",
                                                    color="#333",
                                                ),
                                            ),
                                            rx.hstack(
                                                rx.dialog.close(
                                                    rx.button(
                                                        "Cancel",
                                                        variant="outline",
                                                        color_scheme="gray",
                                                        size="3",
                                                    ),
                                                ),
                                                rx.dialog.close(
                                                    rx.button(
                                                        rx.hstack(rx.icon("trash-2", size=16), rx.text("Delete"), spacing="2"),
                                                        on_click=PortalState.confirm_delete(item["id"]),
                                                        color_scheme="red",
                                                        size="3",
                                                    ),
                                                ),
                                                spacing="3",
                                                justify="end",
                                                width="100%",
                                                padding_top="0.5rem",
                                            ),
                                            spacing="4",
                                            width="100%",
                                        ),
                                        max_width="420px",
                                    ),
                                ),
                                spacing="1",
                            ),
                        )
                    ),
                    _hover={"background": "rgba(102,126,234,0.04)"},
                    border_bottom="1px solid #f0f0f0",
                    padding="1rem",
                ),
            )
        ),
        width="100%",
        size="3",
    )


def users_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Username", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Role", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Actions", font_weight="700", color="white", font_size="0.95rem"),
            ),
            background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
        ),
        rx.table.body(
            rx.foreach(
                PortalState.users,
                lambda user: rx.table.row(
                    rx.table.cell(
                        rx.hstack(
                            rx.icon("user", size=16, color="#667eea"),
                            rx.text(user["username"], font_weight="600", color="#1a1a1a", size="3"),
                            spacing="2",
                            align_items="center",
                        )
                    ),
                    rx.table.cell(
                        rx.el.select(
                            rx.el.option("VIEWER", value="VIEWER"),
                            rx.el.option("EDITOR", value="EDITOR"),
                            rx.el.option("ADMIN", value="ADMIN"),
                            value=user["role"],
                            on_change=PortalState.change_user_role(user["id"]),
                            style={
                                "padding": "0.375rem 0.625rem",
                                "border_radius": "0.375rem",
                                "border": "1.5px solid #d0d0d0",
                                "background_color": "white",
                                "font_size": "0.875rem",
                                "color": "#111111",
                                "cursor": "pointer",
                            },
                        )
                    ),
                    rx.table.cell(
                        rx.hstack(
                            rx.button(
                                rx.icon("pencil", size=14),
                                on_click=PortalState.open_edit_user_form(user["id"]),
                                color_scheme="blue",
                                variant="ghost",
                                size="1",
                            ),
                            rx.cond(
                                user["username"] != PortalState.current_user,
                                rx.dialog.root(
                                    rx.dialog.trigger(
                                        rx.button(rx.icon("trash-2", size=14), color_scheme="red", variant="ghost", size="1"),
                                    ),
                                    rx.dialog.content(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.icon("triangle-alert", size=22, color="#dc2626"),
                                                rx.dialog.title("Delete User", size="5", weight="bold", color="#1a1a1a"),
                                                spacing="2",
                                                align_items="center",
                                            ),
                                            rx.divider(),
                                            rx.dialog.description(
                                                rx.text(
                                                    "Permanently delete user ",
                                                    rx.text.strong(user["username"]),
                                                    "? This cannot be undone.",
                                                    size="3",
                                                    color="#333",
                                                ),
                                            ),
                                            rx.hstack(
                                                rx.dialog.close(rx.button("Cancel", variant="outline", color_scheme="gray", size="3")),
                                                rx.dialog.close(
                                                    rx.button(
                                                        rx.hstack(rx.icon("trash-2", size=16), rx.text("Delete"), spacing="2"),
                                                        on_click=PortalState.delete_user(user["id"]),
                                                        color_scheme="red",
                                                        size="3",
                                                    ),
                                                ),
                                                spacing="3",
                                                justify="end",
                                                width="100%",
                                                padding_top="0.5rem",
                                            ),
                                            spacing="4",
                                            width="100%",
                                        ),
                                        max_width="420px",
                                    ),
                                ),
                            ),
                            spacing="2",
                        )
                    ),
                    _hover={"background": "rgba(102,126,234,0.04)"},
                    border_bottom="1px solid #f0f0f0",
                    padding="1rem",
                ),
            )
        ),
        width="100%",
        size="3",
    )


def edit_user_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_edit_user_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("user-pen", size=22, color="#667eea"),
                        rx.heading("Edit User", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(rx.icon("x", size=18), on_click=PortalState.close_edit_user_form, variant="ghost", size="1"),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    _form_input("Username", "Enter username", PortalState.edit_user_form_username, PortalState.handle_edit_user_form_username_change),
                    _form_input("New Password", "Leave blank to keep current password", PortalState.edit_user_form_password, PortalState.handle_edit_user_form_password_change),
                    rx.cond(
                        PortalState.edit_user_form_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.edit_user_form_error, size="2", color="#dc2626"),
                                spacing="2",
                            ),
                            padding="0.75rem",
                            border_radius="0.5rem",
                            background="#fee2e2",
                            border_left="4px solid #dc2626",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.button("Cancel", on_click=PortalState.close_edit_user_form, variant="outline", color_scheme="gray", size="3"),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save Changes"), spacing="2"),
                            on_click=PortalState.save_edit_user,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="480px",
                width="90%",
                box_shadow="0 20px 60px rgba(0,0,0,0.3)",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background="rgba(0,0,0,0.5)",
            z_index="1000",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def add_user_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_add_user_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("user-plus", size=22, color="#667eea"),
                        rx.heading("Add User", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(rx.icon("x", size=18), on_click=PortalState.close_add_user_form, variant="ghost", size="1"),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    _form_input("Username", "Enter username", PortalState.user_form_username, PortalState.handle_user_form_username_change),
                    _form_input("Password", "Min. 6 characters", PortalState.user_form_password, PortalState.handle_user_form_password_change),
                    _form_select(
                        "Role",
                        ["VIEWER", "EDITOR", "ADMIN"],
                        PortalState.user_form_role,
                        PortalState.handle_user_form_role_change,
                    ),
                    rx.cond(
                        PortalState.user_form_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.user_form_error, size="2", color="#dc2626"),
                                spacing="2",
                            ),
                            padding="0.75rem",
                            border_radius="0.5rem",
                            background="#fee2e2",
                            border_left="4px solid #dc2626",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.button("Cancel", on_click=PortalState.close_add_user_form, variant="outline", color_scheme="gray", size="3"),
                        rx.button(
                            rx.hstack(rx.icon("user-plus", size=16), rx.text("Add User"), spacing="2"),
                            on_click=PortalState.save_user,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="3",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="480px",
                width="90%",
                box_shadow="0 20px 60px rgba(0,0,0,0.3)",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background="rgba(0,0,0,0.5)",
            z_index="1000",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def admin_panel() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("users", size=22, color="#667eea"),
                    rx.vstack(
                        rx.heading("User Management", size="5", color="#1a1a1a"),
                        rx.text(f"{PortalState.users.length()} users", size="1", color="#999"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(rx.icon("user-plus", size=16), rx.text("Add User"), spacing="2"),
                        on_click=PortalState.open_add_user_form,
                        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        color="white",
                        size="2",
                    ),
                    width="100%",
                    align_items="center",
                ),
                users_table(),
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
    )


def companies_section() -> rx.Component:
    return rx.vstack(
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
                        rx.hstack(rx.icon("search", size=16), rx.text("Search"), spacing="2"),
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
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("database", size=22, color="#667eea"),
                    rx.vstack(
                        rx.heading("Company Registry", size="5", color="#1a1a1a"),
                        rx.text(f"{PortalState.companies.length()} companies", size="1", color="#999"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                        rx.button(
                            rx.hstack(rx.icon("plus", size=16), rx.text("Add Company"), spacing="2"),
                            on_click=PortalState.open_add_form,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="2",
                        ),
                    ),
                    width="100%",
                    align_items="center",
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
    )


def dashboard_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header
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
                            rx.hstack(rx.icon("log-out", size=16), rx.text("Logout"), spacing="2"),
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
            # Tab navigation bar (Admin tab visible only for ADMIN role)
            rx.box(
                rx.hstack(
                    rx.button(
                        rx.hstack(rx.icon("building-2", size=15), rx.text("Companies"), spacing="2"),
                        on_click=PortalState.switch_tab("companies"),
                        variant="ghost",
                        size="2",
                        color=rx.cond(PortalState.active_tab == "companies", "white", "rgba(255,255,255,0.65)"),
                        background=rx.cond(PortalState.active_tab == "companies", "rgba(255,255,255,0.22)", "transparent"),
                        border_radius="0.5rem",
                        _hover={"background": "rgba(255,255,255,0.15)", "color": "white"},
                    ),
                    rx.cond(
                        PortalState.role == "ADMIN",
                        rx.button(
                            rx.hstack(rx.icon("shield-check", size=15), rx.text("Admin"), spacing="2"),
                            on_click=PortalState.switch_tab("admin"),
                            variant="ghost",
                            size="2",
                            color=rx.cond(PortalState.active_tab == "admin", "white", "rgba(255,255,255,0.65)"),
                            background=rx.cond(PortalState.active_tab == "admin", "rgba(255,255,255,0.22)", "transparent"),
                            border_radius="0.5rem",
                            _hover={"background": "rgba(255,255,255,0.15)", "color": "white"},
                        ),
                    ),
                    spacing="1",
                    padding="0.5rem 1.5rem",
                ),
                background="linear-gradient(90deg, #5a6fd6 0%, #6a3f95 100%)",
                width="100%",
            ),
            # Error banner (shared across tabs)
            rx.cond(
                PortalState.error_message != "",
                rx.box(
                    rx.hstack(
                        rx.icon("circle-alert", size=20, color="#dc2626"),
                        rx.text(PortalState.error_message, size="2", color="#dc2626", weight="medium"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=14),
                            on_click=PortalState.clear_error,
                            variant="ghost",
                            size="1",
                            color="#dc2626",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="center",
                    ),
                    padding="0.75rem 2rem",
                    background="#fee2e2",
                    border_bottom="2px solid #fca5a5",
                    width="100%",
                ),
            ),
            # Tab content
            rx.cond(
                PortalState.active_tab == "companies",
                companies_section(),
                admin_panel(),
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        add_company_dialog(),
        edit_company_dialog(),
        add_user_dialog(),
        edit_user_dialog(),
        background="#f5f7fa",
        width="100%",
        padding="0",
    )


def loading_overlay() -> rx.Component:
    """Full-screen spinner shown while a save is in flight."""
    return rx.box(
        rx.vstack(
            rx.spinner(size="3", color="white"),
            rx.text("Saving…", size="3", color="white", weight="bold"),
            spacing="3",
            align_items="center",
        ),
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        background="rgba(0,0,0,0.55)",
        z_index="9999",
        display="flex",
        align_items="center",
        justify_content="center",
    )


def index() -> rx.Component:
    return rx.box(
        rx.cond(PortalState.is_authenticated, dashboard_page(), login_page()),
        rx.cond(PortalState.is_saving, loading_overlay()),
    )


app = rx.App()
# on_load fires on every page load AND on every WebSocket reconnect.
# on_page_load resets all form state, so stale disk-persisted state can
# never cause the Add Company dialog to reappear after saving.
app.add_page(index, title="CDM Portal", on_load=PortalState.on_page_load)

