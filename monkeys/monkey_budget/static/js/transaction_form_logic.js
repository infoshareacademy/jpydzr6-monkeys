document.addEventListener('DOMContentLoaded', function() {

    const accountSelect = document.getElementById('id_account');
    const subtransactionsContainer = document.getElementById('subtransactions-container');
    const addBtn = document.getElementById('add-subtransaction');
    const totalFormsInput = document.querySelector('[name$="TOTAL_FORMS"]');
    const form = document.querySelector('form');
    // Dynamiczne ustalenie prefixu formsetu
    const formsetPrefix = totalFormsInput?.getAttribute('name').split('-')[0] || 'subtransactions';

    /*
    Obsługa przecinka w kwocie subtransakcji na podstawie wybranego konta
    */
    const updatePlaceholder = (accountId) => {
        if (!accountId || typeof appUrl === 'undefined') {
            if (typeof appUrl === 'undefined') console.warn("Zmienna 'appUrl' nie jest zdefiniowana globalnie.");
            return;
        }

        const apiUrl = `${appUrl}api/account-currency-info/${accountId}/`; // Poprawka: Dodano '/' na końcu URL
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!subtransactionsContainer) return;
                const amountInputs = subtransactionsContainer.querySelectorAll(`input[name^="${formsetPrefix}-"][name$="-amount_decimal"]`);
                amountInputs.forEach((amountInput) => {
                    amountInput.step = data.step || '0.01';
                    amountInput.placeholder = data.placeholder || '0.00';
                });
            })
            .catch(error => console.error('Error fetching currency info:', error));
    };

    /*
    Aktualizacja indeksów (uproszczona - może być niekompletna, jeśli HTML się zmieni)
    */
    function updateFormIndices() {
        if (!subtransactionsContainer) return;
        const forms = subtransactionsContainer.querySelectorAll('.subtransaction-form');
        forms.forEach((form, index) => {
            const deleteCheckbox = form.querySelector(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`);
            const deleteLabel = form.querySelector(`label[for^="id_${formsetPrefix}-"][for$="-DELETE"]`); // Selector może być niestabilny
            if (deleteCheckbox && deleteLabel) {
                const newCheckboxId = `id_${formsetPrefix}-${index}-DELETE`;
                // Ostrożnie z ID, Django może zarządzać nimi inaczej.
                // Jeśli label używa ID checkboxa, to aktualizacja 'for' jest kluczowa.
                deleteCheckbox.id = newCheckboxId; // Aktualizuj ID checkboxa
                deleteLabel.setAttribute('for', newCheckboxId); // Aktualizuj 'for' labelki
            }
            // Można by tu dodać aktualizację innych pól, ale pełna funkcja jest poniżej
        });
    }

    /*
    Pełna aktualizacja atrybutów formularza (bardziej niezawodna)
    */
    function updateFormAttributes(formElement, index) {
        if (!formElement) return;
        const regex = new RegExp(`(${formsetPrefix}-)(\\d+)`, 'g');
        formElement.querySelectorAll('input, select, textarea, label').forEach(el => {
            ['name', 'id', 'for'].forEach(attr => {
                const oldVal = el.getAttribute(attr);
                if (oldVal && oldVal.includes(`${formsetPrefix}-`)) {
                    const newVal = oldVal.replace(regex, `$1${index}`);
                    if (oldVal !== newVal) {
                        el.setAttribute(attr, newVal);
                    }
                }
            });
        });
    }

    // --- Funkcja do zarządzania stanem przycisków "Usuń" ---
    function updateDeleteButtonState() {
        if (!subtransactionsContainer) return;

        let nonDeletedCount = 0;
        const allForms = subtransactionsContainer.querySelectorAll('.subtransaction-form');

        // Policz, ile formularzy NIE jest zaznaczonych do usunięcia
        allForms.forEach(form => {
            const cb = form.querySelector(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`);
            if (cb && !cb.checked) {
                nonDeletedCount++;
            }
        });

        console.log(`Liczba formularzy nieoznaczonych do usunięcia: ${nonDeletedCount}`);

        // Zaktualizuj stan WSZYSTKICH przycisków/checkboxów usuwania
        allForms.forEach(form => {
            const cb = form.querySelector(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`);
            // Znajdź labelkę po ID checkboxa - to kluczowe dla poprawnego działania
            const lbl = cb ? form.querySelector(`label[for="${cb.id}"]`) : null;

            if (cb && lbl) {
                // Wyłącz kontrolki (checkbox + label), jeśli jest to JEDYNY pozostały nieoznaczony do usunięcia formularz
                const shouldDisable = (nonDeletedCount === 1 && !cb.checked);

                cb.disabled = shouldDisable;
                // Użyj klas Bootstrapa (jeśli są używane) lub własnych stylów
                lbl.classList.toggle('disabled', shouldDisable);
                // Zablokuj kliknięcia na labelce, gdy jest wyłączona
                lbl.style.pointerEvents = shouldDisable ? 'none' : '';

                // console.log(`Formularz ${cb.id}: Wyłączony = ${shouldDisable}`);
            } else if (cb && !lbl) {
                // Ostrzeżenie, jeśli nie znaleziono labelki - może wskazywać na problem w HTML
                console.warn(`Nie znaleziono labelki dla checkboxa ${cb.id}. Stan przycisku może nie być poprawnie zarządzany wizualnie.`);
                 // Mimo braku labelki, sam checkbox powinien być wyłączony
                const shouldDisable = (nonDeletedCount === 1 && !cb.checked);
                cb.disabled = shouldDisable;
            }
        });
    }


    // --- Bloki Listenerów ---

    // Listener dla zmiany konta
    if (accountSelect) {
        accountSelect.addEventListener('change', function() {
            updatePlaceholder(this.value);
        });
        // Inicjalizacja placeholderów przy ładowaniu strony, jeśli konto jest wybrane
        if (accountSelect.value) {
            updatePlaceholder(accountSelect.value);
        }
    }

    // Listener dla przycisku dodawania
    if (addBtn && subtransactionsContainer && totalFormsInput) {
        addBtn.addEventListener('click', function() {
            const currentFormCount = parseInt(totalFormsInput.value, 10);

            // --- ZMIANA 1: Znajdź szablon po ID ---
            const templateId = `${formsetPrefix}-empty-form`;
            const formTemplate = document.getElementById(templateId);

            if (formTemplate) {
                // --- ZMIANA 2: Klonuj szablon, usuń jego ID i uczyń widocznym ---
                const newForm = formTemplate.cloneNode(true); // Klonuj szablon div
                newForm.removeAttribute('id');                 // Usuń ID '...-empty-form' z klona
                newForm.style.display = '';                  // Usuń 'display: none;' aby był widoczny

                // --- ZMIANA 3: Zaktualizuj atrybuty zamieniając '__prefix__' na indeks ---
                const indexRegex = new RegExp('__prefix__', 'g');
                // Przejdź przez WSZYSTKIE elementy potomne w sklonowanym formularzu
                newForm.querySelectorAll('*').forEach(el => {
                    ['name', 'id', 'for'].forEach(attr => {
                        const oldValue = el.getAttribute(attr);
                        // Jeśli atrybut istnieje i zawiera placeholder '__prefix__'
                        if (oldValue && oldValue.includes('__prefix__')) {
                            // Zamień placeholder na aktualny indeks (numer formularza)
                            const newValue = oldValue.replace(indexRegex, currentFormCount);
                            el.setAttribute(attr, newValue);
                        }
                    });
                });

                // --- ZMIANA 4 (bez zmian w kodzie, ale ważne): Czyszczenie wartości ---
                // Ten kod powinien działać, czyści pola w nowym formularzu.
                newForm.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=button]):not([type=submit]), textarea, select').forEach(input => {
                    if(input.type !== 'radio') { input.value = ''; }
                });
                newForm.querySelectorAll('input[type=checkbox], input[type=radio]').forEach(input => { input.checked = false; });

                // Upewnij się, że checkbox DELETE jest odznaczony i AKTYWNY w nowym formularzu
                const deleteCheckbox = newForm.querySelector(`input[name$="-DELETE"]`);
                if (deleteCheckbox) {
                    deleteCheckbox.checked = false;
                    deleteCheckbox.disabled = false; // Nowy formularz zawsze ma aktywny przycisk usuwania
                    const deleteLabel = newForm.querySelector(`label[for="${deleteCheckbox.id}"]`);
                    if (deleteLabel) {
                        deleteLabel.classList.remove('active', 'disabled'); // Usuń klasy stanu
                        deleteLabel.style.pointerEvents = ''; // Zresetuj styl
                    }
                }
                newForm.classList.remove('marked-for-deletion'); // Usuń klasę wizualną jeśli była skopiowana

                // Dodanie nowego formularza do kontenera na stronie
                subtransactionsContainer.appendChild(newForm);
                // Aktualizacja liczby formularzy w polu zarządzania formsetem
                totalFormsInput.value = currentFormCount + 1;

                // Aktualizacja placeholderów (np. formatu waluty) dla nowego formularza
                if (accountSelect?.value) {
                    updatePlaceholder(accountSelect.value);
                }

                // --- ZMIANA 5: Zawsze aktualizuj stan przycisków po dodaniu ---
                updateDeleteButtonState(); // Sprawdź, czy np. przycisk pierwszego formularza ma być włączony

            } else {
                // Komunikat błędu, jeśli szablon nie został znaleziony
                console.error(`Nie znaleziono szablonu formularza o ID "${templateId}". Upewnij się, że istnieje w HTML.`);
            }
        });
    }

    // Listener dla zmian w kontenerze (wizualne oznaczanie + logika dezaktywacji)
    if (subtransactionsContainer) {
        subtransactionsContainer.addEventListener('change', function(event) {
            const changedCheckbox = event.target;

            // Sprawdź, czy zdarzenie pochodzi z checkboxa DELETE
            if (changedCheckbox.matches(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`)) {
                const formElement = changedCheckbox.closest('.subtransaction-form');
                const label = formElement?.querySelector(`label[for="${changedCheckbox.id}"]`); // Kluczowe jest znalezienie labelki po ID

                // --- Istniejąca logika do przełączania stanu wizualnego ---
                if (formElement) {
                    formElement.classList.toggle('marked-for-deletion', changedCheckbox.checked);
                }
                if (label) {
                    // Synchronizuj klasę .active Bootstrapa (jeśli używana) na labelce
                    label.classList.toggle('active', changedCheckbox.checked);
                }
                // --- Koniec logiki wizualnej ---

                // --- NOWA LOGIKA: Sprawdź i zaktualizuj stan przycisków "Usuń" ---
                updateDeleteButtonState(); // Wywołaj funkcję zarządzającą stanem
            }
        });

        /*
        Zastosuj stan początkowy wizualny przy ładowaniu strony
        */
        console.log("Inicjalizacja stanu wizualnego przycisków DELETE...");
        const initialDeleteCheckboxes = subtransactionsContainer.querySelectorAll(`input[name^="${formsetPrefix}-"][name$="-DELETE"]`);
        initialDeleteCheckboxes.forEach(checkbox => {
            const formElement = checkbox.closest('.subtransaction-form');
            const label = formElement?.querySelector(`label[for="${checkbox.id}"]`);

            if (formElement) {
                formElement.classList.toggle('marked-for-deletion', checkbox.checked);
            }
            if (label) {
                label.classList.toggle('active', checkbox.checked);
            }
        });
        console.log("Zakończono inicjalizację stanu wizualnego.");

    } else {
        console.error("Nie znaleziono kontenera subtransakcji (#subtransactions-container).");
    }

    // Listener dla wysyłania formularza
    if (form) {
        form.addEventListener('submit', function(e) {
            // Usunięcie NOWYCH formularzy oznaczonych do usunięcia (tych bez data-pk)
            if (subtransactionsContainer) {
                const newFormsToDelete = subtransactionsContainer.querySelectorAll(`.subtransaction-form:not([data-pk]) input[name^="${formsetPrefix}-"][name$="-DELETE"]:checked`);
                newFormsToDelete.forEach(checkbox => {
                    const formElement = checkbox.closest('.subtransaction-form');
                    // Dodatkowe sprawdzenie, czy element faktycznie jest dzieckiem kontenera
                    if (formElement && formElement.parentNode === subtransactionsContainer) {
                         console.log(`Usuwanie nowego formularza oznaczonego do usunięcia (bez PK) z DOM: ${formElement.querySelector('input, select, textarea')?.name || 'brak nazwy'}`);
                         subtransactionsContainer.removeChild(formElement);
                    }
                });
            }

            // Przeliczenie i aktualizacja TOTAL_FORMS oraz reindeksacja pozostałych
            const remainingForms = subtransactionsContainer ? subtransactionsContainer.querySelectorAll('.subtransaction-form') : [];
            if (totalFormsInput) {
                totalFormsInput.value = remainingForms.length;
                console.log(`Aktualizacja TOTAL_FORMS na: ${remainingForms.length}`);
            }

            // Reindeksacja pozostałych formularzy (używając pełnej funkcji)
            remainingForms.forEach((formElement, index) => {
                 console.log(`Reindeksacja formularza ${index}`);
                 updateFormAttributes(formElement, index);
            });

            // *** WAŻNE: Bezpośrednio przed wysłaniem, upewnijmy się, że stan przycisków jest poprawny ***
            console.log("Sprawdzanie stanu przycisków 'Usuń' przed wysłaniem...");
            updateDeleteButtonState(); // Ponownie sprawdź i ustaw stan przycisków

            console.log("Formularz gotowy do wysłania.");
            // e.preventDefault(); // Odkomentuj, aby zatrzymać wysyłanie i sprawdzić konsole/stan formularza
        });
    }

    // --- Inicjalizacja przy ładowaniu strony ---
    // Wywołaj inicjalizację stanu przycisków PO inicjalizacji stanu wizualnego
    function initializeDeleteButtonState() {
        console.log("Inicjalizacja stanu przycisków usuwania...");
        updateDeleteButtonState(); // Użyj głównej funkcji do ustawienia stanu początkowego
        console.log("Zakończono inicjalizację stanu przycisków usuwania.");
    }

    // Wywołanie funkcji inicjującej stan przycisków na końcu ładowania DOM
    if (subtransactionsContainer) { // Upewnij się, że kontener istnieje przed inicjalizacją
       initializeDeleteButtonState();
    }

    console.log("Logika formularza transakcji zainicjalizowana.");
});
