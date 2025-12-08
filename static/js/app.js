document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('planForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const warnings = document.getElementById('warnings');
    const menuContent = document.getElementById('menuContent');
    const shoppingContent = document.getElementById('shoppingContent');

    // Recipe selection tabs
    const myRecipesTab = document.getElementById('myRecipesTab');
    const importUrlTab = document.getElementById('importUrlTab');
    const aiAssistantTab = document.getElementById('aiAssistantTab');
    const myRecipesSection = document.getElementById('myRecipesSection');
    const importUrlSection = document.getElementById('importUrlSection');
    const aiAssistantSection = document.getElementById('aiAssistantSection');
    const myRecipesDropdown = document.getElementById('myRecipesDropdown');
    const addFromLibraryBtn = document.getElementById('addFromLibraryBtn');

    // Recipe import elements
    const recipeUrlInput = document.getElementById('recipeUrl');
    const importBtn = document.getElementById('importBtn');
    const importedRecipesContainer = document.getElementById('importedRecipes');
    const saveRecipesModal = document.getElementById('saveRecipesModal');
    const saveRecipesList = document.getElementById('saveRecipesList');
    const saveRecipesSubmit = document.getElementById('saveRecipesSubmit');
    const saveRecipesSkip = document.getElementById('saveRecipesSkip');

    // AI chat elements
    const aiChatInput = document.getElementById('aiChatInput');
    const aiChatSend = document.getElementById('aiChatSend');
    const chatMessages = document.getElementById('chatMessages');
    const aiSuggestedRecipes = document.getElementById('aiSuggestedRecipes');

    let importedRecipes = [];
    let hasGeneratedPlan = false;
    let libraryRecipes = [];
    let chatHistory = [];

    // Load recipes from library
    loadLibraryRecipes();

    // Tab switching
    myRecipesTab.addEventListener('click', function() {
        myRecipesTab.classList.add('active');
        importUrlTab.classList.remove('active');
        aiAssistantTab.classList.remove('active');
        myRecipesSection.classList.remove('hidden');
        importUrlSection.classList.add('hidden');
        aiAssistantSection.classList.add('hidden');
    });

    importUrlTab.addEventListener('click', function() {
        importUrlTab.classList.add('active');
        myRecipesTab.classList.remove('active');
        aiAssistantTab.classList.remove('active');
        importUrlSection.classList.remove('hidden');
        myRecipesSection.classList.add('hidden');
        aiAssistantSection.classList.add('hidden');
    });

    aiAssistantTab.addEventListener('click', function() {
        aiAssistantTab.classList.add('active');
        myRecipesTab.classList.remove('active');
        importUrlTab.classList.remove('active');
        aiAssistantSection.classList.remove('hidden');
        myRecipesSection.classList.add('hidden');
        importUrlSection.classList.add('hidden');
    });

    // Add recipes from library
    addFromLibraryBtn.addEventListener('click', function() {
        const selectedOptions = Array.from(myRecipesDropdown.selectedOptions);

        if (selectedOptions.length === 0) {
            showToast('Please select at least one recipe', 'info');
            return;
        }

        selectedOptions.forEach(option => {
            const recipeId = parseInt(option.value);
            const recipe = libraryRecipes.find(r => r.id === recipeId);

            if (recipe && !importedRecipes.find(r => r.id === recipeId)) {
                importedRecipes.push(recipe);
                displayImportedRecipeChip(recipe);
            }
        });

        // Clear selection
        myRecipesDropdown.selectedIndex = -1;
        showToast(`Added ${selectedOptions.length} recipe(s) to your meal plan`, 'success');
    });

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

    // AI chat send button handler
    aiChatSend.addEventListener('click', async function() {
        await sendAIChatMessage();
    });

    // Allow Enter key to send AI chat message
    aiChatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            aiChatSend.click();
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
            cooking_time_preference: document.getElementById('cooking_time_preference').value,
            selected_recipe_ids: importedRecipes.map(r => r.id)
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

            // Show save recipes modal if there are imported recipes
            if (importedRecipes.length > 0) {
                // Small delay so user can see the plan first
                setTimeout(() => {
                    showSaveRecipesModal();
                }, 500);
            }

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

            // Add to imported recipes list
            importedRecipes.push(data.recipe);

            // Display the imported recipe as a chip
            displayImportedRecipeChip(data.recipe);

            // Clear the input
            recipeUrlInput.value = '';

            // Show success message
            showToast(`✓ Imported: ${data.recipe.name}`, 'success');

        } catch (error) {
            showToast(`✗ ${error.message}`, 'error');
        } finally {
            // Re-enable button
            importBtn.disabled = false;
            importBtn.textContent = '+ Import';
        }
    }

    function displayImportedRecipeChip(recipe) {
        const chip = document.createElement('div');
        chip.className = 'recipe-chip';
        chip.dataset.recipeId = recipe.id;

        chip.innerHTML = `
            <span class="recipe-chip-name">${recipe.name}</span>
            <span class="recipe-chip-meta">(${recipe.cooking_time})</span>
            <button class="chip-remove-btn" onclick="removeImportedRecipe(${recipe.id})">×</button>
        `;

        importedRecipesContainer.appendChild(chip);
    }

    // Make removeImportedRecipe available globally
    window.removeImportedRecipe = async function(recipeId) {
        // Remove from imported recipes array
        importedRecipes = importedRecipes.filter(r => r.id !== recipeId);

        // Remove from DOM
        const chip = document.querySelector(`[data-recipe-id="${recipeId}"]`);
        if (chip) {
            chip.remove();
        }
    };

    function showSaveRecipesModal() {
        if (importedRecipes.length === 0) {
            return;
        }

        // Clear previous list
        saveRecipesList.innerHTML = '';

        // Add checkbox for each imported recipe
        importedRecipes.forEach(recipe => {
            const item = document.createElement('div');
            item.className = 'save-recipe-item';
            item.innerHTML = `
                <label>
                    <input type="checkbox" checked data-recipe-id="${recipe.id}">
                    <span class="save-recipe-name">${recipe.name}</span>
                </label>
            `;
            saveRecipesList.appendChild(item);
        });

        saveRecipesModal.classList.remove('hidden');
    }

    saveRecipesSubmit.addEventListener('click', async function() {
        // Get selected recipe IDs
        const checkboxes = saveRecipesList.querySelectorAll('input[type="checkbox"]:checked');
        const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.recipeId));

        if (selectedIds.length === 0) {
            showToast('✓ No recipes saved', 'info');
            saveRecipesModal.classList.add('hidden');
            clearImportedRecipes();
            return;
        }

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

            showToast(`✓ Saved ${selectedIds.length} recipe(s) permanently`, 'success');

            // Hide modal
            saveRecipesModal.classList.add('hidden');

            // Clear imported recipes
            clearImportedRecipes();

        } catch (error) {
            showToast(`✗ ${error.message}`, 'error');
        }
    });

    saveRecipesSkip.addEventListener('click', function() {
        // Don't save permanently
        showToast('✓ Recipes not saved', 'info');

        // Hide modal
        saveRecipesModal.classList.add('hidden');

        // Clear imported recipes
        clearImportedRecipes();
    });

    function clearImportedRecipes() {
        importedRecipes = [];
        importedRecipesContainer.innerHTML = '';
    }

    async function loadLibraryRecipes() {
        try {
            const response = await fetch('/api/recipes');

            if (!response.ok) {
                throw new Error('Failed to load recipes');
            }

            libraryRecipes = await response.json();

            // Populate dropdown
            myRecipesDropdown.innerHTML = '';

            if (libraryRecipes.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.disabled = true;
                option.textContent = 'No recipes in library yet';
                myRecipesDropdown.appendChild(option);
            } else {
                libraryRecipes.forEach(recipe => {
                    const option = document.createElement('option');
                    option.value = recipe.id;

                    // Format: Recipe Name (Quick/Long, X servings)
                    const cookingTimeLabel = recipe.cooking_time === 'quick' ? 'Quick' : 'Long';
                    option.textContent = `${recipe.name} (${cookingTimeLabel}, ${recipe.servings} servings)`;

                    myRecipesDropdown.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading library recipes:', error);
            myRecipesDropdown.innerHTML = '<option value="" disabled>Error loading recipes</option>';
        }
    }

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

    async function sendAIChatMessage() {
        const message = aiChatInput.value.trim();

        if (!message) {
            showToast('Please enter a message', 'info');
            return;
        }

        // Display user message
        displayUserMessage(message);

        // Clear input
        aiChatInput.value = '';

        // Disable input while processing
        aiChatInput.disabled = true;
        aiChatSend.disabled = true;
        aiChatSend.textContent = 'Thinking...';

        try {
            const response = await fetch('/api/ai-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    history: chatHistory
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to get AI response');
            }

            // Add to chat history
            chatHistory.push({ role: 'user', content: message });
            chatHistory.push({ role: 'assistant', content: data.message });

            // Display AI response
            displayAIMessage(data.message);

            // Display suggested recipes if any
            if (data.recipe_urls && data.recipe_urls.length > 0) {
                displaySuggestedRecipes(data.recipe_urls);
            }

        } catch (error) {
            showToast(`✗ ${error.message}`, 'error');
        } finally {
            // Re-enable input
            aiChatInput.disabled = false;
            aiChatSend.disabled = false;
            aiChatSend.textContent = 'Send';
            aiChatInput.focus();
        }
    }

    function displayUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message';
        messageDiv.innerHTML = `<strong>You:</strong> ${escapeHtml(message)}`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function displayAIMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message ai-message';

        // Convert URLs to clickable links and preserve formatting
        const formattedMessage = formatAIMessage(message);
        messageDiv.innerHTML = `<strong>AI Assistant:</strong> ${formattedMessage}`;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatAIMessage(message) {
        // Escape HTML
        let formatted = escapeHtml(message);

        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');

        // Convert BBC Good Food URLs to clickable links
        formatted = formatted.replace(
            /(https?:\/\/(?:www\.)?bbcgoodfood\.com\/recipes\/[a-z0-9-]+)/gi,
            '<a href="$1" target="_blank" rel="noopener">$1</a>'
        );

        return formatted;
    }

    function displaySuggestedRecipes(recipeUrls) {
        // Clear previous suggestions
        aiSuggestedRecipes.innerHTML = '<h4 style="margin-top: 20px; margin-bottom: 10px;">Suggested Recipes:</h4>';

        recipeUrls.forEach(url => {
            const recipeCard = document.createElement('div');
            recipeCard.className = 'ai-recipe-card';

            // Extract recipe name from URL (approximate)
            const recipeName = url.split('/').pop().replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

            recipeCard.innerHTML = `
                <div class="ai-recipe-info">
                    <div class="ai-recipe-name">${recipeName}</div>
                    <a href="${url}" target="_blank" rel="noopener" class="ai-recipe-url">${url}</a>
                </div>
                <button class="ai-add-recipe-btn" onclick="addAIRecipeToMenu('${url}')">+ Add to Menu</button>
            `;

            aiSuggestedRecipes.appendChild(recipeCard);
        });
    }

    // Make addAIRecipeToMenu available globally
    window.addAIRecipeToMenu = async function(url) {
        await importRecipeFromURL(url);
    };

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});


