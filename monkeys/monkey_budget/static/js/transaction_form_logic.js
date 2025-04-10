document.addEventListener('DOMContentLoaded', function() {

    const accountSelect = document.getElementById('id_account');
    const subtransactionsContainer = document.getElementById('subtransactions-container');
    const addBtn = document.getElementById('add-subtransaction');
    const totalFormsInput = document.querySelector('[name$="TOTAL_FORMS"]');
    const form = document.querySelector('form');
    const formsetPrefix = 'subtransactions'; // Prefix Twojego FormSetu

    /*
    Obsługa przecinka w kwocie subtransakcji na podstawie wybranego konta
    */
    const updatePlaceholder = (accountId) => {
        if (!accountId) return;
        // Zakładając, że appUrl jest zdefiniowane globalnie lub w skrypcie
        const apiUrl = `${appUrl}api/account-currency-info/${accountId}`;

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // Znajdź wszystkie pola amount_decimal w formsecie
                const amountInputs = subtransactionsContainer.querySelectorAll(`input[name^="${formsetPrefix}-"][name$="-amount_decimal"]`);
                amountInputs.forEach((amountInput) => {
                    amountInput.step = data.step;
                    amountInput.placeholder = data.placeholder;
                });
            })
            .catch(error => console.error('Error fetching currency info:', error));
    };

    if (accountSelect) {
        accountSelect.addEventListener('change', function() {
            updatePlaceholder(this.value);
        });

        // Wywołaj przy ładowaniu strony, jeśli konto jest już wybrane
        if (accountSelect.value) {
            updatePlaceholder(accountSelect.value);
        }
    }

    /*
    Aktualizacja indeksów i powiązań label/checkbox dla przycisków usuwania
    */
    function updateFormIndices() {
        const forms = subtransactionsContainer.querySelectorAll('.subtransaction-form');
        forms.forEach((form, index) => {
            // Aktualizacja dla checkboxa DELETE i jego labelki
            const deleteCheckbox = form.querySelector(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`);
            const deleteLabel = form.querySelector(`label[for^="id_${formsetPrefix}-"][for$="-DELETE"]`);

            if (deleteCheckbox && deleteLabel) {
                const newCheckboxId = `id_${formsetPrefix}-${index}-DELETE`;
                deleteCheckbox.id = newCheckboxId;
                deleteLabel.setAttribute('for', newCheckboxId);
            }

            // Opcjonalnie: Aktualizacja innych ID/for jeśli są potrzebne i generowane dynamicznie
        });
    }

    /*
    Obsługa przycisku dodawania nowej subtransakcji
    */
    if (addBtn && subtransactionsContainer && totalFormsInput) {
        addBtn.addEventListener('click', function() {
            const currentFormCount = parseInt(totalFormsInput.value, 10);
            const formTemplate = subtransactionsContainer.querySelector('.subtransaction-form'); // Użyj pierwszego jako szablonu

            if (formTemplate) {
                const newForm = formTemplate.cloneNode(true);

                // Usuń atrybut data-pk jeśli istnieje (bo to nowy formularz)
                newForm.removeAttribute('data-pk');

                // Wykryj prefix dynamicznie z pierwszego pola (np. amount_decimal)
                const sampleInputName = formTemplate.querySelector('input:not([type=hidden]), select, textarea')?.getAttribute('name');
                const namePrefixMatch = sampleInputName?.match(new RegExp(`^(${formsetPrefix}-\\d+)-`));

                if (!namePrefixMatch) {
                    console.error("Nie można ustalić prefixu formularza. Sprawdź nazwy pól.");
                    return; // Przerwij, jeśli nie można znaleźć wzorca
                }
                const regexPrefix = namePrefixMatch[1].replace(/\d+$/, ''); // np. "subtransactions-"

                // Aktualizacja atrybutów name, id dla wszystkich inputów, selectów, textarea
                newForm.querySelectorAll('input, select, textarea, label').forEach(el => {
                    ['name', 'id', 'for'].forEach(attr => {
                        const oldVal = el.getAttribute(attr);
                        if (oldVal && oldVal.includes(regexPrefix)) {
                            // Zastąp stary indeks nowym indeksem (currentFormCount)
                            const newVal = oldVal.replace(new RegExp(`(${regexPrefix})(\\d+)`), `$1${currentFormCount}`);
                            el.setAttribute(attr, newVal);
                        }
                    });
                });

                // Wyczyść wartości pól (oprócz ukrytych - jak ID czy DELETE)
                newForm.querySelectorAll('input:not([type=hidden]):not([type=checkbox]), textarea, select').forEach(input => {
                    input.value = '';
                });
                // Odznacz checkbox DELETE i usuń klasę wizualną
                const deleteCheckbox = newForm.querySelector(`input[name$="-DELETE"]`);
                if (deleteCheckbox) {
                    deleteCheckbox.checked = false;
                }
                newForm.classList.remove('marked-for-deletion'); // Usuń klasę wizualną (jeśli używasz)

                // Dodaj nowy formularz do kontenera
                subtransactionsContainer.appendChild(newForm);

                // Zaktualizuj TOTAL_FORMS
                totalFormsInput.value = currentFormCount + 1;

                // Zaktualizuj powiązania ID dla nowo dodanego formularza i potencjalnie poprzednich
                updateFormIndices();

                // Ponownie zastosuj logikę currency placeholder dla nowego formularza
                if (accountSelect?.value) {
                   updatePlaceholder(accountSelect.value);
                }

            } else {
                console.error("Nie znaleziono szablonu formularza subtransakcji (.subtransaction-form).");
            }
        });
    }

    /*
    Obsługa wizualnego oznaczania do usunięcia (delegacja zdarzeń)
    */
     if (subtransactionsContainer) {
        subtransactionsContainer.addEventListener('change', function(event) {
            const deleteCheckbox = event.target;
            // Sprawdź, czy zdarzenie pochodzi z checkboxa DELETE
            if (deleteCheckbox.matches(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`)) {
                const formElement = deleteCheckbox.closest('.subtransaction-form');
                const label = formElement?.querySelector(`label[for="${deleteCheckbox.id}"]`);

                if (formElement) {
                    formElement.classList.toggle('marked-for-deletion', deleteCheckbox.checked);
                }
                if (label) {
                    // Synchronizuj klasę .active Bootstrapa na labelce
                    label.classList.toggle('active', deleteCheckbox.checked);
                }
            }
        });

        /*
        Zastosuj stan początkowy przy ładowaniu strony (np. po nieudanej walidacji)
        */
        console.log("Inicjalizacja stanu wizualnego przycisków DELETE...");
        const initialDeleteCheckboxes = subtransactionsContainer.querySelectorAll(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`);
        console.log(`Znaleziono ${initialDeleteCheckboxes.length} checkboxów DELETE do sprawdzenia.`);

        initialDeleteCheckboxes.forEach((checkbox, index) => {
            const formElement = checkbox.closest('.subtransaction-form');
            // Znajdź labelkę powiązaną z checkboxem przez atrybut 'for'
            const label = formElement?.querySelector(`label[for="${checkbox.id}"]`);

            console.log(`Checkbox #${index} (ID: ${checkbox.id}): checked=${checkbox.checked}`);

            if (formElement) {
                // Użyj classList.add/remove zamiast toggle dla pewności
                if (checkbox.checked) {
                    formElement.classList.add('marked-for-deletion');
                    console.log(`  -> Dodano 'marked-for-deletion' do formElement dla checkboxa #${index}`);
                } else {
                    formElement.classList.remove('marked-for-deletion');
                }
            } else {
                console.warn(`  -> Nie znaleziono elementu .subtransaction-form dla checkboxa #${index}`);
            }

            // Synchronizuj klasę .active Bootstrapa na labelce
            if (label) {
                 if (checkbox.checked) {
                    label.classList.add('active');
                    console.log(`  -> Dodano klasę 'active' do labelki (for=${checkbox.id})`);
                 } else {
                    label.classList.remove('active');
                 }
            } else {
                 console.log(`  -> Nie znaleziono labelki dla checkboxa #${index} (szukano for=${checkbox.id})`);
            }
        });
        console.log("Zakończono inicjalizację stanu wizualnego.");

    } else {
        console.error("Nie znaleziono kontenera subtransakcji (#subtransactions-container).");
    }


    /*
    Obsługa wysyłania formularza: usuwanie TYLKO NOWYCH form oznaczonych do usunięcia
    */
    if (form) {
        form.addEventListener('submit', function(e) {
            // Znajdź NOWE formularze (bez data-pk) oznaczone do usunięcia
            const newFormsToDelete = subtransactionsContainer.querySelectorAll(`.subtransaction-form:not([data-pk]) input[name^="${formsetPrefix}-"][name$="-DELETE"]:checked`);

            newFormsToDelete.forEach(checkbox => {
                const formElement = checkbox.closest('.subtransaction-form');
                if (formElement) {
                    formElement.parentNode.removeChild(formElement);
                }
            });

            // Przelicz i zaktualizuj TOTAL_FORMS PO usunięciu nowych, niechcianych formularzy
            const remainingForms = subtransactionsContainer.querySelectorAll('.subtransaction-form');
            totalFormsInput.value = remainingForms.length;

            // Ważne: Zaktualizuj indeksy PO usunięciu, aby były ciągłe (0, 1, 2...) przed wysłaniem
            remainingForms.forEach((formElement, index) => {
                 // Wykryj prefix dynamicznie
                const sampleInputName = formElement.querySelector('input:not([type=hidden]), select, textarea')?.getAttribute('name');
                const namePrefixMatch = sampleInputName?.match(new RegExp(`^(${formsetPrefix}-\\d+)-`));
                if (!namePrefixMatch) return; // Pomiń jeśli coś jest nie tak
                const regexPrefix = namePrefixMatch[1].replace(/\d+$/, ''); // np. "subtransactions-"

                formElement.querySelectorAll('input, select, textarea, label').forEach(el => {
                    ['name', 'id', 'for'].forEach(attr => {
                        const oldVal = el.getAttribute(attr);
                        if (oldVal && oldVal.includes(regexPrefix)) {
                            const newVal = oldVal.replace(new RegExp(`(${regexPrefix})(\\d+)`), `$1${index}`);
                            el.setAttribute(attr, newVal);
                        }
                    });
                });
            });
        });
    }

    // Inicjalizacja indeksów przy pierwszym ładowaniu strony
    updateFormIndices();
});
