"""Views module for Nueva Ecija Travel Desktop Client."""

from desktop_client.views.welcome_view import WelcomeView
from desktop_client.views.login_view import LoginView
from desktop_client.views.signup_view import SignupView
from desktop_client.views.dashboard_view import DashboardView
from desktop_client.views.places_view import PlacesView
from desktop_client.views.suggested_wizard_view import SuggestedWizardView
from desktop_client.views.custom_builder_view import CustomBuilderView
from desktop_client.views.saved_trips_view import SavedTripsView
from desktop_client.views.trip_detail_view import TripDetailView
from desktop_client.views.profile_view import ProfileView

__all__ = [
    "WelcomeView",
    "LoginView",
    "SignupView",
    "DashboardView",
    "PlacesView",
    "SuggestedWizardView",
    "CustomBuilderView",
    "SavedTripsView",
    "TripDetailView",
    "ProfileView",
]
