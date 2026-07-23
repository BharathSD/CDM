from __future__ import annotations

import re
from datetime import datetime

import reflex as rx
from sqlalchemy import func, or_

from .database import (
    Company,
    CompanyDirector,
    CompanyLLP,
    Director,
    LLP,
    LLPDirector,
    SessionLocal,
    User,
    hash_password,
    init_db,
    verify_password,
)

init_db()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _parse_doi(value: str) -> bool:
    """Return True if value is a valid calendar date in DD/MM/YYYY format."""
    try:
        datetime.strptime(value, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def _format_date(value: str | None) -> str:
    """Convert YYYY-MM-DD (from DB / old picker) to DD/MM/YYYY for display."""
    if not value:
        return ""
    m = _ISO_DATE_RE.match(value)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    return value


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
    filter_classes: list[str] = []
    filter_categories: list[str] = []
    filter_sub_categories: list[str] = []
    # filter dropdown UI state
    class_dropdown_open: bool = False
    category_dropdown_open: bool = False
    sub_category_dropdown_open: bool = False
    class_search: str = ""
    category_search: str = ""
    sub_category_search: str = ""
    companies: list[dict] = []

    # ── Add-company form ──────────────────────────────────────────────────────
    show_add_form: bool = False
    is_saving: bool = False
    form_cin: str = ""
    form_name: str = ""
    form_class: str = ""
    form_category: str = ""
    form_sub_category: str = ""
    form_doi: str = ""
    form_email: str = ""
    form_address: str = ""
    form_error: str = ""
    # Extended MCA fields – add form
    form_roc_code: str = ""
    form_roc_office: str = ""
    form_rd_name: str = ""
    form_rd_region: str = ""
    form_registration_number: str = ""
    form_authorised_capital: str = ""
    form_paid_up_capital: str = ""
    form_number_of_members: str = ""
    form_date_of_last_agm: str = ""
    form_date_of_balance_sheet: str = ""
    form_listed_status: str = ""
    form_suspended_at_stock_exchange: str = ""
    form_pin_code: str = ""
    form_phone: str = ""
    form_country: str = ""

    # ── Edit-company form ─────────────────────────────────────────────────────
    show_edit_company_form: bool = False
    edit_company_id: str = ""
    edit_form_cin: str = ""
    edit_form_name: str = ""
    edit_form_class: str = ""
    edit_form_category: str = ""
    edit_form_sub_category: str = ""
    edit_form_doi: str = ""
    edit_form_email: str = ""
    edit_form_address: str = ""
    edit_form_error: str = ""
    # Extended MCA fields – edit form
    edit_form_roc_code: str = ""
    edit_form_roc_office: str = ""
    edit_form_rd_name: str = ""
    edit_form_rd_region: str = ""
    edit_form_registration_number: str = ""
    edit_form_authorised_capital: str = ""
    edit_form_paid_up_capital: str = ""
    edit_form_number_of_members: str = ""
    edit_form_date_of_last_agm: str = ""
    edit_form_date_of_balance_sheet: str = ""
    edit_form_listed_status: str = ""
    edit_form_suspended_at_stock_exchange: str = ""
    edit_form_pin_code: str = ""
    edit_form_phone: str = ""
    edit_form_country: str = ""

    # ── Directors ─────────────────────────────────────────────────────────────
    directors: list[dict] = []
    directors_search_query: str = ""
    show_add_director_form: bool = False
    form_din: str = ""
    form_director_name: str = ""
    form_director_email: str = ""
    form_director_phone: str = ""
    form_director_error: str = ""
    # Edit director form
    show_edit_director_form: bool = False
    edit_director_id: str = ""
    edit_form_din: str = ""
    edit_form_director_name: str = ""
    edit_form_director_email: str = ""
    edit_form_director_phone: str = ""
    edit_form_director_error: str = ""

    # ── Company-Director associations ─────────────────────────────────────────
    show_manage_directors: bool = False
    managing_company_id: str = ""
    managing_company_name: str = ""
    company_directors: list[dict] = []
    assoc_search_query: str = ""
    assoc_search_results: list[dict] = []
    assoc_selected_director_id: str = ""
    assoc_selected_director_name: str = ""
    assoc_share_percent: str = ""
    assoc_designation: str = ""
    assoc_category: str = ""
    assoc_original_appointment_date: str = ""
    assoc_current_designation_date: str = ""
    assoc_cessation_date: str = ""
    assoc_error: str = ""
    confirm_remove_assoc_id: str = ""
    assoc_editing_id: str = ""

    # ── LLPs ──────────────────────────────────────────────────────────────────
    llps_search_query: str = ""
    llps: list[dict] = []

    show_add_llp_form: bool = False
    form_llpin: str = ""
    form_llp_name: str = ""
    form_llp_roc_name: str = ""
    form_llp_doi: str = ""
    form_llp_email: str = ""
    form_llp_address: str = ""
    form_llp_number_of_partners: str = ""
    form_llp_number_of_designated_partners: str = ""
    form_llp_total_obligation: str = ""
    form_llp_strike_off_date: str = ""
    form_llp_status_under_cirp: str = ""
    form_llp_small_llp: str = ""
    form_llp_error: str = ""

    show_edit_llp_form: bool = False
    edit_llp_id: str = ""
    edit_form_llpin: str = ""
    edit_form_llp_name: str = ""
    edit_form_llp_roc_name: str = ""
    edit_form_llp_doi: str = ""
    edit_form_llp_email: str = ""
    edit_form_llp_address: str = ""
    edit_form_llp_number_of_partners: str = ""
    edit_form_llp_number_of_designated_partners: str = ""
    edit_form_llp_total_obligation: str = ""
    edit_form_llp_strike_off_date: str = ""
    edit_form_llp_status_under_cirp: str = ""
    edit_form_llp_small_llp: str = ""
    edit_form_llp_error: str = ""

    # ── LLP ↔ Director (designated partner) associations ─────────────────────
    show_manage_llp_partners: bool = False
    managing_llp_id: str = ""
    managing_llp_name: str = ""
    llp_partners: list[dict] = []
    llp_partner_search_query: str = ""
    llp_partner_search_results: list[dict] = []
    llp_partner_selected_director_id: str = ""
    llp_partner_selected_director_name: str = ""
    llp_partner_designation: str = ""
    llp_partner_appointment_date: str = ""
    llp_partner_cessation_date: str = ""
    llp_partner_is_signatory: str = ""
    llp_partner_error: str = ""
    confirm_remove_llp_partner_id: str = ""
    llp_partner_editing_id: str = ""

    # ── LLP ↔ Company links ────────────────────────────────────────────────
    show_manage_llp_companies: bool = False
    llp_companies: list[dict] = []
    llp_company_search_query: str = ""
    llp_company_search_results: list[dict] = []
    llp_company_selected_id: str = ""
    llp_company_selected_name: str = ""
    llp_company_relationship_note: str = ""
    llp_company_error: str = ""
    confirm_remove_llp_company_id: str = ""

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
        self.form_doi = ""
        self.form_email = ""
        self.form_address = ""
        self.form_error = ""
        self.form_roc_code = ""
        self.form_roc_office = ""
        self.form_rd_name = ""
        self.form_rd_region = ""
        self.form_registration_number = ""
        self.form_paid_up_capital = ""
        self.form_number_of_members = ""
        self.form_date_of_last_agm = ""
        self.form_date_of_balance_sheet = ""
        self.form_listed_status = ""
        self.form_suspended_at_stock_exchange = ""
        self.form_pin_code = ""
        self.form_phone = ""
        self.form_country = ""

    def _clear_edit_company_form(self) -> None:
        """Reset every edit-company-form var to its default."""
        self.show_edit_company_form = False
        self.edit_company_id = ""
        self.edit_form_cin = ""
        self.edit_form_name = ""
        self.edit_form_class = ""
        self.edit_form_category = ""
        self.edit_form_sub_category = ""
        self.edit_form_doi = ""
        self.edit_form_email = ""
        self.edit_form_address = ""
        self.edit_form_error = ""
        self.edit_form_roc_code = ""
        self.edit_form_roc_office = ""
        self.edit_form_rd_name = ""
        self.edit_form_rd_region = ""
        self.edit_form_registration_number = ""
        self.edit_form_paid_up_capital = ""
        self.edit_form_number_of_members = ""
        self.edit_form_date_of_last_agm = ""
        self.edit_form_date_of_balance_sheet = ""
        self.edit_form_listed_status = ""
        self.edit_form_suspended_at_stock_exchange = ""
        self.edit_form_pin_code = ""
        self.edit_form_phone = ""
        self.edit_form_country = ""

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

    def _clear_director_form(self) -> None:
        """Reset every director-form var to its default."""
        self.show_add_director_form = False
        self.form_din = ""
        self.form_director_name = ""
        self.form_director_email = ""
        self.form_director_phone = ""
        self.form_director_error = ""

    def _clear_edit_director_form(self) -> None:
        """Reset every edit-director-form var to its default."""
        self.show_edit_director_form = False
        self.edit_director_id = ""
        self.edit_form_din = ""
        self.edit_form_director_name = ""
        self.edit_form_director_email = ""
        self.edit_form_director_phone = ""
        self.edit_form_director_error = ""

    def _clear_manage_directors(self) -> None:
        """Reset company-director association panel state."""
        self.show_manage_directors = False
        self.managing_company_id = ""
        self.managing_company_name = ""
        self.company_directors = []
        self.assoc_search_query = ""
        self.assoc_search_results = []
        self.assoc_selected_director_id = ""
        self.assoc_selected_director_name = ""
        self.assoc_share_percent = ""
        self.assoc_designation = ""
        self.assoc_category = ""
        self.assoc_original_appointment_date = ""
        self.assoc_current_designation_date = ""
        self.assoc_cessation_date = ""
        self.assoc_error = ""
        self.confirm_remove_assoc_id = ""
        self.assoc_editing_id = ""

    def _clear_llp_form(self) -> None:
        """Reset every LLP-form var to its default."""
        self.show_add_llp_form = False
        self.form_llpin = ""
        self.form_llp_name = ""
        self.form_llp_roc_name = ""
        self.form_llp_doi = ""
        self.form_llp_email = ""
        self.form_llp_address = ""
        self.form_llp_number_of_partners = ""
        self.form_llp_number_of_designated_partners = ""
        self.form_llp_total_obligation = ""
        self.form_llp_strike_off_date = ""
        self.form_llp_status_under_cirp = ""
        self.form_llp_small_llp = ""
        self.form_llp_error = ""

    def _clear_edit_llp_form(self) -> None:
        """Reset every edit-LLP-form var to its default."""
        self.show_edit_llp_form = False
        self.edit_llp_id = ""
        self.edit_form_llpin = ""
        self.edit_form_llp_name = ""
        self.edit_form_llp_roc_name = ""
        self.edit_form_llp_doi = ""
        self.edit_form_llp_email = ""
        self.edit_form_llp_address = ""
        self.edit_form_llp_number_of_partners = ""
        self.edit_form_llp_number_of_designated_partners = ""
        self.edit_form_llp_total_obligation = ""
        self.edit_form_llp_strike_off_date = ""
        self.edit_form_llp_status_under_cirp = ""
        self.edit_form_llp_small_llp = ""
        self.edit_form_llp_error = ""

    def _clear_manage_llp_partners(self) -> None:
        """Reset LLP-director (designated partner) association panel state."""
        self.show_manage_llp_partners = False
        self.managing_llp_id = ""
        self.managing_llp_name = ""
        self.llp_partners = []
        self.llp_partner_search_query = ""
        self.llp_partner_search_results = []
        self.llp_partner_selected_director_id = ""
        self.llp_partner_selected_director_name = ""
        self.llp_partner_designation = ""
        self.llp_partner_appointment_date = ""
        self.llp_partner_cessation_date = ""
        self.llp_partner_is_signatory = ""
        self.llp_partner_error = ""
        self.confirm_remove_llp_partner_id = ""
        self.llp_partner_editing_id = ""

    def _clear_manage_llp_companies(self) -> None:
        """Reset LLP-company link panel state."""
        self.show_manage_llp_companies = False
        self.llp_companies = []
        self.llp_company_search_query = ""
        self.llp_company_search_results = []
        self.llp_company_selected_id = ""
        self.llp_company_selected_name = ""
        self.llp_company_relationship_note = ""
        self.llp_company_error = ""
        self.confirm_remove_llp_company_id = ""

    # ── Computed vars ─────────────────────────────────────────────────────────

    @rx.var
    def filtered_class_options(self) -> list[str]:
        options = ["PUBLIC", "PRIVATE"]
        if not self.class_search.strip():
            return options
        term = self.class_search.strip().lower()
        return [o for o in options if term in o.lower()]

    @rx.var
    def filtered_category_options(self) -> list[str]:
        options = ["Company limited by Shares"]
        if not self.category_search.strip():
            return options
        term = self.category_search.strip().lower()
        return [o for o in options if term in o.lower()]

    @rx.var
    def filtered_sub_category_options(self) -> list[str]:
        options = [
            "Non-government company",
            "State government company",
            "Union government company",
            "Subsidiary of company incorporated outside India",
        ]
        if not self.sub_category_search.strip():
            return options
        term = self.sub_category_search.strip().lower()
        return [o for o in options if term in o.lower()]

    # ── Page lifecycle ────────────────────────────────────────────────────────

    def on_page_load(self):
        """Registered via on_load so it runs on every page load AND on every
        WebSocket reconnect (Reflex re-fires on_load_internal after reconnect).
        Guarantees transient form state is never restored from stale disk state."""
        self._clear_form()
        self._clear_edit_company_form()
        self._clear_user_form()
        self._clear_edit_user_form()
        self._clear_director_form()
        self._clear_edit_director_form()
        self._clear_llp_form()
        self._clear_edit_llp_form()
        if self.is_authenticated:
            self.load_companies()
            self.load_directors()
            self.load_llps()
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
        self._clear_director_form()
        self.active_tab = "companies"
        self.is_authenticated = False
        self.current_user = ""
        self.role = ""
        self.username = ""
        self.password = ""
        self.error_message = ""
        self.companies = []
        self.users = []
        self.directors = []
        self.llps = []
        self.search_query = ""
        self.directors_search_query = ""
        self.llps_search_query = ""
        self.filter_classes = []
        self.filter_categories = []
        self.filter_sub_categories = []
        self.class_dropdown_open = False
        self.category_dropdown_open = False
        self.sub_category_dropdown_open = False
        self.class_search = ""
        self.category_search = ""
        self.sub_category_search = ""
        self._clear_edit_company_form()
        self._clear_edit_user_form()
        self._clear_edit_director_form()
        self._clear_manage_directors()
        self._clear_edit_llp_form()
        self._clear_manage_llp_partners()
        self._clear_manage_llp_companies()

    def clear_error(self):
        self.error_message = ""

    # ── Companies ─────────────────────────────────────────────────────────────

    def handle_search_input(self, value: str):
        self.search_query = value
        self.load_companies()

    def handle_search_key_down(self, key: str):
        if key == "Enter":
            self.load_companies()

    def toggle_filter_class(self, value: str, checked: bool):
        _all_opts = ["PUBLIC", "PRIVATE"]
        if value == "ALL":
            self.filter_classes = []
            self.load_companies()
            return
        if checked:
            if value not in self.filter_classes:
                new_list = self.filter_classes + [value]
                # If every option is now ticked, revert to "all" mode
                self.filter_classes = [] if sorted(new_list) == sorted(_all_opts) else new_list
        else:
            if not self.filter_classes:
                # Was in "all" mode – switch to all-except-this
                self.filter_classes = [o for o in _all_opts if o != value]
            else:
                self.filter_classes = [v for v in self.filter_classes if v != value]
        self.load_companies()

    def toggle_filter_category(self, value: str, checked: bool):
        _all_opts = ["Company limited by Shares"]
        if value == "ALL":
            self.filter_categories = []
            self.load_companies()
            return
        if checked:
            if value not in self.filter_categories:
                new_list = self.filter_categories + [value]
                self.filter_categories = [] if sorted(new_list) == sorted(_all_opts) else new_list
        else:
            if not self.filter_categories:
                self.filter_categories = [o for o in _all_opts if o != value]
            else:
                self.filter_categories = [v for v in self.filter_categories if v != value]
        self.load_companies()

    def toggle_filter_sub_category(self, value: str, checked: bool):
        _all_opts = [
            "Non-government company",
            "State government company",
            "Union government company",
            "Subsidiary of company incorporated outside India",
        ]
        if value == "ALL":
            self.filter_sub_categories = []
            self.load_companies()
            return
        if checked:
            if value not in self.filter_sub_categories:
                new_list = self.filter_sub_categories + [value]
                self.filter_sub_categories = [] if sorted(new_list) == sorted(_all_opts) else new_list
        else:
            if not self.filter_sub_categories:
                self.filter_sub_categories = [o for o in _all_opts if o != value]
            else:
                self.filter_sub_categories = [v for v in self.filter_sub_categories if v != value]
        self.load_companies()

    def clear_filters(self):
        self.filter_classes = []
        self.filter_categories = []
        self.filter_sub_categories = []
        self.class_dropdown_open = False
        self.category_dropdown_open = False
        self.sub_category_dropdown_open = False
        self.class_search = ""
        self.category_search = ""
        self.sub_category_search = ""
        self.load_companies()

    def toggle_class_dropdown(self):
        self.class_dropdown_open = not self.class_dropdown_open
        self.category_dropdown_open = False
        self.sub_category_dropdown_open = False
        if not self.class_dropdown_open:
            self.class_search = ""

    def toggle_category_dropdown(self):
        self.category_dropdown_open = not self.category_dropdown_open
        self.class_dropdown_open = False
        self.sub_category_dropdown_open = False
        if not self.category_dropdown_open:
            self.category_search = ""

    def toggle_sub_category_dropdown(self):
        self.sub_category_dropdown_open = not self.sub_category_dropdown_open
        self.class_dropdown_open = False
        self.category_dropdown_open = False
        if not self.sub_category_dropdown_open:
            self.sub_category_search = ""

    def handle_class_search(self, value: str):
        self.class_search = value

    def handle_category_search(self, value: str):
        self.category_search = value

    def handle_sub_category_search(self, value: str):
        self.sub_category_search = value

    def close_all_dropdowns(self):
        self.class_dropdown_open = False
        self.category_dropdown_open = False
        self.sub_category_dropdown_open = False
        self.class_search = ""
        self.category_search = ""
        self.sub_category_search = ""

    def load_companies(self):
        with SessionLocal() as session:
            query = session.query(Company)
            if self.search_query.strip():
                term = f"%{self.search_query.strip()}%"
                query = query.filter(
                    or_(Company.cin.ilike(term), Company.name.ilike(term))
                )
            if self.filter_classes:
                query = query.filter(Company.company_class.in_(self.filter_classes))
            if self.filter_categories:
                query = query.filter(Company.company_type.in_(self.filter_categories))
            if self.filter_sub_categories:
                query = query.filter(Company.sub_category.in_(self.filter_sub_categories))
            rows = query.order_by(Company.id.desc()).all()
            self.companies = [
                {
                    "id": str(r.id),
                    "cin": r.cin,
                    "name": r.name,
                    "class": r.company_class or "-",
                    "category": r.company_type or "-",
                    "sub_category": r.sub_category or "-",
                    "doi": _format_date(r.date_of_incorporation),
                    "email": r.email or "",
                    "address": r.address or "",
                    "roc_code": r.roc_code or "",
                    "roc_office": r.roc_office or "",
                    "rd_name": r.rd_name or "",
                    "rd_region": r.rd_region or "",
                    "registration_number": r.registration_number or "",
                    "authorised_capital": str(r.authorised_capital) if r.authorised_capital is not None else "",
                    "paid_up_capital": str(r.paid_up_capital) if r.paid_up_capital is not None else "",
                    "number_of_members": r.number_of_members or "",
                    "date_of_last_agm": _format_date(r.date_of_last_agm),
                    "date_of_balance_sheet": _format_date(r.date_of_balance_sheet),
                    "listed_status": r.listed_status or "",
                    "suspended_at_stock_exchange": r.suspended_at_stock_exchange or "",
                    "pin_code": r.pin_code or "",
                    "phone": r.phone or "",
                    "country": r.country or "",
                }
                for r in rows
            ]

    def confirm_delete(self, company_id: str):
        if self.role != "ADMIN":
            self.error_message = "Only admins can delete companies."
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
                self.edit_form_doi = c["doi"]
                self.edit_form_email = c["email"]
                self.edit_form_address = c["address"]
                self.edit_form_roc_code = c["roc_code"]
                self.edit_form_roc_office = c["roc_office"]
                self.edit_form_rd_name = c["rd_name"]
                self.edit_form_rd_region = c["rd_region"]
                self.edit_form_registration_number = c["registration_number"]
                self.edit_form_paid_up_capital = c["paid_up_capital"]
                self.edit_form_number_of_members = c["number_of_members"]
                self.edit_form_date_of_last_agm = c["date_of_last_agm"]
                self.edit_form_date_of_balance_sheet = c["date_of_balance_sheet"]
                self.edit_form_listed_status = c["listed_status"]
                self.edit_form_suspended_at_stock_exchange = c["suspended_at_stock_exchange"]
                self.edit_form_pin_code = c["pin_code"]
                self.edit_form_phone = c["phone"]
                self.edit_form_country = c["country"]
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

    def handle_form_doi_change(self, value: str):
        if self.show_add_form:
            m = _ISO_DATE_RE.match(value)
            self.form_doi = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_form_email_change(self, value: str):
        if self.show_add_form:
            self.form_email = value

    def handle_form_address_change(self, value: str):
        if self.show_add_form:
            self.form_address = value

    def handle_form_roc_code_change(self, value: str):
        if self.show_add_form:
            self.form_roc_code = value

    def handle_form_roc_office_change(self, value: str):
        if self.show_add_form:
            self.form_roc_office = value

    def handle_form_rd_name_change(self, value: str):
        if self.show_add_form:
            self.form_rd_name = value

    def handle_form_rd_region_change(self, value: str):
        if self.show_add_form:
            self.form_rd_region = value

    def handle_form_registration_number_change(self, value: str):
        if self.show_add_form:
            self.form_registration_number = value

    def handle_form_authorised_capital_change(self, value):
        if self.show_add_form:
            self.form_authorised_capital = str(value) if value is not None else ""

    def handle_form_paid_up_capital_change(self, value):
        if self.show_add_form:
            self.form_paid_up_capital = str(value) if value is not None else ""

    def handle_form_number_of_members_change(self, value: str):
        if self.show_add_form:
            self.form_number_of_members = value

    def handle_form_date_of_last_agm_change(self, value: str):
        if self.show_add_form:
            m = _ISO_DATE_RE.match(value)
            self.form_date_of_last_agm = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_form_date_of_balance_sheet_change(self, value: str):
        if self.show_add_form:
            m = _ISO_DATE_RE.match(value)
            self.form_date_of_balance_sheet = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_form_listed_status_change(self, value: str):
        if self.show_add_form:
            self.form_listed_status = value

    def handle_form_suspended_change(self, value: str):
        if self.show_add_form:
            self.form_suspended_at_stock_exchange = value

    def handle_form_pin_code_change(self, value: str):
        if self.show_add_form:
            self.form_pin_code = value

    def handle_form_phone_change(self, value: str):
        if self.show_add_form:
            self.form_phone = value

    def handle_form_country_change(self, value: str):
        if self.show_add_form:
            self.form_country = value

    def handle_edit_form_doi_change(self, value: str):
        if self.show_edit_company_form:
            m = _ISO_DATE_RE.match(value)
            self.edit_form_doi = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_edit_form_email_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_email = value

    def handle_edit_form_address_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_address = value

    def handle_edit_form_roc_code_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_roc_code = value

    def handle_edit_form_roc_office_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_roc_office = value

    def handle_edit_form_rd_name_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_rd_name = value

    def handle_edit_form_rd_region_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_rd_region = value

    def handle_edit_form_registration_number_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_registration_number = value

    def handle_edit_form_authorised_capital_change(self, value):
        if self.show_edit_company_form:
            self.edit_form_authorised_capital = str(value) if value is not None else ""

    def handle_edit_form_paid_up_capital_change(self, value):
        if self.show_edit_company_form:
            self.edit_form_paid_up_capital = str(value) if value is not None else ""

    def handle_edit_form_number_of_members_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_number_of_members = value

    def handle_edit_form_date_of_last_agm_change(self, value: str):
        if self.show_edit_company_form:
            m = _ISO_DATE_RE.match(value)
            self.edit_form_date_of_last_agm = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_edit_form_date_of_balance_sheet_change(self, value: str):
        if self.show_edit_company_form:
            m = _ISO_DATE_RE.match(value)
            self.edit_form_date_of_balance_sheet = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_edit_form_listed_status_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_listed_status = value

    def handle_edit_form_suspended_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_suspended_at_stock_exchange = value

    def handle_edit_form_pin_code_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_pin_code = value

    def handle_edit_form_phone_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_phone = value

    def handle_edit_form_country_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_country = value

    def save_edit_company(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.edit_form_error = "You do not have permission to edit companies."
            return
        cin = self.edit_form_cin.strip()
        name = self.edit_form_name.strip()
        company_class = self.edit_form_class.strip()
        company_category = self.edit_form_category.strip()
        company_sub_category = self.edit_form_sub_category.strip()
        doi = self.edit_form_doi.strip()
        email = self.edit_form_email.strip()
        address = self.edit_form_address.strip()
        if not cin or not name or not company_class or not company_category or not company_sub_category:
            self.edit_form_error = "All fields are required."
            return
        if email and not _EMAIL_RE.match(email):
            self.edit_form_error = "Enter a valid email address."
            return
        if doi and not _parse_doi(doi):
            self.edit_form_error = "Invalid date. Use DD/MM/YYYY (e.g. 15/08/2024)."
            return
        extra = {
            "roc_code": self.edit_form_roc_code.strip(),
            "roc_office": self.edit_form_roc_office.strip(),
            "rd_name": self.edit_form_rd_name.strip(),
            "rd_region": self.edit_form_rd_region.strip(),
            "registration_number": self.edit_form_registration_number.strip(),
            "authorised_capital": str(self.edit_form_authorised_capital).strip(),
            "paid_up_capital": str(self.edit_form_paid_up_capital).strip(),
            "number_of_members": self.edit_form_number_of_members.strip(),
            "date_of_last_agm": self.edit_form_date_of_last_agm.strip(),
            "date_of_balance_sheet": self.edit_form_date_of_balance_sheet.strip(),
            "listed_status": self.edit_form_listed_status.strip(),
            "suspended": self.edit_form_suspended_at_stock_exchange.strip(),
            "pin_code": self.edit_form_pin_code.strip(),
            "phone": self.edit_form_phone.strip(),
            "country": self.edit_form_country.strip(),
        }
        cid = self.edit_company_id
        self._clear_edit_company_form()
        self.is_saving = True
        return PortalState.commit_edit_company(
            cid, cin, name, company_class, company_category, company_sub_category,
            doi, email, address,
            extra["roc_code"], extra["roc_office"], extra["rd_name"], extra["rd_region"],
            extra["registration_number"],
            extra["authorised_capital"], extra["paid_up_capital"],
            extra["number_of_members"], extra["date_of_last_agm"],
            extra["date_of_balance_sheet"], extra["listed_status"],
            extra["suspended"], extra["pin_code"], extra["phone"], extra["country"],
        )

    def commit_edit_company(
        self,
        company_id: str,
        cin: str,
        name: str,
        company_class: str,
        company_category: str,
        company_sub_category: str,
        doi: str = "",
        email: str = "",
        address: str = "",
        roc_code: str = "",
        roc_office: str = "",
        rd_name: str = "",
        rd_region: str = "",
        registration_number: str = "",
        authorised_capital: str = "",
        paid_up_capital: str = "",
        number_of_members: str = "",
        date_of_last_agm: str = "",
        date_of_balance_sheet: str = "",
        listed_status: str = "",
        suspended: str = "",
        pin_code: str = "",
        phone: str = "",
        country: str = "",
    ):
        try:
            cid = int(company_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid company ID '{company_id}'."
            self.is_saving = False
            return
        def _cap(v): return float(v) if v else None
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
                company.date_of_incorporation = doi or None
                company.email = email or None
                company.address = address or None
                company.roc_code = roc_code or None
                company.roc_office = roc_office or None
                company.rd_name = rd_name or None
                company.rd_region = rd_region or None
                company.registration_number = registration_number or None
                company.authorised_capital = _cap(authorised_capital)
                company.paid_up_capital = _cap(paid_up_capital)
                company.number_of_members = number_of_members or None
                company.date_of_last_agm = date_of_last_agm or None
                company.date_of_balance_sheet = date_of_balance_sheet or None
                company.listed_status = listed_status or None
                company.suspended_at_stock_exchange = suspended or None
                company.pin_code = pin_code or None
                company.phone = phone or None
                company.country = country or None
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
        doi = self.form_doi.strip()
        email = self.form_email.strip()
        address = self.form_address.strip()

        if not cin or not name or not company_class or not company_category or not company_sub_category:
            self.form_error = "All fields are required."
            return
        if email and not _EMAIL_RE.match(email):
            self.form_error = "Enter a valid email address."
            return
        if doi and not _parse_doi(doi):
            self.form_error = "Invalid date. Use DD/MM/YYYY (e.g. 15/08/2024)."
            return

        extra = {
            "roc_code": self.form_roc_code.strip(),
            "roc_office": self.form_roc_office.strip(),
            "rd_name": self.form_rd_name.strip(),
            "rd_region": self.form_rd_region.strip(),
            "registration_number": self.form_registration_number.strip(),
            "authorised_capital": str(self.form_authorised_capital).strip(),
            "paid_up_capital": str(self.form_paid_up_capital).strip(),
            "number_of_members": self.form_number_of_members.strip(),
            "date_of_last_agm": self.form_date_of_last_agm.strip(),
            "date_of_balance_sheet": self.form_date_of_balance_sheet.strip(),
            "listed_status": self.form_listed_status.strip(),
            "suspended": self.form_suspended_at_stock_exchange.strip(),
            "pin_code": self.form_pin_code.strip(),
            "phone": self.form_phone.strip(),
            "country": self.form_country.strip(),
        }
        self._clear_form()
        self.is_saving = True
        return PortalState.commit_save(
            cin, name, company_class, company_category, company_sub_category,
            doi, email, address,
            extra["roc_code"], extra["roc_office"], extra["rd_name"], extra["rd_region"],
            extra["registration_number"],
            extra["authorised_capital"], extra["paid_up_capital"],
            extra["number_of_members"], extra["date_of_last_agm"],
            extra["date_of_balance_sheet"], extra["listed_status"],
            extra["suspended"], extra["pin_code"], extra["phone"], extra["country"],
        )

    def commit_save(
        self,
        cin: str,
        name: str,
        company_class: str,
        company_category: str,
        company_sub_category: str,
        doi: str = "",
        email: str = "",
        address: str = "",
        roc_code: str = "",
        roc_office: str = "",
        rd_name: str = "",
        rd_region: str = "",
        registration_number: str = "",
        authorised_capital: str = "",
        paid_up_capital: str = "",
        number_of_members: str = "",
        date_of_last_agm: str = "",
        date_of_balance_sheet: str = "",
        listed_status: str = "",
        suspended: str = "",
        pin_code: str = "",
        phone: str = "",
        country: str = "",
    ):
        """Second hop: DB insert + table refresh."""
        def _cap(v): return float(v) if v else None
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
                    date_of_incorporation=doi or None,
                    email=email or None,
                    address=address or None,
                    roc_code=roc_code or None,
                    roc_office=roc_office or None,
                    rd_name=rd_name or None,
                    rd_region=rd_region or None,
                    registration_number=registration_number or None,
                    authorised_capital=_cap(authorised_capital),
                    paid_up_capital=_cap(paid_up_capital),
                    number_of_members=number_of_members or None,
                    date_of_last_agm=date_of_last_agm or None,
                    date_of_balance_sheet=date_of_balance_sheet or None,
                    listed_status=listed_status or None,
                    suspended_at_stock_exchange=suspended or None,
                    pin_code=pin_code or None,
                    phone=phone or None,
                    country=country or None,
                )
            )
            session.commit()
        self.is_saving = False
        self.load_companies()

    # ── User management ───────────────────────────────────────────────────────

    def switch_tab(self, tab: str):
        self.active_tab = tab
        self.error_message = ""
        if tab == "directors":
            self.load_directors()
        if tab == "llps":
            self.load_llps()
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

    # ── Directors ────────────────────────────────────────────────────────────

    def load_directors(self):
        with SessionLocal() as session:
            query = session.query(Director)
            if self.directors_search_query.strip():
                term = f"%{self.directors_search_query.strip()}%"
                query = query.filter(
                    or_(Director.din.ilike(term), Director.name.ilike(term))
                )
            rows = query.order_by(Director.id.desc()).all()
            self.directors = [
                {
                    "id": str(r.id),
                    "din": r.din,
                    "name": r.name,
                    "email": r.email or "",
                    "phone": r.phone or "",
                    "status": r.status,
                }
                for r in rows
            ]

    def handle_directors_search(self, value: str):
        self.directors_search_query = value
        self.load_directors()

    def handle_form_din_change(self, value: str):
        if self.show_add_director_form:
            self.form_din = value

    def handle_form_director_name_change(self, value: str):
        if self.show_add_director_form:
            self.form_director_name = value

    def handle_form_director_email_change(self, value: str):
        if self.show_add_director_form:
            self.form_director_email = value

    def handle_form_director_phone_change(self, value: str):
        if self.show_add_director_form:
            self.form_director_phone = value

    def open_add_director_form(self):
        self._clear_director_form()
        self.show_add_director_form = True

    def close_add_director_form(self):
        self._clear_director_form()

    def save_director(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.form_director_error = "You do not have permission to add directors."
            return
        din = self.form_din.strip()
        name = self.form_director_name.strip()
        email = self.form_director_email.strip()
        phone = self.form_director_phone.strip()
        if not din or not name:
            self.form_director_error = "DIN and Name are required."
            return
        if email and not _EMAIL_RE.match(email):
            self.form_director_error = "Enter a valid email address."
            return
        self._clear_director_form()
        self.is_saving = True
        return PortalState.commit_save_director(din, name, email, phone)

    def commit_save_director(self, din: str, name: str, email: str = "", phone: str = ""):
        with SessionLocal() as session:
            if session.query(Director).filter(Director.din == din).first():
                self.error_message = f"A director with DIN '{din}' already exists."
                self.is_saving = False
                return
            session.add(Director(din=din, name=name, email=email or None, phone=phone or None))
            session.commit()
        self.is_saving = False
        self.load_directors()

    def open_edit_director_form(self, director_id: str):
        self._clear_edit_director_form()
        self.edit_director_id = director_id
        for d in self.directors:
            if d["id"] == director_id:
                self.edit_form_din = d["din"]
                self.edit_form_director_name = d["name"]
                self.edit_form_director_email = d["email"]
                self.edit_form_director_phone = d["phone"]
                break
        self.show_edit_director_form = True

    def close_edit_director_form(self):
        self._clear_edit_director_form()

    def handle_edit_form_din_change(self, value: str):
        if self.show_edit_director_form:
            self.edit_form_din = value

    def handle_edit_form_director_name_change(self, value: str):
        if self.show_edit_director_form:
            self.edit_form_director_name = value

    def handle_edit_form_director_email_change(self, value: str):
        if self.show_edit_director_form:
            self.edit_form_director_email = value

    def handle_edit_form_director_phone_change(self, value: str):
        if self.show_edit_director_form:
            self.edit_form_director_phone = value

    def save_edit_director(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.edit_form_director_error = "You do not have permission to edit directors."
            return
        din = self.edit_form_din.strip()
        name = self.edit_form_director_name.strip()
        email = self.edit_form_director_email.strip()
        phone = self.edit_form_director_phone.strip()
        if not din or not name:
            self.edit_form_director_error = "DIN and Name are required."
            return
        if email and not _EMAIL_RE.match(email):
            self.edit_form_director_error = "Enter a valid email address."
            return
        did = self.edit_director_id
        self._clear_edit_director_form()
        self.is_saving = True
        return PortalState.commit_edit_director(did, din, name, email, phone)

    def commit_edit_director(self, director_id: str, din: str, name: str, email: str = "", phone: str = ""):
        try:
            did = int(director_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid director ID '{director_id}'."
            self.is_saving = False
            return
        with SessionLocal() as session:
            existing = session.query(Director).filter(Director.din == din, Director.id != did).first()
            if existing:
                self.error_message = f"Another director with DIN '{din}' already exists."
                self.is_saving = False
                return
            director = session.query(Director).filter(Director.id == did).first()
            if director:
                director.din = din
                director.name = name
                director.email = email or None
                director.phone = phone or None
                session.commit()
        self.is_saving = False
        self.load_directors()

    def confirm_delete_director(self, director_id: str):
        if self.role != "ADMIN":
            self.error_message = "Only admins can delete directors."
            return
        try:
            did = int(director_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid director ID '{director_id}'."
            return
        with SessionLocal() as session:
            director = session.query(Director).filter(Director.id == did).first()
            if director:
                session.delete(director)
                session.commit()
        self.load_directors()

    # ── Company-Director associations ────────────────────────────────────────

    def _load_company_directors(self):
        try:
            cid = int(self.managing_company_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            rows = (
                session.query(CompanyDirector, Director)
                .join(Director, CompanyDirector.director_id == Director.id)
                .filter(CompanyDirector.company_id == cid)
                .all()
            )
            self.company_directors = [
                {
                    "assoc_id": str(cd.id),
                    "director_id": str(d.id),
                    "din": d.din,
                    "name": d.name,
                    "share_percent": str(cd.share_percent) if cd.share_percent is not None else "",
                    "designation": cd.designation or "",
                    "category": cd.category or "",
                    "original_appointment_date": _format_date(cd.original_appointment_date),
                    "current_designation_date": _format_date(cd.current_designation_date),
                    "cessation_date": _format_date(cd.cessation_date),
                }
                for cd, d in rows
            ]

    def open_manage_directors(self, company_id: str):
        self._clear_manage_directors()
        self.managing_company_id = company_id
        for c in self.companies:
            if c["id"] == company_id:
                self.managing_company_name = c["name"]
                break
        self.show_manage_directors = True
        self._load_company_directors()

    def close_manage_directors(self):
        self._clear_manage_directors()

    def handle_assoc_search(self, value: str):
        self.assoc_search_query = value
        self.assoc_selected_director_id = ""
        self.assoc_selected_director_name = ""
        if not value.strip():
            self.assoc_search_results = []
            return
        with SessionLocal() as session:
            term = f"%{value.strip()}%"
            rows = (
                session.query(Director)
                .filter(or_(Director.din.ilike(term), Director.name.ilike(term)))
                .limit(8)
                .all()
            )
            self.assoc_search_results = [
                {"id": str(r.id), "din": r.din, "name": r.name}
                for r in rows
            ]

    def select_director_for_assoc(self, director_id: str):
        self.assoc_selected_director_id = director_id
        self.assoc_search_results = []
        try:
            did = int(director_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            d = session.query(Director).filter(Director.id == did).first()
            if d:
                self.assoc_selected_director_name = f"{d.name}  (DIN: {d.din})"
                self.assoc_search_query = d.name

    def handle_assoc_share_change(self, value):  # noqa: override with untyped to avoid Reflex coercion
        self.assoc_share_percent = str(value) if value is not None else ""

    def handle_assoc_designation_change(self, value: str):
        self.assoc_designation = value

    def handle_assoc_category_change(self, value: str):
        self.assoc_category = value

    def handle_assoc_original_appointment_date_change(self, value: str):
        m = _ISO_DATE_RE.match(value)
        self.assoc_original_appointment_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_assoc_current_designation_date_change(self, value: str):
        m = _ISO_DATE_RE.match(value)
        self.assoc_current_designation_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_assoc_cessation_date_change(self, value: str):
        m = _ISO_DATE_RE.match(value)
        self.assoc_cessation_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def _validate_assoc_form(self) -> tuple[float | None, str] | None:
        """Shared validation for add/edit association forms.

        Returns (share_val, designation) on success, or None (setting
        self.assoc_error) on failure.
        """
        share_str = str(self.assoc_share_percent).strip()
        if not share_str:
            self.assoc_error = "Share percentage is required."
            return None
        try:
            share_val = float(share_str)
            if share_val <= 0 or share_val > 100:
                self.assoc_error = "Share percentage must be greater than 0 and at most 100."
                return None
        except ValueError:
            self.assoc_error = "Share percentage must be a number."
            return None
        if not self.assoc_designation.strip():
            self.assoc_error = "Designation is required."
            return None
        for label, value in (
            ("Original Date of Appointment", self.assoc_original_appointment_date),
            ("Date of Appointment at Current Designation", self.assoc_current_designation_date),
            ("Date of Cessation", self.assoc_cessation_date),
        ):
            if value.strip() and not _parse_doi(value.strip()):
                self.assoc_error = f"{label}: invalid date. Use DD/MM/YYYY."
                return None
        return share_val

    def add_director_to_company(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.assoc_error = "You do not have permission."
            return
        if self.assoc_editing_id:
            return self.save_association_edit()
        if not self.assoc_selected_director_id:
            self.assoc_error = "Please select a director from the search results."
            return
        share_val = self._validate_assoc_form()
        if share_val is None:
            return
        self.assoc_error = ""
        cid = self.managing_company_id
        did = self.assoc_selected_director_id
        designation = self.assoc_designation.strip()
        category = self.assoc_category.strip()
        original_appointment_date = self.assoc_original_appointment_date.strip()
        current_designation_date = self.assoc_current_designation_date.strip()
        cessation_date = self.assoc_cessation_date.strip()
        self.is_saving = True
        return PortalState.commit_add_director_to_company(
            cid, did, str(share_val), designation, category,
            original_appointment_date, current_designation_date, cessation_date,
        )

    def commit_add_director_to_company(
        self,
        company_id: str,
        director_id: str,
        share_str: str,
        designation: str = "",
        category: str = "",
        original_appointment_date: str = "",
        current_designation_date: str = "",
        cessation_date: str = "",
    ):
        try:
            cid = int(company_id)
            did = int(director_id)
        except (ValueError, TypeError):
            self.is_saving = False
            return
        share_val = float(share_str) if share_str else None
        with SessionLocal() as session:
            existing = session.query(CompanyDirector).filter(
                CompanyDirector.company_id == cid,
                CompanyDirector.director_id == did,
            ).first()
            if existing:
                self.assoc_error = "This director is already associated with this company."
                self.is_saving = False
                return
            if share_val is not None:
                current_total = session.query(func.sum(CompanyDirector.share_percent)).filter(
                    CompanyDirector.company_id == cid,
                    CompanyDirector.share_percent.isnot(None),
                ).scalar() or 0.0
                if current_total + share_val > 100:
                    self.assoc_error = f"Total share would exceed 100% (current total: {current_total:.2f}%)."
                    self.is_saving = False
                    return
            session.add(
                CompanyDirector(
                    company_id=cid,
                    director_id=did,
                    share_percent=share_val,
                    designation=designation or None,
                    category=category or None,
                    original_appointment_date=original_appointment_date or None,
                    current_designation_date=current_designation_date or None,
                    cessation_date=cessation_date or None,
                )
            )
            session.commit()
        self.assoc_share_percent = ""
        self.assoc_designation = ""
        self.assoc_category = ""
        self.assoc_original_appointment_date = ""
        self.assoc_current_designation_date = ""
        self.assoc_cessation_date = ""
        self.assoc_error = ""
        self.is_saving = False
        self._load_company_directors()

    def start_edit_association(self, assoc_id: str):
        for d in self.company_directors:
            if d["assoc_id"] == assoc_id:
                self.assoc_editing_id = assoc_id
                self.assoc_selected_director_id = d["director_id"]
                self.assoc_selected_director_name = f"{d['name']}  (DIN: {d['din']})"
                self.assoc_search_query = ""
                self.assoc_search_results = []
                self.assoc_share_percent = d["share_percent"]
                self.assoc_designation = d["designation"]
                self.assoc_category = d["category"]
                self.assoc_original_appointment_date = d["original_appointment_date"]
                self.assoc_current_designation_date = d["current_designation_date"]
                self.assoc_cessation_date = d["cessation_date"]
                self.assoc_error = ""
                break

    def cancel_edit_association(self):
        self.assoc_editing_id = ""
        self.assoc_selected_director_id = ""
        self.assoc_selected_director_name = ""
        self.assoc_search_query = ""
        self.assoc_search_results = []
        self.assoc_share_percent = ""
        self.assoc_designation = ""
        self.assoc_category = ""
        self.assoc_original_appointment_date = ""
        self.assoc_current_designation_date = ""
        self.assoc_cessation_date = ""
        self.assoc_error = ""

    def save_association_edit(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.assoc_error = "You do not have permission."
            return
        share_val = self._validate_assoc_form()
        if share_val is None:
            return
        self.assoc_error = ""
        aid = self.assoc_editing_id
        designation = self.assoc_designation.strip()
        category = self.assoc_category.strip()
        original_appointment_date = self.assoc_original_appointment_date.strip()
        current_designation_date = self.assoc_current_designation_date.strip()
        cessation_date = self.assoc_cessation_date.strip()
        self.is_saving = True
        return PortalState.commit_edit_association(
            aid, str(share_val), designation, category,
            original_appointment_date, current_designation_date, cessation_date,
        )

    def commit_edit_association(
        self,
        assoc_id: str,
        share_str: str,
        designation: str = "",
        category: str = "",
        original_appointment_date: str = "",
        current_designation_date: str = "",
        cessation_date: str = "",
    ):
        try:
            aid = int(assoc_id)
        except (ValueError, TypeError):
            self.is_saving = False
            return
        share_val = float(share_str) if share_str else None
        with SessionLocal() as session:
            assoc = session.query(CompanyDirector).filter(CompanyDirector.id == aid).first()
            if not assoc:
                self.is_saving = False
                return
            if share_val is not None:
                current_total = session.query(func.sum(CompanyDirector.share_percent)).filter(
                    CompanyDirector.company_id == assoc.company_id,
                    CompanyDirector.share_percent.isnot(None),
                    CompanyDirector.id != aid,
                ).scalar() or 0.0
                if current_total + share_val > 100:
                    self.assoc_error = f"Total share would exceed 100% (current total: {current_total:.2f}%)."
                    self.is_saving = False
                    return
            assoc.share_percent = share_val
            assoc.designation = designation or None
            assoc.category = category or None
            assoc.original_appointment_date = original_appointment_date or None
            assoc.current_designation_date = current_designation_date or None
            assoc.cessation_date = cessation_date or None
            session.commit()
        self.cancel_edit_association()
        self.is_saving = False
        self._load_company_directors()

    def prompt_remove_director(self, assoc_id: str):
        self.confirm_remove_assoc_id = assoc_id

    def cancel_remove_director(self):
        self.confirm_remove_assoc_id = ""

    def remove_director_from_company(self, assoc_id: str):
        if self.role not in ("ADMIN", "EDITOR"):
            self.assoc_error = "You do not have permission."
            return
        self.confirm_remove_assoc_id = ""
        if self.assoc_editing_id == assoc_id:
            self.cancel_edit_association()
        try:
            aid = int(assoc_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            assoc = session.query(CompanyDirector).filter(CompanyDirector.id == aid).first()
            if assoc:
                session.delete(assoc)
                session.commit()
        self._load_company_directors()

    # ── LLPs ─────────────────────────────────────────────────────────────────

    def load_llps(self):
        with SessionLocal() as session:
            query = session.query(LLP)
            if self.llps_search_query.strip():
                term = f"%{self.llps_search_query.strip()}%"
                query = query.filter(or_(LLP.llpin.ilike(term), LLP.name.ilike(term)))
            rows = query.order_by(LLP.id.desc()).all()
            self.llps = [
                {
                    "id": str(r.id),
                    "llpin": r.llpin,
                    "name": r.name,
                    "status": r.status,
                    "roc_name": r.roc_name or "",
                    "doi": _format_date(r.date_of_incorporation),
                    "email": r.email or "",
                    "address": r.address or "",
                    "number_of_partners": r.number_of_partners or "",
                    "number_of_designated_partners": r.number_of_designated_partners or "",
                    "total_obligation": str(r.total_obligation_of_contribution) if r.total_obligation_of_contribution is not None else "",
                    "strike_off_date": _format_date(r.strike_off_date),
                    "status_under_cirp": r.status_under_cirp or "",
                    "small_llp": r.small_llp or "",
                }
                for r in rows
            ]

    def handle_llps_search(self, value: str):
        self.llps_search_query = value
        self.load_llps()

    def confirm_delete_llp(self, llp_id: str):
        if self.role != "ADMIN":
            self.error_message = "Only admins can delete LLPs."
            return
        try:
            lid = int(llp_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid LLP ID '{llp_id}'."
            return
        with SessionLocal() as session:
            llp = session.query(LLP).filter(LLP.id == lid).first()
            if llp:
                session.delete(llp)
                session.commit()
        self.load_llps()

    # ── Add-LLP form handlers ───────────────────────────────────────────────

    def open_add_llp_form(self):
        self._clear_llp_form()
        self.show_add_llp_form = True

    def close_add_llp_form(self):
        self._clear_llp_form()

    def handle_form_llpin_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llpin = value

    def handle_form_llp_name_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_name = value

    def handle_form_llp_roc_name_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_roc_name = value

    def handle_form_llp_doi_change(self, value: str):
        if self.show_add_llp_form:
            m = _ISO_DATE_RE.match(value)
            self.form_llp_doi = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_form_llp_email_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_email = value

    def handle_form_llp_address_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_address = value

    def handle_form_llp_number_of_partners_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_number_of_partners = value

    def handle_form_llp_number_of_designated_partners_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_number_of_designated_partners = value

    def handle_form_llp_total_obligation_change(self, value):
        if self.show_add_llp_form:
            self.form_llp_total_obligation = str(value) if value is not None else ""

    def handle_form_llp_strike_off_date_change(self, value: str):
        if self.show_add_llp_form:
            m = _ISO_DATE_RE.match(value)
            self.form_llp_strike_off_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_form_llp_status_under_cirp_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_status_under_cirp = value

    def handle_form_llp_small_llp_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_small_llp = value

    def save_llp(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.form_llp_error = "You do not have permission to add LLPs."
            return
        llpin = self.form_llpin.strip()
        name = self.form_llp_name.strip()
        if not llpin or not name:
            self.form_llp_error = "LLPIN and Name are required."
            return
        email = self.form_llp_email.strip()
        if email and not _EMAIL_RE.match(email):
            self.form_llp_error = "Enter a valid email address."
            return
        doi = self.form_llp_doi.strip()
        if doi and not _parse_doi(doi):
            self.form_llp_error = "Invalid date of incorporation. Use DD/MM/YYYY."
            return
        strike_off_date = self.form_llp_strike_off_date.strip()
        if strike_off_date and not _parse_doi(strike_off_date):
            self.form_llp_error = "Invalid strike-off date. Use DD/MM/YYYY."
            return
        extra = {
            "roc_name": self.form_llp_roc_name.strip(),
            "address": self.form_llp_address.strip(),
            "number_of_partners": self.form_llp_number_of_partners.strip(),
            "number_of_designated_partners": self.form_llp_number_of_designated_partners.strip(),
            "total_obligation": str(self.form_llp_total_obligation).strip(),
            "status_under_cirp": self.form_llp_status_under_cirp.strip(),
            "small_llp": self.form_llp_small_llp.strip(),
        }
        self._clear_llp_form()
        self.is_saving = True
        return PortalState.commit_save_llp(
            llpin, name, extra["roc_name"], doi, email, extra["address"],
            extra["number_of_partners"], extra["number_of_designated_partners"],
            extra["total_obligation"], strike_off_date,
            extra["status_under_cirp"], extra["small_llp"],
        )

    def commit_save_llp(
        self, llpin: str, name: str, roc_name: str = "", doi: str = "", email: str = "",
        address: str = "", number_of_partners: str = "", number_of_designated_partners: str = "",
        total_obligation: str = "", strike_off_date: str = "",
        status_under_cirp: str = "", small_llp: str = "",
    ):
        def _num(v): return float(v) if v else None
        with SessionLocal() as session:
            if session.query(LLP).filter(LLP.llpin == llpin).first():
                self.error_message = f"An LLP with LLPIN '{llpin}' already exists."
                self.is_saving = False
                return
            session.add(
                LLP(
                    llpin=llpin,
                    name=name,
                    roc_name=roc_name or None,
                    date_of_incorporation=doi or None,
                    email=email or None,
                    address=address or None,
                    number_of_partners=number_of_partners or None,
                    number_of_designated_partners=number_of_designated_partners or None,
                    total_obligation_of_contribution=_num(total_obligation),
                    strike_off_date=strike_off_date or None,
                    status_under_cirp=status_under_cirp or None,
                    small_llp=small_llp or None,
                )
            )
            session.commit()
        self.is_saving = False
        self.load_llps()

    # ── Edit-LLP form handlers ──────────────────────────────────────────────

    def open_edit_llp_form(self, llp_id: str):
        self._clear_edit_llp_form()
        self.edit_llp_id = llp_id
        for l in self.llps:
            if l["id"] == llp_id:
                self.edit_form_llpin = l["llpin"]
                self.edit_form_llp_name = l["name"]
                self.edit_form_llp_roc_name = l["roc_name"]
                self.edit_form_llp_doi = l["doi"]
                self.edit_form_llp_email = l["email"]
                self.edit_form_llp_address = l["address"]
                self.edit_form_llp_number_of_partners = l["number_of_partners"]
                self.edit_form_llp_number_of_designated_partners = l["number_of_designated_partners"]
                self.edit_form_llp_total_obligation = l["total_obligation"]
                self.edit_form_llp_strike_off_date = l["strike_off_date"]
                self.edit_form_llp_status_under_cirp = l["status_under_cirp"]
                self.edit_form_llp_small_llp = l["small_llp"]
                break
        self.show_edit_llp_form = True

    def close_edit_llp_form(self):
        self._clear_edit_llp_form()

    def handle_edit_form_llpin_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llpin = value

    def handle_edit_form_llp_name_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_name = value

    def handle_edit_form_llp_roc_name_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_roc_name = value

    def handle_edit_form_llp_doi_change(self, value: str):
        if self.show_edit_llp_form:
            m = _ISO_DATE_RE.match(value)
            self.edit_form_llp_doi = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_edit_form_llp_email_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_email = value

    def handle_edit_form_llp_address_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_address = value

    def handle_edit_form_llp_number_of_partners_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_number_of_partners = value

    def handle_edit_form_llp_number_of_designated_partners_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_number_of_designated_partners = value

    def handle_edit_form_llp_total_obligation_change(self, value):
        if self.show_edit_llp_form:
            self.edit_form_llp_total_obligation = str(value) if value is not None else ""

    def handle_edit_form_llp_strike_off_date_change(self, value: str):
        if self.show_edit_llp_form:
            m = _ISO_DATE_RE.match(value)
            self.edit_form_llp_strike_off_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_edit_form_llp_status_under_cirp_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_status_under_cirp = value

    def handle_edit_form_llp_small_llp_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_small_llp = value

    def save_edit_llp(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.edit_form_llp_error = "You do not have permission to edit LLPs."
            return
        llpin = self.edit_form_llpin.strip()
        name = self.edit_form_llp_name.strip()
        if not llpin or not name:
            self.edit_form_llp_error = "LLPIN and Name are required."
            return
        email = self.edit_form_llp_email.strip()
        if email and not _EMAIL_RE.match(email):
            self.edit_form_llp_error = "Enter a valid email address."
            return
        doi = self.edit_form_llp_doi.strip()
        if doi and not _parse_doi(doi):
            self.edit_form_llp_error = "Invalid date of incorporation. Use DD/MM/YYYY."
            return
        strike_off_date = self.edit_form_llp_strike_off_date.strip()
        if strike_off_date and not _parse_doi(strike_off_date):
            self.edit_form_llp_error = "Invalid strike-off date. Use DD/MM/YYYY."
            return
        lid = self.edit_llp_id
        extra = {
            "roc_name": self.edit_form_llp_roc_name.strip(),
            "address": self.edit_form_llp_address.strip(),
            "number_of_partners": self.edit_form_llp_number_of_partners.strip(),
            "number_of_designated_partners": self.edit_form_llp_number_of_designated_partners.strip(),
            "total_obligation": str(self.edit_form_llp_total_obligation).strip(),
            "status_under_cirp": self.edit_form_llp_status_under_cirp.strip(),
            "small_llp": self.edit_form_llp_small_llp.strip(),
        }
        self._clear_edit_llp_form()
        self.is_saving = True
        return PortalState.commit_edit_llp(
            lid, llpin, name, extra["roc_name"], doi, email, extra["address"],
            extra["number_of_partners"], extra["number_of_designated_partners"],
            extra["total_obligation"], strike_off_date,
            extra["status_under_cirp"], extra["small_llp"],
        )

    def commit_edit_llp(
        self, llp_id: str, llpin: str, name: str, roc_name: str = "", doi: str = "", email: str = "",
        address: str = "", number_of_partners: str = "", number_of_designated_partners: str = "",
        total_obligation: str = "", strike_off_date: str = "",
        status_under_cirp: str = "", small_llp: str = "",
    ):
        try:
            lid = int(llp_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid LLP ID '{llp_id}'."
            self.is_saving = False
            return
        def _num(v): return float(v) if v else None
        with SessionLocal() as session:
            existing = session.query(LLP).filter(LLP.llpin == llpin, LLP.id != lid).first()
            if existing:
                self.error_message = f"Another LLP with LLPIN '{llpin}' already exists."
                self.is_saving = False
                return
            llp = session.query(LLP).filter(LLP.id == lid).first()
            if llp:
                llp.llpin = llpin
                llp.name = name
                llp.roc_name = roc_name or None
                llp.date_of_incorporation = doi or None
                llp.email = email or None
                llp.address = address or None
                llp.number_of_partners = number_of_partners or None
                llp.number_of_designated_partners = number_of_designated_partners or None
                llp.total_obligation_of_contribution = _num(total_obligation)
                llp.strike_off_date = strike_off_date or None
                llp.status_under_cirp = status_under_cirp or None
                llp.small_llp = small_llp or None
                session.commit()
        self.is_saving = False
        self.load_llps()

    # ── LLP ↔ Director (designated partner) associations ──────────────────────

    def _load_llp_partners(self):
        try:
            lid = int(self.managing_llp_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            rows = (
                session.query(LLPDirector, Director)
                .join(Director, LLPDirector.director_id == Director.id)
                .filter(LLPDirector.llp_id == lid)
                .all()
            )
            self.llp_partners = [
                {
                    "assoc_id": str(ld.id),
                    "director_id": str(d.id),
                    "din": d.din,
                    "name": d.name,
                    "designation": ld.designation or "",
                    "appointment_date": _format_date(ld.appointment_date),
                    "cessation_date": _format_date(ld.cessation_date),
                    "is_signatory": ld.is_signatory or "",
                }
                for ld, d in rows
            ]

    def open_manage_llp_partners(self, llp_id: str):
        self._clear_manage_llp_partners()
        self.managing_llp_id = llp_id
        for l in self.llps:
            if l["id"] == llp_id:
                self.managing_llp_name = l["name"]
                break
        self.show_manage_llp_partners = True
        self._load_llp_partners()

    def close_manage_llp_partners(self):
        self._clear_manage_llp_partners()

    def handle_llp_partner_search(self, value: str):
        self.llp_partner_search_query = value
        self.llp_partner_selected_director_id = ""
        self.llp_partner_selected_director_name = ""
        if not value.strip():
            self.llp_partner_search_results = []
            return
        with SessionLocal() as session:
            term = f"%{value.strip()}%"
            rows = (
                session.query(Director)
                .filter(or_(Director.din.ilike(term), Director.name.ilike(term)))
                .limit(8)
                .all()
            )
            self.llp_partner_search_results = [
                {"id": str(r.id), "din": r.din, "name": r.name} for r in rows
            ]

    def select_director_for_llp_partner(self, director_id: str):
        self.llp_partner_selected_director_id = director_id
        self.llp_partner_search_results = []
        try:
            did = int(director_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            d = session.query(Director).filter(Director.id == did).first()
            if d:
                self.llp_partner_selected_director_name = f"{d.name}  (DIN: {d.din})"
                self.llp_partner_search_query = d.name

    def handle_llp_partner_designation_change(self, value: str):
        self.llp_partner_designation = value

    def handle_llp_partner_appointment_date_change(self, value: str):
        m = _ISO_DATE_RE.match(value)
        self.llp_partner_appointment_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_llp_partner_cessation_date_change(self, value: str):
        m = _ISO_DATE_RE.match(value)
        self.llp_partner_cessation_date = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else value

    def handle_llp_partner_is_signatory_change(self, value: str):
        self.llp_partner_is_signatory = value

    def _validate_llp_partner_form(self) -> bool:
        if not self.llp_partner_designation.strip():
            self.llp_partner_error = "Designation is required."
            return False
        for label, value in (
            ("Date of Appointment", self.llp_partner_appointment_date),
            ("Cessation Date", self.llp_partner_cessation_date),
        ):
            if value.strip() and not _parse_doi(value.strip()):
                self.llp_partner_error = f"{label}: invalid date. Use DD/MM/YYYY."
                return False
        return True

    def add_director_to_llp(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.llp_partner_error = "You do not have permission."
            return
        if self.llp_partner_editing_id:
            return self.save_llp_partner_edit()
        if not self.llp_partner_selected_director_id:
            self.llp_partner_error = "Please select a director from the search results."
            return
        if not self._validate_llp_partner_form():
            return
        self.llp_partner_error = ""
        lid = self.managing_llp_id
        did = self.llp_partner_selected_director_id
        designation = self.llp_partner_designation.strip()
        appointment_date = self.llp_partner_appointment_date.strip()
        cessation_date = self.llp_partner_cessation_date.strip()
        is_signatory = self.llp_partner_is_signatory.strip()
        self.is_saving = True
        return PortalState.commit_add_director_to_llp(
            lid, did, designation, appointment_date, cessation_date, is_signatory,
        )

    def commit_add_director_to_llp(
        self, llp_id: str, director_id: str, designation: str = "",
        appointment_date: str = "", cessation_date: str = "", is_signatory: str = "",
    ):
        try:
            lid = int(llp_id)
            did = int(director_id)
        except (ValueError, TypeError):
            self.is_saving = False
            return
        with SessionLocal() as session:
            existing = session.query(LLPDirector).filter(
                LLPDirector.llp_id == lid, LLPDirector.director_id == did,
            ).first()
            if existing:
                self.llp_partner_error = "This director is already a designated partner of this LLP."
                self.is_saving = False
                return
            session.add(
                LLPDirector(
                    llp_id=lid,
                    director_id=did,
                    designation=designation or None,
                    appointment_date=appointment_date or None,
                    cessation_date=cessation_date or None,
                    is_signatory=is_signatory or None,
                )
            )
            session.commit()
        self.llp_partner_designation = ""
        self.llp_partner_appointment_date = ""
        self.llp_partner_cessation_date = ""
        self.llp_partner_is_signatory = ""
        self.llp_partner_error = ""
        self.is_saving = False
        self._load_llp_partners()

    def start_edit_llp_partner(self, assoc_id: str):
        for d in self.llp_partners:
            if d["assoc_id"] == assoc_id:
                self.llp_partner_editing_id = assoc_id
                self.llp_partner_selected_director_id = d["director_id"]
                self.llp_partner_selected_director_name = f"{d['name']}  (DIN: {d['din']})"
                self.llp_partner_search_query = ""
                self.llp_partner_search_results = []
                self.llp_partner_designation = d["designation"]
                self.llp_partner_appointment_date = d["appointment_date"]
                self.llp_partner_cessation_date = d["cessation_date"]
                self.llp_partner_is_signatory = d["is_signatory"]
                self.llp_partner_error = ""
                break

    def cancel_edit_llp_partner(self):
        self.llp_partner_editing_id = ""
        self.llp_partner_selected_director_id = ""
        self.llp_partner_selected_director_name = ""
        self.llp_partner_search_query = ""
        self.llp_partner_search_results = []
        self.llp_partner_designation = ""
        self.llp_partner_appointment_date = ""
        self.llp_partner_cessation_date = ""
        self.llp_partner_is_signatory = ""
        self.llp_partner_error = ""

    def save_llp_partner_edit(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.llp_partner_error = "You do not have permission."
            return
        if not self._validate_llp_partner_form():
            return
        self.llp_partner_error = ""
        aid = self.llp_partner_editing_id
        designation = self.llp_partner_designation.strip()
        appointment_date = self.llp_partner_appointment_date.strip()
        cessation_date = self.llp_partner_cessation_date.strip()
        is_signatory = self.llp_partner_is_signatory.strip()
        self.is_saving = True
        return PortalState.commit_edit_llp_partner(
            aid, designation, appointment_date, cessation_date, is_signatory,
        )

    def commit_edit_llp_partner(
        self, assoc_id: str, designation: str = "",
        appointment_date: str = "", cessation_date: str = "", is_signatory: str = "",
    ):
        try:
            aid = int(assoc_id)
        except (ValueError, TypeError):
            self.is_saving = False
            return
        with SessionLocal() as session:
            assoc = session.query(LLPDirector).filter(LLPDirector.id == aid).first()
            if not assoc:
                self.is_saving = False
                return
            assoc.designation = designation or None
            assoc.appointment_date = appointment_date or None
            assoc.cessation_date = cessation_date or None
            assoc.is_signatory = is_signatory or None
            session.commit()
        self.cancel_edit_llp_partner()
        self.is_saving = False
        self._load_llp_partners()

    def prompt_remove_llp_partner(self, assoc_id: str):
        self.confirm_remove_llp_partner_id = assoc_id

    def cancel_remove_llp_partner(self):
        self.confirm_remove_llp_partner_id = ""

    def remove_director_from_llp(self, assoc_id: str):
        if self.role not in ("ADMIN", "EDITOR"):
            self.llp_partner_error = "You do not have permission."
            return
        self.confirm_remove_llp_partner_id = ""
        if self.llp_partner_editing_id == assoc_id:
            self.cancel_edit_llp_partner()
        try:
            aid = int(assoc_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            assoc = session.query(LLPDirector).filter(LLPDirector.id == aid).first()
            if assoc:
                session.delete(assoc)
                session.commit()
        self._load_llp_partners()

    # ── LLP ↔ Company links ────────────────────────────────────────────────

    def _load_llp_companies(self):
        try:
            lid = int(self.managing_llp_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            rows = (
                session.query(CompanyLLP, Company)
                .join(Company, CompanyLLP.company_id == Company.id)
                .filter(CompanyLLP.llp_id == lid)
                .all()
            )
            self.llp_companies = [
                {
                    "link_id": str(cl.id),
                    "company_id": str(c.id),
                    "cin": c.cin,
                    "name": c.name,
                    "relationship_note": cl.relationship_note or "",
                }
                for cl, c in rows
            ]

    def open_manage_llp_companies(self, llp_id: str):
        self._clear_manage_llp_companies()
        self.managing_llp_id = llp_id
        for l in self.llps:
            if l["id"] == llp_id:
                self.managing_llp_name = l["name"]
                break
        self.show_manage_llp_companies = True
        self._load_llp_companies()

    def close_manage_llp_companies(self):
        self._clear_manage_llp_companies()

    def handle_llp_company_search(self, value: str):
        self.llp_company_search_query = value
        self.llp_company_selected_id = ""
        self.llp_company_selected_name = ""
        if not value.strip():
            self.llp_company_search_results = []
            return
        with SessionLocal() as session:
            term = f"%{value.strip()}%"
            rows = (
                session.query(Company)
                .filter(or_(Company.cin.ilike(term), Company.name.ilike(term)))
                .limit(8)
                .all()
            )
            self.llp_company_search_results = [
                {"id": str(r.id), "cin": r.cin, "name": r.name} for r in rows
            ]

    def select_company_for_llp(self, company_id: str):
        self.llp_company_selected_id = company_id
        self.llp_company_search_results = []
        try:
            cid = int(company_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            c = session.query(Company).filter(Company.id == cid).first()
            if c:
                self.llp_company_selected_name = f"{c.name}  (CIN: {c.cin})"
                self.llp_company_search_query = c.name

    def handle_llp_company_relationship_note_change(self, value: str):
        self.llp_company_relationship_note = value

    def link_company_to_llp(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.llp_company_error = "You do not have permission."
            return
        if not self.llp_company_selected_id:
            self.llp_company_error = "Please select a company from the search results."
            return
        self.llp_company_error = ""
        lid = self.managing_llp_id
        cid = self.llp_company_selected_id
        note = self.llp_company_relationship_note.strip()
        self.is_saving = True
        return PortalState.commit_link_company_to_llp(lid, cid, note)

    def commit_link_company_to_llp(self, llp_id: str, company_id: str, relationship_note: str = ""):
        try:
            lid = int(llp_id)
            cid = int(company_id)
        except (ValueError, TypeError):
            self.is_saving = False
            return
        with SessionLocal() as session:
            existing = session.query(CompanyLLP).filter(
                CompanyLLP.llp_id == lid, CompanyLLP.company_id == cid,
            ).first()
            if existing:
                self.llp_company_error = "This company is already linked to this LLP."
                self.is_saving = False
                return
            session.add(CompanyLLP(company_id=cid, llp_id=lid, relationship_note=relationship_note or None))
            session.commit()
        self.llp_company_relationship_note = ""
        self.llp_company_selected_id = ""
        self.llp_company_selected_name = ""
        self.llp_company_search_query = ""
        self.llp_company_error = ""
        self.is_saving = False
        self._load_llp_companies()

    def prompt_remove_llp_company(self, link_id: str):
        self.confirm_remove_llp_company_id = link_id

    def cancel_remove_llp_company(self):
        self.confirm_remove_llp_company_id = ""

    def remove_company_from_llp(self, link_id: str):
        if self.role not in ("ADMIN", "EDITOR"):
            self.llp_company_error = "You do not have permission."
            return
        self.confirm_remove_llp_company_id = ""
        try:
            id_ = int(link_id)
        except (ValueError, TypeError):
            return
        with SessionLocal() as session:
            link = session.query(CompanyLLP).filter(CompanyLLP.id == id_).first()
            if link:
                session.delete(link)
                session.commit()
        self._load_llp_companies()


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
            width="40%",
            height="100vh",
            justify="center",
            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        ),
        rx.vstack(
            rx.vstack(
                rx.heading("Welcome Back", size="9", color="#1a1a1a", weight="bold"),
                rx.text("Enter credentials to access", size="7", color="#666"),
                spacing="2",
                margin_bottom="2rem",
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Username", size="2", weight="bold", color="#333"),
                    rx.el.input(
                        placeholder="Username",
                        value=PortalState.username,
                        on_change=PortalState.handle_username_change,
                        on_key_down=PortalState.handle_key_down,
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "1rem 1rem",
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
                    width="40%",
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
                            "padding": "1rem 1rem",
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
                    width="40%",
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
                width="40%",
                padding="1.25rem 1rem",
                height="3.5rem",
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


def _form_input(label: str, placeholder: str, value, on_change, input_type: str = "text") -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold", color="#333"),
        rx.el.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            type=input_type,
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


def _form_date_input(label: str, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold", color="#333"),
        rx.el.input(
            type="text",
            placeholder="DD/MM/YYYY",
            value=value,
            on_change=on_change,
            style={
                "width": "100%",
                "padding": "0.625rem 0.875rem",
                "border_radius": "0.5rem",
                "border": "2px solid #d0d0d0",
                "background_color": "white",
                "font_size": "0.95rem",
                "color": "#1a1a1a",
                "outline": "none",
                "box_sizing": "border-box",
            },
        ),
        rx.text("Format: DD/MM/YYYY (e.g. 15/08/2024)", size="1", color="#999"),
        spacing="1",
        width="100%",
    )


def _form_textarea(label: str, placeholder: str, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="bold", color="#333"),
        rx.el.textarea(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            rows="3",
            style={
                "width": "100%",
                "padding": "0.625rem 0.875rem",
                "border_radius": "0.5rem",
                "border": "2px solid #d0d0d0",
                "background_color": "white",
                "font_size": "0.95rem",
                "color": "#1a1a1a",
                "outline": "none",
                "box_sizing": "border-box",
                "resize": "vertical",
                "font_family": "inherit",
                "min_height": "80px",
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
                    # ── Identification ────────────────────────────────────────
                    rx.text("Identification", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("CIN", "e.g. U74999MH2021PTC123456", PortalState.form_cin, PortalState.handle_form_cin_change),
                        _form_input("Registration Number", "e.g. 123456", PortalState.form_registration_number, PortalState.handle_form_registration_number_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_input("Company Name", "Enter full company name", PortalState.form_name, PortalState.handle_form_name_change),
                    # ── Jurisdiction ────────────────────────────────────────────
                    rx.text("Jurisdiction", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("ROC Name", "e.g. Registrar of Companies, Mumbai", PortalState.form_roc_code, PortalState.handle_form_roc_code_change),
                        _form_input("ROC Office", "e.g. Mumbai", PortalState.form_roc_office, PortalState.handle_form_roc_office_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_input("RD Name", "e.g. Regional Director, Western Region", PortalState.form_rd_name, PortalState.handle_form_rd_name_change),
                        _form_input("RD Region", "e.g. Western Region", PortalState.form_rd_region, PortalState.handle_form_rd_region_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    # ── Classification ────────────────────────────────────────
                    rx.text("Classification", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_select("Class", ["PUBLIC", "PRIVATE"], PortalState.form_class, PortalState.handle_form_class_change),
                        _form_select("Category", ["Company limited by Shares", "Company limited by Guarantee", "Unlimited Company"], PortalState.form_category, PortalState.handle_form_category_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_select(
                        "Sub Category",
                        ["Non-government company", "State government company", "Union government company", "Subsidiary of company incorporated outside India"],
                        PortalState.form_sub_category,
                        PortalState.handle_form_sub_category_change,
                    ),
                    rx.grid(
                        _form_select("Listed Status", ["Listed", "Unlisted"], PortalState.form_listed_status, PortalState.handle_form_listed_status_change),
                        _form_select("Suspended at Stock Exchange", ["Yes", "No"], PortalState.form_suspended_at_stock_exchange, PortalState.handle_form_suspended_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    # ── Financials ────────────────────────────────────────────
                    rx.text("Financials", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        rx.vstack(
                            rx.text("Authorised Capital (₹)", size="2", weight="bold", color="#333"),
                            rx.el.input(
                                placeholder="e.g. 1000000",
                                value=PortalState.form_authorised_capital,
                                on_change=PortalState.handle_form_authorised_capital_change,
                                type="number", min="0", step="1",
                                style={"width": "100%", "padding": "0.625rem 0.875rem", "border_radius": "0.5rem", "border": "2px solid #d0d0d0", "background_color": "white", "font_size": "0.95rem", "color": "black", "outline": "none", "box_sizing": "border-box"},
                            ),
                            spacing="1", width="100%",
                        ),
                        rx.vstack(
                            rx.text("Paid Up Capital (₹)", size="2", weight="bold", color="#333"),
                            rx.el.input(
                                placeholder="e.g. 500000",
                                value=PortalState.form_paid_up_capital,
                                on_change=PortalState.handle_form_paid_up_capital_change,
                                type="number", min="0", step="1",
                                style={"width": "100%", "padding": "0.625rem 0.875rem", "border_radius": "0.5rem", "border": "2px solid #d0d0d0", "background_color": "white", "font_size": "0.95rem", "color": "black", "outline": "none", "box_sizing": "border-box"},
                            ),
                            spacing="1", width="100%",
                        ),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_input("Number of Members", "e.g. 7", PortalState.form_number_of_members, PortalState.handle_form_number_of_members_change),
                    # ── Important Dates ───────────────────────────────────────
                    rx.text("Important Dates", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_date_input("Date of Incorporation", PortalState.form_doi, PortalState.handle_form_doi_change),
                        _form_date_input("Date of Last AGM", PortalState.form_date_of_last_agm, PortalState.handle_form_date_of_last_agm_change),
                        _form_date_input("Date of Balance Sheet", PortalState.form_date_of_balance_sheet, PortalState.handle_form_date_of_balance_sheet_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    # ── Contact & Address ─────────────────────────────────────
                    rx.text("Contact & Address", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("Email Address", "e.g. company@example.com", PortalState.form_email, PortalState.handle_form_email_change, "email"),
                        _form_input("Phone", "e.g. 022-12345678", PortalState.form_phone, PortalState.handle_form_phone_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_textarea("Registered Address", "Building/Street, Area", PortalState.form_address, PortalState.handle_form_address_change),
                    rx.grid(
                        _form_input("Pin Code", "e.g. 400001", PortalState.form_pin_code, PortalState.handle_form_pin_code_change),
                        _form_input("Country", "e.g. India", PortalState.form_country, PortalState.handle_form_country_change),
                        columns="2", spacing="3", width="100%",
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
                max_width="700px",
                width="95%",
                max_height="90vh",
                overflow_y="auto",
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
                    # ── Identification ────────────────────────────────────────
                    rx.text("Identification", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("CIN", "e.g. U74999MH2021PTC123456", PortalState.edit_form_cin, PortalState.handle_edit_form_cin_change),
                        _form_input("Registration Number", "e.g. 123456", PortalState.edit_form_registration_number, PortalState.handle_edit_form_registration_number_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_input("Company Name", "Enter full company name", PortalState.edit_form_name, PortalState.handle_edit_form_name_change),
                    # ── Jurisdiction ────────────────────────────────────────────
                    rx.text("Jurisdiction", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("ROC Name", "e.g. Registrar of Companies, Mumbai", PortalState.edit_form_roc_code, PortalState.handle_edit_form_roc_code_change),
                        _form_input("ROC Office", "e.g. Mumbai", PortalState.edit_form_roc_office, PortalState.handle_edit_form_roc_office_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_input("RD Name", "e.g. Regional Director, Western Region", PortalState.edit_form_rd_name, PortalState.handle_edit_form_rd_name_change),
                        _form_input("RD Region", "e.g. Western Region", PortalState.edit_form_rd_region, PortalState.handle_edit_form_rd_region_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    # ── Classification ────────────────────────────────────────
                    rx.text("Classification", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_select("Class", ["PUBLIC", "PRIVATE"], PortalState.edit_form_class, PortalState.handle_edit_form_class_change),
                        _form_select("Category", ["Company limited by Shares", "Company limited by Guarantee", "Unlimited Company"], PortalState.edit_form_category, PortalState.handle_edit_form_category_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_select(
                        "Sub Category",
                        ["Non-government company", "State government company", "Union government company", "Subsidiary of company incorporated outside India"],
                        PortalState.edit_form_sub_category,
                        PortalState.handle_edit_form_sub_category_change,
                    ),
                    rx.grid(
                        _form_select("Listed Status", ["Listed", "Unlisted"], PortalState.edit_form_listed_status, PortalState.handle_edit_form_listed_status_change),
                        _form_select("Suspended at Stock Exchange", ["Yes", "No"], PortalState.edit_form_suspended_at_stock_exchange, PortalState.handle_edit_form_suspended_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    # ── Financials ────────────────────────────────────────────
                    rx.text("Financials", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        rx.vstack(
                            rx.text("Authorised Capital (₹)", size="2", weight="bold", color="#333"),
                            rx.el.input(
                                placeholder="e.g. 1000000",
                                value=PortalState.edit_form_authorised_capital,
                                on_change=PortalState.handle_edit_form_authorised_capital_change,
                                type="number", min="0", step="1",
                                style={"width": "100%", "padding": "0.625rem 0.875rem", "border_radius": "0.5rem", "border": "2px solid #d0d0d0", "background_color": "white", "font_size": "0.95rem", "color": "black", "outline": "none", "box_sizing": "border-box"},
                            ),
                            spacing="1", width="100%",
                        ),
                        rx.vstack(
                            rx.text("Paid Up Capital (₹)", size="2", weight="bold", color="#333"),
                            rx.el.input(
                                placeholder="e.g. 500000",
                                value=PortalState.edit_form_paid_up_capital,
                                on_change=PortalState.handle_edit_form_paid_up_capital_change,
                                type="number", min="0", step="1",
                                style={"width": "100%", "padding": "0.625rem 0.875rem", "border_radius": "0.5rem", "border": "2px solid #d0d0d0", "background_color": "white", "font_size": "0.95rem", "color": "black", "outline": "none", "box_sizing": "border-box"},
                            ),
                            spacing="1", width="100%",
                        ),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_input("Number of Members", "e.g. 7", PortalState.edit_form_number_of_members, PortalState.handle_edit_form_number_of_members_change),
                    # ── Important Dates ───────────────────────────────────────
                    rx.text("Important Dates", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_date_input("Date of Incorporation", PortalState.edit_form_doi, PortalState.handle_edit_form_doi_change),
                        _form_date_input("Date of Last AGM", PortalState.edit_form_date_of_last_agm, PortalState.handle_edit_form_date_of_last_agm_change),
                        _form_date_input("Date of Balance Sheet", PortalState.edit_form_date_of_balance_sheet, PortalState.handle_edit_form_date_of_balance_sheet_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    # ── Contact & Address ─────────────────────────────────────
                    rx.text("Contact & Address", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("Email Address", "e.g. company@example.com", PortalState.edit_form_email, PortalState.handle_edit_form_email_change, "email"),
                        _form_input("Phone", "e.g. 022-12345678", PortalState.edit_form_phone, PortalState.handle_edit_form_phone_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_textarea("Registered Address", "Building/Street, Area", PortalState.edit_form_address, PortalState.handle_edit_form_address_change),
                    rx.grid(
                        _form_input("Pin Code", "e.g. 400001", PortalState.edit_form_pin_code, PortalState.handle_edit_form_pin_code_change),
                        _form_input("Country", "e.g. India", PortalState.edit_form_country, PortalState.handle_edit_form_country_change),
                        columns="2", spacing="3", width="100%",
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
                max_width="700px",
                width="95%",
                max_height="90vh",
                overflow_y="auto",
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
                rx.table.column_header_cell("Date of Incorp.", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Email", font_weight="700", color="white", font_size="0.95rem"),
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
                    rx.table.cell(rx.text(item["doi"], color="#555", size="2")),
                    rx.table.cell(
                        rx.cond(
                            item["email"] != "",
                            rx.link(item["email"], href=f"mailto:{item['email']}", size="2", color="#667eea"),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(
                        rx.hstack(
                            rx.button(
                                rx.icon("users", size=14),
                                on_click=PortalState.open_manage_directors(item["id"]),
                                color_scheme="violet",
                                variant="ghost",
                                size="1",
                            ),
                            rx.cond(
                                (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                                rx.button(
                                    rx.icon("pencil", size=14),
                                    on_click=PortalState.open_edit_company_form(item["id"]),
                                    color_scheme="blue",
                                    variant="ghost",
                                    size="1",
                                ),
                            ),
                            rx.cond(
                                PortalState.role == "ADMIN",
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
                                                rx.vstack(
                                                    rx.text(
                                                        "Are you sure you want to permanently delete this company? This action cannot be undone.",
                                                        size="3",
                                                        color="#333",
                                                    ),
                                                    rx.box(
                                                        rx.hstack(
                                                            rx.text("CIN:", size="2", weight="bold", color="#555"),
                                                            rx.text(item["cin"], size="2", color="#1a1a1a"),
                                                            spacing="2",
                                                        ),
                                                        rx.hstack(
                                                            rx.text("Name:", size="2", weight="bold", color="#555"),
                                                            rx.text(item["name"], size="2", color="#1a1a1a"),
                                                            spacing="2",
                                                        ),
                                                        padding="0.75rem",
                                                        background="#f5f5f5",
                                                        border_radius="0.5rem",
                                                        border_left="3px solid #dc2626",
                                                        width="100%",
                                                    ),
                                                    spacing="3",
                                                    width="100%",
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
                                        background="white",
                                    ),
                                ),
                                ),
                            ),
                            spacing="1",
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
                                        background="white",
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


def add_director_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_add_director_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("user-round-plus", size=22, color="#667eea"),
                        rx.heading("Add Director", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_add_director_form,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    _form_input("DIN (Director Identification Number)", "e.g. 00123456", PortalState.form_din, PortalState.handle_form_din_change),
                    _form_input("Full Name", "Enter director's full name", PortalState.form_director_name, PortalState.handle_form_director_name_change),
                    _form_input("Email ID", "e.g. director@example.com", PortalState.form_director_email, PortalState.handle_form_director_email_change, "email"),
                    _form_input("Phone Number", "e.g. +91 98765 43210", PortalState.form_director_phone, PortalState.handle_form_director_phone_change),
                    rx.cond(
                        PortalState.form_director_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.form_director_error, size="2", color="#dc2626"),
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
                            on_click=PortalState.close_add_director_form,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save Director"), spacing="2"),
                            on_click=PortalState.save_director,
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


def edit_director_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_edit_director_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("pencil", size=22, color="#667eea"),
                        rx.heading("Edit Director", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_edit_director_form,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    _form_input("DIN (Director Identification Number)", "e.g. 00123456", PortalState.edit_form_din, PortalState.handle_edit_form_din_change),
                    _form_input("Full Name", "Enter director's full name", PortalState.edit_form_director_name, PortalState.handle_edit_form_director_name_change),
                    _form_input("Email ID", "e.g. director@example.com", PortalState.edit_form_director_email, PortalState.handle_edit_form_director_email_change, "email"),
                    _form_input("Phone Number", "e.g. +91 98765 43210", PortalState.edit_form_director_phone, PortalState.handle_edit_form_director_phone_change),
                    rx.cond(
                        PortalState.edit_form_director_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.edit_form_director_error, size="2", color="#dc2626"),
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
                            on_click=PortalState.close_edit_director_form,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save Changes"), spacing="2"),
                            on_click=PortalState.save_edit_director,
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


def directors_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("DIN", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Name", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Email", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Phone", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Status", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Actions", font_weight="700", color="white", font_size="0.95rem"),
            ),
            background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
            padding="1rem",
        ),
        rx.table.body(
            rx.foreach(
                PortalState.directors,
                lambda item: rx.table.row(
                    rx.table.cell(rx.text(item["din"], font_weight="600", color="#1a1a1a", size="3")),
                    rx.table.cell(rx.text(item["name"], font_weight="500", color="#333", size="3")),
                    rx.table.cell(
                        rx.cond(
                            item["email"] != "",
                            rx.link(item["email"], href=f"mailto:{item['email']}", size="2", color="#667eea"),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(
                        rx.cond(
                            item["phone"] != "",
                            rx.text(item["phone"], size="2", color="#333"),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(rx.badge(item["status"], variant="outline", color_scheme="green")),
                    rx.table.cell(
                        rx.cond(
                            (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                            rx.button(
                                rx.icon("pencil", size=14),
                                on_click=PortalState.open_edit_director_form(item["id"]),
                                color_scheme="blue",
                                variant="ghost",
                                size="1",
                            ),
                        ),
                        rx.cond(
                            PortalState.role == "ADMIN",
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
                                                rx.dialog.title("Delete Director", size="5", weight="bold", color="#1a1a1a"),
                                                spacing="2",
                                                align_items="center",
                                            ),
                                            rx.divider(),
                                            rx.dialog.description(
                                                rx.vstack(
                                                    rx.text(
                                                        "Permanently delete this director? This cannot be undone.",
                                                        size="3",
                                                        color="#333",
                                                    ),
                                                    rx.box(
                                                        rx.hstack(
                                                            rx.text("DIN:", size="2", weight="bold", color="#555"),
                                                            rx.text(item["din"], size="2", color="#1a1a1a"),
                                                            spacing="2",
                                                        ),
                                                        rx.hstack(
                                                            rx.text("Name:", size="2", weight="bold", color="#555"),
                                                            rx.text(item["name"], size="2", color="#1a1a1a"),
                                                            spacing="2",
                                                        ),
                                                        padding="0.75rem",
                                                        background="#f5f5f5",
                                                        border_radius="0.5rem",
                                                        border_left="3px solid #dc2626",
                                                        width="100%",
                                                    ),
                                                    spacing="3",
                                                    width="100%",
                                                ),
                                            ),
                                            rx.hstack(
                                                rx.dialog.close(
                                                    rx.button("Cancel", variant="outline", color_scheme="gray", size="3"),
                                                ),
                                                rx.dialog.close(
                                                    rx.button(
                                                        rx.hstack(rx.icon("trash-2", size=16), rx.text("Delete"), spacing="2"),
                                                        on_click=PortalState.confirm_delete_director(item["id"]),
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
                                        background="white",
                                    ),
                                ),
                            ),
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


def directors_section() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("user-round", size=22, color="#667eea"),
                    rx.vstack(
                        rx.heading("Director Registry", size="5", color="#1a1a1a"),
                        rx.text(f"{PortalState.directors.length()} directors", size="1", color="#999"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                        rx.button(
                            rx.hstack(rx.icon("user-round-plus", size=16), rx.text("Add Director"), spacing="2"),
                            on_click=PortalState.open_add_director_form,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="2",
                        ),
                    ),
                    width="100%",
                    align_items="center",
                ),
                rx.hstack(
                    rx.el.input(
                        placeholder="Search by DIN or director name…",
                        value=PortalState.directors_search_query,
                        on_change=PortalState.handle_directors_search,
                        style={
                            "flex": "1",
                            "padding": "0.6rem 0.875rem",
                            "border_radius": "0.5rem",
                            "border": "1.5px solid #d0d0d0",
                            "background_color": "white",
                            "font_size": "0.9rem",
                            "color": "#1a1a1a",
                            "outline": "none",
                            "box_sizing": "border-box",
                        },
                    ),
                    width="100%",
                    align_items="center",
                ),
                directors_table(),
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


def manage_company_directors_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_manage_directors,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("users", size=22, color="#667eea"),
                        rx.vstack(
                            rx.heading("Manage Directors", size="5", color="#1a1a1a", weight="bold"),
                            rx.text(PortalState.managing_company_name, size="2", color="#667eea", weight="medium"),
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_manage_directors,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    # Current directors list
                    rx.vstack(
                        rx.text("Associated Directors", size="3", weight="bold", color="#1a1a1a"),
                        rx.cond(
                            PortalState.company_directors.length() == 0,
                            rx.text("No directors associated yet.", size="2", color="#aaa"),
                            rx.box(
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("DIN", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Name", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Designation", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Category", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Share %", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Orig. Appt.", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Current Desg. Date", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Cessation", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("", font_weight="700", color="white"),
                                        ),
                                        background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            PortalState.company_directors,
                                            lambda d: rx.table.row(
                                                rx.table.cell(rx.text(d["din"], size="2", font_weight="600", color="#1a1a1a", white_space="nowrap")),
                                                rx.table.cell(rx.text(d["name"], size="2", color="#1a1a1a", white_space="nowrap")),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["designation"] != "",
                                                        rx.text(d["designation"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["category"] != "",
                                                        rx.text(d["category"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["share_percent"] != "",
                                                        rx.text(d["share_percent"], "%", size="2", color="#1a1a1a"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["original_appointment_date"] != "",
                                                        rx.text(d["original_appointment_date"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["current_designation_date"] != "",
                                                        rx.text(d["current_designation_date"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["cessation_date"] != "",
                                                        rx.text(d["cessation_date"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                                                        rx.cond(
                                                            PortalState.confirm_remove_assoc_id == d["assoc_id"],
                                                            rx.hstack(
                                                                rx.text("Remove?", size="1", color="#dc2626", weight="bold"),
                                                                rx.button(
                                                                    "Yes",
                                                                    on_click=PortalState.remove_director_from_company(d["assoc_id"]),
                                                                    color_scheme="red",
                                                                    size="1",
                                                                ),
                                                                rx.button(
                                                                    "No",
                                                                    on_click=PortalState.cancel_remove_director,
                                                                    variant="outline",
                                                                    size="1",
                                                                ),
                                                                spacing="1",
                                                                align_items="center",
                                                            ),
                                                            rx.hstack(
                                                                rx.button(
                                                                    rx.icon("pencil", size=12),
                                                                    on_click=PortalState.start_edit_association(d["assoc_id"]),
                                                                    color_scheme="blue",
                                                                    variant="ghost",
                                                                    size="1",
                                                                ),
                                                                rx.button(
                                                                    rx.icon("x", size=12),
                                                                    on_click=PortalState.prompt_remove_director(d["assoc_id"]),
                                                                    color_scheme="red",
                                                                    variant="ghost",
                                                                    size="1",
                                                                ),
                                                                spacing="1",
                                                            ),
                                                        ),
                                                    )
                                                ),
                                                border_bottom="1px solid #f0f0f0",
                                            ),
                                        )
                                    ),
                                    width="100%",
                                    size="2",
                                ),
                                width="100%",
                                overflow_x="auto",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # Add/edit director section (ADMIN/EDITOR only)
                    rx.cond(
                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                        rx.vstack(
                            rx.divider(),
                            rx.cond(
                                PortalState.assoc_editing_id != "",
                                rx.text("Edit Association", size="2", weight="bold", color="#333"),
                                rx.text("Add Director to Company", size="2", weight="bold", color="#333"),
                            ),
                            rx.cond(
                                PortalState.assoc_editing_id == "",
                                rx.vstack(
                                    rx.el.input(
                                        placeholder="Search director by DIN or name…",
                                        value=PortalState.assoc_search_query,
                                        on_change=PortalState.handle_assoc_search,
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
                                    rx.cond(
                                        PortalState.assoc_search_results.length() > 0,
                                        rx.box(
                                            rx.foreach(
                                                PortalState.assoc_search_results,
                                                lambda r: rx.box(
                                                    rx.hstack(
                                                        rx.text(r["din"], size="2", font_weight="600", color="#667eea"),
                                                        rx.text(r["name"], size="2", color="#333"),
                                                        spacing="2",
                                                    ),
                                                    padding="0.5rem 0.75rem",
                                                    cursor="pointer",
                                                    border_bottom="1px solid #f0f0f0",
                                                    _hover={"background": "#f0f4ff"},
                                                    on_click=PortalState.select_director_for_assoc(r["id"]),
                                                ),
                                            ),
                                            border="1.5px solid #d0d0d0",
                                            border_radius="0.5rem",
                                            background="white",
                                            width="100%",
                                            max_height="180px",
                                            overflow_y="auto",
                                        ),
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                            ),
                            rx.cond(
                                PortalState.assoc_selected_director_name != "",
                                rx.box(
                                    rx.hstack(
                                        rx.icon("circle-check", size=16, color="#16a34a"),
                                        rx.text(PortalState.assoc_selected_director_name, size="2", color="#166534"),
                                        spacing="2",
                                    ),
                                    padding="0.5rem 0.75rem",
                                    background="#dcfce7",
                                    border_radius="0.5rem",
                                    border_left="3px solid #16a34a",
                                    width="100%",
                                ),
                            ),
                            rx.grid(
                                _form_input("Designation", "e.g. Director / Additional Director", PortalState.assoc_designation, PortalState.handle_assoc_designation_change),
                                _form_input("Category", "e.g. Promoter / Professional", PortalState.assoc_category, PortalState.handle_assoc_category_change),
                                columns="2", spacing="3", width="100%",
                            ),
                            rx.grid(
                                _form_date_input("Original Date of Appointment", PortalState.assoc_original_appointment_date, PortalState.handle_assoc_original_appointment_date_change),
                                _form_date_input("Date of Appointment at Current Designation", PortalState.assoc_current_designation_date, PortalState.handle_assoc_current_designation_date_change),
                                columns="2", spacing="3", width="100%",
                            ),
                            _form_date_input("Date of Cessation (if applicable)", PortalState.assoc_cessation_date, PortalState.handle_assoc_cessation_date_change),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Share %", size="2", weight="bold", color="#333"),
                                    rx.el.input(
                                        placeholder="e.g. 25.5",
                                        value=PortalState.assoc_share_percent,
                                        on_change=PortalState.handle_assoc_share_change,
                                        type="number",
                                        min="0",
                                        max="100",
                                        step="0.01",
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
                                    width="140px",
                                ),
                                rx.spacer(),
                                rx.cond(
                                    PortalState.assoc_editing_id != "",
                                    rx.button(
                                        "Cancel",
                                        on_click=PortalState.cancel_edit_association,
                                        variant="outline",
                                        color_scheme="gray",
                                        size="3",
                                    ),
                                ),
                                rx.cond(
                                    PortalState.assoc_editing_id != "",
                                    rx.button(
                                        rx.hstack(rx.icon("save", size=16), rx.text("Save Changes"), spacing="2"),
                                        on_click=PortalState.add_director_to_company,
                                        loading=PortalState.is_saving,
                                        disabled=PortalState.is_saving,
                                        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                        color="white",
                                        size="3",
                                        align_self="flex-end",
                                    ),
                                    rx.button(
                                        rx.hstack(rx.icon("user-round-plus", size=16), rx.text("Add Director"), spacing="2"),
                                        on_click=PortalState.add_director_to_company,
                                        loading=PortalState.is_saving,
                                        disabled=PortalState.is_saving,
                                        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                        color="white",
                                        size="3",
                                        align_self="flex-end",
                                    ),
                                ),
                                width="100%",
                                align_items="flex-end",
                                spacing="2",
                            ),
                            rx.cond(
                                PortalState.assoc_error != "",
                                rx.box(
                                    rx.hstack(
                                        rx.icon("circle-alert", size=16, color="#dc2626"),
                                        rx.text(PortalState.assoc_error, size="2", color="#dc2626"),
                                        spacing="2",
                                    ),
                                    padding="0.75rem",
                                    border_radius="0.5rem",
                                    background="#fee2e2",
                                    border_left="4px solid #dc2626",
                                    width="100%",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Close",
                            on_click=PortalState.close_manage_directors,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="820px",
                width="90%",
                max_height="90vh",
                overflow_y="auto",
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


def add_llp_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_add_llp_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("building", size=22, color="#667eea"),
                        rx.heading("Add LLP", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_add_llp_form,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    rx.grid(
                        _form_input("LLPIN", "e.g. AAA-1234", PortalState.form_llpin, PortalState.handle_form_llpin_change),
                        _form_input("LLP Name", "Enter full LLP name", PortalState.form_llp_name, PortalState.handle_form_llp_name_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_input("ROC Name", "e.g. ROC Bangalore", PortalState.form_llp_roc_name, PortalState.handle_form_llp_roc_name_change),
                        _form_date_input("Date of Incorporation", PortalState.form_llp_doi, PortalState.handle_form_llp_doi_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_input("Email ID", "e.g. llp@example.com", PortalState.form_llp_email, PortalState.handle_form_llp_email_change, "email"),
                        _form_input("Total Obligation of Contribution (₹)", "e.g. 500000", PortalState.form_llp_total_obligation, PortalState.handle_form_llp_total_obligation_change, "number"),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_textarea("Registered Address", "Enter registered address", PortalState.form_llp_address, PortalState.handle_form_llp_address_change),
                    rx.grid(
                        _form_input("Number of Partners", "e.g. 2", PortalState.form_llp_number_of_partners, PortalState.handle_form_llp_number_of_partners_change),
                        _form_input("Number of Designated Partners", "e.g. 2", PortalState.form_llp_number_of_designated_partners, PortalState.handle_form_llp_number_of_designated_partners_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_select("Status under CIRP", ["Yes", "No"], PortalState.form_llp_status_under_cirp, PortalState.handle_form_llp_status_under_cirp_change),
                        _form_select("Small LLP", ["Yes", "No"], PortalState.form_llp_small_llp, PortalState.handle_form_llp_small_llp_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_date_input("Strike off / amalgamated / transferred date", PortalState.form_llp_strike_off_date, PortalState.handle_form_llp_strike_off_date_change),
                    rx.cond(
                        PortalState.form_llp_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.form_llp_error, size="2", color="#dc2626"),
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
                            on_click=PortalState.close_add_llp_form,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save LLP"), spacing="2"),
                            on_click=PortalState.save_llp,
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
                max_width="620px",
                width="90%",
                max_height="90vh",
                overflow_y="auto",
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


def edit_llp_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_edit_llp_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("pencil", size=22, color="#667eea"),
                        rx.heading("Edit LLP", size="5", color="#1a1a1a", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_edit_llp_form,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    rx.grid(
                        _form_input("LLPIN", "e.g. AAA-1234", PortalState.edit_form_llpin, PortalState.handle_edit_form_llpin_change),
                        _form_input("LLP Name", "Enter full LLP name", PortalState.edit_form_llp_name, PortalState.handle_edit_form_llp_name_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_input("ROC Name", "e.g. ROC Bangalore", PortalState.edit_form_llp_roc_name, PortalState.handle_edit_form_llp_roc_name_change),
                        _form_date_input("Date of Incorporation", PortalState.edit_form_llp_doi, PortalState.handle_edit_form_llp_doi_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_input("Email ID", "e.g. llp@example.com", PortalState.edit_form_llp_email, PortalState.handle_edit_form_llp_email_change, "email"),
                        _form_input("Total Obligation of Contribution (₹)", "e.g. 500000", PortalState.edit_form_llp_total_obligation, PortalState.handle_edit_form_llp_total_obligation_change, "number"),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_textarea("Registered Address", "Enter registered address", PortalState.edit_form_llp_address, PortalState.handle_edit_form_llp_address_change),
                    rx.grid(
                        _form_input("Number of Partners", "e.g. 2", PortalState.edit_form_llp_number_of_partners, PortalState.handle_edit_form_llp_number_of_partners_change),
                        _form_input("Number of Designated Partners", "e.g. 2", PortalState.edit_form_llp_number_of_designated_partners, PortalState.handle_edit_form_llp_number_of_designated_partners_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.grid(
                        _form_select("Status under CIRP", ["Yes", "No"], PortalState.edit_form_llp_status_under_cirp, PortalState.handle_edit_form_llp_status_under_cirp_change),
                        _form_select("Small LLP", ["Yes", "No"], PortalState.edit_form_llp_small_llp, PortalState.handle_edit_form_llp_small_llp_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_date_input("Strike off / amalgamated / transferred date", PortalState.edit_form_llp_strike_off_date, PortalState.handle_edit_form_llp_strike_off_date_change),
                    rx.cond(
                        PortalState.edit_form_llp_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=16, color="#dc2626"),
                                rx.text(PortalState.edit_form_llp_error, size="2", color="#dc2626"),
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
                            on_click=PortalState.close_edit_llp_form,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("save", size=16), rx.text("Save Changes"), spacing="2"),
                            on_click=PortalState.save_edit_llp,
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
                max_width="620px",
                width="90%",
                max_height="90vh",
                overflow_y="auto",
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


def llps_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("LLPIN", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("LLP Name", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("ROC Name", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Date of Incorp.", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Email", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Actions", font_weight="700", color="white", font_size="0.95rem"),
            ),
            background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
            padding="1rem",
        ),
        rx.table.body(
            rx.foreach(
                PortalState.llps,
                lambda item: rx.table.row(
                    rx.table.cell(rx.text(item["llpin"], font_weight="600", color="#1a1a1a", size="3")),
                    rx.table.cell(rx.text(item["name"], font_weight="500", color="#333", size="3")),
                    rx.table.cell(
                        rx.cond(
                            item["roc_name"] != "",
                            rx.text(item["roc_name"], size="2", color="#333"),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(
                        rx.cond(
                            item["doi"] != "",
                            rx.text(item["doi"], size="2", color="#333"),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(
                        rx.cond(
                            item["email"] != "",
                            rx.link(item["email"], href=f"mailto:{item['email']}", size="2", color="#667eea"),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(
                        rx.hstack(
                            rx.button(
                                rx.icon("users", size=14),
                                on_click=PortalState.open_manage_llp_partners(item["id"]),
                                color_scheme="violet",
                                variant="ghost",
                                size="1",
                            ),
                            rx.button(
                                rx.icon("link", size=14),
                                on_click=PortalState.open_manage_llp_companies(item["id"]),
                                color_scheme="grass",
                                variant="ghost",
                                size="1",
                            ),
                            rx.cond(
                                (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                                rx.button(
                                    rx.icon("pencil", size=14),
                                    on_click=PortalState.open_edit_llp_form(item["id"]),
                                    color_scheme="blue",
                                    variant="ghost",
                                    size="1",
                                ),
                            ),
                            rx.cond(
                                PortalState.role == "ADMIN",
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
                                                rx.dialog.title("Delete LLP", size="5", weight="bold", color="#1a1a1a"),
                                                spacing="2",
                                                align_items="center",
                                            ),
                                            rx.divider(),
                                            rx.dialog.description(
                                                rx.vstack(
                                                    rx.text(
                                                        "Are you sure you want to permanently delete this LLP? This action cannot be undone.",
                                                        size="3",
                                                        color="#333",
                                                    ),
                                                    rx.box(
                                                        rx.hstack(
                                                            rx.text("LLPIN:", size="2", weight="bold", color="#555"),
                                                            rx.text(item["llpin"], size="2", color="#1a1a1a"),
                                                            spacing="2",
                                                        ),
                                                        rx.hstack(
                                                            rx.text("Name:", size="2", weight="bold", color="#555"),
                                                            rx.text(item["name"], size="2", color="#1a1a1a"),
                                                            spacing="2",
                                                        ),
                                                        padding="0.75rem",
                                                        background="#f5f5f5",
                                                        border_radius="0.5rem",
                                                        border_left="3px solid #dc2626",
                                                        width="100%",
                                                    ),
                                                    spacing="3",
                                                    width="100%",
                                                ),
                                            ),
                                            rx.hstack(
                                                rx.dialog.close(
                                                    rx.button("Cancel", variant="outline", color_scheme="gray", size="3"),
                                                ),
                                                rx.dialog.close(
                                                    rx.button(
                                                        rx.hstack(rx.icon("trash-2", size=16), rx.text("Delete"), spacing="2"),
                                                        on_click=PortalState.confirm_delete_llp(item["id"]),
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
                                        background="white",
                                    ),
                                ),
                            ),
                            spacing="1",
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


def llps_section() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("building", size=22, color="#667eea"),
                    rx.vstack(
                        rx.heading("LLP Registry", size="5", color="#1a1a1a"),
                        rx.text(f"{PortalState.llps.length()} LLPs", size="1", color="#999"),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.cond(
                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                        rx.button(
                            rx.hstack(rx.icon("building", size=16), rx.text("Add LLP"), spacing="2"),
                            on_click=PortalState.open_add_llp_form,
                            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            color="white",
                            size="2",
                        ),
                    ),
                    width="100%",
                    align_items="center",
                ),
                rx.hstack(
                    rx.el.input(
                        placeholder="Search by LLPIN or LLP name…",
                        value=PortalState.llps_search_query,
                        on_change=PortalState.handle_llps_search,
                        style={
                            "flex": "1",
                            "padding": "0.6rem 0.875rem",
                            "border_radius": "0.5rem",
                            "border": "1.5px solid #d0d0d0",
                            "background_color": "white",
                            "font_size": "0.9rem",
                            "color": "#1a1a1a",
                            "outline": "none",
                            "box_sizing": "border-box",
                        },
                    ),
                    width="100%",
                    align_items="center",
                ),
                llps_table(),
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


def manage_llp_partners_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_manage_llp_partners,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("users", size=22, color="#667eea"),
                        rx.vstack(
                            rx.heading("Manage Designated Partners", size="5", color="#1a1a1a", weight="bold"),
                            rx.text(PortalState.managing_llp_name, size="2", color="#667eea", weight="medium"),
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_manage_llp_partners,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    rx.vstack(
                        rx.text("Designated Partners", size="3", weight="bold", color="#1a1a1a"),
                        rx.cond(
                            PortalState.llp_partners.length() == 0,
                            rx.text("No designated partners yet.", size="2", color="#aaa"),
                            rx.box(
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("DIN", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Name", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Designation", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Appointed", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Cessation", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("Signatory", font_weight="700", color="white", font_size="0.85rem"),
                                            rx.table.column_header_cell("", font_weight="700", color="white"),
                                        ),
                                        background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            PortalState.llp_partners,
                                            lambda d: rx.table.row(
                                                rx.table.cell(rx.text(d["din"], size="2", font_weight="600", color="#1a1a1a", white_space="nowrap")),
                                                rx.table.cell(rx.text(d["name"], size="2", color="#1a1a1a", white_space="nowrap")),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["designation"] != "",
                                                        rx.text(d["designation"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["appointment_date"] != "",
                                                        rx.text(d["appointment_date"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["cessation_date"] != "",
                                                        rx.text(d["cessation_date"], size="2", color="#1a1a1a", white_space="nowrap"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        d["is_signatory"] != "",
                                                        rx.text(d["is_signatory"], size="2", color="#1a1a1a"),
                                                        rx.text("-", size="2", color="#aaa"),
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.cond(
                                                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                                                        rx.cond(
                                                            PortalState.confirm_remove_llp_partner_id == d["assoc_id"],
                                                            rx.hstack(
                                                                rx.text("Remove?", size="1", color="#dc2626", weight="bold"),
                                                                rx.button(
                                                                    "Yes",
                                                                    on_click=PortalState.remove_director_from_llp(d["assoc_id"]),
                                                                    color_scheme="red",
                                                                    size="1",
                                                                ),
                                                                rx.button(
                                                                    "No",
                                                                    on_click=PortalState.cancel_remove_llp_partner,
                                                                    variant="outline",
                                                                    size="1",
                                                                ),
                                                                spacing="1",
                                                                align_items="center",
                                                            ),
                                                            rx.hstack(
                                                                rx.button(
                                                                    rx.icon("pencil", size=12),
                                                                    on_click=PortalState.start_edit_llp_partner(d["assoc_id"]),
                                                                    color_scheme="blue",
                                                                    variant="ghost",
                                                                    size="1",
                                                                ),
                                                                rx.button(
                                                                    rx.icon("x", size=12),
                                                                    on_click=PortalState.prompt_remove_llp_partner(d["assoc_id"]),
                                                                    color_scheme="red",
                                                                    variant="ghost",
                                                                    size="1",
                                                                ),
                                                                spacing="1",
                                                            ),
                                                        ),
                                                    )
                                                ),
                                                border_bottom="1px solid #f0f0f0",
                                            ),
                                        )
                                    ),
                                    width="100%",
                                    size="2",
                                ),
                                width="100%",
                                overflow_x="auto",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.cond(
                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                        rx.vstack(
                            rx.divider(),
                            rx.cond(
                                PortalState.llp_partner_editing_id != "",
                                rx.text("Edit Designated Partner", size="2", weight="bold", color="#333"),
                                rx.text("Add Designated Partner", size="2", weight="bold", color="#333"),
                            ),
                            rx.cond(
                                PortalState.llp_partner_editing_id == "",
                                rx.vstack(
                                    rx.el.input(
                                        placeholder="Search director by DIN or name…",
                                        value=PortalState.llp_partner_search_query,
                                        on_change=PortalState.handle_llp_partner_search,
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
                                    rx.cond(
                                        PortalState.llp_partner_search_results.length() > 0,
                                        rx.box(
                                            rx.foreach(
                                                PortalState.llp_partner_search_results,
                                                lambda r: rx.box(
                                                    rx.hstack(
                                                        rx.text(r["din"], size="2", font_weight="600", color="#667eea"),
                                                        rx.text(r["name"], size="2", color="#333"),
                                                        spacing="2",
                                                    ),
                                                    padding="0.5rem 0.75rem",
                                                    cursor="pointer",
                                                    border_bottom="1px solid #f0f0f0",
                                                    _hover={"background": "#f0f4ff"},
                                                    on_click=PortalState.select_director_for_llp_partner(r["id"]),
                                                ),
                                            ),
                                            border="1.5px solid #d0d0d0",
                                            border_radius="0.5rem",
                                            background="white",
                                            width="100%",
                                            max_height="180px",
                                            overflow_y="auto",
                                        ),
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                            ),
                            rx.cond(
                                PortalState.llp_partner_selected_director_name != "",
                                rx.box(
                                    rx.hstack(
                                        rx.icon("circle-check", size=16, color="#16a34a"),
                                        rx.text(PortalState.llp_partner_selected_director_name, size="2", color="#166534"),
                                        spacing="2",
                                    ),
                                    padding="0.5rem 0.75rem",
                                    background="#dcfce7",
                                    border_radius="0.5rem",
                                    border_left="3px solid #16a34a",
                                    width="100%",
                                ),
                            ),
                            rx.grid(
                                _form_input("Designation", "e.g. Designated Partner", PortalState.llp_partner_designation, PortalState.handle_llp_partner_designation_change),
                                _form_select("Signatory", ["Yes", "No"], PortalState.llp_partner_is_signatory, PortalState.handle_llp_partner_is_signatory_change),
                                columns="2", spacing="3", width="100%",
                            ),
                            rx.grid(
                                _form_date_input("Date of Appointment", PortalState.llp_partner_appointment_date, PortalState.handle_llp_partner_appointment_date_change),
                                _form_date_input("Cessation Date (if applicable)", PortalState.llp_partner_cessation_date, PortalState.handle_llp_partner_cessation_date_change),
                                columns="2", spacing="3", width="100%",
                            ),
                            rx.hstack(
                                rx.spacer(),
                                rx.cond(
                                    PortalState.llp_partner_editing_id != "",
                                    rx.button(
                                        "Cancel",
                                        on_click=PortalState.cancel_edit_llp_partner,
                                        variant="outline",
                                        color_scheme="gray",
                                        size="3",
                                    ),
                                ),
                                rx.cond(
                                    PortalState.llp_partner_editing_id != "",
                                    rx.button(
                                        rx.hstack(rx.icon("save", size=16), rx.text("Save Changes"), spacing="2"),
                                        on_click=PortalState.add_director_to_llp,
                                        loading=PortalState.is_saving,
                                        disabled=PortalState.is_saving,
                                        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                        color="white",
                                        size="3",
                                    ),
                                    rx.button(
                                        rx.hstack(rx.icon("user-round-plus", size=16), rx.text("Add Partner"), spacing="2"),
                                        on_click=PortalState.add_director_to_llp,
                                        loading=PortalState.is_saving,
                                        disabled=PortalState.is_saving,
                                        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                        color="white",
                                        size="3",
                                    ),
                                ),
                                width="100%",
                                spacing="2",
                            ),
                            rx.cond(
                                PortalState.llp_partner_error != "",
                                rx.box(
                                    rx.hstack(
                                        rx.icon("circle-alert", size=16, color="#dc2626"),
                                        rx.text(PortalState.llp_partner_error, size="2", color="#dc2626"),
                                        spacing="2",
                                    ),
                                    padding="0.75rem",
                                    border_radius="0.5rem",
                                    background="#fee2e2",
                                    border_left="4px solid #dc2626",
                                    width="100%",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Close",
                            on_click=PortalState.close_manage_llp_partners,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="820px",
                width="90%",
                max_height="90vh",
                overflow_y="auto",
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


def manage_llp_companies_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_manage_llp_companies,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("link", size=22, color="#667eea"),
                        rx.vstack(
                            rx.heading("Linked Companies", size="5", color="#1a1a1a", weight="bold"),
                            rx.text(PortalState.managing_llp_name, size="2", color="#667eea", weight="medium"),
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_manage_llp_companies,
                            variant="ghost",
                            size="1",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    rx.vstack(
                        rx.text("Linked Companies", size="3", weight="bold", color="#1a1a1a"),
                        rx.cond(
                            PortalState.llp_companies.length() == 0,
                            rx.text("No companies linked yet.", size="2", color="#aaa"),
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("CIN", font_weight="700", color="white", font_size="0.85rem"),
                                        rx.table.column_header_cell("Company Name", font_weight="700", color="white", font_size="0.85rem"),
                                        rx.table.column_header_cell("Relationship", font_weight="700", color="white", font_size="0.85rem"),
                                        rx.table.column_header_cell("", font_weight="700", color="white"),
                                    ),
                                    background="linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        PortalState.llp_companies,
                                        lambda c: rx.table.row(
                                            rx.table.cell(rx.text(c["cin"], size="2", font_weight="600", color="#1a1a1a")),
                                            rx.table.cell(rx.text(c["name"], size="2", color="#1a1a1a")),
                                            rx.table.cell(
                                                rx.cond(
                                                    c["relationship_note"] != "",
                                                    rx.text(c["relationship_note"], size="2", color="#1a1a1a"),
                                                    rx.text("-", size="2", color="#aaa"),
                                                )
                                            ),
                                            rx.table.cell(
                                                rx.cond(
                                                    (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                                                    rx.cond(
                                                        PortalState.confirm_remove_llp_company_id == c["link_id"],
                                                        rx.hstack(
                                                            rx.text("Remove?", size="1", color="#dc2626", weight="bold"),
                                                            rx.button(
                                                                "Yes",
                                                                on_click=PortalState.remove_company_from_llp(c["link_id"]),
                                                                color_scheme="red",
                                                                size="1",
                                                            ),
                                                            rx.button(
                                                                "No",
                                                                on_click=PortalState.cancel_remove_llp_company,
                                                                variant="outline",
                                                                size="1",
                                                            ),
                                                            spacing="1",
                                                            align_items="center",
                                                        ),
                                                        rx.button(
                                                            rx.icon("x", size=12),
                                                            on_click=PortalState.prompt_remove_llp_company(c["link_id"]),
                                                            color_scheme="red",
                                                            variant="ghost",
                                                            size="1",
                                                        ),
                                                    ),
                                                )
                                            ),
                                            border_bottom="1px solid #f0f0f0",
                                        ),
                                    )
                                ),
                                width="100%",
                                size="2",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.cond(
                        (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                        rx.vstack(
                            rx.divider(),
                            rx.text("Link a Company", size="2", weight="bold", color="#333"),
                            rx.vstack(
                                rx.el.input(
                                    placeholder="Search company by CIN or name…",
                                    value=PortalState.llp_company_search_query,
                                    on_change=PortalState.handle_llp_company_search,
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
                                rx.cond(
                                    PortalState.llp_company_search_results.length() > 0,
                                    rx.box(
                                        rx.foreach(
                                            PortalState.llp_company_search_results,
                                            lambda r: rx.box(
                                                rx.hstack(
                                                    rx.text(r["cin"], size="2", font_weight="600", color="#667eea"),
                                                    rx.text(r["name"], size="2", color="#333"),
                                                    spacing="2",
                                                ),
                                                padding="0.5rem 0.75rem",
                                                cursor="pointer",
                                                border_bottom="1px solid #f0f0f0",
                                                _hover={"background": "#f0f4ff"},
                                                on_click=PortalState.select_company_for_llp(r["id"]),
                                            ),
                                        ),
                                        border="1.5px solid #d0d0d0",
                                        border_radius="0.5rem",
                                        background="white",
                                        width="100%",
                                        max_height="180px",
                                        overflow_y="auto",
                                    ),
                                ),
                                rx.cond(
                                    PortalState.llp_company_selected_name != "",
                                    rx.box(
                                        rx.hstack(
                                            rx.icon("circle-check", size=16, color="#16a34a"),
                                            rx.text(PortalState.llp_company_selected_name, size="2", color="#166534"),
                                            spacing="2",
                                        ),
                                        padding="0.5rem 0.75rem",
                                        background="#dcfce7",
                                        border_radius="0.5rem",
                                        border_left="3px solid #16a34a",
                                        width="100%",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Relationship (optional)", size="2", weight="bold", color="#333"),
                                    rx.el.input(
                                        placeholder="e.g. Subsidiary, Group entity",
                                        value=PortalState.llp_company_relationship_note,
                                        on_change=PortalState.handle_llp_company_relationship_note_change,
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
                                ),
                                rx.spacer(),
                                rx.button(
                                    rx.hstack(rx.icon("link", size=16), rx.text("Link Company"), spacing="2"),
                                    on_click=PortalState.link_company_to_llp,
                                    loading=PortalState.is_saving,
                                    disabled=PortalState.is_saving,
                                    background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                    color="white",
                                    size="3",
                                    align_self="flex-end",
                                ),
                                width="100%",
                                align_items="flex-end",
                            ),
                            rx.cond(
                                PortalState.llp_company_error != "",
                                rx.box(
                                    rx.hstack(
                                        rx.icon("circle-alert", size=16, color="#dc2626"),
                                        rx.text(PortalState.llp_company_error, size="2", color="#dc2626"),
                                        spacing="2",
                                    ),
                                    padding="0.75rem",
                                    border_radius="0.5rem",
                                    background="#fee2e2",
                                    border_left="4px solid #dc2626",
                                    width="100%",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Close",
                            on_click=PortalState.close_manage_llp_companies,
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                        ),
                        width="100%",
                        padding_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="white",
                border_radius="0.75rem",
                padding="2rem",
                max_width="640px",
                width="90%",
                max_height="90vh",
                overflow_y="auto",
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


def _filter_dropdown(
    label: str,
    is_open,
    toggle_handler,
    search_value,
    search_handler,
    options_var,
    selected_var,
    toggle_option_handler,
) -> rx.Component:
    return rx.box(
        rx.button(
            rx.hstack(
                rx.text(
                    label,
                    size="1",
                    weight="medium",
                    color=rx.cond(selected_var.length() > 0, "#667eea", "#444"),
                ),
                rx.cond(
                    selected_var.length() > 0,
                    rx.badge(selected_var.length(), color_scheme="violet", variant="solid", size="1"),
                ),
                rx.cond(
                    is_open,
                    rx.icon("chevron-up", size=12, color="#666"),
                    rx.icon("chevron-down", size=12, color="#666"),
                ),
                spacing="1",
                align_items="center",
            ),
            on_click=toggle_handler,
            variant="outline",
            size="1",
            style={
                "border": rx.cond(selected_var.length() > 0, "1.5px solid #667eea", "1.5px solid #d0d0d0"),
                "background": "white",
                "cursor": "pointer",
                "border_radius": "0.5rem",
                "padding": "0.375rem 0.75rem",
                "min_width": "100px",
            },
        ),
        rx.cond(
            is_open,
            rx.box(
                rx.vstack(
                    rx.el.input(
                        placeholder="Search...",
                        value=search_value,
                        on_change=search_handler,
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "0.375rem 0.625rem",
                            "border_radius": "0.375rem",
                            "border": "1.5px solid #d0d0d0",
                            "background_color": "white",
                            "font_size": "0.8rem",
                            "color": "#1a1a1a",
                            "outline": "none",
                            "box_sizing": "border-box",
                        },
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.checkbox(
                                checked=selected_var.length() == 0,
                                on_change=toggle_option_handler("ALL"),
                                size="1",
                            ),
                            rx.text("All", size="1", color="#1a1a1a", weight="medium"),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.divider(margin_y="0.25rem"),
                        rx.foreach(
                            options_var,
                            lambda opt: rx.hstack(
                                rx.checkbox(
                                    checked=(selected_var.length() == 0) | selected_var.contains(opt),
                                    on_change=toggle_option_handler(opt),
                                    size="1",
                                ),
                                rx.text(opt, size="1", color="#1a1a1a"),
                                spacing="2",
                                align_items="center",
                            ),
                        ),
                        spacing="2",
                        align_items="start",
                        max_height="180px",
                        overflow_y="auto",
                        width="100%",
                    ),
                    spacing="2",
                    padding="0.625rem",
                    width="100%",
                ),
                position="absolute",
                top="calc(100% + 4px)",
                left="0",
                min_width="210px",
                background="white",
                border_radius="0.5rem",
                border="1.5px solid #e0e0e0",
                box_shadow="0 4px 16px rgba(0,0,0,0.12)",
                z_index="600",
            ),
        ),
        position="relative",
        display="inline-block",
    )


def companies_section() -> rx.Component:
    return rx.vstack(
        rx.cond(
            PortalState.class_dropdown_open | PortalState.category_dropdown_open | PortalState.sub_category_dropdown_open,
            rx.box(
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                z_index="499",
                on_click=PortalState.close_all_dropdowns,
            ),
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("search", size=20, color="#667eea"),
                    rx.vstack(
                        rx.text("Quick Search", size="2", weight="bold", color="#333"),
                        rx.text("Filter by CIN, name, class, category or sub category", size="1", color="#999"),
                        spacing="1",
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.el.input(
                        placeholder="Enter CIN or company name...",
                        value=PortalState.search_query,
                        on_change=PortalState.handle_search_input,
                        on_key_down=PortalState.handle_search_key_down,
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "0.75rem 1rem",
                            "border_radius": "0.625rem",
                            "border": "2px solid #e0e0e0",
                            "background_color": "white",
                            "font_size": "1rem",
                            "font_weight": "500",
                            "color": "#1a1a1a",
                            "outline": "none",
                            "box_sizing": "border-box",
                            "transition": "border-color 0.2s",
                        },
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
                rx.hstack(
                    _filter_dropdown(
                        "Class",
                        PortalState.class_dropdown_open,
                        PortalState.toggle_class_dropdown,
                        PortalState.class_search,
                        PortalState.handle_class_search,
                        PortalState.filtered_class_options,
                        PortalState.filter_classes,
                        PortalState.toggle_filter_class,
                    ),
                    _filter_dropdown(
                        "Category",
                        PortalState.category_dropdown_open,
                        PortalState.toggle_category_dropdown,
                        PortalState.category_search,
                        PortalState.handle_category_search,
                        PortalState.filtered_category_options,
                        PortalState.filter_categories,
                        PortalState.toggle_filter_category,
                    ),
                    _filter_dropdown(
                        "Sub Category",
                        PortalState.sub_category_dropdown_open,
                        PortalState.toggle_sub_category_dropdown,
                        PortalState.sub_category_search,
                        PortalState.handle_sub_category_search,
                        PortalState.filtered_sub_category_options,
                        PortalState.filter_sub_categories,
                        PortalState.toggle_filter_sub_category,
                    ),
                    rx.cond(
                        (PortalState.filter_classes.length() > 0) | (PortalState.filter_categories.length() > 0) | (PortalState.filter_sub_categories.length() > 0),
                        rx.button(
                            rx.hstack(rx.icon("x", size=14), rx.text("Clear"), spacing="1"),
                            on_click=PortalState.clear_filters,
                            variant="outline",
                            color_scheme="gray",
                            size="1",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                    align_items="center",
                    flex_wrap="wrap",
                    padding="0.25rem 0",
                    overflow="visible",
                ),
                spacing="4",
                width="100%",
                overflow="visible",
            ),
            width="100%",
            padding="1.5rem",
            background="white",
            border_radius="0.75rem",
            box_shadow="0 2px 12px rgba(0,0,0,0.06)",
            overflow="visible",
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
            # Tab navigation bar
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
                    rx.button(
                        rx.hstack(rx.icon("user-round", size=15), rx.text("Directors"), spacing="2"),
                        on_click=PortalState.switch_tab("directors"),
                        variant="ghost",
                        size="2",
                        color=rx.cond(PortalState.active_tab == "directors", "white", "rgba(255,255,255,0.65)"),
                        background=rx.cond(PortalState.active_tab == "directors", "rgba(255,255,255,0.22)", "transparent"),
                        border_radius="0.5rem",
                        _hover={"background": "rgba(255,255,255,0.15)", "color": "white"},
                    ),
                    rx.button(
                        rx.hstack(rx.icon("building", size=15), rx.text("LLPs"), spacing="2"),
                        on_click=PortalState.switch_tab("llps"),
                        variant="ghost",
                        size="2",
                        color=rx.cond(PortalState.active_tab == "llps", "white", "rgba(255,255,255,0.65)"),
                        background=rx.cond(PortalState.active_tab == "llps", "rgba(255,255,255,0.22)", "transparent"),
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
                rx.cond(
                    PortalState.active_tab == "directors",
                    directors_section(),
                    rx.cond(
                        PortalState.active_tab == "llps",
                        llps_section(),
                        admin_panel(),
                    ),
                ),
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        add_company_dialog(),
        edit_company_dialog(),
        add_director_dialog(),
        edit_director_dialog(),
        manage_company_directors_dialog(),
        add_llp_dialog(),
        edit_llp_dialog(),
        manage_llp_partners_dialog(),
        manage_llp_companies_dialog(),
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
        rx.el.style("input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; } input[type=number] { -moz-appearance: textfield; }"),
        rx.cond(PortalState.is_authenticated, dashboard_page(), login_page()),
        rx.cond(PortalState.is_saving, loading_overlay()),
    )


app = rx.App()
# on_load fires on every page load AND on every WebSocket reconnect.
# on_page_load resets all form state, so stale disk-persisted state can
# never cause the Add Company dialog to reappear after saving.
app.add_page(index, title="CDM Portal", on_load=PortalState.on_page_load)

