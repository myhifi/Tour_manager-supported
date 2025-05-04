import os
from datetime import date, datetime, timedelta # Import date, datetime, and timedelta
from dateutil.parser import parse # Import parse for robust date/time parsing (install python-dateutil)

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Import the necessary helper functions
from helpers import login_required, get_empty_field, role_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///tour_manager.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
# Removed @login_required decorator to make this page accessible without login
def index():
    """Show the tour manager landing page and a list of public tours."""
    # Check if the user is logged in by trying to get user_id from session
    user_id = session.get("user_id")
    user_roll = session.get("user_roll") # Get user roll if logged in

    # Fetch a list of tours to display on the landing page for everyone.
    # This might be a selection of upcoming tours that are scheduled or confirmed
    # and not yet full.
    public_tours = db.execute("""
        SELECT * FROM tours
        WHERE date >= ? AND status IN ('Scheduled', 'Confirmed')
        AND current_bookings < max_capacity
        ORDER BY date, time
        LIMIT 5 -- Limit the number of tours displayed on the landing page
    """, date.today())

    # Process the fetched data (optional).
    # Format dates and times for display.
    for tour in public_tours:
        tour['formatted_date'] = tour['date'] # Adjust formatting as needed
        tour['formatted_time'] = tour['time'] # Adjust formatting as needed


    # Pass user_id, user_roll, and the list of public tours to the template
    return render_template("index.html", user_id=user_id, user_roll=user_roll, public_tours=public_tours)


@app.route("/history")
@login_required
def history():
    """Show history of user's bookings."""
    # Get the logged-in user's ID from the session
    user_id = session["user_id"]

    # Fetch all bookings for this user, joining with tours to get tour details
    # Order by booking_date descending to show the most recent bookings first
    booking_history = db.execute("""
        SELECT
            b.id,
            b.tour_id,
            b.user_id,
            b.booking_date,
            b.number_of_people,
            b.status AS booking_status, -- Alias booking status to avoid conflict with tour status
            t.name AS tour_name,
            t.date AS tour_date,
            t.time AS tour_time,
            t.price AS tour_price,
            t.location AS tour_location,
            t.status AS tour_status -- Include tour status
        FROM bookings b
        JOIN tours t ON b.tour_id = t.id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC
    """, user_id)

    # Process the fetched data (optional).
    # Format dates and times for display.
    for booking in booking_history:
        # Format booking_date as YYYY-MM-DD HH:MM
        try:
            booking_datetime = datetime.strptime(booking['booking_date'], '%Y-%m-%d %H:%M:%S') # Assuming datetime format
            booking['formatted_booking_date'] = booking_datetime.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            booking['formatted_booking_date'] = booking['booking_date'] # Keep original if parsing fails

        # Format tour_date as YYYY-MM-DD
        try:
            tour_date_obj = datetime.strptime(booking['tour_date'], '%Y-%m-%d').date()
            booking['formatted_tour_date'] = tour_date_obj.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            booking['formatted_tour_date'] = booking['tour_date'] # Keep original if parsing fails

        # Format tour_time as HH:MM
        try:
             # Assuming time is stored as HH:MM or HH:MM:SS string
            tour_time_obj = datetime.strptime(booking['tour_time'], '%H:%M:%S').time() # Adjust format if needed
            booking['formatted_tour_time'] = tour_time_obj.strftime('%H:%M')
        except (ValueError, TypeError):
            booking['formatted_tour_time'] = booking['tour_time'] # Keep original if parsing fails


    # Render the history.html template, passing the booking history
    return render_template("history.html", booking_history=booking_history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Use the helper function to get the name of the first empty field
        empty_field = get_empty_field("username", "password", "roll")

        # Get form data (needed to pass back to template if validation fails)
        username = request.form.get("username")
        roll = request.form.get("roll") # Get the selected roll
        password = request.form.get("password") # Get password for validation


        # If empty_field is not None, it means a required field was empty
        if empty_field:
            flash(f"must provide {empty_field}") # Flash a specific message based on the field name
            # Pass back username and roll to re-populate the form
            return render_template("login.html", username=username, roll=roll)


        # Select user based on username first (more secure)
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # Find the user row that matches the submitted roll
        user_row = None
        for row in rows:
            if row["roll"] == roll:
                user_row = row
                break # Found the matching roll, no need to check further

        # Check if a user with that username and roll was found AND the password is correct
        if user_row is None or not check_password_hash(user_row["hash"], password):
             # Update the error message to be more general, as we don't want to reveal
             # whether the username, password, or roll was incorrect specifically.
            flash("invalid username, password, or roll")
            # Pass back username and roll to re-populate the form
            return render_template("login.html", username=username, roll=roll)

        # Remember which user has logged in
        session["user_id"] = user_row["id"] # Use the ID from the found row
        session["user_roll"] = user_row["roll"] # Store the user's roll in the session

        flash(f"{roll} {username} Logged in successfully!") # Optional: Flash a success message
        return redirect(url_for("index")) # Use url_for

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    flash("Logged out successfully.") # Optional: Flash a logout message
    return redirect(url_for("login")) # Use url_for

# ... (your register route) ...

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Get form data (needed to pass back to template if validation fails)
        username = request.form.get('username')
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        roll = request.form.get("roll") # Get the selected roll

        # Check if username, password, confirmation, and roll fields are empty
        empty_field = get_empty_field("username", "password", "confirmation", "roll")

        if empty_field:
            flash(f"Must provide {empty_field}")
            # Pass back username and roll to re-populate the form (NOT password/confirmation)
            return render_template("register.html", username=username, roll=roll)

        # Check if passwords match
        if password != confirmation:
            flash("Password and confirmation do not match")
             # Pass back username and roll to re-populate the form (NOT password/confirmation)
            return render_template("register.html", username=username, roll=roll)

        # Check if username AND roll already exists (as you correctly identified)
        existing_user = db.execute("SELECT * FROM users WHERE username = ? AND roll = ?", username, roll)

        if existing_user:
            flash(f"Username '{username}' already exists for the role '{roll}'")
            # Pass back username and roll to re-populate the form (NOT password/confirmation)
            return render_template("register.html", username=username, roll=roll)

        # If all checks pass, insert the new user into the database
        hashed = generate_password_hash(password)
        # insert username & hashed password with roll in db
        result = db.execute("INSERT INTO users (username, hash, roll) VALUES (?, ?, ?)", username, hashed, roll)

        # Log the user in automatically after registration
        # Use the lastrowid from the insert result to get the new user's ID
        session["user_id"] = result
        session["user_roll"] = roll # Corrected session key to match 'user_roll' used in login

        flash("Registered successfully!")
        return redirect(url_for("index")) # Use url_for

    # User reached route via GET (as by clicking a link or via redirect)
    # This line handles the initial GET request to display the form.
    return render_template("register.html")


# New route for changing password
@app.route("/change_password", methods=["GET", "POST"])
@login_required # User must be logged in to change password
def change_password():
    """Allow logged-in user to change their password."""

    if request.method == "POST":
        # Get form data
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Check if all fields are filled
        empty_field = get_empty_field("current_password", "new_password", "confirmation")
        if empty_field:
            flash(f"Must provide {empty_field}")
            return render_template("change_password.html") # Re-render the form

        # Get the logged-in user's ID from the session
        user_id = session["user_id"]

        # Fetch the user's current hashed password from the database
        user = db.execute("SELECT hash FROM users WHERE id = ?", user_id)

        # Check if the current password entered matches the stored hash
        if not check_password_hash(user[0]["hash"], current_password):
            flash("Incorrect current password")
            return render_template("change_password.html") # Re-render the form

        # Check if the new password and confirmation match
        if new_password != confirmation:
            flash("New password and confirmation do not match")
            return render_template("change_password.html") # Re-render the form

        # Hash the new password
        hashed_new_password = generate_password_hash(new_password)

        # Update the user's password in the database
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            hashed_new_password,
            user_id
        )

        flash("Password changed successfully!")
        # Redirect to a suitable page after changing password (e.g., index or profile)
        return redirect(url_for("index"))

    # User reached route via GET
    else:
        return render_template("change_password.html")


