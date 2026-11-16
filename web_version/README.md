# Movie Ticket Reservation System — Web Version

This is a separate Flask/browser version of the original Tkinter desktop project.
The original files are not edited by this web version.

## Run on your computer (Windows)

1. Install Python 3.10 or newer.
2. Open this `web_version` folder in VS Code.
3. Open Terminal > New Terminal.
4. Run:

```bash
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser.

## Login

The original desktop project's database code creates an admin account:
- Username: `admin`
- Password: `admin`

Change this password before making the site public. For a real deployment, replace the default admin credentials and use a strong `SECRET_KEY`.

New visitors can register from the website. Registered accounts have the `user` role.

## Deploy to Render

1. Upload the contents of this folder into a new folder named `web_version` in your existing GitHub repository. Do not replace the original desktop files.
2. In Render, choose **New + > Web Service**, connect the GitHub repository, and set **Root Directory** to `web_version`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app`
5. Add a persistent disk mounted at `/var/data` if your Render plan supports it. Add environment variable:
   `DATABASE_PATH=/var/data/movie_reservation.db`
6. Add a strong `SECRET_KEY` environment variable if not generated automatically.
7. Deploy. Render will provide the public website URL after a successful deployment.

**Important:** Without a persistent disk or external database, SQLite data on a typical web-service filesystem can be lost when the service restarts or redeploys. A persistent disk may depend on the Render plan and can add cost. Check the current Render plan and disk options before enabling it.

## Features

- User registration and login
- Separate admin and user access based on account role
- User: view currently bookable shows, book tickets, view/cancel own bookings
- Admin: add/delete movies, add/delete shows, view/delete bookings, clear bookings
- The original desktop project's 10% tax and 5% discount for bookings of 5 or more seats are retained
- Booking deadline / booking-window support

## Database

By default this version creates its own `movie_reservation_web.db` file. It does not overwrite the desktop project's `movie_reservation.db`.
