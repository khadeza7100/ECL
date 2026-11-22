import sys
import os
import logging

class SuppressWebSocketDisconnectFilter(logging.Filter):
    def filter(self, record):
        if record.exc_info and len(record.exc_info) > 0:
            exc_type = record.exc_info[0]
            if exc_type and "WebSocketDisconnect" in exc_type.__name__:
                return False
        return True

uvicorn_error_logger = logging.getLogger("uvicorn.error")
uvicorn_error_logger.addFilter(SuppressWebSocketDisconnectFilter())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db
init_db()

import flet as ft

from views.home_view import get_home_view
from views.left_sidebar import get_left_sidebar
from views.right_sidebar import get_right_sidebar
from views.csv_upload_view import get_csv_upload_view

from forms.corporate_form import get_corporate_profile_form
from forms.individual_form import get_individual_profile_form
from forms.collateral_form import get_collateral_profile_form
from forms.credit_ratings_form import get_credit_ratings_form
from forms.funded_ac_form import get_funded_ac_profile_form
from forms.non_funded_ac_form import get_non_funded_ac_profile_form
from forms.economic_variables_form import get_economic_variables_form
from forms.collateral_haircut_form import get_collateral_haircut_form
from forms.discounting_factor_form import get_discounting_factor_form
from forms.loan_staging_criteria_form import get_loan_staging_criteria_form
from forms.ccf_form import get_ccf_form
from forms.proxy_data_model_form import get_proxy_data_model_form
from forms.stage_migration_form import get_stage_migration_form
from forms.pd_calculation_form import get_pd_calculation_form
from forms.adjusted_pd_form import get_adjusted_pd_form
from forms.collateral_distribution_form import get_collateral_distribution_form
from forms.lgd_calculation_form import get_lgd_calculation_form
from forms.ecl_calculation_form import get_ecl_calculation_form
from forms.p_value_form import get_p_value_form
from forms.multicollinearity_form import get_multicollinearity_form
from forms.r_squared_form import get_r_squared_form
from forms.vif_form import get_vif_form
from forms.reporting_date_form import get_reporting_date_form
from forms.dropdown_configuration_form import get_dropdown_configuration_form
from forms.calculated_ead_form import get_calculated_ead_form

