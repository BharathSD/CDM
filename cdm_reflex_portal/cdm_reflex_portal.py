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
    ShareCapital,
    ShareCapitalDetails,
    AuditorMaster,
    ShareholderMaster,
)

init_db()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_CIN_RE = re.compile(r"^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$")
_LLPIN_RE = re.compile(r"^[A-Z]{3}-?\d{4}$")

def _parse_doi(value: str) -> bool:
    """Return True for a valid ISO date (YYYY-MM-DD) that is not in the future."""
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d").date()
        return parsed <= datetime.today().date()
    except (TypeError, ValueError):
        return False


def is_valid_cin(cin: str) -> bool:
    return bool(_CIN_RE.fullmatch(cin.strip().upper()))


def is_valid_llpin(llpin: str) -> bool:
    return bool(_LLPIN_RE.fullmatch(llpin.strip().upper()))


def _normalize_date(value: str | None) -> str:
    """Normalize ISO or legacy DD/MM/YYYY/DD-MM-YYYY values to ISO YYYY-MM-DD."""
    if not value:
        return ""
    value = str(value).strip()
    if not value:
        return ""
    if _ISO_DATE_RE.fullmatch(value):
        return value
    for pattern in (r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$",):
        m = re.match(pattern, value)
        if m:
            try:
                parsed = datetime.strptime(
                    f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}",
                    "%d/%m/%Y",
                )
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                return ""
    return ""


def _format_date(value: str | None) -> str:
    """Return dates in the single application-wide ISO format."""
    return _normalize_date(value)


