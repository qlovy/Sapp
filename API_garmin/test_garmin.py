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

import json
import datetime
from datetime import timedelta
from typing import Any

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

def init_api(email: str | None = None, password: str | None = None) -> Garmin | None:
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
            if not email:
                email = input("Login email: ")
            if not password:
                password = getpass("Enter password: ")

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




class Config:
    """Configuration class for the Garmin Connect API demo."""

    def __init__(self):
        # Load environment variables
        self.email = os.getenv("GARMIN_EMAIL")
        self.password = os.getenv("GARMIN_PASSWORD")
        #self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
        # self.tokenstore_base64 = (
        #     os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
        # )

        # Date settings
        self.today = datetime.date.today()
        self.week_start = self.today - timedelta(days=7)
        self.month_start = self.today - timedelta(days=30)

        # API call settings
        self.default_limit = 100
        self.start = 0
        self.start_badge = 1  # Badge related calls start counting at 1

        # Activity settings
        # self.activitytype = ""  # Possible values: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
        # self.activityfile = "test_data/*.gpx"  # Supported file types: .fit .gpx .tcx
        # self.workoutfile = "test_data/sample_workout.json"  # Sample workout JSON file

        # Export settings
        # self.export_dir = Path("your_data")
        # self.export_dir.mkdir(exist_ok=True)


# Initialize configuration
config = Config()

def _display_single(api_call: str, output: Any):
    """Internal function to display single API response."""
    print(f"\n📡 API Call: {api_call}")
    print("-" * 50)

    if output is None:
        print("No data returned")
        # Save empty JSON to response.json in the export directory
        response_file = config.export_dir / "response.json"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(f"{'-' * 20} {api_call} {'-' * 20}\n{{}}\n{'-' * 77}\n")
        return

    try:
        # Format the output
        if isinstance(output, int | str | dict | list):
            formatted_output = json.dumps(output, indent=2, default=str)
        else:
            formatted_output = str(output)

        # Save to response.json in the export directory
        response_content = (
            f"{'-' * 20} {api_call} {'-' * 20}\n{formatted_output}\n{'-' * 77}\n"
        )

        response_file = config.export_dir / "response.json"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(response_content)

        print(formatted_output)
        print("-" * 77)

    except Exception as e:
        print(f"Error formatting output: {e}")
        print(output)


def _display_group(group_name: str, api_responses: list[tuple[str, Any]]):
    """Internal function to display grouped API responses."""
    print(f"\n📡 API Group: {group_name}")

    # Collect all responses for saving
    all_responses = {}
    response_content_parts = []

    for api_call, output in api_responses:
        print(f"\n📋 {api_call}")
        print("-" * 50)

        if output is None:
            print("No data returned")
            formatted_output = "{}"
        else:
            try:
                if isinstance(output, int | str | dict | list):
                    formatted_output = json.dumps(output, indent=2, default=str)
                else:
                    formatted_output = str(output)
                print(formatted_output)
            except Exception as e:
                print(f"Error formatting output: {e}")
                formatted_output = str(output)
                print(output)

        # Store for grouped response file
        all_responses[api_call] = output
        response_content_parts.append(
            f"{'-' * 20} {api_call} {'-' * 20}\n{formatted_output}"
        )
        print("-" * 50)

    # Save grouped responses to file
    # try:
    #     response_file = config.export_dir / "response.json"
    #     header = "=" * 20 + f" {group_name} " + "=" * 20
    #     footer = "=" * 77
    #     content_lines = [header, *response_content_parts, footer, ""]
    #     grouped_content = "\n".join(content_lines)
    #     with response_file.open("w", encoding="utf-8") as f:
    #         f.write(grouped_content)

    #     print(f"\n✅ Grouped responses saved to: {response_file}")
    #     print("=" * 77)

    # except Exception as e:
    #     print(f"Error saving grouped responses: {e}")


def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}"


