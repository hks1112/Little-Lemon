# Little Lemon API — Setup & Submission

This project is fully written and ready to go. Because the assignment requires
you to submit an actual `db.sqlite3` file with real user accounts already
created in it, there is no way around running it locally **once** to generate
that database — but it's just 6 copy-paste commands, no coding required.

## 1. One-time setup

Open a terminal in this `LittleLemon` folder and run:

```
pipenv install
pipenv shell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py bootstrap_demo
```

- `createsuperuser` will ask you to pick a username/password interactively —
  choose your own and remember them.
- `bootstrap_demo` automatically creates a manager user, a delivery-crew
  user, and a customer user (with the passwords already written into
  `notes.txt`), plus a few categories and menu items so the browsing
  endpoints have real data to return.

## 2. Fill in notes.txt

Open `notes.txt` and replace the superuser placeholder with the
username/password you chose in `createsuperuser`. The other three accounts
are already filled in for you.

## 3. Quick sanity check (optional but recommended)

```
python manage.py runserver
```

Then in your browser or Insomnia:
- `GET http://127.0.0.1:8000/api/menu-items` — should return the 7 seeded items
- `POST http://127.0.0.1:8000/auth/token/login/` with your superuser's
  username/password — should return a token
- `GET http://127.0.0.1:8000/api/categories` — should return 4 categories

Stop the server with `Ctrl+C` when you're satisfied it works.

## 4. Zip it for submission

Once `db.sqlite3` exists (created in step 1) and `notes.txt` is filled in,
zip the whole `LittleLemon` folder (including `db.sqlite3` and `notes.txt`
inside it) and upload that zip to the peer-review assignment.

Do **not** delete `db.sqlite3` before zipping — the assignment explicitly
requires it so your reviewer doesn't have to create their own users.

## Endpoint reference (matches every grading criterion)

| # | Criterion | Endpoint |
|---|-----------|----------|
| 1 | Admin assigns user to Manager group | `POST /api/groups/manager/users` (admin token) |
| 2 | Access manager group with admin token | `GET /api/groups/manager/users` (admin token) |
| 3 | Admin adds menu items | `POST /api/menu-items` (admin/manager) |
| 4 | Admin adds categories | `POST /api/categories` (admin) |
| 5 | Manager logs in | `POST /auth/token/login/` |
| 6 | Manager updates item of the day | `PATCH /api/menu-items/{id}` (manager) |
| 7 | Manager assigns delivery crew | `POST /api/groups/delivery-crew/users` (manager) |
| 8 | Manager assigns orders to delivery crew | `PATCH /api/orders/{id}` with `delivery_crew` (manager) |
| 9 | Delivery crew sees assigned orders | `GET /api/orders` (delivery crew) |
| 10 | Delivery crew marks delivered | `PATCH /api/orders/{id}` with `status` (delivery crew) |
| 11 | Customer registers | `POST /auth/users/` |
| 12 | Customer logs in, gets token | `POST /auth/token/login/` |
| 13 | Browse categories | `GET /api/categories` |
| 14 | Browse all menu items | `GET /api/menu-items` |
| 15 | Browse by category | `GET /api/menu-items?category=main-courses` |
| 16 | Paginate menu items | `GET /api/menu-items?page=1&perpage=2` |
| 17 | Sort by price | `GET /api/menu-items?ordering=price` |
| 18 | Add to cart | `POST /api/cart/menu-items` |
| 19 | View own cart | `GET /api/cart/menu-items` |
| 20 | Place order | `POST /api/orders` |
| 21 | Browse own orders | `GET /api/orders` (customer) |
