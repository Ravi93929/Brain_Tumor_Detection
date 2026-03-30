# NeuroScan AI - Split Frontend and Backend

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Project structure

- `routes/` -> Flask route handlers
- `services/` -> business logic, mail, OTP, prediction, PDF
- `database/` -> SQLite setup
- `templates/` -> Jinja frontend pages
- `static/css/` -> CSS
- `models/model.h5` -> trained model file
- `uploads/` -> uploaded MRI images

## Important

You must place your trained file here:

```text
models/model.h5
```

If mail OTP is required, set environment variables before running:

```text
FLASK_SECRET_KEY=your_secret_key
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_google_app_password
USE_HTTPS=0
```
