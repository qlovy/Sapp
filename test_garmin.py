# code from https://github.com/cyberjunky/python-garminconnect/tree/master, example.py & demo.py

import logging
import os
import sys
from datetime import date
from getpass import getpass
from os.path import split
from pathlib import Path

from dotenv import load_dotenv

import requests
from garth.exc import GarthException, GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Suppress garminconnect library logging to avoid tracebacks in normal operation
logging.getLogger("garminconnect").setLevel(logging.CRITICAL)

# get environnement variable
load_dotenv()

def safe_api_call(api_method, *args, **kwargs):
    """
    Safe API call wrapper with comprehensive error handling.

    This demonstrates the error handling patterns used throughout the library.
    Returns (success: bool, result: Any, error_message: str)
    """
    try:
        result = api_method(*args, **kwargs)
        return True, result, None

    except GarthHTTPError as e:
        # Handle specific HTTP errors gracefully
        error_str = str(e)
        status_code = getattr(getattr(e, "response", None), "status_code", None)

        if status_code == 400 or "400" in error_str:
            return (
                False,
                None,
                "Endpoint not available (400 Bad Request) - Feature may not be enabled for your account",
            )
        elif status_code == 401 or "401" in error_str:
            return (
                False,
                None,
                "Authentication required (401 Unauthorized) - Please re-authenticate",
            )
        elif status_code == 403 or "403" in error_str:
            return (
                False,
                None,
                "Access denied (403 Forbidden) - Account may not have permission",
            )
        elif status_code == 404 or "404" in error_str:
            return (
                False,
                None,
                "Endpoint not found (404) - Feature may have been moved or removed",
            )
        elif status_code == 429 or "429" in error_str:
            return (
                False,
                None,
                "Rate limit exceeded (429) - Please wait before making more requests",
            )
        elif status_code == 500 or "500" in error_str:
            return (
                False,
                None,
                "Server error (500) - Garmin's servers are experiencing issues",
            )
        elif status_code == 503 or "503" in error_str:
            return (
                False,
                None,
                "Service unavailable (503) - Garmin's servers are temporarily unavailable",
            )
        else:
            return False, None, f"HTTP error: {e}"

    except FileNotFoundError:
        return (
            False,
            None,
            "No valid tokens found. Please login with your email/password to create new tokens.",
        )

    except GarminConnectAuthenticationError as e:
        return False, None, f"Authentication issue: {e}"

    except GarminConnectConnectionError as e:
        return False, None, f"Connection issue: {e}"

    except GarminConnectTooManyRequestsError as e:
        return False, None, f"Rate limit exceeded: {e}"

    except Exception as e:
        return False, None, f"Unexpected error: {e}"


def get_credentials():
    """Get email and password from environment or user input."""
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email:
        email = input("Login email: ")
    if not password:
        password = getpass("Enter password: ")

    return email, password


def init_api() -> Garmin | None:
    """Initialize Garmin API with authentication and token management."""

    """
    # Configure token storage
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = Path(tokenstore).expanduser()

    print(f"🔐 Token storage: {tokenstore_path}")

    # Check if token files exist
    if tokenstore_path.exists():
        print("📄 Found existing token directory")
        token_files = list(tokenstore_path.glob("*.json"))
        if token_files:
            print(
                f"🔑 Found {len(token_files)} token file(s): {[f.name for f in token_files]}"
            )
        else:
            print("⚠️ Token directory exists but no token files found")
    else:
        print("📭 No existing token directory found")

    # First try to login with stored tokens
    try:
        print("🔄 Attempting to use saved authentication tokens...")
        garmin = Garmin()
        garmin.login(str(tokenstore_path))
        print("✅ Successfully logged in using saved tokens!")
        return garmin

    except (
        FileNotFoundError,
        GarthHTTPError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ):
        print("🔑 No valid tokens found. Requesting fresh login credentials.")
    """
        
    # Loop for credential entry with retry on auth failure
    while True:
        try:
            # Get credentials
            email, password = get_credentials()

            print("Logging in with credentials...")
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                print("🔐 Multi-factor authentication required")

                mfa_code = input("Please enter your MFA code: ")
                print("🔄 Submitting MFA code...")

                try:
                    garmin.resume_login(result2, mfa_code)
                    print("✅ MFA authentication successful!")

                except GarthHTTPError as garth_error:
                    # Handle specific HTTP errors from MFA
                    error_str = str(garth_error)
                    if "429" in error_str and "Too Many Requests" in error_str:
                        print("❌ Too many MFA attempts")
                        print("💡 Please wait 30 minutes before trying again")
                        sys.exit(1)
                    elif "401" in error_str or "403" in error_str:
                        print("❌ Invalid MFA code")
                        print("💡 Please verify your MFA code and try again")
                        continue
                    else:
                        # Other HTTP errors - don't retry
                        print(f"❌ MFA authentication failed: {garth_error}")
                        sys.exit(1)

                except GarthException as garth_error:
                    print(f"❌ MFA authentication failed: {garth_error}")
                    print("💡 Please verify your MFA code and try again")
                    continue

            """
            # Save tokens for future use
            garmin.garth.dump(str(tokenstore_path))
            print(f"💾 Authentication tokens saved to: {tokenstore_path}")
            """
            print("✅ Login successful!")
            return garmin

        except GarminConnectAuthenticationError:
            print("❌ Authentication failed:")
            print("💡 Please check your username and password and try again")
            # Continue the loop to retry
            continue

        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectConnectionError,
            requests.exceptions.HTTPError,
        ) as err:
            print(f"❌ Connection error: {err}")
            print("💡 Please check your internet connection and try again")
            return None

        except KeyboardInterrupt:
            print("\n👋 Cancelled by user")
            return None

