/**
 * Category filtering functionality for transaction forms
 * 
 * This script handles the dynamic loading of categories based on the selected
 * transaction direction. It fetches categories from the server and updates
 * the category dropdowns in the transaction form.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the transaction direction select element
    const directionSelect = document.getElementById('id_transaction_direction');
    
    if (!directionSelect) {
        return; // Exit if the element doesn't exist
    }
    
    // Store initial category values for each subtransaction form
    const initialCategories = {};
    document.querySelectorAll('.subtransaction-form').forEach((form, index) => {
        const categorySelect = form.querySelector('.category-select');
        if (categorySelect) {
            initialCategories[index] = categorySelect.value;
        }
    });
    
    // Function to update categories based on transaction direction
    function updateCategories(direction) {
        // Get all category select elements
        const categorySelects = document.querySelectorAll('.category-select');
        
        // Disable all category selects while loading
        categorySelects.forEach(select => {
            select.disabled = true;
        });
        
        // Fetch categories from the server
        fetch(`/api/categories/${direction}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update each category select with the new options
                categorySelects.forEach((select, index) => {
                    // Clear existing options
                    select.innerHTML = '';
                    
                    // Add a default empty option
                    const defaultOption = document.createElement('option');
                    defaultOption.value = '';
                    defaultOption.textContent = 'Wybierz kategorię';
                    select.appendChild(defaultOption);
                    
                    // Add new options from the server response
                    data.categories.forEach(category => {
                        const option = document.createElement('option');
                        option.value = category.id;
                        option.textContent = `${category.main_category_name} - ${category.name}`;
                        select.appendChild(option);
                    });
                    
                    // Restore the initial value if it exists
                    if (initialCategories[index] && initialCategories[index] !== '') {
                        select.value = initialCategories[index];
                    }
                    
                    // Re-enable the select
                    select.disabled = false;
                });
            })
            .catch(error => {
                console.error('Error fetching categories:', error);
                // Re-enable selects even if there was an error
                categorySelects.forEach(select => {
                    select.disabled = false;
                });
            });
    }
    
    // Check if we have an initial direction from the server
    if (typeof initialDirection !== 'undefined') {
        // Set the direction select to the initial value
        directionSelect.value = initialDirection;
        // Update categories with the initial direction
        updateCategories(initialDirection);
    } else {
        // Update categories when the page loads with the current direction
        updateCategories(directionSelect.value);
    }
    
    // Update categories when the transaction direction changes
    directionSelect.addEventListener('change', function() {
        // Clear initial categories when direction changes
        initialCategories.length = 0;
        updateCategories(this.value);
    });
    
    // Function to handle adding new subtransaction forms
    function handleNewSubtransactionForm() {
        // Get the add subtransaction button
        const addButton = document.getElementById('add-subtransaction');
        
        if (!addButton) {
            return; // Exit if the element doesn't exist
        }
        
        // Add event listener to the add button
        addButton.addEventListener('click', function() {
            // Wait for the new form to be added to the DOM
            setTimeout(() => {
                // Get the newly added category select
                const newCategorySelect = document.querySelector('.subtransaction-form:last-child .category-select');
                
                if (newCategorySelect) {
                    // Update the categories for the new select
                    updateCategories(directionSelect.value);
                }
            }, 100); // Small delay to ensure the DOM has been updated
        });
    }
    
    // Initialize the add subtransaction handler
    handleNewSubtransactionForm();
}); 