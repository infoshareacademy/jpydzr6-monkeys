# jpydzr6-monkeys

# Set the SECRET_KEY

The secret key is not included in the repository, the user must provide it itself following these steps:
- In the directory `monkeys/monkeys/` create an `.env` file
- In this file save the key: `SECRET_KEY='your_secret_key'`. Remember the single quotation mark for the key itself.  

# Monetary class

This is a class for basic monetary/money operations. In its core it operates in the smallest unit of a currency (called
minor unit).

The class is inspired by dinero.js library [dinero.js v2](https://v2.dinerojs.com/docs) library and its
fork [wilfredinni/dinero](https://wilfredinni.github.io/dinero/)

## Currencies

The class functions expects as the second argument a dictionary of specific currency. In the beginning there are
attached three currencies.

## Instantiating a monetary objects and allowed operations

- Instantiating
  ```
  pln1 = Monetary(1, PLN)
  pln2 = Monetary(Monetary.major_to_minor_unit(100.0, PLN), PLN)
  ```
  `m1 = PLN 0.01, m2 = PLN 100.00`
- Adding `pln3 = pln1 + pln2`
- Subtracting `pln3 = pln2 - pln1`
- Multiplying `pln3 = pln2 * 2` (the Monetary object must be on the left side of equation)
- Dividing `pln3 = pln2 / 2` (the Monetary object must be on the left side of equation)
- The result of division result is rounded. If it is less than the minor unit, the result will be zero `pln3 = pln1 / 2`
- Combining currencies will result in error
  ```
  eur1 = Monetary(100, EUR)
  some = pln1 + eur1
  ```
  *AttributeError: The currencies does not match*

## Major to minor unit conversion

If there is a need it is possible to convert major unit (typed as int, float or string) to the minor one of chosen
currency

- `Monetary.major_to_minor_unit(1, PLN)` will give in result (int) `100`
- `Monetary.major_to_minor_unit(1.11, PLN)` will give in result (int) `111`
- `Monetary.major_to_minor_unit(1.2, PLN)` will give in result (int) `120`
- `Monetary.major_to_minor_unit("1.34", PLN)` will give in result (int) `134`
- `Monetary.major_to_minor_unit("1.567", PLN)` will give in result (int) `156`


## Translations 

To localise applikaction we have use rosetta with deepl translate API

apt-get install gettext

python manage.py makemessages -l en -l pl

# Monkey Budget

A Django-based budget management application.

## Features

- User authentication with email verification
- Account management
- Transaction tracking
- Multi-currency support
- Responsive design with Bootstrap 5
- Internationalization support (English and Polish)

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your-secret-key
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-specific-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Translations

The application supports multiple languages (English and Polish) using Django's internationalization framework and Rosetta for translation management.

### Prerequisites

1. Install gettext (required for translation tools):
   ```bash
   # On Debian/Ubuntu:
   sudo apt-get install gettext
   
### Translation Workflow

1. Generate message files for translation:
   ```bash
   python manage.py makemessages -l en -l pl
   ```
   This will create/update `.po` files in `monkeys/locale/<language_code>/LC_MESSAGES/django.po`

2. Translate the strings:
   - Access the Rosetta interface at `/rosetta/` (requires admin access)
   - Or edit the `.po` files directly in a text editor
   - Each string has a `msgid` (original text) and `msgstr` (translation)
   - Add translations for each language

3. Compile the translations:
   ```bash
   python manage.py compilemessages
   ```
   This will create `.mo` files from the `.po` files

4. Restart the Django server to apply changes

### Translation Files Structure

```
monkeys/
└── locale/
    ├── en/
    │   └── LC_MESSAGES/
    │       ├── django.po
    │       └── django.mo
    └── pl/
        └── LC_MESSAGES/
            ├── django.po
            └── django.mo
```

### Adding New Translatable Strings

1. In templates:
   ```html
   {% load i18n %}
   {% trans "Your text here" %}
   ```

2. In Python code:
   ```python
   from django.utils.translation import gettext as _
   message = _("Your text here")
   ```

### Translation Context

When translating strings, you can provide context to help translators:
```html
{% trans "Login" context "login" %}
```

### Common Issues

1. If translations don't appear:
   - Make sure `django.middleware.locale.LocaleMiddleware` is in MIDDLEWARE
   - Check that `USE_I18N = True` in settings.py
   - Verify that the language code is in `LANGUAGES` setting
   - Ensure `.mo` files are compiled

2. If Rosetta interface is not accessible:
   - Make sure you're logged in as a superuser
   - Check that 'rosetta' is in INSTALLED_APPS
   - Verify the URL pattern is correctly configured