def safe_call_for_group(
    api_method,
    *args,
    method_name: str | None = None,
    api_call_desc: str | None = None,
    **kwargs,
):
    """Safe API call wrapper that returns result suitable for grouped display.

    Args:
        api_method: The API method to call
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        api_call_desc: Description for display purposes (optional)
        **kwargs: Keyword arguments for the API method

    Returns:
        tuple: (api_call_description: str, result: Any) - suitable for grouped display

    """
    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    if api_call_desc is None:
        # Try to construct a reasonable description
        args_str = ", ".join(str(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        api_call_desc = f"{method_name}({all_args})"

    success, result, error_msg = safe_api_call(
        api_method, *args, method_name=method_name, **kwargs
    )

    if success:
        return api_call_desc, result
    return f"{api_call_desc} [ERROR]", {"error": error_msg}


def get_solar_data(api: Garmin) -> None:
    """Get solar data from all Garmin devices using centralized error handling."""
    print("☀️ Getting solar data from devices...")

    # Collect all API responses for grouped display
    api_responses = []

    # Get all devices using centralized wrapper
    api_responses.append(
        safe_call_for_group(
            api.get_devices,
            method_name="get_devices",
            api_call_desc="api.get_devices()",
        )
    )

    # Get device last used using centralized wrapper
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get the device list to process solar data
    devices_success, devices, _ = safe_api_call(
        api.get_devices, method_name="get_devices"
    )

    # Get solar data for each device
    if devices_success and devices:
        for device in devices:
            device_id = device.get("deviceId")
            if device_id:
                device_name = device.get("displayName", f"Device {device_id}")
                print(
                    f"\n☀️ Getting solar data for device: {device_name} (ID: {device_id})"
                )

                # Use centralized wrapper for each device's solar data
                api_responses.append(
                    safe_call_for_group(
                        api.get_device_solar_data,
                        device_id,
                        config.today.isoformat(),
                        method_name="get_device_solar_data",
                        api_call_desc=f"api.get_device_solar_data({device_id}, '{config.today.isoformat()}')",
                    )
                )
    else:
        print("ℹ️ No devices found or error retrieving devices")

    # Display all responses as a group
    call_and_display(group_name="Solar Data Collection", api_responses=api_responses)


# def upload_activity_file(api: Garmin) -> None:
#     """Upload activity data from file."""
#     import glob

#     try:
#         # List all .gpx files in test_data
#         gpx_files = glob.glob(config.activityfile)
#         if not gpx_files:
#             print("❌ No .gpx files found in test_data directory.")
#             print("ℹ️ Please add GPX files to test_data before uploading.")
#             return

#         print("Select a GPX file to upload:")
#         for idx, fname in enumerate(gpx_files, 1):
#             print(f"  {idx}. {fname}")

#         while True:
#             try:
#                 choice = int(input(f"Enter number (1-{len(gpx_files)}): "))
#                 if 1 <= choice <= len(gpx_files):
#                     selected_file = gpx_files[choice - 1]
#                     break
#                 print("Invalid selection. Try again.")
#             except ValueError:
#                 print("Please enter a valid number.")

#         print(f"📤 Uploading activity from file: {selected_file}")

#         call_and_display(
#             api.upload_activity,
#             selected_file,
#             method_name="upload_activity",
#             api_call_desc=f"api.upload_activity({selected_file})",
#         )

#     except FileNotFoundError:
#         print(f"❌ File not found: {selected_file}")
#         print("ℹ️ Please ensure the activity file exists in the current directory")
#     except requests.exceptions.HTTPError as e:
#         if e.response.status_code == 409:
#             print(
#                 "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect"
#             )
#             print("ℹ️ Garmin Connect prevents duplicate activities from being uploaded")
#             print(
#                 "💡 Try modifying the activity timestamps or creating a new activity file"
#             )
#         elif e.response.status_code == 413:
#             print(
#                 "❌ File too large: The activity file exceeds Garmin Connect's size limit"
#             )
#             print("💡 Try compressing the file or reducing the number of data points")
#         elif e.response.status_code == 422:
#             print(
#                 "❌ Invalid file format: The activity file format is not supported or corrupted"
#             )
#             print("ℹ️ Supported formats: FIT, GPX, TCX")
#             print("💡 Try converting to a different format or check file integrity")
#         elif e.response.status_code == 400:
#             print("❌ Bad request: Invalid activity data or malformed file")
#             print(
#                 "💡 Check if the activity file contains valid GPS coordinates and timestamps"
#             )
#         elif e.response.status_code == 401:
#             print("❌ Authentication failed: Please login again")
#             print("💡 Your session may have expired")
#         elif e.response.status_code == 429:
#             print("❌ Rate limit exceeded: Too many upload requests")
#             print("💡 Please wait a few minutes before trying again")
#         else:
#             print(f"❌ HTTP Error {e.response.status_code}: {e}")
#     except GarminConnectAuthenticationError as e:
#         print(f"❌ Authentication error: {e}")
#         print("💡 Please check your login credentials and try again")
#     except GarminConnectConnectionError as e:
#         print(f"❌ Connection error: {e}")
#         print("💡 Please check your internet connection and try again")
#     except GarminConnectTooManyRequestsError as e:
#         print(f"❌ Too many requests: {e}")
#         print("💡 Please wait a few minutes before trying again")
#     except Exception as e:
#         error_str = str(e)
#         if "409 Client Error: Conflict" in error_str:
#             print(
#                 "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect"
#             )
#             print("ℹ️ Garmin Connect prevents duplicate activities from being uploaded")
#             print(
#                 "💡 Try modifying the activity timestamps or creating a new activity file"
#             )
#         elif "413" in error_str and "Request Entity Too Large" in error_str:
#             print(
#                 "❌ File too large: The activity file exceeds Garmin Connect's size limit"
#             )
#             print("💡 Try compressing the file or reducing the number of data points")
#         elif "422" in error_str and "Unprocessable Entity" in error_str:
#             print(
#                 "❌ Invalid file format: The activity file format is not supported or corrupted"
#             )
#             print("ℹ️ Supported formats: FIT, GPX, TCX")
#             print("💡 Try converting to a different format or check file integrity")
#         elif "400" in error_str and "Bad Request" in error_str:
#             print("❌ Bad request: Invalid activity data or malformed file")
#             print(
#                 "💡 Check if the activity file contains valid GPS coordinates and timestamps"
#             )
#         elif "401" in error_str and "Unauthorized" in error_str:
#             print("❌ Authentication failed: Please login again")
#             print("💡 Your session may have expired")
#         elif "429" in error_str and "Too Many Requests" in error_str:
#             print("❌ Rate limit exceeded: Too many upload requests")
#             print("💡 Please wait a few minutes before trying again")
#         else:
#             print(f"❌ Unexpected error uploading activity: {e}")
#             print("💡 Please check the file format and try again")


# def download_activities_by_date(api: Garmin) -> None:
#     """Download activities by date range in multiple formats."""
#     try:
#         print(
#             f"📥 Downloading activities by date range ({config.week_start.isoformat()} to {config.today.isoformat()})..."
#         )

#         # Get activities for the date range (last 7 days as default)
#         activities = api.get_activities_by_date(
#             config.week_start.isoformat(), config.today.isoformat()
#         )

#         if not activities:
#             print("ℹ️ No activities found in the specified date range")
#             return

#         print(f"📊 Found {len(activities)} activities to download")

#         # Download each activity in multiple formats
#         for activity in activities:
#             activity_id = activity.get("activityId")
#             activity_name = activity.get("activityName", "Unknown")
#             start_time = activity.get("startTimeLocal", "").replace(":", "-")

#             if not activity_id:
#                 continue

#             print(f"📥 Downloading: {activity_name} (ID: {activity_id})")

#             # Download formats: GPX, TCX, ORIGINAL, CSV
#             formats = ["GPX", "TCX", "ORIGINAL", "CSV"]

#             for fmt in formats:
#                 try:
#                     filename = f"{start_time}_{activity_id}_ACTIVITY.{fmt.lower()}"
#                     if fmt == "ORIGINAL":
#                         filename = f"{start_time}_{activity_id}_ACTIVITY.zip"

#                     filepath = config.export_dir / filename

#                     if fmt == "CSV":
#                         # Get activity details for CSV export
#                         activity_details = api.get_activity_details(activity_id)
#                         with open(filepath, "w", encoding="utf-8") as f:
#                             import json

#                             json.dump(activity_details, f, indent=2, ensure_ascii=False)
#                         print(f"  ✅ {fmt}: {filename}")
#                     else:
#                         # Download the file from Garmin using proper enum values
#                         format_mapping = {
#                             "GPX": api.ActivityDownloadFormat.GPX,
#                             "TCX": api.ActivityDownloadFormat.TCX,
#                             "ORIGINAL": api.ActivityDownloadFormat.ORIGINAL,
#                         }

#                         dl_fmt = format_mapping[fmt]
#                         content = api.download_activity(activity_id, dl_fmt=dl_fmt)

#                         if content:
#                             with open(filepath, "wb") as f:
#                                 f.write(content)
#                             print(f"  ✅ {fmt}: {filename}")
#                         else:
#                             print(f"  ❌ {fmt}: No content available")

#                 except Exception as e:
#                     print(f"  ❌ {fmt}: Error downloading - {e}")

#         print(f"✅ Activity downloads completed! Files saved to: {config.export_dir}")

#     except Exception as e:
#         print(f"❌ Error downloading activities: {e}")


# def add_weigh_in_data(api: Garmin) -> None:
#     """Add a weigh-in with timestamps."""
#     try:
#         # Get weight input from user
#         print("⚖️ Adding weigh-in entry")
#         print("-" * 30)

#         # Weight input with validation
#         while True:
#             try:
#                 weight_str = input("Enter weight (30-300, default: 85.1): ").strip()
#                 if not weight_str:
#                     weight = 85.1
#                     break
#                 weight = float(weight_str)
#                 if 30 <= weight <= 300:
#                     break
#                 print("❌ Weight must be between 30 and 300")
#             except ValueError:
#                 print("❌ Please enter a valid number")

#         # Unit selection
#         while True:
#             unit_input = input("Enter unit (kg/lbs, default: kg): ").strip().lower()
#             if not unit_input:
#                 weight_unit = "kg"
#                 break
#             if unit_input in ["kg", "lbs"]:
#                 weight_unit = unit_input
#                 break
#             print("❌ Please enter 'kg' or 'lbs'")

#         print(f"⚖️ Adding weigh-in: {weight} {weight_unit}")

#         # Collect all API responses for grouped display
#         api_responses = []

#         # Add a simple weigh-in
#         result1 = api.add_weigh_in(weight=weight, unitKey=weight_unit)
#         api_responses.append(
#             (f"api.add_weigh_in(weight={weight}, unitKey={weight_unit})", result1)
#         )

#         # Add a weigh-in with timestamps for yesterday
#         import datetime
#         from datetime import timezone

#         yesterday = config.today - datetime.timedelta(days=1)  # Get yesterday's date
#         weigh_in_date = datetime.datetime.strptime(yesterday.isoformat(), "%Y-%m-%d")
#         local_timestamp = weigh_in_date.strftime("%Y-%m-%dT%H:%M:%S")
#         gmt_timestamp = weigh_in_date.astimezone(timezone.utc).strftime(
#             "%Y-%m-%dT%H:%M:%S"
#         )

#         result2 = api.add_weigh_in_with_timestamps(
#             weight=weight,
#             unitKey=weight_unit,
#             dateTimestamp=local_timestamp,
#             gmtTimestamp=gmt_timestamp,
#         )
#         api_responses.append(
#             (
#                 f"api.add_weigh_in_with_timestamps(weight={weight}, unitKey={weight_unit}, dateTimestamp={local_timestamp}, gmtTimestamp={gmt_timestamp})",
#                 result2,
#             )
#         )

#         # Display all responses as a group
#         call_and_display(group_name="Weigh-in Data Entry", api_responses=api_responses)

#         print("✅ Weigh-in data added successfully!")

#     except Exception as e:
#         print(f"❌ Error adding weigh-in: {e}")


# Helper functions for the new API methods
def get_lactate_threshold_data(api: Garmin) -> None:
    """Get lactate threshold data."""
    try:
        # Collect all API responses for grouped display
        api_responses = []

        # Get latest lactate threshold
        latest = api.get_lactate_threshold(latest=True)
        api_responses.append(("api.get_lactate_threshold(latest=True)", latest))

        # Get historical lactate threshold for past four weeks
        four_weeks_ago = config.today - datetime.timedelta(days=28)
        historical = api.get_lactate_threshold(
            latest=False,
            start_date=four_weeks_ago.isoformat(),
            end_date=config.today.isoformat(),
            aggregation="daily",
        )
        api_responses.append(
            (
                f"api.get_lactate_threshold(latest=False, start_date='{four_weeks_ago.isoformat()}', end_date='{config.today.isoformat()}', aggregation='daily')",
                historical,
            )
        )

        # Display all responses as a group
        call_and_display(
            group_name="Lactate Threshold Data", api_responses=api_responses
        )

    except Exception as e:
        print(f"❌ Error getting lactate threshold data: {e}")


def get_activity_splits_data(api: Garmin) -> None:
    """Get activity splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_splits,
                activity_id,
                method_name="get_activity_splits",
                api_call_desc=f"api.get_activity_splits({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity splits: {e}")


def get_activity_typed_splits_data(api: Garmin) -> None:
    """Get activity typed splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_typed_splits,
                activity_id,
                method_name="get_activity_typed_splits",
                api_call_desc=f"api.get_activity_typed_splits({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity typed splits: {e}")


def get_activity_split_summaries_data(api: Garmin) -> None:
    """Get activity split summaries for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_split_summaries,
                activity_id,
                method_name="get_activity_split_summaries",
                api_call_desc=f"api.get_activity_split_summaries({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity split summaries: {e}")


def get_activity_weather_data(api: Garmin) -> None:
    """Get activity weather data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_weather,
                activity_id,
                method_name="get_activity_weather",
                api_call_desc=f"api.get_activity_weather({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity weather: {e}")