# --- Employee Routes ---

@app.route("/employee_tasks")
@login_required # Ensure the user is logged in first
@role_required("employee", "administrator") # Check if their roll is 'employee' or 'administrator'
def employee_tasks():
    """Show employee tasks."""

    # 1. Fetch data needed for the employee dashboard.
    # Refine data fetching to get relevant information for the dashboard view.

    # Fetch a list of upcoming tours (scheduled for today or in the future)
    # Use the date.today() function to compare against the tour date.
    # Order by date and time to show the soonest tours first.
    upcoming_tours = db.execute("SELECT * FROM tours WHERE date >= ? ORDER BY date, time", date.today())

    # Fetch a list of recent bookings (e.g., bookings made in the last week)
    # Join bookings, tours, and users tables to get tour name and customer username.
    # Calculate the datetime one week ago.
    # Order by booking_date descending to show the most recent bookings first.
    one_week_ago = datetime.now() - timedelta(weeks=1)
    recent_bookings = db.execute("""
        SELECT
            b.id,
            b.tour_id,
            b.user_id,
            b.booking_date,
            b.number_of_people,
            b.status,
            t.name AS tour_name,          -- Alias tour name
            u.username AS customer_username -- Alias customer username
        FROM bookings b
        JOIN tours t ON b.tour_id = t.id
        JOIN users u ON b.user_id = u.id
        WHERE b.booking_date >= ?
        ORDER BY b.booking_date DESC
    """, one_week_ago)


    # Fetch counts of bookings by status
    confirmed_count_result = db.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'")
    tours_confirmed = confirmed_count_result[0]['COUNT(*)'] if confirmed_count_result else 0

    cancelled_count_result = db.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Cancelled'")
    tours_cancelled = cancelled_count_result[0]['COUNT(*)'] if cancelled_count_result else 0

    pending_count_result = db.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Pending'")
    tours_pending = pending_count_result[0]['COUNT(*)'] if pending_count_result else 0

    # Calculate total revenue from confirmed bookings
    total_revenue_result = db.execute("""
        SELECT COALESCE(SUM(b.number_of_people * t.price), 0) AS total_revenue
        FROM bookings b
        JOIN tours t ON b.tour_id = t.id
        WHERE b.status = 'Confirmed'
    """)
    total_revenue = total_revenue_result[0]['total_revenue'] if total_revenue_result else 0

    # --- Data for Charts ---
    # Removed chart data fetching and preparation
    # --- End Data for Charts ---


    # TODO: Consider fetching tasks assigned to this specific employee if you add an assignment feature.
    # This would involve querying another table that links users to specific tasks or tours.


    # 2. Process the fetched data as needed.
    # Format dates or times for display in the template.
    # Convert date and time objects to strings in a specific format for upcoming tours.
    # Convert datetime objects to strings in a specific format for recent bookings.
    # The total revenue is already calculated, but you might want to format it as currency in the template (done in HTML).

    # Formatting dates and times for display
    for tour in upcoming_tours:
        # Format date asYYYY-MM-DD
        # Assuming 'date' is stored as a string inYYYY-MM-DD format or a date object
        # If it's a date object, use strftime: tour['formatted_date'] = tour['date'].strftime('%Y-%m-%d')
        tour['formatted_date'] = tour['date'] # Keep as is if already string
        # Format time as HH:MM (assuming time is stored as HH:MM string or similar)
        # If it's a time object, use strftime: tour['formatted_time'] = tour['time'].strftime('%H:%M')
        tour['formatted_time'] = tour['time'] # Keep as is if already string


    for booking in recent_bookings:
         # Format booking_date asYYYY-MM-DD HH:MM
         # Assuming booking.booking_date is a datetime object or string
         # If it's a datetime object, use strftime: booking['formatted_booking_date'] = booking['booking_date'].strftime('%Y-%m-%d %H:%M')
         booking['formatted_booking_date'] = booking['booking_date'] # Keep as is if already string


    # 3. Render the employee_tasks.html template.
    # Pass the fetched and processed data to the template.
    # Ensure all variables needed in the template are included here.
    return render_template(
        "employee_tasks.html",
        upcoming_tours=upcoming_tours, # Passing filtered and formatted tours
        recent_bookings=recent_bookings, # Passing filtered and formatted bookings
        tours_confirmed=tours_confirmed,
        tours_cancelled=tours_cancelled,
        tours_pending=tours_pending,
        total_revenue=total_revenue # Passing the calculated total revenue
        # Removed chart data variables
        # booking_status_labels=chart_labels,
        # booking_status_data=chart_data
        # Pass any other processed data here
    )


