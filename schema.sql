CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    roll TEXT NOT NULL CHECK(roll IN ('customer', 'employee', 'administrator')),
    UNIQUE(username, roll) -- This line ensures the combination of username and roll is unique
);

CREATE TABLE tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    duration TEXT, -- e.g., "3 hours"
    price NUMERIC NOT NULL,
    max_capacity INTEGER NOT NULL DEFAULT 0,
    current_bookings INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('Scheduled', 'Confirmed', 'Cancelled', 'Completed', 'Archived')) DEFAULT 'Scheduled',
    created_by_user_id INTEGER NOT NULL,
    FOREIGN KEY(created_by_user_id) REFERENCES users(id)
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tour_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL, -- The customer who booked
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    number_of_people INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN
('Pending', 'Confirmed', 'Cancelled')) DEFAULT 'Pending',
    FOREIGN KEY(tour_id) REFERENCES tours(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);