def get_activity_hr_timezones_data(api: Garmin) -> None:
    """Get activity heart rate timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_hr_in_timezones,
                activity_id,
                method_name="get_activity_hr_in_timezones",
                api_call_desc=f"api.get_activity_hr_in_timezones({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity HR timezones: {e}")


def get_activity_power_timezones_data(api: Garmin) -> None:
    """Get activity power timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_power_in_timezones,
                activity_id,
                method_name="get_activity_power_in_timezones",
                api_call_desc=f"api.get_activity_power_in_timezones({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity power timezones: {e}")


def get_cycling_ftp_data(api: Garmin) -> None:
    """Get cycling Functional Threshold Power (FTP) information."""
    call_and_display(
        api.get_cycling_ftp,
        method_name="get_cycling_ftp",
        api_call_desc="api.get_cycling_ftp()",
    )


def get_activity_details_data(api: Garmin) -> None:
    """Get detailed activity information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_details,
                activity_id,
                method_name="get_activity_details",
                api_call_desc=f"api.get_activity_details({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity details: {e}")


def get_activity_gear_data(api: Garmin) -> None:
    """Get activity gear information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_gear,
                activity_id,
                method_name="get_activity_gear",
                api_call_desc=f"api.get_activity_gear({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity gear: {e}")


# def get_single_activity_data(api: Garmin) -> None:
#     """Get single activity data for the last activity."""
#     try:
#         activities = api.get_activities(0, 1)
#         if activities:
#             activity_id = activities[0]["activityId"]
#             call_and_display(
#                 api.get_activity,
#                 activity_id,
#                 method_name="get_activity",
#                 api_call_desc=f"api.get_activity({activity_id})",
#             )
#         else:
#             print("ℹ️ No activities found")
#     except Exception as e:
#         print(f"❌ Error getting single activity: {e}")


def get_activity_exercise_sets_data(api: Garmin) -> None:
    """Get exercise sets for strength training activities."""
    try:
        activities = api.get_activities(
            0, 20
        )  # Get more activities to find a strength training one
        strength_activity = None

        # Find strength training activities
        for activity in activities:
            activity_type = activity.get("activityType", {})
            type_key = activity_type.get("typeKey", "")
            if "strength" in type_key.lower() or "training" in type_key.lower():
                strength_activity = activity
                break

        if strength_activity:
            activity_id = strength_activity["activityId"]
            call_and_display(
                api.get_activity_exercise_sets,
                activity_id,
                method_name="get_activity_exercise_sets",
                api_call_desc=f"api.get_activity_exercise_sets({activity_id})",
            )
        else:
            # Return empty JSON response
            print("ℹ️ No strength training activities found")
    except Exception:
        print("ℹ️ No activity exercise sets available")


def get_training_plan_by_id_data(api: Garmin) -> None:
    """Get training plan details by ID (routes FBT_ADAPTIVE plans to the adaptive endpoint)."""
    resp = api.get_training_plans() or {}
    training_plans = resp.get("trainingPlanList") or []

    if not training_plans:
        print("ℹ️ No training plans found in your list")
        prompt_text = "Enter training plan ID: "
    else:
        prompt_text = "Enter training plan ID (press Enter for most recent): "

    user_input = input(prompt_text).strip()
    selected = None
    if user_input:
        try:
            wanted_id = int(user_input)
            selected = next(
                (
                    p
                    for p in training_plans
                    if int(p.get("trainingPlanId", 0)) == wanted_id
                ),
                None,
            )
            if not selected:
                print(
                    f"ℹ️ Plan ID {wanted_id} not found in your plans; attempting fetch anyway"
                )
                plan_id = wanted_id
                plan_name = f"Plan {wanted_id}"
                plan_category = None
            else:
                plan_id = int(selected["trainingPlanId"])
                plan_name = selected.get("name", str(plan_id))
                plan_category = selected.get("trainingPlanCategory")
        except ValueError:
            print("❌ Invalid plan ID")
            return
    else:
        if not training_plans:
            print("❌ No training plans available and no ID provided")
            return
        selected = training_plans[-1]
        plan_id = int(selected["trainingPlanId"])
        plan_name = selected.get("name", str(plan_id))
        plan_category = selected.get("trainingPlanCategory")

    if plan_category == "FBT_ADAPTIVE":
        call_and_display(
            api.get_adaptive_training_plan_by_id,
            plan_id,
            method_name="get_adaptive_training_plan_by_id",
            api_call_desc=f"api.get_adaptive_training_plan_by_id({plan_id}) - {plan_name}",
        )
    else:
        call_and_display(
            api.get_training_plan_by_id,
            plan_id,
            method_name="get_training_plan_by_id",
            api_call_desc=f"api.get_training_plan_by_id({plan_id}) - {plan_name}",
        )


