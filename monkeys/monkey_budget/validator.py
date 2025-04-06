from django.core.exceptions import ValidationError


def validate_file_size(value):
    max_size_mb = 3
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Plik jest za duży! Maksymalny rozmiar to {max_size_mb} MB.")