# --- Tour Management Routes ---

@app.route("/tours/add", methods=["GET", "POST"])
@login_required
@role_required("employee", "administrator")
def add_tour():
    """Add a new tour."""
    # 1. Handle GET request: Display the form to add a new tour.
    if request.method == "GET":
        # Render the add_tour.html template.
        return render_template("add_tour.html")

    # 2. Handle POST request: Process the submitted form data.
    elif request.method == "POST":
        # 2.1. Get form data for the new tour (name, location, description, date, time, duration, price, max_capacity).
        name = request.form.get("name")
        location = request.form.get("location")
        description = request.form.get("description")
        date_str = request.form.get("date") # Get date as string
        time_str = request.form.get("time") # Get time as string
        duration = request.form.get("duration")
        price_str = request.form.get("price") # Get price as string
        max_capacity_str = request.form.get("max_capacity") # Get max_capacity as string

        # 2.2. Validate the form data.
        # Use get_empty_field to check for required fields.
        empty_field = get_empty_field("name", "location", "date", "time", "price", "max_capacity")
        if empty_field:
            flash(f"Must provide {empty_field}")
            # Re-render the form with submitted data (except sensitive)
            return render_template("add_tour.html",
                                   name=name, location=location, description=description,
                                   date=date_str, time=time_str, duration=duration,
                                   price=price_str, max_capacity=max_capacity_str)

        # Add checks for data types (e.g., price, max_capacity should be numbers).
        try:
            price = float(price_str)
            max_capacity = int(max_capacity_str)
        except ValueError:
            flash("Price and Max Capacity must be numbers.")
             # Re-render the form with submitted data
            return render_template("add_tour.html",
                                   name=name, location=location, description=description,
                                   date=date_str, time=time_str, duration=duration,
                                   price=price_str, max_capacity=max_capacity_str)

        # Validate date and time formats (optional but recommended)
        # Use dateutil.parser.parse for more flexible parsing
        try:
            # Attempt to parse date and time
            tour_date = parse(date_str).date()
            tour_time = parse(time_str).time()
        except ValueError:
            flash("Invalid date or time format.")
            # Re-render the form with submitted data
            return render_template("add_tour.html",
                                   name=name, location=location, description=description,
                                   date=date_str, time=time_str, duration=duration,
                                   price=price_str, max_capacity=max_capacity_str)


        # Ensure max_capacity is a positive number.
        if max_capacity <= 0:
            flash("Max Capacity must be a positive number.")
            # Re-render the form with submitted data
            return render_template("add_tour.html",
                                   name=name, location=location, description=description,
                                   date=date_str, time=time_str, duration=duration,
                                   price=price_str, max_capacity=max_capacity_str)

        # 2.3. If validation fails: (Handled above)

        # 2.4. If validation passes:
        # Get the current logged-in user's ID from the session (session["user_id"]). This is the created_by_user_id.
        user_id = session["user_id"]

        # Insert the new tour details into the 'tours' table in the database.
        # The 'status' will default to 'Scheduled'.
        # The 'current_bookings' will default to 0.
        db.execute(
            "INSERT INTO tours (name, location, description, date, time, duration, price, max_capacity, created_by_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            name, location, description, tour_date, tour_time, duration, price, max_capacity, user_id
        )

        # 2.5. Flash a success message (e.g., "Tour added successfully!").
        flash("Tour added successfully!")
        # Redirect to a suitable page (e.g., the employee dashboard or a list of tours).
        return redirect(url_for("employee_tasks")) # Redirect to the employee dashboard


