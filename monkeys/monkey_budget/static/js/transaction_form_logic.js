document.addEventListener('DOMContentLoaded', function() {
/*
Obsługa przecinka w kwotcie subtransakcji na podstawie wybranego konta
 */
    const accountSelect = document.getElementById('id_account');

    const updatePlaceholder = (accountId) => {
        if (!accountId) return;

        const apiUrl = appUrl+'api/account-currency-info/'+accountId
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // Znajdź wszystkie pola amount_decimal w formsecie
                const transactionForms = document.querySelectorAll('[id^="id_subtransactions-"][id$="-amount_decimal"]');

                transactionForms.forEach((amountInput) => {
                    // Ustaw dynamicznie step i placeholder dla każdego pola
                    amountInput.step = data.step;
                    amountInput.placeholder = data.placeholder;
                });
            })
            .catch(error => console.error('Error fetching currency info:', error));
    };

    accountSelect.addEventListener('change', function() {
        updatePlaceholder(this.value);
    });

    if (accountSelect.value) {
        updatePlaceholder(accountSelect.value);
    }

/*
Obsługa przycisków dodawania i usuwania subtransakcji oraz powiązanego z tym dodawania formularzy subtransakcji
 */
    const addBtn = document.getElementById('add-subtransaction');
    const container = document.getElementById('subtransactions-container');
    const totalForms = document.querySelector('[name$="TOTAL_FORMS"]');

    // Funkcja dostosowująca id przycisków po dodaniu nowego formularza
    function updateToggleButtonIds() {
        const forms = document.querySelectorAll('.subtransaction-form');
        forms.forEach((form, index) => {
            const deleteCheckbox = form.querySelector('.btn-check');
            const deleteLabel = form.querySelector('.btn-outline-danger');

            if (deleteCheckbox && deleteLabel) {
                const newId = `delete-check-${index + 1}`;
                deleteCheckbox.id = newId;
                deleteLabel.setAttribute('for', newId);
            }
        });
    }

    // 2. Obsługa przycisku dodawania
    addBtn.addEventListener('click', function() {
        // Pobierz aktualną liczbę formularzy
        const formCount = parseInt(totalForms.value);

        // Sklonuj pierwszy formularz
        const firstForm = container.querySelector('.subtransaction-form');

        if (firstForm) {
            const newForm = firstForm.cloneNode(true);

            // Aktualizacja ID i nazw pól
            newForm.innerHTML = newForm.innerHTML.replace(
                new RegExp('(subtransactions-\\d+|id_subtransactions-\\d+)', 'g'),
                function (match) {
                    return match.replace(/\d+/, formCount);
                }
            );

            // Wyczyść wartości
            newForm.querySelectorAll('input:not([type=hidden]), textarea, select').forEach(input => {
                input.value = '';
            });

            // Upewnij się, że checkbox DELETE nie jest zaznaczony
            const deleteCheckbox = newForm.querySelector('[name$="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.checked = false;
            }

            // Resetuj wygląd
            newForm.style.opacity = '1';
            newForm.classList.remove('marked-delete');
            const deleteBtn = newForm.querySelector('.btn-delete');
            if (deleteBtn) {
                deleteBtn.textContent = 'Usuń';
            }

            // Dodaj nowy formularz do kontenera
            container.appendChild(newForm);

            // Zwiększ licznik formularzy
            totalForms.value = formCount + 1;

            // Dodaj obsługę przycisku usuwania do nowego formularza
            updateToggleButtonIds();
        }
    });

    // Inicjalizacja obsługi przycisków usuwania
    updateToggleButtonIds();

/*
Czyszczenie nowych formularzy, które mają jednak być usunięte
 */
    const form = document.querySelector('form');

    form.addEventListener('submit', function(e) {
        // Znajdź wszystkie nowe formularze oznaczone do usunięcia
        const newForms = document.querySelectorAll('.subtransaction-form:not([data-pk]) input[name$="-DELETE"]:checked');

        // Usuń całe formularze z DOM przed wysłaniem
        newForms.forEach(checkbox => {
            const formElement = checkbox.closest('.subtransaction-form');
            formElement.parentNode.removeChild(formElement);
        });

        // Zrekalkuluj TOTAL_FORMS
        const totalFormsInput = document.querySelector('[name$="TOTAL_FORMS"]');
        totalFormsInput.value = document.querySelectorAll('.subtransaction-form').length;
    });


});