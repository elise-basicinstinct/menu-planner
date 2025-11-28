document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('planForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const warnings = document.getElementById('warnings');
    const menuContent = document.getElementById('menuContent');
    const shoppingContent = document.getElementById('shoppingContent');

    // Recipe import elements
    const recipeUrlInput = document.getElementById('recipeUrl');
    const importBtn = document.getElementById('importBtn');
    const importedRecipesContainer = document.getElementById('importedRecipes');
    const addToMenuModal = document.getElementById('addToMenuModal');
    const addToMenuMessage = document.getElementById('addToMenuMessage');
    const addToMenuYes = document.getElementById('addToMenuYes');
    const addToMenuNo = document.getElementById('addToMenuNo');
    const saveRecipesModal = document.getElementById('saveRecipesModal');
    const saveRecipesMessage = document.getElementById('saveRecipesMessage');
    const saveRecipesYes = document.getElementById('saveRecipesYes');
    const saveRecipesNo = document.getElementById('saveRecipesNo');

    let importedRecipes = [];
    let hasGeneratedPlan = false;
    let currentImportedRecipe = null;

    // Recipe import button handler
    importBtn.addEventListener('click', async function() {
        const url = recipeUrlInput.value.trim();

        if (!url) {
            alert('Please enter a recipe URL');
            return;
        }

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            alert('Please enter a valid URL starting with http:// or https://');
            return;
        }

        await importRecipeFromURL(url);
    });

    // Allow Enter key to import recipe
    recipeUrlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            importBtn.click();
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous results
        results.classList.add('hidden');
        warnings.classList.add('hidden');
        
        // Show loading
        loading.classList.remove('hidden');
        
        // Get form data
        const formData = {
            household_size: parseInt(document.getElementById('household_size').value),
            nights: parseInt(document.getElementById('nights').value),
            cooking_time_preference: document.getElementById('cooking_time_preference').value
        };
        
        try {
            // Make API request
            const response = await fetch('/api/generate-plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate plan');
            }
            
            // Hide loading
            loading.classList.add('hidden');
            
            // Display warnings if any
            if (data.warnings && data.warnings.length > 0) {
                warnings.innerHTML = data.warnings.map(w => `<p>⚠️ ${w}</p>`).join('');
                warnings.classList.remove('hidden');
            }
            
            // Display menu
            displayMenu(data.menu);
            
            // Display shopping list
            displayShoppingList(data.shopping_list);

            // Show results
            results.classList.remove('hidden');

            // Mark that plan has been generated
            hasGeneratedPlan = true;

            // Scroll to results
            results.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            loading.classList.add('hidden');
            alert('Error: ' + error.message);
        }
    });
    
    function displayMenu(menu) {
        menuContent.innerHTML = menu.map((recipe, index) => `
            <div class="recipe-card">
                <div class="recipe-header">
                    <div class="recipe-title">Night ${index + 1}: ${recipe.name}</div>
                    <div class="recipe-meta">
                        <span>⏱️ ${recipe.cooking_time}</span>
                        <span>👥 ${recipe.scaled_servings} servings</span>
                    </div>
                </div>
                
                <div class="ingredients-list">
                    <h3>Ingredients:</h3>
                    <ul>
                        ${recipe.ingredients.map(ing => `
                            <li>
                                <span class="shopping-item-name">${ing.name}</span>
                                <span class="shopping-item-amount">${ing.amount} ${ing.unit}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                
                ${recipe.steps ? `
                    <div class="steps-list">
                        <h3>Cooking Steps:</h3>
                        <ol>
                            ${recipe.steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    function displayShoppingList(shoppingList) {
        const sortedItems = Object.entries(shoppingList).sort((a, b) => a[0].localeCompare(b[0]));

        shoppingContent.innerHTML = `
            <div class="shopping-list">
                <ul>
                    ${sortedItems.map(([name, details]) => `
                        <li>
                            <div class="shopping-item">
                                <span class="shopping-item-name">${name}</span>
                                <span class="shopping-item-amount">${details.amount} ${details.unit}</span>
                            </div>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    async function importRecipeFromURL(url) {
        // Disable button and show loading state
        importBtn.disabled = true;
        importBtn.textContent = 'Importing...';

        try {
            const response = await fetch('/api/import-recipe-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to import recipe');
            }

            // Store the current imported recipe
            currentImportedRecipe = data.recipe;

            // Add to imported recipes list
            importedRecipes.push(data.recipe);

            // Display the imported recipe
            displayImportedRecipe(data.recipe);

            // Clear the input
            recipeUrlInput.value = '';

            // Show success message
            showToast(`✓ Imported: ${data.recipe.name}`, 'success');

            // Ask if they want to add to this week's menu
            showAddToMenuModal(data.recipe);

        } catch (error) {
            showToast(`✗ ${error.message}`, 'error');
        } finally {
            // Re-enable button
            importBtn.disabled = false;
            importBtn.textContent = 'Import Recipe';
        }
    }

    function displayImportedRecipe(recipe) {
        const recipeCard = document.createElement('div');
        recipeCard.className = 'imported-recipe-card';
        recipeCard.dataset.recipeId = recipe.id;

        recipeCard.innerHTML = `
            <div class="imported-recipe-header">
                <span class="imported-recipe-name">✓ ${recipe.name}</span>
                <button class="remove-recipe-btn" onclick="removeImportedRecipe(${recipe.id})">×</button>
            </div>
            <div class="imported-recipe-meta">
                <span>⏱️ ${recipe.cooking_time}</span>
                <span>👥 ${recipe.servings} servings</span>
                <span>🥘 ${recipe.ingredients.length} ingredients</span>
            </div>
        `;

        importedRecipesContainer.appendChild(recipeCard);
    }

    // Make removeImportedRecipe available globally
    window.removeImportedRecipe = async function(recipeId) {
        // Remove from imported recipes array
        importedRecipes = importedRecipes.filter(r => r.id !== recipeId);

        // Remove from DOM
        const card = document.querySelector(`[data-recipe-id="${recipeId}"]`);
        if (card) {
            card.remove();
        }

        // If no more imported recipes, clear the container
        if (importedRecipes.length === 0) {
            importedRecipesContainer.innerHTML = '';
        }
    };

    function showAddToMenuModal(recipe) {
        addToMenuMessage.textContent = `Would you like to add "${recipe.name}" to this week's meal plan?`;
        addToMenuModal.classList.remove('hidden');
    }

    function showSaveRecipesModal(recipe) {
        saveRecipesMessage.textContent = `Would you like to save "${recipe.name}" permanently to your recipe collection?`;
        saveRecipesModal.classList.remove('hidden');
    }

    addToMenuYes.addEventListener('click', async function() {
        // Hide the add to menu modal
        addToMenuModal.classList.add('hidden');

        // Auto-generate a plan with the imported recipe
        // Set nights to 1 if not already set
        const nightsInput = document.getElementById('nights');
        if (!nightsInput.value || nightsInput.value == '0') {
            nightsInput.value = '1';
        }

        // Automatically trigger plan generation
        await generatePlanWithImportedRecipe();

        // Then ask if they want to save it permanently
        showSaveRecipesModal(currentImportedRecipe);
    });

    async function generatePlanWithImportedRecipe() {
        // Show loading
        loading.classList.remove('hidden');
        results.classList.add('hidden');

        // Get form data
        const formData = {
            household_size: parseInt(document.getElementById('household_size').value),
            nights: parseInt(document.getElementById('nights').value),
            cooking_time_preference: document.getElementById('cooking_time_preference').value
        };

        try {
            // Make API request
            const response = await fetch('/api/generate-plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate plan');
            }

            // Hide loading
            loading.classList.add('hidden');

            // Display warnings if any
            if (data.warnings && data.warnings.length > 0) {
                warnings.innerHTML = data.warnings.map(w => `<p>⚠️ ${w}</p>`).join('');
                warnings.classList.remove('hidden');
            }

            // Display menu
            displayMenu(data.menu);

            // Display shopping list
            displayShoppingList(data.shopping_list);

            // Show results
            results.classList.remove('hidden');

            // Mark that plan has been generated
            hasGeneratedPlan = true;

            // Show success toast
            showToast('✓ Menu plan generated with your imported recipe!', 'success');

            // Scroll to results
            results.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            loading.classList.add('hidden');
            showToast(`✗ ${error.message}`, 'error');
        }
    }

    addToMenuNo.addEventListener('click', function() {
        // Hide the add to menu modal
        addToMenuModal.classList.add('hidden');

        // Still ask if they want to save it permanently
        showSaveRecipesModal(currentImportedRecipe);
    });

    saveRecipesYes.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/save-temp-recipes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to save recipes');
            }

            showToast(`✓ Saved to all recipes permanently`, 'success');

            // Hide modal
            saveRecipesModal.classList.add('hidden');

        } catch (error) {
            showToast(`✗ ${error.message}`, 'error');
        }
    });

    saveRecipesNo.addEventListener('click', function() {
        // Don't save permanently, but keep it for this week's menu
        showToast('✓ Recipe available for this week only', 'info');

        // Hide modal
        saveRecipesModal.classList.add('hidden');
    });

    function showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        // Add to body
        document.body.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});