def _input_date_value(value):
    """Return a date-input-safe ISO value; supports Reflex Vars and legacy strings."""
    if isinstance(value, str):
        return _normalize_date(value)
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
    is_non_client: bool = False
    form_cin: str = ""
    form_name: str = ""
    form_pan: str = ""
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
    visible_company_id: str = ""

    # ── Edit-company form ─────────────────────────────────────────────────────
    show_edit_company_form: bool = False
    is_edit_form_non_client: bool = False
    edit_company_id: str = ""
    edit_form_cin: str = ""
    edit_form_name: str = ""
    edit_form_pan: str = ""
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
    edit_company_tab: str = "company"

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
    # Director association viewer
    show_director_associations: bool = False
    viewing_director_id: str = ""
    viewing_director_name: str = ""
    viewing_director_din: str = ""
    director_company_associations: list[dict] = []
    director_llp_associations: list[dict] = []

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
    form_llp_is_non_client: bool = False
    form_llpin: str = ""
    form_llp_name: str = ""
    form_llp_pan: str = ""
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
    edit_form_llp_is_non_client: bool = False
    edit_llp_id: str = ""
    edit_form_llpin: str = ""
    edit_form_llp_name: str = ""
    edit_form_llp_pan: str = ""
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

    # ── Share Capital ─────────────────────────────────────────
    share_capital_company_id: str = ""
    form_capital_type: str = ""
    show_share_capital: bool = False
    share_capital_type: str = "EQUITY"

    # Equity / Preference - Overall
    share_capital_authorized_shares: str = ""
    share_capital_paid_up_shares: str = ""
    share_capital_authorized_amount: str = ""
    share_capital_paid_up_amount: str = ""

    # Class A
    show_class_a: bool = False
    share_capital_a_authorized_shares: str = ""
    share_capital_a_paid_up_shares: str = ""
    share_capital_a_authorized_nominal: str = ""
    share_capital_a_paid_up_nominal: str = ""
    share_capital_a_authorized_amount: str = ""
    share_capital_a_paid_up_amount: str = ""

    # Class B
    show_class_b: bool = False
    share_capital_b_authorized_shares: str = ""
    share_capital_b_paid_up_shares: str = ""
    share_capital_b_authorized_nominal: str = ""
    share_capital_b_paid_up_nominal: str = ""
    share_capital_b_authorized_amount: str = ""
    share_capital_b_paid_up_amount: str = ""


    # Auditor Master

    # Auditor details
    edit_auditor_srn: str = ""
    edit_auditor_category: str = "Individual"

    edit_auditor_firm_name: str = ""
    edit_auditor_firm_membership_no: str = ""
    edit_auditor_firm_pan: str = ""
    edit_auditor_firm_email: str = ""

    edit_auditor_address: str = ""
    edit_auditor_country: str = ""
    edit_auditor_state: str = ""
    edit_auditor_city: str = ""
    edit_auditor_pin_code: str = ""

    edit_auditor_partner_membership_no: str = ""
    edit_auditor_name: str = ""
    edit_auditor_pan: str = ""
    edit_auditor_mobile: str = ""
    edit_auditor_email: str = ""
    edit_auditor_designation: str = ""

    # Shareholder Master

    edit_shareholder_id: str = ""

    edit_shareholder_name: str = ""
    edit_shareholder_address: str = ""
    edit_shareholder_email: str = ""
    edit_shareholder_registration_number_cin: str = ""
    edit_shareholder_father_mother_spouse_name: str = ""
    edit_shareholder_status: str = ""
    edit_shareholder_occupation: str = ""
    edit_shareholder_pan: str = ""
    edit_shareholder_nationality: str = ""

    edit_shareholder_date_of_becoming_member: str = ""
    edit_shareholder_date_of_declaration_u_s_89: str = ""
    edit_shareholder_beneficial_owner_name_address: str = ""
    edit_shareholder_date_of_receipt_of_nomination: str = ""
    edit_shareholder_nominee_name_address: str = ""
    edit_shareholder_date_of_cessation_of_membership: str = ""

    edit_shareholder_allotment_transfer_no: str = ""
    edit_shareholder_date_of_allotment_transfer: str = ""
    edit_shareholder_number_of_shares: str = ""
    edit_shareholder_distinctive_numbers: str = ""
    edit_shareholder_folio_of_transferor: str = ""
    edit_shareholder_name_of_transferor: str = ""
    edit_shareholder_date_of_issue_endorsement: str = ""
    edit_shareholder_certificate_no: str = ""
    

    # ---------------------------------------------------------
    # Shareholder Master
    # ---------------------------------------------------------

    show_add_shareholder: bool = False

    shareholder_name_of_member: str = ""
    shareholder_address: str = ""
    shareholder_email: str = ""
    shareholder_registration_number_cin: str = ""
    shareholder_father_mother_spouse_name: str = ""
    shareholder_status: str = ""
    shareholder_occupation: str = ""
    shareholder_pan: str = ""
    shareholder_nationality: str = ""

    shareholder_date_of_becoming_member: str = ""
    shareholder_date_of_declaration_u_s_89: str = ""
    shareholder_beneficial_owner_name_address: str = ""
    shareholder_date_of_receipt_of_nomination: str = ""
    shareholder_nominee_name_address: str = ""
    shareholder_date_of_cessation_of_membership: str = ""

    shareholder_allotment_transfer_no: str = ""
    shareholder_date_of_allotment_transfer: str = ""
    shareholder_number_of_shares: str = ""
    shareholder_distinctive_numbers: str = ""
    shareholder_folio_of_transferor: str = ""
    shareholder_name_of_transferor: str = ""
    shareholder_date_of_issue_endorsement: str = ""
    shareholder_certificate_no: str = ""
    shareholders: list[dict] = []
    # ── Internal helpers ──────────────────────────────────────────────────────
    def toggle_company_sensitive_data(self, company_id: str):
        if self.visible_company_id == company_id:
            self.visible_company_id = ""
        else:
            self.visible_company_id = company_id

    def open_edit_company_with_tabs(self, company_id: str):
        self.open_edit_company_form(company_id)
        self.edit_company_tab = "company"


    def handle_edit_auditor_srn_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_srn = value

    def handle_edit_auditor_category_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_category = value

    def handle_edit_auditor_firm_name_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_firm_name = value

    def handle_edit_auditor_firm_membership_no_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_firm_membership_no = value

    def handle_edit_auditor_firm_pan_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_firm_pan = value

    def handle_edit_auditor_firm_email_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_firm_email = value

    def handle_edit_auditor_address_change(self, value: str):
        if self.show_edit_company_form:
                self.edit_auditor_address = value

    def handle_edit_auditor_country(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_country = value

    def handle_edit_auditor_state(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_state = value

    def handle_edit_auditor_city(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_city = value
                

    def handle_edit_auditor_pin_code(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_pin_code = value

    def handle_edit_auditor_designation(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_designation = value

    def handle_edit_auditor_email(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_email = value

    def handle_edit_auditor_mobile(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_mobile = value

    def handle_edit_auditor_pan(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_pan = value

    def handle_edit_auditor_name(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_name = value

    def handle_edit_auditor_partner_membership_no(self, value: str):
        if self.show_edit_company_form:
            self.edit_auditor_partner_membership_no = value

    def _clear_form(self) -> None:
        """Reset every company-form var to its default."""
        self.show_add_form = False
        self.is_saving = False
        self.is_non_client = False
        self.form_cin = ""
        self.form_name = ""
        self.form_pan = ""
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
        self.is_edit_form_non_client = False
        self.edit_company_id = ""
        self.edit_form_cin = ""
        self.edit_form_name = ""
        self.edit_form_pan = ""
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
        self.edit_form_authorised_capital = ""
        self.edit_form_paid_up_capital = ""
        self.edit_form_number_of_members = ""
        self.edit_form_date_of_last_agm = ""
        self.edit_form_date_of_balance_sheet = ""
        self.edit_form_listed_status = ""
        self.edit_form_suspended_at_stock_exchange = ""
        self.edit_form_pin_code = ""
        self.edit_form_phone = ""
        self.edit_form_country = ""

        # Auditor state must never leak from the previously opened company.
        self.edit_auditor_srn = ""
        self.edit_auditor_category = "Individual"
        self.edit_auditor_firm_name = ""
        self.edit_auditor_firm_membership_no = ""
        self.edit_auditor_firm_pan = ""
        self.edit_auditor_firm_email = ""
        self.edit_auditor_address = ""
        self.edit_auditor_country = ""
        self.edit_auditor_state = ""
        self.edit_auditor_city = ""
        self.edit_auditor_pin_code = ""
        self.edit_auditor_partner_membership_no = ""
        self.edit_auditor_name = ""
        self.edit_auditor_pan = ""
        self.edit_auditor_mobile = ""
        self.edit_auditor_email = ""
        self.edit_auditor_designation = ""

        self.edit_shareholder_id = ""
        self.shareholders = []
        self.share_capital_company_id = ""
        self.show_share_capital = False
        self.show_class_a = False
        self.show_class_b = False
        self.reset_share_capital_form()

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

    def _clear_director_associations(self) -> None:
        """Reset director association viewer state."""
        self.show_director_associations = False
        self.viewing_director_id = ""
        self.viewing_director_name = ""
        self.viewing_director_din = ""
        self.director_company_associations = []
        self.director_llp_associations = []

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
        self.form_llp_is_non_client = False
        self.form_llpin = ""
        self.form_llp_name = ""
        self.form_llp_pan = ""
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
        self.edit_form_llp_is_non_client = False
        self.edit_llp_id = ""
        self.edit_form_llpin = ""
        self.edit_form_llp_name = ""
        self.edit_form_llp_pan = ""
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
        self._clear_director_associations()
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
                    "pan": r.pan or "",
                    "non_client": bool(r.non_client),
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

    def load_share_capital(self, company_id: str,capital_type: str):
        with SessionLocal() as session:

            rows = (
                session.query(ShareCapital, ShareCapitalDetails)
                .join(
                Company,
                Company.id == ShareCapital.company_id
            )
            .join(
                ShareCapitalDetails,
                ShareCapitalDetails.share_capital_id == ShareCapital.id
            )
            .filter(Company.id == company_id,
                    ShareCapital.capital_type == capital_type)
            .all()
        )
       
        if not rows:
            return

        # All rows have the same ShareCapital
        share_capital = rows[0][0]

        self.share_capital_type = share_capital.capital_type or ""

        for share_capital, detail in rows:

            if detail.class_type == "OVERALL":

                self.share_capital_authorized_shares = (
                    str(detail.authorized_shares) if detail.authorized_shares is not None else ""
                )

                self.share_capital_paid_up_shares = (
                    str(detail.paid_up_shares) if detail.paid_up_shares is not None else ""
                )

                self.share_capital_authorized_amount = (
                    str(detail.authorized_total_amount) if detail.authorized_total_amount is not None else ""
                )

                self.share_capital_paid_up_amount = (
                    str(detail.paid_up_total_amount) if detail.paid_up_total_amount is not None else ""
                )

            elif detail.class_type == "CLASS_A":

                self.share_capital_a_authorized_shares = (
                    str(detail.authorized_shares) if detail.authorized_shares is not None else ""
                )

                self.share_capital_a_paid_up_shares = (
                    str(detail.paid_up_shares) if detail.paid_up_shares is not None else ""
                )

                self.share_capital_a_authorized_nominal = (
                    str(detail.authorized_nominal_value) if detail.authorized_nominal_value is not None else ""
                )

                self.share_capital_a_paid_up_nominal = (
                    str(detail.paid_up_nominal_value) if detail.paid_up_nominal_value is not None else ""
                )

                self.share_capital_a_authorized_amount = (
                    str(detail.authorized_total_amount) if detail.authorized_total_amount is not None else ""
                )

                self.share_capital_a_paid_up_amount = (
                    str(detail.paid_up_total_amount) if detail.paid_up_total_amount is not None else ""
                )

            elif detail.class_type == "CLASS_B":

                self.share_capital_b_authorized_shares = (
                    str(detail.authorized_shares) if detail.authorized_shares is not None else ""
                )

                self.share_capital_b_paid_up_shares = (
                    str(detail.paid_up_shares) if detail.paid_up_shares is not None else ""
                )

                self.share_capital_b_authorized_nominal = (
                    str(detail.authorized_nominal_value) if detail.authorized_nominal_value is not None else ""
                )

                self.share_capital_b_paid_up_nominal = (
                    str(detail.paid_up_nominal_value) if detail.paid_up_nominal_value is not None else ""
                )

                self.share_capital_b_authorized_amount = (
                    str(detail.authorized_total_amount) if detail.authorized_total_amount is not None else ""
                )

                self.share_capital_b_paid_up_amount = (
                    str(detail.paid_up_total_amount) if detail.paid_up_total_amount is not None else ""
                )

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
                # Delete child records first because SQLite may not enforce FK cascades.
                session.query(AuditorMaster).filter(AuditorMaster.company_id == cid).delete(synchronize_session=False)
                shareholder_rows = session.query(ShareholderMaster).filter(ShareholderMaster.company_id == cid).all()
                for row in shareholder_rows:
                    session.delete(row)
                share_capitals = session.query(ShareCapital).filter(ShareCapital.company_id == cid).all()
                for sc in share_capitals:
                    session.query(ShareCapitalDetails).filter(ShareCapitalDetails.share_capital_id == sc.id).delete(synchronize_session=False)
                    session.delete(sc)
                session.delete(company)
                session.commit()
        self.load_companies()

    # ── Add-company form handlers ─────────────────────────────────────────────
    def handle_form_is_non_client_change(self, value: bool):
        self.is_non_client = value

    def handle_edit_form_is_non_client_change(self, value: bool):
        self.is_edit_form_non_client = value

    def handle_llp_is_non_client_change(self, value: bool):
            self.form_llp_is_non_client = value

    def handle_edit_llp_is_non_client_change(self, value: bool):
            self.edit_form_llp_is_non_client = value
           
    def handle_form_cin_change(self, value: str):
        if self.show_add_form:
            self.form_cin = value

    def handle_form_name_change(self, value: str):
        if self.show_add_form:
            self.form_name = value

    def handle_form_pan_change(self, value: str):
        if self.show_add_form:
            self.form_pan = value   

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
                self.is_edit_form_non_client = bool(c.get("non_client", False))
                self.edit_form_cin = c["cin"]
                self.edit_form_name = c["name"]
                self.edit_form_pan = c.get("pan", "")
                self.edit_form_class = c["class"] if c["class"] != "-" else ""
                self.edit_form_category = c["category"] if c["category"] != "-" else ""
                self.edit_form_sub_category = c["sub_category"] if c["sub_category"] != "-" else ""
                self.edit_form_doi = _normalize_date(c.get("doi", ""))
                self.edit_form_email = c["email"]
                self.edit_form_address = c["address"]
                self.edit_form_roc_code = c["roc_code"]
                self.edit_form_roc_office = c["roc_office"]
                self.edit_form_rd_name = c["rd_name"]
                self.edit_form_rd_region = c["rd_region"]
                self.edit_form_registration_number = c["registration_number"]
                self.edit_form_authorised_capital = c.get("authorised_capital", "")
                self.edit_form_paid_up_capital = c["paid_up_capital"]
                self.edit_form_number_of_members = c["number_of_members"]
                self.edit_form_date_of_last_agm = _normalize_date(c.get("date_of_last_agm", ""))
                self.edit_form_date_of_balance_sheet = _normalize_date(c.get("date_of_balance_sheet", ""))
                self.edit_form_listed_status = c["listed_status"]
                self.edit_form_suspended_at_stock_exchange = c["suspended_at_stock_exchange"]
                self.edit_form_pin_code = c["pin_code"]
                self.edit_form_phone = c["phone"]
                self.edit_form_country = c["country"]
                break

        # Load Auditor Details
        with SessionLocal() as session:
            auditor = (
                session.query(AuditorMaster)
                .filter(AuditorMaster.company_id == int(company_id))
                .first()
            )

            if auditor:
                self.edit_auditor_srn = auditor.srn or ""
                self.edit_auditor_category = auditor.auditor_category or "Individual"
                self.edit_auditor_firm_name = auditor.firm_name or ""
                self.edit_auditor_firm_membership_no = auditor.firm_membership_no or ""
                self.edit_auditor_firm_pan = auditor.firm_pan or ""
                self.edit_auditor_firm_email = auditor.firm_email or ""
                self.edit_auditor_address = auditor.address or ""
                self.edit_auditor_country = auditor.country or ""
                self.edit_auditor_state = auditor.state or ""
                self.edit_auditor_city = auditor.city or ""
                self.edit_auditor_pin_code = auditor.pin_code or ""
                self.edit_auditor_partner_membership_no = auditor.partner_membership_no or ""
                self.edit_auditor_name = auditor.auditor_name or ""
                self.edit_auditor_pan = auditor.auditor_pan or ""
                self.edit_auditor_mobile = auditor.mobile or ""
                self.edit_auditor_email = auditor.email or ""
                self.edit_auditor_designation = auditor.designation or ""

        self.show_edit_company_form = True
        
    def toggle_class_a(self):
        self.show_class_a = not self.show_class_a

    def toggle_class_b(self):
        self.show_class_b = not self.show_class_b


    def add_class_b(self):
        self.show_class_b = True

    def close_edit_company_form(self):
        self._clear_edit_company_form()

    def handle_edit_form_cin_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_cin = value

    def handle_edit_form_name_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_name = value

    def handle_edit_form_pan_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_pan = value

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
            self.form_doi = value

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
            self.form_date_of_last_agm = value

    def handle_form_date_of_balance_sheet_change(self, value: str):
        if self.show_add_form:
            self.form_date_of_balance_sheet = value

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
            self.edit_form_doi = value

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
            self.edit_form_date_of_last_agm = value

    def handle_edit_form_date_of_balance_sheet_change(self, value: str):
        if self.show_edit_company_form:
            self.edit_form_date_of_balance_sheet = value

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

    def handle_shareholder_name_of_member_change(self, value: str):
        self.shareholder_name_of_member = value


    def handle_shareholder_address_change(self, value: str):
        self.shareholder_address = value


    def handle_shareholder_email_change(self, value: str):
        self.shareholder_email = value


    def handle_shareholder_registration_number_cin_change(self, value: str):
        self.shareholder_registration_number_cin = value


    def handle_shareholder_father_mother_spouse_name_change(self, value: str):
        self.shareholder_father_mother_spouse_name = value


    def handle_shareholder_status_change(self, value: str):
        self.shareholder_status = value


    def handle_shareholder_occupation_change(self, value: str):
        self.shareholder_occupation = value


    def handle_shareholder_pan_change(self, value: str):
        self.shareholder_pan = value


    def handle_shareholder_nationality_change(self, value: str):
        self.shareholder_nationality = value


    def handle_shareholder_date_of_becoming_member_change(self, value: str):
        self.shareholder_date_of_becoming_member = value


    def handle_shareholder_date_of_declaration_u_s_89_change(self, value: str):
        self.shareholder_date_of_declaration_u_s_89 = value


    def handle_shareholder_beneficial_owner_name_address_change(self, value: str):
        self.shareholder_beneficial_owner_name_address = value


    def handle_shareholder_date_of_receipt_of_nomination_change(self, value: str):
        self.shareholder_date_of_receipt_of_nomination = value


    def handle_shareholder_nominee_name_address_change(self, value: str):
        self.shareholder_nominee_name_address = value


    def handle_shareholder_date_of_cessation_of_membership_change(self, value: str):
        self.shareholder_date_of_cessation_of_membership = value


    def handle_shareholder_allotment_transfer_no_change(self, value: str):
        self.shareholder_allotment_transfer_no = value


    def handle_shareholder_date_of_allotment_transfer_change(self, value: str):
        self.shareholder_date_of_allotment_transfer = value


    def handle_shareholder_number_of_shares_change(self, value: str):
        self.shareholder_number_of_shares = value


    def handle_shareholder_distinctive_numbers_change(self, value: str):
        self.shareholder_distinctive_numbers = value


    def handle_shareholder_folio_of_transferor_change(self, value: str):
        self.shareholder_folio_of_transferor = value


    def handle_shareholder_name_of_transferor_change(self, value: str):
        self.shareholder_name_of_transferor = value


    def handle_shareholder_date_of_issue_endorsement_change(self, value: str):
        self.shareholder_date_of_issue_endorsement = value


    def handle_shareholder_certificate_no_change(self, value: str):
        self.shareholder_certificate_no = value
    def save_edit_company(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.edit_form_error = "You do not have permission to edit companies."
            return

        cin = self.edit_form_cin.strip().upper()
        name = self.edit_form_name.strip()
        pan = self.edit_form_pan.strip()
        company_class = self.edit_form_class.strip()
        company_category = self.edit_form_category.strip()
        company_sub_category = self.edit_form_sub_category.strip()
        doi = _normalize_date(self.edit_form_doi.strip())
        email = self.edit_form_email.strip()
        address = self.edit_form_address.strip()

        self.edit_form_error = ""
        if not cin:
            self.edit_form_error = "CIN is required."
            return
        if not is_valid_cin(cin):
            self.edit_form_error = "Not a valid CIN."
            return
        if not name:
            self.edit_form_error = "Name is required."
            return

        # Non-client companies do not require client classification fields.
        if self.is_edit_form_non_client:
            registration_number = self.edit_form_registration_number.strip()
            if not registration_number:
                self.edit_form_error = "Registration Number is required."
                return
            if not registration_number.isnumeric():
                self.edit_form_error = "Registration Number must contain only digits."
                return
        else:
            if not company_class:
                self.edit_form_error = "Company Class is required."
                return
            if not company_category:
                self.edit_form_error = "Company Category is required."
                return
            if not company_sub_category:
                self.edit_form_error = "Company Sub Category is required."
                return

        if email and not _EMAIL_RE.match(email):
            self.edit_form_error = "Enter a valid email address."
            return
        if doi and not _parse_doi(doi):
            self.edit_form_error = "Date cannot be in the future and must be in YYYY-MM-DD format."
            return

        extra = {
            "pan": pan,
            "roc_code": self.edit_form_roc_code.strip(),
            "roc_office": self.edit_form_roc_office.strip(),
            "rd_name": self.edit_form_rd_name.strip(),
            "rd_region": self.edit_form_rd_region.strip(),
            "registration_number": self.edit_form_registration_number.strip(),
            "authorised_capital": str(self.edit_form_authorised_capital).strip(),
            "paid_up_capital": str(self.edit_form_paid_up_capital).strip(),
            "number_of_members": self.edit_form_number_of_members.strip(),
            "date_of_last_agm": _normalize_date(self.edit_form_date_of_last_agm.strip()),
            "date_of_balance_sheet": _normalize_date(self.edit_form_date_of_balance_sheet.strip()),
            "listed_status": self.edit_form_listed_status.strip(),
            "suspended": self.edit_form_suspended_at_stock_exchange.strip(),
            "pin_code": self.edit_form_pin_code.strip(),
            "phone": self.edit_form_phone.strip(),
            "country": self.edit_form_country.strip(),
            "non_client": self.is_edit_form_non_client,
            "auditor_srn": self.edit_auditor_srn.strip(),
            "auditor_category": self.edit_auditor_category.strip(),
            "auditor_firm_name": self.edit_auditor_firm_name.strip(),
            "auditor_firm_membership_no": self.edit_auditor_firm_membership_no.strip(),
            "auditor_firm_pan": self.edit_auditor_firm_pan.strip(),
            "auditor_firm_email": self.edit_auditor_firm_email.strip(),
            "auditor_address": self.edit_auditor_address.strip(),
            "auditor_country": self.edit_auditor_country.strip(),
            "auditor_state": self.edit_auditor_state.strip(),
            "auditor_city": self.edit_auditor_city.strip(),
            "auditor_pin_code": self.edit_auditor_pin_code.strip(),
            "auditor_partner_membership_no": self.edit_auditor_partner_membership_no.strip(),
            "auditor_name": self.edit_auditor_name.strip(),
            "auditor_pan": self.edit_auditor_pan.strip(),
            "auditor_mobile": self.edit_auditor_mobile.strip(),
            "auditor_email": self.edit_auditor_email.strip(),
            "auditor_designation": self.edit_auditor_designation.strip(),
        }

        cid = self.edit_company_id
        self._clear_edit_company_form()
        self.is_saving = True
        return PortalState.commit_edit_company(
            cid, cin, name, pan, company_class, company_category, company_sub_category,
            doi, email, address,
            extra["roc_code"], extra["roc_office"], extra["rd_name"], extra["rd_region"],
            extra["registration_number"], extra["authorised_capital"], extra["paid_up_capital"],
            extra["number_of_members"], extra["date_of_last_agm"], extra["date_of_balance_sheet"],
            extra["listed_status"], extra["suspended"], extra["pin_code"], extra["phone"], extra["country"],
            extra["non_client"], extra["auditor_srn"], extra["auditor_category"], extra["auditor_firm_name"],
            extra["auditor_firm_membership_no"], extra["auditor_firm_pan"], extra["auditor_firm_email"],
            extra["auditor_address"], extra["auditor_country"], extra["auditor_state"], extra["auditor_city"],
            extra["auditor_pin_code"], extra["auditor_partner_membership_no"], extra["auditor_name"],
            extra["auditor_pan"], extra["auditor_mobile"], extra["auditor_email"], extra["auditor_designation"],
        )

    def commit_edit_company(
        self, company_id: str, cin: str, name: str, pan: str = "",
        company_class: str = "", company_category: str = "", company_sub_category: str = "",
        doi: str = "", email: str = "", address: str = "", roc_code: str = "",
        roc_office: str = "", rd_name: str = "", rd_region: str = "", registration_number: str = "",
        authorised_capital: str = "", paid_up_capital: str = "", number_of_members: str = "",
        date_of_last_agm: str = "", date_of_balance_sheet: str = "", listed_status: str = "",
        suspended: str = "", pin_code: str = "", phone: str = "", country: str = "",
        non_client: bool = False, auditor_srn: str = "", auditor_category: str = "Individual",
        auditor_firm_name: str = "", auditor_firm_membership_no: str = "", auditor_firm_pan: str = "",
        auditor_firm_email: str = "", auditor_address: str = "", auditor_country: str = "",
        auditor_state: str = "", auditor_city: str = "", auditor_pin_code: str = "",
        auditor_partner_membership_no: str = "", auditor_name: str = "", auditor_pan: str = "",
        auditor_mobile: str = "", auditor_email: str = "", auditor_designation: str = "",
    ):
        try:
            cid = int(company_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid company ID '{company_id}'."
            self.is_saving = False
            return

        def _cap(v):
            return float(v) if str(v).strip() else None

        try:
            with SessionLocal() as session:
                existing = session.query(Company).filter(Company.cin == cin, Company.id != cid).first()
                if existing:
                    self.error_message = f"Another company with CIN '{cin}' already exists."
                    self.is_saving = False
                    return

                company = session.query(Company).filter(Company.id == cid).first()
                if not company:
                    self.error_message = f"Company with ID '{company_id}' was not found."
                    self.is_saving = False
                    return

                company.cin = cin
                company.name = name
                company.pan = pan or None
                company.company_class = company_class
                company.company_type = company_category
                company.non_client = bool(non_client)
                company.sub_category = company_sub_category
                company.date_of_incorporation = _normalize_date(doi) or None
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
                company.date_of_last_agm = _normalize_date(date_of_last_agm) or None
                company.date_of_balance_sheet = _normalize_date(date_of_balance_sheet) or None
                company.listed_status = listed_status or None
                company.suspended_at_stock_exchange = suspended or None
                company.pin_code = pin_code or None
                company.phone = phone or None
                company.country = country or None

                auditor_fields = [
                    auditor_srn, auditor_firm_name, auditor_firm_membership_no, auditor_firm_pan,
                    auditor_firm_email, auditor_address, auditor_country, auditor_state, auditor_city,
                    auditor_pin_code, auditor_partner_membership_no, auditor_name, auditor_pan,
                    auditor_mobile, auditor_email, auditor_designation,
                ]
                auditor_entered = any(str(v).strip() for v in auditor_fields)
                auditor = session.query(AuditorMaster).filter(AuditorMaster.company_id == cid).first()

                if auditor_entered:
                    if not auditor_srn.strip():
                        session.rollback()
                        self.error_message = "Auditor SRN is required when auditor details are entered."
                        self.is_saving = False
                        return
                    if auditor is None:
                        auditor = AuditorMaster(company_id=cid)
                    auditor.srn = auditor_srn.strip()
                    auditor.auditor_category = auditor_category or "Individual"
                    auditor.firm_name = auditor_firm_name or None
                    auditor.firm_membership_no = auditor_firm_membership_no or None
                    auditor.firm_pan = auditor_firm_pan or None
                    auditor.firm_email = auditor_firm_email or None
                    auditor.address = auditor_address or None
                    auditor.country = auditor_country or None
                    auditor.state = auditor_state or None
                    auditor.city = auditor_city or None
                    auditor.pin_code = auditor_pin_code or None
                    auditor.partner_membership_no = auditor_partner_membership_no or None
                    auditor.auditor_name = auditor_name or ""
                    auditor.auditor_pan = auditor_pan or None
                    auditor.mobile = auditor_mobile or None
                    auditor.email = auditor_email or None
                    auditor.designation = auditor_designation or None
                    session.add(auditor)
                elif auditor is not None:
                    # Existing auditor may intentionally be cleared. Since SRN is
                    # non-nullable, remove the row rather than setting SRN to NULL.
                    session.delete(auditor)

                session.commit()

        except Exception as e:
            self.is_saving = False
            self.error_message = f"Unable to save company: {e}"
            return

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
        pan = self.form_pan.strip()
        company_class = self.form_class.strip()
        company_category = self.form_category.strip()
        company_sub_category = self.form_sub_category.strip()
        doi = self.form_doi.strip()
        email = self.form_email.strip()
        address = self.form_address.strip()
        if not cin:
            self.form_error = "CIN is required."
            return
        if not is_valid_cin(cin):
            self.form_error = "Not a valid CIN."
            return
        if not name:
            self.form_error = "Name is required."
            return
        if self.is_non_client:
            if not self.form_registration_number:
                self.form_error = "Registration Number is required."
                return
            if not self.form_registration_number.isnumeric():
                self.form_error = "Registration Number must contain only digits."
                return
        if not self.is_non_client:
            if not company_class:
                self.form_error = "Company Class is required."
                return
            if not company_category:
                self.form_error = "Company Category is required."
                return
            if not company_sub_category:
                self.form_error = "Company Sub Category is required."
                return
            if email and not _EMAIL_RE.match(email):
                self.form_error = "Enter a valid email address."
                return
            if doi and not _parse_doi(doi):
                self.form_error = "Date cannot be in the future and must be in YYYY-MM-DD format."
                return

        extra = {
            "pan": pan,
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
            "non_client": self.is_non_client
        }
        self._clear_form()
        self.is_saving = True
        return PortalState.commit_save(
            cin, name, pan, company_class, company_category, company_sub_category,
            doi, email, address,
            extra["roc_code"], extra["roc_office"], extra["rd_name"], extra["rd_region"],
            extra["registration_number"],
            extra["authorised_capital"], extra["paid_up_capital"],
            extra["number_of_members"], extra["date_of_last_agm"],
            extra["date_of_balance_sheet"], extra["listed_status"],
            extra["suspended"], extra["pin_code"], extra["phone"], extra["country"],
            extra["non_client"],
        )
    def save_share_capital(self):
        if self.role not in ("ADMIN", "EDITOR"):
            self.form_error = "You do not have permission to add share capital details."
            return

        company_id = self.share_capital_company_id.strip()
        capital_type = self.share_capital_type.strip()

        if not company_id:
            self.form_error = "Company ID is required."
            return

        if not capital_type:
            self.form_error = "Capital Type is required."
            return

        whole_number_fields = [
            self.share_capital_authorized_shares,
            self.share_capital_paid_up_shares,
            self.share_capital_a_authorized_shares,
            self.share_capital_a_paid_up_shares,
            self.share_capital_b_authorized_shares,
            self.share_capital_b_paid_up_shares,
        ]
        for value in whole_number_fields:
            if value not in (None, ""):
                try:
                    number = float(value)
                    if number < 0 or not number.is_integer():
                        self.form_error = "Share counts must be non-negative whole numbers."
                        return
                except (TypeError, ValueError):
                    self.form_error = "Share counts must be valid numbers."
                    return

        decimal_fields = [
            self.share_capital_authorized_amount, self.share_capital_paid_up_amount,
            self.share_capital_a_authorized_nominal, self.share_capital_a_paid_up_nominal,
            self.share_capital_a_authorized_amount, self.share_capital_a_paid_up_amount,
            self.share_capital_b_authorized_nominal, self.share_capital_b_paid_up_nominal,
            self.share_capital_b_authorized_amount, self.share_capital_b_paid_up_amount,
        ]
        for value in decimal_fields:
            if value not in (None, ""):
                try:
                    if float(value) < 0:
                        self.form_error = "Share capital values cannot be negative."
                        return
                except (TypeError, ValueError):
                    self.form_error = "Share capital values must be valid numbers."
                    return

        details = [
            {
                "class_type": "OVERALL",
                "authorized_shares": self.share_capital_authorized_shares,
                "paid_up_shares": self.share_capital_paid_up_shares,
                "authorized_total_amount": self.share_capital_authorized_amount,
                "paid_up_total_amount": self.share_capital_paid_up_amount,
            },
            {
                "class_type": "CLASS_A",
                "authorized_shares": self.share_capital_a_authorized_shares,
                "paid_up_shares": self.share_capital_a_paid_up_shares,
                "authorized_nominal_value": self.share_capital_a_authorized_nominal,
                "paid_up_nominal_value": self.share_capital_a_paid_up_nominal,
                "authorized_total_amount": self.share_capital_a_authorized_amount,
                "paid_up_total_amount": self.share_capital_a_paid_up_amount,
            },
            {
                "class_type": "CLASS_B",
                "authorized_shares": self.share_capital_b_authorized_shares,
                "paid_up_shares": self.share_capital_b_paid_up_shares,
                "authorized_nominal_value": self.share_capital_b_authorized_nominal,
                "paid_up_nominal_value": self.share_capital_b_paid_up_nominal,
                "authorized_total_amount": self.share_capital_b_authorized_amount,
                "paid_up_total_amount": self.share_capital_b_paid_up_amount,
            },
        ]

        self.is_saving = True

        return PortalState.commit_save_share_capital(
            company_id,
            capital_type,
            details,
        )
    
    
    def commit_save_share_capital(
        self,
        id: str,
        capital_type: str,
        details: list[dict],
    ):
        try:
            cid = int(id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid company ID '{id}'."
            self.is_saving = False
            return

        def _int(v):
            if v in (None, ""):
                return None
            value = float(v)
            if not value.is_integer() or value < 0:
                raise ValueError("Share counts must be non-negative whole numbers.")
            return int(value)

        def _decimal(v):
            if v in (None, ""):
                return None
            value = float(v)
            if value < 0:
                raise ValueError("Amounts must be non-negative.")
            return value

        with SessionLocal() as session:

            # ---------------------------------------------------------
            # Check if company exists
            # ---------------------------------------------------------
            company = session.query(Company).filter(
                Company.id == cid
            ).first()

            if not company:
                self.error_message = f"No company found '{id}'."
                self.is_saving = False
                return

            # ---------------------------------------------------------
            # Get existing ShareCapital
            # based on company_id + capital_type
            # ---------------------------------------------------------
            share_capital = session.query(ShareCapital).filter(
                ShareCapital.company_id == cid,
                ShareCapital.capital_type == capital_type,
            ).first()
            
            
            if share_capital:
                # Existing record
                share_capital.update_dt = func.current_timestamp()


            else:
                # New record
                share_capital = ShareCapital(
                    company_id=cid,
                    capital_type=capital_type,
                )

                session.add(share_capital)
                session.flush()



            # ---------------------------------------------------------
            # Make sure ID is available
            # ---------------------------------------------------------
            session.flush()

            # ---------------------------------------------------------
            # Add / update ShareCapitalDetails
            # ---------------------------------------------------------
            for detail in details:

                class_type = detail.get("class_type")

                existing_detail = session.query(
                    ShareCapitalDetails
                ).filter(
                    ShareCapitalDetails.share_capital_id == share_capital.id,
                    ShareCapitalDetails.class_type == class_type,
                ).first()

                if existing_detail:

                    # ---------------------------------------------
                    # Update existing detail
                    # ---------------------------------------------
                    existing_detail.authorized_shares = _int(
                        detail.get("authorized_shares")
                    )

                    existing_detail.paid_up_shares = _int(
                        detail.get("paid_up_shares")
                    )

                    existing_detail.authorized_nominal_value = _decimal(
                        detail.get("authorized_nominal_value")
                    )

                    existing_detail.paid_up_nominal_value = _decimal(
                        detail.get("paid_up_nominal_value")
                    )

                    existing_detail.authorized_total_amount = _decimal(
                        detail.get("authorized_total_amount")
                    )

                    existing_detail.paid_up_total_amount = _decimal(
                        detail.get("paid_up_total_amount")
                    )


                else:

                    # ---------------------------------------------
                    # Create new detail
                    # ---------------------------------------------
                    session.add(
                        ShareCapitalDetails(
                            share_capital_id=share_capital.id,
                            class_type=class_type,

                            authorized_shares=_int(
                                detail.get("authorized_shares")
                            ),

                            paid_up_shares=_int(
                                detail.get("paid_up_shares")
                            ),

                            authorized_nominal_value=_decimal(
                                detail.get("authorized_nominal_value")
                            ),

                            paid_up_nominal_value=_decimal(
                                detail.get("paid_up_nominal_value")
                            ),

                            authorized_total_amount=_decimal(
                                detail.get("authorized_total_amount")
                            ),

                            paid_up_total_amount=_decimal(
                                detail.get("paid_up_total_amount")
                            ),
                        )
                    )

                    

            # ---------------------------------------------------------
            # Commit
            # ---------------------------------------------------------
            session.commit()

        self.is_saving = False
        self.reset_share_capital_form()
        self.share_capital_type = capital_type
        self.load_share_capital(str(cid), capital_type)
        self.close_share_capital()

    
    def commit_save(
        self,
        cin: str,
        name: str,
        pan: str = "",
        company_class: str = "",
        company_category: str = "",
        company_sub_category: str = "",
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
        non_client: bool = False,
    ):
        """Second hop: DB insert + table refresh."""
        def _cap(v): return float(v) if v else None
        non_client_value = int(bool(non_client))
        with SessionLocal() as session:
            if session.query(Company).filter(Company.cin == cin).first():
                self.error_message = f"A company with CIN '{cin}' already exists."
                self.is_saving = False
                return
            session.add(
                Company(
                    cin=cin,
                    name=name,
                    pan=pan or None,
                    company_class=company_class,
                    company_type=company_category,
                    non_client=bool(non_client_value),
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

    def set_edit_company_tab(self, tab: str):
        self.edit_company_tab = tab

    def show_share_capital_tab(self):
        self.edit_company_tab = "share_capital"
        return PortalState.open_share_capital(self.edit_company_id)
    
    def edit_shareholder(self, shareholder_id: str):
        if self.role not in ("ADMIN", "EDITOR"):
            self.error_message = "You do not have permission to edit shareholder details."
            return

        try:
            sid = int(shareholder_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid shareholder ID '{shareholder_id}'."
            return

        with SessionLocal() as session:
            shareholder = (
                session.query(ShareholderMaster)
                .filter(ShareholderMaster.id == sid)
                .first()
            )

            if not shareholder:
                self.error_message = f"Shareholder with ID '{shareholder_id}' was not found."
                return

            # Remember which record we are editing
            self.edit_shareholder_id = shareholder_id

            # Load existing values into the form
            self.shareholder_name_of_member = shareholder.name_of_member or ""
            self.shareholder_address = shareholder.address or ""
            self.shareholder_email = shareholder.email or ""
            self.shareholder_registration_number_cin = shareholder.registration_number_cin or ""
            self.shareholder_father_mother_spouse_name = shareholder.father_mother_spouse_name or ""
            self.shareholder_status = shareholder.status or ""
            self.shareholder_occupation = shareholder.occupation or ""
            self.shareholder_pan = shareholder.pan or ""
            self.shareholder_nationality = shareholder.nationality or ""

            self.shareholder_date_of_becoming_member = shareholder.date_of_becoming_member or ""
            self.shareholder_date_of_declaration_u_s_89 = shareholder.date_of_declaration_u_s_89 or ""
            self.shareholder_beneficial_owner_name_address = (
                shareholder.beneficial_owner_name_address or ""
            )
            self.shareholder_date_of_receipt_of_nomination = (
                shareholder.date_of_receipt_of_nomination or ""
            )
            self.shareholder_nominee_name_address = shareholder.nominee_name_address or ""
            self.shareholder_date_of_cessation_of_membership = (
                shareholder.date_of_cessation_of_membership or ""
            )

            self.shareholder_allotment_transfer_no = shareholder.allotment_transfer_no or ""
            self.shareholder_date_of_allotment_transfer = (
                shareholder.date_of_allotment_transfer or ""
            )
            self.shareholder_number_of_shares = shareholder.number_of_shares or ""
            self.shareholder_distinctive_numbers = shareholder.distinctive_numbers or ""
            self.shareholder_folio_of_transferor = shareholder.folio_of_transferor or ""
            self.shareholder_name_of_transferor = shareholder.name_of_transferor or ""
            self.shareholder_date_of_issue_endorsement = (
                shareholder.date_of_issue_endorsement or ""
            )
            self.shareholder_certificate_no = shareholder.certificate_no or ""

        # Open the same form used for Add Shareholder
        self.show_add_shareholder = True
    def save_shareholder(self):

        if self.role not in ("ADMIN", "EDITOR"):
            self.error_message = (
                "You do not have permission to add shareholder details."
            )
            return

        company_id = self.edit_company_id.strip()

        if not company_id:
            self.error_message = "Company ID is required."
            return

        name_of_member = self.shareholder_name_of_member.strip()

        if not name_of_member:
            self.error_message = "Name of the Member is required."
            return

        email = self.shareholder_email.strip()

        if email and not _EMAIL_RE.match(email):
            self.error_message = "Enter a valid email address."
            return

        self.is_saving = True

        return PortalState.commit_save_shareholder(
            company_id,

            self.shareholder_name_of_member.strip(),
            self.shareholder_address.strip(),
            self.shareholder_email.strip(),
            self.shareholder_registration_number_cin.strip(),
            self.shareholder_father_mother_spouse_name.strip(),
            self.shareholder_status.strip(),
            self.shareholder_occupation.strip(),
            self.shareholder_pan.strip(),
            self.shareholder_nationality.strip(),

            self.shareholder_date_of_becoming_member,
            self.shareholder_date_of_declaration_u_s_89,
            self.shareholder_beneficial_owner_name_address.strip(),
            self.shareholder_date_of_receipt_of_nomination,
            self.shareholder_nominee_name_address.strip(),
            self.shareholder_date_of_cessation_of_membership,

            self.shareholder_allotment_transfer_no.strip(),
            self.shareholder_date_of_allotment_transfer,
            self.shareholder_number_of_shares.strip(),
            self.shareholder_distinctive_numbers.strip(),
            self.shareholder_folio_of_transferor.strip(),
            self.shareholder_name_of_transferor.strip(),
            self.shareholder_date_of_issue_endorsement,
            self.shareholder_certificate_no.strip(),
            self.edit_shareholder_id,
        )

    def commit_save_shareholder(
        self, company_id: str, name_of_member: str, address: str, email: str,
        registration_number_cin: str, father_mother_spouse_name: str, status: str,
        occupation: str, pan: str, nationality: str, date_of_becoming_member: str,
        date_of_declaration_u_s_89: str, beneficial_owner_name_address: str,
        date_of_receipt_of_nomination: str, nominee_name_address: str,
        date_of_cessation_of_membership: str, allotment_transfer_no: str,
        date_of_allotment_transfer: str, number_of_shares: str, distinctive_numbers: str,
        folio_of_transferor: str, name_of_transferor: str, date_of_issue_endorsement: str,
        certificate_no: str, edit_shareholder_id: str = "",
    ):
        try:    
            cid = int(company_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid company ID '{company_id}'."
            self.is_saving = False
            return

        try:
            with SessionLocal() as session:
                company = session.query(Company).filter(Company.id == cid).first()
                if not company:
                    self.error_message = f"No company found with ID '{company_id}'."
                    self.is_saving = False
                    return

                shareholder = None
                if edit_shareholder_id:
                    try:
                        sid = int(edit_shareholder_id)
                    except (ValueError, TypeError):
                        self.error_message = f"Invalid shareholder ID '{edit_shareholder_id}'."
                        self.is_saving = False
                        return
                    shareholder = (session.query(ShareholderMaster)
                                   .filter(ShareholderMaster.id == sid, ShareholderMaster.company_id == cid)
                                   .first())
                    if not shareholder:
                        self.error_message = f"Shareholder with ID '{edit_shareholder_id}' was not found."
                        self.is_saving = False
                        return
                else:
                    shareholder = ShareholderMaster(company_id=cid, is_active=True)
                    session.add(shareholder)

                shareholder.name_of_member = name_of_member
                shareholder.address = address or None
                shareholder.email = email or None
                shareholder.registration_number_cin = registration_number_cin or None
                shareholder.father_mother_spouse_name = father_mother_spouse_name or None
                shareholder.status = status or None
                shareholder.occupation = occupation or None
                shareholder.pan = pan or None
                shareholder.nationality = nationality or None
                shareholder.date_of_becoming_member = date_of_becoming_member or None
                shareholder.date_of_declaration_u_s_89 = date_of_declaration_u_s_89 or None
                shareholder.beneficial_owner_name_address = beneficial_owner_name_address or None
                shareholder.date_of_receipt_of_nomination = date_of_receipt_of_nomination or None
                shareholder.nominee_name_address = nominee_name_address or None
                shareholder.date_of_cessation_of_membership = date_of_cessation_of_membership or None
                shareholder.allotment_transfer_no = allotment_transfer_no or None
                shareholder.date_of_allotment_transfer = date_of_allotment_transfer or None
                shareholder.number_of_shares = number_of_shares or None
                shareholder.distinctive_numbers = distinctive_numbers or None
                shareholder.folio_of_transferor = folio_of_transferor or None
                shareholder.name_of_transferor = name_of_transferor or None
                shareholder.date_of_issue_endorsement = date_of_issue_endorsement or None
                shareholder.certificate_no = certificate_no or None
                shareholder.is_active = True

                session.commit()
        except Exception as e:
            self.error_message = f"Unable to save shareholder: {e}"
            self.is_saving = False
            return

        self.is_saving = False
        self.show_add_shareholder = False
        self.edit_shareholder_id = ""
        self.get_shareholder_master()

    def get_shareholder_master(self):

        if not self.edit_company_id:
            self.shareholders = []
            return

        try:
            cid = int(self.edit_company_id)
        except (ValueError, TypeError):
            self.shareholders = []
            return

        with SessionLocal() as session:

            rows = (
                session.query(ShareholderMaster)
                .filter(
                    ShareholderMaster.company_id == cid,
                    ShareholderMaster.is_active == True,
                )
                .order_by(ShareholderMaster.id.desc())
                .all()
            )

            self.shareholders = [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id),

                    "name_of_member": r.name_of_member or "",
                    "address": r.address or "",
                    "email": r.email or "",
                    "registration_number_cin": r.registration_number_cin or "",
                    "father_mother_spouse_name": r.father_mother_spouse_name or "",
                    "status": r.status or "",
                    "occupation": r.occupation or "",
                    "pan": r.pan or "",
                    "nationality": r.nationality or "",

                    "date_of_becoming_member": r.date_of_becoming_member or "",
                    "date_of_declaration_u_s_89": (
                        r.date_of_declaration_u_s_89 or ""
                    ),
                    "beneficial_owner_name_address": (
                        r.beneficial_owner_name_address or ""
                    ),
                    "date_of_receipt_of_nomination": (
                        r.date_of_receipt_of_nomination or ""
                    ),
                    "nominee_name_address": r.nominee_name_address or "",
                    "date_of_cessation_of_membership": (
                        r.date_of_cessation_of_membership or ""
                    ),

                    "allotment_transfer_no": r.allotment_transfer_no or "",
                    "date_of_allotment_transfer": (
                        r.date_of_allotment_transfer or ""
                    ),
                    "number_of_shares": r.number_of_shares or "",
                    "distinctive_numbers": r.distinctive_numbers or "",
                    "folio_of_transferor": r.folio_of_transferor or "",
                    "name_of_transferor": r.name_of_transferor or "",
                    "date_of_issue_endorsement": (
                        r.date_of_issue_endorsement or ""
                    ),
                    "certificate_no": r.certificate_no or "",
                }
                for r in rows
            ]

        
    def show_company_tab(self):
        self.edit_company_tab = "company"

    def show_auditor_tab(self):
        self.edit_company_tab = "auditor"

    def show_shareholder_tab(self):
        self.edit_company_tab = "shareholder"
        return PortalState.get_shareholder_master()

    def open_add_shareholder(self):
        # Clear shareholder form
        self.shareholder_name_of_member = ""
        self.shareholder_address = ""
        self.shareholder_email = ""
        self.shareholder_registration_number_cin = ""
        self.shareholder_father_mother_spouse_name = ""
        self.shareholder_status = ""
        self.shareholder_occupation = ""
        self.shareholder_pan = ""
        self.shareholder_nationality = ""

        self.shareholder_date_of_becoming_member = ""
        self.shareholder_date_of_declaration_u_s_89 = ""
        self.shareholder_beneficial_owner_name_address = ""
        self.shareholder_date_of_receipt_of_nomination = ""
        self.shareholder_nominee_name_address = ""
        self.shareholder_date_of_cessation_of_membership = ""

        self.shareholder_allotment_transfer_no = ""
        self.shareholder_date_of_allotment_transfer = ""
        self.shareholder_number_of_shares = ""
        self.shareholder_distinctive_numbers = ""
        self.shareholder_folio_of_transferor = ""
        self.shareholder_name_of_transferor = ""
        self.shareholder_date_of_issue_endorsement = ""
        self.shareholder_certificate_no = ""

        self.edit_shareholder_id = ""
        self.show_add_shareholder = True


    def close_add_shareholder(self):
        self.show_add_shareholder = False
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
        if not din.isnumeric():
            self.form_director_error = "DIN must contain only digits."
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

    def open_director_associations(self, director_id: str):
        self._clear_director_associations()
        self.viewing_director_id = director_id
        try:
            did = int(director_id)
        except (ValueError, TypeError):
            self.error_message = f"Invalid director ID '{director_id}'."
            return

        with SessionLocal() as session:
            director = session.query(Director).filter(Director.id == did).first()
            if not director:
                self.error_message = "Director not found."
                return
            self.viewing_director_name = director.name
            self.viewing_director_din = director.din

            company_rows = (
                session.query(CompanyDirector, Company)
                .join(Company, CompanyDirector.company_id == Company.id)
                .filter(CompanyDirector.director_id == did)
                .order_by(Company.name.asc())
                .all()
            )
            self.director_company_associations = [
                {
                    "company_id": str(c.id),
                    "cin": c.cin,
                    "name": c.name,
                    "designation": cd.designation or "",
                    "category": cd.category or "",
                    "share_percent": str(cd.share_percent) if cd.share_percent is not None else "",
                    "original_appointment_date": _format_date(cd.original_appointment_date),
                    "current_designation_date": _format_date(cd.current_designation_date),
                    "cessation_date": _format_date(cd.cessation_date),
                }
                for cd, c in company_rows
            ]

            llp_rows = (
                session.query(LLPDirector, LLP)
                .join(LLP, LLPDirector.llp_id == LLP.id)
                .filter(LLPDirector.director_id == did)
                .order_by(LLP.name.asc())
                .all()
            )
            self.director_llp_associations = [
                {
                    "llp_id": str(l.id),
                    "llpin": l.llpin,
                    "name": l.name,
                    "designation": ld.designation or "",
                    "appointment_date": _format_date(ld.appointment_date),
                    "cessation_date": _format_date(ld.cessation_date),
                    "is_signatory": ld.is_signatory or "",
                }
                for ld, l in llp_rows
            ]

        self.show_director_associations = True

    def close_director_associations(self):
        self._clear_director_associations()

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

    # ── Share capital management ─────────────────────────────────────────────
    def _set_share_capital_number(self, field: str, value):
        text = "" if value is None else str(value)
        # Keep the text while the user is typing; validation/conversion happens on save.
        if text == "" or re.fullmatch(r"\d*(?:\.\d*)?", text):
            setattr(self, field, text)

    def set_share_capital_authorized_shares(self, value: str):
        self._set_share_capital_number("share_capital_authorized_shares", value)
    def set_share_capital_paid_up_shares(self, value: str):
        self._set_share_capital_number("share_capital_paid_up_shares", value)
    def set_share_capital_authorized_amount(self, value: str):
        self._set_share_capital_number("share_capital_authorized_amount", value)
    def set_share_capital_paid_up_amount(self, value: str):
        self._set_share_capital_number("share_capital_paid_up_amount", value)
    def set_share_capital_a_authorized_shares(self, value: str):
        self._set_share_capital_number("share_capital_a_authorized_shares", value)
    def set_share_capital_a_paid_up_shares(self, value: str):
        self._set_share_capital_number("share_capital_a_paid_up_shares", value)
    def set_share_capital_a_authorized_nominal(self, value: str):
        self._set_share_capital_number("share_capital_a_authorized_nominal", value)
    def set_share_capital_a_paid_up_nominal(self, value: str):
        self._set_share_capital_number("share_capital_a_paid_up_nominal", value)
    def set_share_capital_a_authorized_amount(self, value: str):
        self._set_share_capital_number("share_capital_a_authorized_amount", value)
    def set_share_capital_a_paid_up_amount(self, value: str):
        self._set_share_capital_number("share_capital_a_paid_up_amount", value)
    def set_share_capital_b_authorized_shares(self, value: str):
        self._set_share_capital_number("share_capital_b_authorized_shares", value)
    def set_share_capital_b_paid_up_shares(self, value: str):
        self._set_share_capital_number("share_capital_b_paid_up_shares", value)
    def set_share_capital_b_authorized_nominal(self, value: str):
        self._set_share_capital_number("share_capital_b_authorized_nominal", value)
    def set_share_capital_b_paid_up_nominal(self, value: str):
        self._set_share_capital_number("share_capital_b_paid_up_nominal", value)
    def set_share_capital_b_authorized_amount(self, value: str):
        self._set_share_capital_number("share_capital_b_authorized_amount", value)
    def set_share_capital_b_paid_up_amount(self, value: str):
        self._set_share_capital_number("share_capital_b_paid_up_amount", value)

    def reset_share_capital_form(self):
        self.share_capital_type = ""
        self.share_capital_authorized_shares = ""
        self.share_capital_paid_up_shares = ""
        self.share_capital_authorized_amount = ""
        self.share_capital_paid_up_amount = ""
        self.share_capital_a_authorized_shares = ""
        self.share_capital_a_paid_up_shares = ""
        self.share_capital_a_authorized_nominal = ""
        self.share_capital_a_paid_up_nominal = ""
        self.share_capital_a_authorized_amount = ""
        self.share_capital_a_paid_up_amount = ""
        self.share_capital_b_authorized_shares = ""
        self.share_capital_b_paid_up_shares = ""
        self.share_capital_b_authorized_nominal = ""
        self.share_capital_b_paid_up_nominal = ""
        self.share_capital_b_authorized_amount = ""
        self.share_capital_b_paid_up_amount = ""

    def open_share_capital(self, company_id: str):
        self.share_capital_company_id = company_id
    
        self.reset_share_capital_form()
        self.share_capital_type = "EQUITY"

        self.load_share_capital(
            company_id,
            self.share_capital_type,
        )

        self.show_share_capital = True


    def close_share_capital(self):
        self.show_share_capital = False
        self.show_class_a = False
        self.show_class_b = False

    def set_share_capital_type(self, value: str):
        if value == "Equity Share Capital":
            capital_type = "EQUITY"
        elif value == "Preference Share Capital":
            capital_type = "PREFERENCE"
        else:
            return

        self.reset_share_capital_form()
        self.share_capital_type = capital_type
        self.load_share_capital(self.share_capital_company_id, capital_type)


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
        self.assoc_original_appointment_date = value

    def handle_assoc_current_designation_date_change(self, value: str):
        self.assoc_current_designation_date = value

    def handle_assoc_cessation_date_change(self, value: str):
        self.assoc_cessation_date = value

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
                self.assoc_error = f"{label}: invalid date. Use YYYY-MM-DD."
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
                    "pan": r.pan or "",
                    "non_client": bool(r.non_client),
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

    def handle_form_llp_pan_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_pan = value

    def handle_form_llp_name_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_name = value

    def handle_form_llp_roc_name_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_roc_name = value

    def handle_form_llp_doi_change(self, value: str):
        if self.show_add_llp_form:
            self.form_llp_doi = value

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
            self.form_llp_strike_off_date = value

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
        pan = self.form_llp_pan.strip()
        if not llpin or not name:
            self.form_llp_error = "LLPIN and Name are required."
            return
        if not is_valid_llpin(llpin):
            self.form_llp_error = "Not a Valid LLPIN."
            return
        email = self.form_llp_email.strip()
        if email and not _EMAIL_RE.match(email):
            self.form_llp_error = "Enter a valid email address."
            return
        doi = self.form_llp_doi.strip()
        if doi and not _parse_doi(doi):
            self.form_llp_error = "Invalid date of incorporation. Use YYYY-MM-DD."
            return
        strike_off_date = self.form_llp_strike_off_date.strip()
        if strike_off_date and not _parse_doi(strike_off_date):
            self.form_llp_error = "Invalid strike-off date. Use YYYY-MM-DD."
            return
        extra = {
            "roc_name": self.form_llp_roc_name.strip(),
            "address": self.form_llp_address.strip(),
            "number_of_partners": self.form_llp_number_of_partners.strip(),
            "number_of_designated_partners": self.form_llp_number_of_designated_partners.strip(),
            "total_obligation": str(self.form_llp_total_obligation).strip(),
            "status_under_cirp": self.form_llp_status_under_cirp.strip(),
            "small_llp": self.form_llp_small_llp.strip(),
            "non_client": self.form_llp_is_non_client,
        }
        self._clear_llp_form()
        self.is_saving = True
        return PortalState.commit_save_llp(
            llpin, name, pan, extra["roc_name"], doi, email, extra["address"],
            extra["number_of_partners"], extra["number_of_designated_partners"],
            extra["total_obligation"], strike_off_date,
            extra["status_under_cirp"], extra["small_llp"],
            extra["non_client"]
        )

    def commit_save_llp(
        self, llpin: str, name: str, pan: str = "", roc_name: str = "", doi: str = "", email: str = "",
        address: str = "", number_of_partners: str = "", number_of_designated_partners: str = "",
        total_obligation: str = "", strike_off_date: str = "",
        status_under_cirp: str = "", small_llp: str = "",non_client: bool = False
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
                    pan=pan or None,
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
                    non_client=int(bool(non_client))
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
                self.edit_form_llp_is_non_client = bool(l.get("non_client", False))
                self.edit_form_llpin = l["llpin"]
                self.edit_form_llp_name = l["name"]
                self.edit_form_llp_pan = l.get("pan", "")
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

    def handle_edit_form_llp_pan_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_pan = value

    def handle_edit_form_llp_name_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_name = value

    def handle_edit_form_llp_roc_name_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_roc_name = value

    def handle_edit_form_llp_doi_change(self, value: str):
        if self.show_edit_llp_form:
            self.edit_form_llp_doi = value

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
            self.edit_form_llp_strike_off_date = value

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
        pan = self.edit_form_llp_pan.strip()
        if not llpin or not name:
            self.edit_form_llp_error = "LLPIN and Name are required."
            return
        email = self.edit_form_llp_email.strip()
        if email and not _EMAIL_RE.match(email):
            self.edit_form_llp_error = "Enter a valid email address."
            return
        doi = self.edit_form_llp_doi.strip()
        if doi and not _parse_doi(doi):
            self.edit_form_llp_error = "Invalid date of incorporation. Use YYYY-MM-DD."
            return
        strike_off_date = self.edit_form_llp_strike_off_date.strip()
        if strike_off_date and not _parse_doi(strike_off_date):
            self.edit_form_llp_error = "Invalid strike-off date. Use YYYY-MM-DD."
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
            "non_client": self.edit_form_llp_is_non_client,
        }
        self._clear_edit_llp_form()
        self.is_saving = True
        return PortalState.commit_edit_llp(
            lid, llpin, name, pan, extra["roc_name"], doi, email, extra["address"],
            extra["number_of_partners"], extra["number_of_designated_partners"],
            extra["total_obligation"], strike_off_date,
            extra["status_under_cirp"], extra["small_llp"],
            extra["non_client"]
        )

    def commit_edit_llp(
        self, llp_id: str, llpin: str, name: str, pan: str = "", roc_name: str = "", doi: str = "", email: str = "",
        address: str = "", number_of_partners: str = "", number_of_designated_partners: str = "",
        total_obligation: str = "", strike_off_date: str = "",
        status_under_cirp: str = "", small_llp: str = "", non_client: int = False
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
                llp.pan = pan or None
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
                llp.non_client = int(bool(non_client)) 
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
        self.llp_partner_appointment_date = value

    def handle_llp_partner_cessation_date_change(self, value: str):
        self.llp_partner_cessation_date = value

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
                self.llp_partner_error = f"{label}: invalid date. Use YYYY-MM-DD."
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


def company_details_tab() -> rx.Component:
    return rx.vstack(
        _form_checkbox(
            "Non Client",
            PortalState.is_edit_form_non_client,
            PortalState.handle_edit_form_is_non_client_change,
        ),

        # ── Identification ────────────────────────────────────────
        rx.text(
            "Identification",
            size="2",
            weight="bold",
            color="#667eea",
        ),

        rx.grid(
            _form_input(
                "CIN",
                "e.g. U74999MH2021PTC123456",
                PortalState.edit_form_cin,
                PortalState.handle_edit_form_cin_change,
            ),
            _form_input(
                "Registration Number",
                "e.g. 123456",
                PortalState.edit_form_registration_number,
                PortalState.handle_edit_form_registration_number_change,
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),

        _form_input(
            "Company Name",
            "Enter full company name",
            PortalState.edit_form_name,
            PortalState.handle_edit_form_name_change,
        ),

        rx.cond(
            ~PortalState.is_edit_form_non_client,
            _form_input(
                "PAN",
                "e.g. AAAAA0000A",
                PortalState.edit_form_pan,
                PortalState.handle_edit_form_pan_change,
            ),
        ),

        # ── Jurisdiction & Classification ─────────────────────────
        rx.cond(
            ~PortalState.is_edit_form_non_client,
            rx.vstack(
                rx.text(
                    "Jurisdiction",
                    size="2",
                    weight="bold",
                    color="#667eea",
                ),

                rx.grid(
                    _form_input(
                        "ROC Name",
                        "e.g. Registrar of Companies, Mumbai",
                        PortalState.edit_form_roc_code,
                        PortalState.handle_edit_form_roc_code_change,
                    ),
                    _form_input(
                        "ROC Office",
                        "e.g. Mumbai",
                        PortalState.edit_form_roc_office,
                        PortalState.handle_edit_form_roc_office_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),

                rx.grid(
                    _form_input(
                        "RD Name",
                        "e.g. Regional Director, Western Region",
                        PortalState.edit_form_rd_name,
                        PortalState.handle_edit_form_rd_name_change,
                    ),
                    _form_input(
                        "RD Region",
                        "e.g. Western Region",
                        PortalState.edit_form_rd_region,
                        PortalState.handle_edit_form_rd_region_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),

                # ── Classification ───────────────────────────────
                rx.text(
                    "Classification",
                    size="2",
                    weight="bold",
                    color="#667eea",
                ),

                rx.grid(
                    _form_select(
                        "Class",
                        ["PUBLIC", "PRIVATE"],
                        PortalState.edit_form_class,
                        PortalState.handle_edit_form_class_change,
                    ),
                    _form_select(
                        "Category",
                        [
                            "Company limited by Shares",
                            "Company limited by Guarantee",
                            "Unlimited Company",
                        ],
                        PortalState.edit_form_category,
                        PortalState.handle_edit_form_category_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),

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

                rx.grid(
                    _form_select(
                        "Listed Status",
                        ["Listed", "Unlisted"],
                        PortalState.edit_form_listed_status,
                        PortalState.handle_edit_form_listed_status_change,
                    ),
                    _form_select(
                        "Suspended at Stock Exchange",
                        ["Yes", "No"],
                        PortalState.edit_form_suspended_at_stock_exchange,
                        PortalState.handle_edit_form_suspended_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),

                # ── Financials ───────────────────────────────────
                rx.text(
                    "Financials",
                    size="2",
                    weight="bold",
                    color="#667eea",
                ),

                rx.grid(
                    rx.vstack(
                        rx.text(
                            "Authorised Capital (₹)",
                            size="2",
                            weight="bold",
                            color="#333",
                        ),
                        rx.el.input(
                            placeholder="e.g. 1000000",
                            value=PortalState.edit_form_authorised_capital,
                            on_change=PortalState.handle_edit_form_authorised_capital_change,
                            type="number",
                            min="0",
                            step="1",
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

                    rx.vstack(
                        rx.text(
                            "Paid Up Capital (₹)",
                            size="2",
                            weight="bold",
                            color="#333",
                        ),
                        rx.el.input(
                            placeholder="e.g. 500000",
                            value=PortalState.edit_form_paid_up_capital,
                            on_change=PortalState.handle_edit_form_paid_up_capital_change,
                            type="number",
                            min="0",
                            step="1",
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

                    columns="2",
                    spacing="3",
                    width="100%",
                ),

                _form_input(
                    "Number of Members",
                    "e.g. 7",
                    PortalState.edit_form_number_of_members,
                    PortalState.handle_edit_form_number_of_members_change,
                ),

                # ── Important Dates ───────────────────────────────
                rx.text(
                    "Important Dates",
                    size="2",
                    weight="bold",
                    color="#667eea",
                ),

                rx.grid(
                    _form_date_input(
                        "Date of Incorporation",
                        PortalState.edit_form_doi,
                        PortalState.handle_edit_form_doi_change,
                    ),
                    _form_date_input(
                        "Date of Last AGM",
                        PortalState.edit_form_date_of_last_agm,
                        PortalState.handle_edit_form_date_of_last_agm_change,
                    ),
                    _form_date_input(
                        "Date of Balance Sheet",
                        PortalState.edit_form_date_of_balance_sheet,
                        PortalState.handle_edit_form_date_of_balance_sheet_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),

                # ── Contact & Address ─────────────────────────────
                rx.text(
                    "Contact & Address",
                    size="2",
                    weight="bold",
                    color="#667eea",
                ),

                rx.grid(
                    _form_input(
                        "Email Address",
                        "e.g. company@example.com",
                        PortalState.edit_form_email,
                        PortalState.handle_edit_form_email_change,
                        "email",
                    ),
                    _form_input(
                        "Phone",
                        "e.g. 022-12345678",
                        PortalState.edit_form_phone,
                        PortalState.handle_edit_form_phone_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),

                _form_textarea(
                    "Registered Address",
                    "Building/Street, Area",
                    PortalState.edit_form_address,
                    PortalState.handle_edit_form_address_change,
                ),

                rx.grid(
                    _form_input(
                        "Pin Code",
                        "e.g. 400001",
                        PortalState.edit_form_pin_code,
                        PortalState.handle_edit_form_pin_code_change,
                    ),
                    _form_input(
                        "Country",
                        "e.g. India",
                        PortalState.edit_form_country,
                        PortalState.handle_edit_form_country_change,
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
            ),
        ),

        spacing="4",
        width="100%",
    )

def auditor_tab() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Auditor Details",
            size="4",
        ),

        # --------------------------------
        # E-Form Details
        # --------------------------------

        rx.heading(
            "E-Form Details",
            size="3",
        ),

        rx.vstack(
            rx.text("SRN of E-Form ADT-1"),

            rx.input(
                value=PortalState.edit_auditor_srn,
                on_change=PortalState.handle_edit_auditor_srn_change,
                placeholder="Enter SRN",
                width="100%",
            ),

            width="100%",
        ),

        # --------------------------------
        # Auditor Category
        # --------------------------------

        rx.heading(
            "Category of Auditor",
            size="3",
        ),

        rx.radio_group(
            ["Individual", "Firm"],
            value=PortalState.edit_auditor_category,
            on_change=PortalState.handle_edit_auditor_category_change,
        ),

        # --------------------------------
        # Firm Details
        # --------------------------------

        rx.cond(
            PortalState.edit_auditor_category == "Firm",

            rx.vstack(
                rx.heading(
                    "Firm Details",
                    size="3",
                ),

                rx.hstack(
                    rx.vstack(
                        rx.text("Name of the Firm"),

                        rx.input(
                            value=PortalState.edit_auditor_firm_name,
                            on_change=PortalState.handle_edit_auditor_firm_name_change,
                            width="100%",
                        ),

                        width="50%",
                    ),

                    rx.vstack(
                        rx.text("Firm Membership No"),

                        rx.input(
                            value=PortalState.edit_auditor_firm_membership_no,
                            on_change=PortalState.handle_edit_auditor_firm_membership_no_change,
                            width="100%",
                        ),

                        width="50%",
                    ),

                    width="100%",
                    spacing="4",
                ),

                rx.hstack(
                    rx.vstack(
                        rx.text("Firm PAN Number"),

                        rx.input(
                            value=PortalState.edit_auditor_firm_pan,
                            on_change=PortalState.handle_edit_auditor_firm_pan_change,
                            width="100%",
                        ),

                        width="50%",
                    ),

                    rx.vstack(
                        rx.text("Firm's Email ID"),

                        rx.input(
                            value=PortalState.edit_auditor_firm_email,
                            on_change=PortalState.handle_edit_auditor_firm_email_change,
                            width="100%",
                        ),

                        width="50%",
                    ),

                    width="100%",
                    spacing="4",
                ),

                rx.text("Address"),

                rx.text_area(
                    value=PortalState.edit_auditor_address,
                    on_change=PortalState.handle_edit_auditor_address_change,
                    width="100%",
                ),

                rx.hstack(
                    rx.vstack(
                        rx.text("Country"),

                        rx.input(
                            value=PortalState.edit_auditor_country,
                            on_change=PortalState.handle_edit_auditor_country,
                            width="100%",
                        ),

                        width="25%",
                    ),

                    rx.vstack(
                        rx.text("State"),

                        rx.input(
                            value=PortalState.edit_auditor_state,
                            on_change=PortalState.handle_edit_auditor_state,
                            width="100%",
                        ),

                        width="25%",
                    ),

                    rx.vstack(
                        rx.text("City"),

                        rx.input(
                            value=PortalState.edit_auditor_city,
                            on_change=PortalState.handle_edit_auditor_city,
                            width="100%",
                        ),

                        width="25%",
                    ),

                    rx.vstack(
                        rx.text("PIN Code"),

                        rx.input(
                            value=PortalState.edit_auditor_pin_code,
                            on_change=PortalState.handle_edit_auditor_pin_code,
                            width="100%",
                        ),

                        width="25%",
                    ),

                    width="100%",
                    spacing="4",
                ),

                width="100%",
                spacing="4",
            ),

            rx.fragment(),
        ),

        # --------------------------------
        # Auditor / Partner Details
        # --------------------------------

        rx.heading(
            "Auditor Details",
            size="3",
        ),

        rx.hstack(
            rx.vstack(
                rx.text("Partner/Proprietor Membership No"),

                rx.input(
                    value=PortalState.edit_auditor_partner_membership_no,
                    on_change=PortalState.handle_edit_auditor_partner_membership_no,
                    width="100%",
                ),

                width="50%",
            ),

            rx.vstack(
                rx.text("Name of the Auditor"),

                rx.input(
                    value=PortalState.edit_auditor_name,
                    on_change=PortalState.handle_edit_auditor_name,
                    width="100%",
                ),

                width="50%",
            ),

            width="100%",
            spacing="4",
        ),

        rx.hstack(
            rx.vstack(
                rx.text("PAN Number of Auditor"),

                rx.input(
                    value=PortalState.edit_auditor_pan,
                    on_change=PortalState.handle_edit_auditor_pan,
                    width="100%",
                ),

                width="50%",
            ),

            rx.vstack(
                rx.text("Mobile Number"),

                rx.input(
                    value=PortalState.edit_auditor_mobile,
                    on_change=PortalState.handle_edit_auditor_mobile,
                    width="100%",
                ),

                width="50%",
            ),

            width="100%",
            spacing="4",
        ),

        rx.hstack(
            rx.vstack(
                rx.text("Email ID"),

                rx.input(
                    value=PortalState.edit_auditor_email,
                    on_change=PortalState.handle_edit_auditor_email,
                    width="100%",
                ),

                width="50%",
            ),

            rx.vstack(
                rx.text("Designation"),

                rx.input(
                    value=PortalState.edit_auditor_designation,
                    on_change=PortalState.handle_edit_auditor_designation,
                    width="100%",
                ),

                width="50%",
            ),

            width="100%",
            spacing="4",
        ),

        width="100%",
        spacing="4",
    )

def shareholder_master_tab() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Shareholder Master",
            size="4",
        ),

        rx.button(
            rx.hstack(
                rx.icon("plus", size=16),
                rx.text("Add Shareholder"),
                spacing="2",
            ),
            on_click=PortalState.open_add_shareholder,
            background="#0d8bf2",
            color="white",
            size="3",
        ),

        rx.divider(),

        rx.cond(
            PortalState.shareholders.length() > 0,

            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Name of Member"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("PAN"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Occupation"),
                            rx.table.column_header_cell("Actions"),
                        )
                    ),

                    rx.table.body(
                        rx.foreach(
                            PortalState.shareholders,
                            lambda shareholder: rx.table.row(
                                rx.table.cell(shareholder["name_of_member"]),
                                rx.table.cell(shareholder["email"]),
                                rx.table.cell(shareholder["pan"]),
                                rx.table.cell(shareholder["status"]),
                                rx.table.cell(shareholder["occupation"]),

                                rx.table.cell(
                                    rx.button(
                                        rx.icon("pencil", size=14),
                                        on_click=lambda: PortalState.edit_shareholder(shareholder["id"]),
                                        color_scheme="blue",
                                        variant="ghost",
                                        size="1",
                                    )
                                ),
                            ),
                        )
                    ),
                ),
                width="100%",
                overflow_x="auto",
                border="1px solid #e5e7eb",
                border_radius="8px",
            ),

            rx.text(
                "No shareholders found.",
                color="#888",
            ),
        ),
        # Add Shareholder dialog
        shareholder_form_dialog(),

        width="100%",
        spacing="4",
    )

def shareholder_form_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_add_shareholder,

        rx.box(
            rx.box(
                rx.vstack(

                    # --------------------------------------------------
                    # Header
                    # --------------------------------------------------

                    rx.hstack(
                        rx.icon(
                            "user-round-plus",
                            size=22,
                            color="#667eea",
                        ),

                        rx.heading(
                            rx.cond(
                                PortalState.edit_shareholder_id != "",
                                "Edit Shareholder",
                                "Add Shareholder",
                            ),
                            size="5",
                            color="#1a1a1a",
                            weight="bold",
                        ),

                        rx.spacer(),

                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_add_shareholder,
                            variant="ghost",
                            size="1",
                        ),

                        width="100%",
                        align_items="center",
                    ),

                    rx.divider(),

                    # --------------------------------------------------
                    # Member Details
                    # --------------------------------------------------

                    rx.text(
                        "Member Details",
                        size="3",
                        weight="bold",
                        color="#667eea",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("Name of the Member"),
                            rx.input(
                                value=PortalState.shareholder_name_of_member,
                                on_change=PortalState.handle_shareholder_name_of_member_change,
                                placeholder="Enter member name",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Registration Number / CIN"),
                            rx.input(
                                value=PortalState.shareholder_registration_number_cin,
                                on_change=PortalState.handle_shareholder_registration_number_cin_change,
                                placeholder="Enter registration number / CIN",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.vstack(
                        rx.text("Address of the Member"),
                        rx.text_area(
                            value=PortalState.shareholder_address,
                            on_change=PortalState.handle_shareholder_address_change,
                            placeholder="Enter member address",
                            width="100%",
                        ),
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("Email ID"),
                            rx.input(
                                value=PortalState.shareholder_email,
                                on_change=PortalState.handle_shareholder_email_change,
                                placeholder="Enter email ID",
                                type="email",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Father's / Mother's / Spouse's Name"),
                            rx.input(
                                value=PortalState.shareholder_father_mother_spouse_name,
                                on_change=PortalState.handle_shareholder_father_mother_spouse_name_change,
                                placeholder="Enter name",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("Status"),
                            rx.select(
                                [
                                    "Active",
                                    "Inactive",
                                    "Nominee",
                                    "Other",
                                ],
                                value=PortalState.shareholder_status,
                                on_change=PortalState.handle_shareholder_status_change,
                                placeholder="Select status",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Occupation"),
                            rx.input(
                                value=PortalState.shareholder_occupation,
                                on_change=PortalState.handle_shareholder_occupation_change,
                                placeholder="Enter occupation",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("PAN No"),
                            rx.input(
                                value=PortalState.shareholder_pan,
                                on_change=PortalState.handle_shareholder_pan_change,
                                placeholder="Enter PAN number",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Nationality"),
                            rx.input(
                                value=PortalState.shareholder_nationality,
                                on_change=PortalState.handle_shareholder_nationality_change,
                                placeholder="Enter nationality",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    # --------------------------------------------------
                    # Membership Details
                    # --------------------------------------------------

                    rx.text(
                        "Membership Details",
                        size="3",
                        weight="bold",
                        color="#667eea",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("Date of Becoming Member"),
                            rx.input(
                                type="date",
                                value=PortalState.shareholder_date_of_becoming_member,
                                on_change=PortalState.handle_shareholder_date_of_becoming_member_change,
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text(
                                "Date of Declaration U/S 89, if applicable"
                            ),
                            rx.input(
                                type="date",
                                value=PortalState.shareholder_date_of_declaration_u_s_89,
                                on_change=PortalState.handle_shareholder_date_of_declaration_u_s_89_change,
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.vstack(
                        rx.text(
                            "Name and Address of Beneficial Owner"
                        ),
                        rx.text_area(
                            value=PortalState.shareholder_beneficial_owner_name_address,
                            on_change=PortalState.handle_shareholder_beneficial_owner_name_address_change,
                            placeholder="Enter beneficial owner name and address",
                            width="100%",
                        ),
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text(
                                "Date of Receipt of Nomination, if applicable"
                            ),
                            rx.input(
                                type="date",
                                value=PortalState.shareholder_date_of_receipt_of_nomination,
                                on_change=PortalState.handle_shareholder_date_of_receipt_of_nomination_change,
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Date of Cessation of Membership"),
                            rx.input(
                                type="date",
                                value=PortalState.shareholder_date_of_cessation_of_membership,
                                on_change=PortalState.handle_shareholder_date_of_cessation_of_membership_change,
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.vstack(
                        rx.text("Name and Address of Nominee"),
                        rx.text_area(
                            value=PortalState.shareholder_nominee_name_address,
                            on_change=PortalState.handle_shareholder_nominee_name_address_change,
                            placeholder="Enter nominee name and address",
                            width="100%",
                        ),
                        width="100%",
                    ),

                    # --------------------------------------------------
                    # Share / Transfer Details
                    # --------------------------------------------------

                    rx.text(
                        "Share / Transfer Details",
                        size="3",
                        weight="bold",
                        color="#667eea",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("Allotment No / Transfer No"),
                            rx.input(
                                value=PortalState.shareholder_allotment_transfer_no,
                                on_change=PortalState.handle_shareholder_allotment_transfer_no_change,
                                placeholder="Enter allotment / transfer number",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Date of Allotment / Transfer"),
                            rx.input(
                                type="date",
                                value=PortalState.shareholder_date_of_allotment_transfer,
                                on_change=PortalState.handle_shareholder_date_of_allotment_transfer_change,
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("No. of Shares Allotted / Transferred"),
                            rx.input(
                                value=PortalState.shareholder_number_of_shares,
                                on_change=PortalState.handle_shareholder_number_of_shares_change,
                                placeholder="Enter number of shares",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Distinctive Numbers"),
                            rx.input(
                                value=PortalState.shareholder_distinctive_numbers,
                                on_change=PortalState.handle_shareholder_distinctive_numbers_change,
                                placeholder="Enter distinctive numbers",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text("Folio of Transferor, if applicable"),
                            rx.input(
                                value=PortalState.shareholder_folio_of_transferor,
                                on_change=PortalState.handle_shareholder_folio_of_transferor_change,
                                placeholder="Enter folio number",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Name of the Transferor, if applicable"),
                            rx.input(
                                value=PortalState.shareholder_name_of_transferor,
                                on_change=PortalState.handle_shareholder_name_of_transferor_change,
                                placeholder="Enter transferor name",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    rx.grid(

                        rx.vstack(
                            rx.text(
                                "Date of Issue / Endorsement of Share Certificate"
                            ),
                            rx.input(
                                value=PortalState.shareholder_date_of_issue_endorsement,
                                on_change=PortalState.handle_shareholder_date_of_issue_endorsement_change,
                                type="date",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        rx.vstack(
                            rx.text("Certificate No."),
                            rx.input(
                                value=PortalState.shareholder_certificate_no,
                                on_change=PortalState.handle_shareholder_certificate_no_change,
                                placeholder="Enter certificate number",
                                width="100%",
                            ),
                            width="100%",
                        ),

                        columns="2",
                        spacing="4",
                        width="100%",
                    ),

                    # --------------------------------------------------
                    # Footer
                    # --------------------------------------------------

                    rx.divider(),

                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=PortalState.close_add_shareholder,
                            variant="outline",
                        ),

                        rx.spacer(),

                        rx.button(
                            rx.hstack(
                                rx.icon("save", size=16),
                                rx.text("Save Shareholder"),
                                spacing="2",
                            ),
                            on_click=PortalState.save_shareholder,
                            background="#667eea",
                            color="white",
                        ),

                        width="100%",
                    ),

                    width="100%",
                    spacing="4",
                ),

                width="850px",
                max_width="95vw",
                max_height="90vh",
                overflow_y="auto",
                padding="1.5rem",
                background="white",
                border_radius="12px",
                box_shadow="0 10px 40px rgba(0,0,0,0.2)",
            ),

            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background="rgba(0,0,0,0.45)",
            z_index="2000",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )

def edit_company_tabs() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            # Company Details
            rx.button(
                "Company Details",
                on_click=PortalState.show_company_tab,
                background=rx.cond(
                    PortalState.edit_company_tab == "company",
                    "#3b82f6",
                    "white",
                ),
                color=rx.cond(
                    PortalState.edit_company_tab == "company",
                    "white",
                    "#374151",
                ),
                border=rx.cond(
                    PortalState.edit_company_tab == "company",
                    "1px solid #3b82f6",
                    "1px solid #d1d5db",
                ),
                border_radius="6px 6px 0 0",
                padding="0.6rem 1.2rem",
                cursor="pointer",
            ),

            # Auditor Details
            rx.button(
                "Auditor Details",
                on_click=PortalState.show_auditor_tab,
                background=rx.cond(
                    PortalState.edit_company_tab == "auditor",
                    "#3b82f6",
                    "white",
                ),
                color=rx.cond(
                    PortalState.edit_company_tab == "auditor",
                    "white",
                    "#374151",
                ),
                border=rx.cond(
                    PortalState.edit_company_tab == "auditor",
                    "1px solid #3b82f6",
                    "1px solid #d1d5db",
                ),
                border_radius="6px 6px 0 0",
                padding="0.6rem 1.2rem",
                cursor="pointer",
            ),

            # Shareholder Master
            rx.button(
                "Shareholder Master",
                on_click=PortalState.show_shareholder_tab,
                background=rx.cond(
                    PortalState.edit_company_tab == "shareholder",
                    "#3b82f6",
                    "white",
                ),
                color=rx.cond(
                    PortalState.edit_company_tab == "shareholder",
                    "white",
                    "#374151",
                ),
                border=rx.cond(
                    PortalState.edit_company_tab == "shareholder",
                    "1px solid #3b82f6",
                    "1px solid #d1d5db",
                ),
                border_radius="6px 6px 0 0",
                padding="0.6rem 1.2rem",
                cursor="pointer",
            ),

            rx.button(
                "Share Capital",
                on_click=PortalState.show_share_capital_tab,
                background=rx.cond(
                    PortalState.edit_company_tab == "share_capital",
                    "#3b82f6",
                    "white",
                ),
                color=rx.cond(
                    PortalState.edit_company_tab == "share_capital",
                    "white",
                    "#374151",
                ),
                border=rx.cond(
                    PortalState.edit_company_tab == "share_capital",
                    "1px solid #3b82f6",
                    "1px solid #d1d5db",
                ),
                border_radius="6px 6px 0 0",
                padding="0.6rem 1.2rem",
                cursor="pointer",
            ),

            spacing="1",
            align_items="end",
        ),

        rx.divider(),

        # Tab content
        rx.cond(
            PortalState.edit_company_tab == "company",

            company_details_tab(),

            rx.cond(
                PortalState.edit_company_tab == "auditor",

                auditor_tab(),

                rx.cond(
                    PortalState.edit_company_tab == "share_capital",

                    share_capital_tab(),

                    shareholder_master_tab(),
                ),
            ),
        ),

        width="100%",
        spacing="4",
    )

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

def _form_checkbox(label: str, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(
            label,
            size="2",
            weight="bold",
            color="#333",
        ),
        rx.checkbox(
            checked=value,
            on_change=on_change,
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
            type="date",
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
        rx.text("Format: YYYY-MM-DD", size="1", color="#999"),
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
                    _form_checkbox("Non Client", PortalState.is_non_client, PortalState.handle_form_is_non_client_change),

                    # ── Identification ────────────────────────────────────────
                    rx.text("Identification", size="2", weight="bold", color="#667eea"),
                    rx.grid(
                        _form_input("CIN", "e.g. U74999MH2021PTC123456", PortalState.form_cin, PortalState.handle_form_cin_change),
                        _form_input("Registration Number", "e.g. 123456", PortalState.form_registration_number, PortalState.handle_form_registration_number_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    _form_input("Company Name", "Enter full company name", PortalState.form_name, PortalState.handle_form_name_change),

                    rx.cond(~PortalState.is_non_client, rx.vstack(
                    rx.grid(
                        _form_input("PAN", "e.g. AAAAA0000A", PortalState.form_pan, PortalState.handle_form_pan_change),
                            columns="2", spacing="3", width="100%",
                    ),   
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
                    ))),
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

                    # Header
                    rx.hstack(
                        rx.icon("pencil", size=22, color="#667eea"),
                        rx.heading(
                            "Edit Company",
                            size="5",
                            color="#1a1a1a",
                            weight="bold",
                        ),
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

                    # Company Details / Auditor Details tabs
                    edit_company_tabs(),

                    # Error message
                    rx.cond(
                        PortalState.edit_form_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon(
                                    "circle-alert",
                                    size=16,
                                    color="#dc2626",
                                ),
                                rx.text(
                                    PortalState.edit_form_error,
                                    size="2",
                                    color="#dc2626",
                                ),
                                spacing="2",
                            ),
                            padding="0.75rem",
                            border_radius="0.5rem",
                            background="#fee2e2",
                            border_left="4px solid #dc2626",
                            width="100%",
                        ),
                    ),

                    # Footer buttons
                    rx.cond(
                        (PortalState.edit_company_tab == "company")
                        | (PortalState.edit_company_tab == "auditor"),
                        rx.hstack(
                            rx.button(
                                "Cancel",
                                on_click=PortalState.close_edit_company_form,
                                variant="outline",
                                color_scheme="gray",
                                size="3",
                            ),
                            rx.button(
                                rx.hstack(
                                    rx.icon("save", size=16),
                                    rx.text("Save Changes"),
                                    spacing="2",
                                ),
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
                        rx.fragment(),
                    ),
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
def share_capital_tab() -> rx.Component:
    return rx.vstack(
        # ── Header ─────────────────────────────────────
        rx.hstack(
            rx.icon(
                "landmark",
                size=24,
                color="#667eea",
            ),
            rx.heading(
                "Share Capital",
                size="5",
                weight="bold",
            ),
            spacing="2",
            align_items="center",
        ),

        rx.divider(),

        # ── Share Capital Type ─────────────────────────
        rx.vstack(
            rx.text(
                "Share Capital Type",
                size="2",
                weight="bold",
                color="#555",
            ),

            rx.select(
                [
                    "Equity Share Capital",
                    "Preference Share Capital",
                ],
                value=rx.cond(
                    PortalState.share_capital_type == "EQUITY",
                    "Equity Share Capital",
                    "Preference Share Capital",
                ),
                on_change=PortalState.set_share_capital_type,
                width="100%",
            ),

            spacing="1",
            width="100%",
        ),

        # ── Overall Capital ───────────────────────────
        rx.vstack(
            rx.text(
                rx.cond(
                    PortalState.share_capital_type == "EQUITY",
                    "Equity Share Capital",
                    "Preference Share Capital",
                ),
                size="4",
                weight="bold",
                color="#333",
            ),

            rx.text(
                "Overall Share Capital",
                size="3",
                weight="bold",
                color="#667eea",
            ),

            rx.grid(
                rx.text(
                    "",
                    weight="bold",
                ),

                rx.text(
                    "Authorized Capital",
                    weight="bold",
                    align="center",
                ),

                rx.text(
                    "Paid Up Capital",
                    weight="bold",
                    align="center",
                ),

                rx.text(
                    rx.cond(
                        PortalState.share_capital_type == "EQUITY",
                        "No. of Equity Shares",
                        "No. of Preference Shares",
                    ),
                    size="2",
                ),

                rx.input(
                    value=PortalState.share_capital_authorized_shares,
                    on_change=PortalState.set_share_capital_authorized_shares,
                    type="number",
                    placeholder="Enter number",
                ),

                rx.input(
                    value=PortalState.share_capital_paid_up_shares,
                    on_change=PortalState.set_share_capital_paid_up_shares,
                    type="number",
                    placeholder="Enter number",
                ),

                rx.text(
                    "Total Amount",
                    size="2",
                ),

                rx.input(
                    value=PortalState.share_capital_authorized_amount,
                    on_change=PortalState.set_share_capital_authorized_amount,
                    type="number",
                    placeholder="Enter amount",
                ),

                rx.input(
                    value=PortalState.share_capital_paid_up_amount,
                    on_change=PortalState.set_share_capital_paid_up_amount,
                    type="number",
                    placeholder="Enter amount",
                ),

                columns="3",
                spacing="3",
                width="100%",
            ),

            spacing="3",
            width="100%",
        ),

        rx.divider(),

        # ── Class A ────────────────────────────────────
        rx.hstack(
            rx.button(
                "Class A",
                on_click=PortalState.toggle_class_a,
                color_scheme="violet",
                variant="outline",
                size="1",
            )
        ),

        rx.cond(
            PortalState.show_class_a,
            share_capital_class_section("Class A", "A"),
            rx.fragment(),
        ),

        rx.divider(),

        # ── Class B ────────────────────────────────────
        rx.hstack(
            rx.button(
                "Class B",
                on_click=PortalState.toggle_class_b,
                color_scheme="violet",
                variant="outline",
                size="1",
            )
        ),

        rx.cond(
            PortalState.show_class_b,
            share_capital_class_section("Class B", "B"),
            rx.fragment(),
        ),

        # ── Buttons ────────────────────────────────────
        rx.hstack(
            rx.button(
                "Cancel",
                on_click=PortalState.close_share_capital,
                variant="outline",
                color_scheme="gray",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("save", size=16),
                    rx.text("Save Share Capital"),
                    spacing="2",
                ),
                on_click=PortalState.save_share_capital,
                color_scheme="violet",
            ),
            spacing="3",
            justify="end",
            width="100%",
        ),

        spacing="4",
        width="100%",
    )
    
def share_capital_class_section(
    title: str,
    class_name: str,
) -> rx.Component:

    if class_name == "A":
        authorized_shares = PortalState.share_capital_a_authorized_shares
        paid_up_shares = PortalState.share_capital_a_paid_up_shares
        authorized_nominal = PortalState.share_capital_a_authorized_nominal
        paid_up_nominal = PortalState.share_capital_a_paid_up_nominal
        authorized_amount = PortalState.share_capital_a_authorized_amount
        paid_up_amount = PortalState.share_capital_a_paid_up_amount

        on_authorized_shares = PortalState.set_share_capital_a_authorized_shares
        on_paid_up_shares = PortalState.set_share_capital_a_paid_up_shares
        on_authorized_nominal = PortalState.set_share_capital_a_authorized_nominal
        on_paid_up_nominal = PortalState.set_share_capital_a_paid_up_nominal
        on_authorized_amount = PortalState.set_share_capital_a_authorized_amount
        on_paid_up_amount = PortalState.set_share_capital_a_paid_up_amount

    else:
        authorized_shares = PortalState.share_capital_b_authorized_shares
        paid_up_shares = PortalState.share_capital_b_paid_up_shares
        authorized_nominal = PortalState.share_capital_b_authorized_nominal
        paid_up_nominal = PortalState.share_capital_b_paid_up_nominal
        authorized_amount = PortalState.share_capital_b_authorized_amount
        paid_up_amount = PortalState.share_capital_b_paid_up_amount

        on_authorized_shares = PortalState.set_share_capital_b_authorized_shares
        on_paid_up_shares = PortalState.set_share_capital_b_paid_up_shares
        on_authorized_nominal = PortalState.set_share_capital_b_authorized_nominal
        on_paid_up_nominal = PortalState.set_share_capital_b_paid_up_nominal
        on_authorized_amount = PortalState.set_share_capital_b_authorized_amount
        on_paid_up_amount = PortalState.set_share_capital_b_paid_up_amount

    return rx.vstack(
        rx.text(
            title,
            size="3",
            weight="bold",
            color="#667eea",
        ),

        rx.grid(
            rx.text(""),
            rx.text(
                "Authorized Capital",
                weight="bold",
                align="center",
            ),
            rx.text(
                "Paid Up Capital",
                weight="bold",
                align="center",
            ),

            # No. of Shares
            rx.text(
                rx.cond(
                    PortalState.share_capital_type == "EQUITY",
                    "No. of Equity Shares",
                    "No. of Preference Shares",
                ),
                size="2",
            ),

            rx.input(
                value=authorized_shares,
                on_change=on_authorized_shares,
                type="number",
                placeholder="Enter number",
            ),

            rx.input(
                value=paid_up_shares,
                on_change=on_paid_up_shares,
                type="number",
                placeholder="Enter number",
            ),

            # Nominal Value
            rx.text(
                "Nominal Value per share",
                size="2",
            ),

            rx.input(
                value=authorized_nominal,
                on_change=on_authorized_nominal,
                type="number",
                placeholder="Enter value",
            ),

            rx.input(
                value=paid_up_nominal,
                on_change=on_paid_up_nominal,
                type="number",
                placeholder="Enter value",
            ),

            # Total Amount
            rx.text(
                "Total Amount",
                size="2",
            ),

            rx.input(
                value=authorized_amount,
                on_change=on_authorized_amount,
                type="number",
                placeholder="Enter amount",
            ),

            rx.input(
                value=paid_up_amount,
                on_change=on_paid_up_amount,
                type="number",
                placeholder="Enter amount",
            ),

            columns="3",
            spacing="3",
            width="100%",
        ),

        spacing="3",
        width="100%",
    )

def companies_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("CIN", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("Company Name", font_weight="700", color="white", font_size="0.95rem"),
                rx.table.column_header_cell("PAN", font_weight="700", color="white", font_size="0.95rem"),
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
                    rx.table.cell(
                        rx.text(
                            rx.cond(
                                PortalState.visible_company_id == item["id"],
                                item["pan"],
                                "**********",
                            ),
                            color="#555",
                            size="2",
                        )
                    ),
                    rx.table.cell(rx.badge(item["class"], variant="outline", color_scheme="violet")),
                    rx.table.cell(rx.badge(item["category"], variant="outline", color_scheme="cyan")),
                    rx.table.cell(rx.text(item["sub_category"], color="#555", size="2")),
                    rx.table.cell(rx.text(item["doi"], color="#555", size="2")),
                    rx.table.cell(
                        rx.cond(
                            item["email"] != "",
                            rx.cond(
                                PortalState.visible_company_id == item["id"],
                                rx.link(
                                    item["email"],
                                    href=f"mailto:{item['email']}",
                                    size="2",
                                    color="#667eea",
                                ),
                                rx.text(
                                    "**********",
                                    size="2",
                                    color="#555",
                                ),
                            ),
                            rx.text("-", color="#aaa", size="2"),
                        )
                    ),
                    rx.table.cell(
                        rx.hstack(
                            # View
                            rx.button(
                                rx.icon("eye", size=14),
                                on_click=PortalState.toggle_company_sensitive_data(item["id"]),
                                color_scheme="green",
                                variant="ghost",
                                size="1",
                            ),
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
                                    on_click=PortalState.open_edit_company_with_tabs(item["id"]),
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
                                                        rx.hstack(
                                                            rx.text("PAN:", size="2", weight="bold", color="#555"),
                                                            rx.text(
                                                            rx.cond(
                                                                PortalState.visible_company_id == item["id"],
                                                                item["pan"],
                                                                "**********",
                                                            ),
                                                            size="2", color="#1a1a1a"
                                                        ),
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
                        rx.hstack(
                        rx.button(
                            rx.hstack(rx.icon("eye", size=14)),
                            on_click=PortalState.open_director_associations(item["id"]),
                            color_scheme="blue",
                            variant="ghost",
                            size="1",
                        ),
                        rx.cond(
                            (PortalState.role == "ADMIN") | (PortalState.role == "EDITOR"),
                            rx.button(
                                rx.icon("pencil", size=14),
                                on_click=PortalState.open_edit_director_form(item["id"]),
                                color_scheme="blue",
                                variant="ghost",
                                size="1",
                                spacing="1",
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
                                        spacing="1",
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
                        spacing="2",
                        align="center",
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


def director_associations_dialog() -> rx.Component:
    return rx.cond(
        PortalState.show_director_associations,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("network", size=22, color="#667eea"),
                        rx.vstack(
                            rx.heading("Director Associations", size="5", color="#1a1a1a", weight="bold"),
                            rx.text(
                                f"{PortalState.viewing_director_name} (DIN: {PortalState.viewing_director_din})",
                                size="2",
                                color="#667eea",
                            ),
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=PortalState.close_director_associations,
                            variant="ghost",
                            size="1",
                            color="#666",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("building-2", size=18, color="#2563eb"),
                            rx.heading(
                                f"Companies ({PortalState.director_company_associations.length()})",
                                size="3",
                                color="#1a1a1a",
                            ),
                            spacing="2",
                            align_items="center",
                            width="100%",
                        ),
                        rx.cond(
                            PortalState.director_company_associations.length() == 0,
                            rx.text("No company association found.", size="2", color="#999"),
                            rx.vstack(
                                rx.foreach(
                                    PortalState.director_company_associations,
                                    lambda item: rx.box(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.heading(item["name"], size="3", color="#1a1a1a"),
                                                rx.spacer(),
                                                rx.badge(item["cin"], color_scheme="blue", variant="soft"),
                                                width="100%",
                                            ),
                                            rx.text(
                                                "Designation: ",
                                                rx.cond(item["designation"] != "", item["designation"], "-"),
                                                " | Category: ",
                                                rx.cond(item["category"] != "", item["category"], "-"),
                                                " | Share %: ",
                                                rx.cond(item["share_percent"] != "", item["share_percent"], "-"),
                                                size="2",
                                                color="#444",
                                            ),
                                            rx.text(
                                                "Original Appointment: ",
                                                rx.cond(item["original_appointment_date"] != "", item["original_appointment_date"], "-"),
                                                " | Current Designation: ",
                                                rx.cond(item["current_designation_date"] != "", item["current_designation_date"], "-"),
                                                " | Cessation: ",
                                                rx.cond(item["cessation_date"] != "", item["cessation_date"], "-"),
                                                size="2",
                                                color="#666",
                                            ),
                                            spacing="1",
                                            width="100%",
                                        ),
                                        width="100%",
                                        padding="0.75rem",
                                        border="1px solid #e5e7eb",
                                        border_radius="0.5rem",
                                        background="#fafafa",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("building", size=18, color="#0f766e"),
                            rx.heading(
                                f"LLPs ({PortalState.director_llp_associations.length()})",
                                size="3",
                                color="#1a1a1a",
                            ),
                            spacing="2",
                            align_items="center",
                            width="100%",
                        ),
                        rx.cond(
                            PortalState.director_llp_associations.length() == 0,
                            rx.text("No LLP association found.", size="2", color="#999"),
                            rx.vstack(
                                rx.foreach(
                                    PortalState.director_llp_associations,
                                    lambda item: rx.box(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.heading(item["name"], size="3", color="#1a1a1a"),
                                                rx.spacer(),
                                                rx.badge(item["llpin"], color_scheme="teal", variant="soft"),
                                                width="100%",
                                            ),
                                            rx.text(
                                                "Designation: ",
                                                rx.cond(item["designation"] != "", item["designation"], "-"),
                                                " | Appointment: ",
                                                rx.cond(item["appointment_date"] != "", item["appointment_date"], "-"),
                                                " | Cessation: ",
                                                rx.cond(item["cessation_date"] != "", item["cessation_date"], "-"),
                                                size="2",
                                                color="#444",
                                            ),
                                            rx.text(
                                                "Signatory: ",
                                                rx.cond(item["is_signatory"] != "", item["is_signatory"], "-"),
                                                size="2",
                                                color="#666",
                                            ),
                                            spacing="1",
                                            width="100%",
                                        ),
                                        width="100%",
                                        padding="0.75rem",
                                        border="1px solid #e5e7eb",
                                        border_radius="0.5rem",
                                        background="#fafafa",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Close",
                            on_click=PortalState.close_director_associations,
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
                padding="1.5rem",
                width="95%",
                max_width="900px",
                max_height="85vh",
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
                    _form_checkbox("Non Client", PortalState.form_llp_is_non_client, PortalState.handle_llp_is_non_client_change),
                    rx.grid(
                        _form_input("LLPIN", "e.g. AAA-1234", PortalState.form_llpin, PortalState.handle_form_llpin_change),
                        _form_input("LLP Name", "Enter full LLP name", PortalState.form_llp_name, PortalState.handle_form_llp_name_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.cond(~PortalState.form_llp_is_non_client,rx.vstack(
                    _form_input("PAN", "e.g. AAAAA0000A", PortalState.form_llp_pan, PortalState.handle_form_llp_pan_change),
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
                    _form_date_input("Strike off / amalgamated / transferred date", PortalState.form_llp_strike_off_date, PortalState.handle_form_llp_strike_off_date_change))),
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
                    _form_checkbox("Non Client", PortalState.edit_form_llp_is_non_client, PortalState.handle_edit_llp_is_non_client_change),
                    rx.grid(
                        _form_input("LLPIN", "e.g. AAA-1234", PortalState.edit_form_llpin, PortalState.handle_edit_form_llpin_change),
                        _form_input("LLP Name", "Enter full LLP name", PortalState.edit_form_llp_name, PortalState.handle_edit_form_llp_name_change),
                        columns="2", spacing="3", width="100%",
                    ),
                    rx.cond(~PortalState.edit_form_llp_is_non_client,rx.vstack(
                    _form_input("PAN", "e.g. AAAAA0000A", PortalState.edit_form_llp_pan, PortalState.handle_edit_form_llp_pan_change),
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
                    _form_date_input("Strike off / amalgamated / transferred date", PortalState.edit_form_llp_strike_off_date, PortalState.handle_edit_form_llp_strike_off_date_change))),
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
                rx.table.column_header_cell("PAN", font_weight="700", color="white", font_size="0.95rem"),
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
                    rx.table.cell(rx.text("**********", color="#555", size="2")),
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
        director_associations_dialog(),
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

