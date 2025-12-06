/**
 * Recipe Library Management
 * JavaScript for the recipe library page
 */

// Global state
let allRecipes = [];
let selectedRecipeIds = new Set();

// DOM Elements
const recipeGrid = document.getElementById('recipeGrid');
const emptyState = document.getElementById('emptyState');
const loadingDiv = document.getElementById('loading');
const bulkActionsBar = document.getElementById('bulkActionsBar');
const selectedCount = document.getElementById('selectedCount');
const addRecipeBtn = document.getElementById('addRecipeBtn');
const addFirstRecipeBtn = document.getElementById('addFirstRecipeBtn');
const addRecipeModal = document.getElementById('addRecipeModal');
const closeAddModal = document.getElementById('closeAddModal');
const cancelAddRecipe = document.getElementById('cancelAddRecipe');
const recipeUrlInput = document.getElementById('recipeUrlInput');
const importRecipeBtn = document.getElementById('importRecipeBtn');
const recipeDetailsModal = document.getElementById('recipeDetailsModal');
const closeDetailsModal = document.getElementById('closeDetailsModal');
const closeDetailsBtn = document.getElementById('closeDetailsBtn');
const deleteConfirmModal = document.getElementById('deleteConfirmModal');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    addRecipeBtn.addEventListener('click', showAddRecipeModal);
    addFirstRecipeBtn.addEventListener('click', showAddRecipeModal);
    closeAddModal.addEventListener('click', hideAddRecipeModal);
    cancelAddRecipe.addEventListener('click', hideAddRecipeModal);
    importRecipeBtn.addEventListener('click', handleImportRecipe);

    // Allow Enter key to trigger import
    recipeUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleImportRecipe();
        }
    });

    closeDetailsModal.addEventListener('click', hideRecipeDetailsModal);
    closeDetailsBtn.addEventListener('click', hideRecipeDetailsModal);

    deleteSelectedBtn.addEventListener('click', showDeleteConfirmation);
    confirmDeleteBtn.addEventListener('click', handleDeleteRecipes);
    cancelDeleteBtn.addEventListener('click', hideDeleteConfirmModal);
}

// Load all recipes from API
async function loadRecipes() {
    try {
        showLoading();

        const response = await fetch('/api/recipes');
        if (!response.ok) {
            throw new Error('Failed to load recipes');
        }

        allRecipes = await response.json();

        hideLoading();

        if (allRecipes.length === 0) {
            showEmptyState();
        } else {
            hideEmptyState();
            displayRecipes();
        }
    } catch (error) {
        hideLoading();
        showToast('Error loading recipes: ' + error.message, 'error');
    }
}

// Display recipes in grid
function displayRecipes() {
    recipeGrid.innerHTML = '';

    allRecipes.forEach(recipe => {
        const card = createRecipeCard(recipe);
        recipeGrid.appendChild(card);
    });
}

// Create a recipe card element
function createRecipeCard(recipe) {
    const card = document.createElement('div');
    card.className = 'recipe-card';
    card.dataset.recipeId = recipe.id;

    const isSelected = selectedRecipeIds.has(recipe.id);
    if (isSelected) {
        card.classList.add('selected');
    }

    const cookingTimeBadge = recipe.cooking_time === 'quick'
        ? '<span class="badge badge-quick">Quick (≤30 min)</span>'
        : '<span class="badge badge-long">Long (>30 min)</span>';

    card.innerHTML = `
        <div class="recipe-card-header">
            <input type="checkbox" class="recipe-checkbox" data-recipe-id="${recipe.id}"
                   ${isSelected ? 'checked' : ''}>
            <h3 class="recipe-card-title">${escapeHtml(recipe.name)}</h3>
        </div>
        <div class="recipe-card-meta">
            ${cookingTimeBadge}
            <span class="recipe-servings">🍽️ ${recipe.servings} servings</span>
        </div>
        <div class="recipe-card-info">
            <span>📝 ${recipe.ingredients.length} ingredients</span>
            <span>👨‍🍳 ${recipe.steps.length} steps</span>
        </div>
    `;

    // Click on card (not checkbox) to view details
    card.addEventListener('click', (e) => {
        if (!e.target.classList.contains('recipe-checkbox')) {
            showRecipeDetails(recipe);
        }
    });

    // Handle checkbox selection
    const checkbox = card.querySelector('.recipe-checkbox');
    checkbox.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent card click
        toggleRecipeSelection(recipe.id, checkbox.checked);
    });

    return card;
}

// Toggle recipe selection
function toggleRecipeSelection(recipeId, isChecked) {
    if (isChecked) {
        selectedRecipeIds.add(recipeId);
    } else {
        selectedRecipeIds.delete(recipeId);
    }

    updateBulkActionsBar();
    updateCardSelection(recipeId, isChecked);
}

// Update card visual state
function updateCardSelection(recipeId, isSelected) {
    const card = document.querySelector(`.recipe-card[data-recipe-id="${recipeId}"]`);
    if (card) {
        if (isSelected) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    }
}

// Update bulk actions bar visibility and count
function updateBulkActionsBar() {
    const count = selectedRecipeIds.size;

    if (count > 0) {
        bulkActionsBar.classList.remove('hidden');
        selectedCount.textContent = `${count} recipe${count > 1 ? 's' : ''} selected`;
    } else {
        bulkActionsBar.classList.add('hidden');
    }
}