@app.route("/tours/edit/<int:tour_id>", methods=["GET", "POST"])
@login_required
@role_required("employee", "administrator")
def edit_tour(tour_id):
    """Edit an existing tour."""
    # 1. Handle GET request: Display the form to edit the tour.
    if request.method == "GET":
        # 1.1. Get the tour_id from the URL (already provided as an argument).
        # 1.2. Fetch the tour details from the 'tours' table using the tour_id.
        tour = db.execute("SELECT * FROM tours WHERE id = ?", tour_id)

        # 1.3. Check if the tour exists. If not, flash an error and redirect (e.g., to employee dashboard).
        if not tour:
            flash("Tour not found.")
            return redirect(url_for("employee_tasks"))

        # Assuming only one tour is returned by ID
        tour_data = tour[0]

        # 1.4. (Optional but recommended) Check if the logged-in employee has permission to edit this tour
        # (e.g., only if they created it, or if they are an administrator). If not, flash an error and redirect.
        # user_id = session["user_id"]
        # if tour_data["created_by_user_id"] != user_id and session["user_roll"] != "administrator":
        #     flash("You do not have permission to edit this tour.")
        #     return redirect(url_for("employee_tasks"))


        # 1.5. Render the edit_tour.html template, passing the tour data to pre-populate the form.
        return render_template("edit_tour.html", tour=tour_data)

    # 2. Handle POST request: Process the submitted form data for editing.
    elif request.method == "POST":
        # 2.1. Get form data (updated tour details).
        # Get the tour_id from the URL (already provided as an argument).
        name = request.form.get("name")
        location = request.form.get("location")
        description = request.form.get("description")
        date_str = request.form.get("date") # Get date as string
        time_str = request.form.get("time") # Get time as string
        duration = request.form.get("duration")
        price_str = request.form.get("price") # Get price as string
        max_capacity_str = request.form.get("max_capacity") # Get max_capacity as string
        status = request.form.get("status") # Get status (if editable via this form)

        # 2.2. Validate the form data (similar to add_tour validation).
        # Include status validation if it's part of the form.
        empty_field = get_empty_field("name", "location", "date", "time", "price", "max_capacity") # Add "status" if applicable
        if empty_field:
            flash(f"Must provide {empty_field}")
            # Re-render the form with submitted data
            return render_template("edit_tour.html",
                                   tour_id=tour_id, # Pass tour_id back
                                   tour={ # Pass submitted data back in a dictionary format matching 'tour'
                                       "name": name, "location": location, "description": description,
                                       "date": date_str, "time": time_str, "duration": duration,
                                       "price": price_str, "max_capacity": max_capacity_str,
                                       "status": status # Include status if applicable
                                   })

        # Add checks for data types (e.g., price, max_capacity should be numbers).
        try:
            price = float(price_str)
            max_capacity = int(max_capacity_str)
        except ValueError:
            flash("Price and Max Capacity must be numbers.")
             # Re-render the form with submitted data
            return render_template("edit_tour.html",
                                   tour_id=tour_id,
                                   tour={
                                       "name": name, "location": location, "description": description,
                                       "date": date_str, "time": time_str, "duration": duration,
                                       "price": price_str, "max_capacity": max_capacity_str,
                                       "status": status
                                   })

        # Validate date and time formats (optional but recommended)
        # Use dateutil.parser.parse for more flexible parsing
        try:
            # Attempt to parse date and time
            tour_date = parse(date_str).date()
            tour_time = parse(time_str).time()
        except ValueError:
            flash("Invalid date or time format.")
            # Re-render the form with submitted data
            return render_template("edit_tour.html",
                                   tour_id=tour_id,
                                   tour={
                                       "name": name, "location": location, "description": description,
                                       "date": date_str, "time": time_str, "duration": duration,
                                       "price": price_str, "max_capacity": max_capacity_str,
                                       "status": status
                                   })


        # Validate max_capacity is a positive number.
        if max_capacity <= 0:
            flash("Max Capacity must be a positive number.")
             # Re-render the form with submitted data
            return render_template("edit_tour.html",
                                   tour_id=tour_id,
                                    tour={
                                       "name": name, "location": location, "description": description,
                                       "date": date_str, "time": time_str, "duration": duration,
                                       "price": price_str, "max_capacity": max_capacity_str,
                                       "status": status
                                   })

        # Validate status if applicable (ensure it's in the allowed list)
        # allowed_statuses = ['Scheduled', 'Confirmed', 'Cancelled', 'Completed', 'Archived']
        # if status and status not in allowed_statuses:
        #      flash("Invalid status provided.")
        #      return render_template("edit_tour.html", ...) # Re-render form


        # 2.3. If validation fails: (Handled above)

        # 2.4. If validation passes:
        # Update the tour record in the 'tours' table where id matches the tour_id.
        # Include status in the update if it's editable via this form.
        db.execute(
            "UPDATE tours SET name = ?, location = ?, description = ?, date = ?, time = ?, duration = ?, price = ?, max_capacity = ? WHERE id = ?", # Add status = ? if applicable
            name, location, description, tour_date, tour_time, duration, price, max_capacity, tour_id # Add status if applicable
        )


        # 2.5. Flash a success message (e.g., "Tour updated successfully!").
        flash("Tour updated successfully!")
        # Redirect to a suitable page (e.g., the employee dashboard or the edited tour's details page).
        return redirect(url_for("employee_tasks")) # Redirect to the employee dashboard


@app.route("/tours/delete/<int:tour_id>", methods=["POST"])
@login_required
@role_required("employee", "administrator")
def delete_tour(tour_id):
    """Delete a tour."""
    # 1. Handle POST request: Process the request to delete the tour.
    if request.method == "POST":
        # 1.1. Get the tour_id from the URL (already provided as an argument).

        # 1.2. (Optional but recommended) Check for dependencies, e.g., if there are active bookings for this tour.
        # Fetch bookings for this tour.
        active_bookings = db.execute("SELECT COUNT(*) FROM bookings WHERE tour_id = ? AND status IN ('Pending', 'Confirmed')", tour_id)
        if active_bookings[0]['COUNT(*)'] > 0:
            flash("Cannot delete tour with active bookings. Please cancel bookings first.")
            return redirect(url_for("employee_tasks")) # Redirect back to employee tasks or tours list

        # 1.3. (Optional but recommended) Check if the logged-in employee has permission to delete this tour.
        # Fetch the tour to check created_by_user_id or check roll.
        # tour = db.execute("SELECT created_by_user_id FROM tours WHERE id = ?", tour_id)
        # if not tour or (tour[0]["created_by_user_id"] != session["user_id"] and session["user_roll"] != "administrator"):
        #      flash("You do not have permission to delete this tour.")
        #      return redirect(url_for("employee_tasks"))


        # 1.4. If deletion is allowed:
        # Delete the tour record from the 'tours' table where id matches the tour_id.
        delete_count = db.execute("DELETE FROM tours WHERE id = ?", tour_id)

        # Check if a row was actually deleted
        if delete_count > 0:
            # 1.5. Flash a success message (e.g., "Tour deleted successfully!").
            flash("Tour deleted successfully!")
        else:
            # If no row was deleted, the tour might not have existed (though handled by edit/get check)
            flash("Tour not found or could not be deleted.")

        # Redirect to a suitable page (e.g., the employee dashboard or a list of tours).
        return redirect(url_for("employee_tasks")) # Redirect to the employee dashboard