def main(page: ft.Page):
    def on_disconnect(e):
        pass

    page.on_disconnect = on_disconnect

    page.title = "Expected Credit Loss (ECL) - Banking Platform"
    page.bgcolor = "#061d19"
    page.padding = 10
    page.window_width = 1340
    page.window_height = 850

    csv_file_picker = ft.FilePicker()
    page.services.append(csv_file_picker)

    active_submenu_ref = {"current": None}
    right_sidebar_navigation = {"active": False}
    ev_recalculation_state = {
        "progress": 0.0,
        "message": "",
        "running": False,
        "completed": False,
    }
    all_submenu_controls = {}

    home_view_layout, charts_blank_area = get_home_view()
    
    form_display_area = ft.Column(
        controls=[], 
        alignment="start", 
        horizontal_alignment="center", 
        visible=False,
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    def change_middle_content(new_content):
        home_view_layout.visible = False
        charts_blank_area.visible = False
        if right_sidebar_navigation["active"]:
            left_sidebar_box.visible = False
            right_sidebar_box.visible = True
        else:
            right_sidebar_box.visible = False
        form_display_area.controls.clear()
        form_display_area.controls.append(new_content)
        form_display_area.visible = True
        page.update()

    def return_to_home_view(e=None):
        right_sidebar_navigation["active"] = False
        reset_ev_recalculation_state()
        if active_submenu_ref["current"] and active_submenu_ref["current"] in all_submenu_controls:
            all_submenu_controls[active_submenu_ref["current"]].color = "white70"
            all_submenu_controls[active_submenu_ref["current"]].weight = "normal"
            active_submenu_ref["current"] = None
        home_view_layout.visible = True
        charts_blank_area.visible = True
        left_sidebar_box.visible = True
        right_sidebar_box.visible = True
        form_display_area.visible = False
        form_display_area.controls.clear()
        page.update()

    def reset_ev_recalculation_state():
        if ev_recalculation_state["running"]:
            return
        ev_recalculation_state.update({
            "progress": 0.0,
            "message": "",
            "completed": False,
        })

    def handle_submenu_click(text_key, ui_action=None):
        if active_submenu_ref["current"] and active_submenu_ref["current"] in all_submenu_controls:
            all_submenu_controls[active_submenu_ref["current"]].color = "white70"
            all_submenu_controls[active_submenu_ref["current"]].weight = "normal"
        if text_key in all_submenu_controls:
            all_submenu_controls[text_key].color = "#00e676"
            all_submenu_controls[text_key].weight = "bold"
            active_submenu_ref["current"] = text_key
        if ui_action:
            ui_action(None)
        page.update()

    def collapse_left_sidebar():
        reset_ev_recalculation_state()
        right_sidebar_navigation["active"] = True
        left_sidebar_box.visible = False
        right_sidebar_box.visible = True

    def handle_right_submenu_click(text_key, ui_action=None):
        collapse_left_sidebar()
        handle_submenu_click(text_key, ui_action)

    def get_form_action(form_type):
        if form_type == "reporting_date":
            change_middle_content(get_reporting_date_form(page))
        elif form_type == "dropdown_configuration":
            change_middle_content(get_dropdown_configuration_form(page))
        elif form_type == "corporate":
            change_middle_content(get_corporate_profile_form(page))
        elif form_type == "individual":
            change_middle_content(get_individual_profile_form(page))
        elif form_type == "collateral":
            change_middle_content(get_collateral_profile_form(page))
        elif form_type == "credit_ratings":
            change_middle_content(get_credit_ratings_form(page))
        elif form_type == "funded_ac":
            change_middle_content(get_funded_ac_profile_form(page))
        elif form_type == "non_funded_ac":
            change_middle_content(get_non_funded_ac_profile_form(page))
        elif form_type == "economic_variables":
            change_middle_content(get_economic_variables_form(page))
        elif form_type == "haircut":
            change_middle_content(get_collateral_haircut_form(page))
        elif form_type == "ccf":
            change_middle_content(get_ccf_form(page))
        elif form_type == "discounting_factor":
            change_middle_content(get_discounting_factor_form(page))
        elif form_type == "loan_staging_criteria":
            change_middle_content(get_loan_staging_criteria_form(page))
        elif form_type == "proxy_data_model":
            change_middle_content(get_proxy_data_model_form(page))
        elif form_type == "calc_smr":
            change_middle_content(get_stage_migration_form(page))
        elif form_type == "calc_pd":
            change_middle_content(get_pd_calculation_form(
                page,
                ev_recalculation_state,
            ))
        elif form_type == "adjusted_pd":
            change_middle_content(get_adjusted_pd_form(
                page,
                lambda e: get_form_action("adjusted_pd"),
                ev_recalculation_state,
            ))
        elif form_type == "calculated_ead":
            change_middle_content(get_calculated_ead_form(page))
        elif form_type == "distribute_collateral":
            change_middle_content(get_collateral_distribution_form(page))
        elif form_type == "calculate_lgd":
            change_middle_content(get_lgd_calculation_form(page))
        elif form_type == "calc_ecl":
            change_middle_content(get_ecl_calculation_form(page))
        elif form_type == "P-Value":
            change_middle_content(get_p_value_form(
                page,
                lambda e: get_form_action("P-Value"),
                ev_recalculation_state,
            ))
        elif form_type == "Multicollinearity":
            change_middle_content(get_multicollinearity_form(
                page,
                lambda e: get_form_action("Multicollinearity"),
                ev_recalculation_state,
            ))
        elif form_type == "R-Squared":
            change_middle_content(get_r_squared_form(
                page,
                lambda e: get_form_action("R-Squared"),
                ev_recalculation_state,
            ))
        elif form_type == "Variance Inflation Factor":
            change_middle_content(get_vif_form(
                page,
                lambda e: get_form_action("Variance Inflation Factor"),
                ev_recalculation_state,
            ))
        elif form_type.startswith("upload_"):
            profile_type = form_type[len("upload_"):]
            change_middle_content(
                get_csv_upload_view(page, csv_file_picker, profile_type)
            )

    left_sidebar_box = get_left_sidebar(page, all_submenu_controls, handle_submenu_click, return_to_home_view, get_form_action)
    right_sidebar_box = get_right_sidebar(
        page,
        all_submenu_controls,
        handle_right_submenu_click,
        return_to_home_view,
        get_form_action,
        collapse_left_sidebar,
    )

    center_workflow = ft.Column([
        home_view_layout, 
        ft.Container(height=10), 
        charts_blank_area, 
        form_display_area
    ], alignment="start", horizontal_alignment="center", expand=True, spacing=5, scroll=ft.ScrollMode.AUTO)

    main_layout = ft.Row([left_sidebar_box, center_workflow, right_sidebar_box], vertical_alignment="start", alignment="spaceBetween", expand=True)
    page.add(main_layout)

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)