// Show recipe details modal
function showRecipeDetails(recipe) {
    document.getElementById('detailsRecipeName').textContent = recipe.name;

    const cookingTimeBadge = recipe.cooking_time === 'quick'
        ? '<span class="badge badge-quick">Quick (≤30 min)</span>'
        : '<span class="badge badge-long">Long (>30 min)</span>';

    let detailsHTML = `
        <div class="recipe-meta-row">
            ${cookingTimeBadge}
            <span class="recipe-servings">🍽️ ${recipe.servings} servings</span>
        </div>

        <div class="recipe-section">
            <h4>Ingredients</h4>
            <ul class="ingredients-list">
                ${recipe.ingredients.map(ing => `
                    <li>${ing.amount} ${ing.unit} ${escapeHtml(ing.name)}</li>
                `).join('')}
            </ul>
        </div>

        <div class="recipe-section">
            <h4>Cooking Steps</h4>
            <ol class="steps-list">
                ${recipe.steps.map(step => `
                    <li>${escapeHtml(step)}</li>
                `).join('')}
            </ol>
        </div>
    `;

    if (recipe.source_url) {
        detailsHTML += `
            <div class="recipe-section">
                <p class="recipe-source">
                    <strong>Source:</strong> <a href="${escapeHtml(recipe.source_url)}" target="_blank">View Original</a>
                </p>
            </div>
        `;
    }

    document.getElementById('recipeDetailsContent').innerHTML = detailsHTML;
    recipeDetailsModal.classList.remove('hidden');
}

// Hide recipe details modal
function hideRecipeDetailsModal() {
    recipeDetailsModal.classList.add('hidden');
}

// Show add recipe modal
function showAddRecipeModal() {
    recipeUrlInput.value = '';
    addRecipeModal.classList.remove('hidden');
}

// Hide add recipe modal
function hideAddRecipeModal() {
    addRecipeModal.classList.add('hidden');
}

// Handle import recipe from URL
async function handleImportRecipe() {
    const url = recipeUrlInput.value.trim();

    if (!url) {
        showToast('Please enter a recipe URL', 'error');
        return;
    }

    // Validate URL format
    try {
        new URL(url);
    } catch {
        showToast('Please enter a valid URL', 'error');
        return;
    }

    // Disable button and show loading
    importRecipeBtn.disabled = true;
    importRecipeBtn.textContent = 'Importing...';

    try {
        // Import recipe via API
        const importResponse = await fetch('/api/import-recipe-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });

        const importResult = await importResponse.json();

        if (!importResponse.ok) {
            throw new Error(importResult.error || 'Failed to import recipe');
        }

        const recipe = importResult.recipe;

        // Immediately save the imported recipe permanently
        const saveResponse = await fetch('/api/recipes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: recipe.name,
                cooking_time: recipe.cooking_time,
                servings: recipe.servings,
                ingredients: recipe.ingredients,
                steps: recipe.steps,
                source_url: recipe.source_url || url,
                image_url: recipe.image_url
            })
        });

        const saveResult = await saveResponse.json();

        if (!saveResponse.ok) {
            throw new Error(saveResult.error || 'Failed to save recipe');
        }

        showToast(`Recipe "${recipe.name}" added successfully!`, 'success');
        hideAddRecipeModal();
        loadRecipes(); // Reload to show new recipe

    } catch (error) {
        showToast('Error importing recipe: ' + error.message, 'error');
    } finally {
        // Re-enable button
        importRecipeBtn.disabled = false;
        importRecipeBtn.textContent = 'Import Recipe';
    }
}

// Show delete confirmation modal
function showDeleteConfirmation() {
    const count = selectedRecipeIds.size;
    const message = count === 1
        ? 'Are you sure you want to delete this recipe? This action cannot be undone.'
        : `Are you sure you want to delete ${count} recipes? This action cannot be undone.`;

    document.getElementById('deleteConfirmMessage').textContent = message;
    deleteConfirmModal.classList.remove('hidden');
}

// Hide delete confirmation modal
function hideDeleteConfirmModal() {
    deleteConfirmModal.classList.add('hidden');
}

// Handle recipe deletion
async function handleDeleteRecipes() {
    const recipeIds = Array.from(selectedRecipeIds);

    if (recipeIds.length === 0) {
        return;
    }

    try {
        const response = await fetch('/api/recipes', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ recipe_ids: recipeIds })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete recipes');
        }

        showToast(result.message || 'Recipes deleted successfully!', 'success');

        // Clear selection
        selectedRecipeIds.clear();
        updateBulkActionsBar();

        hideDeleteConfirmModal();
        loadRecipes(); // Reload to reflect changes

    } catch (error) {
        showToast('Error deleting recipes: ' + error.message, 'error');
        hideDeleteConfirmModal();
    }
}

// UI Helper Functions
function showLoading() {
    loadingDiv.classList.remove('hidden');
    recipeGrid.classList.add('hidden');
    emptyState.classList.add('hidden');
}

function hideLoading() {
    loadingDiv.classList.add('hidden');
    recipeGrid.classList.remove('hidden');
}

function showEmptyState() {
    emptyState.classList.remove('hidden');
    recipeGrid.classList.add('hidden');
}

function hideEmptyState() {
    emptyState.classList.add('hidden');
    recipeGrid.classList.remove('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