def get_workout_by_id_data(api: Garmin) -> None:
    """Get workout by ID for the last workout."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]
            call_and_display(
                api.get_workout_by_id,
                workout_id,
                method_name="get_workout_by_id",
                api_call_desc=f"api.get_workout_by_id({workout_id}) - {workout_name}",
            )
        else:
            print("ℹ️ No workouts found")
    except Exception as e:
        print(f"❌ Error getting workout by ID: {e}")


# def download_workout_data(api: Garmin) -> None:
#     """Download workout to .FIT file."""
#     try:
#         workouts = api.get_workouts()
#         if workouts:
#             workout_id = workouts[-1]["workoutId"]
#             workout_name = workouts[-1]["workoutName"]

#             print(f"📥 Downloading workout: {workout_name}")
#             workout_data = api.download_workout(workout_id)

#             if workout_data:
#                 output_file = config.export_dir / f"{workout_name}_{workout_id}.fit"
#                 with open(output_file, "wb") as f:
#                     f.write(workout_data)
#                 print(f"✅ Workout downloaded to: {output_file}")
#             else:
#                 print("❌ No workout data available")
#         else:
#             print("ℹ️ No workouts found")
#     except Exception as e:
#         print(f"❌ Error downloading workout: {e}")


# def upload_workout_data(api: Garmin) -> None:
#     """Upload workout from JSON file."""
#     try:
#         print(f"📤 Uploading workout from file: {config.workoutfile}")

#         # Check if file exists
#         if not os.path.exists(config.workoutfile):
#             print(f"❌ File not found: {config.workoutfile}")
#             print(
#                 "ℹ️ Please ensure the workout JSON file exists in the test_data directory"
#             )
#             return

#         # Load the workout JSON data
#         import json

#         with open(config.workoutfile, encoding="utf-8") as f:
#             workout_data = json.load(f)

#         # Get current timestamp in Garmin format
#         current_time = datetime.datetime.now()
#         garmin_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S.0")

#         # Remove IDs that shouldn't be included when uploading a new workout
#         fields_to_remove = ["workoutId", "ownerId", "updatedDate", "createdDate"]
#         for field in fields_to_remove:
#             if field in workout_data:
#                 del workout_data[field]

#         # Add current timestamps
#         workout_data["createdDate"] = garmin_timestamp
#         workout_data["updatedDate"] = garmin_timestamp

#         # Remove step IDs to ensure new ones are generated
#         def clean_step_ids(workout_segments):
#             """Recursively remove step IDs from workout structure."""
#             if isinstance(workout_segments, list):
#                 for segment in workout_segments:
#                     clean_step_ids(segment)
#             elif isinstance(workout_segments, dict):
#                 # Remove stepId if present
#                 if "stepId" in workout_segments:
#                     del workout_segments["stepId"]

#                 # Recursively clean nested structures
#                 if "workoutSteps" in workout_segments:
#                     clean_step_ids(workout_segments["workoutSteps"])

#                 # Handle any other nested lists or dicts
#                 for value in workout_segments.values():
#                     if isinstance(value, list | dict):
#                         clean_step_ids(value)

#         # Clean step IDs from workout segments
#         if "workoutSegments" in workout_data:
#             clean_step_ids(workout_data["workoutSegments"])

#         # Update workout name to indicate it's uploaded with current timestamp
#         original_name = workout_data.get("workoutName", "Workout")
#         workout_data["workoutName"] = (
#             f"Uploaded {original_name} - {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
#         )

#         print(f"📤 Uploading workout: {workout_data['workoutName']}")

#         # Upload the workout
#         result = api.upload_workout(workout_data)

#         if result:
#             print("✅ Workout uploaded successfully!")
#             call_and_display(
#                 lambda: result,  # Use a lambda to pass the result
#                 method_name="upload_workout",
#                 api_call_desc="api.upload_workout(workout_data)",
#             )
#         else:
#             print(f"❌ Failed to upload workout from {config.workoutfile}")

#     except FileNotFoundError:
#         print(f"❌ File not found: {config.workoutfile}")
#         print("ℹ️ Please ensure the workout JSON file exists in the test_data directory")
#     except json.JSONDecodeError as e:
#         print(f"❌ Invalid JSON format in {config.workoutfile}: {e}")
#         print("ℹ️ Please check the JSON file format")
#     except Exception as e:
#         print(f"❌ Error uploading workout: {e}")
#         # Check for common upload errors
#         error_str = str(e)
#         if "400" in error_str:
#             print("💡 The workout data may be invalid or malformed")
#         elif "401" in error_str:
#             print("💡 Authentication failed - please login again")
#         elif "403" in error_str:
#             print("💡 Permission denied - check account permissions")
#         elif "409" in error_str:
#             print("💡 Workout may already exist")
#         elif "422" in error_str:
#             print("💡 Workout data validation failed")


# def upload_running_workout_data(api: Garmin) -> None:
#     """Upload a typed running workout."""
#     try:
#         import sys
#         from pathlib import Path

#         # Add test_data to path for imports
#         test_data_path = Path(__file__).parent / "test_data"
#         if str(test_data_path) not in sys.path:
#             sys.path.insert(0, str(test_data_path))

#         from sample_running_workout import create_sample_running_workout

#         print("🏃 Creating and uploading running workout...")
#         workout = create_sample_running_workout()
#         print(f"📤 Uploading workout: {workout.workoutName}")

#         result = api.upload_running_workout(workout)

#         if result:
#             print("✅ Running workout uploaded successfully!")
#             call_and_display(
#                 lambda: result,
#                 method_name="upload_running_workout",
#                 api_call_desc="api.upload_running_workout(workout)",
#             )
#         else:
#             print("❌ Failed to upload running workout")
#     except ImportError as e:
#         print(f"❌ Error: {e}")
#         print(
#             "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
#         )
#     except Exception as e:
#         print(f"❌ Error uploading running workout: {e}")


# def upload_cycling_workout_data(api: Garmin) -> None:
#     """Upload a typed cycling workout."""
#     try:
#         import sys
#         from pathlib import Path

#         # Add test_data to path for imports
#         test_data_path = Path(__file__).parent / "test_data"
#         if str(test_data_path) not in sys.path:
#             sys.path.insert(0, str(test_data_path))

#         from sample_cycling_workout import create_sample_cycling_workout

#         print("🚴 Creating and uploading cycling workout...")
#         workout = create_sample_cycling_workout()
#         print(f"📤 Uploading workout: {workout.workoutName}")

#         result = api.upload_cycling_workout(workout)

#         if result:
#             print("✅ Cycling workout uploaded successfully!")
#             call_and_display(
#                 lambda: result,
#                 method_name="upload_cycling_workout",
#                 api_call_desc="api.upload_cycling_workout(workout)",
#             )
#         else:
#             print("❌ Failed to upload cycling workout")
#     except ImportError as e:
#         print(f"❌ Error: {e}")
#         print(
#             "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
#         )
#     except Exception as e:
#         print(f"❌ Error uploading cycling workout: {e}")


# def upload_swimming_workout_data(api: Garmin) -> None:
#     """Upload a typed swimming workout."""
#     try:
#         import sys
#         from pathlib import Path

#         # Add test_data to path for imports
#         test_data_path = Path(__file__).parent / "test_data"
#         if str(test_data_path) not in sys.path:
#             sys.path.insert(0, str(test_data_path))

#         from sample_swimming_workout import create_sample_swimming_workout

#         print("🏊 Creating and uploading swimming workout...")
#         workout = create_sample_swimming_workout()
#         print(f"📤 Uploading workout: {workout.workoutName}")

#         result = api.upload_swimming_workout(workout)

#         if result:
#             print("✅ Swimming workout uploaded successfully!")
#             call_and_display(
#                 lambda: result,
#                 method_name="upload_swimming_workout",
#                 api_call_desc="api.upload_swimming_workout(workout)",
#             )
#         else:
#             print("❌ Failed to upload swimming workout")
#     except ImportError as e:
#         print(f"❌ Error: {e}")
#         print(
#             "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
#         )
#     except Exception as e:
#         print(f"❌ Error uploading swimming workout: {e}")


# def upload_walking_workout_data(api: Garmin) -> None:
#     """Upload a typed walking workout."""
#     try:
#         import sys
#         from pathlib import Path

#         # Add test_data to path for imports
#         test_data_path = Path(__file__).parent / "test_data"
#         if str(test_data_path) not in sys.path:
#             sys.path.insert(0, str(test_data_path))

#         from sample_walking_workout import create_sample_walking_workout

#         print("🚶 Creating and uploading walking workout...")
#         workout = create_sample_walking_workout()
#         print(f"📤 Uploading workout: {workout.workoutName}")

#         result = api.upload_walking_workout(workout)

#         if result:
#             print("✅ Walking workout uploaded successfully!")
#             call_and_display(
#                 lambda: result,
#                 method_name="upload_walking_workout",
#                 api_call_desc="api.upload_walking_workout(workout)",
#             )
#         else:
#             print("❌ Failed to upload walking workout")
#     except ImportError as e:
#         print(f"❌ Error: {e}")
#         print(
#             "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
#         )
#     except Exception as e:
#         print(f"❌ Error uploading walking workout: {e}")


# def upload_hiking_workout_data(api: Garmin) -> None:
#     """Upload a typed hiking workout."""
#     try:
#         import sys
#         from pathlib import Path

#         # Add test_data to path for imports
#         test_data_path = Path(__file__).parent / "test_data"
#         if str(test_data_path) not in sys.path:
#             sys.path.insert(0, str(test_data_path))

#         from sample_hiking_workout import create_sample_hiking_workout

#         print("🥾 Creating and uploading hiking workout...")
#         workout = create_sample_hiking_workout()
#         print(f"📤 Uploading workout: {workout.workoutName}")

#         result = api.upload_hiking_workout(workout)

#         if result:
#             print("✅ Hiking workout uploaded successfully!")
#             call_and_display(
#                 lambda: result,
#                 method_name="upload_hiking_workout",
#                 api_call_desc="api.upload_hiking_workout(workout)",
#             )
#         else:
#             print("❌ Failed to upload hiking workout")
#     except ImportError as e:
#         print(f"❌ Error: {e}")
#         print(
#             "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
#         )
#     except Exception as e:
#         print(f"❌ Error uploading hiking workout: {e}")


def get_scheduled_workout_by_id_data(api: Garmin) -> None:
    """Get scheduled workout by ID."""
    try:
        scheduled_workout_id = input("Enter scheduled workout ID: ").strip()

        if not scheduled_workout_id:
            print("❌ Scheduled workout ID is required")
            return

        call_and_display(
            api.get_scheduled_workout_by_id,
            scheduled_workout_id,
            method_name="get_scheduled_workout_by_id",
            api_call_desc=f"api.get_scheduled_workout_by_id({scheduled_workout_id})",
        )
    except Exception as e:
        print(f"❌ Error getting scheduled workout by ID: {e}")


# def set_body_composition_data(api: Garmin) -> None:
#     """Set body composition data."""
#     try:
#         print(f"⚖️ Setting body composition data for {config.today.isoformat()}")
#         print("-" * 50)

#         # Get weight input from user
#         while True:
#             try:
#                 weight_str = input(
#                     "Enter weight in kg (30-300, default: 85.1): "
#                 ).strip()
#                 if not weight_str:
#                     weight = 85.1
#                     break
#                 weight = float(weight_str)
#                 if 30 <= weight <= 300:
#                     break
#                 print("❌ Weight must be between 30 and 300 kg")
#             except ValueError:
#                 print("❌ Please enter a valid number")

#         call_and_display(
#             api.set_body_composition,
#             timestamp=config.today.isoformat(),
#             weight=weight,
#             percent_fat=15.4,
#             percent_hydration=54.8,
#             bone_mass=2.9,
#             muscle_mass=55.2,
#             method_name="set_body_composition",
#             api_call_desc=f"api.set_body_composition({config.today.isoformat()}, weight={weight}, ...)",
#         )
#         print("✅ Body composition data set successfully!")
#     except Exception as e:
#         print(f"❌ Error setting body composition: {e}")


# def add_body_composition_data(api: Garmin) -> None:
#     """Add body composition data."""
#     try:
#         print(f"⚖️ Adding body composition data for {config.today.isoformat()}")
#         print("-" * 50)

#         # Get weight input from user
#         while True:
#             try:
#                 weight_str = input(
#                     "Enter weight in kg (30-300, default: 85.1): "
#                 ).strip()
#                 if not weight_str:
#                     weight = 85.1
#                     break
#                 weight = float(weight_str)
#                 if 30 <= weight <= 300:
#                     break
#                 print("❌ Weight must be between 30 and 300 kg")
#             except ValueError:
#                 print("❌ Please enter a valid number")

#         call_and_display(
#             api.add_body_composition,
#             config.today.isoformat(),
#             weight=weight,
#             percent_fat=15.4,
#             percent_hydration=54.8,
#             visceral_fat_mass=10.8,
#             bone_mass=2.9,
#             muscle_mass=55.2,
#             basal_met=1454.1,
#             active_met=None,
#             physique_rating=None,
#             metabolic_age=33.0,
#             visceral_fat_rating=None,
#             bmi=22.2,
#             method_name="add_body_composition",
#             api_call_desc=f"api.add_body_composition({config.today.isoformat()}, weight={weight}, ...)",
#         )
#         print("✅ Body composition data added successfully!")
#     except Exception as e:
#         print(f"❌ Error adding body composition: {e}")


# def delete_weigh_ins_data(api: Garmin) -> None:
#     """Delete all weigh-ins for today."""
#     try:
#         call_and_display(
#             api.delete_weigh_ins,
#             config.today.isoformat(),
#             delete_all=True,
#             method_name="delete_weigh_ins",
#             api_call_desc=f"api.delete_weigh_ins({config.today.isoformat()}, delete_all=True)",
#         )
#         print("✅ Weigh-ins deleted successfully!")
#     except Exception as e:
#         print(f"❌ Error deleting weigh-ins: {e}")


# def delete_weigh_in_data(api: Garmin) -> None:
#     """Delete a specific weigh-in."""
#     try:
#         all_weigh_ins = []

#         # Find weigh-ins
#         print(f"🔍 Checking daily weigh-ins for today ({config.today.isoformat()})...")
#         try:
#             daily_weigh_ins = api.get_daily_weigh_ins(config.today.isoformat())

#             if daily_weigh_ins and "dateWeightList" in daily_weigh_ins:
#                 weight_list = daily_weigh_ins["dateWeightList"]
#                 for weigh_in in weight_list:
#                     if isinstance(weigh_in, dict):
#                         all_weigh_ins.append(weigh_in)
#                 print(f"📊 Found {len(all_weigh_ins)} weigh-in(s) for today")
#             else:
#                 print("📊 No weigh-in data found in response")
#         except Exception as e:
#             print(f"⚠️ Could not fetch daily weigh-ins: {e}")

#         if not all_weigh_ins:
#             print("ℹ️ No weigh-ins found for today")
#             print("💡 You can add a test weigh-in using menu option [4]")
#             return

#         print(f"\n⚖️ Found {len(all_weigh_ins)} weigh-in(s) available for deletion:")
#         print("-" * 70)

#         # Display weigh-ins for user selection
#         for i, weigh_in in enumerate(all_weigh_ins):
#             # Extract weight data - Garmin API uses different field names
#             weight = weigh_in.get("weight")
#             if weight is None:
#                 weight = weigh_in.get("weightValue", "Unknown")

#             # Convert weight from grams to kg if it's a number
#             if isinstance(weight, int | float) and weight > 1000:
#                 weight = weight / 1000  # Convert from grams to kg
#                 weight = round(weight, 1)  # Round to 1 decimal place

#             unit = weigh_in.get("unitKey", "kg")
#             date = weigh_in.get("calendarDate", config.today.isoformat())

#             # Try different timestamp fields
#             timestamp = (
#                 weigh_in.get("timestampGMT")
#                 or weigh_in.get("timestamp")
#                 or weigh_in.get("date")
#             )

#             # Format timestamp for display
#             if timestamp:
#                 try:
#                     import datetime as dt

#                     if isinstance(timestamp, str):
#                         # Handle ISO format strings
#                         datetime_obj = dt.datetime.fromisoformat(
#                             timestamp.replace("Z", "+00:00")
#                         )
#                     else:
#                         # Handle millisecond timestamps
#                         datetime_obj = dt.datetime.fromtimestamp(timestamp / 1000)
#                     time_str = datetime_obj.strftime("%H:%M:%S")
#                 except Exception:
#                     time_str = "Unknown time"
#             else:
#                 time_str = "Unknown time"

#             print(f"  [{i}] {weight} {unit} on {date} at {time_str}")

#         print()
#         try:
#             selection = input(
#                 "Enter the index of the weigh-in to delete (or 'q' to cancel): "
#             ).strip()

#             if selection.lower() == "q":
#                 print("❌ Delete cancelled")
#                 return

#             weigh_in_index = int(selection)
#             if 0 <= weigh_in_index < len(all_weigh_ins):
#                 selected_weigh_in = all_weigh_ins[weigh_in_index]

#                 # Get the weigh-in ID (Garmin uses 'samplePk' as the primary key)
#                 weigh_in_id = (
#                     selected_weigh_in.get("samplePk")
#                     or selected_weigh_in.get("id")
#                     or selected_weigh_in.get("weightPk")
#                     or selected_weigh_in.get("pk")
#                     or selected_weigh_in.get("weightId")
#                     or selected_weigh_in.get("uuid")
#                 )

#                 if weigh_in_id:
#                     weight = selected_weigh_in.get("weight", "Unknown")

#                     # Convert weight from grams to kg if it's a number
#                     if isinstance(weight, int | float) and weight > 1000:
#                         weight = weight / 1000  # Convert from grams to kg
#                         weight = round(weight, 1)  # Round to 1 decimal place

#                     unit = selected_weigh_in.get("unitKey", "kg")
#                     date = selected_weigh_in.get(
#                         "calendarDate", config.today.isoformat()
#                     )

#                     # Confirm deletion
#                     confirm = input(
#                         f"Delete weigh-in {weight} {unit} from {date}? (yes/no): "
#                     ).lower()
#                     if confirm == "yes":
#                         call_and_display(
#                             api.delete_weigh_in,
#                             weigh_in_id,
#                             config.today.isoformat(),
#                             method_name="delete_weigh_in",
#                             api_call_desc=f"api.delete_weigh_in({weigh_in_id}, {config.today.isoformat()})",
#                         )
#                         print("✅ Weigh-in deleted successfully!")
#                     else:
#                         print("❌ Delete cancelled")
#                 else:
#                     print("❌ No weigh-in ID found for selected entry")
#             else:
#                 print("❌ Invalid selection")

#         except ValueError:
#             print("❌ Invalid input - please enter a number")

#     except Exception as e:
#         print(f"❌ Error deleting weigh-in: {e}")


def get_device_settings_data(api: Garmin) -> None:
    """Get device settings for all devices."""
    try:
        devices = api.get_devices()
        if devices:
            for device in devices:
                device_id = device["deviceId"]
                device_name = device.get("displayName", f"Device {device_id}")
                try:
                    call_and_display(
                        api.get_device_settings,
                        device_id,
                        method_name="get_device_settings",
                        api_call_desc=f"api.get_device_settings({device_id}) - {device_name}",
                    )
                except Exception as e:
                    print(f"❌ Error getting settings for device {device_name}: {e}")
        else:
            print("ℹ️ No devices found")
    except Exception as e:
        print(f"❌ Error getting device settings: {e}")


def get_gear_data(api: Garmin) -> None:
    """Get user gear list."""
    print("🔄 Fetching user gear list...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number from the first call
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="User Gear List", api_responses=api_responses)


def get_gear_defaults_data(api: Garmin) -> None:
    """Get gear defaults."""
    print("🔄 Fetching gear defaults...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number from the first call
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            api_responses.append(
                safe_call_for_group(
                    api.get_gear_defaults,
                    user_profile_number,
                    method_name="get_gear_defaults",
                    api_call_desc=f"api.get_gear_defaults({user_profile_number})",
                )
            )
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="Gear Defaults", api_responses=api_responses)


def get_gear_stats_data(api: Garmin) -> None:
    """Get gear statistics."""
    print("🔄 Fetching comprehensive gear statistics...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number and gear list
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            # Get gear list
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )

            # Get gear data to extract UUIDs for stats
            gear_success, gear_data, _ = safe_api_call(
                api.get_gear, user_profile_number, method_name="get_gear"
            )

            if gear_success and gear_data:
                # Get stats for each gear item (limit to first 3)
                for gear_item in gear_data[:3]:
                    gear_uuid = gear_item.get("uuid")
                    gear_name = gear_item.get("displayName", "Unknown")
                    if gear_uuid:
                        api_responses.append(
                            safe_call_for_group(
                                api.get_gear_stats,
                                gear_uuid,
                                method_name="get_gear_stats",
                                api_call_desc=f"api.get_gear_stats('{gear_uuid}') - {gear_name}",
                            )
                        )
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="Gear Statistics", api_responses=api_responses)


def get_gear_activities_data(api: Garmin) -> None:
    """Get gear activities."""
    print("🔄 Fetching gear activities...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number and gear list
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            # Get gear list
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )

            # Get gear data to extract UUID for activities
            gear_success, gear_data, _ = safe_api_call(
                api.get_gear, user_profile_number, method_name="get_gear"
            )

            if gear_success and gear_data and len(gear_data) > 0:
                # Get activities for the first gear item
                gear_uuid = gear_data[0].get("uuid")
                gear_name = gear_data[0].get("displayName", "Unknown")

                if gear_uuid:
                    api_responses.append(
                        safe_call_for_group(
                            api.get_gear_activities,
                            gear_uuid,
                            method_name="get_gear_activities",
                            api_call_desc=f"api.get_gear_activities('{gear_uuid}') - {gear_name}",
                        )
                    )
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="Gear Activities", api_responses=api_responses)


def set_gear_default_data(api: Garmin) -> None:
    """Set gear default."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear = api.get_gear(user_profile_number)
            if gear:
                gear_uuid = gear[0].get("uuid")
                gear_name = gear[0].get("displayName", "Unknown")
                if gear_uuid:
                    # Set as default for running (activity type ID 1)
                    # Correct method signature: set_gear_default(activityType, gearUUID, defaultGear=True)
                    activity_type = 1  # Running
                    call_and_display(
                        api.set_gear_default,
                        activity_type,
                        gear_uuid,
                        True,
                        method_name="set_gear_default",
                        api_call_desc=f"api.set_gear_default({activity_type}, '{gear_uuid}', True) - {gear_name} for running",
                    )
                    print("✅ Gear default set successfully!")
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error setting gear default: {e}")


