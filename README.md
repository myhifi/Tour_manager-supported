Tour Manager
Project Description
The Tour Manager is a web application built with Flask that facilitates the management of tours and bookings. It supports different user roles (Customer, Employee, and Administrator) with varying levels of access and functionality.
Customers can browse available tours, book tours, view their bookings, and cancel bookings. They can also view their booking history. Employees can manage tours (add, edit, delete), view upcoming tours and recent bookings, and update booking statuses. Administrators have overarching access to manage users (including roles), view all tours, and view all bookings.
Features
•	User Authentication: Secure registration and login system with different roles (Customer, Employee, Administrator).
•	Role-Based Access Control: Restrict access to certain routes and functionalities based on the user's assigned role.
•	Employee Dashboard: Provides an overview of key metrics for employees (e.g., confirmed, cancelled, pending bookings, total revenue).
•	Tour Management (Employee/Admin):
o	Add new tours with details like name, location, description, date, time, duration, price, and capacity.
o	Edit existing tour details.
o	Delete tours (with a check for active bookings).
o	Update tour status (Scheduled, Confirmed, Cancelled, Completed, Archived).
•	Booking Management (Employee/Admin):
o	View recent bookings.
o	Update booking statuses (Pending, Confirmed, Cancelled).
o	Automatic update of tour's current bookings count based on booking status changes.
•	Tour Browsing (Customer): View a list of available tours.
•	Tour Details (Customer): View detailed information about a specific tour.
•	Tour Booking (Customer): Book a tour with a specified number of people (subject to availability).
•	My Bookings (Customer): View a list of their own bookings.
•	Booking Cancellation (Customer): Cancel their own bookings (within allowed statuses).
•	Booking History (All Logged-in Users): View a history of all their past and current bookings.
•	Administrator Dashboard: Provides an overview of system-wide metrics (e.g., user counts by role, total tours, total bookings).
•	User Management (Admin): View all users and edit their roles.
•	Comprehensive Data Display: Tables displaying upcoming tours, recent bookings, and user/tour/booking lists for relevant roles.
•	Flash Messages: Provide user feedback for actions (success, errors, warnings).
Technologies Used
•	Flask: Python web framework.
•	CS50 Library (SQL): Simplified interface for interacting with SQLite databases.
•	Werkzeug: Comprehensive WSGI utility library for Python (used by Flask for security features like password hashing).
•	Flask-Session: Extension for managing server-side sessions.
•	SQLite: Lightweight, file-based database.
•	HTML, CSS, JavaScript: Frontend development.
•	Bootstrap: Frontend framework for responsive design.
•	Jinja2: Templating engine used by Flask.
•	python-dateutil: Library for robust date and time parsing (used for handling date/time inputs).
Setup
Prerequisites
•	Python 3.6 or higher
•	pip (Python package installer)
Installation
1.	Clone the repository:
2.	git clone <repository_url>
3.	cd tour_manager

(Replace <repository_url> with the actual URL of your repository)
4.	Create a virtual environment (recommended):
5.	python -m venv venv

6.	Activate the virtual environment:
o	On macOS and Linux:
o	source venv/bin/activate

o	On Windows:
o	venv\Scripts\activate

7.	Install the required packages:
It's recommended to use a requirements.txt file to manage project dependencies.
o	If requirements.txt exists:
o	pip install -r requirements.txt

o	If requirements.txt does not exist:
Create a requirements.txt file in the root directory of your project with the following content:
Flask
cs50
Werkzeug
Flask-Session
python-dateutil

Then, install the packages:
pip install -r requirements.txt

(Note: You might need to run pip freeze > requirements.txt after installing packages manually to generate this file initially).
Database Setup
1.	Create the SQLite database file:
The application is configured to use tour_manager.db. You can create an empty file with this name in the project directory.
2.	Create the necessary tables:
Use a database tool (like sqlite3 command-line tool, DB Browser for SQLite, or a Python script) to execute the SQL statements for creating the users, tours, and bookings tables.
users table:
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    roll TEXT NOT NULL CHECK(roll IN ('customer', 'employee', 'administrator')),
    UNIQUE(username, roll) -- This line ensures the combination of username and roll is unique
);

tours table:
CREATE TABLE tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    duration TEXT, -- e.g., "2 hours", "Half Day"
    price NUMERIC NOT NULL,
    max_capacity INTEGER NOT NULL,
    current_bookings INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('Scheduled', 'Confirmed', 'Cancelled', 'Completed', 'Archived')) DEFAULT 'Scheduled',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NOT NULL, -- Link to the user who created the tour
    FOREIGN KEY(created_by_user_id) REFERENCES users(id)
);

bookings table:
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tour_id INTEGER NOT NULL, -- Link to the tours table
    user_id INTEGER NOT NULL, -- Link to the users table (customer)
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    number_of_people INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Pending', 'Confirmed', 'Cancelled')) DEFAULT 'Pending',
    FOREIGN KEY(tour_id) REFERENCES tours(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

(Optional) password_reset_tokens table (if implementing secure password reset):
CREATE TABLE password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL, -- Link to the users table
    token TEXT NOT NULL UNIQUE, -- The unique token
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- When the token was created
    expires_at DATETIME NOT NULL, -- When the token expires (e.g., 1 hour later)
    used BOOLEAN NOT NULL DEFAULT FALSE, -- Flag to indicate if the token has been used
    FOREIGN KEY(user_id) REFERENCES users(id)
);

3.	Add initial users (optional): You can manually add an administrator, employee, and customer to the users table for testing purposes. Remember to hash the passwords using a tool or a temporary script.
Running the Application
1.	Set the Flask application file:
2.	export FLASK_APP=app.py

