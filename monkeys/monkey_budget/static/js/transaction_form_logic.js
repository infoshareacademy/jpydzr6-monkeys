document.addEventListener('DOMContentLoaded', function() {
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
});