# def add_and_remove_gear_to_activity(api: Garmin) -> None:
#     """Add gear to most recent activity, then remove."""
#     try:
#         device_last_used = api.get_device_last_used()
#         user_profile_number = device_last_used.get("userProfileNumber")
#         if user_profile_number:
#             gear_list = api.get_gear(user_profile_number)
#             if gear_list:
#                 activities = api.get_activities(0, 1)
#                 if activities:
#                     activity_id = activities[0].get("activityId")
#                     activity_name = activities[0].get("activityName")
#                     for gear in gear_list:
#                         if gear["gearStatusName"] == "active":
#                             break
#                     gear_uuid = gear.get("uuid")
#                     gear_name = gear.get("displayName", "Unknown")
#                     if gear_uuid:
#                         # Add gear to an activity
#                         # Correct method signature: add_gear_to_activity(gearUUID, activity_id)
#                         call_and_display(
#                             api.add_gear_to_activity,
#                             gear_uuid,
#                             activity_id,
#                             method_name="add_gear_to_activity",
#                             api_call_desc=f"api.add_gear_to_activity('{gear_uuid}', {activity_id}) - Add {gear_name} to {activity_name}",
#                         )
#                         print("✅ Gear added successfully!")

#                         # Wait for user to check gear, then continue
#                         input(
#                             "Go check Garmin to confirm, then press Enter to continue"
#                         )