# --- Booking Management Routes ---

@app.route("/bookings/update_status/<int:booking_id>", methods=["POST"])
@login_required
@role_required("employee", "administrator")
def update_booking_status(booking_id):
    """Update the status of a booking."""
    # 1. Handle POST request: Process the request to update booking status.
    if request.method == "POST":
        # 1.1. Get the booking_id from the URL (already provided as an argument).
        # 1.2. Get the new status from the form data (e.g., request.form.get("status")).
        new_status = request.form.get("status")

        # 1.3. Validate the new status (ensure it's one of the allowed statuses in your DB schema: 'Pending', 'Confirmed', 'Cancelled').
        allowed_statuses = ['Pending', 'Confirmed', 'Cancelled']
        if not new_status or new_status not in allowed_statuses:
            flash("Invalid status provided.")
            # Redirect back to the page where the update was initiated (e.g., employee tasks or bookings list)
            return redirect(url_for("employee_tasks")) # Adjust redirect as needed

        # 1.4. Check if the booking exists and fetch necessary data like number_of_people and tour_id
        booking = db.execute("SELECT id, tour_id, status, number_of_people FROM bookings WHERE id = ?", booking_id)
        if not booking:
            flash("Booking not found.")
            return redirect(url_for("employee_tasks")) # Adjust redirect as needed

        # Assuming only one booking is returned by ID
        booking_data = booking[0]
        old_status = booking_data["status"]
        tour_id = booking_data["tour_id"]
        number_of_people = booking_data["number_of_people"] # Fetch number_of_people


        # 1.5. (Optional but recommended) Check if the logged-in employee has permission to update this booking.
        # This might involve checking if they created the tour or if they are an admin.


        # 1.6. If validation and checks pass:
        # Update the 'status' column in the 'bookings' table where id matches the booking_id.
        update_count = db.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            new_status,
            booking_id
        )

        # Consider updating the 'current_bookings' count in the associated 'tours' table if the status changes
        if update_count > 0: # Check if the update was successful
            if old_status == 'Pending' and new_status == 'Confirmed':
                # Increment current_bookings for the tour
                db.execute("UPDATE tours SET current_bookings = current_bookings + ? WHERE id = ?", number_of_people, tour_id)
            elif old_status == 'Confirmed' and new_status == 'Cancelled':
                 # Decrement current_bookings for the tour
                 db.execute("UPDATE tours SET current_bookings = current_bookings - ? WHERE id = ?", number_of_people, tour_id)
            # Add logic for other status changes if needed (e.g., Pending to Cancelled)
            elif old_status == 'Pending' and new_status == 'Cancelled':
                 # No change to current_bookings needed as it wasn't confirmed yet
                 pass
            elif old_status == 'Cancelled' and new_status == 'Confirmed':
                 # This might not be a valid transition in your workflow, but if it is,
                 # you would increment current_bookings.
                 db.execute("UPDATE tours SET current_bookings = current_bookings + ? WHERE id = ?", number_of_people, tour_id)
            elif old_status == 'Cancelled' and new_status == 'Pending':
                 # This might not be a valid transition
                 pass
            elif old_status == 'Confirmed' and new_status == 'Pending':
                 # This might not be a valid transition
                 pass


        # 1.7. Flash a success message (e.g., "Booking status updated!").
        flash("Booking status updated!")
        # Redirect back to a suitable page (e.g., the bookings list or the tour details page).
        return redirect(url_for("employee_tasks")) # Adjust redirect as needed


# --- Tour Status Management Routes ---

@app.route("/tours/update_status/<int:tour_id>", methods=["POST"])
@login_required
@role_required("employee", "administrator")
def update_tour_status(tour_id):
    """Update the overall status of a tour."""
    # 1. Handle POST request: Process the request to update tour status.
    if request.method == "POST":
        # 1.1. Get the tour_id from the URL (already provided as an argument).
        # 1.2. Get the new status from the form data (e.g., request.form.get("status")).
        new_status = request.form.get("status")

        # 1.3. Validate the new status (ensure it's one of the allowed statuses in your DB schema: 'Scheduled', 'Confirmed', 'Cancelled', 'Completed', 'Archived').
        allowed_statuses = ['Scheduled', 'Confirmed', 'Cancelled', 'Completed', 'Archived']
        if not new_status or new_status not in allowed_statuses:
            flash("Invalid status provided.")
            # Redirect back to the page where the update was initiated (e.g., employee tasks or tours list)
            return redirect(url_for("employee_tasks")) # Adjust redirect as needed

        # 1.4. Check if the tour exists. If not, flash an error and redirect.
        tour = db.execute("SELECT id, status FROM tours WHERE id = ?", tour_id)
        if not tour:
            flash("Tour not found.")
            return redirect(url_for("employee_tasks")) # Adjust redirect as needed

        # Assuming only one tour is returned by ID
        tour_data = tour[0]
        old_status = tour_data["status"]

        # 1.5. (Optional but recommended) Check if the logged-in employee has permission to update this tour status.


        # 1.6. If validation and checks pass:
        # Update the 'status' column in the 'tours' table where id matches the tour_id.
        update_count = db.execute(
            "UPDATE tours SET status = ? WHERE id = ?",
            new_status,
            tour_id
        )

        # Consider adding additional logic based on status change (e.g., if status is set to 'Cancelled',
        # you might want to automatically cancel all associated bookings and notify customers).
        if update_count > 0: # Check if the update was successful
             if old_status != 'Cancelled' and new_status == 'Cancelled':
                 # Automatically cancel all pending or confirmed bookings for this tour
                 db.execute("UPDATE bookings SET status = 'Cancelled' WHERE tour_id = ? AND status IN ('Pending', 'Confirmed')", tour_id)
                 # You might also want to add logic to notify customers here

        # 1.7. Flash a success message (e.g., "Tour status updated!").
        flash("Tour status updated!")
        # Redirect back to a suitable page (e.g., the employee dashboard or the tour details page).
        return redirect(url_for("employee_tasks")) # Adjust redirect as needed