def get_single_activity_data(api: Garmin, nb_of_days, data) -> None:
    try:
        data.append(api.get_activities(0, nb_of_days))
    except Exception as e:
        print(f"❌ Error getting single activity: {e}")










def execute_api_call(api: Garmin, key: str) -> None:
    """Execute an API call based on the key."""
    if not api:
        print("API not available")
        return

    try:
        # Map of keys to API methods - this can be extended as needed
        api_methods = {
            # User & Profile
            # "get_full_name": lambda: call_and_display(
            #     api.get_full_name,
            #     method_name="get_full_name",
            #     api_call_desc="api.get_full_name()",
            # ),
            # "get_unit_system": lambda: call_and_display(
            #     api.get_unit_system,
            #     method_name="get_unit_system",
            #     api_call_desc="api.get_unit_system()",
            # ),
            # "get_user_profile": lambda: call_and_display(
            #     api.get_user_profile,
            #     method_name="get_user_profile",
            #     api_call_desc="api.get_user_profile()",
            # ),
            # "get_userprofile_settings": lambda: call_and_display(
            #     api.get_userprofile_settings,
            #     method_name="get_userprofile_settings",
            #     api_call_desc="api.get_userprofile_settings()",
            # ),
            # Daily Health & Activity
            "get_stats": lambda: call_and_display(
                api.get_stats,
                config.today.isoformat(),
                method_name="get_stats",
                api_call_desc=f"api.get_stats('{config.today.isoformat()}')",
            ),
            "get_user_summary": lambda: call_and_display(
                api.get_user_summary,
                config.today.isoformat(),
                method_name="get_user_summary",
                api_call_desc=f"api.get_user_summary('{config.today.isoformat()}')",
            ),
            "get_stats_and_body": lambda: call_and_display(
                api.get_stats_and_body,
                config.today.isoformat(),
                method_name="get_stats_and_body",
                api_call_desc=f"api.get_stats_and_body('{config.today.isoformat()}')",
            ),
            "get_steps_data": lambda: call_and_display(
                api.get_steps_data,
                config.today.isoformat(),
                method_name="get_steps_data",
                api_call_desc=f"api.get_steps_data('{config.today.isoformat()}')",
            ),
            "get_heart_rates": lambda: call_and_display(
                api.get_heart_rates,
                config.today.isoformat(),
                method_name="get_heart_rates",
                api_call_desc=f"api.get_heart_rates('{config.today.isoformat()}')",
            ),
            "get_resting_heart_rate": lambda: call_and_display(
                api.get_rhr_day,
                config.today.isoformat(),
                method_name="get_rhr_day",
                api_call_desc=f"api.get_rhr_day('{config.today.isoformat()}')",
            ),
            "get_sleep_data": lambda: call_and_display(
                api.get_sleep_data,
                config.today.isoformat(),
                method_name="get_sleep_data",
                api_call_desc=f"api.get_sleep_data('{config.today.isoformat()}')",
            ),
            "get_all_day_stress": lambda: call_and_display(
                api.get_all_day_stress,
                config.today.isoformat(),
                method_name="get_all_day_stress",
                api_call_desc=f"api.get_all_day_stress('{config.today.isoformat()}')",
            ),
            # Advanced Health Metrics
            "get_training_readiness": lambda: call_and_display(
                api.get_training_readiness,
                config.today.isoformat(),
                method_name="get_training_readiness",
                api_call_desc=f"api.get_training_readiness('{config.today.isoformat()}')",
            ),
            "get_morning_training_readiness": lambda: call_and_display(
                api.get_morning_training_readiness,
                config.today.isoformat(),
                method_name="get_morning_training_readiness",
                api_call_desc=f"api.get_morning_training_readiness('{config.today.isoformat()}')",
            ),
            "get_training_status": lambda: call_and_display(
                api.get_training_status,
                config.today.isoformat(),
                method_name="get_training_status",
                api_call_desc=f"api.get_training_status('{config.today.isoformat()}')",
            ),
            "get_respiration_data": lambda: call_and_display(
                api.get_respiration_data,
                config.today.isoformat(),
                method_name="get_respiration_data",
                api_call_desc=f"api.get_respiration_data('{config.today.isoformat()}')",
            ),
            "get_spo2_data": lambda: call_and_display(
                api.get_spo2_data,
                config.today.isoformat(),
                method_name="get_spo2_data",
                api_call_desc=f"api.get_spo2_data('{config.today.isoformat()}')",
            ),
            "get_max_metrics": lambda: call_and_display(
                api.get_max_metrics,
                config.today.isoformat(),
                method_name="get_max_metrics",
                api_call_desc=f"api.get_max_metrics('{config.today.isoformat()}')",
            ),
            "get_hrv_data": lambda: call_and_display(
                api.get_hrv_data,
                config.today.isoformat(),
                method_name="get_hrv_data",
                api_call_desc=f"api.get_hrv_data('{config.today.isoformat()}')",
            ),
            "get_fitnessage_data": lambda: call_and_display(
                api.get_fitnessage_data,
                config.today.isoformat(),
                method_name="get_fitnessage_data",
                api_call_desc=f"api.get_fitnessage_data('{config.today.isoformat()}')",
            ),
            "get_stress_data": lambda: call_and_display(
                api.get_stress_data,
                config.today.isoformat(),
                method_name="get_stress_data",
                api_call_desc=f"api.get_stress_data('{config.today.isoformat()}')",
            ),
            "get_lactate_threshold": lambda: get_lactate_threshold_data(api),
            "get_intensity_minutes_data": lambda: call_and_display(
                api.get_intensity_minutes_data,
                config.today.isoformat(),
                method_name="get_intensity_minutes_data",
                api_call_desc=f"api.get_intensity_minutes_data('{config.today.isoformat()}')",
            ),
            "get_lifestyle_logging_data": lambda: call_and_display(
                api.get_lifestyle_logging_data,
                config.today.isoformat(),
                method_name="get_lifestyle_logging_data",
                api_call_desc=f"api.get_lifestyle_logging_data('{config.today.isoformat()}')",
            ),
            # Historical Data & Trends
            "get_daily_steps": lambda: call_and_display(
                api.get_daily_steps,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_daily_steps",
                api_call_desc=f"api.get_daily_steps('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_body_battery": lambda: call_and_display(
                api.get_body_battery,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_body_battery",
                api_call_desc=f"api.get_body_battery('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_floors": lambda: call_and_display(
                api.get_floors,
                config.week_start.isoformat(),
                method_name="get_floors",
                api_call_desc=f"api.get_floors('{config.week_start.isoformat()}')",
            ),
            "get_blood_pressure": lambda: call_and_display(
                api.get_blood_pressure,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_blood_pressure",
                api_call_desc=f"api.get_blood_pressure('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_progress_summary_between_dates": lambda: call_and_display(
                api.get_progress_summary_between_dates,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_progress_summary_between_dates",
                api_call_desc=f"api.get_progress_summary_between_dates('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_body_battery_events": lambda: call_and_display(
                api.get_body_battery_events,
                config.week_start.isoformat(),
                method_name="get_body_battery_events",
                api_call_desc=f"api.get_body_battery_events('{config.week_start.isoformat()}')",
            ),
            "get_weekly_steps": lambda: call_and_display(
                api.get_weekly_steps,
                config.today.isoformat(),
                52,
                method_name="get_weekly_steps",
                api_call_desc=f"api.get_weekly_steps('{config.today.isoformat()}', 52)",
            ),
            "get_weekly_stress": lambda: call_and_display(
                api.get_weekly_stress,
                config.today.isoformat(),
                52,
                method_name="get_weekly_stress",
                api_call_desc=f"api.get_weekly_stress('{config.today.isoformat()}', 52)",
            ),
            "get_weekly_intensity_minutes": lambda: call_and_display(
                api.get_weekly_intensity_minutes,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_weekly_intensity_minutes",
                api_call_desc=f"api.get_weekly_intensity_minutes('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            # Activities & Workouts
            "get_activities": lambda: call_and_display(
                api.get_activities,
                config.start,
                config.default_limit,
                method_name="get_activities",
                api_call_desc=f"api.get_activities({config.start}, {config.default_limit})",
            ),
            "get_last_activity": lambda: call_and_display(
                api.get_last_activity,
                method_name="get_last_activity",
                api_call_desc="api.get_last_activity()",
            ),
            "get_activities_fordate": lambda: call_and_display(
                api.get_activities_fordate,
                config.today.isoformat(),
                method_name="get_activities_fordate",
                api_call_desc=f"api.get_activities_fordate('{config.today.isoformat()}')",
            ),
            "get_activity_types": lambda: call_and_display(
                api.get_activity_types,
                method_name="get_activity_types",
                api_call_desc="api.get_activity_types()",
            ),
            "get_workouts": lambda: call_and_display(
                api.get_workouts,
                method_name="get_workouts",
                api_call_desc="api.get_workouts()",
            ),
            "get_training_plan_by_id": lambda: get_training_plan_by_id_data(api),
            "get_training_plans": lambda: call_and_display(
                api.get_training_plans,
                method_name="get_training_plans",
                api_call_desc="api.get_training_plans()",
            ),
            "upload_activity": lambda: upload_activity_file(api),
            "download_activities": lambda: download_activities_by_date(api),
            "get_activity_splits": lambda: get_activity_splits_data(api),
            "get_activity_typed_splits": lambda: get_activity_typed_splits_data(api),
            "get_activity_split_summaries": lambda: get_activity_split_summaries_data(
                api
            ),
            "get_activity_weather": lambda: get_activity_weather_data(api),
            "get_activity_hr_in_timezones": lambda: get_activity_hr_timezones_data(api),
            "get_activity_power_in_timezones": lambda: get_activity_power_timezones_data(
                api
            ),
            "get_cycling_ftp": lambda: get_cycling_ftp_data(api),
            "get_activity_details": lambda: get_activity_details_data(api),
            "get_activity_gear": lambda: get_activity_gear_data(api),
            "get_activity": lambda: get_single_activity_data(api),
            "get_activity_exercise_sets": lambda: get_activity_exercise_sets_data(api),
            "get_workout_by_id": lambda: get_workout_by_id_data(api),
            "download_workout": lambda: download_workout_data(api),
            "upload_workout": lambda: upload_workout_data(api),
            "upload_running_workout": lambda: upload_running_workout_data(api),
            "upload_cycling_workout": lambda: upload_cycling_workout_data(api),
            "upload_swimming_workout": lambda: upload_swimming_workout_data(api),
            "upload_walking_workout": lambda: upload_walking_workout_data(api),
            "upload_hiking_workout": lambda: upload_hiking_workout_data(api),
            "get_scheduled_workout_by_id": lambda: get_scheduled_workout_by_id_data(
                api
            ),
            "count_activities": lambda: call_and_display(
                api.count_activities,
                method_name="count_activities",
                api_call_desc="api.count_activities()",
            ),
            # Body Composition & Weight
            "get_body_composition": lambda: call_and_display(
                api.get_body_composition,
                config.today.isoformat(),
                method_name="get_body_composition",
                api_call_desc=f"api.get_body_composition('{config.today.isoformat()}')",
            ),
            "get_weigh_ins": lambda: call_and_display(
                api.get_weigh_ins,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_weigh_ins",
                api_call_desc=f"api.get_weigh_ins('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_daily_weigh_ins": lambda: call_and_display(
                api.get_daily_weigh_ins,
                config.today.isoformat(),
                method_name="get_daily_weigh_ins",
                api_call_desc=f"api.get_daily_weigh_ins('{config.today.isoformat()}')",
            ),
            # "add_weigh_in": lambda: add_weigh_in_data(api),
            # "set_body_composition": lambda: set_body_composition_data(api),
            # "add_body_composition": lambda: add_body_composition_data(api),
            # "delete_weigh_ins": lambda: delete_weigh_ins_data(api),
            # "delete_weigh_in": lambda: delete_weigh_in_data(api),
            # Goals & Achievements
            "get_personal_records": lambda: call_and_display(
                api.get_personal_record,
                method_name="get_personal_record",
                api_call_desc="api.get_personal_record()",
            ),
            # "get_earned_badges": lambda: call_and_display(
            #     api.get_earned_badges,
            #     method_name="get_earned_badges",
            #     api_call_desc="api.get_earned_badges()",
            # ),
            # "get_adhoc_challenges": lambda: call_and_display(
            #     api.get_adhoc_challenges,
            #     config.start,
            #     config.default_limit,
            #     method_name="get_adhoc_challenges",
            #     api_call_desc=f"api.get_adhoc_challenges({config.start}, {config.default_limit})",
            # ),
            # "get_available_badge_challenges": lambda: call_and_display(
            #     api.get_available_badge_challenges,
            #     config.start_badge,
            #     config.default_limit,
            #     method_name="get_available_badge_challenges",
            #     api_call_desc=f"api.get_available_badge_challenges({config.start_badge}, {config.default_limit})",
            # ),
            # "get_active_goals": lambda: call_and_display(
            #     api.get_goals,
            #     status="active",
            #     start=config.start,
            #     limit=config.default_limit,
            #     method_name="get_goals",
            #     api_call_desc=f"api.get_goals(status='active', start={config.start}, limit={config.default_limit})",
            # ),
            # "get_future_goals": lambda: call_and_display(
            #     api.get_goals,
            #     status="future",
            #     start=config.start,
            #     limit=config.default_limit,
            #     method_name="get_goals",
            #     api_call_desc=f"api.get_goals(status='future', start={config.start}, limit={config.default_limit})",
            # ),
            # "get_past_goals": lambda: call_and_display(
            #     api.get_goals,
            #     status="past",
            #     start=config.start,
            #     limit=config.default_limit,
            #     method_name="get_goals",
            #     api_call_desc=f"api.get_goals(status='past', start={config.start}, limit={config.default_limit})",
            # ),
            # "get_badge_challenges": lambda: call_and_display(
            #     api.get_badge_challenges,
            #     config.start_badge,
            #     config.default_limit,
            #     method_name="get_badge_challenges",
            #     api_call_desc=f"api.get_badge_challenges({config.start_badge}, {config.default_limit})",
            # ),
            # "get_non_completed_badge_challenges": lambda: call_and_display(
            #     api.get_non_completed_badge_challenges,
            #     config.start_badge,
            #     config.default_limit,
            #     method_name="get_non_completed_badge_challenges",
            #     api_call_desc=f"api.get_non_completed_badge_challenges({config.start_badge}, {config.default_limit})",
            # ),
            # "get_inprogress_virtual_challenges": lambda: get_virtual_challenges_data(
            #     api
            # ),
            "get_race_predictions": lambda: call_and_display(
                api.get_race_predictions,
                method_name="get_race_predictions",
                api_call_desc="api.get_race_predictions()",
            ),
            "get_hill_score": lambda: call_and_display(
                api.get_hill_score,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_hill_score",
                api_call_desc=f"api.get_hill_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_endurance_score": lambda: call_and_display(
                api.get_endurance_score,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_endurance_score",
                api_call_desc=f"api.get_endurance_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_available_badges": lambda: call_and_display(
                api.get_available_badges,
                method_name="get_available_badges",
                api_call_desc="api.get_available_badges()",
            ),
            "get_in_progress_badges": lambda: call_and_display(
                api.get_in_progress_badges,
                method_name="get_in_progress_badges",
                api_call_desc="api.get_in_progress_badges()",
            ),
            # Device & Technical
            "get_devices": lambda: call_and_display(
                api.get_devices,
                method_name="get_devices",
                api_call_desc="api.get_devices()",
            ),
            "get_device_alarms": lambda: call_and_display(
                api.get_device_alarms,
                method_name="get_device_alarms",
                api_call_desc="api.get_device_alarms()",
            ),
            "get_solar_data": lambda: get_solar_data(api),
            "request_reload": lambda: call_and_display(
                api.request_reload,
                config.today.isoformat(),
                method_name="request_reload",
                api_call_desc=f"api.request_reload('{config.today.isoformat()}')",
            ),
            "get_device_settings": lambda: get_device_settings_data(api),
            "get_device_last_used": lambda: call_and_display(
                api.get_device_last_used,
                method_name="get_device_last_used",
                api_call_desc="api.get_device_last_used()",
            ),
            "get_primary_training_device": lambda: call_and_display(
                api.get_primary_training_device,
                method_name="get_primary_training_device",
                api_call_desc="api.get_primary_training_device()",
            ),
            # Gear & Equipment
            "get_gear": lambda: get_gear_data(api),
            "get_gear_defaults": lambda: get_gear_defaults_data(api),
            "get_gear_stats": lambda: get_gear_stats_data(api),
            "get_gear_activities": lambda: get_gear_activities_data(api),
            "set_gear_default": lambda: set_gear_default_data(api),
            "track_gear_usage": lambda: track_gear_usage_data(api),
            "add_and_remove_gear_to_activity": lambda: add_and_remove_gear_to_activity(
                api
            ),
            # Hydration & Wellness
            "get_hydration_data": lambda: call_and_display(
                api.get_hydration_data,
                config.today.isoformat(),
                method_name="get_hydration_data",
                api_call_desc=f"api.get_hydration_data('{config.today.isoformat()}')",
            ),
            "get_pregnancy_summary": lambda: call_and_display(
                api.get_pregnancy_summary,
                method_name="get_pregnancy_summary",
                api_call_desc="api.get_pregnancy_summary()",
            ),
            "get_all_day_events": lambda: call_and_display(
                api.get_all_day_events,
                config.week_start.isoformat(),
                method_name="get_all_day_events",
                api_call_desc=f"api.get_all_day_events('{config.week_start.isoformat()}')",
            ),
            # "add_hydration_data": lambda: add_hydration_data_entry(api),
            # "set_blood_pressure": lambda: set_blood_pressure_data(api),
            "get_menstrual_data_for_date": lambda: call_and_display(
                api.get_menstrual_data_for_date,
                config.today.isoformat(),
                method_name="get_menstrual_data_for_date",
                api_call_desc=f"api.get_menstrual_data_for_date('{config.today.isoformat()}')",
            ),
            "get_menstrual_calendar_data": lambda: call_and_display(
                api.get_menstrual_calendar_data,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_menstrual_calendar_data",
                api_call_desc=f"api.get_menstrual_calendar_data('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            # Blood Pressure Management
            # "delete_blood_pressure": lambda: delete_blood_pressure_data(api),
            # Activity Management
            # "set_activity_name": lambda: set_activity_name_data(api),
            # "set_activity_type": lambda: set_activity_type_data(api),
            # "create_manual_activity": lambda: create_manual_activity_data(api),
            # "delete_activity": lambda: delete_activity_data(api),
            "get_activities_by_date": lambda: call_and_display(
                api.get_activities_by_date,
                config.today.isoformat(),
                config.today.isoformat(),
                method_name="get_activities_by_date",
                api_call_desc=f"api.get_activities_by_date('{config.today.isoformat()}', '{config.today.isoformat()}')",
            ),
            # System & Export
            # "create_health_report": lambda: DataExporter.create_health_report(api),
            # "remove_tokens": lambda: remove_stored_tokens(),
            "disconnect": lambda: disconnect_api(api),
            # GraphQL Queries
            "query_garmin_graphql": lambda: query_garmin_graphql_data(api),
        }

        if key in api_methods:
            print(f"\n🔄 Executing: {key}")
            api_methods[key]()
        else:
            print(f"❌ API method '{key}' not implemented yet. You can add it later!")

    except Exception as e:
        print(f"❌ Error executing {key}: {e}")




def main():
    # Initialize API with authentication (will only prompt for credentials if needed)
    api = init_api()

    if not api:
        print("❌ Failed to initialize API. Exiting.")
        return
    
    data = []

    nb_activity_import = 2 # nombre max: 20

    get_single_activity_data(api, nb_activity_import, data)

    f = open("./data/data.txt", "w")
    f.write(str(data))
    f.close()

    execute_api_call(api, "get_lactate_threshold")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🚪 Exiting example. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")