#                         # Remove gear from an activity
#                         # Correct method signature: remove_gear_from_activity(gearUUID, activity_id)
#                         call_and_display(
#                             api.remove_gear_from_activity,
#                             gear_uuid,
#                             activity_id,
#                             method_name="remove_gear_from_activity",
#                             api_call_desc=f"api.remove_gear_from_activity('{gear_uuid}', {activity_id}) - Remove {gear_name} from {activity_name}",
#                         )
#                         print("✅ Gear removed successfully!")
#                     else:
#                         print("❌ No activities found")
#                 else:
#                     print("❌ No gear UUID found")
#             else:
#                 print("ℹ️ No gear found")
#         else:
#             print("❌ Could not get user profile number")
#     except Exception as e:
#         print(f"❌ Error adding gear: {e}")


def set_activity_name_data(api: Garmin) -> None:
    """Set activity name."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            print(f"Current name of fetched activity: {activities[0]['activityName']}")
            new_name = input("Enter new activity name: (or 'q' to cancel): ").strip()

            if new_name.lower() == "q":
                print("❌ Rename cancelled")
                return

            if new_name:
                call_and_display(
                    api.set_activity_name,
                    activity_id,
                    new_name,
                    method_name="set_activity_name",
                    api_call_desc=f"api.set_activity_name({activity_id}, '{new_name}')",
                )
                print("✅ Activity name updated!")
            else:
                print("❌ No name provided")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error setting activity name: {e}")


# def set_activity_type_data(api: Garmin) -> None:
#     """Set activity type."""
#     try:
#         activities = api.get_activities(0, 1)
#         if activities:
#             activity_id = activities[0]["activityId"]
#             activity_types = api.get_activity_types()

#             # Show available types
#             print("\nAvailable activity types: (limit=10)")
#             for i, activity_type in enumerate(activity_types[:10]):  # Show first 10
#                 print(
#                     f"{i}: {activity_type.get('typeKey', 'Unknown')} - {activity_type.get('display', 'No description')}"
#                 )

#             try:
#                 print(
#                     f"Current type of fetched activity '{activities[0]['activityName']}': {activities[0]['activityType']['typeKey']}"
#                 )
#                 type_index = input(
#                     "Enter activity type index: (or 'q' to cancel): "
#                 ).strip()

#                 if type_index.lower() == "q":
#                     print("❌ Type change cancelled")
#                     return

#                 type_index = int(type_index)
#                 if 0 <= type_index < len(activity_types):
#                     selected_type = activity_types[type_index]
#                     type_id = selected_type["typeId"]
#                     type_key = selected_type["typeKey"]
#                     parent_type_id = selected_type.get(
#                         "parentTypeId", selected_type["typeId"]
#                     )

#                     call_and_display(
#                         api.set_activity_type,
#                         activity_id,
#                         type_id,
#                         type_key,
#                         parent_type_id,
#                         method_name="set_activity_type",
#                         api_call_desc=f"api.set_activity_type({activity_id}, {type_id}, '{type_key}', {parent_type_id})",
#                     )
#                     print("✅ Activity type updated!")
#                 else:
#                     print("❌ Invalid index")
#             except ValueError:
#                 print("❌ Invalid input")
#         else:
#             print("❌ No activities found")
#     except Exception as e:
#         print(f"❌ Error setting activity type: {e}")


# def create_manual_activity_data(api: Garmin) -> None:
#     """Create manual activity."""
#     try:
#         print("Creating manual activity...")
#         print("Enter activity details (press Enter for defaults):")

#         activity_name = (
#             input("Activity name [Manual Activity]: ").strip() or "Manual Activity"
#         )
#         type_key = input("Activity type key [running]: ").strip() or "running"
#         duration_min = input("Duration in minutes [60]: ").strip() or "60"
#         distance_km = input("Distance in kilometers [5]: ").strip() or "5"
#         timezone = input("Timezone [UTC]: ").strip() or "UTC"

#         try:
#             duration_min = float(duration_min)
#             distance_km = float(distance_km)

#             # Use the current time as start time
#             import datetime

#             start_datetime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.00")

#             call_and_display(
#                 api.create_manual_activity,
#                 start_datetime=start_datetime,
#                 time_zone=timezone,
#                 type_key=type_key,
#                 distance_km=distance_km,
#                 duration_min=duration_min,
#                 activity_name=activity_name,
#                 method_name="create_manual_activity",
#                 api_call_desc=f"api.create_manual_activity(start_datetime='{start_datetime}', time_zone='{timezone}', type_key='{type_key}', distance_km={distance_km}, duration_min={duration_min}, activity_name='{activity_name}')",
#             )
#             print("✅ Manual activity created!")
#         except ValueError:
#             print("❌ Invalid numeric input")
#     except Exception as e:
#         print(f"❌ Error creating manual activity: {e}")


# def delete_activity_data(api: Garmin) -> None:
#     """Delete activity."""
#     try:
#         activities = api.get_activities(0, 5)
#         if activities:
#             print("\nRecent activities:")
#             for i, activity in enumerate(activities):
#                 activity_name = activity.get("activityName", "Unnamed")
#                 activity_id = activity.get("activityId")
#                 start_time = activity.get("startTimeLocal", "Unknown time")
#                 print(f"{i}: {activity_name} ({activity_id}) - {start_time}")

#             try:
#                 activity_index = input(
#                     "Enter activity index to delete: (or 'q' to cancel): "
#                 ).strip()

#                 if activity_index.lower() == "q":
#                     print("❌ Delete cancelled")
#                     return
#                 activity_index = int(activity_index)
#                 if 0 <= activity_index < len(activities):
#                     activity_id = activities[activity_index]["activityId"]
#                     activity_name = activities[activity_index].get(
#                         "activityName", "Unnamed"
#                     )

#                     confirm = input(f"Delete '{activity_name}'? (yes/no): ").lower()
#                     if confirm == "yes":
#                         call_and_display(
#                             api.delete_activity,
#                             activity_id,
#                             method_name="delete_activity",
#                             api_call_desc=f"api.delete_activity({activity_id})",
#                         )
#                         print("✅ Activity deleted!")
#                     else:
#                         print("❌ Delete cancelled")
#                 else:
#                     print("❌ Invalid index")
#             except ValueError:
#                 print("❌ Invalid input")
#         else:
#             print("❌ No activities found")
#     except Exception as e:
#         print(f"❌ Error deleting activity: {e}")


# def delete_blood_pressure_data(api: Garmin) -> None:
#     """Delete blood pressure entry."""
#     try:
#         # Get recent blood pressure entries
#         bp_data = api.get_blood_pressure(
#             config.week_start.isoformat(), config.today.isoformat()
#         )
#         entry_list = []

#         # Parse the actual blood pressure data structure
#         if bp_data and bp_data.get("measurementSummaries"):
#             for summary in bp_data["measurementSummaries"]:
#                 if summary.get("measurements"):
#                     for measurement in summary["measurements"]:
#                         # Use 'version' as the identifier (this is what Garmin uses)
#                         entry_id = measurement.get("version")
#                         systolic = measurement.get("systolic")
#                         diastolic = measurement.get("diastolic")
#                         pulse = measurement.get("pulse")
#                         timestamp = measurement.get("measurementTimestampLocal")
#                         notes = measurement.get("notes", "")

#                         # Extract date for deletion API (format: YYYY-MM-DD)
#                         measurement_date = None
#                         if timestamp:
#                             try:
#                                 measurement_date = timestamp.split("T")[
#                                     0
#                                 ]  # Get just the date part
#                             except Exception:
#                                 measurement_date = summary.get(
#                                     "startDate"
#                                 )  # Fallback to summary date
#                         else:
#                             measurement_date = summary.get(
#                                 "startDate"
#                             )  # Fallback to summary date

#                         if entry_id and systolic and diastolic and measurement_date:
#                             # Format display text with more details
#                             display_parts = [f"{systolic}/{diastolic}"]
#                             if pulse:
#                                 display_parts.append(f"pulse {pulse}")
#                             if timestamp:
#                                 display_parts.append(f"at {timestamp}")
#                             if notes:
#                                 display_parts.append(f"({notes})")

#                             display_text = " ".join(display_parts)
#                             # Store both entry_id and measurement_date for deletion
#                             entry_list.append(
#                                 (entry_id, display_text, measurement_date)
#                             )

#         if entry_list:
#             print(f"\n📊 Found {len(entry_list)} blood pressure entries:")
#             print("-" * 70)
#             for i, (entry_id, display_text, _measurement_date) in enumerate(entry_list):
#                 print(f"  [{i}] {display_text} (ID: {entry_id})")

#             try:
#                 entry_index = input(
#                     "\nEnter entry index to delete: (or 'q' to cancel): "
#                 ).strip()

#                 if entry_index.lower() == "q":
#                     print("❌ Entry deletion cancelled")
#                     return

#                 entry_index = int(entry_index)
#                 if 0 <= entry_index < len(entry_list):
#                     entry_id, display_text, measurement_date = entry_list[entry_index]
#                     confirm = input(
#                         f"Delete entry '{display_text}'? (yes/no): "
#                     ).lower()
#                     if confirm == "yes":
#                         call_and_display(
#                             api.delete_blood_pressure,
#                             entry_id,
#                             measurement_date,
#                             method_name="delete_blood_pressure",
#                             api_call_desc=f"api.delete_blood_pressure('{entry_id}', '{measurement_date}')",
#                         )
#                         print("✅ Blood pressure entry deleted!")
#                     else:
#                         print("❌ Delete cancelled")
#                 else:
#                     print("❌ Invalid index")
#             except ValueError:
#                 print("❌ Invalid input")
#         else:
#             print("❌ No blood pressure entries found for past week")
#             print("💡 You can add a test measurement using menu option [3]")

#     except Exception as e:
#         print(f"❌ Error deleting blood pressure: {e}")


# def query_garmin_graphql_data(api: Garmin) -> None:
#     """Execute GraphQL query with a menu of available queries."""
#     try:
#         print("Available GraphQL queries:")
#         print("  [1] Activities (recent activities with details)")
#         print("  [2] Health Snapshot (comprehensive health data)")
#         print("  [3] Weight Data (weight measurements)")
#         print("  [4] Blood Pressure (blood pressure data)")
#         print("  [5] Sleep Summaries (sleep analysis)")
#         print("  [6] Heart Rate Variability (HRV data)")
#         print("  [7] User Daily Summary (comprehensive daily stats)")
#         print("  [8] Training Readiness (training readiness metrics)")
#         print("  [9] Training Status (training status data)")
#         print("  [10] Activity Stats (aggregated activity statistics)")
#         print("  [11] VO2 Max (VO2 max data)")
#         print("  [12] Endurance Score (endurance scoring)")
#         print("  [13] User Goals (current goals)")
#         print("  [14] Stress Data (epoch chart with stress)")
#         print("  [15] Badge Challenges (available challenges)")
#         print("  [16] Adhoc Challenges (adhoc challenges)")
#         print("  [c] Custom query")

#         choice = input("\nEnter choice (1-16, c): ").strip()

#         # Use today's date and date range for queries that need them
#         today = config.today.isoformat()
#         week_start = config.week_start.isoformat()
#         start_datetime = f"{today}T00:00:00.00"
#         end_datetime = f"{today}T23:59:59.999"

#         if choice == "1":
#             query = f'query{{activitiesScalar(displayName:"{api.display_name}", startTimestampLocal:"{start_datetime}", endTimestampLocal:"{end_datetime}", limit:10)}}'
#         elif choice == "2":
#             query = f'query{{healthSnapshotScalar(startDate:"{week_start}", endDate:"{today}")}}'
#         elif choice == "3":
#             query = (
#                 f'query{{weightScalar(startDate:"{week_start}", endDate:"{today}")}}'
#             )
#         elif choice == "4":
#             query = f'query{{bloodPressureScalar(startDate:"{week_start}", endDate:"{today}")}}'
#         elif choice == "5":
#             query = f'query{{sleepSummariesScalar(startDate:"{week_start}", endDate:"{today}")}}'
#         elif choice == "6":
#             query = f'query{{heartRateVariabilityScalar(startDate:"{week_start}", endDate:"{today}")}}'
#         elif choice == "7":
#             query = f'query{{userDailySummaryV2Scalar(startDate:"{week_start}", endDate:"{today}")}}'
#         elif choice == "8":
#             query = f'query{{trainingReadinessRangeScalar(startDate:"{week_start}", endDate:"{today}")}}'
#         elif choice == "9":
#             query = f'query{{trainingStatusDailyScalar(calendarDate:"{today}")}}'
#         elif choice == "10":
#             query = f'query{{activityStatsScalar(aggregation:"daily", startDate:"{week_start}", endDate:"{today}", metrics:["duration", "distance"], groupByParentActivityType:true, standardizedUnits:true)}}'
#         elif choice == "11":
#             query = (
#                 f'query{{vo2MaxScalar(startDate:"{week_start}", endDate:"{today}")}}'
#             )
#         elif choice == "12":
#             query = f'query{{enduranceScoreScalar(startDate:"{week_start}", endDate:"{today}", aggregation:"weekly")}}'
#         elif choice == "13":
#             query = "query{userGoalsScalar}"
#         elif choice == "14":
#             query = f'query{{epochChartScalar(date:"{today}", include:["stress"])}}'
#         elif choice == "15":
#             query = "query{badgeChallengesScalar}"
#         elif choice == "16":
#             query = "query{adhocChallengesScalar}"
#         elif choice.lower() == "c":
#             print("\nEnter your custom GraphQL query:")
#             print("Example: query{userGoalsScalar}")
#             query = input("Query: ").strip()
#         else:
#             print("❌ Invalid choice")
#             return

#         if query:
#             # GraphQL API expects a dictionary with the query as a string value
#             graphql_payload = {"query": query}
#             call_and_display(
#                 api.query_garmin_graphql,
#                 graphql_payload,
#                 method_name="query_garmin_graphql",
#                 api_call_desc=f"api.query_garmin_graphql({graphql_payload})",
#             )
#         else:
#             print("❌ No query provided")
#     except Exception as e:
#         print(f"❌ Error executing GraphQL query: {e}")


# def get_virtual_challenges_data(api: Garmin) -> None:
#     """Get virtual challenges data with centralized error handling."""
#     print("🏆 Attempting to get virtual challenges data...")

#     # Try in-progress virtual challenges - this endpoint often returns 400 for accounts
#     # that don't have virtual challenges enabled, so handle it quietly
#     try:
#         challenges = api.get_inprogress_virtual_challenges(
#             config.start, config.default_limit
#         )
#         if challenges:
#             print("✅ Virtual challenges data retrieved successfully")
#             call_and_display(
#                 api.get_inprogress_virtual_challenges,
#                 config.start,
#                 config.default_limit,
#                 method_name="get_inprogress_virtual_challenges",
#                 api_call_desc=f"api.get_inprogress_virtual_challenges({config.start}, {config.default_limit})",
#             )
#             return
#         print("ℹ️ No in-progress virtual challenges found")
#         return
#     except GarminConnectConnectionError as e:
#         # Handle the common 400 error case quietly - this is expected for many accounts
#         error_str = str(e)
#         if "400" in error_str and (
#             "Bad Request" in error_str or "API client error" in error_str
#         ):
#             print("ℹ️ Virtual challenges are not available for your account")
#         else:
#             # For unexpected connection errors, show them
#             print(f"⚠️ Connection error accessing virtual challenges: {error_str}")
#     except Exception as e:
#         print(f"⚠️ Unexpected error accessing virtual challenges: {e}")

#     # Since virtual challenges failed or returned no data, suggest alternatives
#     print("💡 You can try other challenge-related endpoints instead:")
#     print("   - Badge challenges (menu option 7-8)")
#     print("   - Available badge challenges (menu option 7-4)")
#     print("   - Adhoc challenges (menu option 7-3)")


# def add_hydration_data_entry(api: Garmin) -> None:
#     """Add hydration data entry."""
#     try:
#         import datetime

#         value_in_ml = 240
#         raw_date = config.today
#         cdate = str(raw_date)
#         raw_ts = datetime.datetime.now()
#         timestamp = datetime.datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

#         call_and_display(
#             api.add_hydration_data,
#             value_in_ml=value_in_ml,
#             cdate=cdate,
#             timestamp=timestamp,
#             method_name="add_hydration_data",
#             api_call_desc=f"api.add_hydration_data(value_in_ml={value_in_ml}, cdate='{cdate}', timestamp='{timestamp}')",
#         )
#         print("✅ Hydration data added successfully!")
#     except Exception as e:
#         print(f"❌ Error adding hydration data: {e}")


# def set_blood_pressure_data(api: Garmin) -> None:
#     """Set blood pressure (and pulse) data."""
#     try:
#         print("🩸 Adding blood pressure (and pulse) measurement")
#         print("Enter blood pressure values (press Enter for defaults):")

#         # Get systolic pressure
#         systolic_input = input("Systolic pressure [120]: ").strip()
#         systolic = int(systolic_input) if systolic_input else 120

#         # Get diastolic pressure
#         diastolic_input = input("Diastolic pressure [80]: ").strip()
#         diastolic = int(diastolic_input) if diastolic_input else 80

#         # Get pulse
#         pulse_input = input("Pulse rate [60]: ").strip()
#         pulse = int(pulse_input) if pulse_input else 60

#         # Get notes (optional)
#         notes = input("Notes (optional): ").strip() or "Added via demo.py"

#         # Validate ranges
#         if not (50 <= systolic <= 300):
#             print("❌ Invalid systolic pressure (should be between 50-300)")
#             return
#         if not (30 <= diastolic <= 200):
#             print("❌ Invalid diastolic pressure (should be between 30-200)")
#             return
#         if not (30 <= pulse <= 250):
#             print("❌ Invalid pulse rate (should be between 30-250)")
#             return

#         print(f"📊 Recording: {systolic}/{diastolic} mmHg, pulse {pulse} bpm")

#         call_and_display(
#             api.set_blood_pressure,
#             systolic,
#             diastolic,
#             pulse,
#             notes=notes,
#             method_name="set_blood_pressure",
#             api_call_desc=f"api.set_blood_pressure({systolic}, {diastolic}, {pulse}, notes='{notes}')",
#         )
#         print("✅ Blood pressure data set successfully!")

#     except ValueError:
#         print("❌ Invalid input - please enter numeric values")
#     except Exception as e:
#         print(f"❌ Error setting blood pressure: {e}")


def track_gear_usage_data(api: Garmin) -> None:
    """Calculate total time of use of a piece of gear by going through all activities where said gear has been used."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear_list = api.get_gear(user_profile_number)
            # call_and_display(api.get_gear, user_profile_number, method_name="get_gear", api_call_desc=f"api.get_gear({user_profile_number})")
            if gear_list and isinstance(gear_list, list):
                first_gear = gear_list[0]
                gear_uuid = first_gear.get("uuid")
                gear_name = first_gear.get("displayName", "Unknown")
                print(f"Tracking usage for gear: {gear_name} (UUID: {gear_uuid})")
                activityList = api.get_gear_activities(gear_uuid)
                if len(activityList) == 0:
                    print("No activities found for the given gear uuid.")
                else:
                    print("Found " + str(len(activityList)) + " activities.")

                D = 0
                for a in activityList:
                    print(
                        "Activity: "
                        + a["startTimeLocal"]
                        + (" | " + a["activityName"] if a["activityName"] else "")
                    )
                    print(
                        "  Duration: "
                        + format_timedelta(datetime.timedelta(seconds=a["duration"]))
                    )
                    D += a["duration"]
                print("")
                print(
                    "Total Duration: " + format_timedelta(datetime.timedelta(seconds=D))
                )
                print("")
            else:
                print("No gear found for this user.")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear for track_gear_usage_data: {e}")

