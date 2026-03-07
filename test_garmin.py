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
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🚪 Exiting example. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")