(On Windows, use set FLASK_APP=app.py)
3.	Run the Flask development server:
4.	flask run

5.	Open your web browser and go to http://127.0.0.1:5000/.
Usage
User Roles
•	Customer:
o	Register and log in.
o	Browse available tours (/tours).
o	View details of a specific tour (/tours/<tour_id>).
o	Book available tours (/book/<tour_id>).
o	View their own bookings (/my_bookings).
o	Cancel their own bookings (/bookings/cancel/<booking_id> - via POST form).
o	View their booking history (/history).
o	Change their password (/change_password).
•	Employee:
o	Log in with an employee account.
o	Access the Employee Dashboard (/employee_tasks).
o	View upcoming tours and recent bookings.
o	Add new tours (/tours/add).
o	Edit tours (/tours/edit/<tour_id>).
o	Delete tours (/tours/delete/<tour_id> - via POST form).
o	Update tour status (/tours/update_status/<tour_id> - via POST form).
o	Update booking status (/bookings/update_status/<booking_id> - via POST form).
o	View their booking history (/history).
o	Change their password (/change_password).
•	Administrator:
o	Log in with an administrator account.
o	Access the Administrator Dashboard (/admin_dashboard).
o	View system overview.
o	View all users (/admin/users).
o	Edit user roles (/admin/users/edit_role/<user_id>).
o	View all tours (/admin/tours).
o	View all bookings (/admin/bookings).
o	Has access to all Employee functionalities.
o	View their booking history (/history).
o	Change their password (/change_password).
Accessing Pages
•	/: Landing page (accessible without login).
•	/login: User login page.
•	/logout: User logout action.
•	/register: New user registration page.
•	/change_password: Change password page (requires login).
•	/reset_password: (If implemented) Password reset request page.
•	/reset_password/<token>: (If implemented) Password reset confirmation page.
•	/employee_tasks: Employee Dashboard (requires Employee or Administrator role).
•	/tours/add: Add New Tour page (requires Employee or Administrator role).
•	/tours/edit/<tour_id>: Edit Tour page (requires Employee or Administrator role).
•	/tours/delete/<tour_id>: Delete Tour action (requires Employee or Administrator role).
•	/bookings/update_status/<booking_id>: Update Booking Status action (requires Employee or Administrator role).
•	/tours/update_status/<tour_id>: Update Tour Status action (requires Employee or Administrator role).
•	/tours: List of available tours (customer view).
•	/tours/<tour_id>: View specific tour details (customer view).
•	/book/<tour_id>: Book a tour page (requires Customer role).
•	/my_bookings: Customer's list of bookings (requires Customer role).
•	/bookings/cancel/<booking_id>: Cancel booking action (requires Customer role).
•	/history: User Booking History (requires any logged-in user).
•	/admin_dashboard: Administrator Dashboard (requires Administrator role).
•	/admin/users: Administrator's list of users (requires Administrator role).
•	/admin/users/edit_role/<user_id>: Edit user role page (requires Administrator role).
•	/admin/tours: Administrator's list of all tours (requires Administrator role).
•	/admin/bookings: Administrator's list of all bookings (requires Administrator role).
•	/customer_profile: Customer Profile page (requires Customer role).
File Structure
tour_manager/
├── app.py              # Main Flask application file
├── helpers.py          # Helper functions (login_required, validation, role_required)
├── tour_manager.db     # SQLite database file
├── static/             # Static files (CSS, JavaScript, images - if any)
│   └── styles.css      # Example CSS file
└── templates/          # Jinja2 HTML templates
    ├── layout.html     # Base template
    ├── index.html      # Landing page
    ├── login.html      # Login form
    ├── register.html   # Registration form
    ├── change_password.html # Change password form
    ├── employee_tasks.html # Employee Dashboard
    ├── add_tour.html     # Add Tour form
    ├── edit_tour.html    # Edit Tour form
    ├── list_tours.html   # Customer tour list
    ├── view_tour_details.html # Customer tour details
    ├── book_tour.html    # Customer booking form
    ├── my_bookings.html  # Customer bookings list
    ├── history.html      # User Booking History
    ├── admin_dashboard.html # Administrator Dashboard
    ├── admin_list_users.html # Admin user list
    ├── admin_edit_user_role.html # Admin edit user role form
    ├── admin_list_tours.html # Admin tour list
    ├── admin_list_bookings.html # Admin booking list
    {# Add templates for simple reset if implemented #}
    {# ├── simple_reset_request.html #}
    {# ├── simple_change_password.html #}
    {# Add templates for secure reset if implemented #}
    {# ├── reset_password_request.html #}
    {# ├── reset_password_confirm.html #}

Potential Future Enhancements
•	Secure Password Reset: Implement the token-based password reset flow.
•	Email Notifications: Send emails for booking confirmations, cancellations, password resets, etc.
•	Search and Filtering: Add search and filtering options for tours and bookings.
•	Pagination: Implement pagination for long lists of tours and bookings.
•	Tour Images/Gallery: Allow uploading and displaying images for tours.
•	Reviews/Ratings: Implement a system for customers to leave reviews for tours.
•	Employee Task Assignment: Allow administrators to assign specific tours or tasks to employees.
•	More Detailed Dashboards: Add more charts and metrics to the employee and administrator dashboards.
•	Admin User Deletion: Add functionality for administrators to delete users (with caution).
•	API Endpoints: Create API endpoints for external applications to interact with the tour data.
•	Improved UI/UX: Further refine the user interface and user experience.
License
This project is licensed under the MIT License. (You would need to create a LICENSE file with the MIT license text).