def call_and_display(
    api_method=None,
    *args,
    method_name: str | None = None,
    api_call_desc: str | None = None,
    group_name: str | None = None,
    api_responses: list | None = None,
    **kwargs,
):
    """Unified wrapper that calls API methods safely and displays results.
    Can handle both single API calls and grouped API responses.

    For single API calls:
        call_and_display(api.get_user_summary, "2024-01-01")

    For grouped responses:
        call_and_display(group_name="User Data", api_responses=[("api.get_user", data)])

    Args:
        api_method: The API method to call (for single calls)
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        api_call_desc: Description for display purposes (optional)
        group_name: Name for grouped display (when displaying multiple responses)
        api_responses: List of (api_call_desc, result) tuples for grouped display
        **kwargs: Keyword arguments for the API method

    Returns:
        For single calls: tuple: (success: bool, result: Any)
        For grouped calls: None

    """
    # Handle grouped display mode
    if group_name is not None and api_responses is not None:
        return _display_group(group_name, api_responses)

    # Handle single API call mode
    if api_method is None:
        raise ValueError(
            "Either api_method or (group_name + api_responses) must be provided"
        )

    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    if api_call_desc is None:
        # Try to construct a reasonable description
        args_str = ", ".join(str(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        api_call_desc = f"{method_name}({all_args})"

    success, result, error_msg = safe_api_call(
        api_method, *args, method_name=method_name, **kwargs
    )

    if success:
        _display_single(api_call_desc, result)
        return True, result
    # Display error in a consistent format
    _display_single(f"{api_call_desc} [ERROR]", {"error": error_msg})
    return False, None

def disconnect_api(api: Garmin):
    """Disconnect from Garmin Connect."""
    api.logout()
    print("✅ Disconnected from Garmin Connect")

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
            # "upload_activity": lambda: upload_activity_file(api),
            # "download_activities": lambda: download_activities_by_date(api),
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
            # "download_workout": lambda: download_workout_data(api),
            # "upload_workout": lambda: upload_workout_data(api),
            # "upload_running_workout": lambda: upload_running_workout_data(api),
            # "upload_cycling_workout": lambda: upload_cycling_workout_data(api),
            # "upload_swimming_workout": lambda: upload_swimming_workout_data(api),
            # "upload_walking_workout": lambda: upload_walking_workout_data(api),
            # "upload_hiking_workout": lambda: upload_hiking_workout_data(api),
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
            # "add_and_remove_gear_to_activity": lambda: add_and_remove_gear_to_activity(
            #     api
            # ),
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
            # "query_garmin_graphql": lambda: query_garmin_graphql_data(api),
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
    api = init_api(config.email, config.password)

    if not api:
        print("❌ Failed to initialize API. Exiting.")
        return
    
    data = []

    nb_activity_import = 2 # nombre max: 20

    get_single_activity_data(api, nb_activity_import, data)

    f = open("./data/data.txt", "w")
    f.write(str(data))
    f.close()

    print(execute_api_call(api, "get_lactate_threshold"))
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🚪 Exiting example. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")