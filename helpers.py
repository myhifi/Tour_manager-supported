from flask import redirect, render_template, session, request, flash, url_for
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            # return redirect("/login")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def get_empty_field(*field_names):
    """
    Checks if any of the specified form fields submitted via POST are empty.
    Takes a variable number of string field names as arguments.
    Returns the name of the first empty field found, or None if all fields are filled.
    """
    for field_name in field_names:
        field_value = request.form.get(field_name)
        # Check if the value is None (field not present) or an empty string after stripping whitespace
        if field_value is None or field_value.strip() == "":
            return field_name # Return the name of the first empty field found
    return None # Return None if all fields have values

# New decorator to restrict access based on user role
def role_required(*allowed_roles):
    """
    Decorate routes to require a specific role.
    Takes one or more allowed role strings as arguments (e.g., 'admin', 'employee').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First, ensure the user is logged in
            if session.get("user_id") is None:
                flash("You need to log in to access this page.")
                return redirect(url_for("login"))

            # Check if the user's roll is in the allowed roles list
            user_roll = session.get("user_roll")
            if user_roll not in allowed_roles:
                # Flash an error message and redirect
                flash("You do not have the necessary permissions to access this page.")
                # Redirect to a suitable page, e.g., the index page or a custom error page
                return redirect(url_for("index")) # Or url_for("permission_denied") if you create one

            # If logged in and role is allowed, proceed with the original function
            return f(*args, **kwargs)
        return decorated_function
    return decorator