# --- Customer Routes ---

@app.route("/tours")
# @login_required # Decide if tours list requires login
# @role_required("customer") # Decide if only customers can see the list
def list_tours():
    """Display a list of available tours for customers."""
    # 1. Fetch tours that are available for booking.
    # This might mean tours with status 'Scheduled' or 'Confirmed' and in the future.
    # Order by date and time.
    # You might want to exclude tours that are full (current_bookings >= max_capacity).
    available_tours = db.execute("""
        SELECT * FROM tours
        WHERE date >= ? AND status IN ('Scheduled', 'Confirmed')
        AND current_bookings < max_capacity
        ORDER BY date, time
    """, date.today())

    # 2. Process the fetched data (optional).
    # Format dates and times for display.

    # Formatting dates and times for display
    for tour in available_tours:
        tour['formatted_date'] = tour['date'] # Adjust formatting as needed
        tour['formatted_time'] = tour['time'] # Adjust formatting as needed


    # 3. Render a template to display the tours.
    # Pass the list of available tours to the template.
    return render_template("list_tours.html", available_tours=available_tours)


@app.route("/tours/<int:tour_id>")
# @login_required # Decide if viewing tour details requires login
# @role_required("customer") # Decide if only customers can see details
def view_tour_details(tour_id):
    """Display details of a specific tour."""
    # 1. Get the tour_id from the URL.
    # 2. Fetch the specific tour details from the database.
    tour = db.execute("SELECT * FROM tours WHERE id = ?", tour_id)

    # 3. Check if the tour exists. If not, flash an error and redirect (e.g., to the list of tours).
    if not tour:
        flash("Tour not found.")
        return redirect(url_for("list_tours"))

    # Assuming only one tour is returned by ID
    tour_data = tour[0]

    # Convert date string to date object for comparison in template
    try:
        tour_data['date_obj'] = datetime.strptime(tour_data['date'], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        tour_data['date_obj'] = None # Handle potential errors


    # 4. (Optional) Fetch related data, e.g., reviews or photos if you add those features.

    # 5. Process the fetched data (optional).
    # Format dates and times for display.
    tour_data['formatted_date'] = tour_data['date'] # Adjust formatting as needed
    tour_data['formatted_time'] = tour_data['time'] # Adjust formatting as needed


    # 6. Render a template to display the tour details.
    # Pass the tour data and the current date for booking availability check in the template
    return render_template("view_tour_details.html", tour=tour_data, today=date.today())


@app.route("/book/<int:tour_id>", methods=["GET", "POST"])
@login_required # Booking requires login
@role_required("customer") # Only customers can book
def book_tour(tour_id):
    """Handle booking a tour."""
    # 1. Handle GET request: Display the booking form.
    if request.method == "GET":
        # 1.1. Get the tour_id from the URL.
        # 1.2. Fetch the tour details to display information on the booking form (name, date, time, price, availability).
        tour = db.execute("SELECT * FROM tours WHERE id = ?", tour_id)

        # 1.3. Check if the tour exists and is available for booking.
        if not tour or tour[0]['date'] < date.today() or tour[0]['status'] not in ('Scheduled', 'Confirmed') or tour[0]['current_bookings'] >= tour[0]['max_capacity']:
            flash("Tour is not available for booking.")
            return redirect(url_for("list_tours"))

        # Assuming only one tour is returned by ID
        tour_data = tour[0]

        # 1.4. Render the booking form template.
        # Pass the tour data to the template.
        return render_template("book_tour.html", tour=tour_data)

    # 2. Handle POST request: Process the booking submission.
    elif request.method == "POST":
        # 2.1. Get the tour_id from the URL.
        # 2.2. Get form data (e.g., number of people).
        number_of_people_str = request.form.get("number_of_people")

        # 2.3. Validate form data.
        # Check if number_of_people is provided and is a positive integer.
        # Check if the requested number of people exceeds the available capacity for the tour.
        try:
            number_of_people = int(number_of_people_str)
            if number_of_people <= 0:
                 flash("Number of people must be a positive integer.")
                 # Re-fetch tour data and re-render the form
                 tour = db.execute("SELECT * FROM tours WHERE id = ?", tour_id)
                 return render_template("book_tour.html", tour=tour[0])
        except ValueError:
            flash("Number of people must be a number.")
             # Re-fetch tour data and re-render the form
            tour = db.execute("SELECT * FROM tours WHERE id = ?", tour_id)
            return render_template("book_tour.html", tour=tour[0])

        # Fetch the tour again to check availability before booking
        tour = db.execute("SELECT * FROM tours WHERE id = ?", tour_id)
        if not tour or tour[0]['date'] < date.today() or tour[0]['status'] not in ('Scheduled', 'Confirmed'):
            flash("Tour is no longer available for booking.")
            return redirect(url_for("list_tours"))

        tour_data = tour[0]
        available_capacity = tour_data['max_capacity'] - tour_data['current_bookings']

        if number_of_people > available_capacity:
            flash(f"Only {available_capacity} spots available.")
            # Re-render the form with submitted data
            return render_template("book_tour.html", tour=tour_data, number_of_people=number_of_people_str)


        # 2.4. If validation passes:
        # Get the logged-in customer's user_id from the session.
        user_id = session["user_id"]

        # Insert a new booking record into the 'bookings' table.
        # Set status to 'Pending' initially.
        db.execute(
            "INSERT INTO bookings (tour_id, user_id, number_of_people, status) VALUES (?, ?, ?, ?)",
            tour_id, user_id, number_of_people, 'Pending'
        )

        # Update the 'current_bookings' count in the 'tours' table (increment by number_of_people).
        # Note: This should ideally happen when the booking is confirmed, but for simplicity,
        # we'll increment on initial booking here. You might adjust this based on your workflow.
        db.execute("UPDATE tours SET current_bookings = current_bookings + ? WHERE id = ?", number_of_people, tour_id)


        # 2.5. Flash a success message (e.g., "Booking request submitted!").
        flash("Booking request submitted! Your booking is pending confirmation.")
        # Redirect to a suitable page (e.g., the customer's 'my bookings' page or the tour details page).
        return redirect(url_for("my_bookings"))


@app.route("/my_bookings")
@login_required # Requires login
@role_required("customer") # Only customers can view their bookings
def my_bookings():
    """Display a list of the logged-in customer's bookings."""
    # 1. Get the logged-in customer's user_id from the session.
    user_id = session["user_id"]

    # 2. Fetch all bookings for this user.
    # Join with the 'tours' table to get tour details for each booking.
    customer_bookings = db.execute("""
        SELECT
            b.id,
            b.tour_id,
            b.user_id,
            b.booking_date,
            b.number_of_people,
            b.status,
            t.name AS tour_name,
            t.date AS tour_date,
            t.time AS tour_time,
            t.price AS tour_price
        FROM bookings b
        JOIN tours t ON b.tour_id = t.id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC
    """, user_id)

    # 3. Process the fetched data (optional).
    # Format dates and times for display.
    for booking in customer_bookings:
        booking['formatted_booking_date'] = booking['booking_date'] # Adjust formatting as needed
        booking['formatted_tour_date'] = booking['tour_date'] # Adjust formatting as needed
        booking['formatted_tour_time'] = booking['tour_time'] # Adjust formatting as needed


    # 4. Render a template to display the bookings.
    # Pass the list of customer bookings to the template.
    return render_template("my_bookings.html", customer_bookings=customer_bookings)


@app.route("/bookings/cancel/<int:booking_id>", methods=["POST"])
@login_required # Requires login
@role_required("customer") # Only customers can cancel their bookings
def cancel_booking(booking_id):
    """Allow a customer to cancel one of their bookings."""
    # 1. Handle POST request: Process the cancellation request.
    if request.method == "POST":
        # 1.1. Get the booking_id from the URL.
        # 1.2. Get the logged-in customer's user_id from the session.
        user_id = session["user_id"]

        # 1.3. Fetch the booking to be canceled.
        # Check if the booking exists, belongs to the logged-in user, and is in a cancellable status (e.g., 'Pending' or 'Confirmed').
        booking = db.execute("SELECT id, tour_id, user_id, status, number_of_people FROM bookings WHERE id = ? AND user_id = ?", booking_id, user_id)

        if not booking:
            flash("Booking not found or you do not have permission to cancel it.")
            return redirect(url_for("my_bookings")) # Redirect back to my bookings

        booking_data = booking[0]
        old_status = booking_data["status"]
        tour_id = booking_data["tour_id"]
        number_of_people = booking_data["number_of_people"]

        if old_status not in ('Pending', 'Confirmed'):
             flash(f"Booking status '{old_status}' cannot be cancelled.")
             return redirect(url_for("my_bookings")) # Redirect back to my bookings


        # 1.4. If cancellation is allowed:
        # Update the booking status to 'Cancelled'.
        update_count = db.execute(
            "UPDATE bookings SET status = 'Cancelled' WHERE id = ?",
            booking_id
        )

        # If the old status was 'Confirmed', decrement the 'current_bookings' count in the associated 'tours' table.
        if update_count > 0 and old_status == 'Confirmed':
            db.execute("UPDATE tours SET current_bookings = current_bookings - ? WHERE id = ?", number_of_people, tour_id)


        # 1.5. Flash a success message (e.g., "Booking canceled successfully!").
        flash("Booking canceled successfully!")
        # Redirect back to the customer's 'my bookings' page.
        return redirect(url_for("my_bookings"))


# --- Administrator Routes ---

@app.route("/admin_dashboard")
@login_required
@role_required("administrator")
def admin_dashboard():
    """Show admin dashboard."""
    # 1. Fetch data needed for the admin dashboard overview.
    # This might include counts of users, tours (by status), bookings (by status), total revenue etc.
    # Some of this data might be similar to the employee dashboard but for all records.

    # Example: Fetch counts of users by roll
    customer_count_result = db.execute("SELECT COUNT(*) FROM users WHERE roll = 'customer'")
    customer_count = customer_count_result[0]['COUNT(*)'] if customer_count_result else 0

    employee_count_result = db.execute("SELECT COUNT(*) FROM users WHERE roll = 'employee'")
    employee_count = employee_count_result[0]['COUNT(*)'] if employee_count_result else 0

    admin_count_result = db.execute("SELECT COUNT(*) FROM users WHERE roll = 'administrator'")
    admin_count = admin_count_result[0]['COUNT(*)'] if admin_count_result else 0

    # Example: Fetch total number of tours (all statuses)
    total_tours_result = db.execute("SELECT COUNT(*) FROM tours")
    total_tours = total_tours_result[0]['COUNT(*)'] if total_tours_result else 0

    # Example: Fetch total number of bookings (all statuses)
    total_bookings_result = db.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = total_bookings_result[0]['COUNT(*)'] if total_bookings_result else 0

    # Total revenue from confirmed bookings is already calculated in employee_tasks,
    # you could reuse that query here if needed for an admin overview.


    # 2. Render the admin_dashboard.html template.
    # Pass the fetched data to the template.
    return render_template(
        "admin_dashboard.html",
        customer_count=customer_count,
        employee_count=employee_count,
        admin_count=admin_count,
        total_tours=total_tours,
        total_bookings=total_bookings
        # Pass other overview data here
    )


@app.route("/admin/users")
@login_required
@role_required("administrator")
def admin_list_users():
    """Display a list of all users for administrators."""
    # 1. Fetch all users from the database.
    # You might want to exclude the currently logged-in administrator from the list for safety.
    users = db.execute("SELECT id, username, roll FROM users") # Exclude hash for security

    # 2. Render a template to display the users.
    # Pass the list of users to the template.
    return render_template("admin_list_users.html", users=users)


@app.route("/admin/users/edit_role/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("administrator")
def admin_edit_user_role(user_id):
    """Allow administrator to edit a user's role."""
    # 1. Handle GET request: Display the form to edit the user's role.
    if request.method == "GET":
        # 1.1. Get the user_id from the URL.
        # 1.2. Fetch the user details (id, username, current roll) from the database.
        user = db.execute("SELECT id, username, roll FROM users WHERE id = ?", user_id)

        # 1.3. Check if the user exists. If not, flash an error and redirect (e.g., to admin user list).
        if not user:
            flash("User not found.")
            return redirect(url_for("admin_list_users"))

        # Assuming only one user is returned by ID
        user_data = user[0]

        # 1.4. (Optional) Prevent changing the role of the currently logged-in administrator.
        if user_data["id"] == session["user_id"]:
             flash("You cannot change your own role.")
             return redirect(url_for("admin_list_users"))


        # 1.5. Render the admin_edit_user_role.html template, passing the user data.
        # Pass the allowed roles to the template for the dropdown.
        allowed_roles = ['customer', 'employee', 'administrator']
        return render_template("admin_edit_user_role.html", user=user_data, allowed_roles=allowed_roles)

    # 2. Handle POST request: Process the role update.
    elif request.method == "POST":
        # 2.1. Get the user_id from the URL.
        # 2.2. Get the new roll from the form data.
        new_roll = request.form.get("roll")

        # 2.3. Validate the new roll (ensure it's one of the allowed roles).
        allowed_roles = ['customer', 'employee', 'administrator']
        if not new_roll or new_roll not in allowed_roles:
            flash("Invalid role provided.")
            # Re-fetch user data and re-render the form
            user = db.execute("SELECT id, username, roll FROM users WHERE id = ?", user_id)
            return render_template("admin_edit_user_role.html", user=user[0], allowed_roles=allowed_roles)

        # 2.4. (Optional) Prevent changing the role of the currently logged-in administrator.
        if user_id == session["user_id"]:
             flash("You cannot change your own role.")
             return redirect(url_for("admin_list_users"))


        # 2.5. If validation and checks pass:
        # Update the user's 'roll' in the 'users' table.
        update_count = db.execute(
            "UPDATE users SET roll = ? WHERE id = ?",
            new_roll,
            user_id
        )

        # 2.6. Flash a success message.
        if update_count > 0:
             flash(f"User role updated to {new_roll}!")
        else:
             flash("Could not update user role.") # Should not happen if user exists and isn't self

        # 2.7. Redirect to the admin user list.
        return redirect(url_for("admin_list_users"))


@app.route("/admin/tours")
@login_required
@role_required("administrator")
def admin_list_tours():
    """Display a list of all tours (all statuses) for administrators."""
    # 1. Fetch all tours from the database.
    # Order by date and time.
    all_tours = db.execute("SELECT * FROM tours ORDER BY date, time")

    # 2. Process the fetched data (optional).
    # Format dates and times for display.
    for tour in all_tours:
        tour['formatted_date'] = tour['date'] # Adjust formatting as needed
        tour['formatted_time'] = tour['time'] # Adjust formatting as needed


    # 3. Render a template to display all tours.
    # Pass the list of all tours to the template.
    return render_template("admin_list_tours.html", all_tours=all_tours)


@app.route("/admin/bookings")
@login_required
@role_required("administrator")
def admin_list_bookings():
    """Display a list of all bookings (all statuses) for administrators."""
    # 1. Fetch all bookings from the database.
    # Join with 'tours' and 'users' tables to get tour name and customer username.
    # Order by booking date.
    all_bookings = db.execute("""
        SELECT
            b.id,
            b.tour_id,
            b.user_id,
            b.booking_date,
            b.number_of_people,
            b.status,
            t.name AS tour_name,
            u.username AS customer_username
        FROM bookings b
        JOIN tours t ON b.tour_id = t.id
        JOIN users u ON b.user_id = u.id
        ORDER BY b.booking_date DESC
    """)

    # 2. Process the fetched data (optional).
    # Format dates and times for display.
    for booking in all_bookings:
        booking['formatted_booking_date'] = booking['booking_date'] # Adjust formatting as needed


    # 3. Render a template to display all bookings.
    # Pass the list of all bookings to the template.
    return render_template("admin_list_bookings.html", all_bookings=all_bookings)


# Example of a route accessible by customers
@app.route("/customer_profile")
@login_required # Ensure the user is logged in first
@role_required("customer") # Check if their roll is 'customer'
def customer_profile():
    """Show customer profile."""
    # TODO: Fetch and display customer-specific information
    # For now, it just renders the template.
    return render_template("customer_profile.html") # You'll need to create this template
